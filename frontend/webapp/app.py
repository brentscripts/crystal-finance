import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_wtf.csrf import generate_csrf
import sqlite3
import io
import csv
from datetime import datetime

from importers.bank import BankCSVImporter
from importers.chase import ChaseCSVImporter
from database.db import FinanceDatabase

# === Load environment variables ===
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['DATABASE'] = os.environ['DATABASE']

# Enable CSRF protection
csrf = CSRFProtect(app)

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# === Validation helper ===
def validate_transaction(data):
    errors = []

    # Date check
    try:
        datetime.strptime(data.get('date', ''), '%Y-%m-%d')
    except ValueError:
        errors.append("Invalid date format (YYYY-MM-DD).")

    # Description
    desc = data.get('description', '').strip()
    if not desc or len(desc) > 200:
        errors.append("Description is required and must be ≤ 200 chars.")

    # Category
    cat = data.get('category', '').strip()
    if len(cat) > 100:
        errors.append("Category too long.")

    # Amount
    try:
        amount = float(data.get('amount', ''))        
    except ValueError:
        errors.append("Amount must be a valid number.")


    # Source
    if data.get('source') not in ('bank', 'chase'):
        errors.append("Source must be 'bank' or 'chase'.")

    return errors

# === Database connection helper ===
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# === Home/index route with pagination, sorting, filtering ===
@app.route('/')
def index():
    try:
        # Get query parameters
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(max(int(request.args.get('per_page', 20)), 1), 100)
        sort = request.args.get('sort', 'date')
        if sort not in ('date', 'description', 'category', 'amount', 'source'):
            sort = 'date'
        order = request.args.get('order', 'desc')
        if order not in ('asc', 'desc'):
            order = 'desc'

        filter_desc = request.args.get('filter_desc', '').strip()
        filter_cat = request.args.get('filter_cat', '').strip()
        filter_source = request.args.get('filter_source', '').strip()

        # Build SQL query
        sql = 'SELECT * FROM transactions WHERE 1=1'
        params = []
        if filter_desc:
            sql += ' AND description LIKE ?'
            params.append(f'%{filter_desc}%')
        if filter_cat:
            sql += ' AND category LIKE ?'
            params.append(f'%{filter_cat}%')
        if filter_source:
            sql += ' AND source LIKE ?'
            params.append(f'%{filter_source}%')
        sql += f' ORDER BY {sort} {order.upper()}'
        sql += ' LIMIT ? OFFSET ?'
        params.extend([per_page, (page-1)*per_page])

        conn = get_db_connection()
        transactions = conn.execute(sql, params).fetchall()

        # Get total count for pagination
        count_sql = 'SELECT COUNT(*) FROM transactions WHERE 1=1'
        count_params = []
        if filter_desc:
            count_sql += ' AND description LIKE ?'
            count_params.append(f'%{filter_desc}%')
        if filter_cat:
            count_sql += ' AND category LIKE ?'
            count_params.append(f'%{filter_cat}%')
        if filter_source:
            count_sql += ' AND source LIKE ?'
            count_params.append(f'%{filter_source}%')
        total = conn.execute(count_sql, count_params).fetchone()[0]
        conn.close()

        return render_template('index.html', transactions=transactions, page=page, per_page=per_page, total=total,
                               sort=sort, order=order, filter_desc=filter_desc, filter_cat=filter_cat, filter_source=filter_source)
    except Exception as e:
        app.logger.error(f"Index route error: {e}", exc_info=True)
        return render_template('error.html', title="Error Loading Transactions",
                               message="We couldn’t load your transactions right now. Please try again."), 500

# === Add route for single or bulk transactions ===
@app.route('/add', methods=('GET', 'POST'))
def add():
    message = None
    if request.method == 'POST':
        try:
            # === Mass upload via CSV ===
            if 'file' in request.files:
                file = request.files.get('file')
                source = request.form.get('source', '').strip()

                if not file or not source:
                    message = 'Please select a file and source type.'
                else:
                    temp_path = 'temp_upload.csv'
                    file.save(temp_path)

                    if source not in ('bank', 'chase'):
                        return render_template('add.html', message='Unknown source type.')

                    importer = BankCSVImporter() if source == 'bank' else ChaseCSVImporter()

                    try:
                        transactions = importer.parse(temp_path)
                    finally:
                        os.remove(temp_path)

                    # Validate each transaction
                    valid_txns = []
                    for txn in transactions:
                        errors = validate_transaction(txn)
                        if not errors:
                            valid_txns.append(txn)

                    if not valid_txns:
                        message = 'No valid transactions found in CSV.'
                    else:
                        db = FinanceDatabase(app.config['DATABASE'])
                        db.insert_transactions(valid_txns)
                        db.close()
                        message = f'Successfully imported {len(valid_txns)} transactions from {source}.'

            # === Single transaction add ===
            elif all(x in request.form for x in ['date', 'description', 'amount', 'source']):
                form_data = {k: request.form.get(k, '').strip() for k in
                             ['date', 'description', 'category', 'amount', 'source']}
                errors = validate_transaction(form_data)
                if errors:
                    return render_template('add.html', message="; ".join(errors)), 400

                conn = get_db_connection()
                conn.execute(
                    'INSERT INTO transactions (date, description, category, amount, source) VALUES (?, ?, ?, ?, ?)',
                    (form_data['date'], form_data['description'], form_data['category'], float(form_data['amount']),
                     form_data['source'])
                )
                conn.commit()
                conn.close()
                return redirect(url_for('index'))

            else:
                message = "Invalid form submission."
        except Exception as e:
            app.logger.error(f"Add route error: {e}", exc_info=True)
            message = "An unexpected error occurred while adding transactions."

    return render_template('add.html', message=message)

# === Delete route ===
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM transactions WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return render_template('error.html', title="Not Found",
                                   message="Transaction not found."), 404
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Delete route error: {e}", exc_info=True)
        return render_template('error.html',
                               title="Error Deleting Transaction",
                               message="We couldn’t delete the transaction. Please try again."), 500

# === Inline update route for AJAX ===
@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    try:
        data = request.get_json()
        errors = validate_transaction(data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        conn = get_db_connection()
        result = conn.execute(
            'UPDATE transactions SET date = ?, description = ?, category = ?, amount = ?, source = ? WHERE id = ?',
            (data['date'], data['description'], data['category'], float(data['amount']), data['source'], id)
        )
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return jsonify({'success': False, 'error': 'Transaction not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Update route error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# === Global CSRF error handler ===
def handle_csrf_error(e):
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        # For fetch/AJAX requests
        return jsonify({
            'success': False,
            'error': 'CSRF token missing or invalid'
        }), 400
    else:
        # For browser form submits
        return "<h1>Security Check Failed</h1><p>Your form session expired or is invalid. Please try again.</p>", 400

# === Dashboard for Charts ===
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# === Serve JSON for Chart.js ===
@app.route('/api/expenses_by_category')
def expenses_by_category():
    try:
        conn = get_db_connection()
        data = conn.execute("""
            SELECT category, ABS(SUM(amount)) AS total
            FROM transactions
            WHERE amount < 0 AND category <> 'Transfer'
            GROUP BY category
            ORDER BY total DESC
        """).fetchall()
        conn.close()
        results = [{'category': row['category'], 'total': row['total']} for row in data]
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error fetching expenses by category: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/monthly_cash_flow')
def monthly_cash_flow():
    try:
        conn = get_db_connection()
        data = conn.execute("""
            SELECT 
                strftime('%Y-%m', date) AS month,
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income,
                ABS(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END)) AS expenses
            FROM transactions
            GROUP BY month
            ORDER BY month
        """).fetchall()
        conn.close()
        results = [{'month': row['month'], 'income': row['income'] or 0, 'expenses': row['expenses'] or 0} for row in data]
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error fetching monthly cash flow: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/income_vs_expenses')
def income_vs_expenses():
    try:
        conn = get_db_connection()
        data = conn.execute("""
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income,
                ABS(SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END)) AS expenses
            FROM transactions
        """).fetchone()
        conn.close()

        result = {
            'income': data['income'] or 0,
            'expenses': data['expenses'] or 0
        }
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching income vs expenses: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/donations_vs_income')
def donations_vs_income():
    try:
        conn = get_db_connection()
        data = conn.execute("""
            SELECT 
                SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) AS income,
                ABS(SUM(CASE 
                    WHEN amount < 0 AND LOWER(category) = 'gifts & donations' 
                    THEN amount ELSE 0 END)) AS donations
            FROM transactions
        """).fetchone()
        conn.close()

        result = {
            'income': data['income'] or 0,
            'donations': data['donations'] or 0
        }
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error fetching donations vs income: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == "__main__":
    app.run(debug=True)





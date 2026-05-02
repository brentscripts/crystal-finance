"""
Crystal Finance Web Application - Frontend
Azure Entra ID (MSAL) Authentication with C# Web API Backend
Uses MySQL via C# Web API instead of direct database access
"""

import os
import uuid
import logging
import msal
import requests
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO)

# === Load environment variables ===
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# === Flask Application ===
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')

# === Flask-Session Configuration ===
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
Session(app)

# === CSRF Protection ===
csrf = CSRFProtect(app)

# === Azure Entra ID / MSAL Configuration ===
AZURE_TENANT = os.environ.get('AZURE_TENANT', 'common')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AUTHORITY = os.environ.get(
    'AUTHORITY', 
    f'https://login.microsoftonline.com/{AZURE_TENANT}'
)
REDIRECT_URI = os.environ.get(
    'REDIRECT_URI', 
    'http://localhost:5000/getAToken'
)
API_SCOPE = os.environ.get('API_SCOPE', '')

if isinstance(API_SCOPE, str):
    API_SCOPE = API_SCOPE.split() if API_SCOPE else []

# === Web API Configuration ===
API_BASE_URL = os.environ.get(
    'API_BASE_URL',
    'http://localhost:5001'
).rstrip('/')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 30))

# ============================================================================
# MSAL Helper Functions
# ============================================================================

def _load_cache():
    """Load token cache from Flask session."""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    """Save token cache to Flask session."""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None):
    """
    Build and return MSAL ConfidentialClientApplication.
    
    Args:
        cache: Optional token cache for token storage
        
    Returns:
        msal.ConfidentialClientApplication instance
        
    Raises:
        ValueError: If CLIENT_ID or CLIENT_SECRET not configured
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET must be configured in environment variables"
        )
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )


def get_valid_token():
    """
    Get a valid access token, refreshing if necessary.
    
    Returns:
        str: Access token if available, None otherwise
    """
    try:
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        
        if accounts:
            scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
            result = cca.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                _save_cache(cache)
                return result["access_token"]
    except Exception as e:
        app.logger.error(f"Error getting valid token: {e}")
    
    return None


def get_api_client():
    """
    Get authenticated HTTP client with bearer token.
    
    Returns:
        requests.Session: Authenticated session with Authorization header, or None if auth fails
    """
    token = get_valid_token()
    if not token:
        return None
    
    client = requests.Session()
    client.headers.update({
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    })
    return client


# ============================================================================
# API Helper Functions
# ============================================================================

def call_api(method, endpoint, data=None, params=None, files=None):
    """
    Make authenticated call to C# Web API.
    
    Args:
        method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
        endpoint: API endpoint (e.g., '/api/CrystalFinance' or '/api/transactions/import')
        data: Request body (for POST/PUT)
        params: Query parameters
        files: Files for upload
        
    Returns:
        tuple: (success: bool, data: dict, status_code: int, error_msg: str)
    """
    client = get_api_client()
    if not client:
        return False, None, 401, "Failed to authenticate with API"
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = client.get(url, params=params, timeout=API_TIMEOUT)
        elif method == 'POST':
            if files:
                # For file uploads, don't set Content-Type; requests will set it automatically
                client.headers.pop('Content-Type', None)
                response = client.post(url, data=data, files=files, params=params, timeout=API_TIMEOUT)
            else:
                response = client.post(url, json=data, params=params, timeout=API_TIMEOUT)
        elif method == 'PUT':
            response = client.put(url, json=data, params=params, timeout=API_TIMEOUT)
        elif method == 'DELETE':
            response = client.delete(url, timeout=API_TIMEOUT)
        else:
            return False, None, 400, f"Unsupported HTTP method: {method}"
        
        # Parse response
        try:
            response_data = response.json()
        except:
            response_data = None
        
        # Check for API success (wrapped in ApiResponse)
        if response.status_code == 200 or response.status_code == 201:
            if response_data and 'success' in response_data:
                if response_data['success']:
                    return True, response_data.get('data'), response.status_code, None
                else:
                    error_msg = response_data.get('message', 'API request failed')
                    return False, None, response.status_code, error_msg
            else:
                # Assume success if no wrapped response
                return True, response_data, response.status_code, None
        elif response.status_code == 404:
            msg = response_data.get('message', 'Not found') if response_data else 'Resource not found'
            return False, None, 404, msg
        elif response.status_code == 400:
            msg = response_data.get('message', 'Bad request') if response_data else 'Invalid request'
            return False, None, 400, msg
        else:
            msg = response_data.get('message', 'API error') if response_data else f'API error: {response.status_code}'
            return False, None, response.status_code, msg
            
    except requests.Timeout:
        return False, None, 504, f"API request timeout ({API_TIMEOUT}s)"
    except requests.ConnectionError:
        return False, None, 503, f"Cannot connect to API: {API_BASE_URL}"
    except Exception as e:
        app.logger.error(f"API call error: {e}", exc_info=True)
        return False, None, 500, f"Unexpected error: {str(e)}"


# ============================================================================
# Authentication Routes
# ============================================================================

@app.route("/login")
def login():
    """
    Initiate OAuth2 login flow with Azure Entra ID.
    
    Redirects to Azure Entra ID login page if not already authenticated.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    
    try:
        scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
        cca = _build_msal_app()
        
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session["oauth_state"] = state
        
        auth_url = cca.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=REDIRECT_URI,
            state=state
        )
        
        app.logger.info("User initiated login")
        return redirect(auth_url)
        
    except ValueError as e:
        app.logger.error(f"Login error: {e}")
        return render_template(
            'error.html',
            title="Configuration Error",
            message="Application not properly configured. Contact administrator."
        ), 500


@app.route("/getAToken")
@csrf.exempt
def authorized():
    """
    Handle OAuth2 callback from Azure Entra ID.
    
    Validates state parameter, exchanges authorization code for tokens,
    and stores user info in session.
    """
    # Validate state parameter for CSRF protection
    state = request.args.get('state')
    session_state = session.get("oauth_state")
    
    if not state or state != session_state:
        app.logger.warning("State parameter mismatch in OAuth2 callback")
        return render_template(
            'error.html',
            title="Security Error",
            message="Invalid state parameter. Authentication failed."
        ), 400
    
    # Check for authentication errors from Azure
    if "error" in request.args:
        error = request.args.get("error")
        error_desc = request.args.get("error_description", "Unknown error")
        app.logger.error(f"Azure Auth Error: {error} - {error_desc}")
        return render_template(
            'error.html',
            title="Authentication Failed",
            message=f"Login failed: {error_desc}"
        ), 400
    
    # Verify authorization code presence
    if "code" not in request.args:
        app.logger.warning("No authorization code in OAuth2 callback")
        return render_template(
            'error.html',
            title="Invalid Request",
            message="No authorization code provided."
        ), 400
    
    try:
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
        
        # Exchange authorization code for tokens
        result = cca.acquire_token_by_authorization_code(
            code=request.args['code'],
            scopes=scopes,
            redirect_uri=REDIRECT_URI
        )
        
        if "error" in result:
            error_desc = result.get('error_description', 'Unknown error')
            app.logger.error(f"Token acquisition failed: {error_desc}")
            return render_template(
                'error.html',
                title="Token Error",
                message=f"Failed to obtain access token: {error_desc}"
            ), 400
        
        # Extract user information from ID token claims
        id_token_claims = result.get("id_token_claims", {})
        session["user"] = {
            "name": id_token_claims.get("name", "User"),
            "email": id_token_claims.get("email", id_token_claims.get("upn", "")),
            "oid": id_token_claims.get("oid"),
        }
        _save_cache(cache)
        
        user_email = session["user"].get("email", "Unknown")
        app.logger.info(f"User authenticated: {user_email}")
        
        return redirect(url_for("access"))
        
    except Exception as e:
        app.logger.error(f"Authorization handler error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="System Error",
            message="An error occurred during authentication. Please try again."
        ), 500


@app.route("/logout")
def logout():
    """
    Clear session and log out user.
    
    Clears all session data and redirects to home page.
    """
    user_email = session.get("user", {}).get("email", "Unknown")
    session.clear()
    app.logger.info(f"User logged out: {user_email}")
    
    # Optional: Redirect to Azure AD logout endpoint for complete logout
    # logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('index', _external=True)}"
    # return redirect(logout_url)
    
    return redirect(url_for("index"))


# ============================================================================
# Main Routes
# ============================================================================

@app.route("/")
def index():
    """
    Public home page.
    
    Shows login prompt if user is not authenticated.
    Redirects to access page if already authenticated.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    return render_template("index.html")


@app.route("/access")
def access():
    """
    Authenticated access page (dashboard).
    
    Requires user to be logged in. Shows user info and navigation.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    user = session.get("user")
    return render_template("access.html", user=user)


@app.route("/transactions")
def transactions():
    """
    Display transactions with pagination.
    
    Requires authentication. Supports:
    - Pagination (page, pageSize query parameters)
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        page = max(int(request.args.get('page', 1)), 1)
        page_size = min(max(int(request.args.get('pageSize', 20)), 1), 100)
        
        success, data, status_code, error = call_api(
            'GET',
            '/api/CrystalFinance',
            params={'pageNumber': page, 'pageSize': page_size}
        )
        
        if not success:
            app.logger.warning(f"Failed to fetch transactions: {error}")
            return render_template(
                'error.html',
                title="Error Loading Transactions",
                message=error or "Could not load transactions from the server."
            ), status_code
        
        # data is a PagedResult{items, totalPages, totalItems}
        transactions = data.get('items', []) if data else []
        total_pages = data.get('totalPages', 1) if data else 1
        total = data.get('totalItems', 0) if data else 0
        
        return render_template(
            'transactions.html',
            transactions=transactions,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
        
    except ValueError:
        return render_template(
            'error.html',
            title="Invalid Request",
            message="Invalid pagination parameters."
        ), 400
    except Exception as e:
        app.logger.error(f"Transactions route error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error Loading Transactions",
            message="An unexpected error occurred."
        ), 500


@app.route('/add', methods=('GET', 'POST'))
def add():
    """
    Add a new transaction via API.
    
    Supports POST with transaction data.
    Requires authentication.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    message = None
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['trxDate', 'amount', 'source', 'description']
            if not all(field in request.form for field in required_fields):
                message = "Missing required fields: trxDate, amount, source, description"
                return render_template('add.html', message=message), 400
            
            # Build transaction data (map HTML field names to API model names)
            transaction = {
                'trxDate': request.form.get('trxDate'),
                'amount': float(request.form.get('amount')),
                'source': request.form.get('source'),
                'description': request.form.get('description'),
                'category': request.form.get('category', ''),
                'transactionType': request.form.get('transactionType', ''),
                'checkNumber': request.form.get('checkNumber', ''),
                'referenceNumber': request.form.get('referenceNumber', ''),
                'memo': request.form.get('memo', ''),
            }
            
            # Remove empty optional fields
            transaction = {k: v for k, v in transaction.items() if v or k in ['trxDate', 'amount', 'source', 'description']}
            
            success, data, status_code, error = call_api(
                'POST',
                '/api/CrystalFinance',
                data=transaction
            )
            
            if not success:
                app.logger.warning(f"Failed to add transaction: {error}")
                message = error or "Failed to add transaction"
                return render_template('add.html', message=message), status_code
            
            app.logger.info(f"Transaction added successfully")
            return redirect(url_for('transactions'))
                
        except ValueError as e:
            app.logger.error(f"Invalid form data: {e}")
            message = f"Invalid data: {str(e)}"
            return render_template('add.html', message=message), 400
        except Exception as e:
            app.logger.error(f"Add route error: {e}", exc_info=True)
            message = "An unexpected error occurred while adding transaction."
            return render_template('add.html', message=message), 500

    return render_template('add.html', message=message)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete a transaction by ID via API. Requires authentication."""
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        success, data, status_code, error = call_api('DELETE', f'/api/CrystalFinance/{id}')
        
        if not success:
            app.logger.warning(f"Failed to delete transaction {id}: {error}")
            return render_template(
                'error.html',
                title="Error Deleting Transaction",
                message=error or "Could not delete transaction."
            ), status_code
        
        app.logger.info(f"Transaction {id} deleted successfully")
        return redirect(url_for('transactions'))
        
    except Exception as e:
        app.logger.error(f"Delete route error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error Deleting Transaction",
            message="An unexpected error occurred."
        ), 500


@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    """Update a transaction by ID via API. AJAX endpoint. Requires authentication."""
    if not session.get("user"):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        # Add ID to the data if not present
        if 'id' not in data:
            data['id'] = id
        
        success, result, status_code, error = call_api(
            'PUT',
            f'/api/CrystalFinance/{id}',
            data=data
        )
        
        if not success:
            app.logger.warning(f"Failed to update transaction {id}: {error}")
            return jsonify({'success': False, 'error': error or 'Update failed'}), status_code
        
        app.logger.info(f"Transaction {id} updated successfully")
        return jsonify({'success': True, 'data': result})
        
    except Exception as e:
        app.logger.error(f"Update route error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/dashboard')
def dashboard():
    """Display dashboard with charts. Requires authentication."""
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template('dashboard.html')


@app.route('/api/expenses_by_category')
def expenses_by_category():
    """API endpoint: Get expenses grouped by category."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        # Call backend API for aggregated data
        success, data, status_code, error = call_api(
            'GET',
            '/api/CrystalFinance/analytics/expenses-by-category'
        )
        
        if not success:
            app.logger.error(f"Failed to fetch expenses by category: {error}")
            return jsonify({'error': error or 'Failed to fetch data'}), status_code
        
        return jsonify(data or [])
        
    except Exception as e:
        app.logger.error(f"Error fetching expenses by category: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/monthly_cash_flow')
def monthly_cash_flow():
    """API endpoint: Get monthly income and expenses."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success, data, status_code, error = call_api(
            'GET',
            '/api/CrystalFinance/analytics/monthly-cash-flow'
        )
        
        if not success:
            app.logger.error(f"Failed to fetch monthly cash flow: {error}")
            return jsonify({'error': error or 'Failed to fetch data'}), status_code
        
        return jsonify(data or [])
        
    except Exception as e:
        app.logger.error(f"Error fetching monthly cash flow: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/income_vs_expenses')
def income_vs_expenses():
    """API endpoint: Get total income vs expenses."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success, data, status_code, error = call_api(
            'GET',
            '/api/CrystalFinance/analytics/income-vs-expenses'
        )
        
        if not success:
            app.logger.error(f"Failed to fetch income vs expenses: {error}")
            return jsonify({'error': error or 'Failed to fetch data'}), status_code
        
        return jsonify(data or {})
        
    except Exception as e:
        app.logger.error(f"Error fetching income vs expenses: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


# ============================================================================
# Template Helpers & Filters
# ============================================================================

@app.context_processor
def inject_csrf_token():
    """Inject CSRF token into all templates."""
    return dict(csrf_token=generate_csrf())


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(400)
def handle_csrf_error(e):
    """Handle CSRF validation errors."""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(
            {'success': False, 'error': 'CSRF token missing or invalid'}
        ), 400
    else:
        return render_template(
            'error.html',
            title="Security Check Failed",
            message="Your form session expired or is invalid. Please try again."
        ), 400


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template(
        'error.html',
        title="Page Not Found",
        message="The page you're looking for doesn't exist."
    ), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {e}", exc_info=True)
    return render_template(
        'error.html',
        title="Server Error",
        message="An unexpected error occurred. Please try again later."
    ), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', False)
    )

# ============================================================================
# MSAL Helper Functions
# ============================================================================

def _load_cache():
    """Load token cache from Flask session."""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    """Save token cache to Flask session."""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None):
    """
    Build and return MSAL ConfidentialClientApplication.
    
    Args:
        cache: Optional token cache for token storage
        
    Returns:
        msal.ConfidentialClientApplication instance
        
    Raises:
        ValueError: If CLIENT_ID or CLIENT_SECRET not configured
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET must be configured in environment variables"
        )
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )


def get_valid_token():
    """
    Get a valid access token, refreshing if necessary.
    
    Returns:
        str: Access token if available, None otherwise
    """
    try:
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        
        if accounts:
            scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
            result = cca.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                _save_cache(cache)
                return result["access_token"]
    except Exception as e:
        app.logger.error(f"Error getting valid token: {e}")
    
    return None


def get_api_client():
    """
    Get authenticated HTTP client with bearer token.
    
    Returns:
        requests.Session: Authenticated session with Authorization header
    """
    token = get_valid_token()
    if not token:
        return None
    
    client = requests.Session()
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client


# ============================================================================
# Database Helper Functions
# ============================================================================

def get_db_connection():
    """
    Get database connection with Row factory.
    
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def validate_transaction(data):
    """
    Validate transaction data.
    
    Args:
        data: Dictionary with transaction fields
        
    Returns:
        list: List of validation error messages (empty if valid)
    """
    errors = []

    # Date validation
    try:
        datetime.datetime.strptime(data.get('date', ''), '%Y-%m-%d')
    except ValueError:
        errors.append("Invalid date format (YYYY-MM-DD).")

    # Description validation
    desc = data.get('description', '').strip()
    if not desc or len(desc) > 200:
        errors.append("Description is required and must be ≤ 200 chars.")

    # Category validation
    cat = data.get('category', '').strip()
    if len(cat) > 100:
        errors.append("Category too long.")

    # Amount validation
    try:
        float(data.get('amount', ''))
    except ValueError:
        errors.append("Amount must be a valid number.")

    # Source validation
    if data.get('source') not in ('bank', 'chase'):
        errors.append("Source must be 'bank' or 'chase'.")

    return errors


# ============================================================================
# Authentication Routes
# ============================================================================

@app.route("/login")
def login():
    """
    Initiate OAuth2 login flow with Azure Entra ID.
    
    Redirects to Azure Entra ID login page if not already authenticated.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    
    try:
        scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
        cca = _build_msal_app()
        
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session["oauth_state"] = state
        
        auth_url = cca.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=REDIRECT_URI,
            state=state
        )
        
        app.logger.info("User initiated login")
        return redirect(auth_url)
        
    except ValueError as e:
        app.logger.error(f"Login error: {e}")
        return render_template(
            'error.html',
            title="Configuration Error",
            message="Application not properly configured. Contact administrator."
        ), 500


@app.route("/getAToken")
@csrf.exempt
def authorized():
    """
    Handle OAuth2 callback from Azure Entra ID.
    
    Validates state parameter, exchanges authorization code for tokens,
    and stores user info in session.
    """
    # Validate state parameter for CSRF protection
    state = request.args.get('state')
    session_state = session.get("oauth_state")
    
    if not state or state != session_state:
        app.logger.warning("State parameter mismatch in OAuth2 callback")
        return render_template(
            'error.html',
            title="Security Error",
            message="Invalid state parameter. Authentication failed."
        ), 400
    
    # Check for authentication errors from Azure
    if "error" in request.args:
        error = request.args.get("error")
        error_desc = request.args.get("error_description", "Unknown error")
        app.logger.error(f"Azure Auth Error: {error} - {error_desc}")
        return render_template(
            'error.html',
            title="Authentication Failed",
            message=f"Login failed: {error_desc}"
        ), 400
    
    # Verify authorization code presence
    if "code" not in request.args:
        app.logger.warning("No authorization code in OAuth2 callback")
        return render_template(
            'error.html',
            title="Invalid Request",
            message="No authorization code provided."
        ), 400
    
    try:
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
        
        # Exchange authorization code for tokens
        result = cca.acquire_token_by_authorization_code(
            code=request.args['code'],
            scopes=scopes,
            redirect_uri=REDIRECT_URI
        )
        
        if "error" in result:
            error_desc = result.get('error_description', 'Unknown error')
            app.logger.error(f"Token acquisition failed: {error_desc}")
            return render_template(
                'error.html',
                title="Token Error",
                message=f"Failed to obtain access token: {error_desc}"
            ), 400
        
        # Extract user information from ID token claims
        id_token_claims = result.get("id_token_claims", {})
        session["user"] = {
            "name": id_token_claims.get("name", "User"),
            "email": id_token_claims.get("email", id_token_claims.get("upn", "")),
            "oid": id_token_claims.get("oid"),
        }
        _save_cache(cache)
        
        user_email = session["user"].get("email", "Unknown")
        app.logger.info(f"User authenticated: {user_email}")
        
        return redirect(url_for("access"))
        
    except Exception as e:
        app.logger.error(f"Authorization handler error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="System Error",
            message="An error occurred during authentication. Please try again."
        ), 500


@app.route("/logout")
def logout():
    """
    Clear session and log out user.
    
    Clears all session data and redirects to home page.
    """
    user_email = session.get("user", {}).get("email", "Unknown")
    session.clear()
    app.logger.info(f"User logged out: {user_email}")
    
    # Optional: Redirect to Azure AD logout endpoint for complete logout
    # logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('index', _external=True)}"
    # return redirect(logout_url)
    
    return redirect(url_for("index"))


# ============================================================================
# Main Routes
# ============================================================================

@app.route("/")
def index():
    """
    Public home page.
    
    Shows login prompt if user is not authenticated.
    Redirects to access page if already authenticated.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    return render_template("index.html")


@app.route("/access")
def access():
    """
    Authenticated access page (dashboard).
    
    Requires user to be logged in. Shows user info and navigation.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    user = session.get("user")
    return render_template("access.html", user=user)


@app.route("/transactions")
def transactions():
    """
    Display transactions with pagination, sorting, and filtering.
    
    Requires authentication. Supports:
    - Pagination (page, per_page)
    - Sorting (sort column, ascending/descending)
    - Filtering (description, category, source)
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        # Parse query parameters
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

        # Build SQL query with filters
        sql = 'SELECT * FROM transactions WHERE 1=1'
        params = []
        if filter_desc:
            sql += ' AND description LIKE ?'
            params.append(f'%{filter_desc}%')
        if filter_cat:
            sql += ' AND category LIKE ?'
            params.append(f'%{filter_cat}%')
        if filter_source:
            sql += ' AND source = ?'
            params.append(filter_source)
        
        sql += f' ORDER BY {sort} {order.upper()}'
        sql += ' LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])

        conn = get_db_connection()
        txns = conn.execute(sql, params).fetchall()

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
            count_sql += ' AND source = ?'
            count_params.append(filter_source)
        
        total = conn.execute(count_sql, count_params).fetchone()[0]
        conn.close()

        return render_template(
            'transactions.html',
            transactions=txns,
            page=page,
            per_page=per_page,
            total=total,
            sort=sort,
            order=order,
            filter_desc=filter_desc,
            filter_cat=filter_cat,
            filter_source=filter_source
        )
        
    except Exception as e:
        app.logger.error(f"Transactions route error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error Loading Transactions",
            message="We couldn't load your transactions right now. Please try again."
        ), 500


@app.route('/add', methods=('GET', 'POST'))
def add():
    """
    Add a new transaction.
    
    Supports both single transaction entry and CSV bulk upload.
    Requires authentication.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    message = None
    if request.method == 'POST':
        try:
            # Single transaction add
            if all(x in request.form for x in ['date', 'description', 'amount', 'source']):
                form_data = {
                    k: request.form.get(k, '').strip()
                    for k in ['date', 'description', 'category', 'amount', 'source']
                }
                errors = validate_transaction(form_data)
                if errors:
                    return render_template('add.html', message="; ".join(errors)), 400

                conn = get_db_connection()
                conn.execute(
                    'INSERT INTO transactions (date, description, category, amount, source) VALUES (?, ?, ?, ?, ?)',
                    (
                        form_data['date'],
                        form_data['description'],
                        form_data['category'],
                        float(form_data['amount']),
                        form_data['source']
                    )
                )
                conn.commit()
                conn.close()
                app.logger.info(f"Transaction added: {form_data['description']}")
                return redirect(url_for('transactions'))
            else:
                message = "Invalid form submission. Please fill in all required fields."
                
        except Exception as e:
            app.logger.error(f"Add route error: {e}", exc_info=True)
            message = "An unexpected error occurred while adding transaction."

    return render_template('add.html', message=message)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete a transaction by ID. Requires authentication."""
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        conn = get_db_connection()
        result = conn.execute('DELETE FROM transactions WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return render_template(
                'error.html',
                title="Not Found",
                message="Transaction not found."
            ), 404
        
        app.logger.info(f"Transaction deleted: ID {id}")
        return redirect(url_for('transactions'))
        
    except Exception as e:
        app.logger.error(f"Delete route error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error Deleting Transaction",
            message="We couldn't delete the transaction. Please try again."
        ), 500


@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    """Update a transaction by ID. AJAX endpoint. Requires authentication."""
    if not session.get("user"):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        errors = validate_transaction(data)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        conn = get_db_connection()
        result = conn.execute(
            'UPDATE transactions SET date = ?, description = ?, category = ?, amount = ?, source = ? WHERE id = ?',
            (
                data['date'],
                data['description'],
                data['category'],
                float(data['amount']),
                data['source'],
                id
            )
        )
        conn.commit()
        conn.close()

        if result.rowcount == 0:
            return jsonify({'success': False, 'error': 'Transaction not found'}), 404
        
        app.logger.info(f"Transaction updated: ID {id}")
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Update route error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.route('/dashboard')
def dashboard():
    """Display dashboard with charts. Requires authentication."""
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template('dashboard.html')


@app.route('/api/expenses_by_category')
def expenses_by_category():
    """API endpoint: Get expenses grouped by category."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
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
        
        results = [
            {'category': row['category'], 'total': row['total']}
            for row in data
        ]
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f"Error fetching expenses by category: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/monthly_cash_flow')
def monthly_cash_flow():
    """API endpoint: Get monthly income and expenses."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
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
        
        results = [
            {
                'month': row['month'],
                'income': row['income'] or 0,
                'expenses': row['expenses'] or 0
            }
            for row in data
        ]
        return jsonify(results)
        
    except Exception as e:
        app.logger.error(f"Error fetching monthly cash flow: {e}", exc_info=True)
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/api/income_vs_expenses')
def income_vs_expenses():
    """API endpoint: Get total income vs expenses."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
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
    """API endpoint: Get donations vs income."""
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
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


# ============================================================================
# Template Helpers & Filters
# ============================================================================

@app.context_processor
def inject_csrf_token():
    """Inject CSRF token into all templates."""
    return dict(csrf_token=generate_csrf())


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(400)
def handle_csrf_error(e):
    """Handle CSRF validation errors."""
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify(
            {'success': False, 'error': 'CSRF token missing or invalid'}
        ), 400
    else:
        return render_template(
            'error.html',
            title="Security Check Failed",
            message="Your form session expired or is invalid. Please try again."
        ), 400


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template(
        'error.html',
        title="Page Not Found",
        message="The page you're looking for doesn't exist."
    ), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {e}", exc_info=True)
    return render_template(
        'error.html',
        title="Server Error",
        message="An unexpected error occurred. Please try again later."
    ), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', False)
    )


def init_db():
    """Initialize database schema if not exists."""
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Initialize database on startup
if not os.path.exists(DATABASE):
    init_db()

# === Flask-Session Configuration ===
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
Session(app)
csrf = CSRFProtect(app)

# === MSAL Configuration ===
AZURE_TENANT = os.environ.get('AZURE_TENANT', 'common')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AUTHORITY = os.environ.get('AUTHORITY', f'https://login.microsoftonline.com/{AZURE_TENANT}')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://localhost:5000/getAToken')
API_SCOPE = os.environ.get('API_SCOPE', [])

if isinstance(API_SCOPE, str):
    API_SCOPE = API_SCOPE.split()

# === MSAL Cache Helpers ===
def _load_cache():
    """Load token cache from session."""
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache

def _save_cache(cache):
    """Save token cache to session."""
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()

def _build_msal_app(cache=None):
    """Build and return MSAL ConfidentialClientApplication."""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be configured in environment variables")
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

# === Auth Routes ===
@app.route("/login")
def login():
    """Initiate OAuth2 login flow with Azure Entra ID."""
    if session.get("user"):
        return redirect(url_for("access"))
    
    scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
    cca = _build_msal_app()
    
    # Generate state for CSRF protection and store in session
    state = str(uuid.uuid4())
    session["oauth_state"] = state
    
    auth_url = cca.get_authorization_request_url(
        scopes=scopes,
        redirect_uri=REDIRECT_URI,
        state=state
    )
    return redirect(auth_url)

@app.route("/getAToken")
@csrf.exempt
def authorized():
    """Handle OAuth2 callback from Azure Entra ID."""
    # Validate state parameter for CSRF protection
    state = request.args.get('state')
    session_state = session.get("oauth_state")
    
    if not state or state != session_state:
        return render_template('error.html', 
                             title="Security Error",
                             message="Invalid state parameter. Authentication failed."), 400
    
    # Check for authentication errors
    if "error" in request.args:
        error = request.args.get("error")
        error_desc = request.args.get("error_description", "Unknown error")
        app.logger.error(f"Azure Auth Error: {error} - {error_desc}")
        return render_template('error.html',
                             title="Authentication Failed",
                             message=f"Login failed: {error_desc}"), 400
    
    # Check for authorization code
    if "code" not in request.args:
        return render_template('error.html',
                             title="Invalid Request",
                             message="No authorization code provided."), 400
    
    cache = _load_cache()
    cca = _build_msal_app(cache=cache)
    scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
    
    # Exchange authorization code for tokens
    result = cca.acquire_token_by_authorization_code(
        code=request.args['code'],
        scopes=scopes,
        redirect_uri=REDIRECT_URI
    )
    
    if "error" in result:
        app.logger.error(f"Token acquisition failed: {result.get('error_description')}")
        return render_template('error.html',
                             title="Token Error",
                             message=f"Failed to obtain access token: {result.get('error_description')}"), 400
    
    # Store user info and token in session
    id_token_claims = result.get("id_token_claims", {})
    session["user"] = {
        "name": id_token_claims.get("name", "User"),
        "email": id_token_claims.get("email", id_token_claims.get("upn", "")),
        "oid": id_token_claims.get("oid"),
    }
    _save_cache(cache)
    
    app.logger.info(f"User authenticated: {session['user'].get('email')}")
    return redirect(url_for("access"))

@app.route("/logout")
def logout():
    """Clear session and redirect to logout endpoint."""
    user_email = session.get("user", {}).get("email", "Unknown")
    session.clear()
    app.logger.info(f"User logged out: {user_email}")
    
    # Optional: Redirect to Azure AD logout endpoint
    # logout_url = f"{AUTHORITY}/oauth2/v2.0/logout?post_logout_redirect_uri={url_for('index', _external=True)}"
    # return redirect(logout_url)
    
    return redirect(url_for("index"))

# === Token and API Client Helpers ===
def get_valid_token():
    """Get a valid access token, refreshing if necessary."""
    cache = _load_cache()
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    
    if accounts:
        scopes = API_SCOPE or [f"{CLIENT_ID}/.default"]
        result = cca.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            _save_cache(cache)
            return result["access_token"]
    return None

def get_api_client():
    """Get authenticated HTTP client with bearer token."""
    token = get_valid_token()
    if not token:
        return None
    
    client = requests.Session()
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client

# === Database Connection Helper ===
def get_db_connection():
    """Get database connection with Row factory."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# === Main Routes ===
@app.route("/")
def index():
    """Public home page (no auth required)."""
    if session.get("user"):
        return redirect(url_for("access"))
    return render_template("index.html")

@app.route("/access")
def access():
    """Authenticated access page (requires login)."""
    if not session.get("user"):
        return redirect(url_for("login"))
    
    user = session.get("user")
    return render_template("access.html", user=user)

@app.route("/data")
def get_data():
    client = get_api_client()
    if not client:
        return redirect(url_for("login"))
    
    # Example API call
    response = client.get(f"{os.environ['API_BASE_URL']}/api/values")
    return jsonify(response.json())

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





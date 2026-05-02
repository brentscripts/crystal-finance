"""
Crystal Finance Flask Web Application

A Flask-based web application for personal financial management with:
- Azure Entra ID (OAuth 2.0) authentication via MSAL
- C# Web API backend for all data operations
- MySQL database (accessed via Web API)
- Jinja2 template rendering
- CSRF protection via Flask-WTF
"""

import os
import uuid
import logging
from datetime import datetime
import requests
from flask import (
    Flask, render_template, request, session, redirect, url_for, jsonify
)
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, generate_csrf
import msal

# ============================================================================
# Flask Application Setup
# ============================================================================

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# ============================================================================
# Environment Configuration
# ============================================================================

# Web API Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:5001')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', 10))

# MSAL/Azure Configuration
AZURE_TENANT = os.environ.get('AZURE_TENANT', 'common')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AUTHORITY = os.environ.get('AUTHORITY')

REDIRECT_URI = os.environ.get(
    'REDIRECT_URI',
    'http://localhost:5000/getAToken'
)
API_SCOPE = os.environ.get('API_SCOPE', f'{CLIENT_ID}/.default')

if isinstance(API_SCOPE, str):
    API_SCOPE = [API_SCOPE] if API_SCOPE else [f'{CLIENT_ID}/.default']

# ============================================================================
# Session & CSRF Configuration
# ============================================================================

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
Session(app)
csrf = CSRFProtect(app)

# ============================================================================
# MSAL Helper Functions
# ============================================================================


def _load_cache():
    """
    Load token cache from session storage.
    
    Returns:
        msal.SerializableTokenCache: Deserialized token cache from session
    """
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    """
    Save token cache to session storage.
    
    Args:
        cache (msal.SerializableTokenCache): Token cache to save
    """
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None):
    """
    Build and return MSAL ConfidentialClientApplication.
    
    Args:
        cache (msal.SerializableTokenCache, optional): Token cache instance
        
    Returns:
        msal.ConfidentialClientApplication: Configured MSAL app
        
    Raises:
        ValueError: If CLIENT_ID or CLIENT_SECRET not configured
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        raise ValueError(
            "CLIENT_ID and CLIENT_SECRET must be set in environment variables"
        )
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

# ============================================================================
# Token & API Client Functions
# ============================================================================


def get_valid_token():
    """
    Get a valid access token, refreshing if necessary.
    
    Attempts to acquire a token silently using cached credentials.
    Falls back to requesting a new token if refresh fails.
    
    Returns:
        str: Valid access token, or None if authentication fails
    """
    try:
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        
        if accounts:
            result = cca.acquire_token_silent(API_SCOPE, account=accounts[0])
            if result and "access_token" in result:
                _save_cache(cache)
                return result["access_token"]
            
            if "error" in result:
                app.logger.warning(f"Token refresh failed: {result.get('error_description')}")
    
    except Exception as e:
        app.logger.error(f"Error acquiring token: {e}")
    
    return None


def get_api_client():
    """
    Get authenticated HTTP client with Bearer token.
    
    Creates a requests Session with Authorization header containing
    a valid access token.
    
    Returns:
        requests.Session: Configured session with auth header, or None if token unavailable
    """
    token = get_valid_token()
    if not token:
        app.logger.warning("No valid token available for API client")
        return None
    
    client = requests.Session()
    client.headers.update({'Authorization': f'Bearer {token}'})
    return client


def call_api(method, endpoint, data=None, params=None, files=None):
    """
    Make authenticated API call to backend service.
    
    Central point for all API communication with error handling,
    timeout management, and response validation.
    
    Args:
        method (str): HTTP method ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
        endpoint (str): API endpoint path (e.g., '/api/transactions')
        data (dict, optional): JSON request body
        params (dict, optional): Query parameters
        files (dict, optional): Files for multipart upload
        
    Returns:
        dict: API response in format {'success': bool, 'data': obj, 'message': str}
        
    Raises:
        Exception: If client authentication fails or timeout occurs
    """
    client = get_api_client()
    if not client:
        return {
            'success': False,
            'error': 'Authentication required',
            'message': 'Please log in to continue'
        }
    
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = client.get(url, params=params, timeout=API_TIMEOUT)
        elif method.upper() == 'POST':
            response = client.post(
                url,
                json=data,
                params=params,
                files=files,
                timeout=API_TIMEOUT
            )
        elif method.upper() == 'PUT':
            response = client.put(url, json=data, params=params, timeout=API_TIMEOUT)
        elif method.upper() == 'DELETE':
            response = client.delete(url, params=params, timeout=API_TIMEOUT)
        elif method.upper() == 'PATCH':
            response = client.patch(url, json=data, params=params, timeout=API_TIMEOUT)
        else:
            return {'success': False, 'error': f'Unsupported method: {method}'}
        
        # Handle HTTP errors
        if response.status_code >= 400:
            error_message = f"HTTP {response.status_code}: {response.reason}"
            app.logger.error(f"API Error: {error_message}")
            try:
                return response.json()  # Server may return error details
            except:
                return {
                    'success': False,
                    'error': 'API Error',
                    'message': error_message
                }
        
        # Parse successful response
        try:
            return response.json()
        except:
            return {'success': True, 'data': response.text}
    
    except requests.Timeout:
        error_msg = f"API request timeout ({API_TIMEOUT}s): {endpoint}"
        app.logger.error(error_msg)
        return {
            'success': False,
            'error': 'Timeout',
            'message': 'Request took too long. Please try again.'
        }
    
    except requests.ConnectionError:
        error_msg = f"Cannot connect to API: {API_BASE_URL}"
        app.logger.error(error_msg)
        return {
            'success': False,
            'error': 'Connection Error',
            'message': 'Cannot reach the server. Please try again later.'
        }
    
    except Exception as e:
        app.logger.error(f"API call error: {e}", exc_info=True)
        return {
            'success': False,
            'error': 'Internal Error',
            'message': 'An unexpected error occurred. Please try again.'
        }

# ============================================================================
# Authentication Routes
# ============================================================================


@app.route("/login")
def login():
    """
    Initiate OAuth2 login flow with Azure Entra ID.
    
    Redirects to Azure Entra ID login page if not already authenticated.
    Stores state parameter in session for CSRF protection.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    
    try:
        cca = _build_msal_app()
        
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session["oauth_state"] = state
        
        auth_url = cca.get_authorization_request_url(
            scopes=API_SCOPE,
            redirect_uri=REDIRECT_URI,
            state=state
        )
        
        app.logger.info("User initiated login")
        return redirect(auth_url)
    
    except ValueError as e:
        app.logger.error(f"Login configuration error: {e}")
        return render_template(
            'error.html',
            title="Configuration Error",
            message="Application not properly configured. Contact administrator."
        ), 500
    except Exception as e:
        app.logger.error(f"Login error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Login Error",
            message="An error occurred during login. Please try again."
        ), 500


@app.route("/getAToken")
@csrf.exempt
def authorized():
    """
    Handle OAuth2 callback from Azure Entra ID.
    
    Validates state parameter for CSRF protection, exchanges authorization
    code for tokens, and stores user info in session.
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
        
        # Exchange authorization code for tokens
        result = cca.acquire_token_by_authorization_code(
            code=request.args['code'],
            scopes=API_SCOPE,
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
    
    return redirect(url_for("index"))

# ============================================================================
# Content Routes
# ============================================================================


@app.route("/")
def index():
    """
    Public home page (no authentication required).
    
    Redirects authenticated users to /access dashboard.
    """
    if session.get("user"):
        return redirect(url_for("access"))
    return render_template("index.html")


@app.route("/access")
def access():
    """
    Authenticated user dashboard (requires login).
    
    Displays user profile and navigation to app features.
    Redirects to login if not authenticated.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    user = session.get("user")
    return render_template("access.html", user=user)


@app.route("/transactions")
def transactions():
    """
    Display list of transactions from Web API.
    
    Retrieves paginated transaction list from backend API.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        # Get pagination parameters
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(max(int(request.args.get('per_page', 20)), 1), 100)
        
        # Call API to get transactions
        result = call_api(
            'GET',
            '/api/transactions',
            params={'page': page, 'pageSize': per_page}
        )
        
        if not result.get('success'):
            return render_template(
                'error.html',
                title="Error Loading Transactions",
                message=result.get('message', 'Unable to load transactions.')
            ), 500
        
        transactions_data = result.get('data', {})
        
        return render_template(
            'dashboard.html',
            transactions=transactions_data.get('items', []),
            page=page,
            per_page=per_page,
            total=transactions_data.get('total', 0),
            user=session.get('user')
        )
    
    except Exception as e:
        app.logger.error(f"Transactions route error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error",
            message="An unexpected error occurred."
        ), 500


@app.route("/add", methods=['GET', 'POST'])
def add():
    """
    Add new transaction via Web API.
    
    GET: Display form
    POST: Submit transaction data to API
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'date': request.form.get('date', '').strip(),
                'description': request.form.get('description', '').strip(),
                'category': request.form.get('category', '').strip(),
                'amount': request.form.get('amount', '').strip(),
                'source': request.form.get('source', '').strip(),
            }
            
            # Call API to add transaction
            result = call_api('POST', '/api/transactions', data=form_data)
            
            if not result.get('success'):
                return render_template(
                    'add.html',
                    message=result.get('message', 'Failed to add transaction.'),
                    user=session.get('user')
                ), 400
            
            app.logger.info(f"Transaction added: {form_data['description']}")
            return redirect(url_for('transactions'))
        
        except Exception as e:
            app.logger.error(f"Add transaction error: {e}", exc_info=True)
            return render_template(
                'add.html',
                message="An error occurred while adding the transaction.",
                user=session.get('user')
            ), 500
    
    return render_template('add.html', user=session.get('user'))


@app.route("/delete/<int:id>", methods=['POST'])
def delete(id):
    """
    Delete transaction via Web API.
    
    Args:
        id (int): Transaction ID
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    try:
        result = call_api('DELETE', f'/api/transactions/{id}')
        
        if not result.get('success'):
            return render_template(
                'error.html',
                title="Error Deleting Transaction",
                message=result.get('message', 'Unable to delete transaction.')
            ), 500
        
        app.logger.info(f"Transaction deleted: {id}")
        return redirect(url_for('transactions'))
    
    except Exception as e:
        app.logger.error(f"Delete transaction error: {e}", exc_info=True)
        return render_template(
            'error.html',
            title="Error",
            message="An unexpected error occurred."
        ), 500


@app.route("/update/<int:id>", methods=['POST'])
def update(id):
    """
    Update transaction via Web API (AJAX endpoint).
    
    Args:
        id (int): Transaction ID
        
    Returns:
        JSON response with success status
    """
    if not session.get("user"):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        result = call_api('PUT', f'/api/transactions/{id}', data=data)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('message', 'Update failed')
            }), 400
        
        app.logger.info(f"Transaction updated: {id}")
        return jsonify({'success': True})
    
    except Exception as e:
        app.logger.error(f"Update transaction error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Internal error'}), 500


@app.route("/dashboard")
def dashboard():
    """
    Display analytics dashboard with charts and statistics.
    
    Requires authentication. Charts are rendered client-side using data from API.
    """
    if not session.get("user"):
        return redirect(url_for("login"))
    
    return render_template('dashboard.html', user=session.get('user'))

# ============================================================================
# API Endpoints for Dashboard Charts
# ============================================================================


@app.route('/api/expenses_by_category')
def expenses_by_category():
    """
    Get expenses grouped by category for pie chart.
    
    Returns:
        JSON: [{'category': str, 'total': float}, ...]
    """
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = call_api('GET', '/api/analytics/expenses-by-category')
        return jsonify(result.get('data', []))
    except Exception as e:
        app.logger.error(f"Error fetching expenses by category: {e}")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/api/monthly_cash_flow')
def monthly_cash_flow():
    """
    Get monthly income and expenses for line chart.
    
    Returns:
        JSON: [{'month': str, 'income': float, 'expenses': float}, ...]
    """
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = call_api('GET', '/api/analytics/monthly-cash-flow')
        return jsonify(result.get('data', []))
    except Exception as e:
        app.logger.error(f"Error fetching monthly cash flow: {e}")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/api/income_vs_expenses')
def income_vs_expenses():
    """
    Get total income vs expenses for comparison chart.
    
    Returns:
        JSON: {'income': float, 'expenses': float}
    """
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = call_api('GET', '/api/analytics/income-vs-expenses')
        return jsonify(result.get('data', {}))
    except Exception as e:
        app.logger.error(f"Error fetching income vs expenses: {e}")
        return jsonify({'error': 'Internal error'}), 500


@app.route('/api/donations_vs_income')
def donations_vs_income():
    """
    Get charitable donations vs income for comparison chart.
    
    Returns:
        JSON: {'income': float, 'donations': float}
    """
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = call_api('GET', '/api/analytics/donations-vs-income')
        return jsonify(result.get('data', {}))
    except Exception as e:
        app.logger.error(f"Error fetching donations vs income: {e}")
        return jsonify({'error': 'Internal error'}), 500

# ============================================================================
# Context Processors & Error Handlers
# ============================================================================


@app.context_processor
def inject_csrf_token():
    """Inject CSRF token into all templates."""
    return dict(csrf_token=generate_csrf())


@app.errorhandler(400)
def bad_request(e):
    """Handle 400 Bad Request errors."""
    app.logger.warning(f"Bad request: {e}")
    return render_template(
        'error.html',
        title="Bad Request",
        message="The request was invalid. Please check and try again."
    ), 400


@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors."""
    return render_template(
        'error.html',
        title="Not Found",
        message="The page you're looking for doesn't exist."
    ), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 Internal Server errors."""
    app.logger.error(f"Internal server error: {e}", exc_info=True)
    return render_template(
        'error.html',
        title="Server Error",
        message="An unexpected error occurred. Please try again later."
    ), 500


@app.errorhandler(403)
def handle_csrf_error(e):
    """Handle CSRF validation errors."""
    app.logger.warning(f"CSRF validation failed: {e}")
    
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        return jsonify({'success': False, 'error': 'CSRF token invalid'}), 400
    else:
        return render_template(
            'error.html',
            title="Security Check Failed",
            message="Your form session expired or is invalid. Please try again."
        ), 400

# ============================================================================
# Application Entry Point
# ============================================================================


if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', False)
    )

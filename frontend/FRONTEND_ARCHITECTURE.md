# Crystal Finance - Frontend Architecture

## Overview

The Crystal Finance frontend is a Flask web application that provides a user interface for financial transaction management. It has been refactored to use **Azure Entra ID (MSAL) OAuth 2.0 authentication** and communicates with a **C# Web API backend** (which uses MySQL database) instead of direct SQLite access.

## Architecture Changes

### Before (SQLite-based)

```
Browser → Flask App → SQLite Database
```

### After (API-based with Azure AD)

```
Browser → Azure AD (Login) → Flask App ← (with Bearer Token) ← C# Web API ← MySQL Database
```

## Key Components

### 1. Authentication Flow (MSAL - Microsoft Authentication Library)

The application uses Azure Entra ID OAuth 2.0 for secure authentication:

1. **Login Route** (`/login`)
   - User clicks login button
   - Redirected to Azure AD login page
   - MSAL generates authorization URL with state parameter

2. **Callback Route** (`/getAToken`)
   - Azure AD redirects back with authorization code
   - Flask exchanges code for access tokens
   - User info is stored in session
   - Token cache is saved in session for future API calls

3. **Logout Route** (`/logout`)
   - Clears session data
   - Optional redirect to Azure AD logout endpoint

### 2. API Communication Layer

All data operations now go through the C# Web API instead of direct database access:

**API Helper Functions:**

- `get_api_client()` - Creates authenticated HTTP client with bearer token
- `call_api()` - Centralized function for making API calls with error handling

**Benefits:**

- Centralized data validation (in C# API)
- Easier to add API analytics and logging
- Scalable architecture for microservices
- Database agnostic (can migrate from MySQL without changing frontend)

### 3. Removed SQLite Code

The refactoring removed:

- `sqlite3` imports and database connections
- `init_db()` function and schema initialization
- `get_db_connection()` function
- Direct SQL queries in route handlers
- Transaction validation logic (now in API)

## Project Structure

```
frontend/
├── webapp/
│   ├── app.py                      # Main Flask application
│   ├── static/
│   │   ├── style.css               # Shared styles
│   │   ├── dashboard.js            # Chart.js dashboard
│   │   ├── editTable.js            # Transaction table interactions
│   ├── templates/
│   │   ├── login.html              # Azure AD login page
│   │   ├── access.html             # Authenticated dashboard
│   │   ├── transactions.html       # Transaction list view
│   │   ├── add.html                # Add transaction form
│   │   ├── dashboard.html          # Analytics dashboard
│   │   ├── error.html              # Error display page
│   │   ├── index.html              # Public home page
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Development dependencies
├── .env.example                    # Environment variables template
├── docker-compose.yml              # Docker configuration
├── Dockerfile                      # Container image
└── README.md                       # This file
```

## API Endpoints Used

The Flask app calls these C# Web API endpoints:

### Transaction Management

- **GET** `/api/CrystalFinance`
  - Parameters: `pageNumber`, `pageSize`
  - Returns: Paginated transaction list

- **GET** `/api/CrystalFinance/{id}`
  - Returns: Single transaction by ID

- **POST** `/api/CrystalFinance`
  - Body: TransactionModel JSON
  - Creates new transaction

- **PUT** `/api/CrystalFinance/{id}`
  - Body: TransactionModel JSON
  - Updates existing transaction

- **DELETE** `/api/CrystalFinance/{id}`
  - Deletes transaction

### Bulk Operations

- **POST** `/api/transactions/import`
  - Parameters: `source` (bank, chase, etc.)
  - Uploads CSV file for bulk import

### Analytics (Proposed)

- **GET** `/api/CrystalFinance/analytics/expenses-by-category`
- **GET** `/api/CrystalFinance/analytics/monthly-cash-flow`
- **GET** `/api/CrystalFinance/analytics/income-vs-expenses`

## Environment Variables

Required environment variables (see `.env.example`):

### MSAL Configuration

```
CLIENT_ID=<Azure AD Application ID>
CLIENT_SECRET=<Azure AD Client Secret>
AZURE_TENANT=common
AUTHORITY=https://login.microsoftonline.com/common
REDIRECT_URI=http://localhost:5000/getAToken
API_SCOPE=<API Scope from Azure AD>
```

### Flask Configuration

```
SECRET_KEY=<Random 32-byte hex string>
FLASK_ENV=development
FLASK_DEBUG=False
PORT=5000
```

### API Configuration

```
API_BASE_URL=http://localhost:5001
API_TIMEOUT=30
```

## Running the Application

### Prerequisites

- Python 3.9+
- C# Web API running on `http://localhost:5001`
- Azure Entra ID application registered

### Development

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file**

   ```bash
   cp .env.example .env
   # Edit .env with your Azure AD credentials
   ```

3. **Run Flask development server**

   ```bash
   python -m flask run
   # or
   python app.py
   ```

4. **Access application**
   ```
   http://localhost:5000
   ```

### Production

1. **Install production dependencies**

   ```bash
   pip install -r requirements.txt gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

### Docker

1. **Build image**

   ```bash
   docker build -t crystal-finance-frontend .
   ```

2. **Run container**
   ```bash
   docker run -e CLIENT_ID=xxx -e CLIENT_SECRET=yyy \
     -e API_BASE_URL=http://api:5001 \
     -p 5000:5000 crystal-finance-frontend
   ```

## Flask Routes

### Public Routes

- `GET /` - Home page (public)
- `GET /login` - Initiate Azure AD login
- `GET /getAToken` - OAuth2 callback handler

### Authenticated Routes

- `GET /access` - User dashboard
- `GET /transactions` - Transaction list (paginated)
- `GET /add` - Add transaction form
- `POST /add` - Submit new transaction
- `POST /delete/<id>` - Delete transaction
- `POST /update/<id>` - Update transaction (AJAX)
- `GET /dashboard` - Analytics dashboard

### API Routes

- `GET /api/expenses_by_category` - Chart data
- `GET /api/monthly_cash_flow` - Chart data
- `GET /api/income_vs_expenses` - Chart data
- `GET /api/donations_vs_income` - Chart data

## Data Flow

### Adding a Transaction

1. User fills form on `/add`
2. Form POST to `/add` route
3. Flask validates required fields
4. Flask calls `call_api('POST', '/api/CrystalFinance', data=transaction)`
5. API validates transaction using TransactionModel validation
6. API inserts into MySQL database
7. Redirect to `/transactions` list

### Fetching Transactions

1. User visits `/transactions`
2. Flask checks authentication (redirects to login if needed)
3. Flask calls `call_api('GET', '/api/CrystalFinance', params={pageNumber, pageSize})`
4. API queries MySQL and returns paginated results
5. Flask renders `transactions.html` template with data

### Authentication

1. User clicks "Sign in with Microsoft"
2. Redirected to `/login` route
3. Flask generates MSAL auth URL with state
4. Azure AD login page loads
5. User authenticates
6. Azure AD redirects to `/getAToken` with code and state
7. Flask validates state parameter (CSRF protection)
8. Flask exchanges code for tokens
9. Tokens stored in session
10. Redirected to `/access` dashboard

## Security Features

1. **CSRF Protection** - Flask-WTF protects forms with CSRF tokens
2. **OAuth 2.0 State Verification** - Prevents CSRF in auth flow
3. **Bearer Token Authentication** - All API calls use OAuth tokens
4. **Session Management** - Tokens cached in server sessions
5. **HTTPS Ready** - Configure for HTTPS in production
6. **Environment Variables** - Secrets not hardcoded

## Error Handling

The application handles various error scenarios:

1. **Authentication Errors**
   - Missing CLIENT_ID/CLIENT_SECRET
   - Azure AD unavailable
   - State parameter mismatch

2. **API Errors**
   - Connection timeout
   - Invalid response format
   - Validation errors from API

3. **User Errors**
   - Invalid form data
   - Not found (404)
   - Unauthorized access (401)

All errors redirect to `error.html` template with descriptive messages.

## Logging

The application uses Python's built-in logging with INFO level:

- Login attempts
- Token acquisition
- API call errors
- Route execution errors

## Database Schema (Reference)

The C# API backend uses this MySQL schema:

```sql
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    source VARCHAR(50),
    trxDate DATE,
    amount DECIMAL(18,2),
    description VARCHAR(255),
    category VARCHAR(100),
    transactionType VARCHAR(50),
    checkNumber VARCHAR(50),
    referenceNumber VARCHAR(50),
    memo VARCHAR(255),
    balance DECIMAL(18,2),
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Next Steps

1. **Analytics Endpoints** - Add C# API endpoints for analytics
2. **Bulk Import** - Implement CSV import functionality
3. **User Preferences** - Add user settings and preferences
4. **Multi-Account** - Support multiple financial accounts
5. **Notifications** - Alert on budget thresholds
6. **Mobile App** - React Native mobile version

## Dependencies

### Main Dependencies

- `flask` - Web framework
- `flask-session` - Server-side session management
- `flask-wtf` - CSRF protection
- `msal` - Microsoft Authentication Library
- `requests` - HTTP client for API calls
- `python-dotenv` - Environment variable loading

### Development Dependencies

- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `black` - Code formatter
- `pylint` - Code linter

## Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Submit pull request

## License

Proprietary - Crystal Finance

## Support

For issues or questions:

1. Check documentation
2. Review logs for errors
3. Verify environment variables
4. Ensure C# API is running
5. Contact support team

---

**Last Updated:** May 2026
**Framework:** Flask 3.x with MSAL OAuth 2.0
**Backend:** C# Web API with MySQL

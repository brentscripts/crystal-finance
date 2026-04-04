# Crystal-Finance

## Overview
Crystal-Finance is a personal finance application focused on **cash flow tracking** (income vs. expenses) with built-in **tithing calculations**. Transaction data is imported from bank and credit card CSV files into a MySQL database and analyzed using Power BI.

The project intentionally uses a robust stack to gain hands-on **.NET full-stack** and **cloud-ready** experience while solving a real, personal use case.

---

## Architecture (Current – Phase 1)
- **Data ingestion**: PowerShell scripts for CSV parsing and normalization
- **Database**: MySQL running in Docker
- **CRUD access**: MySQL CLI, VS Code, or MySQL Workbench
- **Reporting**: Power BI Desktop
- **Deployment**: Local Docker Compose only

---

## Quick Start
Minimal steps to get running locally.

1. Start MySQL:
   ```bash
   docker compose up -d
   ```

2. Create a `.env` file in the repo root:
   ```env
   HOST_PORT=3307
   MYSQL_ROOT_PASSWORD=your_password
   MYSQL_DATABASE=finance
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   ```

3. Import a CSV file:
   ```powershell
   .\powershell\import-transactions.ps1 -CsvPath .\data\chase.csv -Source Chase
   ```

4. Open Power BI and connect to MySQL (`finance` database on `HOST_PORT`).

---

## Detailed Usage

### Prerequisites
- Docker & Docker Compose
- PowerShell (Windows recommended)
- MySQL CLI or MySQL Workbench
- MySQL .NET Connector (required by `import-transactions.ps1`)

---

### Database Access

#### Option 1 — From Host (MySQL CLI)
Use this when MySQL is exposed via Docker ports.

```powershell
mysql -h 127.0.0.1 -P 3307 -u root -p
```

- `-P` specifies the port
- `-p` prompts for password
- Do **not** pass passwords inline

#### Option 2 — Inside Docker Container
Use this when MySQL is *not* exposed to the host.

```bash
docker ps
docker exec -it <container_name> mysql -u root -p
```

---

### Basic MySQL CLI commands for navigating databases and inspecting schema.

#### Databases
List databases:
```sql
SHOW DATABASES;
```

Select a database:
```sql
USE finance;
```

Show current database:
```sql
SELECT DATABASE();
```

---

#### Tables
List tables in the current database:
```sql
SHOW TABLES;
```

Describe table columns:
```sql
DESCRIBE transactions;
```
### Import Transactions
Set environment variables (PowerShell):

```powershell
$env:HOST_PORT="3307"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_password"
$env:MYSQL_DATABASE="finance"
```

Run the import:
```powershell
.\powershell\import-transactions.ps1 -CsvPath .\data\chase.csv -Source Chase
```

- CSV files are normalized into the `transactions` table
- Uses `INSERT IGNORE` to prevent duplicate rows

---

### Find Duplicate Entries
```powershell
.\powershell\find-duplicate-entries.ps1
```

- Outputs `data/duplicate-entries.csv`
- Supports scanning one or multiple CSV files

---

### Manual SQL / CRUD
```sql
USE finance;

INSERT IGNORE INTO transactions
(trx_date, description, category, amount, source, transaction_type, memo, balance)
VALUES
('2025-05-05','CPP*ORYA','Entertainment',-100.00,'Chase','Sale','',NULL);
```

Manual CRUD can be performed using:
- VS Code (SQLTools / MySQL extensions)
- MySQL Workbench

---

### Power BI
1. Install MySQL ODBC Driver or Connector/NET
2. Power BI Desktop → **Get Data** → **MySQL database**
3. Host: `127.0.0.1`
4. Port: `HOST_PORT`
5. Database: `finance`

---

## Notes, Gotchas & Decisions
- Host-based MySQL access requires exposed Docker ports
- Passwords should never be passed inline in CLI commands
- `import-transactions.ps1` depends on a locally installed MySQL .NET Connector DLL
- `duplicate-entries.csv` is overwritten on each run
- Test imports inside transactions when validating data:
  ```sql
  START TRANSACTION;
  -- run inserts
  ROLLBACK; -- or COMMIT
  ```

---

## Roadmap / Future
- Blazor UI for web-based CRUD and configuration
- Optional WPF desktop client
- .NET Web API to centralize business logic
- Azure DevOps CI/CD pipelines
- Azure-hosted, containerized deployment

---

## Under Construction: Crystal-Finance v2

### .NET Web API - How to use Scalar with OAuth2.0

1. **Register your application** in Azure AD to obtain your **Client ID** and **Tenant ID**.
2. **Configure Scalar** in your `Program.cs`:
    - **Startup folder**
        - `OpenApiConfig.cs`
        - `OpenApiTransformer.cs` 

    > [!TIP]
    > This code is based on an implementation by **Hals**.
    > 
    > * **Source:** ["Setup Scalar with Microsoft.AspNetCore.OpenApi and OAuth2"](https://hals.app)
    > * **Link:** [hals.app/blog/dotnet-openapi-scalar-oauth2](https://hals.app)

3. **Modify `launchsettings.json`**:
    ```json
    "launchBrowser": true,
    "launchUrl": "scalar/v1"
    ```

4. **Test API endpoint in Scalar**:
    - Select a controller endpoint and click the **Test Request** button.
    - Set **Authentication** settings required for the [Microsoft Identity Client (MSAL)](https://learn.microsoft.com) library to acquire an access token:
        - **Use PKCE:** `SHA-256`
        - **Credentials Location:** `Body`
        - **Scopes Selected:** Select available value
        - **Query Parameters:** Enter values if applicable
        - **Request Body:** Enter values if applicable

5. Click the **Authorize** button to get Token.

6. Click the **Send** button to execute the request and view the response.


### Configure Blazor WASM UI with Entra ID

> [!TIP]
> **Learning Resource:** This configuration follows the guide by [Anjuli Johnson](https://www.youtube.com/watch?v=XHB5aqcvxBg) for .NET 8 Entra ID integration.

#### 1. Azure Portal Setup
- **Register Application:** Register as a **Single-page application (SPA)**.
    - **Redirect URI:** `https://localhost:[PORT]/authentication/login-callback`
    - **Authentication:** Ensure **Access tokens** and **ID tokens** are **unchecked** (MSAL uses Authorization Code Flow + PKCE).
- **App Roles:** Create an `Admin` role in **App roles** > **Create app role**.
- **Assignment:** Assign your user to the role via **Enterprise Applications** > **Users and groups**.
    - *Note: On Free Tier tenants, assign individual users directly as Group assignment is restricted.*
- **API Permissions:** 
    - Add `api://<client-id>/access_as_user`.
    - Click **Grant admin consent** for the directory.

#### 2. Visual Studio Setup
- Create Blazor WASM with **Microsoft Identity** authentication.
- **Scopes:** Use the full URI: `api://{WEB_API_CLIENT_ID}/access_as_user`.
- **Default Scopes:** Keep `User.Read` for basic profile access.

## Credits & Attributions
- **Entra ID Role Mapping:** The `CustomAccountFactory` logic is based on the [CodeWithAnjuli GitHub Repository](https://github.com).
    > **Code with Anjuli** (Youtube video)
    > 
    > * **Source:** ["Configure Blazor WebAssembly with Entra ID (.NET 8)"](https://www.youtube.com/watch?v=XHB5aqcvxBg)

- **Register your Blazor application** in Azure AD to obtain your **Client ID** and **Tenant ID**.
    - Single-page application (SPA) registration
    - Redirect URI: `https://localhost/authentication/login-callback`
    - Authentication settings: **Access tokens**, **ID tokens** `unchecked` for Blazor WASM
    - API permissions: Add permissions for your Web API (e.g., `api://<client-id>/access_as_user`)
        - Click Add Permission > API my organization uses > Search for your API > Select permissions > Add permissions
        - Click Grant admin consent for Default Directory 
    - Owners: Click Add Owners > Search for your user account > Select and add
- In Visual Studio, create a new blazor webassembly project with **Microsoft Identity** authentication.
    - Visual Studio will walk you through Microsoft Identity configuration during project setup.
    - Add permission to call your Web API (settings found in `Expose an API` section of your API registration in Azure AD).
        - API URL (Application ID URI): This is the unique identifier for your API, found in the Expose an API blade of the CrystalFinance.Api registration. It usually follows the format: api://{WEB_API_CLIENT_ID}.
        - Scopes: These are the specific permissions defined by your API. You must enter the full scope URI (e.g., api://{WEB_API_CLIENT_ID}/access_as_user). 
    - Leave Microsoft Graph permissions as default `User.Read` for now (you can add more later if needed).

## License
Copyright (c) 2026 Brent Crystal. All rights reserved. No license is granted at this time.

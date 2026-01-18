# Crystal-Finance Application Documentation

## Project Overview

This project is a simple and efficient application designed to manage personal finances, focusing primarily on cash flow monitoring (total expenses vs. total income). A core functional requirement is the ability to calculate tithing on income.

The application uses a SQL database to store transaction data imported from various bank and credit card CSV statements. Key functionalities include:

*   Reading and parsing diverse CSV files into a standardized `Transaction` format.
*   CRUD (Create, Read, Update, Delete) operations for single transactions.
*   Mass uploading transactions via CSV files.
*   Analyzing transaction data using Power BI.
  
---

## 🏗️ Phase 1: Initial Architecture

The initial design focuses on leveraging existing tools and simple scripts for core functionality:

*   **CSV Processing & Database Writing:** Performed using Powershell scripts.
*   **Database Management:** Data is stored in a MySQL database.
*   **CRUD Operations:** Managed via VS Code or MySQL Workbench.
*   **Deployment:** The entire application is deployed locally within a Docker container.

## Next Iteration & Future Enhancements

The next phase of development will introduce a more robust user experience and a cloud-based deployment strategy:

*   **User Interface:** A Blazor UI layer will be added for user-friendly CRUD operations.
*   **API Layer:** A Web API will manage the interaction between the UI and the database.
*   **Deployment Strategy:** Implementation of DevOps practices to deploy the Docker container to Azure.

## Technical Goals

While some of the chosen architecture might seem robust for a small personal application, the primary objective is to **gain .NET Full-Stack developer experience** using this specific stack and set of tools. This project serves as a comprehensive learning platform.

---

## Initial Architecture (**README**)

- **Purpose**: Quick reference for starting MySQL (Docker), logging in, loading CSV data with `import-transactions.ps1`, checking duplicates with `find-duplicate-entries.ps1`, and manually inserting specific rows into the `transactions` table.

**Prerequisites**
- **Docker / Docker Compose**: Installed and running.
- **PowerShell**: Recommended on Windows (scripts live in `./powershell`).
- **MySQL client or Workbench**: For manual SQL entry.
- **MySQL .NET Connector**: Required by `import-transactions.ps1` if you run it from Windows PowerShell. The script currently references a connector DLL path — install the connector and update the path in `powershell/import-transactions.ps1` if needed.

**Start MySQL (Docker)**
- **Command**: From the repo root run:
  - `docker compose up -d`
- **Notes**: The `docker-compose.yml` exposes MySQL on host port `${HOST_PORT}` (set in your environment or `.env`). By default the container's MySQL listens on container port `3306`.

**Login to MySQL (host machine)**
- **Using mysql CLI** (PowerShell example):
  - Set environment values or use your values directly:
    - ``$env:HOST_PORT="3306"``
    - ``$env:MYSQL_USER="root"``
    - ``$env:MYSQL_PASSWORD="your_password"``
    - ``$env:MYSQL_DATABASE="finance"``
  - Connect:
    - ``mysql -h 127.0.0.1 -u $env:MYSQL_USER -p``
  - When prompted, enter the password from `$env:MYSQL_PASSWORD`.

**.env sample**
Create a simple `.env` file in the repo root (used by `docker compose`) or export these as env vars before running scripts:
```
HOST_PORT=3307
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=finance
MYSQL_USER=root
MYSQL_PASSWORD=your_password
```

**Load data using import-transactions.ps1**
- **Set environment variables for the script** (PowerShell):
  - ``$env:HOST_PORT = "3307"``
  - ``$env:MYSQL_USER = "root"``
  - ``$env:MYSQL_PASSWORD = "your_password"``
  - ``$env:MYSQL_DATABASE = "finance"``
- **Run the import script** (example importing `chase.csv`):
  - ``.\powershell\import-transactions.ps1 -CsvPath ".\data\chase.csv" -Source Chase``
- **What it does**: The script parses the CSV, converts fields, and inserts rows using `INSERT IGNORE` to prevent inserting rows that already exist (i.e., it will skip duplicates).

**Check for duplicates using find-duplicate-entries.ps1**
- **Run the duplicate finder** (defaults to `data/chase.csv` and `data/bank.csv` if no paths given):
  - ``.\powershell\find-duplicate-entries.ps1``
  - Or scan a single file: ``.\powershell\find-duplicate-entries.ps1 -CsvPaths .\data\chase.csv``
- **Output**: Writes `data/duplicate-entries.csv` containing duplicate groups with `DuplicateGroupId` and `DuplicateIndex` to help review.

**Manually insert specific entries into MySQL**
- **Open a SQL session** (mysql CLI or Workbench) and switch to the `finance` database:
  - ``USE finance;``
- **Example INSERT statements** (these map columns to the `transactions` table defined in `mysql/init.sql`). Replace values or run inside a transaction for testing.

-- CPP*ORYA (three duplicate rows)
```
INSERT IGNORE INTO transactions (trx_date, description, category, amount, source, transaction_type, memo, balance)
VALUES ('2025-05-05','CPP*ORYA','Entertainment',-100.00,'Chase','Sale','',NULL);
```
- Paste multiple line insert statements as `Single line` in VSCode.

**Manual CRUD (VS Code or MySQL Workbench)**
- You can perform manual `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operations using either:
  - **VS Code** with a MySQL extension (e.g., "MySQL" or "SQLTools") — open a connection to `127.0.0.1:$env:HOST_PORT` and run queries from the editor.
  - **MySQL Workbench** — connect to `127.0.0.1` on `HOST_PORT` and use the SQL Editor for ad-hoc CRUD.

**Power BI (front end)**
- Power BI Desktop is used as the reporting/visualization UI for this project. To connect Power BI to the MySQL `finance` database:
  - Install the MySQL ODBC driver or ConnectorNET as required by Power BI.
  - In Power BI Desktop: `Get Data` -> `MySQL database` and enter `127.0.0.1` and the host port (`HOST_PORT`) plus database `finance` and your credentials.

**Notes & safety**
- Test manual or bulk imports inside a transaction so you can `ROLLBACK` if something looks wrong:
  - ``START TRANSACTION;`` then run your `INSERT`/`LOAD DATA` commands, then ``ROLLBACK;`` to undo or ``COMMIT;`` to make permanent.
- The `find-duplicate-entries.ps1` script writes `data/duplicate-entries.csv` and will overwrite it by default; back it up if you need to preserve earlier outputs.
  
File locations referenced:
- `./powershell/import-transactions.ps1`
- `./powershell/find-duplicate-entries.ps1`
- `./data/duplicate-entries.csv`
- `./mysql/init.sql`

---

## 🏗️ Phase 2: Planned Architecture & Cloud Deployment

The next phase of the project transitions from local scripts to full-stack applications. The architecture is designed to provide robust user interfaces while gaining valuable cloud-native experience.

### 1. The Blazor User Interface (UI)

The primary web frontend will be developed using **Blazor UI**, specifically Blazor WebAssembly or Blazor Server.

*   **Purpose**: Provides a user-friendly web interface to replace manual interactions in MySQL Workbench or the CLI.
*   **Functionality**: Allows for robust CRUD operations on transactions, configuration management, and viewing reports.

### 2. Alternative: WPF Desktop UI

As an alternative or parallel development track, a Windows Presentation Foundation (**WPF**) application is planned.

*   **Purpose**: Provides a rich, native desktop experience for Windows users who prefer a local application interface over a web browser UI.
*   **Functionality**: This desktop application will interact with the same Web API layer to perform all necessary finance management operations.
*   **Goal**: This track helps maximize **.NET Full-Stack** experience by covering both web and desktop application development paradigms.

### 3. The Web API Layer (C# .NET)

A new C# **Web API** project will act as the intermediary between both the Blazor UI and the WPF desktop application and the MySQL database.

*   **Purpose**: Decouples the frontend from the data layer, enhances security, and centralizes business logic (like tithing calculations and data validation).
*   **Technology**: Built with .NET and potentially using Entity Framework Core for data access to MySQL.

### 4. Azure DevOps & CI/CD Pipelines

**Azure DevOps** will manage the Continuous Integration (CI) and Continuous Deployment (CD) processes for all C# projects.

*   **Azure Repos**: The source of truth for all code (C#, Blazor, WPF, HTML/CSS).
*   **Azure Pipelines**:
    *   **CI Pipeline**: Automatically builds all application projects (Console, API, Blazor, WPF) whenever code is pushed.
    *   **CD Pipeline**: Pushes built artifacts or Docker images to Azure hosting services after successful builds.

### 5. Azure Cloud Deployment Strategy

The application components will be deployed as a containerized solution to Microsoft Azure.

*   **Containerization**: The Web API layer will run inside **Docker containers**. (WPF applications are deployed as native Windows executables).
*   **Azure Hosting**: We will use Azure services (likely Azure Container Instances or Azure App Service) to host the containers.

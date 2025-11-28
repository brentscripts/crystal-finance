**Crystal Finance — README**

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

**Load data using import-transactions.ps1**
- **Set environment variables for the script** (PowerShell):
  - ``$env:HOST_PORT = "3306"``
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


---
File locations referenced:
- `./powershell/import-transactions.ps1`
- `./powershell/find-duplicate-entries.ps1`
- `./data/duplicate-entries.csv`
- `./mysql/init.sql`

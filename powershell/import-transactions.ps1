<#
.SYNOPSIS
Imports financial transactions from Bank and Chase CSVs into MySQL database.
Handles null/missing fields and prevents duplicate inserts.
#>

param(
    [string]$CsvPath = "../data/sample.csv",
    [string]$Source = ""  # Optional: Bank or Chase. If empty, script tries to detect
)

# Load MySQL .NET connector - try known locations then search Program Files
$dllCandidates = @(
    "C:\\Program Files (x86)\\MySQL\\MySQL Installer for Windows\\MySql.Data.dll",
    "C:\\Program Files (x86)\\MySQL\\Connector NET 8.0\\Assemblies\\v4.5.2\\MySql.Data.dll",
    "C:\\Program Files\\MySQL\\Connector NET 8.0\\Assemblies\\v4.5.2\\MySql.Data.dll"
)
$dllPath = $dllCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $dllPath) {
    Write-Host "MySql.Data.dll not found in common locations; searching 'Program Files'..."
    $found = Get-ChildItem 'C:\\Program Files*' -Recurse -ErrorAction SilentlyContinue -Filter MySql.Data.dll | Select-Object -First 1
    if ($found) { $dllPath = $found.FullName }
}
if (-not $dllPath) {
    Write-Error "MySql.Data.dll not found. Install Connector/NET or update the script with the correct path."
    exit 1
}
try {
    Add-Type -Path $dllPath
    Write-Host "Loaded MySQL assembly from: $dllPath"
}
catch {
    Write-Error "Failed to load MySql.Data.dll from $($dllPath): $($_.Exception.Message)"
    exit 1
}

# Load environment variables from .env
$envFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"

if (-not (Test-Path $envFile)) {
    Write-Error ".env file not found at $envFile"
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*(#|$)') { return }
    $name, $value = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
}

Write-Host ".env loaded successfully"

# Database credentials from environment variables (logged for diagnostics - avoid secrets in shared logs)
$server   = "127.0.0.1"
$port     = $env:HOST_PORT
$user     = $env:MYSQL_USER
$password = $env:MYSQL_PASSWORD
$database = $env:MYSQL_DATABASE
Write-Host "DB env: HOST_PORT=$env:HOST_PORT; MYSQL_USER=$env:MYSQL_USER; MYSQL_DATABASE=$env:MYSQL_DATABASE"

# Prompt for password if not provided via environment variable
if ([string]::IsNullOrEmpty($password)) {
    Write-Host "MYSQL_PASSWORD not set; prompting for password (input hidden)..."
    try {
        $securePwd = Read-Host -AsSecureString "MySQL password"
        $password = (New-Object System.Net.NetworkCredential('', $securePwd)).Password
    }
    catch {
        Write-Error "Failed to read secure password: $($_.Exception.Message)"
        exit 1
    }
}

$connectionString = "server=$server;port=$port;user=$user;password=$password;database=$database;"

$connection = New-Object MySql.Data.MySqlClient.MySqlConnection($connectionString)
try {
    $connection.Open()
    Write-Host "Connection opened. State: $($connection.State)"
}
catch {
    Write-Error "Failed to open DB connection: $($_.Exception.Message)"
    exit 1
}

# Import CSV
if (-Not (Test-Path $CsvPath)) {
    Write-Error "CSV file not found: $CsvPath"
    exit
}

$csv = Import-Csv $CsvPath

# Detect source if not specified
if ([string]::IsNullOrEmpty($Source)) {
    $headers = $csv | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name
    if ($headers -contains "Transaction ID") { $Source = "Bank" }
    elseif ($headers -contains "Transaction Date") { $Source = "Chase" }
    else { Write-Error "Cannot detect CSV source. Please specify -Source 'Bank' or 'Chase'."; exit }
}

Write-Host "Detected CSV Source: $Source"
$insertCount = 0
$skipCount = 0

foreach ($row in $csv) {
    $cmd = $connection.CreateCommand()
    $cmd.CommandText = @"
INSERT IGNORE INTO transactions 
(trx_date, description, category, amount, source, transaction_type, reference_number, check_number, memo, balance)
VALUES
(@trx_date, @description, @category, @amount, @source, @transaction_type, @reference_number, @check_number, @memo, @balance)
"@

    try {
        if ($Source -eq "Bank") {
            # Required fields
            $trx_date = if ($row."Posting Date") { [DateTime]::Parse($row."Posting Date") } else { $null }
            $description = if ($row.Description) { $row.Description } else { $null }
            $category = if ($row."Transaction Category") { $row."Transaction Category" } else { $null }
            $amount = if ($row.Amount) { [decimal]$row.Amount } else { $null }

            # Optional fields
            $transaction_type = if ($row."Transaction Type") { $row."Transaction Type" } else { $null }
            $reference_number = if ($row."Reference Number") { $row."Reference Number" } else { $null }
            $check_number = if ($row."Check Number") { $row."Check Number" } else { $null }
            $memo = if ($row.Memo) { $row.Memo } else { $null }
            $balance = if ($row.Balance) { [decimal]$row.Balance } else { $null }

            # Add parameters
            $cmd.Parameters.AddWithValue("@trx_date", $trx_date)
            $cmd.Parameters.AddWithValue("@description", $description)
            $cmd.Parameters.AddWithValue("@category", $category)
            $cmd.Parameters.AddWithValue("@amount", $amount)
            $cmd.Parameters.AddWithValue("@source", "Bank")
            $cmd.Parameters.AddWithValue("@transaction_type", $transaction_type)
            $cmd.Parameters.AddWithValue("@reference_number", $reference_number)
            $cmd.Parameters.AddWithValue("@check_number", $check_number)
            $cmd.Parameters.AddWithValue("@memo", $memo)
            $cmd.Parameters.AddWithValue("@balance", $balance)
        }
        elseif ($Source -eq "Chase") {
            $trx_date = if ($row."Transaction Date") { [DateTime]::Parse($row."Transaction Date") } else { $null }
            $description = if ($row.Description) { $row.Description } else { $null }
            $category = if ($row.Category) { $row.Category } else { $null }
            $amount = if ($row.Amount) { [decimal]$row.Amount } else { $null }

            $transaction_type = if ($row.Type) { $row.Type } else { $null }
            $memo = if ($row.Memo) { $row.Memo } else { $null }

            $cmd.Parameters.AddWithValue("@trx_date", $trx_date)
            $cmd.Parameters.AddWithValue("@description", $description)
            $cmd.Parameters.AddWithValue("@category", $category)
            $cmd.Parameters.AddWithValue("@amount", $amount)
            $cmd.Parameters.AddWithValue("@source", "Chase")
            $cmd.Parameters.AddWithValue("@transaction_type", $transaction_type)
            $cmd.Parameters.AddWithValue("@reference_number", $null)
            $cmd.Parameters.AddWithValue("@check_number", $null)
            $cmd.Parameters.AddWithValue("@memo", $memo)
            $cmd.Parameters.AddWithValue("@balance", $null)
        }

        if ($connection.State -ne 'Open') {
            Write-Warning "Connection not open before ExecuteNonQuery — attempting reconnect."
            try {
                $connection.Open()
                Write-Host "Reconnected. State: $($connection.State)"
            }
            catch {
                Write-Error "Reconnect failed: $($_.Exception.Message)"
                break
            }
        }
        $rowsAffected = $cmd.ExecuteNonQuery()
        if ($rowsAffected -eq 0) {
            $skipCount++
        } else {
            $insertCount++
        }
    }
    catch {
        Write-Warning "Failed to insert row: $($_.Exception.Message)"
    }
}

$connection.Close()
Write-Host "Imported $insertCount new transactions from $CsvPath."
Write-Host "Skipped $skipCount duplicate transactions."

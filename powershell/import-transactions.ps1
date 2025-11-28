<#
.SYNOPSIS
Imports financial transactions from Bank and Chase CSVs into MySQL database.
Handles null/missing fields and prevents duplicate inserts.
#>

param(
    [string]$CsvPath = "../data/sample.csv",
    [string]$Source = ""  # Optional: Bank or Chase. If empty, script tries to detect
)

# Load MySQL .NET connectorC:\Program Files (x86)\MySQL\Connector NET 8.0\Assemblies\v4.5.2\MySql.Data.dll
Add-Type -Path "C:\Program Files (x86)\MySQL\MySQL Installer for Windows\MySql.Data.dll"

# Database credentials from environment variables
$server   = "127.0.0.1"
$port     = $env:HOST_PORT
$user     = $env:MYSQL_USER
$password = $env:MYSQL_PASSWORD
$database = $env:MYSQL_DATABASE

$connectionString = "server=$server;port=$port;user=$user;password=$password;database=$database;"

$connection = New-Object MySql.Data.MySqlClient.MySqlConnection($connectionString)
$connection.Open()

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

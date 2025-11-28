<#
.SYNOPSIS
Finds duplicate transaction rows within CSV files (default: `data/chase.csv` and `data/bank.csv`) and writes them to `data/duplicate-entries.csv` for review.

Usage examples:
    # Scan defaults (chase.csv and bank.csv in the repo data folder)
    .\powershell\find-duplicate-entries.ps1

    # Scan specific files and write to a custom output
    .\powershell\find-duplicate-entries.ps1 -CsvPaths .\data\chase.csv, .\data\bank.csv -OutFile my-dupes.csv
#>

param(
    [string[]]$CsvPaths = @(),
    [string]$OutFile = "duplicate-entries.csv"
)

# Resolve script and data directories
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $scriptDir "..\data"
try { $dataDir = (Resolve-Path $dataDir).Path } catch { $dataDir = (Join-Path $scriptDir "..\data") }

if ($CsvPaths.Count -eq 0) {
    $defaults = @("chase.csv","bank.csv")
    foreach ($f in $defaults) {
        $p = Join-Path $dataDir $f
        if (Test-Path $p) { $CsvPaths += $p }
    }
}

if ($CsvPaths.Count -eq 0) {
    Write-Host "No CSV files supplied and no default files found in $dataDir. Exiting."
    exit 0
}

$duplicates = @()
$groupId = 0

foreach ($path in $CsvPaths) {
    Write-Host "Scanning: $path"
    try {
        $csv = Import-Csv -Path $path -ErrorAction Stop
    } catch {
        $err = $_
        Write-Warning ("Failed to import {0}: {1}" -f $path, $err.Exception.Message)
        continue
    }
    if ($csv.Count -eq 0) { Write-Host "  (empty file)"; continue }

    $headers = $csv | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name

    # Detect common column names
    $dateCol = $null
    if ($headers -contains 'Transaction Date') { $dateCol = 'Transaction Date' }
    elseif ($headers -contains 'Posting Date') { $dateCol = 'Posting Date' }
    elseif ($headers -contains 'Date') { $dateCol = 'Date' }

    $descCol = if ($headers -contains 'Description') { 'Description' } elseif ($headers -contains 'Payee') { 'Payee' } else { $headers[0] }
    $amountCol = if ($headers -contains 'Amount') { 'Amount' } else { ($headers | Where-Object { $_ -match 'Amount|Debit|Credit' } | Select-Object -First 1) }

    $map = @{}

    foreach ($row in $csv) {
        # Normalize date
        $dateVal = ''
        if ($dateCol -and $row.$dateCol) {
            try { $dateVal = ([DateTime]::Parse($row.$dateCol)).ToString('yyyy-MM-dd') } catch { $dateVal = $row.$dateCol }
        }

        # Normalize description
        $descVal = ''
        if ($descCol -and $row.$descCol) { $descVal = ($row.$descCol).ToString().Trim().ToLower() }

        # Normalize amount (strip $ and commas)
        $amountVal = ''
        if ($amountCol -and $row.$amountCol) {
            $clean = ($row.$amountCol).ToString() -replace '[\$,]', ''
            try { $amountVal = [decimal]$clean } catch { $amountVal = $clean }
        }

        $key = "$dateVal|$amountVal|$descVal"
        if (-not $map.ContainsKey($key)) { $map[$key] = @() }
        $map[$key] += $row
    }

    # Collect groups where more than one row shares the key
    foreach ($entry in $map.GetEnumerator()) {
        if ($entry.Value.Count -gt 1) {
            $groupId++
            $i = 0
            foreach ($r in $entry.Value) {
                $i++
                $out = @{}
                $out['SourceFile'] = (Split-Path -Leaf $path)
                $out['DuplicateGroupId'] = $groupId
                $out['DuplicateIndex'] = $i
                foreach ($p in $r.PSObject.Properties) { $out[$p.Name] = $p.Value }
                $duplicates += [PSCustomObject]$out
            }
        }
    }
}

$outPath = Join-Path $dataDir $OutFile

if ($duplicates.Count -eq 0) {
    Write-Host "No duplicate rows found in the scanned files."
    exit 0
}

# Export duplicates (overwrite existing file)
try {
    $duplicates | Export-Csv -Path $outPath -NoTypeInformation -Force
    Write-Host "Wrote $($duplicates.Count) duplicate rows (grouped into $groupId groups) to: $outPath"
} catch {
    $err = $_
    Write-Error ("Failed to write duplicates to {0}: {1}" -f $outPath, $err.Exception.Message)
}

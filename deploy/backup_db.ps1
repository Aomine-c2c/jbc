<#
.SYNOPSIS
Backs up the MySQL Database.

.DESCRIPTION
Runs mysqldump, compresses the output to a ZIP file, and removes backups older than 30 days.

.EXAMPLE
.\backup_db.ps1 -DbUser "root" -DbPassword "secret" -DbName "dwrms"
#>

param (
    [string]$DbUser = "root",
    [string]$DbPassword = "",
    [string]$DbName = "dwrms",
    [string]$BackupDir = "C:\Backups\DWRMS",
    [int]$KeepDays = 30
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SqlFile = "$BackupDir\${DbName}_${Timestamp}.sql"
$ZipFile = "$BackupDir\${DbName}_${Timestamp}.zip"

Write-Host "Creating database backup for '$DbName'..." -ForegroundColor Cyan

# Run mysqldump
$DumpCmd = "mysqldump"
$DumpArgs = @("-u", $DbUser)
if ($DbPassword) {
    $DumpArgs += "-p${DbPassword}"
}
$DumpArgs += $DbName

& $DumpCmd $DumpArgs > $SqlFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "mysqldump failed."
    exit $LASTEXITCODE
}

Write-Host "Compressing backup..."
Compress-Archive -Path $SqlFile -DestinationPath $ZipFile -Force
Remove-Item -Path $SqlFile -Force

Write-Host "Backup saved to: $ZipFile" -ForegroundColor Green

Write-Host "Cleaning up backups older than $KeepDays days..."
Get-ChildItem -Path $BackupDir -Filter "*.zip" | 
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$KeepDays) } | 
    Remove-Item -Force

Write-Host "Backup process complete." -ForegroundColor Green

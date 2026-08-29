<#
.SYNOPSIS
Restores the MySQL Database from a backup file (.sql or .zip).

.DESCRIPTION
Unzips the file if necessary, and uses the mysql client to import the SQL script.

.EXAMPLE
.\restore_db.ps1 -BackupFile "C:\Backups\DWRMS\dwrms_20231010.zip" -DbUser "root" -DbPassword "secret" -DbName "dwrms"
#>

param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$DbUser = "root",
    [string]$DbPassword = "",
    [string]$DbName = "dwrms"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

$IsZip = $BackupFile.EndsWith(".zip")
$SqlFileToRestore = $BackupFile

if ($IsZip) {
    Write-Host "Extracting ZIP archive..."
    $ExtractTempDir = Join-Path $env:TEMP "dwrms_restore_$(Get-Random)"
    Expand-Archive -Path $BackupFile -DestinationPath $ExtractTempDir -Force
    $ExtractedFiles = Get-ChildItem -Path $ExtractTempDir -Filter "*.sql"
    
    if ($ExtractedFiles.Count -eq 0) {
        Write-Error "No .sql file found inside the ZIP archive."
        Remove-Item -Path $ExtractTempDir -Recurse -Force
        exit 1
    }
    $SqlFileToRestore = $ExtractedFiles[0].FullName
}

Write-Host "Restoring database '$DbName' from $SqlFileToRestore..." -ForegroundColor Cyan

$MysqlCmd = "mysql"
$MysqlArgs = @("-u", $DbUser)
if ($DbPassword) {
    $MysqlArgs += "-p${DbPassword}"
}
$MysqlArgs += $DbName

cmd.exe /c "$MysqlCmd $($MysqlArgs -join ' ') < `"$SqlFileToRestore`""

if ($LASTEXITCODE -ne 0) {
    Write-Error "Database restore failed."
} else {
    Write-Host "Database restored successfully." -ForegroundColor Green
}

if ($IsZip -and (Test-Path $ExtractTempDir)) {
    Remove-Item -Path $ExtractTempDir -Recurse -Force
}

#!/usr/bin/env pwsh
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pythonPath = "python"

if (Test-Path "$scriptDir\backend\.venv\Scripts\python.exe") {
    $pythonPath = "$scriptDir\backend\.venv\Scripts\python.exe"
} elseif (Test-Path "$scriptDir\.venv\Scripts\python.exe") {
    $pythonPath = "$scriptDir\.venv\Scripts\python.exe"
}

& $pythonPath "$scriptDir\ops" @args

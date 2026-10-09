# activate.ps1
if (!(Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment not found. Did you create it?"
    return
}

. .\.venv\Scripts\Activate.ps1
Write-Host "Virtual environment activated."

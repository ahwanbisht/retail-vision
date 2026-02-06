$ErrorActionPreference = 'Stop'

Write-Host '== Retail Vision one-command local setup ==' -ForegroundColor Cyan

if (-not (Test-Path '.venv')) {
  Write-Host 'Creating virtual environment (.venv)...' -ForegroundColor Yellow
  py -3.11 -m venv .venv
}

Write-Host 'Activating .venv...' -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

Write-Host 'Installing core dependencies...' -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

if ($env:INSTALL_VISION -eq '1') {
  Write-Host 'Installing optional vision dependencies...' -ForegroundColor Yellow
  pip install -r requirements-vision.txt
}

if (-not (Test-Path '.env')) {
  Write-Host 'Creating .env from template...' -ForegroundColor Yellow
  Copy-Item .env.example .env
  Write-Host 'Please edit .env and set POSTGRES_URL, then re-run this script.' -ForegroundColor Red
  exit 1
}

if (-not $env:POSTGRES_URL) {
  Write-Host 'Loading env vars from .env for this session...' -ForegroundColor Yellow
  Get-Content .env | ForEach-Object {
    if ($_ -match '^[A-Za-z_][A-Za-z0-9_]*=') {
      $name, $value = $_ -split '=', 2
      [System.Environment]::SetEnvironmentVariable($name, $value)
    }
  }
}

Write-Host 'Applying database schema (no psql required)...' -ForegroundColor Yellow
python -m scripts.apply_schema

Write-Host 'Starting FastAPI on http://127.0.0.1:8000 ...' -ForegroundColor Green
Start-Process powershell -ArgumentList '-NoExit', '-Command', '. .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload'

Write-Host 'Starting Streamlit on http://localhost:8501 ...' -ForegroundColor Green
Start-Process powershell -ArgumentList '-NoExit', '-Command', '. .\.venv\Scripts\Activate.ps1; streamlit run dashboards/streamlit_app.py'

Write-Host 'Done. Open:' -ForegroundColor Cyan
Write-Host '  API Docs: http://127.0.0.1:8000/docs'
Write-Host '  Streamlit: http://localhost:8501'

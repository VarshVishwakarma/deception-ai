# =========================

# DeceptionAI Setup Script

# =========================

$pythonUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
$installerPath = "$env:TEMP\python-3.10.11.exe"

Write-Host " Downloading Python 3.10.11..."
Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath

Write-Host " Installing Python 3.10 silently..."
Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait

Write-Host " Verifying Python installation..."
py -3.10 --version

Write-Host " Creating virtual environment..."
py -3.10 -m venv venv

Write-Host " Activating environment..."
& ".\venv\Scripts\Activate.ps1"

Write-Host " Upgrading pip..."
python -m pip install --upgrade pip

Write-Host " Installing dependencies..."
pip install transformers datasets torch scikit-learn pandas

Write-Host " Setup complete!"
Write-Host " To activate later: venv\Scripts\activate"

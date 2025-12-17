<#
Set up a Python virtual environment and install requirements on Windows (PowerShell).
Usage: .\setup_windows.ps1
#>
$venv = ".venv"
if (-not (Test-Path $venv)) {
  python -m venv $venv
}
Write-Host "Installing/Upgrading pip and installing requirements using venv python..."
Start-Process -FilePath "$venv\Scripts\python.exe" -ArgumentList '-m','pip','install','--upgrade','pip' -Wait -NoNewWindow
if (Test-Path "requirements.txt") {
  Start-Process -FilePath "$venv\Scripts\python.exe" -ArgumentList '-m','pip','install','-r','requirements.txt' -Wait -NoNewWindow
} else { Write-Host "requirements.txt not found" }
Write-Host "Setup complete. To activate venv: . $venv\Scripts\Activate.ps1"

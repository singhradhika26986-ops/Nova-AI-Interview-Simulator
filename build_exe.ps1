$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Installing runtime and build dependencies..."
python -m pip install -r requirements.txt
python -m pip install pyinstaller

Write-Host "Building Windows executable..."
pyinstaller `
  --noconfirm `
  --clean `
  --name "NovaInterviewSimulator" `
  --add-data "app.py;." `
  --add-data "auth.py;." `
  --add-data "answer_evaluator.py;." `
  --add-data "dashboard.py;." `
  --add-data "database.py;." `
  --add-data "face_detection.py;." `
  --add-data "qa_dataset.py;." `
  --add-data "question_generator.py;." `
  --add-data "report_export.py;." `
  --add-data "voice.py;." `
  --add-data "README.md;." `
  launcher.py

Write-Host ""
Write-Host "Build complete."
Write-Host "Executable location: $projectRoot\dist\NovaInterviewSimulator\NovaInterviewSimulator.exe"

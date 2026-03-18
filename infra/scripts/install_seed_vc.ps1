param(
  [string]$RepoDir = "external/seed-vc",
  [string]$PythonExe = "py -3.10",
  [string]$RepoUrl = "https://github.com/Plachtaa/seed-vc.git"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $RepoDir)) {
  git clone $RepoUrl $RepoDir
}

$repoFullPath = (Resolve-Path $RepoDir).Path
$venvPath = Join-Path $repoFullPath ".venv"

if (-not (Test-Path $venvPath)) {
  Invoke-Expression "$PythonExe -m venv `"$venvPath`""
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $repoFullPath "requirements.txt")

Write-Host ""
Write-Host "Seed-VC was installed in: $repoFullPath"
Write-Host "Use this environment in VoiceForge with:"
Write-Host "  VF_SEED_VC_PYTHON=$venvPython"
Write-Host "  VF_SEED_VC_REPO_DIR=$repoFullPath"

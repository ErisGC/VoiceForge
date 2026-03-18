param(
  [string]$VoiceForgePython = "python",
  [string]$SeedVCPython = $env:VF_SEED_VC_PYTHON,
  [string]$SeedVCRepoDir = $env:VF_SEED_VC_REPO_DIR,
  [string]$CaseDir = "data/demo/seed-vc-case-01",
  [switch]$Reset
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  Write-Error $Message
  exit 1
}

function New-DemoWav(
  [string]$Path,
  [string]$VoiceName,
  [string]$Text
) {
  $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
  try {
    $synth.SelectVoice($VoiceName)
    $synth.SetOutputToWaveFile($Path)
    $synth.Rate = 0
    $synth.Speak($Text)
  }
  finally {
    $synth.Dispose()
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$caseRoot = Join-Path $repoRoot $CaseDir
$inputDir = Join-Path $caseRoot "input"
$outputDir = Join-Path $caseRoot "output"
$runtimeDir = Join-Path $caseRoot "runtime"
$summaryPath = Join-Path $outputDir "summary.json"

if ($Reset -and (Test-Path $caseRoot)) {
  Remove-Item -Recurse -Force $caseRoot
}

if ([string]::IsNullOrWhiteSpace($SeedVCPython)) {
  Fail "VF_SEED_VC_PYTHON no esta configurado. Instala Seed-VC con .\infra\scripts\install_seed_vc.ps1 y exporta VF_SEED_VC_PYTHON."
}

if ([string]::IsNullOrWhiteSpace($SeedVCRepoDir)) {
  Fail "VF_SEED_VC_REPO_DIR no esta configurado. Instala Seed-VC con .\infra\scripts\install_seed_vc.ps1 y exporta VF_SEED_VC_REPO_DIR."
}

if (-not (Test-Path $SeedVCPython)) {
  Fail "No se encontró el runtime de Seed-VC en '$SeedVCPython'. Revisa VF_SEED_VC_PYTHON."
}

if (-not (Test-Path $SeedVCRepoDir)) {
  Fail "No se encontro el repositorio de Seed-VC en '$SeedVCRepoDir'. Ejecuta .\infra\scripts\install_seed_vc.ps1 -RepoDir `"$SeedVCRepoDir`"."
}

if (-not (Test-Path (Join-Path $SeedVCRepoDir "inference.py"))) {
  Fail "El repositorio configurado en '$SeedVCRepoDir' no contiene inference.py. Reinstala Seed-VC desde el repo oficial."
}

New-Item -ItemType Directory -Force -Path $inputDir | Out-Null
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

try {
  Add-Type -AssemblyName System.Speech
}
catch {
  Fail "No fue posible cargar System.Speech para generar los WAV de ejemplo. Ejecuta la demo en Windows Desktop o proporciona audios manualmente al runner Python."
}

$probeSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $installedVoices = @($probeSynth.GetInstalledVoices())
}
finally {
  $probeSynth.Dispose()
}

if ($installedVoices.Count -lt 1) {
  Fail "No hay voces SAPI instaladas en este host. Instala al menos una voz de Windows o usa infra\scripts\demo_seed_vc_e2e.py con tus propios WAVs."
}

$targetVoice = $installedVoices[0].VoiceInfo.Name
$sourceVoice = if ($installedVoices.Count -gt 1) { $installedVoices[1].VoiceInfo.Name } else { $targetVoice }

$referenceOne = Join-Path $inputDir "reference_01.wav"
$referenceTwo = Join-Path $inputDir "reference_02.wav"
$sourceFile = Join-Path $inputDir "source.wav"

New-DemoWav -Path $referenceOne -VoiceName $targetVoice -Text "Hello from VoiceForge. This is the first reference clip for the target voice profile."
New-DemoWav -Path $referenceTwo -VoiceName $targetVoice -Text "This second reference clip adds more variation so the readiness score improves for the demo."
New-DemoWav -Path $sourceFile -VoiceName $sourceVoice -Text "This is the source speech that should be converted into the target voice with Seed V C."

$pythonScript = Join-Path $repoRoot "infra\scripts\demo_seed_vc_e2e.py"
$arguments = @(
  $pythonScript,
  "--case-dir", $caseRoot,
  "--seed-vc-python", $SeedVCPython,
  "--seed-vc-repo-dir", $SeedVCRepoDir,
  "--seed-vc-working-root", $runtimeDir,
  "--source-file", $sourceFile,
  "--reference-file", $referenceOne,
  "--reference-file", $referenceTwo
)

& $VoiceForgePython @arguments
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

if (-not (Test-Path $summaryPath)) {
  Fail "La demo terminó sin generar $summaryPath."
}

$summary = Get-Content $summaryPath | ConvertFrom-Json
Write-Host ""
Write-Host "Demo Seed-VC completada."
Write-Host "WAV final:" $summary.published_output_path
Write-Host "Summary:" $summaryPath

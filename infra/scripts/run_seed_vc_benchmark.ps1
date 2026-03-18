param(
  [string]$VoiceForgePython = "python",
  [string]$SeedVCPython = $env:VF_SEED_VC_PYTHON,
  [string]$SeedVCRepoDir = $env:VF_SEED_VC_REPO_DIR,
  [string]$BenchmarkDir = "data/bench/seed-vc",
  [int]$Iterations = 2,
  [string]$ReferenceCacheEnabled = "true",
  [string]$SourceCacheEnabled = "true",
  [string]$ResidentReferenceRuntimeEnabled = "true",
  [string]$ResidentSourceRuntimeEnabled = "true",
  [int]$DiffusionSteps = 25,
  [string]$Fp16 = "false",
  [string]$BaselineSummary = "",
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
$benchmarkRoot = Join-Path $repoRoot $BenchmarkDir
$inputDir = Join-Path $benchmarkRoot "input"

if ($Reset -and (Test-Path $benchmarkRoot)) {
  Remove-Item -Recurse -Force $benchmarkRoot
}

if ([string]::IsNullOrWhiteSpace($SeedVCPython)) {
  Fail "VF_SEED_VC_PYTHON no esta configurado."
}

if ([string]::IsNullOrWhiteSpace($SeedVCRepoDir)) {
  Fail "VF_SEED_VC_REPO_DIR no esta configurado."
}

if (-not (Test-Path $SeedVCPython)) {
  Fail "No se encontro el runtime de Seed-VC en '$SeedVCPython'."
}

if (-not (Test-Path (Join-Path $SeedVCRepoDir "inference.py"))) {
  Fail "El repo configurado en '$SeedVCRepoDir' no contiene inference.py."
}

New-Item -ItemType Directory -Force -Path $inputDir | Out-Null

try {
  Add-Type -AssemblyName System.Speech
}
catch {
  Fail "No fue posible cargar System.Speech para generar los WAVs del benchmark."
}

$probeSynth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $installedVoices = @($probeSynth.GetInstalledVoices())
}
finally {
  $probeSynth.Dispose()
}

if ($installedVoices.Count -lt 1) {
  Fail "No hay voces SAPI instaladas en este host."
}

$targetVoice = $installedVoices[0].VoiceInfo.Name
$sourceVoice = if ($installedVoices.Count -gt 1) { $installedVoices[1].VoiceInfo.Name } else { $targetVoice }

$referenceOne = Join-Path $inputDir "reference_01.wav"
$referenceTwo = Join-Path $inputDir "reference_02.wav"
$sourceFile = Join-Path $inputDir "source.wav"

New-DemoWav -Path $referenceOne -VoiceName $targetVoice -Text "Hello from VoiceForge. This is the first reference clip for the target benchmark voice."
New-DemoWav -Path $referenceTwo -VoiceName $targetVoice -Text "This second reference clip keeps the test case stable across cold and warm runs."
New-DemoWav -Path $sourceFile -VoiceName $sourceVoice -Text "This is the source speech used to benchmark the offline Seed V C conversion pipeline."

$pythonScript = Join-Path $repoRoot "infra\scripts\benchmark_seed_vc.py"
$arguments = @(
  $pythonScript,
  "--benchmark-dir", $benchmarkRoot,
  "--seed-vc-python", $SeedVCPython,
  "--seed-vc-repo-dir", $SeedVCRepoDir,
  "--source-file", $sourceFile,
  "--reference-file", $referenceOne,
  "--reference-file", $referenceTwo,
  "--iterations", $Iterations,
  "--reference-cache-enabled", $ReferenceCacheEnabled,
  "--source-cache-enabled", $SourceCacheEnabled,
  "--resident-reference-runtime-enabled", $ResidentReferenceRuntimeEnabled,
  "--resident-source-runtime-enabled", $ResidentSourceRuntimeEnabled,
  "--diffusion-steps", $DiffusionSteps,
  "--fp16", $Fp16
)

if (-not [string]::IsNullOrWhiteSpace($BaselineSummary)) {
  $arguments += @("--baseline-summary", (Resolve-Path $BaselineSummary).Path)
}

& $VoiceForgePython @arguments
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

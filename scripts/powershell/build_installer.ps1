$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$issPath = Join-Path $repoRoot "packaging\ArtemisToolkit.iss"
$exePath = Join-Path $repoRoot "dist\ArtemisToolkit\ArtemisToolkit.exe"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Packaged EXE was not found. Run scripts\powershell\build_exe.ps1 first."
}

if (-not (Test-Path -LiteralPath $issPath)) {
    throw "Installer script was not found: $issPath"
}

$iscc = $null

if ($env:INNO_SETUP_ISCC -and (Test-Path -LiteralPath $env:INNO_SETUP_ISCC)) {
    $iscc = Get-Item -LiteralPath $env:INNO_SETUP_ISCC
}

if (-not $iscc) {
    $iscc = Get-Command ISCC -ErrorAction SilentlyContinue
}

if (-not $iscc) {
    $commonPaths = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )

    foreach ($path in $commonPaths) {
        if ($path -and (Test-Path -LiteralPath $path)) {
            $iscc = Get-Item -LiteralPath $path
            break
        }
    }
}

if (-not $iscc) {
    throw "Inno Setup compiler was not found. Install Inno Setup 6 or add ISCC.exe to PATH."
}

$compilerPath = $iscc.Source
if (-not $compilerPath) {
    $compilerPath = $iscc.FullName
}

Write-Host "Artemis Toolkit installer build"
Write-Host "Repo: $repoRoot"
Write-Host "Inno compiler: $compilerPath"

Push-Location $repoRoot
try {
    & $compilerPath $issPath
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup compiler failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}

$installerPath = Join-Path $repoRoot "dist\installer\ArtemisToolkitSetup-v0.6.1.exe"

if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Installer build finished but output was not found: $installerPath"
}

Write-Host ""
Write-Host "Installer build complete:"
Write-Host $installerPath

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$entryPoint = Join-Path $repoRoot "artemis_app.py"
$distPath = Join-Path $repoRoot "dist"
$buildPath = Join-Path $repoRoot "build"
$specPath = Join-Path $repoRoot "ArtemisToolkit.spec"
$iconPath = Join-Path $repoRoot "icons\app.ico"

Write-Host "Artemis Toolkit EXE build"
Write-Host "Repo: $repoRoot"
Write-Host "Python: $python"

if (Test-Path -LiteralPath $distPath) {
    Remove-Item -LiteralPath $distPath -Recurse -Force
}

if (Test-Path -LiteralPath $buildPath) {
    Remove-Item -LiteralPath $buildPath -Recurse -Force
}

if (Test-Path -LiteralPath $specPath) {
    Remove-Item -LiteralPath $specPath -Force
}

$separator = [System.IO.Path]::PathSeparator
$addDataIcons = "icons${separator}icons"
$addDataConfig = "config${separator}config"

$args = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--windowed",
    "--name", "ArtemisToolkit",
    "--distpath", $distPath,
    "--workpath", $buildPath,
    "--specpath", $repoRoot,
    "--add-data", $addDataIcons,
    "--add-data", $addDataConfig,
    $entryPoint
)

if (Test-Path -LiteralPath $iconPath) {
    $args = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name", "ArtemisToolkit",
        "--icon", $iconPath,
        "--distpath", $distPath,
        "--workpath", $buildPath,
        "--specpath", $repoRoot,
        "--add-data", $addDataIcons,
        "--add-data", $addDataConfig,
        $entryPoint
    )
}

Push-Location $repoRoot
try {
    & $python @args
}
finally {
    Pop-Location
}

$exePath = Join-Path $distPath "ArtemisToolkit\ArtemisToolkit.exe"

if (-not (Test-Path -LiteralPath $exePath)) {
    throw "Build finished but EXE was not found: $exePath"
}

Write-Host ""
Write-Host "Build complete:"
Write-Host $exePath

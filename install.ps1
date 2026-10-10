<#
.SYNOPSIS
    Installs ai-sys-buddy for the current Windows user.

.DESCRIPTION
    Downloads the ai-sys-buddy.exe release asset (or uses a local copy), installs
    it under %LOCALAPPDATA%\Programs\ai-sys-buddy, creates an `ai` command shim,
    adds the folder to the user PATH and writes an initial config with your
    Ollama URL and model.

    The repository is private, so pass a GitHub token with -Token (or set the
    GITHUB_TOKEN environment variable) to download the release. Alternatively,
    place ai-sys-buddy.exe next to this script and run it without a token.

.EXAMPLE
    # From a downloaded file next to ai-sys-buddy.exe:
    powershell -ExecutionPolicy Bypass -File .\install.ps1

.EXAMPLE
    # One-liner (repo private -> needs a token):
    $env:GITHUB_TOKEN="ghp_xxx"; irm -Headers @{Authorization="token $env:GITHUB_TOKEN"} https://raw.githubusercontent.com/brodatech-lab/ai-sys-buddy/main/install.ps1 | iex

.EXAMPLE
    # Uninstall:
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$Token = $env:GITHUB_TOKEN,
    [string]$OllamaUrl = "",
    [string]$Model = "",
    [string]$Source = "",
    [switch]$Uninstall,
    [switch]$NoPath
)

$ErrorActionPreference = "Stop"

$Repo       = "brodatech-lab/ai-sys-buddy"
$AssetName  = "ai-sys-buddy.exe"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\ai-sys-buddy"
$ExePath    = Join-Path $InstallDir $AssetName
$ShimPath   = Join-Path $InstallDir "ai.cmd"
$ConfigDir  = Join-Path $env:APPDATA "ai-sys-buddy"
$ConfigPath = Join-Path $ConfigDir "config.json"

function Write-Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Write-Ok($text)   { Write-Host "[+] $text" -ForegroundColor Green }
function Write-Warn2($text){ Write-Host "[!] $text" -ForegroundColor Yellow }

function Remove-FromUserPath([string]$dir) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ([string]::IsNullOrEmpty($userPath)) { return }
    $parts = $userPath.Split(';') | Where-Object { $_ -and ($_ -ne $dir) }
    [Environment]::SetEnvironmentVariable("Path", ($parts -join ';'), "User")
}

function Add-ToUserPath([string]$dir) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($userPath -and ($userPath.Split(';') -contains $dir)) {
        Write-Ok "PATH already contains $dir"
    } else {
        $newPath = if ([string]::IsNullOrEmpty($userPath)) { $dir } else { "$userPath;$dir" }
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Ok "Added $dir to your user PATH"
    }
    if ($env:Path.Split(';') -notcontains $dir) { $env:Path += ";$dir" }
}

if ($Uninstall) {
    Write-Step "Uninstalling ai-sys-buddy"
    Remove-FromUserPath $InstallDir
    if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
    Write-Ok "Removed $InstallDir and its PATH entry"
    if (Test-Path $ConfigDir) {
        $answer = Read-Host "Also remove your config at $ConfigDir ? [y/N]"
        if ($answer -match '^[yY]') { Remove-Item -Recurse -Force $ConfigDir; Write-Ok "Removed config" }
    }
    return
}

# TLS 1.2 for GitHub on older Windows PowerShell.
try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
} catch { }

Write-Step "Installing ai-sys-buddy"

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

# 1) Obtain the executable: local copy, explicit -Source, or GitHub release.
$localExe = ""
if (-not [string]::IsNullOrEmpty($PSScriptRoot)) {
    $localExe = Join-Path $PSScriptRoot $AssetName
}
if (-not [string]::IsNullOrEmpty($Source)) {
    Copy-Item -Force $Source $ExePath
    Write-Ok "Copied binary from $Source"
} elseif ($localExe -and (Test-Path $localExe)) {
    Copy-Item -Force $localExe $ExePath
    Write-Ok "Using local $AssetName"
} else {
    if ([string]::IsNullOrEmpty($Token)) {
        $secure = Read-Host "GitHub token (needed because the repo is private)" -AsSecureString
        $Token = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
            [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
    }
    if ([string]::IsNullOrEmpty($Token)) {
        throw "No token and no local $AssetName found. Download the release asset and place it next to this script, or pass -Token."
    }
    $headers = @{ Authorization = "token $Token"; "User-Agent" = "ai-sys-buddy-installer" }
    Write-Step "Fetching latest release info"
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers $headers
    $asset = $release.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1
    if (-not $asset) { throw "Release $($release.tag_name) has no $AssetName asset." }
    Write-Step "Downloading $AssetName from $($release.tag_name)"
    Invoke-WebRequest -Uri $asset.url -Headers @{
        Authorization = "token $Token"
        Accept        = "application/octet-stream"
        "User-Agent"  = "ai-sys-buddy-installer"
    } -OutFile $ExePath
    Write-Ok "Downloaded $AssetName"
}

# 2) `ai` command shim so it behaves like on Linux.
$shim = "@echo off`r`n`"%~dp0$AssetName`" %*`r`n"
Set-Content -Path $ShimPath -Value $shim -Encoding ASCII
Write-Ok "Created command shim: $ShimPath"

# 3) Add to PATH.
if (-not $NoPath) { Add-ToUserPath $InstallDir } else { Write-Warn2 "Skipped PATH update (-NoPath)" }

# 4) Initial configuration: Ollama URL and model.
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

$defaultUrl = "http://127.0.0.1:11434"
if ([string]::IsNullOrEmpty($OllamaUrl)) {
    $OllamaUrl = Read-Host "Ollama URL [$defaultUrl]"
    if ([string]::IsNullOrEmpty($OllamaUrl)) { $OllamaUrl = $defaultUrl }
}
$OllamaUrl = $OllamaUrl.TrimEnd('/')

$models = @()
try {
    $tags = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -TimeoutSec 8
    $models = @($tags.models | ForEach-Object { $_.name } | Where-Object { $_ })
    Write-Ok "Ollama reachable at $OllamaUrl"
} catch {
    Write-Warn2 "Could not reach Ollama at $OllamaUrl (is 'ollama serve' running?)."
}

if ([string]::IsNullOrEmpty($Model)) {
    if ($models.Count -gt 0) {
        Write-Host "Installed models:"
        for ($i = 0; $i -lt $models.Count; $i++) { Write-Host ("  {0}) {1}" -f ($i + 1), $models[$i]) }
        $pick = Read-Host "Choose a model [1]"
        if ([string]::IsNullOrEmpty($pick)) { $pick = "1" }
        $index = [int]$pick - 1
        if ($index -ge 0 -and $index -lt $models.Count) { $Model = $models[$index] }
    } else {
        $Model = Read-Host "Model name (you can change it later with 'ai s')"
    }
}

$config = [ordered]@{
    ollama_url        = $OllamaUrl
    model             = $Model
    persona_name      = "ai"
    ui_backend        = "rich"
    history_size      = 4
    verbose_default   = $false
    think             = $false
    telemetry_enabled = $false
    no_color          = $false
}
$json = $config | ConvertTo-Json
# Write UTF-8 without BOM so the Python config reader parses it cleanly.
[System.IO.File]::WriteAllText($ConfigPath, $json, (New-Object System.Text.UTF8Encoding($false)))
Write-Ok "Wrote config: $ConfigPath"

Write-Host ""
Write-Ok "ai-sys-buddy installed."
Write-Host '  Command : ai "how do I check disk usage?"'
Write-Host "  Settings: ai s"
Write-Host "  Note    : open a NEW terminal so the PATH change takes effect."

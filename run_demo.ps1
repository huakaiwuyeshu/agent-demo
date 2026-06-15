param(
    [string]$Version = "all",
    [string]$Scenario = "complete",
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Find-Python {
    $candidates = @("python", "py")
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $candidate
        }
    }
    throw "Python was not found. Please install Python or add it to PATH."
}

$python = Find-Python

Write-Host ""
Write-Host "API Agent multi-version demo" -ForegroundColor Cyan
Write-Host "Directory: $scriptDir"
Write-Host "Version: $Version"
Write-Host "Scenario: $Scenario"
Write-Host ""

$argsList = @("app.py", "--version", $Version, "--scenario", $Scenario)
if ($Message.Trim().Length -gt 0) {
    $argsList += @("--message", $Message)
}

& $python @argsList

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

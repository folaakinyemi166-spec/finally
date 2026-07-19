# Build (if needed) and run the FinAlly container (PLAN.md §11).
# Usage: scripts\start_windows.ps1 [-Build]
param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$ImageName = "finally"
$ContainerName = "finally"
$Port = 8000

if (-not (Test-Path ".env")) {
    Write-Error "No .env file found. Copy .env.example to .env and set OPENROUTER_API_KEY first."
    exit 1
}

New-Item -ItemType Directory -Force -Path "db" | Out-Null

$imageExists = docker image inspect $ImageName 2>$null
if ($Build -or -not $imageExists) {
    Write-Host "Building $ImageName image..."
    docker build -t $ImageName .
}

$existing = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$ContainerName$"
if ($existing) {
    Write-Host "Removing existing $ContainerName container..."
    docker rm -f $ContainerName | Out-Null
}

docker run -d `
    --name $ContainerName `
    -p "${Port}:8000" `
    -v "${PWD}\db:/app/db" `
    --env-file .env `
    $ImageName

Write-Host "FinAlly is running at http://localhost:$Port"
Start-Sleep -Seconds 1
Start-Process "http://localhost:$Port"

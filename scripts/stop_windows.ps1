# Stop and remove the FinAlly container. Does NOT remove db\finally.db —
# your portfolio/watchlist/trade history is preserved (PLAN.md §11).
$ErrorActionPreference = "Stop"

$ContainerName = "finally"

$existing = docker ps -a --format '{{.Names}}' | Select-String -Pattern "^$ContainerName$"
if ($existing) {
    Write-Host "Stopping and removing $ContainerName..."
    docker rm -f $ContainerName | Out-Null
    Write-Host "Stopped. Your data in db\finally.db is preserved."
} else {
    Write-Host "$ContainerName is not running."
}

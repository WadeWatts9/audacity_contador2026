param (
    [string]$BackupDir = ".\backups"
)

if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $BackupDir "audacity_backup_$timestamp.sql"

Write-Host "Iniciando respaldo de base de datos Audacity..." -ForegroundColor Cyan
docker compose exec -T db pg_dump -U audacity_user -d audacity_db > $backupFile

if (Test-Path $backupFile) {
    $size = (Get-Item $backupFile).Length
    Write-Host "Respaldo completado exitosamente: $backupFile ($size bytes)" -ForegroundColor Green
} else {
    Write-Host "Error: No se pudo generar el archivo de respaldo." -ForegroundColor Red
}

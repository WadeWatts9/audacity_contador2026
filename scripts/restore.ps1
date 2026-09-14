param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile
)

if (-not (Test-Path $BackupFile)) {
    Write-Host "Error: No se encontró el archivo de respaldo en '$BackupFile'" -ForegroundColor Red
    exit 1
}

Write-Host "ADVERTENCIA: Esto restaurará la base de datos Audacity desde '$BackupFile'" -ForegroundColor Yellow
$confirm = Read-Host "¿Desea continuar? (S/N)"
if ($confirm -ne "S" -and $confirm -ne "s") {
    Write-Host "Operación cancelada por el usuario." -ForegroundColor Gray
    exit 0
}

Write-Host "Restaurando base de datos..." -ForegroundColor Cyan
Get-Content $BackupFile | docker compose exec -T db psql -U audacity_user -d audacity_db

Write-Host "Restauración completada exitosamente." -ForegroundColor Green

param(
    [switch]$StopRabbit
)

$ErrorActionPreference = "Continue"

Write-Host "Buscando procesos de SmartAudit..."

$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and
    $_.CommandLine -like "*SmartAudit*" -and
    (
        $_.CommandLine -like "*main:app*--reload*" -or
        $_.CommandLine -like "*rabbitMq.worker*" -or
        $_.CommandLine -like "*npm*run*dev*" -or
        $_.CommandLine -like "*vite*"
    )
}

if (-not $targets) {
    Write-Host "No habia procesos SmartAudit activos."
}
else {
    foreach ($p in $targets) {
        try {
            Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
            Write-Host ("Detenido PID " + $p.ProcessId)
        }
        catch {
            Write-Host ("No se pudo detener PID " + $p.ProcessId + ": " + $_.Exception.Message)
        }
    }
}

if ($StopRabbit) {
    Write-Host "Intentando parar RabbitMQ..."
    docker stop smartaudit-rabbitmq *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "RabbitMQ detenido."
    }
    else {
        Write-Host "No se pudo detener RabbitMQ o no estaba en ejecucion."
    }
}

Write-Host "Fin."

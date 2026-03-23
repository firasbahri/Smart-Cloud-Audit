param(
    [switch]$InstallFrontendDeps,
    [switch]$OpenServiceWindows,
    [switch]$RunInBackground,
    [string]$RabbitContainerName = "smartaudit-rabbitmq",
    [int]$RabbitAmqpPort = 5672,
    [int]$RabbitManagementPort = 15672,
    [string]$LogsDirectory = "logs"
)

$ErrorActionPreference = "Continue"

# Prevent native command stderr (e.g., Docker warnings) from being promoted to terminating errors.
$PSNativeCommandUseErrorActionPreference = $false

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "Backend"
$frontendPath = Join-Path $projectRoot "Frontend/smart-audit-frontend"
$venvActivate = Join-Path $backendPath "venv/Scripts/Activate.ps1"
$pythonExe = Join-Path $backendPath "venv/Scripts/python.exe"
$logsPath = Join-Path $projectRoot $LogsDirectory

if (-not (Test-Path $backendPath)) {
    throw "No se encontro la carpeta Backend en: $backendPath"
}

if (-not (Test-Path $frontendPath)) {
    throw "No se encontro la carpeta Frontend en: $frontendPath"
}

if (-not (Test-Path $venvActivate)) {
    throw "No se encontro el entorno virtual en: $venvActivate"
}

if (-not (Test-Path $pythonExe)) {
    throw "No se encontro python del entorno virtual en: $pythonExe"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI no esta disponible en PATH. Instala Docker Desktop o agrega docker al PATH."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm no esta disponible en PATH. Instala Node.js o agrega npm al PATH."
}

if (-not (Test-Path $logsPath)) {
    New-Item -ItemType Directory -Path $logsPath | Out-Null
}

function Wait-ForDocker {
    param(
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        docker info 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Start-Sleep -Seconds 3
    }
    return $false
}

Write-Host "Verificando Docker daemon..."
docker info 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker no responde. Intentando abrir Docker Desktop..."
    $dockerDesktopPaths = @(
        "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "$Env:ProgramFiles(x86)\Docker\Docker\Docker Desktop.exe"
    )

    $launched = $false
    foreach ($path in $dockerDesktopPaths) {
        if (Test-Path $path) {
            Start-Process -FilePath $path
            $launched = $true
            break
        }
    }

    if (-not $launched) {
        Write-Host "No se encontro Docker Desktop.exe en rutas comunes."
    }

    if (-not (Wait-ForDocker -TimeoutSeconds 150)) {
        throw "Docker daemon no esta disponible tras esperar. Abre Docker Desktop manualmente e intenta de nuevo."
    }
}

Write-Host "Docker activo. Verificando contenedor RabbitMQ..."
$existingRabbit = docker ps -a --filter "name=^/$RabbitContainerName$" --format "{{.Names}}"

if ($existingRabbit -eq $RabbitContainerName) {
    $isRunning = docker ps --filter "name=^/$RabbitContainerName$" --format "{{.Names}}"
    if ($isRunning -ne $RabbitContainerName) {
        Write-Host "Iniciando contenedor RabbitMQ existente: $RabbitContainerName"
        docker start $RabbitContainerName *> $null
    }
    else {
        Write-Host "Contenedor RabbitMQ ya estaba en ejecucion: $RabbitContainerName"
    }
}
else {
    Write-Host "Creando y arrancando contenedor RabbitMQ: $RabbitContainerName"
    docker run -d --name $RabbitContainerName --restart unless-stopped -p ${RabbitAmqpPort}:5672 -p ${RabbitManagementPort}:15672 rabbitmq:3-management *> $null
}

Write-Host "Esperando a que RabbitMQ termine de iniciar..."
Start-Sleep -Seconds 8

if ($InstallFrontendDeps) {
    Write-Host "Instalando dependencias del frontend..."
    Push-Location $frontendPath
    try {
        npm install
    }
    finally {
        Pop-Location
    }
}

if ($OpenServiceWindows) {
    Write-Host "Iniciando backend (uvicorn) en ventana separada..."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$backendPath'; . '$venvActivate'; uvicorn main:app --reload"
    )

    Write-Host "Iniciando worker RabbitMQ en ventana separada..."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$backendPath'; . '$venvActivate'; python -m rabbitMq.worker"
    )

    Write-Host "Iniciando frontend (Vite) en ventana separada..."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$frontendPath'; npm run dev"
    )

    Write-Host "Servicios lanzados en ventanas separadas."
    Write-Host "0) Docker + RabbitMQ"
    Write-Host "1) Backend (uvicorn)"
    Write-Host "2) Worker RabbitMQ"
    Write-Host "3) Frontend (npm run dev)"
}
elseif ($RunInBackground) {
    $backendLog = Join-Path $logsPath "backend.log"
    $workerLog = Join-Path $logsPath "worker.log"
    $frontendLog = Join-Path $logsPath "frontend.log"

    Write-Host "Iniciando backend (uvicorn) en segundo plano..."
    $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @("-m", "uvicorn", "main:app", "--reload") -WorkingDirectory $backendPath -RedirectStandardOutput $backendLog -RedirectStandardError $backendLog -PassThru

    Write-Host "Iniciando worker RabbitMQ en segundo plano..."
    $workerProcess = Start-Process -FilePath $pythonExe -ArgumentList @("-m", "rabbitMq.worker") -WorkingDirectory $backendPath -RedirectStandardOutput $workerLog -RedirectStandardError $workerLog -PassThru

    Write-Host "Iniciando frontend (Vite) en segundo plano..."
    $frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev") -WorkingDirectory $frontendPath -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendLog -PassThru

    Write-Host "Servicios iniciados en segundo plano. Puedes cerrar esta terminal de VS Code."
    Write-Host "Logs en: $logsPath"
    Write-Host "Backend PID: $($backendProcess.Id)"
    Write-Host "Worker PID: $($workerProcess.Id)"
    Write-Host "Frontend PID: $($frontendProcess.Id)"
    Write-Host "Para ver logs: Get-Content '$backendLog' -Wait"
}
else {
    Write-Host "Iniciando backend (uvicorn) en la terminal integrada de VS Code..."
    $backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @("-m", "uvicorn", "main:app", "--reload") -WorkingDirectory $backendPath -NoNewWindow -PassThru

    Write-Host "Iniciando worker RabbitMQ en la terminal integrada de VS Code..."
    $workerProcess = Start-Process -FilePath $pythonExe -ArgumentList @("-m", "rabbitMq.worker") -WorkingDirectory $backendPath -NoNewWindow -PassThru

    Write-Host "Iniciando frontend (Vite) en la terminal integrada de VS Code..."
    $frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList @("run", "dev") -WorkingDirectory $frontendPath -NoNewWindow -PassThru

    Write-Host "Servicios iniciados en esta terminal de VS Code."
    Write-Host "Backend PID: $($backendProcess.Id)"
    Write-Host "Worker PID: $($workerProcess.Id)"
    Write-Host "Frontend PID: $($frontendProcess.Id)"
    Write-Host "Si quieres desacoplarlos y poder cerrar la terminal, usa: -RunInBackground"
}
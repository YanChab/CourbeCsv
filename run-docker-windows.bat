@echo off
REM Script to run the application with Docker on Windows
REM Requires VcXsrv or Xming installed

echo ============================================
echo Visualiseur CSV - Docker Windows Launcher
echo ============================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas en cours d'execution.
    echo Veuillez demarrer Docker Desktop et reessayer.
    pause
    exit /b 1
)

REM Get host IP address for X11 display
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do set HOST_IP=%%b
    goto :found_ip
)
:found_ip

echo [INFO] Adresse IP detectee: %HOST_IP%
echo.

REM Set DISPLAY environment variable
set DISPLAY=%HOST_IP%:0.0

echo [INFO] DISPLAY configure sur: %DISPLAY%
echo.
echo [IMPORTANT] Assurez-vous que VcXsrv ou Xming est lance avec:
echo   - "Disable access control" coche
echo   - Display number: 0
echo.

REM Build and run
echo [INFO] Construction et lancement du conteneur...
docker-compose up --build

pause

@echo off
cd /d "%~dp0"
echo Stopping Ragatouille services with Docker Compose...
docker-compose down
if %errorlevel% equ 0 (
    echo Ragatouille services stopped successfully.
) else (
    echo Failed to stop Ragatouille services. Please check the logs above for errors.
)
pause
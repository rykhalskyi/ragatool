@echo off
cd /d "%~dp0"
echo Starting Ragatouille services with Docker Compose...
docker-compose up -d
if %errorlevel% equ 0 (
    echo Ragatouille services started successfully.
    echo Frontend will be available at http://localhost:4300
    echo Backend will be available at http://localhost:4301
    echo MCP server wil be available at http://localhost:4302	
) else (
    echo Failed to start Ragatouille services. Please check the logs above for errors.
)
pause
@echo off
REM Create a ZIP archive of the scripts folder
REM This script uses PowerShell to compress the scripts directory

setlocal enabledelayedexpansion



REM Get the current directory
set "source_dir=%cd%\write"
set "output_file=%cd%\ragatouille-write.zip"

REM Check if scripts folder exists
if not exist "%source_dir%" (
    echo Error: scripts folder not found at %source_dir%
    exit /b 1
)

REM Remove existing zip file if it exists
if exist "%output_file%" (
    echo Removing existing scripts.zip...
    del "%output_file%"
)

REM Create the ZIP archive using PowerShell
echo Creating ZIP archive: %output_file%
powershell -Command "Compress-Archive -Path '%source_dir%' -DestinationPath '%output_file%' -Force"

if %errorlevel% equ 0 (
    echo Success! ZIP archive created: %output_file%

	if exist "ragatouille-write.plugin" (
	echo Removing existing ragatouille-write.plugin
		del "ragatouille-write.plugin"
	)	
	
    REM Rename the zip file to .zip2
    ren "%output_file%" "ragatouille-write.plugin"
    
    if exist "ragatouille-write.plugin" (
        echo Renamed to: ragatouille-write.plugin
    ) else (
        echo Error: Failed to rename ZIP file
        exit /b 1
    )
) else (
    echo.
    echo Error: Failed to create ZIP archive
    exit /b 1
)

endlocal

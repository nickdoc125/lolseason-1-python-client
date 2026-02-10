@echo off
chcp 65001 >nul
title Children of the Grave - Extract Client Data
setlocal enabledelayedexpansion

echo ========================================
echo    CLIENT DATA EXTRACTION
echo ========================================
echo.

cd /d "%~dp0"

set "ARCHIVE_PATH=playable_client_126.7z"
set "MODDED_LEVELS_PATH=modded_levels_paste_on_client.7z"
set "EXTRACT_PATH=..\Fishbones_Data"
set "SEVENZR_PATH=7zr.exe"

echo Checking 7zr...
if not exist "%SEVENZR_PATH%" (
    echo ERROR: 7zr.exe not found at: %SEVENZR_PATH%
    echo Download from: https://www.7-zip.org/download.html
    goto :error
)

echo Checking archives...
if not exist "%ARCHIVE_PATH%" (
    echo ERROR: Archive file not found at: %ARCHIVE_PATH%
    goto :error
)

if not exist "%MODDED_LEVELS_PATH%" (
    echo ERROR: Modded levels archive not found at: %MODDED_LEVELS_PATH%
    goto :error
)

echo Using portable 7zr.exe
echo Starting extraction...

if not exist "%EXTRACT_PATH%" mkdir "%EXTRACT_PATH%"

set /a SUCCESS_COUNT=0

echo Extracting main client data...
"%SEVENZR_PATH%" x "%ARCHIVE_PATH%" -o"%EXTRACT_PATH%" -y
if !errorlevel! equ 0 (
    echo Main client extraction completed successfully!
    set /a SUCCESS_COUNT+=1
) else (
    echo Main client extraction failed!
    goto :error
)

echo.

echo Extracting modded levels...
"%SEVENZR_PATH%" x "%MODDED_LEVELS_PATH%" -o"%EXTRACT_PATH%" -y
if !errorlevel! equ 0 (
    echo Modded levels extraction completed successfully!
    set /a SUCCESS_COUNT+=1
    
    echo.
    echo Moving modded levels to client directory...
    
    rem Check if source directory exists
    if exist "..\Fishbones_Data\modded_levels_paste_on_client\LEVELS" (
        rem Create destination directory if it doesn't exist
        if not exist "..\Fishbones_Data\playable_client_126\LEVELS" (
            mkdir "..\Fishbones_Data\playable_client_126\LEVELS"
        )
        
        rem Copy and then delete (more reliable than /MOVE)
        xcopy "..\Fishbones_Data\modded_levels_paste_on_client\LEVELS" "..\Fishbones_Data\playable_client_126\LEVELS" /E /I /Y
        if !errorlevel! equ 0 (
            echo Files copied successfully, removing source...
            rmdir "..\Fishbones_Data\modded_levels_paste_on_client\LEVELS" /S /Q
            rmdir "..\Fishbones_Data\modded_levels_paste_on_client" /S /Q
            echo Cleanup completed!
        ) else (
            echo ERROR: Failed to copy modded levels!
        )
    ) else (
        echo ERROR: Source modded levels directory not found!
    )
) else (
    echo Modded levels extraction failed!
    goto :error
)

if !SUCCESS_COUNT! equ 2 (
    echo.
    echo ========================================
    echo    EXTRACTION SUCCESSFUL!
    echo Both archives extracted successfully!
    echo ========================================
    echo.
    echo Files extracted to: %EXTRACT_PATH%
    exit /b 0
) else (
    echo.
    echo ========================================
    echo    EXTRACTION PARTIALLY FAILED!
    echo    !SUCCESS_COUNT! out of 2 archives extracted
    echo ========================================
    echo.
    exit /b 1
)

:error
echo.
echo ========================================
echo    EXTRACTION FAILED!
echo ========================================
echo.
exit /b 1
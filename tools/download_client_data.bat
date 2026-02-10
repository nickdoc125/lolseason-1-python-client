@echo off
chcp 65001 >nul
title Children of the Grave - Download Client Data
setlocal enabledelayedexpansion

echo ========================================
echo    CLIENT DATA DOWNLOAD
echo ========================================
echo.

cd /d "%~dp0"

set "MEGATOOLS_PATH=megatools\megatools.exe"
set "DOWNLOAD_DIR=..\tools"

echo Checking megatools...
if not exist "%MEGATOOLS_PATH%" (
    echo ERROR: megatools not found at: %MEGATOOLS_PATH%
    goto :error
)

if not exist "%DOWNLOAD_DIR%" mkdir "%DOWNLOAD_DIR%"

echo Download directory: %DOWNLOAD_DIR%
echo.

set "URL1=https://mega.nz/file/uqRmkCKC#nJFZ2hAYqTq5q-T1PExXPpu0aX4ALjjZj2SZ4q9yCpk"
set "URL2=https://mega.nz/file/ruZDDKTB#XNxrd3gr2GdxhqYPdgAWG2dT4sxBv9Q1mzMT1M-rjLc"

set /a SUCCESS_COUNT=0

echo Downloading File 1/2...
echo URL: %URL1%
echo Progress: [
"%MEGATOOLS_PATH%" dl --path "%DOWNLOAD_DIR%" "%URL1%"
if !errorlevel! equ 0 (
    echo ] 100%%
    echo Completed successfully!
    set /a SUCCESS_COUNT+=1
) else (
    echo ] FAILED
    echo Error downloading file 1
)

echo.

echo Downloading File 2/2...
echo URL: %URL2%
echo Progress: [
"%MEGATOOLS_PATH%" dl --path "%DOWNLOAD_DIR%" "%URL2%"
if !errorlevel! equ 0 (
    echo ] 100%%
    echo Completed successfully!
    set /a SUCCESS_COUNT+=1
) else (
    echo ] FAILED
    echo Error downloading file 2
)

if !SUCCESS_COUNT! equ 2 (
    echo.
    echo ========================================
    echo    DOWNLOAD SUCCESSFUL!
    echo ========================================
    echo.
    exit /b 0
) else (
    echo.
    echo ========================================
    echo    DOWNLOAD PARTIALLY FAILED!
    echo    !SUCCESS_COUNT! out of 2 files downloaded
    echo ========================================
    echo.
    exit /b 1
)

:error
echo.
echo ========================================
echo    DOWNLOAD FAILED!
echo ========================================
echo.
exit /b 1
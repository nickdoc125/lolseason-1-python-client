@echo off
chcp 65001 >nul
title Children of the Grave - Server Update
setlocal enabledelayedexpansion

echo ========================================
echo    SERVER UPDATE TOOL
echo ========================================
echo.

cd /d "%~dp0"

set "GIT_EXE=PortableGit\bin\git.exe"
set "REPO_URL=https://gitgud.io/skelsoft/brokenwings.git"
set "TARGET=..\Fishbones_Data\ChildrenOfTheGrave-Gameserver"

echo Checking Git...
if not exist "%GIT_EXE%" (
    echo ERROR: Git not found at: %GIT_EXE%
    goto :error
)

set /a ATTEMPT=1
set /a MAX_ATTEMPTS=2

:retry
echo.
echo Attempt !ATTEMPT! of !MAX_ATTEMPTS!
echo ===============================

if not exist "%TARGET%" (
    echo No existing directory found
    echo Cloning repository...
    "%GIT_EXE%" clone "%REPO_URL%" "%TARGET%"
    if !errorlevel! equ 0 (
        echo Clone completed successfully!
        goto :success
    ) else (
        echo Clone failed!
        goto :next_attempt
    )
)

echo Existing directory found
if exist "%TARGET%\.git" (
    echo Git repository detected
    echo Updating repository...
    "%GIT_EXE%" -C "%TARGET%" pull
    if !errorlevel! equ 0 (
        echo Update completed successfully!
        goto :success
    ) else (
        echo Update failed - Trying fresh clone...
    )
) else (
    echo Directory is not a git repository
)

echo Deleting existing directory...
rmdir /s /q "%TARGET%" 2>nul
if exist "%TARGET%" (
    echo ERROR: Could not delete directory
    goto :next_attempt
)

echo Delete completed!
echo Cloning repository...
"%GIT_EXE%" clone "%REPO_URL%" "%TARGET%"
if !errorlevel! equ 0 (
    echo Clone completed successfully!
    goto :success
)

:next_attempt
if !ATTEMPT! lss !MAX_ATTEMPTS! (
    set /a ATTEMPT+=1
    echo Retrying in 5 seconds...
    timeout /t 5 /nobreak >nul
    goto :retry
)

:error
echo.
echo ========================================
echo    UPDATE FAILED!
echo ========================================
echo.
echo Troubleshooting suggestions:
echo 1. Check internet connection
echo 2. Make sure no files are open from the folder
echo 3. Try running as Administrator
echo 4. Manually delete the folder: %TARGET%
echo.
exit /b 1

:success
echo.
echo ========================================
echo    UPDATE SUCCESSFUL!
echo ========================================
echo.
exit /b 0
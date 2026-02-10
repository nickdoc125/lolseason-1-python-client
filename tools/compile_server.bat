@echo off
chcp 65001 >nul
title Children of the Grave - Server Compilation
setlocal enabledelayedexpansion

echo ========================================
echo    SERVER COMPILATION TOOL
echo ========================================
echo.

cd /d "%~dp0"

set "SOLUTION_PATH=..\Fishbones_Data\ChildrenOfTheGrave-Gameserver\ChildrenOfTheGraveServer.sln"
set "DOTNET_PATH=dotnet\dotnet.exe"

echo Checking prerequisites...
if not exist "%SOLUTION_PATH%" (
    echo ERROR: Solution file not found at: %SOLUTION_PATH%
    goto :error
)

if not exist "%DOTNET_PATH%" (
    echo ERROR: Dotnet executable not found at: %DOTNET_PATH%
    goto :error
)

echo SUCCESS: All prerequisites found!
echo.

echo STEP 1: Restoring NuGet packages...
echo Restoring...
"%DOTNET_PATH%" restore "%SOLUTION_PATH%"
if !errorlevel! neq 0 (
    echo ERROR: Package restoration failed!
    goto :error
)
echo SUCCESS: Dependencies restored successfully!
echo.

echo STEP 2: Compiling project...
echo Compiling...
"%DOTNET_PATH%" build "%SOLUTION_PATH%" --configuration Debug
if !errorlevel! neq 0 (
    echo ERROR: Build failed!
    goto :error
)

echo SUCCESS: Build completed successfully!
echo.
echo ========================================
echo    COMPILATION SUCCESSFUL!
echo    Ready to launch server!
echo ========================================
echo.
exit /b 0

:error
echo.
echo ========================================
echo    COMPILATION FAILED!
echo    Please check the errors above
echo ========================================
echo.
exit /b 1
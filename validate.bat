@echo off
echo ========================================
echo PowerShell Check
echo ========================================
echo.

echo Checking for PowerShell 7...
where pwsh
if %ERRORLEVEL% EQU 0 (
    echo Found PowerShell 7!
    pwsh --version
) else (
    echo PowerShell 7 not found in PATH
    echo.
    echo Checking default installation location...
    if exist "C:\Program Files\PowerShell\7\pwsh.exe" (
        echo Found at: C:\Program Files\PowerShell\7\pwsh.exe
        echo Please restart your terminal to update PATH
    ) else (
        echo Not found. Please install from: https://aka.ms/powershell
    )
)

echo.
echo ========================================
echo Python Check
echo ========================================
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found
    exit /b 1
)

echo.
echo ========================================
echo Running API Tests
echo ========================================
python test_api_endpoints.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: All tests passed!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo FAILED: Tests encountered errors
    echo ========================================
    exit /b 1
)

@echo off
REM Quick test runner for OpenEnv API validation
REM This script runs the API endpoint tests

echo ==================================================
echo OpenEnv Email Triage - API Validation Tests
echo ==================================================
echo.

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)
echo.

echo Installing dependencies (if needed)...
pip install -q -r requirements.txt
echo.

echo Running API endpoint tests...
python test_api_endpoints.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Tests failed!
    exit /b 1
)

echo.
echo ==================================================
echo All tests passed successfully!
echo ==================================================
echo.
echo Next steps:
echo 1. Test Docker build: docker build -t openenv-email-triage .
echo 2. Run container: docker run -p 7860:7860 openenv-email-triage
echo 3. Push to HuggingFace Space
echo 4. Run 'openenv validate'
echo.

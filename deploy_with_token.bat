@echo off
REM ============================================
REM HuggingFace Deployment - Copy Your Token
REM ============================================

echo.
echo ============================================
echo DEPLOYING TO HUGGINGFACE SPACE
echo ============================================
echo.
echo You have your token ready! Great!
echo.
echo This will deploy your fixed code to HuggingFace.
echo.

REM Prompt for token
set /p TOKEN="Paste your HuggingFace token here (starts with hf_): "

if "%TOKEN%"=="" (
    echo ERROR: No token provided
    pause
    exit /b 1
)

echo.
echo Deploying with token...
echo.

REM Use the token in the git URL
git push https://oauth2:%TOKEN%@huggingface.co/spaces/openenv/openenv-email-triage main

if errorlevel 1 (
    echo.
    echo ========================================
    echo DEPLOYMENT FAILED
    echo ========================================
    echo.
    echo Possible issues:
    echo   1. Space doesn't exist: openenv/openenv-email-triage
    echo   2. You don't have access to that organization
    echo   3. Token doesn't have write permissions
    echo.
    echo SOLUTION: Create your own Space
    echo   1. Go to: https://huggingface.co/new-space
    echo   2. Name: openenv-email-triage
    echo   3. SDK: Docker
    echo   4. Visibility: Public
    echo   5. Then run this script again with your username:
    echo.
    set /p USERNAME="Enter your HuggingFace username: "
    echo.
    echo Deploying to your Space...
    git remote set-url huggingface https://huggingface.co/spaces/%USERNAME%/openenv-email-triage
    git push https://oauth2:%TOKEN%@huggingface.co/spaces/%USERNAME%/openenv-email-triage main
    
    if errorlevel 1 (
        echo.
        echo Still failed. Please check:
        echo   - Space exists at: https://huggingface.co/spaces/%USERNAME%/openenv-email-triage
        echo   - Token has WRITE permissions
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo SUCCESS! CODE DEPLOYED TO HUGGINGFACE
echo ========================================
echo.
echo Next steps:
echo   1. Go to your Space and wait for build (2-5 min)
echo   2. Check build logs for "Application startup complete"
echo   3. Test the endpoint:
echo.
echo      curl -X POST https://YOUR_SPACE.hf.space/reset
echo.
echo   4. Should return: {"status":"ok",...}
echo   5. Run: openenv validate openenv-email-triage
echo   6. Resubmit Phase 1 - Will PASS!
echo.
pause

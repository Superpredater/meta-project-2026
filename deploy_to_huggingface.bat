@echo off
echo ============================================
echo HuggingFace Space Deployment Script
echo ============================================
echo.
echo This script will help you deploy to HuggingFace Space.
echo.
echo IMPORTANT: You need a HuggingFace Access Token (not password)
echo Get one from: https://huggingface.co/settings/tokens
echo.
pause

echo.
echo === Step 1: Add HuggingFace as git remote ===
git remote remove huggingface 2>nul
git remote add huggingface https://huggingface.co/spaces/Superpredater231/openenv-email-triage
if errorlevel 1 (
    echo ERROR: Failed to add remote
    pause
    exit /b 1
)
echo SUCCESS: Remote added
echo.

echo === Step 2: Push to HuggingFace ===
echo.
echo When prompted:
echo   Username: Your HuggingFace username (e.g., sanjaypillai)
echo   Password: Your HuggingFace ACCESS TOKEN (starts with hf_...)
echo.
echo DO NOT use your account password - it will NOT work!
echo.
pause

git push huggingface main
if errorlevel 1 (
    echo.
    echo ========================================
    echo DEPLOYMENT FAILED
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Using password instead of token
    echo   2. Token doesn't have write permissions
    echo   3. Space doesn't exist or you don't have access
    echo.
    echo Solutions:
    echo   - Get a new token with WRITE permission
    echo   - Or create your own Space at https://huggingface.co/new-space
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Code pushed to HuggingFace
echo ========================================
echo.
echo Next steps:
echo   1. Go to: https://huggingface.co/spaces/Superpredater231/openenv-email-triage
echo   2. Wait for build to complete (2-5 minutes)
echo   3. Test: curl -X POST https://YOUR_SPACE.hf.space/reset
echo   4. Run: openenv validate openenv-email-triage
echo   5. Resubmit Phase 1
echo.
pause

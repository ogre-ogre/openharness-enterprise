@echo off
echo ========================================
echo OpenHarness Enterprise - Frontend Dev
echo ========================================
echo.

cd /d D:\openharness-enterprise\web

echo [1/2] Installing npm dependencies...
call npm install

echo.
echo [2/2] Starting dev server...
echo Frontend will be available at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server.
echo ========================================

call npm run dev
@echo off
echo ========================================
echo OpenHarness Enterprise - Start Script
echo ========================================
echo.

cd /d D:\openharness-enterprise

echo [1/2] Installing Python dependencies...
uv sync --extra dev

echo.
echo [2/2] Starting server...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo ========================================

uv run oh-enterprise start --port 8000
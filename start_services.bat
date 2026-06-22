@echo off
echo ========================================
echo Starting Agent Demo Services
echo ========================================
echo.

:: Kill existing Python processes on ports 8080 and 8081
echo [1/3] Stopping existing services...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8081') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul

:: Start LLM Proxy
echo [2/3] Starting LLM Proxy (port 8081)...
start "LLM Proxy" cmd /c "cd web && python proxy.py"
timeout /t 2 /nobreak >nul

:: Start Web Server
echo [3/3] Starting Web Server (port 8080)...
start "Web Server" cmd /c "cd web && python -m http.server 8080"
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo Services started successfully!
echo ========================================
echo.
echo Web Demo:      http://127.0.0.1:8080/
echo LLM Proxy:     http://127.0.0.1:8081/
echo.
echo Press any key to open browser...
pause >nul

start http://127.0.0.1:8080/

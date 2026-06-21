@echo off
echo Starting LLM proxy on port 8081...
start /b python "%~dp0web\proxy.py"
timeout /t 1 /nobreak >nul
echo Starting web server on port 8080...
start /b python -m http.server 8080 --directory "%~dp0web"
timeout /t 1 /nobreak >nul
echo Opening browser...
start "" "http://localhost:8080/"
echo.
echo Agent Demo is running:
echo   Web UI:    http://localhost:8080/
echo   LLM Proxy: http://127.0.0.1:8081/
echo.
echo Press Ctrl+C to stop.
pause >nul

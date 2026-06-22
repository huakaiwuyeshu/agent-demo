@echo off
echo ========================================
echo Stopping Agent Demo Services
echo ========================================
echo.

echo Stopping services on ports 8080 and 8081...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
    echo Killing process %%a on port 8080
    taskkill /F /PID %%a
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8081') do (
    echo Killing process %%a on port 8081
    taskkill /F /PID %%a
)

echo.
echo Services stopped successfully!
echo.
pause

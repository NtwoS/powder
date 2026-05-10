@echo off
chcp 65001 >nul 2>&1
title Diana AI - Shutdown
color 0C

echo.
echo  +==============================================+
echo  ^|       MEMATIKAN DIANA AI...                  ^|
echo  +==============================================+
echo.

:: Kill Backend (Python di port 5050)
echo  [*] Menghentikan Backend (Port 5050)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
    echo      PID %%a dihentikan.
)

:: Kill Frontend (Node di port 4321)
echo  [*] Menghentikan Frontend (Port 4321)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":4321" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
    echo      PID %%a dihentikan.
)

:: Kill semua jendela CMD Diana yang terbuka
echo  [*] Menutup jendela Diana...
taskkill /FI "WINDOWTITLE eq Diana AI - Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Diana AI - Frontend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Diana AI - Master Launcher" /F >nul 2>&1

echo.
echo  +==============================================+
echo  ^|       DIANA AI BERHASIL DIMATIKAN            ^|
echo  ^|                                              ^|
echo  ^|  Backend  : Stopped                          ^|
echo  ^|  Frontend : Stopped                          ^|
echo  ^|                                              ^|
echo  ^|  Untuk menyalakan kembali: run_diana.bat     ^|
echo  +==============================================+
echo.
timeout /t 5
exit

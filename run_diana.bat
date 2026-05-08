@echo off
chcp 65001 >nul 2>&1
title Diana AI - Master Launcher
color 0B

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║         DIANA AI - MASTER LAUNCHER           ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: Simpan lokasi awal
set "ROOT_DIR=%~dp0"

:: ============================================
:: LANGKAH 1: CEK DEPENDENCIES
:: ============================================
echo  [*] Memeriksa dependencies...
echo.

:: Cek Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python tidak ditemukan! Install Python terlebih dahulu.
    echo  Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python ditemukan.

:: Cek Node.js
node --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Node.js tidak ditemukan! Install Node.js terlebih dahulu.
    echo  Download: https://nodejs.org/
    pause
    exit /b 1
)
echo  [OK] Node.js ditemukan.

:: Install pip dependencies
echo  [*] Menginstall Python dependencies...
pip install -r "%ROOT_DIR%requirements.txt" --quiet 2>nul
echo  [OK] Python dependencies siap.

:: Install npm dependencies jika belum
if not exist "%ROOT_DIR%frontend\node_modules\" (
    echo  [*] Menginstall Frontend dependencies (pertama kali)...
    cd /d "%ROOT_DIR%frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)
echo  [OK] Frontend dependencies siap.
echo.

:: ============================================
:: LANGKAH 2: MATIKAN PROSES LAMA (jika ada)
:: ============================================
echo  [*] Membersihkan proses lama...
:: Kill proses python di port 5050 jika ada
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5050" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
:: Kill proses node di port 4321 jika ada  
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":4321" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo  [OK] Proses lama dibersihkan.
echo.

:: ============================================
:: LANGKAH 3: JALANKAN BACKEND
:: ============================================
echo  [1/2] Menyalakan Otak Diana (Backend - Port 5050)...
start "Diana AI - Backend" cmd /k "title Diana AI - Backend ^& color 0A ^& cd /d "%ROOT_DIR%backend" ^& echo. ^& echo  === BACKEND DIANA AI === ^& echo. ^& python app.py"

:: Tunggu backend siap
echo  [*] Menunggu backend siap...
timeout /t 4 /nobreak > nul

:: Cek apakah backend benar-benar jalan
echo  [*] Mengecek koneksi backend...
curl -s http://127.0.0.1:5050/status >nul 2>&1
if errorlevel 1 (
    echo  [!!] Backend belum merespon, menunggu 5 detik lagi...
    timeout /t 5 /nobreak > nul
    curl -s http://127.0.0.1:5050/status >nul 2>&1
    if errorlevel 1 (
        color 0E
        echo  [PERINGATAN] Backend mungkin belum siap. Cek jendela Backend.
    ) else (
        echo  [OK] Backend ONLINE di http://127.0.0.1:5050
    )
) else (
    echo  [OK] Backend ONLINE di http://127.0.0.1:5050
)
echo.

:: ============================================
:: LANGKAH 4: JALANKAN FRONTEND
:: ============================================
echo  [2/2] Menyalakan Antarmuka Diana (Frontend - Port 4321)...
start "Diana AI - Frontend" cmd /k "title Diana AI - Frontend ^& color 0D ^& cd /d "%ROOT_DIR%frontend" ^& echo. ^& echo  === FRONTEND DIANA AI === ^& echo. ^& npm run dev"

:: Tunggu frontend siap
echo  [*] Menunggu frontend siap...
timeout /t 5 /nobreak > nul

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║            DIANA AI STATUS MONITOR            ║
echo  ╠══════════════════════════════════════════════╣
echo  ║                                              ║
echo  ║  Backend  : http://127.0.0.1:5050            ║
echo  ║  Frontend : http://localhost:4321             ║
echo  ║                                              ║
echo  ║  Buka browser ke: http://localhost:4321       ║
echo  ║                                              ║
echo  ╠══════════════════════════════════════════════╣
echo  ║  Jendela ini HARUS TETAP TERBUKA             ║
echo  ║  Tekan CTRL+C atau tutup untuk stop Diana    ║
echo  ╚══════════════════════════════════════════════╝
echo.

:: ============================================
:: MONITORING LOOP - Jendela ini tetap terbuka
:: ============================================
:monitor
echo  [%TIME%] Mengecek status Diana...

:: Cek Backend
curl -s -o nul -w "" http://127.0.0.1:5050/status >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [%TIME%] [OFFLINE] Backend TIDAK MERESPON!
    echo             Cek jendela "Diana AI - Backend" untuk error.
) else (
    color 0B
    echo  [%TIME%] [ONLINE]  Backend OK - Frontend: http://localhost:4321
)

:: Tunggu 15 detik sebelum cek lagi
timeout /t 15 /nobreak > nul
goto monitor

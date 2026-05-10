@echo off
chcp 65001 >nul 2>&1
title Diana AI - Master Launcher
color 0B

echo.
echo  +==============================================+
echo  ^|        DIANA AI - MASTER LAUNCHER            ^|
echo  +==============================================+
echo.

:: Simpan lokasi folder ini
set "ROOT_DIR=%~dp0"

:: ============================================
:: LANGKAH 1: CEK DEPENDENCIES
:: ============================================
echo  [*] Memeriksa dependencies...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python tidak ditemukan!
    echo  Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] Python ditemukan.

node --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Node.js tidak ditemukan!
    echo  Download: https://nodejs.org/
    pause
    exit /b 1
)
echo  [OK] Node.js ditemukan.

:: Install pip dependencies
echo  [*] Menginstall Python dependencies...
pip install -r "%ROOT_DIR%requirements.txt" --quiet 2>nul
echo  [OK] Python dependencies siap.

:: Install npm dependencies jika belum ada
if not exist "%ROOT_DIR%frontend\node_modules\" (
    echo  [*] Menginstall Frontend dependencies (pertama kali, harap tunggu)...
    cd /d "%ROOT_DIR%frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)
echo  [OK] Frontend dependencies siap.
echo.

:: ============================================
:: LANGKAH 2: BERSIHKAN PROSES LAMA
:: ============================================
echo  [*] Membersihkan proses lama di port 5050 dan 4321...
powershell -NoProfile -Command ^
  "Get-NetTCPConnection -LocalPort 5050 -State Listen -EA SilentlyContinue | %% { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }; ^
   Get-NetTCPConnection -LocalPort 4321 -State Listen -EA SilentlyContinue | %% { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }" >nul 2>&1
echo  [OK] Proses lama dibersihkan.
echo.

:: ============================================
:: LANGKAH 3: JALANKAN BACKEND
:: ============================================
echo  [1/2] Menyalakan Otak Diana (Backend - Port 5050)...
start "Diana AI - Backend" cmd /c ""%ROOT_DIR%start_backend.bat""

echo  [*] Menunggu backend siap (12 detik)...
timeout /t 12 /nobreak >nul

:: Cek koneksi backend
echo  [*] Mengecek koneksi backend...
powershell -NoProfile -Command ^
  "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5050/status' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    echo  [!!] Backend belum merespon, menunggu 8 detik lagi...
    timeout /t 8 /nobreak >nul
    powershell -NoProfile -Command ^
      "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5050/status' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        color 0E
        echo  [PERINGATAN] Backend belum merespon!
        echo  Cek jendela "Diana AI - Backend" untuk melihat error Python.
    ) else (
        color 0B
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
start "Diana AI - Frontend" cmd /c ""%ROOT_DIR%start_frontend.bat""

echo  [*] Menunggu frontend siap (10 detik)...
timeout /t 10 /nobreak >nul

echo.
echo  +==============================================+
echo  ^|           DIANA AI SUDAH AKTIF!              ^|
echo  +----------------------------------------------+
echo  ^|  Backend  : http://127.0.0.1:5050            ^|
echo  ^|  Frontend : http://localhost:4321             ^|
echo  ^|                                              ^|
echo  ^|  >> Buka browser: http://localhost:4321 <<   ^|
echo  +----------------------------------------------+
echo  ^|  Jendela ini HARUS TETAP TERBUKA             ^|
echo  ^|  Tekan CTRL+C untuk stop semua               ^|
echo  +==============================================+
echo.

:: Buka browser otomatis
start "" "http://localhost:4321"

:: ============================================
:: MONITORING LOOP
:: ============================================
:monitor
echo  [%TIME%] Mengecek status Diana...

powershell -NoProfile -Command ^
  "try { Invoke-WebRequest -Uri 'http://127.0.0.1:5050/status' -UseBasicParsing -TimeoutSec 5 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    color 0C
    echo  [%TIME%] [OFFLINE] Backend tidak merespon! Cek jendela "Diana AI - Backend".
) else (
    color 0B
    echo  [%TIME%] [ONLINE]  Diana aktif - http://localhost:4321
)

timeout /t 20 /nobreak >nul
goto monitor

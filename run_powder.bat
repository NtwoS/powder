@echo off
title Powder AI - Master Launcher
echo ==========================================
echo       POWDER AI SEDANG DIJALANKAN
echo ==========================================
echo.

:: Simpan lokasi awal
set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

:: 1. Cek dependencies (Opsional tapi berguna)
echo [*] Memeriksa Otak Powder...

:: 2. Menjalankan Backend di jendela terpisah
echo [1/2] Menyalakan Otak Powder (Backend)...
start "Powder AI - Backend" cmd /k "cd /d "%ROOT_DIR%backend" && python app.py"

:: Memberikan waktu backend untuk menyala
timeout /t 5 /nobreak > nul

:: 3. Menjalankan Frontend di jendela terpisah
echo [2/2] Menyalakan Antarmuka Powder (Frontend)...
start "Powder AI - Frontend" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo.
echo ==========================================
echo   SEMUA JENDELA SUDAH DIBUKA!
echo.
echo   Jika ada jendela yang langsung tertutup:
echo   1. Pastikan Python sudah terinstall
echo   2. Jalankan: pip install -r requirements.txt
echo.
echo   Akses Powder di: http://localhost:4321
echo ==========================================
timeout /t 15
exit

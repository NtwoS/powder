@echo off
title Diana AI - Backend
color 0A
cd /d "%~dp0backend"
echo.
echo  === BACKEND DIANA AI ===
echo  Alamat: http://127.0.0.1:5050
echo.
python app.py
echo.
echo  [ERROR] Backend berhenti! Tekan tombol apapun untuk menutup.
pause >nul

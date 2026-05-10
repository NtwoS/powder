@echo off
title Diana AI - Frontend
color 0D
cd /d "%~dp0frontend"
echo.
echo  === FRONTEND DIANA AI ===
echo  Alamat: http://localhost:4321
echo.
npm run dev
echo.
echo  [ERROR] Frontend berhenti! Tekan tombol apapun untuk menutup.
pause >nul

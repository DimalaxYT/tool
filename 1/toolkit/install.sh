#!/usr/bin/env bash
# ============================================================
# LANCEUR TOOLKIT v5.7.0
# Vérifie l'environnement, active le venv, lance le menu
# ============================================================
set -e
cd "$(dirname "$0")"

# --- Couleurs ---
G="\033[32m"; Y="\033[33m"; R="\033[31m"; C="\033[36m"; D="\033[2m"; N="\033[0m"

echo -e "${C}╔══════════════════════════════════════════════════╗"
echo -e "║       TOOLKIT v5.7.0 - LANCEUR AUTOMATIQUE       ║"
echo -e "╚══════════════════════════════════════════════════╝${N}"

# --- Vérification Python ---
if ! command -v python3 &>/dev/null; then
    echo -e "${R}[!]${N} python3 introuvable. Installez-le : sudo apt install python3 python3-venv"
    read -p "Entrée pour fermer..."
    exit 1
fi

# --- Vérification venv ---
if [ ! -d ".venv" ]; then
    echo -e "${Y}[~]${N} Virtualenv absent, création..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip >/dev/null
    if [ -f "requirements.txt" ]; then
        echo -e "${Y}[~]${N} Installation des dépendances..."
        pip install -r requirements.txt
    fi
else
    source .venv/bin/activate
fi

# --- Vérification dépendances critiques ---
echo -e "${C}[i]${N} Vérification rapide..."
python3 - <<'EOF' >/dev/null 2>&1 || {
import importlib, sys
missing = []
for m in ["scapy","paramiko","requests","bs4"]:
    try: importlib.import_module(m)
    except ImportError: missing.append(m)
if missing:
    print("MISSING:" + ",".join(missing))
    sys.exit(1)
EOF
    echo -e "${Y}[~]${N} Dépendances manquantes, installation..."
    pip install -r requirements.txt
}

# --- Création dossiers ---
mkdir -p output logs payloads/mail_templates server

# --- Vérification des permissions output/ ---
if [ ! -w "output" ]; then
    echo -e "${Y}[~]${N} Correction permissions output/..."
    sudo chown -R "$USER:$USER" output logs 2>/dev/null || true
fi

# --- Lancement ---
echo -e "${G}[+]${N} Lancement du toolkit..."
echo ""
python3 toolkit.py

# --- Pause à la sortie ---
echo ""
echo -e "${D}[Entrée pour fermer la fenêtre]${N}"
read -p ""
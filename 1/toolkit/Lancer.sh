#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "[+] Debut toolkit..."
[ ! -d ".venv" ] && python3 -m venv .venv
source .venv/bin/activate
if [ ! -f ".venv/.deps_ok" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    touch .venv/.deps_ok
fi
mkdir -p output logs payloads/mail_templates server
python3 toolkit.py
echo "[Fin] Appuyez sur Entree pour fermer"
read -p ""

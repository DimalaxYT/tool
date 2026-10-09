#!/usr/bin/env bash
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_DIR="$HOME/Bureau"
[ ! -d "$DESKTOP_DIR" ] && DESKTOP_DIR="$HOME/Desktop"
[ ! -d "$DESKTOP_DIR" ] && mkdir -p "$DESKTOP_DIR"
chmod +x "$HERE/Lancer.sh" "$HERE/installer_raccourci.sh"
cat > "$DESKTOP_DIR/Toolkit.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Toolkit
Comment=Lance le toolkit
Exec=$HERE/Lancer.sh
Icon=utilities-terminal
Terminal=true
Categories=Network;Security;
Path=$HERE
StartupNotify=true
EOF
chmod +x "$DESKTOP_DIR/Toolkit.desktop"
command -v gio &>/dev/null && gio set "$DESKTOP_DIR/Toolkit.desktop" metadata::trusted true 2>/dev/null || true
echo "[+] Raccourci installé : $DESKTOP_DIR/Toolkit.desktop"

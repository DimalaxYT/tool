# TOOLKIT MULTI-FONCTIONS v1.0.0

Outil modulaire de tests d'intrusion, d'OSINT, de phishing et de stress réseau.
Usage strictement réservé à un environnement isolé et autorisé.

## 1. INSTALLATION

### 1.1 Prérequis
- Python 3.9+
- Droits root/admin (raw sockets, ARP, sniffer)

### 1.2 Dépendances
    pip install -r requirements.txt

### 1.3 requirements.txt
    scapy
    paramiko
    requests
    pynput
    cryptography
    colorama
    beautifulsoup4
    dnspython
    stem
    PySocks

## 2. STRUCTURE

    toolkit/
    ├── toolkit.py
    ├── config.json
    ├── requirements.txt
    ├── README.md
    ├── modules/
    ├── server/
    ├── payloads/
    ├── output/
    └── logs/

## 3. UTILISATION

    python3 toolkit.py <module> [options]

Modules : scan, arp, sniff, ssh, web, keylog, shell, privesc, wifi,
crypto, persist, phish, account, osint, ddos

## 4. MODULES

### 4.1 scan — network_scanner.py
Découverte hôtes (ARP) + scan ports (TCP connect).
    python3 toolkit.py scan --cidr 192.168.1.0/24 --ports 22,80,443

### 4.2 arp — arp_spoofer.py
Empoisonnement ARP bidirectionnel. Active ip_forward.
    python3 toolkit.py arp --target 192.168.1.10 --gateway 192.168.1.1 --iface eth0

### 4.3 sniff — packet_sniffer.py
Capture BPF + détection mots-clés sensibles.
    python3 toolkit.py sniff --iface eth0 --filter "tcp port 80"

### 4.4 ssh — ssh_bruteforce.py
Dictionnaire utilisateur×password via paramiko.
    python3 toolkit.py ssh --host 192.168.1.20 --port 22

### 4.5 web — web_attacker.py
SQLi/XSS/LFI sur paramètres GET.
    python3 toolkit.py web --url "http://cible/page.php"

### 4.6 keylog — keylogger.py
Frappes clavier → output/keys.log.
    python3 toolkit.py keylog

### 4.7 shell — reverse_shell.py
Shell inversé base64.
    python3 toolkit.py shell --mode server --port 4444

### 4.8 privesc — privilege_escalation.py
SUID, sudo -l, cron, kernel, capabilities.
    python3 toolkit.py privesc

### 4.9 wifi — wifi_attacker.py
Deauth + capture handshake WPA.
    python3 toolkit.py wifi --iface wlan0mon --bssid XX:XX:XX:XX:XX:XX

### 4.10 crypto — crypto_tools.py
Casse hash MD5/SHA + AES-256.
    python3 toolkit.py crypto --hash HASH --wordlist payloads/wordlist_pass.txt

### 4.11 persist — persistence.py
Cron/systemd/registry/LaunchAgent.
    python3 toolkit.py persist --payload /chemin/binaire

### 4.12 phish — phishing_mail.py
Campagne SMTP + tracking pixel/URL.
    python3 toolkit.py phish --config config.json

### 4.13 account — account_cracker.py
Credential stuffing, session hijack, OAuth replay, 2FA bypass.
    python3 toolkit.py account --targets payloads/targets_mail.txt

### 4.14 osint — osint_collector.py
Google/GitHub/Shodan/HIBP/Wayback/EXIF + rapport.
    python3 toolkit.py osint --target "email@example.com"

### 4.15 ddos — ddos_engine.py
SYN/UDP/HTTP/Slowloris/Amplification + Tor.
    python3 toolkit.py ddos --target IP --port 80 --method http_flood --threads 500

## 5. CONFIG

### 5.1 config.json
Toutes les sections de paramétrage.

### 5.2 modules/api_keys.json
    {"shodan":"","censys_id":"","censys_secret":"","hibp":"","hunter":""}

### 5.3 payloads/
sqli.txt, xss.txt, lfi.txt, wordlist_users.txt, wordlist_pass.txt,
targets_mail.txt, leaked_creds.txt, dorks.txt, proxies.txt,
mail_templates/template_defaut.html, template_defaut.txt

## 6. SORTIES

| Fichier | Contenu |
|---|---|
| output/scan_results.json | Hôtes et ports |
| output/cracked_hashes.txt | Hashes cassés |
| output/keys.log | Frappes clavier |
| output/phishing_report.json | Campagne phishing |
| output/osint_report.json | OSINT brut |
| output/osint_report.html | OSINT lisible |
| output/cracked_accounts.txt | Comptes compromis |
| output/ddos_stats.json | Stats DDoS |
| logs/toolkit.log | Journal global |

## 7. JOURNAL

Format : [ISO8601] [MODULE] message

## 8. DÉPANNAGE

| Erreur | Solution |
|---|---|
| Permission denied | sudo |
| scapy import error | pip install scapy |
| No such device | vérifier ifconfig |
| SMTP auth failed | config.json |
| Tor not running | service tor start |

## 9. AVERTISSEMENT TECHNIQUE

Sockets brutes, falsification de paquets, connexions non autorisées.
Usage limité à un laboratoire isolé ou périmètre autorisé.

Version 1.0.0
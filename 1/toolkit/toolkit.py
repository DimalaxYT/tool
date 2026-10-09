# -*- coding: utf-8 -*-
# =====================================================================
# TOOLKIT v5.9.0 - MENU PRINCIPAL + BRIHUB + HACKING
# =====================================================================
import os, sys, json, time, logging, socket, subprocess
from datetime import datetime

for d in ["output","logs","payloads","payloads/mail_templates","server"]:
    os.makedirs(d, exist_ok=True)

logging.basicConfig(filename="logs/toolkit.log", level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] %(message)s")

class C:
    RESET="\033[0m"; BOLD="\033[1m"; DIM="\033[2m"
    RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"
    BLUE="\033[34m"; MAGENTA="\033[35m"; CYAN="\033[36m"

SUDO_PASSWORD_FILE = os.path.expanduser("~/.toolkit_sudo_pass")

def is_root():
    if os.name == "posix": return os.geteuid() == 0
    return True

def prompt_sudo_password():
    section("MEMORISER MOT DE PASSE SUDO")
    info("Le mot de passe est stocke dans ~/.toolkit_sudo_pass (chmod 600).")
    pw = input(f"{C.YELLOW}Mot de passe systeme : {C.RESET}")
    try:
        with open(SUDO_PASSWORD_FILE,"w") as f: f.write(pw)
        os.chmod(SUDO_PASSWORD_FILE, 0o600)
        ok("Mot de passe memorise.")
    except Exception as e:
        err(f"Impossible d'enregistrer : {e}")

def sudo_run(cmd):
    if is_root():
        return subprocess.run(cmd, shell=True).returncode == 0
    pw = None
    if os.path.exists(SUDO_PASSWORD_FILE):
        try:
            with open(SUDO_PASSWORD_FILE) as f: pw = f.read().strip()
        except Exception: pass
    if not pw:
        info("Cette action requiert root.")
        pw = input(f"{C.YELLOW}Mot de passe sudo : {C.RESET}")
        try:
            with open(SUDO_PASSWORD_FILE,"w") as f: f.write(pw)
            os.chmod(SUDO_PASSWORD_FILE, 0o600)
        except Exception: pass
    try:
        proc = subprocess.run(["sudo","-S","bash","-c",cmd],
                              input=(pw+"\n").encode(), stderr=subprocess.PIPE)
        return proc.returncode == 0
    except Exception as e:
        err(f"sudo : {e}"); return False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except Exception: return "127.0.0.1"

def get_public_ip():
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=4).read().decode()
    except Exception:
        try:
            import urllib.request
            return urllib.request.urlopen("https://ifconfig.me/ip", timeout=4).read().decode()
        except Exception: return "indisponible"

def get_iface():
    try:
        out = subprocess.check_output(["ip","route","get","8.8.8.8"],
                stderr=subprocess.DEVNULL).decode()
        return out.split("dev")[1].strip().split()[0]
    except Exception: return "?"

def get_banner():
    li = get_local_ip(); pi = get_public_ip(); ifc = get_iface()
    rs = f"{C.GREEN}root{C.RESET}" if is_root() else f"{C.RED}non-root{C.RESET}"
    ss = f"{C.GREEN}OUI{C.RESET}" if os.path.exists(SUDO_PASSWORD_FILE) else f"{C.YELLOW}non{C.RESET}"
    return f"""{C.CYAN}{C.BOLD}
  ████████╗ ██████╗  ██████╗ ██╗     ██╗  ██╗██╗████████╗
  ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██║ ██╔╝██║╚══██╔══╝
     ██║   ██║   ██║██║   ██║██║     █████╔╝ ██║   ██║
     ██║   ██║   ██║██║   ██║██║     ██╔═██╗ ██║   ██║
     ██║   ╚██████╔╝╚██████╔╝███████╗██║  ██╗██║   ██║
     ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝
{C.RESET}{C.DIM}                v5.9.0 - mode interactif{C.RESET}
  {C.YELLOW}Interface :{C.RESET} {ifc}     {C.YELLOW}IP locale :{C.RESET} {li}
  {C.YELLOW}IP publique :{C.RESET} {pi}     {C.YELLOW}Priv :{C.RESET} {rs}
  {C.YELLOW}Sudo memorise :{C.RESET} {ss}
"""

MENU = f"""
{C.BOLD}┌─────────────────────────────────────────────────────────┐
│                    MENU PRINCIPAL                       │
├─────────────────────────────────────────────────────────┤
│  {C.CYAN}[ 1]{C.RESET} Scan reseau (LAN + WAN)                        │
│  {C.CYAN}[ 2]{C.RESET} ARP spoofing (MITM)                            │
│  {C.CYAN}[ 3]{C.RESET} Sniffer + analyse paquets                      │
│  {C.CYAN}[ 4]{C.RESET} Brute-force multi-protocole                    │
│  {C.CYAN}[ 5]{C.RESET} Scanner web                                    │
│  {C.CYAN}[ 6]{C.RESET} Keylogger                                      │
│  {C.CYAN}[ 7]{C.RESET} Reverse shell chiffre                          │
│  {C.CYAN}[ 8]{C.RESET} Enumeration privileges                         │
│  {C.CYAN}[ 9]{C.RESET} Attaque Wi-Fi                                   │
│  {C.CYAN}[10]{C.RESET} Outils crypto                                   │
│  {C.CYAN}[11]{C.RESET} Persistance                                    │
│  {C.CYAN}[12]{C.RESET} Campagne phishing                              │
│  {C.CYAN}[13]{C.RESET} Piratage de comptes                            │
│  {C.CYAN}[14]{C.RESET} {C.GREEN}OSINT avance{C.RESET}                             │
│  {C.CYAN}[15]{C.RESET} {C.MAGENTA}BRIHUB (recherche identite){C.RESET}             │
│  {C.CYAN}[16]{C.RESET} {C.RED}HACKING (exploitation IP){C.RESET}                  │
│  {C.CYAN}[17]{C.RESET} DDoS multi-vecteurs                            │
│  {C.CYAN}[18]{C.RESET} Verifier dependances                           │
│  {C.CYAN}[19]{C.RESET} Consulter rapports                             │
│  {C.CYAN}[20]{C.RESET} Info systeme                                   │
│  {C.CYAN}[21]{C.RESET} Memoriser mot de passe sudo                    │
│  {C.CYAN}[22]{C.RESET} Mettre a jour dependances (pip)                │
│  {C.CYAN}[ 0]{C.RESET} Quitter                                         │
└─────────────────────────────────────────────────────────┘
{C.BOLD}Choix >{C.RESET} """

def clear(): os.system("clear" if os.name=="posix" else "cls")
def pause(): input(f"\n{C.DIM}[Entree pour continuer]{C.RESET}")
def ask(p, d=None):
    v = input(f"{C.YELLOW}{p}{C.RESET}" + (f" [{d}]" if d else "") + " : ").strip()
    return v if v else d
def confirm(p): return input(f"{C.YELLOW}{p} (o/n){C.RESET} : ").strip().lower() in ("o","oui","y","yes")
def ok(m): print(f"{C.GREEN}[+]{C.RESET} {m}")
def err(m): print(f"{C.RED}[!]{C.RESET} {m}")
def info(m): print(f"{C.BLUE}[i]{C.RESET} {m}")
def warn(m): print(f"{C.YELLOW}[~]{C.RESET} {m}")
def section(t): print(f"\n{C.BOLD}{C.CYAN}=== {t} ==={C.RESET}")

def check_deps():
    section("Verification dependances")
    for d in ["scapy","paramiko","requests","pynput","cryptography","bs4","dns","stem","socks","PIL"]:
        try: __import__(d); ok(d)
        except ImportError: err(f"{d} MANQUANT")

def update_deps():
    section("Mise a jour dependances")
    if not os.path.exists("requirements.txt"): err("requirements.txt introuvable"); return
    rc = subprocess.run([sys.executable,"-m","pip","install","-r","requirements.txt"]).returncode
    ok("OK") if rc==0 else err("Echec")

def info_system():
    section("INFO SYSTEME")
    print(f"  Interface    : {get_iface()}")
    print(f"  IP locale    : {get_local_ip()}")
    print(f"  IP publique  : {get_public_ip()}")
    print(f"  Root         : {is_root()}")
    print(f"  Sudo memorise: {os.path.exists(SUDO_PASSWORD_FILE)}")
    print(f"  OS           : {os.name}")
    print(f"  Python       : {sys.version.split()[0]}")
    section("Interfaces")
    os.system("ip -brief addr 2>/dev/null || ifconfig 2>/dev/null")

def run_reports():
    section("Rapports disponibles")
    if not os.path.isdir("output"): err("Aucun dossier"); return
    files = sorted(f for f in os.listdir("output") if f.endswith((".json",".html",".txt",".log")))
    if not files: err("Aucun rapport"); return
    for i,f in enumerate(files,1):
        p = os.path.join("output",f)
        try: sz = os.path.getsize(p)
        except Exception: sz = 0
        print(f"  {C.CYAN}[{i}]{C.RESET} {f:<40} {sz:>8} o")
    ch = ask("Numero (vide=annuler)")
    if not ch: return
    try:
        p = os.path.join("output", files[int(ch)-1])
        if p.endswith(".html"):
            os.system(f"xdg-open {p} 2>/dev/null &")
        else:
            with open(p, encoding="utf-8", errors="ignore") as f:
                print(f.read()[:6000])
    except Exception as e: err(f"{e}")

def run_arp_sudo():
    info("ARP spoofing necessite root.")
    t = ask("IP cible"); g = ask("IP passerelle"); i = ask("Interface","eth0")
    cmd = (f'cd "{os.getcwd()}" && source .venv/bin/activate && '
           f'python3 -c "from modules.arp_spoofer import ARPSpoofer; '
           f's=ARPSpoofer(\'{t}\',\'{g}\',\'{i}\'); '
           f'import signal; signal.signal(signal.SIGINT, lambda *a: s.restore()); '
           f's.spoof()"')
    if not sudo_run(cmd): err("Echec sudo")

def run_sniff_sudo():
    info("Sniffer necessite root.")
    i = ask("Interface","eth0"); f = ask("Filtre BPF","ip")
    cmd = (f'cd "{os.getcwd()}" && source .venv/bin/activate && '
           f'python3 -c "from modules.packet_sniffer import PacketSniffer; '
           f'PacketSniffer(\'{i}\',\'{f}\').start()"')
    if not sudo_run(cmd): err("Echec sudo")

def run_scan():     from modules.network_scanner import run_interactive;      run_interactive()
def run_web():      from modules.web_attacker import run_interactive;         run_interactive()
def run_ssh():      from modules.ssh_bruteforce import run_interactive;       run_interactive()
def run_keylog():   from modules.keylogger import run_interactive;            run_interactive()
def run_shell():    from modules.reverse_shell import run_interactive;        run_interactive()
def run_privesc():  from modules.privilege_escalation import run_interactive; run_interactive()
def run_wifi():     from modules.wifi_attacker import run_interactive;        run_interactive()
def run_crypto():   from modules.crypto_tools import run_interactive;         run_interactive()
def run_persist():  from modules.persistence import run_interactive;          run_interactive()
def run_phish():    from modules.phishing_mail import run_interactive;        run_interactive()
def run_account():  from modules.account_cracker import run_interactive;      run_interactive()
def run_osint():    from modules.osint_collector import run_interactive;      run_interactive()
def run_ddos():     from modules.ddos_engine import run_interactive;          run_interactive()
def run_hacking():  from modules.hacking import run_interactive;              run_interactive()

def run_brihub():
    from modules.osint_collector import BrixHub, IdentitySearch
    brix = BrixHub(); ids = IdentitySearch()
    if not brix.enabled:
        warn(f"BrixHub desactive : {brix.endpoint} ne resout pas (DNS)")
        warn("Modifiez 'brihub.endpoint' dans config.json")
        if not confirm("Continuer quand meme ?"): return
    while True:
        clear()
        print(f"""{C.BOLD}{C.MAGENTA}
┌──────────────────────────────────────────────┐
│           BRIHUB - RECHERCHE IDENTITE        │
├──────────────────────────────────────────────┤
│  {C.CYAN}[ 1]{C.RESET} Nom + Prenom                          │
│  {C.CYAN}[ 2]{C.RESET} Nom + Ville                            │
│  {C.CYAN}[ 3]{C.RESET} Nom seul                               │
│  {C.CYAN}[ 4]{C.RESET} Telephone                              │
│  {C.CYAN}[ 5]{C.RESET} Email                                  │
│  {C.CYAN}[ 6]{C.RESET} IBAN                                   │
│  {C.CYAN}[ 7]{C.RESET} SIRET/SIREN                            │
│  {C.CYAN}[ 8]{C.RESET} Steam ID                               │
│  {C.CYAN}[ 9]{C.RESET} Immatriculation                        │
│  {C.CYAN}[10]{C.RESET} Adresse IP                             │
│  {C.CYAN}[11]{C.RESET} Multi-criteres complet                 │
│  {C.CYAN}[12]{C.RESET} JSON brut                              │
│  {C.CYAN}[13]{C.RESET} Pagination                             │
│  {C.CYAN}[ 0]{C.RESET} Retour                                 │
└──────────────────────────────────────────────┘{C.RESET}
Choix > """, end="")
        ch = input().strip()
        if ch == "0": return
        try:
            if ch == "1":
                n = ask("Nom"); p = ask("Prenom"); v = ask("Ville (vide)","")
                ids.search_full(nom=n, prenom=p, ville=v or None)
            elif ch == "2":
                n = ask("Nom"); v = ask("Ville"); ids.search_full(nom=n, ville=v)
            elif ch == "3":
                n = ask("Nom"); ids.search_full(nom=n)
            elif ch == "4":
                t = ask("Telephone"); ids.search_full(telephone=t)
            elif ch == "5":
                e = ask("Email"); ids.search_full(email=e)
            elif ch == "6":
                ids.search_iban(ask("IBAN"))
            elif ch == "7":
                ids.search_siret(ask("SIRET/SIREN"))
            elif ch == "8":
                ids.search_steam(ask("Steam ID"))
            elif ch == "9":
                brix.print_results(brix.search({"immatriculation":ask("Immatriculation")},per_page=20))
            elif ch == "10":
                brix.print_results(brix.search({"adresse_ip":ask("IP")},per_page=20))
            elif ch == "11":
                c = {}
                for f in ["nom_famille","prenom","nom_naissance","date_naissance",
                          "email","telephone","mobile","adresse","ville",
                          "code_postal","pays","societe","siret","siren",
                          "iban","steam_id","discord_id","adresse_ip","immatriculation"]:
                    v = ask(f"{f} (vide)","")
                    if v: c[f] = v
                if c: brix.print_results(brix.search(c, per_page=100, flexible=True))
                else: err("Aucun critere")
            elif ch == "12":
                try:
                    c = json.loads(ask("JSON"))
                    brix.print_results(brix.search(c, per_page=50, flexible=True))
                except Exception as e: err(f"{e}")
            elif ch == "13":
                n = ask("Nom"); v = ask("Ville (vide)","")
                c = {"nom_famille":n}
                if v: c["ville"] = v
                r = brix.paginate(c, max_pages=10, per_page=100, flexible=True)
                info(f"{len(r)} resultats")
        except Exception as e: err(f"{e}")
        pause()

def main_menu():
    actions = {"1":run_scan,"2":run_arp_sudo,"3":run_sniff_sudo,"4":run_ssh,
        "5":run_web,"6":run_keylog,"7":run_shell,"8":run_privesc,"9":run_wifi,
        "10":run_crypto,"11":run_persist,"12":run_phish,"13":run_account,
        "14":run_osint,"15":run_brihub,"16":run_hacking,"17":run_ddos,
        "18":check_deps,"19":run_reports,"20":info_system,
        "21":prompt_sudo_password,"22":update_deps}
    while True:
        clear(); print(get_banner()); print(MENU, end="")
        ch = input().strip()
        if ch == "0": ok("Fin."); sys.exit(0)
        a = actions.get(ch)
        if not a: err("Choix invalide"); time.sleep(1); continue
        try:
            print(); a()
        except KeyboardInterrupt: warn("Interrompu")
        except Exception as e:
            err(f"{e}"); logging.exception(f"Module {ch}")
        pause()

if __name__ == "__main__":
    main_menu()
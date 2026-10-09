# -*- coding: utf-8 -*-
# Module 1 : scan LAN + WAN v5.5
import socket, json, os, time, re, subprocess, platform, ipaddress
from datetime import datetime

try:
    from scapy.all import ARP, Ether, srp, IP, ICMP, TCP, sr1
    SCAPY_OK = True
except ImportError:
    SCAPY_OK = False

SERVICES = {
    21:("FTP","tcp"),22:("SSH","tcp"),23:("Telnet","tcp"),25:("SMTP","tcp"),
    53:("DNS","udp/tcp"),80:("HTTP","tcp"),110:("POP3","tcp"),111:("rpcbind","tcp"),
    135:("MSRPC","tcp"),139:("NetBIOS","tcp"),143:("IMAP","tcp"),161:("SNMP","udp"),
    389:("LDAP","tcp"),443:("HTTPS","tcp"),445:("SMB","tcp"),465:("SMTPS","tcp"),
    514:("Syslog","udp"),587:("SMTP-Sub","tcp"),631:("IPP","tcp"),993:("IMAPS","tcp"),
    995:("POP3S","tcp"),1080:("SOCKS","tcp"),1433:("MSSQL","tcp"),1521:("Oracle","tcp"),
    2049:("NFS","tcp"),3306:("MySQL","tcp"),3389:("RDP","tcp"),5432:("PostgreSQL","tcp"),
    5900:("VNC","tcp"),5985:("WinRM","tcp"),6379:("Redis","tcp"),8080:("HTTP-Alt","tcp"),
    8443:("HTTPS-Alt","tcp"),9001:("Tor","tcp"),9200:("Elasticsearch","tcp"),
    11211:("Memcached","tcp"),27017:("MongoDB","tcp")
}

BANNER_SIGS = [
    (re.compile(r"SSH-([\d\.]+)-([\w\.\-]+)"), "SSH"),
    (re.compile(r"Server:\s*([^\r\n]+)", re.I), "HTTP"),
    (re.compile(r"^220[ \-](.+)"), "SMTP/FTP"),
    (re.compile(r"^(\d+\.\d+\.\d+[\w\.\-]*)"), "Version")
]

OUI_DB = {
    "000C29":"VMware","005056":"VMware","080027":"VirtualBox",
    "001C42":"Parallels","525400":"QEMU/KVM","B827EB":"Raspberry Pi",
    "DCA632":"Raspberry Pi","001A11":"Google","F4F5D8":"Google",
    "001B63":"Apple","001451":"Apple","F0DBF8":"Apple",
    "001DD8":"Microsoft","0017FA":"Microsoft","C83A35":"Tenda",
    "F8D111":"TP-Link","B0487A":"TP-Link","001E58":"D-Link",
    "F81A67":"TP-Link","001F3F":"Samsung","002637":"Samsung"
}

def is_root():
    if os.name == "posix": return os.geteuid() == 0
    return True

def ensure_output_dir():
    # Création + vérification écriture
    os.makedirs("output", exist_ok=True)
    test_file = os.path.join("output",".write_test")
    try:
        with open(test_file,"w") as f: f.write("x")
        os.remove(test_file)
        return True, ""
    except PermissionError:
        return False, "Permission refusée sur output/ - exécutez : sudo chown -R $USER:$USER ."
    except Exception as e:
        return False, str(e)

class NetworkScanner:
    def __init__(self, cidr, ports, timeout=0.5):
        self.cidr = cidr
        self.ports = ports
        self.timeout = timeout
        self.results = []
        self.wan_mode = False

    # ---------- Découverte LAN ----------
    def arp_scan(self):
        if not SCAPY_OK or not is_root(): return []
        try:
            pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=self.cidr)
            res = srp(pkt, timeout=3, verbose=0)[0]
            return [{"ip":r.psrc,"mac":r.hwsrc} for _,r in res]
        except Exception: return []

    def ping_host(self, ip, timeout=1):
        sysname = platform.system()
        try:
            if sysname == "Windows":
                cmd = ["ping","-n","1","-w",str(timeout*1000),ip]
            else:
                cmd = ["ping","-c","1","-W",str(timeout),ip]
            r = subprocess.run(cmd, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=timeout+1)
            return r.returncode == 0
        except Exception: return False

    def ping_sweep(self):
        try:
            net = ipaddress.ip_network(self.cidr, strict=False)
        except Exception: return []
        hosts = []
        total = net.num_addresses - 2
        print(f"  Ping sweep de {total} adresses...")
        n = 0
        for ip in net.hosts():
            n += 1
            if n % 20 == 0:
                print(f"\r  Progression : {n}/{total}", end="", flush=True)
            if self.ping_host(str(ip)):
                hosts.append({"ip":str(ip),"mac":"?"})
        print(f"\r  Progression : {n}/{total} - terminé")
        return hosts

    def resolve_target(self, target):
        try:
            ipaddress.ip_address(target)
            return target
        except ValueError:
            try: return socket.gethostbyname(target)
            except Exception: return None

    # ---------- Scan WAN avec timeout augmenté ----------
    def wan_scan(self, target, ports, timeout=2.5):
        ip = self.resolve_target(target)
        if not ip:
            print(f"  [!] Impossible de résoudre {target}")
            return []
        print(f"  [i] Cible : {target} -> {ip}")
        print(f"  [i] Timeout par port : {timeout}s (cible externe)")
        host = {"ip": ip, "hostname":"", "mac":"?", "vendor":"",
                "ports": [], "wan": True}
        try: host["hostname"] = socket.gethostbyaddr(ip)[0]
        except Exception: pass
        total = len(ports)
        for i, p in enumerate(ports, 1):
            print(f"\r  Scan port {i}/{total} : {p}", end="", flush=True)
            if self.tcp_connect(ip, p, timeout):
                svc, proto = SERVICES.get(p, ("unknown","tcp"))
                banner = self.grab_banner(ip, p, timeout)
                version = self.parse_banner(banner)
                host["ports"].append({
                    "port":p,"state":"open","service":svc,
                    "protocol":proto,"version":version,"banner":banner[:300]
                })
                print(f"\r  [+] Port {p} OUVERT ({svc}) - {version[:40]}")
        print(f"\r  Scan terminé ({len(host['ports'])} ports ouverts sur {total})")
        return [host]

    def grab_banner(self, ip, port, timeout=2):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            if port in (80,8080,8000,443,8443):
                s.send(b"GET / HTTP/1.0\r\nHost: "+ip.encode()+b"\r\n\r\n")
            elif port in (21,22,25,110,143): pass
            else: s.send(b"\r\n")
            data = s.recv(1024); s.close()
            return data.decode(errors="ignore").strip()
        except Exception: return ""

    def parse_banner(self, banner):
        for pattern, name in BANNER_SIGS:
            m = pattern.search(banner)
            if m: return m.group(1).strip()[:80]
        return banner.split("\n")[0][:80] if banner else ""

    def tcp_connect(self, ip, port, timeout=None):
        if timeout is None: timeout = self.timeout
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            if s.connect_ex((ip, port)) == 0: return True
        except Exception: pass
        finally: s.close()
        return False

    def get_hostname(self, ip):
        try: return socket.gethostbyaddr(ip)[0]
        except Exception: return ""

    def get_vendor(self, mac):
        if not mac or mac == "?": return ""
        oui = mac.upper().replace(":","").replace("-","")[:6]
        return OUI_DB.get(oui, "")

    def scan_host(self, ip):
        host = {"ip":ip,"hostname":self.get_hostname(ip),
                "mac":"?","vendor":"","ports":[]}
        total = len(self.ports)
        for i, p in enumerate(self.ports, 1):
            print(f"\r  Port {i}/{total} : {p}", end="", flush=True)
            if self.tcp_connect(ip, p):
                svc, proto = SERVICES.get(p, ("unknown","tcp"))
                banner = self.grab_banner(ip, p)
                version = self.parse_banner(banner)
                host["ports"].append({
                    "port":p,"state":"open","service":svc,
                    "protocol":proto,"version":version,"banner":banner[:300]
                })
                print(f"\r  [+] {p} OUVERT ({svc}) - {version[:40]}")
        print()
        return host

    def print_table(self):
        print()
        if not self.results:
            print("\033[1m\033[36m" + "═" * 110 + "\033[0m")
            print("\033[1m\033[33m  AUCUN HÔTE DÉTECTÉ\033[0m")
            print("\033[1m\033[36m" + "═" * 110 + "\033[0m")
            return
        print("\033[1m\033[36m" + "═" * 110 + "\033[0m")
        print(f"\033[1m{'IP':<18} {'HOSTNAME':<30} {'MAC':<18} {'VENDOR':<14}\033[0m")
        print("\033[1m\033[36m" + "═" * 110 + "\033[0m")
        for h in self.results:
            print(f"{h['ip']:<18} {(h.get('hostname') or '-'):<30} "
                  f"{(h.get('mac') or '?'):<18} {(h.get('vendor') or '-'):<14}")
        print("\033[1m\033[36m" + "═" * 110 + "\033[0m")
        for h in self.results:
            if not h["ports"]:
                print(f"\n\033[1m\033[33m▶ {h['ip']}\033[0m (aucun port ouvert)")
                continue
            print(f"\n\033[1m\033[33m▶ {h['ip']}\033[0m ({len(h['ports'])} ports ouverts)")
            print(f"  \033[1m{'PORT':<8} {'STATE':<8} {'SERVICE':<16} "
                  f"{'PROTO':<8} {'VERSION':<55}\033[0m")
            print(f"  {'─'*8} {'─'*8} {'─'*16} {'─'*8} {'─'*55}")
            for p in h["ports"]:
                ver = p["version"] or "(aucune bannière)"
                print(f"  {p['port']:<8} {p['state']:<8} {p['service']:<16} "
                      f"{p['protocol']:<8} {ver[:55]:<55}")

    def save(self):
        ok, msg = ensure_output_dir()
        if not ok:
            print(f"\033[31m[!]\033[0m {msg}")
            return
        with open("output/scan_results.json","w",encoding="utf-8") as f:
            json.dump({"timestamp":datetime.now().isoformat(),
                       "results":self.results}, f, indent=2)

    def run_lan(self, use_arp=True):
        if use_arp and is_root() and SCAPY_OK:
            print(f"  [i] Découverte ARP...")
            hosts = self.arp_scan()
        else:
            print(f"  [~] Ping sweep (root absent)")
            hosts = self.ping_sweep()
        if not hosts:
            print(f"  [!] Aucun hôte actif détecté")
            self.print_table(); self.save(); return []
        print(f"  [+] {len(hosts)} hôte(s) actif(s)")
        for i, h in enumerate(hosts, 1):
            print(f"\n  [{i}/{len(hosts)}] {h['ip']}")
            host = self.scan_host(h["ip"])
            host["mac"] = h.get("mac","?")
            host["vendor"] = self.get_vendor(host["mac"])
            self.results.append(host)
        self.print_table(); self.save()
        return self.results

    def run_wan(self, target, timeout=2.5):
        hosts = self.wan_scan(target, self.ports, timeout)
        self.results = hosts
        self.print_table(); self.save()
        return self.results

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask
    section("SCAN RÉSEAU")
    print("  \033[1mMode :\033[0m")
    print("    \033[36m[1]\033[0m LAN  - mon réseau local")
    print("    \033[36m[2]\033[0m WAN  - cible externe")
    mode = ask("Choix", "1")

    if mode == "1":
        if not is_root():
            warn("Pas root - ARP désactivé (ping sweep uniquement)")
            warn("Pour ARP : sudo -E .venv/bin/python toolkit.py")
        from toolkit import get_local_ip
        local = get_local_ip()
        default_cidr = ".".join(local.split(".")[:3]) + ".0/24"
        cidr = ask("CIDR", default_cidr)
        ports_in = ask("Ports", ",".join(str(p) for p in sorted(SERVICES.keys())))
        ports = [int(p) for p in ports_in.split(",") if p.strip().isdigit()]
        info(f"{len(ports)} ports à scanner")
        scanner = NetworkScanner(cidr, ports)
        scanner.run_lan(use_arp=True)
    else:
        target = ask("IP ou domaine cible", "scanme.nmap.org")
        ports_in = ask("Ports", "21,22,25,53,80,110,143,443,445,993,995,3306,3389,5432,8080,8443")
        ports = [int(p) for p in ports_in.split(",") if p.strip().isdigit()]
        timeout = float(ask("Timeout par port (s)", "2.5"))
        info(f"{len(ports)} ports à scanner sur {target}")
        scanner = NetworkScanner("", ports, timeout=timeout)
        scanner.run_wan(target, timeout)

    if scanner.results:
        total = sum(len(h["ports"]) for h in scanner.results)
        ok(f"Rapport : output/scan_results.json "
           f"({len(scanner.results)} hôte(s), {total} port(s))")
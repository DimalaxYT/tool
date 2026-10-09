# -*- coding: utf-8 -*-
# Module 14 : OSINT v5.6 - lite.ddg + Bing + BRIHUB
import os, re, json, socket, hashlib, time
from datetime import datetime
from urllib.parse import quote_plus, unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

UA = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
      "Accept-Language":"fr-FR,fr;q=0.9,en;q=0.8"}

BRIHUB_URL = "https://api.brihub.ru/api/v1/search"

def _h(t):    print(f"\n\033[1m\033[36m── {t} ──\033[0m")
def _ok(m):   print(f"\033[32m[+]\033[0m {m}")
def _no(m):   print(f"\033[31m[-]\033[0m {m}")
def _info(m): print(f"\033[34m[i]\033[0m {m}")
def _warn(m): print(f"\033[33m[~]\033[0m {m}")
def _dim(m):  print(f"\033[2m{m}\033[0m")

# =====================================================================
# BRIHUB CLIENT
# =====================================================================
class BrixHub:
    def __init__(self, endpoint=None):
        import json as _json
        if endpoint is None:
            try:
                with open("config.json") as f:
                    cfg = _json.load(f)
                endpoint = cfg.get("brihub",{}).get("endpoint",
                    "https://api.brihub.ru/api/v1/search")
            except Exception:
                endpoint = "https://api.brihub.ru/api/v1/search"
        self.endpoint = endpoint
        self.enabled = self._check_dns()
        self.s = requests.Session() if requests else None
        if self.s:
            self.s.headers.update({**UA,
                "Content-Type":"application/json",
                "Accept":"application/json"})

    def _check_dns(self):
        # Vérifie que le domaine résout avant toute requête
        try:
            from urllib.parse import urlparse
            host = urlparse(self.endpoint).hostname
            socket.gethostbyname(host)
            return True
        except Exception:
            return False

    def search(self, criterias, page=1, per_page=20, flexible=False, timeout=15):
        if not self.enabled:
            return {"status":"error",
                    "message":f"BrixHub désactivé : {self.endpoint} ne résout pas (DNS). "
                              f"Modifiez 'brihub.endpoint' dans config.json."}
        if not self.s:
            return {"status":"error","message":"requests non installé"}
        payload = {k:v for k,v in criterias.items() if v not in (None,"",[])}
        payload["page"] = page
        payload["per_page"] = per_page
        payload["flexible"] = flexible
        try:
            r = self.s.post(self.endpoint, json=payload, timeout=timeout)
        except Exception as e:
            return {"status":"error","message":str(e)}
        if r.status_code != 200:
            return {"status":"error","message":f"HTTP {r.status_code} - {r.text[:200]}"}
        try:
            return r.json()
        except Exception as e:
            return {"status":"error","message":f"JSON invalide : {e}"}

    def print_results(self, resp):
        if resp.get("status") == "error":
            _no(resp.get("message","Erreur inconnue"))
            return
        data = resp.get("data") or {}
        results = data.get("results") or data.get("items") or []
        meta = resp.get("meta") or {}
        _info(f"Total : {meta.get('total', len(results))} "
              f"| Page {meta.get('page','?')}/{meta.get('pages','?')}")
        if not results:
            _no("Aucun résultat BrixHub")
            return
        for i, item in enumerate(results, 1):
            print(f"\n  \033[1m\033[33m[{i}] "
                  f"{item.get('prenom','')} {item.get('nom_famille','')}"
                  f"\033[0m")
            for k in ["date_naissance","email","telephone","mobile",
                      "adresse","ville","code_postal","pays",
                      "societe","fonction","siret","siren",
                      "iban","bic","steam_id","discord_id",
                      "adresse_ip","immatriculation"]:
                if item.get(k):
                    print(f"      \033[33m{k:<18}\033[0m {item[k]}")

    def paginate(self, criterias, max_pages=5, per_page=50, flexible=False):
        if not self.enabled:
            _no(f"BrixHub désactivé (DNS ne résout pas {self.endpoint})")
            return []
        all_results = []
        for p in range(1, max_pages+1):
            _info(f"Page {p}...")
            resp = self.search(criterias, page=p, per_page=per_page,
                               flexible=flexible)
            if resp.get("status") == "error":
                _no(resp.get("message")); break
            data = resp.get("data") or {}
            results = data.get("results") or data.get("items") or []
            if not results: break
            all_results.extend(results)
            meta = resp.get("meta") or {}
            if p >= meta.get("pages", p): break
            time.sleep(1)
        return all_results
# =====================================================================
# MOTEURS DE RECHERCHE WEB
# =====================================================================
class SearchEngine:
    def __init__(self):
        self.s = requests.Session() if requests else None
        if self.s: self.s.headers.update(UA)

    def lite_ddg(self, query, max_results=20):
        if not self.s: return []
        results = []
        try:
            r = self.s.post("https://lite.duckduckgo.com/lite/",
                            data={"q":query}, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.select("a.result-link")[:max_results]:
                title = a.get_text().strip()
                url = a.get("href","")
                tr = a.find_parent("tr")
                snippet = ""
                if tr:
                    nxt = tr.find_next_sibling("tr")
                    if nxt:
                        snip_el = nxt.select_one("td.result-snippet") or nxt.select_one("td")
                        if snip_el: snippet = snip_el.get_text().strip()
                if title and url.startswith("http"):
                    results.append({"title":title,"snippet":snippet[:300],"url":url})
        except Exception as e:
            _no(f"lite.ddg : {e}")
        return results

    def html_ddg(self, query, max_results=20):
        if not self.s: return []
        results = []
        try:
            r = self.s.post("https://html.duckduckgo.com/html/",
                            data={"q":query}, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for div in soup.select("div.result")[:max_results]:
                t = div.select_one("a.result__a")
                sn = div.select_one("a.result__snippet") or div.select_one(".result__snippet")
                if not t: continue
                u = t.get("href","")
                if "uddg=" in u:
                    m = re.search(r"uddg=([^&]+)", u)
                    if m: u = unquote(m.group(1))
                results.append({
                    "title": t.get_text().strip(),
                    "snippet": sn.get_text().strip() if sn else "",
                    "url": u
                })
        except Exception as e:
            _no(f"html.ddg : {e}")
        return results

    def bing(self, query, max_results=20):
        if not self.s: return []
        results = []
        try:
            r = self.s.get("https://www.bing.com/search",
                           params={"q":query,"setlang":"fr"}, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for li in soup.select("li.b_algo")[:max_results]:
                h2 = li.select_one("h2 a")
                snip = li.select_one("p") or li.select_one(".b_caption p")
                if not h2: continue
                results.append({
                    "title": h2.get_text().strip(),
                    "snippet": snip.get_text().strip() if snip else "",
                    "url": h2.get("href","")
                })
        except Exception as e:
            _no(f"bing : {e}")
        return results

    def multi(self, query, max_per=10):
        seen = set(); out = []
        for r in (self.lite_ddg(query,max_per) +
                  self.html_ddg(query,max_per) +
                  self.bing(query,max_per)):
            if not r.get("url") or r["url"] in seen: continue
            seen.add(r["url"]); out.append(r)
        return out

# =====================================================================
# DETECTION SOCIALE
# =====================================================================
SOCIAL_MARKERS = {
    "GitHub":   {"url":"https://github.com/{u}",              "marker":'vcard-username'},
    "TikTok":   {"url":"https://www.tiktok.com/@{u}",         "marker":'"uniqueId":"{u}"'},
    "Instagram":{"url":"https://www.instagram.com/{u}/",      "marker":'"edge_followed_by"'},
    "Pinterest":{"url":"https://www.pinterest.com/{u}/",      "marker":'"follower_count"'},
    "Telegram": {"url":"https://t.me/{u}",                    "marker":'tgme_page_title'},
    "Twitch":   {"url":"https://www.twitch.tv/{u}",           "marker":'"name":"{u}"'},
    "Steam":    {"url":"https://steamcommunity.com/id/{u}",   "marker":'actual_persona_name'},
    "Spotify":  {"url":"https://open.spotify.com/user/{u}",   "marker":'"type":"user"'},
    "YouTube":  {"url":"https://www.youtube.com/@{u}",        "marker":'"channelId"'},
    "Reddit":   {"url":"https://www.reddit.com/user/{u}/about.json","marker":'"name":"{u}"'}
}
NEGATIVE = ["not found","page not found","doesn't exist","no user","profile not available",
            "user not found","404","sorry, this page isn't available","account suspended",
            "n'a pas été trouvé","this account doesn't exist"]

class SocialChecker:
    def __init__(self):
        self.s = requests.Session() if requests else None
        if self.s: self.s.headers.update(UA)

    def _check(self, url, marker, timeout=8):
        if not self.s: return False
        try:
            r = self.s.get(url, timeout=timeout, allow_redirects=True)
        except Exception:
            return False
        if r.status_code != 200: return False
        body = r.text.lower()[:8000]
        if any(n in body for n in NEGATIVE): return False
        return marker.lower().replace("{u}","") in body

    def check_username(self, username):
        _h(f"Réseaux sociaux : {username}")
        found = {}
        for name, cfg in SOCIAL_MARKERS.items():
            url = cfg["url"].format(u=username)
            marker = cfg["marker"].format(u=username)
            if self._check(url, marker):
                found[name] = url
                _ok(f"{name:<10} {url}")
            else:
                _dim(f"  {name:<10} (absent)")
        return found

# =====================================================================
# RECHERCHE IDENTITÉ (BRIHUB + WEB)
# =====================================================================
class IdentitySearch:
    def __init__(self):
        self.engine = SearchEngine()
        self.brix = BrixHub()

    def _print_web(self, results, max_show=15):
        if not results:
            _no("Aucun résultat web")
            return
        for i, r in enumerate(results[:max_show], 1):
            print(f"\n  \033[1m\033[33m[{i}] {r['title'][:100]}\033[0m")
            if r.get("snippet"):
                print(f"      {r['snippet'][:250]}")
            print(f"      \033[36m{r['url'][:120]}\033[0m")

    def _dedup(self, all_results):
        seen = set(); unique = []
        for r in all_results:
            if r["url"] not in seen:
                seen.add(r["url"]); unique.append(r)
        return unique

    # -------- Recherche complète par identité --------
    def search_full(self, nom=None, prenom=None, ville=None, email=None,
                    telephone=None, date_naissance=None, flexible=True):
        # Construction du payload BrixHub
        criterias = {}
        if nom: criterias["nom_famille"] = nom
        if prenom: criterias["prenom"] = prenom
        if ville: criterias["ville"] = ville
        if email: criterias["email"] = email
        if telephone: criterias["telephone"] = telephone
        if date_naissance: criterias["date_naissance"] = date_naissance

        _h("Recherche BRIHUB (api.brihub.ru)")
        _info(f"Critères : {json.dumps(criterias, ensure_ascii=False)}")
        resp = self.brix.search(criterias, per_page=50, flexible=flexible)
        self.brix.print_results(resp)
        brix_results = (resp.get("data") or {}).get("results", [])
        return brix_results

    # -------- Recherche web associée --------
    def search_web(self, nom=None, prenom=None, telephone=None, ville=None):
        queries = []
        if prenom and nom: queries.append(f'"{prenom} {nom}"')
        elif nom: queries.append(f'"{nom}"')
        if telephone:
            clean = re.sub(r"[^\d+]","", telephone)
            queries.extend([f'"{telephone}"', f'"{clean}"'])
        if ville and nom: queries.append(f'"{nom}" "{ville}"')
        if prenom and nom: queries.append(f'"{prenom} {nom}" site:linkedin.com')
        if prenom and nom: queries.append(f'"{prenom} {nom}" site:facebook.com')

        _h("Recherche WEB associée")
        all_results = []
        for q in queries:
            _info(f"Requête : {q}")
            res = self.engine.multi(q, 8)
            _info(f"  -> {len(res)} résultats")
            all_results.extend(res)
        unique = self._dedup(all_results)
        _info(f"{len(unique)} résultats web uniques")
        self._print_web(unique)
        return unique

    def search_telephone(self, tel):
        _h(f"Recherche téléphone : {tel}")
        clean = re.sub(r"[^\d+]","", tel)
        # 1) BrixHub
        _info("1) BrixHub")
        resp = self.brix.search({"telephone": clean}, per_page=50, flexible=True)
        self.brix.print_results(resp)
        # 2) Web
        _info("2) Recherche web")
        queries = [
            f'"{tel}"', f'"{clean}"',
            f'"{clean}" site:pagesjaunes.fr',
            f'"{clean}" site:118712.fr',
            f'"{clean}" site:facebook.com',
            f'"{clean}" (arnaque OR spam)'
        ]
        all_results = []
        for q in queries:
            res = self.engine.multi(q, 6)
            all_results.extend(res)
        unique = self._dedup(all_results)
        self._print_web(unique)
        _info("Reverse lookup manuels :")
        for n, u in [("Truecaller",f"https://www.truecaller.com/search/fr/{clean}"),
                     ("Sync.me",f"https://sync.me/search/?number={clean}"),
                     ("Numlookup",f"https://www.numlookup.com/?number={clean}"),
                     ("PagesBlanches",f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={clean}")]:
            print(f"      \033[36m{n:<14} {u}\033[0m")
        return unique

    def search_email(self, email):
        _h(f"Recherche email : {email}")
        _info("1) BrixHub")
        resp = self.brix.search({"email": email}, per_page=50, flexible=True)
        self.brix.print_results(resp)
        _info("2) Web")
        res = self.engine.multi(f'"{email}"', 15)
        self._print_web(res)
        return res

    def search_adresse(self, adresse):
        _h(f"Recherche adresse : {adresse}")
        _info("1) BrixHub (par adresse)")
        resp = self.brix.search({"adresse": adresse}, per_page=50, flexible=True)
        self.brix.print_results(resp)
        _info("2) Web")
        res = self.engine.multi(f'"{adresse}"', 10)
        self._print_web(res)
        return res

    def search_iban(self, iban):
        _h(f"Recherche IBAN : {iban}")
        resp = self.brix.search({"iban": iban}, per_page=20, flexible=True)
        self.brix.print_results(resp)
        return resp

    def search_siret(self, siret):
        _h(f"Recherche SIRET : {siret}")
        resp = self.brix.search({"siret": siret}, per_page=20, flexible=True)
        self.brix.print_results(resp)
        return resp

    def search_steam(self, steam_id):
        _h(f"Recherche Steam ID : {steam_id}")
        resp = self.brix.search({"steam_id": steam_id}, per_page=20, flexible=True)
        self.brix.print_results(resp)
        return resp

# =====================================================================
# COLLECTEUR PRINCIPAL
# =====================================================================
class OSINTCollector:
    def __init__(self, target):
        self.target = target
        self.report = {"target":target,"timestamp":datetime.now().isoformat(),"sections":{}}

    def _save(self, name="osint_report"):
        os.makedirs("output", exist_ok=True)
        try:
            with open(f"output/{name}.json","w",encoding="utf-8") as f:
                json.dump(self.report, f, indent=2, default=str)
        except PermissionError:
            _no("Permission refusée sur output/ - sudo chown -R $USER:$USER .")
            return
        parts = ["<html><head><meta charset='utf-8'><style>",
                 "body{font-family:monospace;background:#0d1117;color:#c9d1d9;padding:30px}",
                 "h1{color:#58a6ff}h2{color:#f0f6fc;border-bottom:1px solid #30363d}",
                 "pre{background:#161b22;padding:12px;border-radius:6px;color:#7ee787}",
                 "</style></head><body>",
                 f"<h1>Rapport OSINT - {self.report['target']}</h1>",
                 f"<p>{self.report['timestamp']}</p>"]
        for k,v in self.report["sections"].items():
            parts.append(f"<h2>{k}</h2><pre>{json.dumps(v,indent=2,default=str)}</pre>")
        parts.append("</body></html>")
        with open(f"output/{name}.html","w",encoding="utf-8") as f:
            f.write("".join(parts))
        _ok(f"Rapport : output/{name}.json")

    def hibp(self, value):
        _h(f"Vérification fuites : {value}")
        h = hashlib.sha1(value.encode()).hexdigest().upper()
        prefix, suffix = h[:5], h[5:]
        try:
            r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}",
                             headers=UA, timeout=10)
            if r.status_code == 200:
                for line in r.text.splitlines():
                    if line.startswith(suffix):
                        cnt = int(line.split(":")[1])
                        _warn(f"TROUVÉ dans {cnt} fuites")
                        return {"found":True,"count":cnt}
        except Exception: pass
        _ok("Aucune fuite connue")
        return {"found":False,"count":0}

    def email_analysis(self):
        e = self.target
        print(f"\n\033[1m\033[35m{'═'*60}\033[0m")
        print(f"\033[1m\033[35m  ANALYSE EMAIL : {e}\033[0m")
        print(f"\033[1m\033[35m{'═'*60}\033[0m")
        ids = IdentitySearch()
        self.report["sections"]["hibp"] = self.hibp(e)
        brix = ids.search_email(e)
        self.report["sections"]["brihub"] = brix
        self.report["sections"]["social"] = SocialChecker().check_username(e.split("@")[0])
        self._save("osint_email")

    def username_analysis(self):
        u = self.target
        print(f"\n\033[1m\033[35m{'═'*60}\033[0m")
        print(f"\033[1m\033[35m  RECHERCHE PSEUDO : {u}\033[0m")
        print(f"\033[1m\033[35m{'═'*60}\033[0m")
        sc = SocialChecker(); eng = SearchEngine()
        self.report["sections"]["social"] = sc.check_username(u)
        _h("Recherche web")
        web = eng.multi(f'"{u}"', 15)
        for i,r in enumerate(web[:10],1):
            print(f"  \033[33m[{i}] {r['title'][:80]}\033[0m")
            print(f"      \033[36m{r['url'][:100]}\033[0m")
        self.report["sections"]["web"] = web
        self._save("osint_username")

    def ip_analysis(self, ip):
        _h(f"Analyse IP : {ip}")
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            d = r.json()
            for k in ["country","regionName","city","isp","org","as","lat","lon"]:
                if k in d: print(f"  \033[33m{k:<12}\033[0m {d[k]}")
            self.report["sections"]["ip"] = d
        except Exception as e:
            _no(str(e))
        self._save("osint_ip")

    def run_full(self):
        t = self.target
        if "@" in t: self.email_analysis()
        elif re.match(r"^\d+\.\d+\.\d+\.\d+$", t): self.ip_analysis(t)
        else: self.domain_analysis()
        self._save("osint_report")

    def domain_analysis(self):
        d = self.target
        eng = SearchEngine()
        _h(f"Indexation domaine {d}")
        res = eng.multi(f"site:{d}", 20)
        for i,r in enumerate(res[:15],1):
            print(f"  \033[33m[{i}] {r['title'][:80]}\033[0m")
            print(f"      \033[36m{r['url'][:100]}\033[0m")
        self.report["sections"]["dorks"] = res
        self._save("osint_domain")

    # --- Identité complète ---
    def identity_search(self, nom=None, prenom=None, ville=None, telephone=None,
                        email=None, date_naissance=None, adresse=None,
                        iban=None, siret=None, steam_id=None):
        ids = IdentitySearch()
        result = {}

        # BRIHUB principal
        if any([nom, prenom, ville, email, telephone, date_naissance]):
            result["brihub"] = ids.search_full(nom, prenom, ville, email,
                                               telephone, date_naissance)

        # Recherche web associée
        result["web"] = ids.search_web(nom, prenom, telephone, ville)

        # Cas spéciaux
        if iban:
            result["iban"] = ids.search_iban(iban)
        if siret:
            result["siret"] = ids.search_siret(siret)
        if steam_id:
            result["steam"] = ids.search_steam(steam_id)

        self.report["sections"]["identity"] = result
        self._save("osint_identity")

    @staticmethod
    def batch(filepath):
        if not os.path.exists(filepath):
            _no(f"Fichier introuvable : {filepath}"); return
        with open(filepath) as f:
            for line in f:
                t = line.strip()
                if t:
                    print(f"\n\033[35m▶ {t}\033[0m")
                    OSINTCollector(t).run_full()
                    time.sleep(1)

# =====================================================================
# MENU
# =====================================================================
def run_interactive():
    while True:
        os.system("clear" if os.name == "posix" else "cls")
        print("""\033[1m\033[35m
┌──────────────────────────────────────────────────┐
│         OSINT AVANCÉ v5.6 - MENU                 │
├──────────────────────────────────────────────────┤
│  \033[36m[ 1]\033[0m Cible unique (email/domaine/IP)             │
│  \033[36m[ 2]\033[0m Cible multiple (fichier)                     │
│  \033[36m[ 3]\033[0m Recherche pseudo                              │
│  \033[36m[ 4]\033[0m Analyse email (BrixHub + web + HIBP)         │
│  \033[36m[ 5]\033[0m Analyse domaine                             │
│  \033[36m[ 6]\033[0m Analyse IP (géoloc)                           │
│  \033[36m[ 8]\033[0m \033[1mBRIHUB : Nom + Prénom\033[0m                       │
│  \033[36m[ 9]\033[0m \033[1mBRIHUB : Nom + Ville\033[0m                        │
│  \033[36m[10]\033[0m \033[1mBRIHUB : Téléphone\033[0m                         │
│  \033[36m[11]\033[0m \033[1mBRIHUB : Email\033[0m                             │
│  \033[36m[12]\033[0m \033[1mBRIHUB : IBAN\033[0m                              │
│  \033[36m[13]\033[0m \033[1mBRIHUB : SIRET\033[0m                             │
│  \033[36m[14]\033[0m \033[1mBRIHUB : Steam ID\033[0m                          │
│  \033[36m[15]\033[0m \033[1mRecherche identité COMPLÈTE (multi-critères)\033[0m │
│  \033[36m[16]\033[0m Vérification fuites (HIBP)                    │
│  \033[36m[ 0]\033[0m Retour                                         │
└──────────────────────────────────────────────────┘\033[0m""")
        ch = input("Choix > ").strip()
        if ch == "0": return
        try:
            if ch == "1":   OSINTCollector(input("Cible : ").strip()).run_full()
            elif ch == "2": OSINTCollector.batch(input("Fichier : ").strip() or "payloads/osint_targets.txt")
            elif ch == "3": OSINTCollector(input("Pseudo : ").strip()).username_analysis()
            elif ch == "4": OSINTCollector(input("Email : ").strip()).email_analysis()
            elif ch == "5": OSINTCollector(input("Domaine : ").strip()).domain_analysis()
            elif ch == "6": OSINTCollector(input("IP : ").strip()).run_full()
            elif ch == "8":
                nom = input("Nom de famille : ").strip()
                prenom = input("Prénom : ").strip()
                ville = input("Ville (vide) : ").strip() or None
                OSINTCollector(f"{prenom} {nom}").identity_search(nom=nom, prenom=prenom, ville=ville)
            elif ch == "9":
                nom = input("Nom de famille : ").strip()
                ville = input("Ville : ").strip()
                OSINTCollector(f"{nom} @ {ville}").identity_search(nom=nom, ville=ville)
            elif ch == "10":
                tel = input("Téléphone : ").strip()
                OSINTCollector(tel).identity_search(telephone=tel)
            elif ch == "11":
                e = input("Email : ").strip()
                OSINTCollector(e).identity_search(email=e)
            elif ch == "12":
                iban = input("IBAN : ").strip()
                OSINTCollector(iban).identity_search(iban=iban)
            elif ch == "13":
                siret = input("SIRET : ").strip()
                OSINTCollector(siret).identity_search(siret=siret)
            elif ch == "14":
                sid = input("Steam ID : ").strip()
                OSINTCollector(sid).identity_search(steam_id=sid)
            elif ch == "15":
                nom = input("Nom de famille (vide) : ").strip() or None
                prenom = input("Prénom (vide) : ").strip() or None
                ville = input("Ville (vide) : ").strip() or None
                tel = input("Téléphone (vide) : ").strip() or None
                email = input("Email (vide) : ").strip() or None
                dn = input("Date de naissance AAAA-MM-JJ (vide) : ").strip() or None
                iban = input("IBAN (vide) : ").strip() or None
                siret = input("SIRET (vide) : ").strip() or None
                sid = input("Steam ID (vide) : ").strip() or None
                OSINTCollector(f"{prenom or ''} {nom or ''}").identity_search(
                    nom=nom, prenom=prenom, ville=ville, telephone=tel,
                    email=email, date_naissance=dn, iban=iban, siret=siret,
                    steam_id=sid)
            elif ch == "16":
                OSINTCollector("").hibp(input("Email/hash : ").strip())
        except Exception as e:
            print(f"\033[31m[!]\033[0m {e}")
        input("\n[Entrée pour continuer]")
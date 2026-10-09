# -*- coding: utf-8 -*-
# Module 12 : campagne phishing
import json, os, smtplib, ssl, time, random, uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class PhishingMail:
    def __init__(self, cfg):
        self.cfg = cfg
        self.report = []

    def load_targets(self):
        out = []
        with open(self.cfg["targets"],"r",encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(";")
                if len(parts) >= 3:
                    out.append({"email":parts[0],"nom":parts[1],"prenom":parts[2]})
        return out

    def build(self, target, tpl):
        uid = uuid.uuid4().hex[:12]
        link = f'{self.cfg["redirect_url"]}?id={uid}'
        pixel = f'{self.cfg["redirect_url"]}/pixel?id={uid}'
        html = (tpl.replace("{{nom}}",target["nom"])
                   .replace("{{prenom}}",target["prenom"])
                   .replace("{{email}}",target["email"])
                   .replace("{{lien}}",link)
                   .replace("{{pixel}}",pixel))
        return uid, html

    def send(self, target, tpl):
        uid, html = self.build(target, tpl)
        msg = MIMEMultipart("related")
        msg["From"] = f'{self.cfg["from_name"]} <{self.cfg["from_email"]}>'
        msg["To"] = target["email"]
        msg["Subject"] = self.cfg["subject"]
        msg["Reply-To"] = self.cfg["reply_to"]
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        if self.cfg["smtp_tls"]:
            with smtplib.SMTP(self.cfg["smtp_host"], self.cfg["smtp_port"]) as s:
                s.starttls(context=ctx)
                s.login(self.cfg["smtp_user"], self.cfg["smtp_pass"])
                s.sendmail(self.cfg["from_email"], target["email"], msg.as_string())
        else:
            with smtplib.SMTP_SSL(self.cfg["smtp_host"], self.cfg["smtp_port"], context=ctx) as s:
                s.login(self.cfg["smtp_user"], self.cfg["smtp_pass"])
                s.sendmail(self.cfg["from_email"], target["email"], msg.as_string())
        self.report.append({"uid":uid,"email":target["email"],
                            "sent":datetime.now().isoformat()})

    def run(self):
        tpl = open(self.cfg["template"],encoding="utf-8").read()
        targets = self.load_targets()
        print(f"[i] {len(targets)} cibles")
        for i,t in enumerate(targets,1):
            try:
                self.send(t, tpl)
                print(f"  [+] {i}/{len(targets)} {t['email']}")
            except Exception as e:
                print(f"  [!] {t['email']} : {e}")
            time.sleep(random.uniform(self.cfg["delay_min"], self.cfg["delay_max"]))
        os.makedirs("output", exist_ok=True)
        with open("output/phishing_report.json","w",encoding="utf-8") as f:
            json.dump(self.report, f, indent=2)

def run_interactive():
    from toolkit import ok, err, info, section, ask, confirm
    section("CAMPAGNE PHISHING")
    with open("config.json") as f: cfg = json.load(f)["phishing"]
    if not cfg.get("smtp_host"):
        err("Configurez la section 'phishing' dans config.json")
        info("Champs requis : smtp_host, smtp_user, smtp_pass, from_email, subject")
        return
    if not os.path.exists(cfg["targets"]):
        err(f"Fichier cibles introuvable : {cfg['targets']}"); return
    if not os.path.exists(cfg["template"]):
        err(f"Template introuvable : {cfg['template']}"); return
    info(f"Serveur : {cfg['smtp_host']}:{cfg['smtp_port']}")
    if not confirm("Lancer la campagne ?"): return
    PhishingMail(cfg).run()
    ok("Rapport : output/phishing_report.json")
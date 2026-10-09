# -*- coding: utf-8 -*-
# Module 8 : privesc énumération + détection exploitable
import os, subprocess, json, re
from datetime import datetime

CHECKS = [
    ("SUID", "find / -perm -4000 -type f 2>/dev/null"),
    ("SGID", "find / -perm -2000 -type f 2>/dev/null"),
    ("SUDO", "sudo -n -l 2>/dev/null"),
    ("CRON", "cat /etc/crontab 2>/dev/null; ls -la /etc/cron.* 2>/dev/null"),
    ("KERNEL", "uname -a"),
    ("CAPS", "getcap -r / 2>/dev/null"),
    ("WRITABLE_DIRS", "find / -writable -type d 2>/dev/null | head -30"),
    ("WRITABLE_FILES", "find / -writable -type f 2>/dev/null | head -30"),
    ("PASSWD", "cat /etc/passwd 2>/dev/null"),
    ("ENV", "env"),
    ("DOCKER", "docker ps 2>/dev/null || echo 'no docker'"),
    ("NFS", "cat /etc/exports 2>/dev/null"),
    ("SYSTEMD_TIMERS", "systemctl list-timers 2>/dev/null | head -20"),
    ("NETSTAT", "ss -tulnp 2>/dev/null || netstat -tulnp 2>/dev/null")
]

GTFOBINS = ["nmap","vim","find","bash","sh","python","perl","ruby","node",
            "awk","sed","tar","zip","gcc","cp","mv","less","more","man",
            "nano","ftp","wget","curl","env","tee","dd"]

def check_gtfobins(suid_files):
    matches = []
    for f in suid_files:
        name = os.path.basename(f)
        if name in GTFOBINS:
            matches.append(f)
    return matches

class PrivEsc:
    def __init__(self):
        self.report = {"timestamp": datetime.now().isoformat(), "sections": {}}

    def run(self):
        for name, cmd in CHECKS:
            try:
                out = subprocess.check_output(cmd, shell=True,
                                              stderr=subprocess.DEVNULL,
                                              timeout=30).decode(errors="ignore")
            except Exception:
                out = ""
            self.report["sections"][name] = out
        # Détection GTFOBins
        suid = self.report["sections"].get("SUID","")
        suid_files = [l.split()[-1] for l in suid.splitlines() if " -> " in l or "/" in l]
        suid_files = [f for f in re.findall(r"/\S+", suid)]
        self.report["gtfobins"] = check_gtfobins(suid_files)
        os.makedirs("output", exist_ok=True)
        with open("output/privesc_report.json","w",encoding="utf-8") as f:
            json.dump(self.report, f, indent=2)
        with open("output/privesc_report.txt","w",encoding="utf-8") as f:
            for k,v in self.report["sections"].items():
                f.write(f"===== {k} =====\n{v}\n\n")
            f.write(f"===== GTFOBINS EXPLOITABLES =====\n")
            for g in self.report["gtfobins"]:
                f.write(f"{g}\n")
        return self.report

def run_interactive():
    from toolkit import ok, err, info, warn, section
    section("ÉNUMÉRATION PRIVILÈGES")
    info("Analyse du système...")
    pe = PrivEsc()
    r = pe.run()
    for name in r["sections"]:
        out = r["sections"][name]
        lines = [l for l in out.splitlines() if l.strip()][:5]
        warn(f"{name} : {len(out.splitlines())} lignes")
        for l in lines[:3]: print(f"    {l[:100]}")
    if r["gtfobins"]:
        section("GTFOBins potentiellement exploitables")
        for g in r["gtfobins"]:
            ok(g)
    ok("Rapports : output/privesc_report.json / .txt")
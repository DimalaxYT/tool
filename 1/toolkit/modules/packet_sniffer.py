# -*- coding: utf-8 -*-
# Module 3 : sniffer + analyse + stats
import re, os, json, threading, time
from collections import Counter
from datetime import datetime

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw, DNS, DNSQR
except ImportError:
    sniff = None

SENSITIVE = re.compile(r"(password|passwd|pwd|login|user|token|api[_-]?key|authorization|bearer|session)", re.I)

class PacketSniffer:
    def __init__(self, iface, flt):
        self.iface = iface
        self.filter = flt
        self.stats = Counter()
        self.creds = []
        self.ips = Counter()
        self.start = datetime.now()

    def cb(self, pkt):
        if not pkt.haslayer(IP): return
        self.stats["total"] += 1
        self.ips[pkt[IP].src] += 1
        self.ips[pkt[IP].dst] += 1
        if pkt.haslayer(TCP): self.stats["TCP"] += 1
        if pkt.haslayer(UDP): self.stats["UDP"] += 1
        if pkt.haslayer(ICMP): self.stats["ICMP"] += 1
        if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
            try:
                q = pkt[DNSQR].qname.decode(errors="ignore")
                self.stats["DNS"] += 1
                self.creds.append({"type":"dns","query":q,"src":pkt[IP].src})
            except Exception: pass
        if pkt.haslayer(Raw):
            try:
                txt = pkt[Raw].load.decode("utf-8", errors="ignore")
                if SENSITIVE.search(txt):
                    self.creds.append({
                        "type":"sensitive","src":pkt[IP].src,"dst":pkt[IP].dst,
                        "data":txt[:300]
                    })
                    print(f"  {C_GREEN}[!] {pkt[IP].src}->{pkt[IP].dst} : {txt[:120]}{C_RESET}")
            except Exception: pass

    def start_capture(self, duration=60):
        t0 = time.time()
        sniff(iface=self.iface, filter=self.filter, prn=self.cb,
              store=0, timeout=duration)

    def save(self):
        os.makedirs("output", exist_ok=True)
        with open("output/sniff_report.json","w",encoding="utf-8") as f:
            json.dump({
                "duration": str(datetime.now()-self.start),
                "stats": dict(self.stats),
                "top_ips": self.ips.most_common(20),
                "credentials": self.creds,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)

C_GREEN = "\033[32m"; C_RESET = "\033[0m"

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask
    section("SNIFFER DE PAQUETS")
    iface = ask("Interface", "eth0")
    flt = ask("Filtre BPF", "ip")
    dur = int(ask("Durée (secondes)", "60"))
    info(f"Capture sur {iface}, filtre='{flt}', durée={dur}s")
    s = PacketSniffer(iface, flt)
    try:
        s.start_capture(dur)
    except KeyboardInterrupt:
        pass
    s.save()
    section("Statistiques")
    for k,v in s.stats.items(): print(f"  {k:<10} {v}")
    section("Top IP")
    for ip,n in s.ips.most_common(10): print(f"  {ip:<18} {n}")
    section(f"Credentials/DNS capturés : {len(s.creds)}")
    ok("Rapport : output/sniff_report.json")
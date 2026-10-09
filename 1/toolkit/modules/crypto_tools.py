# -*- coding: utf-8 -*-
# Module 10 : cassage hash + AES-256 + génération
import hashlib, os, json, time, base64, secrets
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

HASH_ALGOS = {"md5":32,"sha1":40,"sha224":56,"sha256":64,"sha384":96,"sha512":128}

class CryptoTools:
    def detect(self, h):
        for name,length in HASH_ALGOS.items():
            if len(h) == length: return name
        return None

    def brute_dict(self, target, wordlist):
        algo = self.detect(target)
        if not algo: return None, 0
        count = 0
        with open(wordlist,"r",encoding="utf-8",errors="ignore") as f:
            for line in f:
                w = line.strip()
                count += 1
                if hashlib.new(algo, w.encode()).hexdigest() == target.lower():
                    return w, count
        return None, count

    def brute_mask(self, target, charset, maxlen=6):
        algo = self.detect(target)
        if not algo: return None
        import itertools
        for L in range(1, maxlen+1):
            for combo in itertools.product(charset, repeat=L):
                w = "".join(combo)
                if hashlib.new(algo, w.encode()).hexdigest() == target.lower():
                    return w
        return None

    def aes_encrypt(self, key, data):
        iv = os.urandom(16)
        c = Cipher(algorithms.AES(key), modes.CBC(iv),
                   backend=default_backend()).encryptor()
        pad = 16 - (len(data) % 16)
        return iv + c.update(data + bytes([pad])*pad) + c.finalize()

    def aes_decrypt(self, key, blob):
        iv, ct = blob[:16], blob[16:]
        c = Cipher(algorithms.AES(key), modes.CBC(iv),
                   backend=default_backend()).decryptor()
        pt = c.update(ct) + c.finalize()
        return pt[:-pt[-1]]

def run_interactive():
    from toolkit import ok, err, info, warn, section, ask, confirm, C
    section("OUTILS CRYPTO")
    print("  1. Casser un hash (dictionnaire)")
    print("  2. Casser un hash (force brute masque)")
    print("  3. Chiffrer AES-256")
    print("  4. Déchiffrer AES-256")
    print("  5. Générer hash d'un mot")
    choice = ask("Choix","1")
    if choice == "1":
        h = ask("Hash cible")
        wl = ask("Wordlist", "payloads/wordlist_pass.txt")
        algo = CryptoTools().detect(h)
        info(f"Algorithme détecté : {algo}")
        t0 = time.time()
        r, n = CryptoTools().brute_dict(h, wl)
        dt = time.time()-t0
        if r: ok(f"TROUVÉ : {r} ({n} essais, {dt:.1f}s)")
        else: err(f"Non trouvé ({n} essais, {dt:.1f}s)")
    elif choice == "2":
        h = ask("Hash cible")
        charset = ask("Charset", "abcdefghijklmnopqrstuvwxyz0123456789")
        maxlen = int(ask("Longueur max","6"))
        info("Force brute en cours...")
        r = CryptoTools().brute_mask(h, charset, maxlen)
        if r: ok(f"TROUVÉ : {r}")
        else: err("Non trouvé")
    elif choice == "3":
        data = ask("Données").encode()
        key = secrets.token_bytes(32)
        blob = CryptoTools().aes_encrypt(key, data)
        print(f"Clé (hex) : {key.hex()}")
        print(f"Blob (b64) : {base64.b64encode(blob).decode()}")
    elif choice == "4":
        key = bytes.fromhex(ask("Clé (hex)"))
        blob = base64.b64decode(ask("Blob (b64)"))
        print(CryptoTools().aes_decrypt(key, blob).decode(errors="ignore"))
    elif choice == "5":
        w = ask("Mot")
        for name in HASH_ALGOS:
            print(f"  {name:<8} {hashlib.new(name, w.encode()).hexdigest()}")
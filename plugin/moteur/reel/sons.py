"""Pose les sons sur la voix, à l'image près, au bon niveau, puis le volume final.

    sons.py reperes.json voix.wav sortie.wav [--master -18]

reperes.json : [{"t": 1.26, "son": "ui:zen/select", "niveau": "petit", "hauteur": 1.0}, ...]
- son : "ui:<pack>/<son>" (uisfx), "rsfx:<nom>" (reel-sfx), un chemin dans outils-son/sons-choisis (« gouttes/goutte-1.wav »),
  ou un chemin complet (son trouvé sur Openverse).
- niveau : "accent" (8 dB sous la voix), "petit" (13 dB sous), "tres_petit" (17 dB sous).
- hauteur : 0.9 = 10 % plus grave (facultatif).
Calage : le point posé sur t est mesuré par Real SFX (arrivée ou sommet pour un son de mouvement, début audible sinon).
"""
import argparse, json, subprocess, sys
import numpy as np
from _base import SONS, ICI, ffmpeg, real_sfx
SR = 48000
NIVEAUX = {"accent": 8, "petit": 13, "tres_petit": 17}
MOUVEMENT = ("whoosh", "swipe", "swell", "montee", "riser")

def chemin(son):
    if son.startswith("ui:"):
        pack, nom = son[3:].split("/"); return SONS / "real-sfx/vendor/node_modules/uisfx/sounds" / pack / f"{nom}.mp3"
    if son.startswith("rsfx:"):
        return next((SONS / "reel-sfx/reel_sfx/sounds").rglob(son[5:] + ".wav"))
    p = SONS / "sons-choisis" / son
    return p if p.exists() else __import__("pathlib").Path(son)

def ancre(p, son):
    c = real_sfx()
    if any(m in son for m in MOUVEMENT):
        a = c.arrival_landmarks(str(p))
        if not a: return 0.0
        off = c.arrive_offset(a, a["peak"]); return off if off is not None else a["peak"]
    return c.onset_time(str(p))

def lire(p, canaux=2):
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", str(p), "-ac", str(canaux), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(r, dtype=np.float32).reshape(-1, canaux).astype(np.float64)

def rms_db(x):
    e = np.sqrt(np.mean(x ** 2, axis=1)); h = int(.05 * SR)
    fr = [np.sqrt(np.mean(e[i:i + h] ** 2)) for i in range(0, max(1, len(e) - h), h)]
    return 20 * np.log10(max(max(fr), 1e-9))

def niveau_parole(v):
    m = v[:, 0]; h = int(.05 * SR)
    fr = np.array([20 * np.log10(np.sqrt(np.mean(m[i:i + h] ** 2)) + 1e-9) for i in range(0, len(m) - h, h)])
    return float(np.mean(fr[fr > np.percentile(fr, 60)]))

def main():
    a = argparse.ArgumentParser(); a.add_argument("reperes"); a.add_argument("voix"); a.add_argument("sortie"); a.add_argument("--master", type=float, default=-18)
    o = a.parse_args()
    reperes = json.load(open(o.reperes, encoding="utf-8")); v = lire(o.voix, 1); v = np.hstack([v, v]); parole = niveau_parole(v)
    piste = np.zeros((len(v) + SR, 2))
    for r in reperes:
        p = chemin(r["son"]); x = lire(p); x /= max(1e-9, np.abs(x).max()); an = ancre(p, r["son"])
        f = r.get("hauteur", 1.0)
        if f != 1.0:
            n = int(len(x) / f); x = np.stack([np.interp(np.arange(n) * f, np.arange(len(x)), x[:, c]) for c in (0, 1)], 1); an /= f
        x *= 10 ** ((parole - NIVEAUX[r.get("niveau", "petit")] - rms_db(x)) / 20)
        i = int((r["t"] - an) * SR)
        if i < 0: x = x[-i:]; i = 0
        n = min(len(x), len(piste) - i); piste[i:i + n] += x[:n]
    sys.path.insert(0, str(SONS / "reel-sfx")); from reel_sfx.mix import mix; from reel_sfx.wavio import write_wav
    m = np.asarray(mix(v, piste[:len(v)], SR, duck_db=3), dtype=np.float64)
    pk = np.abs(m).max(); m = m / pk * 0.89 if pk > 0.89 else m
    brut = o.sortie + ".brut.wav"; write_wav(brut, m, SR)
    subprocess.run([sys.executable, str(ICI / "master.py"), brut, o.sortie, str(o.master)], check=True)
    if not __import__("os").environ.get("STUDIO_GARDER_BRUT"): __import__("os").remove(brut)
    print(len(reperes), "sons posés")

if __name__ == "__main__":
    main()

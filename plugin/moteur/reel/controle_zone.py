"""Safe zone : vérifie par programme qu'aucun pixel ne sort de la zone sûre, sur les images de la vidéo rendue.

    controle_zone.py video.mp4 [--pas 0.25]

Zones : ressources/zones-securite.json (la plus stricte des plateformes) + 20 px de marge. Code de sortie 1 s'il y a une faute.
"""
import argparse, json, subprocess, sys
import numpy as np
from _base import PLUGIN, ffmpeg
MARGE = 20

def masques(Z):
    u = Z["zone_utile"]; m = MARGE
    zones = [("gauche", (0, 0, u["x_min"] + m, 1920)), ("droite", (u["x_max"] - m, 0, 1080, 1920)),
             ("haut", (0, 0, 1080, u["y_min"] + m)), ("bas", (0, u["y_max"] - m, 1080, 1920))]
    for z in Z["zones_interdites"]:
        zones.append((z["nom"], (z["x"] - m, z["y"] - m, z["x"] + z["largeur"] + m, z["y"] + z["hauteur"] + m)))
    return zones

def main():
    a = argparse.ArgumentParser(); a.add_argument("video"); a.add_argument("--pas", type=float, default=0.25); o = a.parse_args()
    Z = json.loads((PLUGIN / "ressources" / "zones-securite.json").read_text(encoding="utf-8"))["reel"]
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", o.video, "-vf", f"fps={1/o.pas},scale=1080:1920,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True, check=True).stdout
    images = np.frombuffer(r, dtype=np.uint8).reshape(-1, 1920, 1080).astype(int)
    fautes = []
    for k, im in enumerate(images):
        m = np.abs(im - im[5, 5]) > 40
        for nom, (x0, y0, x1, y1) in masques(Z):
            n = int(m[max(0, y0):y1, max(0, x0):x1].sum())
            if n: fautes.append({"t": round(k * o.pas, 2), "zone": nom, "pixels": n})
    print(json.dumps({"images": len(images), "fautes": fautes[:50], "ok": not fautes}, ensure_ascii=False, indent=1))
    sys.exit(1 if fautes else 0)

if __name__ == "__main__":
    main()

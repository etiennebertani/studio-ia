"""Rend la page d'animation en vidéo muette 1080 × 1920, 60 images/s, flou de mouvement sur 4 sous-images.

    rendu.py page.html noir|blanc sortie.mp4
"""
import base64, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _base import ffmpeg as _ffmpeg  # noqa: E402
FPS, SUB = 60, 4

def rendre(page, theme, sortie, ffmpeg=None):
    ffmpeg = ffmpeg or _ffmpeg()
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(Path(page).resolve().as_uri() + "?t=" + theme)
        pg.evaluate("document.fonts.load('400 48px P')"); pg.evaluate("document.fonts.load('500 48px P')"); pg.wait_for_timeout(300)
        n = int(pg.evaluate("DUREE") * FPS); d0 = time.time()
        ff = subprocess.Popen([ffmpeg, "-y", "-v", "error", "-f", "image2pipe", "-r", str(FPS), "-c:v", "png", "-i", "-", "-c:v", "libx264",
                               "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(sortie)], stdin=subprocess.PIPE)
        for i in range(n):
            ff.stdin.write(base64.b64decode(pg.evaluate("([t,s])=>image(t,s)", [i / FPS, SUB])))
        ff.stdin.close(); ff.wait(); b.close()
    return round(time.time() - d0)

if __name__ == "__main__":
    print("rendu en", rendre(*sys.argv[1:4]), "s")

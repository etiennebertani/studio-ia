"""Affiche l'état du Studio en JSON. Ne modifie rien.

    python3 verifier.py --data <dossier de données du plugin>
"""
import argparse
import json
import subprocess
from pathlib import Path

import commun

CONTROLE_MOTEUR = """
from pathlib import Path
import PIL, pillow_heif, cv2, numpy
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    assert Path(p.chromium.executable_path).exists()
print("ok")
"""


def moteur_pret(data):
    python = commun.python_moteur(data)
    if not python.exists():
        return False
    try:
        resultat = subprocess.run([str(python), "-c", CONTROLE_MOTEUR],
                                  capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.SubprocessError):
        return False
    return resultat.returncode == 0 and resultat.stdout.strip() == "ok"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    args = parser.parse_args()

    manque = [nom for nom in commun.OUTILS_SYSTEME if not commun.outil(nom)]
    if "ffprobe" in manque and "ffmpeg" in manque:
        manque.remove("ffprobe")
    if not commun.trouver_python():
        manque.append("python@3.13")

    print(json.dumps({
        "manque_systeme": manque,
        "moteur_pret": moteur_pret(args.data),
        "montage_pret": bool(commun.outil("whisper-cli") and commun.modele_whisper()),
        "espace": str(commun.ESPACE),
        "espace_existe": all((commun.ESPACE / d).is_dir() for d in commun.DOSSIERS),
        "configure": bool(commun.lire_config().get("accueil_termine")),
        "modules_disponibles": commun.modules_disponibles(),
        "raccourcis": [nom for nom in commun.noms_raccourcis()
                       if (Path(commun.SKILLS_PERSO) / nom / commun.MARQUE_RACCOURCI).exists()],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

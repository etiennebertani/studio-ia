"""Prépare le Studio : crée l'espace personnel et installe le moteur de rendu.

    python3 preparer.py --data <dossier de données du plugin>
    python3 preparer.py --data <dossier> --terminer-accueil
    python3 preparer.py --data <dossier> --modele-transcription

Peut être relancé sans risque : il ne supprime ni ne remplace aucun fichier personnel.
"""
import argparse
import subprocess
import sys
import urllib.request
from pathlib import Path

import commun


def creer_espace():
    for dossier in commun.DOSSIERS:
        (commun.ESPACE / dossier).mkdir(parents=True, exist_ok=True)


def lancer(commande):
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        sys.exit("Échec de : {}\n{}".format(" ".join(commande), resultat.stderr[-1500:]))


def installer_moteur(data):
    python_systeme = commun.trouver_python()
    if not python_systeme:
        sys.exit("Python 3.10 ou plus récent est introuvable.")
    Path(data).mkdir(parents=True, exist_ok=True)
    python = commun.python_moteur(data)
    if not python.exists():
        lancer([python_systeme, "-m", "venv", str(Path(data) / "venv")])
    requirements = commun.RACINE_PLUGIN / "moteur" / "requirements.txt"
    lancer([str(python), "-m", "pip", "install", "--quiet", "-r", str(requirements)])
    lancer([str(python), "-m", "playwright", "install", "chromium"])


def installer_modele():
    """Télécharge le modèle de transcription (environ 550 Mo), s'il manque."""
    if commun.modele_whisper():
        return
    commun.DOSSIER_MODELES.mkdir(parents=True, exist_ok=True)
    cible = commun.MODELES_WHISPER[0]
    temporaire = cible.with_suffix(".tmp")
    urllib.request.urlretrieve(commun.URL_MODELE, temporaire)
    temporaire.replace(cible)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--terminer-accueil", action="store_true")
    parser.add_argument("--modele-transcription", action="store_true")
    args = parser.parse_args()

    creer_espace()
    if args.modele_transcription:
        installer_modele()
        print("Modèle prêt.")
        return
    if args.terminer_accueil:
        commun.ecrire_config({"accueil_termine": True, "version_config": 1})
        print("Accueil terminé.")
        return
    installer_moteur(args.data)
    print("Moteur prêt.")


if __name__ == "__main__":
    main()

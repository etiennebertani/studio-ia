"""Chemins et réglages communs aux scripts du Studio. Bibliothèque standard uniquement."""
import json
import os
import shutil
import subprocess
from pathlib import Path

RACINE_PLUGIN = Path(__file__).resolve().parent.parent
ESPACE = Path.home() / "Studio" / "mon-espace"
CONFIG = ESPACE / ".studio.json"
NOMS = {
    "branding": "00. Branding", "reels": "01. Reels", "carrousels": "02. Carrousels", "posts": "03. Posts",
    "stories": "04. Stories", "youtube_podcast": "05. YouTube - Podcast",
    "articles": "06. Articles et newsletters", "references": "07. Références", "photos": "08. Photos",
    "rushs": "09. Rushs", "b_roll": "10. B-roll",
}
ARCHIVE = ESPACE / NOMS["branding"] / "archive-contenus.jsonl"
DOSSIERS = list(NOMS.values()) + [NOMS["branding"] + "/musiques", NOMS["branding"] + "/structures"]
SKILLS_PERSO = Path.home() / ".claude" / "skills"
MARQUE_RACCOURCI = ".studio-raccourci"
VERSION_PYTHON_MIN = (3, 10)
OUTILS_SYSTEME = ["ffmpeg", "ffprobe", "git"]
NOMS_PYTHON = ["python3.13", "python3.12", "python3.11", "python3.10", "python3"]
DOSSIERS_PYTHON = ["/opt/homebrew/bin", "/usr/local/bin"]


def version_python(chemin):
    """Renvoie (majeur, mineur), ou None si cet interpréteur ne répond pas."""
    try:
        sortie = subprocess.run(
            [chemin, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True, text=True, timeout=20, check=True,
        ).stdout.split()
        return int(sortie[0]), int(sortie[1])
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None


def trouver_python():
    """Trouve un Python assez récent, ou renvoie None."""
    chemin_recherche = os.pathsep.join([os.environ.get("PATH", "")] + DOSSIERS_PYTHON)
    for nom in NOMS_PYTHON:
        chemin = shutil.which(nom, path=chemin_recherche)
        if chemin:
            version = version_python(chemin)
            if version and version >= VERSION_PYTHON_MIN:
                return chemin
    return None


def python_moteur(data):
    return Path(data) / "venv" / "bin" / "python"


def outil(nom):
    chemin_recherche = os.pathsep.join([os.environ.get("PATH", "")] + DOSSIERS_PYTHON)
    return shutil.which(nom, path=chemin_recherche)


def lire_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ecrire_config(valeurs):
    config = lire_config()
    config.update(valeurs)
    ESPACE.mkdir(parents=True, exist_ok=True)
    temporaire = CONFIG.with_suffix(".tmp")
    temporaire.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporaire.replace(CONFIG)


def modules_disponibles():
    """Les modules de création réellement présents dans le plugin."""
    dossier = RACINE_PLUGIN / "skills"
    return [nom for nom in ("style", "carrousel", "legende", "drive", "reel", "story", "post")
            if (dossier / nom / "SKILL.md").is_file()]


def noms_raccourcis():
    return ["start"] + modules_disponibles()

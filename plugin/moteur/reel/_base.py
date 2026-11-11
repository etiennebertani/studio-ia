"""Chemins partagés par les outils du reel : moteur du plugin, caisse à outils du son, ffmpeg."""
import sys
from pathlib import Path
ICI = Path(__file__).resolve().parent
MOTEUR = ICI.parent
PLUGIN = MOTEUR.parent
SONS = PLUGIN / "outils-son"
sys.path.insert(0, str(MOTEUR))
import commun  # noqa: E402

def ffmpeg():
    return commun.outil("ffmpeg")

def real_sfx():
    """Les fonctions de mesure de Real SFX (Clipwing, scripts MIT), embarquées dans outils-son."""
    sys.path.insert(0, str(SONS / "real-sfx" / "scripts"))
    import common
    return common

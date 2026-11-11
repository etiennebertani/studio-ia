"""Temps fin de chaque mot avec whisper.cpp, à donner ensuite à calage_mots.py.

    transcrire_mots.py voix.wav dtw.json

Réglages indispensables (mesurés le 11 novembre 2026) : -nfa (sans flash attention, sinon les temps DTW sont faux),
-ojf (temps de chaque morceau de mot) et --dtw large.v3.turbo.
"""
import subprocess, sys, tempfile, shutil
from pathlib import Path
from _base import commun, ffmpeg

def transcrire(voix, sortie, langue="fr"):
    cli = commun.outil("whisper-cli"); modele = commun.modele_whisper()
    if not cli or not modele:
        raise SystemExit("whisper-cli ou son modèle manque : lance preparer.py")
    with tempfile.TemporaryDirectory() as d:
        wav = Path(d) / "voix16k.wav"
        subprocess.run([ffmpeg(), "-y", "-v", "error", "-i", str(voix), "-ac", "1", "-ar", "16000", str(wav)], check=True)
        subprocess.run([cli, "-m", str(modele), "-f", str(wav), "-l", langue, "-nfa", "-ojf", "--dtw", "large.v3.turbo",
                        "-of", str(Path(d) / "dtw")], check=True, capture_output=True)
        shutil.copy(Path(d) / "dtw.json", sortie)

if __name__ == "__main__":
    transcrire(sys.argv[1], sys.argv[2])
    print("temps fins écrits :", sys.argv[2])

"""Améliore la voix avec DeepFilterNet, téléchargé une seule fois, en version figée et vérifiée.

    python voix.py etat
    python voix.py installer
    python voix.py ameliorer --entree <audio ou vidéo> --sortie <fichier.wav> [--attenuation 40]

DeepFilterNet est sous licence MIT ou Apache 2.0 (ressources/licences/DeepFilterNet-LICENSE-MIT.txt).
Sans DeepFilterNet (ordinateur non compatible ou téléchargement impossible), la voix passe par le filtre
de ffmpeg, et la sortie le signale : rien ne s'arrête.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

import commun

VERSION = "0.5.6"
BINAIRES = {
    "arm64": ("deep-filter-0.5.6-aarch64-apple-darwin", "4601e7f4e4c03e59a4c5b5000216ef3add3e808799cfccd95e14e83ea4611081"),
    "x86_64": ("deep-filter-0.5.6-x86_64-apple-darwin", "d3be84003acb7c23e738ad7f70a158ec779a8d233a82e7fa3e717d112eb5b50f"),
}
URL = "https://github.com/Rikorose/DeepFilterNet/releases/download/v{}/{}"
DOSSIER = Path.home() / "Library/Application Support/Studio IA/outils"
FILTRE_REPLI = "highpass=f=80,afftdn=nr=12:nf=-30:tn=1"
TAUX = 48000


def binaire():
    choix = BINAIRES.get(platform.machine()) if platform.system() == "Darwin" else None
    return (DOSSIER / choix[0], choix[1]) if choix else (None, None)


def empreinte(chemin):
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def etat():
    chemin, attendu = binaire()
    if chemin is None:
        return {"pret": False, "raison": "ordinateur_non_compatible"}
    if not chemin.is_file():
        return {"pret": False, "raison": "pas_installe"}
    if empreinte(chemin) != attendu:
        return {"pret": False, "raison": "fichier_non_conforme"}
    return {"pret": True, "version": VERSION, "chemin": str(chemin)}


def installer():
    chemin, attendu = binaire()
    if chemin is None:
        return {"pret": False, "raison": "ordinateur_non_compatible"}
    if etat()["pret"]:
        return etat()
    DOSSIER.mkdir(parents=True, exist_ok=True)
    temporaire = chemin.with_suffix(".tmp")
    try:
        urllib.request.urlretrieve(URL.format(VERSION, chemin.name), temporaire)
    except OSError as erreur:
        temporaire.unlink(missing_ok=True)
        return {"pret": False, "raison": "telechargement_impossible", "detail": str(erreur)[:200]}
    if empreinte(temporaire) != attendu:
        temporaire.unlink(missing_ok=True)
        return {"pret": False, "raison": "fichier_non_conforme"}
    temporaire.chmod(0o755)
    temporaire.replace(chemin)
    return etat()


def _lire(chemin):
    import numpy as np
    with wave.open(str(chemin), "rb") as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64)


def _ecrire(chemin, echantillons):
    import numpy as np
    with wave.open(str(chemin), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(TAUX)
        f.writeframes(echantillons.clip(-32768, 32767).astype(np.int16).tobytes())


def _decalage(reference, traite):
    """Le petit retard que DeepFilterNet peut garder, mesuré sur quelques secondes de voix."""
    import numpy as np
    a, b = TAUX, min(len(reference), len(traite), TAUX * 6)
    if b - a < TAUX:
        return 0
    c = np.correlate(traite[a:b], reference[a:b], "full")
    lag = int(np.argmax(c) - (b - a - 1))
    return lag if abs(lag) < TAUX // 10 else 0


def ameliorer(entree, sortie, attenuation=40):
    ffmpeg = commun.outil("ffmpeg")
    sortie = Path(sortie)
    with tempfile.TemporaryDirectory() as dossier:
        brut = Path(dossier) / "voix.wav"
        # 3 dB de marge avant le traitement : DeepFilterNet ne doit jamais saturer.
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(entree), "-vn", "-ac", "1", "-ar", str(TAUX),
                        "-af", "volume=-3dB", str(brut)], check=True)
        e = etat()
        if e["pret"]:
            traite_dossier = Path(dossier) / "traite"
            r = subprocess.run([e["chemin"], "-D", "-a", str(attenuation), "-o", str(traite_dossier), str(brut)],
                               capture_output=True, text=True)
            traite = traite_dossier / brut.name
            if r.returncode == 0 and traite.is_file():
                import numpy as np
                ref, voix = _lire(brut), _lire(traite)
                lag = _decalage(ref, voix)
                if lag:
                    voix = np.roll(voix, -lag)
                crete = float(np.abs(voix).max()) or 1.0
                if crete > 0.89 * 32768:
                    voix = voix * (0.708 * 32768 / crete)
                _ecrire(sortie, voix[:len(ref)])
                return {"ok": True, "methode": "deepfilternet", "version": VERSION, "decalage_corrige": lag}
        subprocess.run([ffmpeg, "-y", "-v", "error", "-i", str(brut), "-af", FILTRE_REPLI, "-ar", str(TAUX), str(sortie)], check=True)
        return {"ok": True, "methode": "repli_ffmpeg", "raison": e.get("raison", "echec_deepfilternet")}


def main():
    p = argparse.ArgumentParser()
    a = p.add_subparsers(dest="action", required=True)
    a.add_parser("etat")
    a.add_parser("installer")
    q = a.add_parser("ameliorer")
    q.add_argument("--entree", required=True)
    q.add_argument("--sortie", required=True)
    q.add_argument("--attenuation", type=int, default=40)
    args = p.parse_args()
    if args.action == "etat":
        r = etat()
    elif args.action == "installer":
        r = installer()
    else:
        r = ameliorer(args.entree, args.sortie, args.attenuation)
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()

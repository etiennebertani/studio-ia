"""Range les slides d'un carrousel par variante et les date dans l'ordre.

    python3 ranger_variantes.py --dossier <final> [--noms 01=noir 02=blanc]

1. S'il y a plusieurs variantes (le numéro avant -slide-nn), chacune va dans son propre dossier de final/ :
   le nom donné par --noms, sinon le style lu dans le nom du fichier (tweet, texte-image…).
   texte.txt et legendes.txt restent dans final/, à côté des dossiers.
2. Chaque slide reçoit une date de prise de vue décalée d'une seconde (slide 1 à hh:mm:00, slide 2 à hh:mm:01…),
   écrite dans ses métadonnées sans toucher à l'image. Photos, sur Mac comme sur iPhone, les range alors dans
   l'ordre, quel que soit l'ordre du téléchargement.
Relancer sur un dossier déjà rangé redate les slides sans rien déplacer. Affiche le résultat au format JSON.
"""
import argparse
import datetime
import json
import os
import re
from pathlib import Path

from PIL import Image

MOTIF = re.compile(r"^(?P<base>.+?)-(?P<variante>\d\d)-slide-(?P<slide>\d\d)\.(jpe?g)$", re.I)
CODES = {"txt": "texte", "txti": "texte-image", "tweet": "tweet", "punch": "punchline", "infographie": "infographie"}


def exif_date(date):
    exif = Image.Exif()
    texte = date.strftime("%Y:%m:%d %H:%M:%S")
    exif[0x0132] = texte                      # DateTime
    ifd = exif.get_ifd(0x8769)
    ifd[0x9003] = texte                       # DateTimeOriginal
    ifd[0x9004] = texte                       # DateTimeDigitized
    decalage = date.astimezone().strftime("%z")
    decalage = decalage[:3] + ":" + decalage[3:]
    ifd[0x9011] = decalage                    # OffsetTimeOriginal
    return exif.tobytes()                     # commence par b"Exif\0\0"


def dater(chemin, date):
    """Remplace le bloc EXIF du JPEG, sans recompresser l'image."""
    data = chemin.read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"pas un JPEG : {chemin.name}")
    i, garde = 2, []
    while i + 4 <= len(data) and data[i] == 0xFF and data[i + 1] not in (0xDA, 0xD9):
        n = int.from_bytes(data[i + 2:i + 4], "big")
        segment = data[i:i + 2 + n]
        if not (data[i + 1] == 0xE1 and segment[4:10] == b"Exif\x00\x00"):
            garde.append(segment)
        i += 2 + n
    corps = exif_date(date)
    app1 = b"\xff\xe1" + (len(corps) + 2).to_bytes(2, "big") + corps
    # APP0 (JFIF) d'abord s'il existe, puis l'EXIF, puis le reste
    app0 = [s for s in garde if s[1] == 0xE0]
    autres = [s for s in garde if s[1] != 0xE0]
    chemin.write_bytes(b"\xff\xd8" + b"".join(app0) + app1 + b"".join(autres) + data[i:])
    t = date.timestamp()
    os.utime(chemin, (t, t))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dossier", required=True)
    p.add_argument("--noms", nargs="*", default=[])
    a = p.parse_args()
    final = Path(a.dossier)
    noms = dict(n.split("=", 1) for n in a.noms)
    slides = [f for f in final.rglob("*") if f.is_file() and MOTIF.match(f.name)]
    variantes = sorted({MOTIF.match(f.name)["variante"] for f in slides})
    deplaces = []
    if len(variantes) > 1:
        for f in slides:
            m = MOTIF.match(f.name)
            nom = noms.get(m["variante"])
            if not nom:
                code = m["base"].split("-carrousel-")[-1].split("-")[0]
                nom = f"{m['variante']} - {CODES.get(code, code)}"
            cible = final / nom / f.name
            if f != cible:
                cible.parent.mkdir(exist_ok=True)
                f.rename(cible)
                deplaces.append(str(cible.relative_to(final)))
        slides = [f for f in final.rglob("*") if f.is_file() and MOTIF.match(f.name)]
        for vide in sorted((d for d in final.rglob("*") if d.is_dir()), reverse=True):
            if not any(vide.iterdir()):
                vide.rmdir()
    depart = datetime.datetime.now().replace(second=0, microsecond=0)
    for f in sorted(slides, key=lambda f: f.name):
        n = int(MOTIF.match(f.name)["slide"])
        dater(f, depart + datetime.timedelta(seconds=n - 1))
    dossiers = sorted({str(f.parent.relative_to(final)) for f in slides})
    print(json.dumps({"ok": True, "variantes": len(variantes), "dossiers": dossiers, "slides": len(slides),
                      "deplaces": len(deplaces), "debut": depart.strftime("%d/%m/%Y %H:%M:%S")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

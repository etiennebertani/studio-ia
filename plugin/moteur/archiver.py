"""Ajoute ou met à jour un contenu validé dans l'archive de la personne.

    python3 archiver.py --dossier <dossier du contenu> --format carrousel --sujet "..." \
        [--style "..."] [--structure "..."] [--notion <lien>] [--date AAAA-MM-JJ]

Une ligne par contenu dans l'archive de la personne (voir commun.ARCHIVE).
Lit final/texte.txt et final/legendes.txt. Relancer sur le même dossier met la ligne à jour.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import commun

ARCHIVE = commun.ARCHIVE


def lire_texte(chemin):
    return chemin.read_text(encoding="utf-8").strip() if chemin.is_file() else ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dossier", required=True)
    parser.add_argument("--format", required=True)
    parser.add_argument("--sujet", required=True)
    parser.add_argument("--style", default="")
    parser.add_argument("--structure", default="")
    parser.add_argument("--notion", default="")
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    args = parser.parse_args()

    dossier = Path(args.dossier).expanduser().resolve()
    if not dossier.is_dir():
        sys.exit("Dossier introuvable : {}".format(dossier))
    ligne = {
        "date": args.date, "format": args.format, "sujet": args.sujet, "style": args.style,
        "structure": args.structure, "dossier": str(dossier), "notion": args.notion,
        "texte": lire_texte(dossier / "final" / "texte.txt"),
        "legendes": lire_texte(dossier / "final" / "legendes.txt"),
    }
    if not ligne["texte"]:
        sys.exit("Pas de texte à archiver dans final/texte.txt.")

    lignes = []
    if ARCHIVE.is_file():
        lignes = [json.loads(l) for l in ARCHIVE.read_text(encoding="utf-8").splitlines() if l.strip()]
    anciennes = [l for l in lignes if l.get("dossier") == ligne["dossier"]]
    if anciennes:
        ligne["statistiques"] = anciennes[0].get("statistiques", {})
    else:
        ligne["statistiques"] = {}
    lignes = [l for l in lignes if l.get("dossier") != ligne["dossier"]] + [ligne]
    temporaire = ARCHIVE.with_suffix(".tmp")
    temporaire.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lignes), encoding="utf-8")
    temporaire.replace(ARCHIVE)
    print("Archive à jour : {} contenu(s).".format(len(lignes)))


if __name__ == "__main__":
    main()

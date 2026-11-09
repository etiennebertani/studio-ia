"""Vérifie que chaque texte d'un carrousel se trouve mot pour mot dans le texte d'origine.

    python3 verifier_texte.py <slides.json> <source.txt>

Sort avec une erreur et liste les passages qui ne correspondent pas.
"""
import json
import re
import sys
from pathlib import Path


def normaliser(texte):
    return re.sub(r"\s+", " ", texte.replace(" ", " ").replace(" ", " ")).strip()


def textes(slide):
    for cle in ("titre", "sous_titre"):
        if slide.get(cle):
            yield slide[cle]
    for paragraphe in slide.get("paragraphes", []):
        yield paragraphe


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    donnees = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    source = normaliser(Path(sys.argv[2]).read_text(encoding="utf-8"))
    ecarts = []
    for numero, slide in enumerate(donnees["slides"], 1):
        for morceau in textes(slide):
            if normaliser(morceau) not in source:
                ecarts.append("Slide {} : {}".format(numero, morceau))
    if ecarts:
        print("Ces textes ne sont pas identiques à l'original :")
        print("\n".join(ecarts))
        sys.exit(1)
    print("Texte identique à l'original.")


if __name__ == "__main__":
    main()

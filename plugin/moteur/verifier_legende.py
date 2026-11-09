"""Vérifie qu'une légende respecte les limites d'Instagram.

    python3 verifier_legende.py <fichier texte>

Limites : 2 200 caractères, 30 hashtags, 20 mentions.
"""
import re
import sys
from pathlib import Path

MAX_CARACTERES, MAX_HASHTAGS, MAX_MENTIONS = 2200, 30, 20


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    texte = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    caracteres, hashtags = len(texte), len(re.findall(r"(?<!\w)#\w+", texte))
    mentions = len(re.findall(r"(?<!\w)@[\w.]+", texte))
    print("{} caractères, {} hashtags, {} mentions".format(caracteres, hashtags, mentions))
    erreurs = []
    if not texte:
        erreurs.append("La légende est vide.")
    if caracteres > MAX_CARACTERES:
        erreurs.append("Trop long de {} caractères.".format(caracteres - MAX_CARACTERES))
    if hashtags > MAX_HASHTAGS:
        erreurs.append("Trop de hashtags.")
    if mentions > MAX_MENTIONS:
        erreurs.append("Trop de mentions.")
    if erreurs:
        sys.exit("\n".join(erreurs))
    print("Légende conforme.")


if __name__ == "__main__":
    main()

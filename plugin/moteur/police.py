"""Installe une police libre de Google Fonts dans le dossier d'une marque.

    <python du moteur> police.py "Nom de la police" <dossier de la marque>

Écrit les fichiers dans <dossier de la marque>/polices/ et affiche, au format JSON,
le nom de la police et la liste à recopier dans "polices" de marque.json.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/google/fonts/contents/{}/{}"
BRUT = "https://raw.githubusercontent.com/google/fonts/main/{}/{}/{}"
LICENCES = ("ofl", "apache", "ufl")
GRAISSES = {"Thin": 100, "ExtraLight": 200, "Light": 300, "Regular": 400, "Medium": 500,
            "SemiBold": 600, "Bold": 700, "ExtraBold": 800, "Black": 900}
GARDEES = (400, 500, 600, 700)
FICHIERS_LICENCE = ("OFL.txt", "LICENSE.txt", "UFL.txt")


def lire(url):
    requete = urllib.request.Request(url, headers={"User-Agent": "studio-ia"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        return reponse.read()


def trouver(nom):
    slug = re.sub(r"[^a-z0-9]", "", nom.lower())
    for licence in LICENCES:
        try:
            return licence, slug, [f["name"] for f in json.loads(lire(API.format(licence, slug)))]
        except urllib.error.HTTPError as erreur:
            if erreur.code == 403:
                sys.exit("Service de polices momentanément indisponible, réessaie dans une heure.")
            if erreur.code != 404:
                raise
    sys.exit("Police introuvable dans Google Fonts : {}".format(nom))


def choisir(fichiers):
    """Renvoie [(fichier, graisse, style)] : polices statiques si possible, sinon variables."""
    statiques = []
    for fichier in fichiers:
        m = re.fullmatch(r".+-([A-Za-z]+?)(Italic)?\.ttf", fichier)
        if m is None and fichier.endswith("-Italic.ttf"):
            statiques.append((fichier, 400, "italic"))
        elif m and (m.group(1) in GRAISSES) and GRAISSES[m.group(1)] in GARDEES:
            statiques.append((fichier, GRAISSES[m.group(1)], "italic" if m.group(2) else "normal"))
    if statiques:
        return statiques
    variables = [f for f in fichiers if f.endswith(".ttf") and "[" in f]
    if not variables:
        sys.exit("Aucun fichier de police exploitable.")
    return [(f, "100 900", "italic" if "Italic" in f else "normal") for f in variables]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    nom, dossier = sys.argv[1], Path(sys.argv[2]).expanduser().resolve()
    cible = dossier / "polices"
    cible.mkdir(parents=True, exist_ok=True)
    licence, slug, fichiers = trouver(nom)
    polices = []
    for fichier, graisse, style in choisir(fichiers):
        adresse = BRUT.format(licence, slug, urllib.request.quote(fichier))
        propre = fichier.replace("[", "-").replace("]", "").replace(",", "-")
        (cible / propre).write_bytes(lire(adresse))
        polices.append({"fichier": "polices/{}".format(propre), "graisse": str(graisse), "style": style})
    for fichier in fichiers:
        if fichier in FICHIERS_LICENCE:
            (cible / "{}-{}".format(slug, fichier)).write_bytes(lire(BRUT.format(licence, slug, fichier)))
    print(json.dumps({"police": nom, "polices": polices}, ensure_ascii=False))


if __name__ == "__main__":
    main()

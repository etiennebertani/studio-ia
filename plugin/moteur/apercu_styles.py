"""Fabrique la planche d'aperçu des styles d'une marque.

    <python du moteur> apercu_styles.py <marque.json> <dossier de sortie> [--texte "Phrase de la personne"]

La planche montre uniquement les catégories présentes dans "categories" de la marque.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

TITRE = "Ton titre de carrousel ici"
TEXTE = "Voici à quoi ressemble ton texte dans ce style. Une idée claire, facile à lire sur un téléphone."


def slides_pour(categorie, titre, texte, image):
    if categorie == "texte-image":
        illustree = {"image": image} if image else {}
        return [
            dict(illustree, style="texte-image-couverture", titre=titre, sous_titre=texte, fleche="swipe"),
            dict(illustree, style="texte-image", paragraphes=[texte], fleche="par ici"),
            dict(illustree, style="texte-image-couverture", titre=titre, theme="sombre", image_position="haut", fleche="swipe"),
        ]
    if categorie == "texte":
        return [{"style": "texte", "titre": titre, "paragraphes": [texte]},
                {"style": "texte", "titre": titre, "paragraphes": [texte], "theme": "sombre"}]
    if categorie == "punchline":
        return [{"style": "punchline", "theme": "blanc", "paragraphes": [texte]},
                {"style": "punchline", "theme": "noir", "paragraphes": [texte]}]
    if categorie == "tweet":
        return [{"style": "tweet", "theme": "noir", "paragraphes": [texte]},
                {"style": "tweet", "theme": "blanc", "paragraphes": [texte]}]
    sys.exit("Catégorie inconnue : {}".format(categorie))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("marque")
    parser.add_argument("sortie")
    parser.add_argument("--titre", default=TITRE)
    parser.add_argument("--texte", default=TEXTE)
    parser.add_argument("--image")
    args = parser.parse_args()

    marque = Path(args.marque).expanduser().resolve()
    sortie = Path(args.sortie).expanduser().resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    donnees = json.loads(marque.read_text(encoding="utf-8"))
    slides = []
    for categorie in donnees.get("categories", {}):
        slides += slides_pour(categorie, args.titre, args.texte, args.image)
    if not slides:
        sys.exit("Aucune catégorie dans cette marque.")
    fichier = sortie / "slides.json"
    fichier.write_text(json.dumps({"marque_fichier": str(marque), "slides": slides}, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    moteur = Path(__file__).resolve().parent / "rendre_carrousel.py"
    sys.exit(subprocess.run([sys.executable, str(moteur), str(fichier), str(sortie / "rendu")]).returncode)


if __name__ == "__main__":
    main()

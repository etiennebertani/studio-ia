"""Contrôle de fin : vérifie qu'un contenu ou un style est vraiment terminé, partout.

    python3 controle_fin.py contenu --dossier <dossier du contenu>
    python3 controle_fin.py style --nom "<nom du style>" --type carrousel|reel

Affiche {"ok": bool, "manquants": [...], "a_confirmer": [...]}. Code de sortie 1 s'il manque quelque chose.
"manquants" se vérifie ici. "a_confirmer" demande de lire Notion ou une autre ressource : le Studio doit le faire lui-même.
"""
import argparse
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

import commun
import nommage

DOSSIER_EXEMPLES = {"carrousel": "Exemples de carrousel", "reel": "Exemples de montage"}
ALIAS = {"texte-image": "texte + image", "texte": "texte", "infographie": "infographie minimale", "yap-plus": "yap+"}


def norm(texte):
    return "".join(c for c in unicodedata.normalize("NFD", str(texte).lower()) if unicodedata.category(c) != "Mn").strip()


def lire_json(chemin):
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def config():
    return lire_json(commun.CONFIG)


def marque():
    for fichier in sorted((commun.ESPACE / commun.NOMS["branding"]).glob("*/marque.json")):
        return lire_json(fichier), fichier.parent
    return {}, None


def ligne_archive(dossier):
    cible = norm(Path(dossier).resolve())
    if commun.ARCHIVE.is_file():
        for ligne in commun.ARCHIVE.read_text(encoding="utf-8").splitlines():
            if ligne.strip():
                infos = json.loads(ligne)
                if norm(Path(infos.get("dossier", "")).resolve()) == cible:
                    return infos
    return None


def type_format(valeur):
    return "reel" if norm(valeur).startswith("reel") else "carrousel"


def a_un_exemple(style, type_):
    dossier = commun.ESPACE / commun.NOMS["references"] / DOSSIER_EXEMPLES[type_]
    registre = lire_json(dossier / "exemples.json")
    cherche = norm(style)
    cherche = norm(ALIAS.get(cherche, cherche))
    mot = cherche.split(" ")[0] if cherche else ""
    return any(mot and norm(cle).split(" ")[0] == mot for cle in registre)


def controle_contenu(dossier):
    dossier = Path(dossier)
    manquants, a_confirmer = [], []
    final = dossier / "final"
    medias = [f for f in final.rglob("*") if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".mp4", ".mov")] if final.is_dir() else []
    if not medias:
        manquants.append("aucun fichier final")
    for fichier in medias:
        infos = nommage.analyser(unicodedata.normalize("NFC", fichier.name))
        if not infos["ok"]:
            manquants.append(f"nom non conforme : {fichier.name}")
    if not (final / "legendes.txt").is_file():
        manquants.append("légendes absentes")
    infos = ligne_archive(dossier)
    if infos is None:
        manquants.append("contenu absent de l'archive")
    else:
        if infos.get("style"):
            type_ = type_format(infos.get("format", "carrousel"))
            if not a_un_exemple(infos["style"], type_):
                manquants.append(f"aucun exemple rangé pour le style : {infos['style']}")
        if config().get("banque_notion"):
            if infos.get("notion"):
                a_confirmer.append(f"lire la fiche Notion {infos['notion']} : statut, lien Drive, légende")
            else:
                manquants.append("lien de la fiche Notion absent de l'archive")
    if config().get("drive_contenu"):
        sortie = subprocess.run([sys.executable, str(Path(__file__).parent / "drive.py"), "etat", "--contenu", str(dossier)],
                                capture_output=True, text=True)
        try:
            etat = json.loads(sortie.stdout)
            if not etat.get("arrive"):
                manquants.append("fichiers pas encore arrivés sur Drive")
            if etat.get("lien"):
                a_confirmer.append(f"la fiche Notion doit avoir ce Lien Drive : {etat['lien']}")
            if etat.get("a_verifier"):
                a_confirmer.append(f"vérifier sur Drive {len(etat['a_verifier'])} fichier(s) sans identifiant local")
        except json.JSONDecodeError:
            manquants.append("état de Drive illisible")
    return manquants, a_confirmer


def controle_style(nom, type_):
    manquants, a_confirmer = [], []
    if not a_un_exemple(nom, type_):
        manquants.append(f"aucun exemple rangé pour le style : {nom}")
    donnees, branding = marque()
    if branding is not None:
        formats = branding / "direction-artistique" / "formats.md"
        if not formats.is_file():
            manquants.append("direction artistique par format absente")
        elif norm(nom) not in norm(formats.read_text(encoding="utf-8")):
            manquants.append(f"style absent de la direction artistique : {nom}")
    for cle, libelle in (("ressource_branding", "document de marque"), ("ressource_guides", "guide général")):
        if donnees.get(cle):
            a_confirmer.append(f"relire le {libelle} ({donnees[cle]}) : le style {nom} y est à jour")
    a_confirmer.append("règles de base et personnalisation séparées dans le plugin, cahier des charges à jour")
    a_confirmer.append("nettoyage : liste des fichiers de travail devenus inutiles proposée à la personne")
    return manquants, a_confirmer


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("contenu").add_argument("--dossier", required=True)
    p = actions.add_parser("style")
    p.add_argument("--nom", required=True)
    p.add_argument("--type", required=True, choices=sorted(DOSSIER_EXEMPLES))
    args = parser.parse_args()
    manquants, a_confirmer = controle_contenu(args.dossier) if args.action == "contenu" else controle_style(args.nom, args.type)
    print(json.dumps({"ok": not manquants, "manquants": manquants, "a_confirmer": a_confirmer}, ensure_ascii=False, indent=1))
    sys.exit(1 if manquants else 0)


if __name__ == "__main__":
    main()

"""Relie l'espace local à un dossier Google Drive présent sur l'ordinateur.

    python3 drive.py configurer --dossier <dossier Drive>   crée les dossiers manquants et mémorise l'emplacement
    python3 drive.py envoyer --contenu <dossier du contenu>  copie un contenu validé vers Drive
    python3 drive.py etat --contenu <dossier du contenu>     dit si tout est arrivé et donne le lien du dossier
    python3 drive.py sauvegarder                             copie Branding, Références et B-roll vers Drive

La copie va toujours de l'ordinateur vers Drive et ne supprime jamais rien sur Drive.
Chaque commande affiche un résultat au format JSON.
"""
import argparse
import hashlib
import json
import re
import shutil
import time
import subprocess
import sys
from pathlib import Path

import commun

A_ENVOYER = ("final", "images", "b-roll", "musique")
RECETTE = Path("travail") / "slides.json"
ATTRIBUT_ID = "com.google.drivefs.item-id#S"
ID_VALIDE = re.compile(r"^[A-Za-z0-9_-]{20,}$")
IGNORES = {".DS_Store"}
EXTENSIONS_VISUELS = {".jpg", ".jpeg", ".png", ".mp4", ".mov"}


def repondre(**valeurs):
    print(json.dumps(valeurs, ensure_ascii=False, indent=2))


def racine_drive():
    chemin = commun.lire_config().get("drive_contenu")
    if not chemin:
        repondre(ok=False, raison="drive_non_configure")
        sys.exit(1)
    racine = Path(chemin)
    if not racine.is_dir():
        repondre(ok=False, raison="dossier_drive_introuvable", dossier=chemin)
        sys.exit(1)
    return racine


def empreinte(chemin):
    calcul = hashlib.sha256()
    with chemin.open("rb") as fichier:
        for bloc in iter(lambda: fichier.read(1048576), b""):
            calcul.update(bloc)
    return calcul.hexdigest()


def identifiant(chemin):
    resultat = subprocess.run(["xattr", "-p", ATTRIBUT_ID, str(chemin)], capture_output=True, text=True)
    valeur = resultat.stdout.strip() if resultat.returncode == 0 else ""
    return valeur if ID_VALIDE.match(valeur) else ""


def fichiers_de(dossier):
    return [f for f in sorted(dossier.rglob("*")) if f.is_file() and f.name not in IGNORES]


def liste_a_envoyer(contenu):
    fichiers = []
    for nom in A_ENVOYER:
        if (contenu / nom).is_dir():
            fichiers += fichiers_de(contenu / nom)
    if (contenu / RECETTE).is_file():
        fichiers.append(contenu / RECETTE)
    return fichiers


def controle(contenu):
    """Renvoie les raisons qui empêchent de considérer le contenu comme fini."""
    final = contenu / "final"
    raisons = []
    if not final.is_dir() or not any(f.suffix.lower() in EXTENSIONS_VISUELS for f in final.rglob("*")):
        raisons.append("design_absent")
    legendes = final / "legendes.txt"
    if not legendes.is_file() or not legendes.read_text(encoding="utf-8").strip():
        raisons.append("legende_absente")
    return raisons


def destination(contenu, racine):
    try:
        return racine / contenu.relative_to(commun.ESPACE)
    except ValueError:
        repondre(ok=False, raison="contenu_hors_de_mon_espace", dossier=str(contenu))
        sys.exit(1)


def identique(source, cible):
    return cible.is_file() and source.stat().st_size == cible.stat().st_size and empreinte(source) == empreinte(cible)


def copier(source, cible):
    if identique(source, cible):
        return False
    cible.parent.mkdir(parents=True, exist_ok=True)
    if cible.exists():
        # Écrire dans le fichier existant : Google Drive garde son identifiant.
        shutil.copyfile(source, cible)
        return True
    temporaire = cible.with_name(cible.name + ".envoi")
    shutil.copyfile(source, temporaire)
    temporaire.replace(cible)
    return True


def cmd_configurer(args):
    racine = Path(args.dossier).expanduser().resolve()
    if not racine.is_dir():
        repondre(ok=False, raison="dossier_introuvable", dossier=str(racine))
        sys.exit(1)
    if "CloudStorage/GoogleDrive-" not in str(racine):
        repondre(ok=False, raison="pas_un_dossier_google_drive", dossier=str(racine))
        sys.exit(1)
    crees = []
    for nom in commun.NOMS.values():
        if not (racine / nom).exists():
            (racine / nom).mkdir()
            crees.append(nom)
    commun.ecrire_config({"drive_contenu": str(racine)})
    repondre(ok=True, dossier=str(racine), crees=crees)


def cmd_envoyer(args):
    contenu = Path(args.contenu).expanduser().resolve()
    raisons = controle(contenu)
    if raisons:
        repondre(ok=False, raisons=raisons)
        sys.exit(1)
    racine = racine_drive()
    cible = destination(contenu, racine)
    copies = 0
    for fichier in liste_a_envoyer(contenu):
        copies += copier(fichier, cible / fichier.relative_to(contenu))
    repondre(ok=True, copies=copies, destination=str(cible))


def cmd_etat(args):
    contenu = Path(args.contenu).expanduser().resolve()
    racine = racine_drive()
    cible = destination(contenu, racine)
    fichiers = liste_a_envoyer(contenu)
    manquants = [str(f.relative_to(contenu)) for f in fichiers
                 if not identique(f, cible / f.relative_to(contenu))]
    sans_id, a_verifier = [], []
    if not manquants:
        limite = time.time() - 3600
        for f in fichiers:
            copie = cible / f.relative_to(contenu)
            if not identifiant(copie):
                (a_verifier if copie.stat().st_mtime < limite else sans_id).append(str(f.relative_to(contenu)))
    id_dossier = identifiant(cible) if cible.is_dir() else ""
    arrive = bool(fichiers) and not manquants and not sans_id and bool(id_dossier)
    repondre(arrive=arrive, fichiers=len(fichiers), manquants=manquants, en_attente=sans_id, a_verifier=a_verifier,
             lien="https://drive.google.com/drive/folders/" + id_dossier if arrive else "")
    sys.exit(0 if arrive else 2)


def cmd_sauvegarder(args):
    racine = racine_drive()
    copies = 0
    for cle in ("branding", "references", "b_roll"):
        source = commun.ESPACE / commun.NOMS[cle]
        if source.is_dir():
            for fichier in fichiers_de(source):
                copies += copier(fichier, racine / commun.NOMS[cle] / fichier.relative_to(source))
    repondre(ok=True, copies=copies)


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("configurer").add_argument("--dossier", required=True)
    actions.add_parser("envoyer").add_argument("--contenu", required=True)
    actions.add_parser("etat").add_argument("--contenu", required=True)
    actions.add_parser("sauvegarder")
    args = parser.parse_args()
    {"configurer": cmd_configurer, "envoyer": cmd_envoyer, "etat": cmd_etat, "sauvegarder": cmd_sauvegarder}[args.action](args)


if __name__ == "__main__":
    main()

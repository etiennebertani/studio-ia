"""La convention de nommage du Studio. C'est le seul endroit où elle est écrite.

    python3 nommage.py verifier <nom> [<nom>...] [--restaurant]
    python3 nommage.py sujet "<texte>"
    python3 nommage.py clients <nom> [<nom>...]
    python3 nommage.py carrousel --dossier <final> --client <client> --style <style> --sujet "<sujet>" [--periode aa-mm] [--numero 2]

Format : aa-mm-client-type-sujet-numéro.ext. Un carrousel ajoute -slide-nn à la fin.
Bibliothèque standard uniquement.
"""
import argparse
import datetime
import json
import re
import unicodedata
from pathlib import Path

TYPES = ("post", "story", "reel-nocc", "reel-cc", "video-nocc", "video-cc", "broll", "visuel", "carrousel")
CODES_CARROUSEL = {"tweet": "tweet", "texte": "txt", "texte-image": "txti", "punchline": "punchline", "infographie": "infographie"}
CATEGORIES_RESTAURANT = ("1-cuisine", "2-boissons", "3-salle", "4-dehors")
MOTS_SUJET_MAX = 6


def sans_accents(texte):
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def sujet(texte, mots_max=MOTS_SUJET_MAX):
    """Transforme un texte en sujet valide : minuscules, tirets, accents conservés."""
    propre = unicodedata.normalize("NFC", texte.lower())
    propre = re.sub(r"[^\w]+", "-", propre.replace("_", "-"), flags=re.UNICODE).strip("-")
    return "-".join(propre.split("-")[:mots_max])


def periode(date=None):
    return (date or datetime.date.today()).strftime("%y-%m")


def nom_fichier(mois, client, type_, sujet_, numero, extension, slide=None):
    if type_ not in TYPES:
        raise ValueError(f"Type hors de la liste fermée : {type_}")
    base = f"{mois}-{client}-{type_}-{sujet_}-{numero:02d}"
    if slide is not None:
        base += f"-slide-{slide:02d}"
    return unicodedata.normalize("NFC", base + extension.lower())


def analyser(nom, restaurant=False):
    """Découpe un nom selon la forme de chaque champ. Renvoie {"ok": bool, "erreurs": [...], champs...}."""
    erreurs = []
    chemin = Path(nom)
    base, extension = chemin.stem, chemin.suffix
    if not extension:
        erreurs.append("pas d'extension")
    if base != base.lower():
        erreurs.append("majuscules")
    if " " in base:
        erreurs.append("espace")
    if "_" in base:
        erreurs.append("underscore")
    if "." in base:
        erreurs.append("point dans le nom")
    if re.search(r"[^\w-]", base):
        erreurs.append("caractère spécial")
    resultat = {"nom": nom, "ok": False, "erreurs": erreurs}
    reste, slide = base, None
    trouve = re.search(r"-slide-(\d\d)$", reste)
    if trouve:
        slide, reste = int(trouve.group(1)), reste[:trouve.start()]
    segments = reste.split("-")
    if len(segments) < 5 or not re.fullmatch(r"\d\d", segments[0]) or not re.fullmatch(r"\d\d", segments[1]):
        erreurs.append("aa-mm manquant")
        return resultat
    if not re.fullmatch(r"\d\d", segments[-1]):
        erreurs.append("numéro à 2 chiffres manquant")
        return resultat
    milieu = "-".join(segments[2:-1])
    type_ = None
    for candidat in sorted(TYPES, key=len, reverse=True):
        place = re.search(rf"(?:^|-){re.escape(candidat)}-", milieu + "-")
        if place:
            type_ = candidat
            debut, fin = place.start(), place.end()
            client = milieu[:debut]
            sujet_ = milieu[fin:] if fin <= len(milieu) else ""
            break
    if type_ is None:
        erreurs.append("type absent de la liste fermée")
        return resultat
    if not client:
        erreurs.append("client manquant")
    if not sujet_:
        erreurs.append("sujet manquant")
    if type_ == "carrousel" and slide is None and extension.lower() in (".jpg", ".jpeg", ".png"):
        erreurs.append("slide-nn manquant")
    if restaurant and type_ == "broll" and not any(sujet_ == c or sujet_.startswith(c + "-") for c in CATEGORIES_RESTAURANT):
        erreurs.append("catégorie de b-roll manquante")
    resultat.update(ok=not erreurs, mois=f"{segments[0]}-{segments[1]}", client=client, type=type_, sujet=sujet_,
                    numero=int(segments[-1]), slide=slide)
    return resultat


def doublons_clients(clients):
    """Les noms différents qui désignent le même client, en ignorant accents et majuscules."""
    groupes = {}
    for client in clients:
        groupes.setdefault(sans_accents(client), set()).add(client)
    return [sorted(g) for g in groupes.values() if len(g) > 1]


def prochain_numero(dossier, prefixes):
    """Le numéro suivant parmi les fichiers commençant par l'un de ces préfixes (aa-mm-client-type-sujet)."""
    plus_haut = 0
    if Path(dossier).is_dir():
        for fichier in Path(dossier).iterdir():
            infos = analyser(unicodedata.normalize("NFC", fichier.name))
            if infos["ok"] and any(unicodedata.normalize("NFC", fichier.name).startswith(p + "-") for p in prefixes):
                plus_haut = max(plus_haut, infos["numero"])
    return plus_haut + 1


def nommer_carrousel(dossier, client, sujet_, mois, numero=None):
    """Renomme les slide-NN d'un dossier selon la convention. Ne touche à rien si un nom existe déjà."""
    dossier = Path(dossier)
    slides = sorted(f for f in dossier.iterdir() if re.fullmatch(r"slide-\d\d", f.stem))
    if not slides:
        return []
    prefixe = f"{mois}-{client}-carrousel-{sujet_}"
    numero = numero or prochain_numero(dossier, [prefixe])
    paires = [(f, dossier / nom_fichier(mois, client, "carrousel", sujet_, numero, f.suffix, int(f.stem[-2:]))) for f in slides]
    if any(cible.exists() for _, cible in paires):
        raise SystemExit("Un fichier porte déjà ce nom. Rien n'a été renommé.")
    for source, cible in paires:
        source.rename(cible)
    return [cible.name for _, cible in paires]


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    p = actions.add_parser("verifier")
    p.add_argument("noms", nargs="+")
    p.add_argument("--restaurant", action="store_true")
    actions.add_parser("sujet").add_argument("texte")
    actions.add_parser("clients").add_argument("noms", nargs="+")
    p = actions.add_parser("carrousel")
    p.add_argument("--dossier", required=True)
    p.add_argument("--client", required=True)
    p.add_argument("--style", required=True, choices=sorted(CODES_CARROUSEL))
    p.add_argument("--sujet", required=True)
    p.add_argument("--periode", default=periode())
    p.add_argument("--numero", type=int)
    args = parser.parse_args()
    if args.action == "verifier":
        sortie = [analyser(n, args.restaurant) for n in args.noms]
    elif args.action == "sujet":
        sortie = sujet(args.texte)
    elif args.action == "clients":
        sortie = doublons_clients(args.noms)
    else:
        sortie = nommer_carrousel(args.dossier, args.client, f"{CODES_CARROUSEL[args.style]}-{sujet(args.sujet)}", args.periode, args.numero)
    print(json.dumps(sortie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

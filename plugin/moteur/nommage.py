"""La convention de nommage, partagée par tous les skills (Studio, Secrétaire, assistant Drive).

Source : ~/Socle. Ce fichier est recopié dans chaque skill par `socle.py diffuser` : ne le modifie
jamais dans un skill, modifie-le dans le Socle.

Il lit deux couches :
  1. ../ressources/convention.json : la convention générique (la forme des noms, les types) ;
  2. l'espace de la personne (ses noms courts, ses règles), qui passe avant. Cherché dans cet ordre :
     --espace <dossier ou fichier>, la variable SOCLE_ESPACE, puis ~/Socle/espaces/<nom>/espace.json.
     Sans espace, seule la convention générique s'applique.

    python3 nommage.py verifier <nom> [<nom>...] [--restaurant] [--espace <espace>]
    python3 nommage.py dossier <nom> [<nom>...]
    python3 nommage.py sujet "<texte>"
    python3 nommage.py clients <nom> [<nom>...]
    python3 nommage.py piece --tiers <nom court> --type facture --date 2026-11-03 --reference "INV-EU-1094" --ext pdf [--dossier <destination>] [--espace <espace>]
    python3 nommage.py carrousel --dossier <final> --client <client> --style <style> --sujet "<sujet>" [--periode aa-mm] [--numero 2] [--version 2]
    python3 nommage.py version

Bibliothèque standard uniquement.
"""
import argparse
import datetime
import json
import os
import re
import unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent
CONVENTION = json.loads((ICI.parent / "ressources" / "convention.json").read_text(encoding="utf-8"))
VERSION = CONVENTION["version"]
TYPES_INFOS = CONVENTION["types"]
TYPES = tuple(TYPES_INFOS)
CODES_CARROUSEL = {"tweet": "tweet", "texte": "txt", "texte-image": "txti", "punchline": "punchline", "infographie": "infographie"}
CATEGORIES_RESTAURANT = tuple(CONVENTION["categories_broll_restaurant"])
FORMATS_CARTE = tuple(CONVENTION["formats_carte"])
MOTS_SUJET_MAX = 6


# ---------- espace ----------

def charger_espace(espace=None):
    """L'espace de la personne, ou None. `espace` : nom (par exemple « mon-entreprise »), dossier ou fichier espace.json."""
    espace = espace or os.environ.get("SOCLE_ESPACE")
    if not espace:
        return None
    chemin = Path(espace).expanduser()
    for autre in (Path.home() / "Socle" / "espaces" / espace, ICI.parent / "ressources" / "espaces" / espace):
        if not chemin.exists():
            chemin = autre
    if chemin.is_dir():
        chemin = chemin / "espace.json"
    if not chemin.exists():
        raise SystemExit(f"Espace introuvable : {espace}")
    donnees = json.loads(chemin.read_text(encoding="utf-8"))
    compatible = str(donnees.get("compatible", ""))
    if compatible.split(".")[0] != VERSION.split(".")[0]:
        raise SystemExit(f"L'espace {donnees.get('espace')} a été écrit pour la convention {compatible}, "
                         f"la convention est en {VERSION} : à revoir avant de renommer quoi que ce soit.")
    for type_, infos in donnees.get("types_en_plus", {}).items():
        TYPES_INFOS.setdefault(type_, infos)
    return donnees


def noms_actes(espace):
    if not espace:
        return None
    return {**espace.get("clients", {}), **espace.get("fournisseurs", {})}


# ---------- écriture ----------

def sans_accents(texte):
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def sujet(texte, mots_max=MOTS_SUJET_MAX):
    """Transforme un texte en sujet valide : minuscules, tirets, accents conservés."""
    propre = unicodedata.normalize("NFC", texte.lower())
    propre = re.sub(r"[^\w]+", "-", propre.replace("_", "-"), flags=re.UNICODE).strip("-")
    return "-".join(propre.split("-")[:mots_max])


def reference(texte):
    """Une référence de pièce (numéro de facture) : minuscules, tirets, sans limite de mots."""
    return sujet(texte, mots_max=50)


def periode(date=None):
    return (date or datetime.date.today()).strftime("%y-%m")


def versionne(type_):
    return bool(TYPES_INFOS.get(type_, {}).get("versionne"))


def nom_fichier(mois, client, type_, sujet_, numero, extension, slide=None, version=None):
    """Le nom complet. Pour un réel, le numéro (rang du réel dans le mois) vient juste après cc / nocc.
    Un type versionné finit par -vN (v1 = la principale), avant -slide-nn pour un carrousel."""
    if type_ not in TYPES_INFOS:
        raise ValueError(f"Type hors de la liste fermée : {type_}")
    if TYPES_INFOS[type_]["ordre"] == "reel":
        base = f"{mois}-{client}-{type_}-{numero:02d}-{sujet_}"
    else:
        base = f"{mois}-{client}-{type_}-{sujet_}-{numero:02d}"
    if versionne(type_):
        base += f"-v{version or 1}"
    elif version is not None:
        raise ValueError(f"Un {type_} n'a pas de version")
    if slide is not None:
        base += f"-slide-{slide:02d}"
    if not extension.startswith("."):
        extension = "." + extension
    return unicodedata.normalize("NFC", base + extension.lower())


# ---------- lecture ----------

def _trouver_type(milieu):
    """Le type qui apparaît le plus tôt ; à égalité, le plus long (reel-cc avant reel, carrousel avant carte)."""
    meilleur = None
    for candidat in TYPES_INFOS:
        place = re.search(rf"(?:^|-){re.escape(candidat)}(?:-|$)", milieu)
        if place:
            debut = place.start() + (1 if milieu[place.start()] == "-" else 0)
            cle = (debut, -len(candidat))
            if meilleur is None or cle < meilleur[0]:
                meilleur = (cle, candidat, debut)
    return (meilleur[1], meilleur[2]) if meilleur else (None, None)


def analyser(nom, restaurant=False, espace=None):
    """Découpe un nom selon la forme de chaque champ. Renvoie {"ok": bool, "erreurs": [...], champs...}."""
    erreurs = []
    nom = unicodedata.normalize("NFC", nom)
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
    if "," in base:
        erreurs.append("virgule")
    if "." in base:
        erreurs.append("point dans le nom")
    if re.search(r"[^\w,.\s-]", base):
        erreurs.append("caractère spécial")
    resultat = {"nom": nom, "ok": False, "erreurs": erreurs}
    reste, slide = base.lower(), None
    trouve = re.search(r"-slide-(\d\d)$", reste)
    if trouve:
        slide, reste = int(trouve.group(1)), reste[:trouve.start()]
    version = None
    trouve = re.search(r"-v(\d+)$", reste)
    if trouve:
        if trouve.group(1).startswith("0"):
            erreurs.append(f"version écrite v{trouve.group(1)} : écrire v{int(trouve.group(1))}")
        version, reste = int(trouve.group(1)), reste[:trouve.start()]
        if re.search(r"-slide-\d\d$", reste):
            erreurs.append("version après la slide : -vN se place avant -slide-nn")
            return resultat
    segments = reste.split("-")
    if len(segments) < 5 or not re.fullmatch(r"\d\d", segments[0]) or not re.fullmatch(r"\d\d", segments[1]):
        erreurs.append("aa-mm manquant")
        return resultat
    milieu = "-".join(segments[2:])
    type_, debut = _trouver_type(milieu)
    if type_ is None:
        erreurs.append("type absent de la liste fermée")
        return resultat
    client = milieu[:debut].rstrip("-")
    apres = milieu[debut + len(type_):].lstrip("-")
    ordre = TYPES_INFOS[type_]["ordre"]
    numero, sujet_ = None, ""
    if ordre == "reel":
        morceaux = apres.split("-") if apres else []
        if morceaux and re.fullmatch(r"\d\d", morceaux[0]):
            numero, sujet_ = int(morceaux[0]), "-".join(morceaux[1:])
        elif morceaux and re.fullmatch(r"\d\d", morceaux[-1]):
            erreurs.append("réel à l'ancien format : le numéro doit suivre cc / nocc")
            return resultat
        else:
            erreurs.append("numéro à 2 chiffres manquant")
            return resultat
    else:
        morceaux = apres.split("-") if apres else []
        if not morceaux or not re.fullmatch(r"\d\d", morceaux[-1]):
            erreurs.append("numéro à 2 chiffres manquant" if not (type_ == "carrousel" and slide) else "numéro du carrousel manquant")
            return resultat
        numero, sujet_ = int(morceaux[-1]), "-".join(morceaux[:-1])
    if versionne(type_) and version is None:
        erreurs.append("version manquante : finir par -v1 (principale), -v2…")
    if not versionne(type_) and version is not None:
        erreurs.append(f"un {type_} n'a pas de version")
    if not client:
        erreurs.append("client manquant")
    if not sujet_:
        erreurs.append("référence manquante" if ordre == "piece" else "sujet manquant")
    if type_ == "carrousel" and slide is None and extension.lower() in (".jpg", ".jpeg", ".png"):
        erreurs.append("slide-nn manquant")
    if ordre == "carte" and sujet_:
        dernier = sujet_.split("-")[-1]
        if not (dernier in FORMATS_CARTE or re.fullmatch(r"\d+x\d+", dernier) or "digitale" in sujet_.split("-")):
            erreurs.append("format de carte manquant")
    actes = noms_actes(espace)
    if actes is not None and client:
        if client not in actes:
            erreurs.append(f"nom court non acté : {client}")
        elif espace.get("clients", {}).get(client, {}).get("restaurant"):
            restaurant = True
    if restaurant and type_ == "broll" and not any(sujet_ == c or sujet_.startswith(c + "-") for c in CATEGORIES_RESTAURANT):
        erreurs.append("catégorie de b-roll manquante")
    resultat.update(ok=not erreurs, mois=f"{segments[0]}-{segments[1]}", client=client, type=type_,
                    famille=TYPES_INFOS[type_]["famille"], sujet=sujet_, numero=numero, version=version, slide=slide)
    return resultat


def analyser_dossier(nom, espace=None):
    """Dossiers nommés par la convention : rushs mensuels, rushs extra, cartes de saison."""
    nom = unicodedata.normalize("NFC", nom)
    erreurs = []
    if nom != nom.lower() or " " in nom or "." in nom or "_" in nom:
        erreurs.append("majuscules, espace, point ou underscore")
    formes = [
        (r"(\d\d)-(\d\d)-(.+)-rushs-mensuels", "rushs-mensuels"),
        (r"(\d\d)-(.+)-rushs-extra", "rushs-extra"),
        (r"(\d\d)-(\d\d)-(.+)-cartes-([^-]+)", "cartes"),
    ]
    for motif, genre in formes:
        trouve = re.fullmatch(motif, nom)
        if trouve:
            client = trouve.group(3) if genre != "rushs-extra" else trouve.group(2)
            if re.search(r"(janvier|fevrier|février|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|decembre|décembre)", client):
                erreurs.append("mois écrit en lettres")
            actes = noms_actes(espace)
            if actes is not None and client not in actes:
                erreurs.append(f"nom court non acté : {client}")
            return {"nom": nom, "ok": not erreurs, "erreurs": erreurs, "genre": genre, "client": client}
    erreurs.append("forme de dossier inconnue")
    return {"nom": nom, "ok": False, "erreurs": erreurs}


def doublons_clients(clients):
    """Les noms différents qui désignent le même client, en ignorant accents et majuscules."""
    groupes = {}
    for client in clients:
        groupes.setdefault(sans_accents(client), set()).add(client)
    return [sorted(g) for g in groupes.values() if len(g) > 1]


# ---------- numéros ----------

def prochain_numero(dossier, prefixes):
    """Le numéro suivant parmi les fichiers commençant par l'un de ces préfixes (aa-mm-client-type-sujet)."""
    plus_haut = 0
    if Path(dossier).is_dir():
        for fichier in Path(dossier).iterdir():
            nom = unicodedata.normalize("NFC", fichier.name)
            infos = analyser(nom)
            if infos["ok"] and any(nom.startswith(p + "-") for p in prefixes):
                plus_haut = max(plus_haut, infos["numero"])
    return plus_haut + 1


def prochain_numero_reel(dossiers, mois, client):
    """Le rang du prochain réel de ce client dans ce mois (cc et nocc partagent le même numéro)."""
    plus_haut = 0
    for dossier in ([dossiers] if isinstance(dossiers, (str, Path)) else dossiers):
        if Path(dossier).is_dir():
            for fichier in Path(dossier).rglob("*"):
                infos = analyser(fichier.name)
                if infos["ok"] and infos["type"] in ("reel-cc", "reel-nocc") and infos["mois"] == mois and infos["client"] == client:
                    plus_haut = max(plus_haut, infos["numero"])
    return plus_haut + 1


def prochaine_version(dossiers, mois, client, numero, types=("reel-cc", "reel-nocc")):
    """La version suivante d'un même contenu (même mois, client, numéro et famille de types)."""
    plus_haute = 0
    for dossier in ([dossiers] if isinstance(dossiers, (str, Path)) else dossiers):
        if Path(dossier).is_dir():
            for fichier in Path(dossier).rglob("*"):
                infos = analyser(fichier.name)
                if infos["ok"] and infos["type"] in types and infos["mois"] == mois and infos["client"] == client and infos["numero"] == numero:
                    plus_haute = max(plus_haute, infos["version"] or 0)
    return plus_haute + 1


def nom_piece(tiers, type_, date, ref, extension, dossier=None, espace=None):
    """Le nom d'une pièce comptable : aa-mm-tiers-type-référence-numéro.ext (aa-mm = mois de la pièce)."""
    if TYPES_INFOS.get(type_, {}).get("ordre") != "piece":
        raise SystemExit(f"{type_} n'est pas un type de pièce ({', '.join(t for t, i in TYPES_INFOS.items() if i['ordre'] == 'piece')})")
    actes = noms_actes(espace)
    if actes is not None and tiers not in actes:
        raise SystemExit(f"Nom court non acté : {tiers}. Demande-le, puis ajoute-le à l'espace.")
    jour = datetime.date.fromisoformat(date) if isinstance(date, str) else date
    mois = jour.strftime("%y-%m")
    ref_ = reference(ref)
    numero = prochain_numero(dossier, [f"{mois}-{tiers}-{type_}-{ref_}"]) if dossier else 1
    return nom_fichier(mois, tiers, type_, ref_, numero, extension)


def nommer_carrousel(dossier, client, sujet_, mois, numero=None, version=None):
    """Renomme les slide-NN d'un dossier selon la convention. Ne touche à rien si un nom existe déjà.
    Une déclinaison du même carrousel (un 4b) garde son numéro et prend la version suivante (--version 2)."""
    dossier = Path(dossier)
    slides = sorted(f for f in dossier.iterdir() if re.fullmatch(r"slide-\d\d", f.stem))
    if not slides:
        return []
    prefixe = f"{mois}-{client}-carrousel-{sujet_}"
    if not numero:
        suivant = prochain_numero(dossier, [prefixe])
        numero = max(1, suivant - 1) if version else suivant
    paires = [(f, dossier / nom_fichier(mois, client, "carrousel", sujet_, numero, f.suffix, int(f.stem[-2:]), version)) for f in slides]
    if any(cible.exists() for _, cible in paires):
        raise SystemExit("Un fichier porte déjà ce nom. Rien n'a été renommé.")
    for source, cible in paires:
        source.rename(cible)
    return [cible.name for _, cible in paires]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--espace")
    actions = parser.add_subparsers(dest="action", required=True)
    p = actions.add_parser("verifier")
    p.add_argument("noms", nargs="+")
    p.add_argument("--restaurant", action="store_true")
    actions.add_parser("dossier").add_argument("noms", nargs="+")
    actions.add_parser("sujet").add_argument("texte")
    actions.add_parser("clients").add_argument("noms", nargs="+")
    actions.add_parser("version")
    p = actions.add_parser("piece")
    p.add_argument("--tiers", required=True)
    p.add_argument("--type", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--reference", required=True)
    p.add_argument("--ext", required=True)
    p.add_argument("--dossier")
    p = actions.add_parser("carrousel")
    p.add_argument("--dossier", required=True)
    p.add_argument("--client", required=True)
    p.add_argument("--style", required=True, choices=sorted(CODES_CARROUSEL))
    p.add_argument("--sujet", required=True)
    p.add_argument("--periode", default=periode())
    p.add_argument("--numero", type=int)
    p.add_argument("--version", type=int)
    args = parser.parse_args()
    espace = charger_espace(args.espace)
    if args.action == "verifier":
        sortie = [analyser(n, args.restaurant, espace) for n in args.noms]
    elif args.action == "dossier":
        sortie = [analyser_dossier(n, espace) for n in args.noms]
    elif args.action == "sujet":
        sortie = sujet(args.texte)
    elif args.action == "clients":
        sortie = doublons_clients(args.noms)
    elif args.action == "version":
        sortie = {"convention": VERSION, "espace": espace and espace.get("espace")}
    elif args.action == "piece":
        sortie = nom_piece(args.tiers, args.type, args.date, args.reference, args.ext, args.dossier, espace)
    else:
        sortie = nommer_carrousel(args.dossier, args.client, f"{CODES_CARROUSEL[args.style]}-{sujet(args.sujet)}", args.periode, args.numero, args.version)
    print(json.dumps(sortie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

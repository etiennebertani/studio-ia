#!/usr/bin/env python3
"""La veille des mises à jour et le miroir, communs à tous les outils de la famille.

Écrit dans le Socle, recopié dans chaque outil par la diffusion. Ne modifie jamais cette copie.

    python3 veille.py etat [--forcer]        # y a-t-il une version plus récente ? (au plus une fois par rythme)
    python3 veille.py rythme semaine|mois|auto|jamais   # le choix de la personne (auto = mises à jour automatiques de Claude Code)
    python3 veille.py vu                       # la personne a vu les nouveautés de la version installée
    python3 veille.py miroir [--vers DOSSIER] # copie l'outil dans le miroir choisi, puis vérifie
    python3 veille.py choisir-miroir DOSSIER   # note le dossier choisi par la personne (sert aussi sans magasinier)

Ce module ne fait que lire en ligne et copier : il n'installe rien, ne supprime rien et n'écrase rien.
Toutes les réponses sont du JSON. Une erreur réseau ne bloque jamais l'outil : elle est rendue dans « erreur ».

L'outil décrit sa source dans ressources/veille.json :
    {"depot": "proprietaire/nom" ou null, "branche": "main", "chemin_version": "plugin/.claude-plugin/plugin.json",
     "nom_miroir": "Nom du dossier dans le miroir"}
Le miroir est choisi par la personne et noté dans ~/Magasinier/mon-espace/config.json : {"miroir": "/chemin"}
(avec ou sans magasinier installé ; l'ancien emplacement ~/.magasinier/config.json est encore lu).
"""
import datetime
import hashlib
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
RYTHMES = {"semaine": 7, "mois": 30, "auto": 7, "jamais": None}
# Une seule liste pour la copie ET la vérification : seul ce qui se refabrique est exclu.
# Les dépendances livrées avec un outil (par exemple vendor/node_modules) font partie de l'outil : elles entrent.
EXCLUS_NOMS = {".git", ".DS_Store", "__pycache__", ".venv"}


def exclu(relatif):
    parts = Path(relatif).parts
    return any(p in EXCLUS_NOMS or p.startswith("chantier-") or p.endswith(".pyc") for p in parts)


def lire_json(chemin, defaut=None):
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def identite():
    infos = lire_json(PLUGIN / ".claude-plugin/plugin.json", {})
    return infos.get("name", PLUGIN.name), infos.get("version", "0")


MON_ESPACE = Path.home() / "Magasinier" / "mon-espace"
ANCIENNE_CONFIG = Path.home() / ".magasinier" / "config.json"  # contrat v3, lue seulement pour la transition


def chemin_config():
    return Path(os.environ.get("MAGASINIER_CONFIG", MON_ESPACE / "config.json"))


def config_magasinier():
    config = lire_json(chemin_config(), None)
    if config is None and "MAGASINIER_CONFIG" not in os.environ:
        config = lire_json(ANCIENNE_CONFIG, None)
    return config or {}


def dossier_etat():
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or MON_ESPACE / "veille"
    Path(base).mkdir(parents=True, exist_ok=True)
    return Path(base)


def en_nombres(version):
    morceaux = []
    for m in str(version).split("."):
        chiffres = "".join(c for c in m if c.isdigit())
        morceaux.append(int(chiffres) if chiffres else 0)
    return tuple(morceaux + [0] * (3 - len(morceaux)))


def etat(forcer=False):
    nom, version = identite()
    source = lire_json(PLUGIN / "ressources/veille.json", {})
    memo_chemin = dossier_etat() / f"veille-{nom}.json"
    memo = lire_json(memo_chemin, {"rythme": "semaine"})
    reponse = {"outil": nom, "installee": version, "rythme": memo.get("rythme", "semaine"),
               "choix_fait": bool(memo.get("choisi"))}
    if memo.get("derniere_vue") != version:
        reponse["nouveautes"] = nouveautes(version, memo.get("derniere_vue"))
    if not source.get("depot"):
        return {**reponse, "a_verifier": False, "raison": "pas de dépôt public pour cet outil"}
    jours = RYTHMES.get(memo.get("rythme", "semaine"), 7)
    derniere = memo.get("derniere_verification")
    if not forcer:
        if jours is None:
            return {**reponse, "a_verifier": False, "raison": "veille coupée par la personne"}
        if derniere and datetime.datetime.fromisoformat(derniere) > datetime.datetime.now() - datetime.timedelta(days=jours):
            return {**reponse, "a_verifier": False, "raison": "déjà vérifié récemment", "derniere_verification": derniere}
    url = os.environ.get("VEILLE_SOURCE") or (
        f"https://raw.githubusercontent.com/{source['depot']}/{source.get('branche', 'main')}/"
        f"{source.get('chemin_version', 'plugin/.claude-plugin/plugin.json')}")
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            publiee = json.loads(r.read().decode("utf-8")).get("version", "0")
    except Exception as erreur:  # le réseau ne bloque jamais l'outil
        return {**reponse, "a_verifier": True, "erreur": f"vérification impossible : {type(erreur).__name__}"}
    memo["derniere_verification"] = datetime.datetime.now().isoformat(timespec="seconds")
    memo_chemin.write_text(json.dumps(memo, ensure_ascii=False, indent=1), encoding="utf-8")
    plus_recente = en_nombres(publiee) > en_nombres(version)
    return {**reponse, "a_verifier": True, "publiee": publiee, "nouvelle": plus_recente,
            "depot": source["depot"]}


def nouveautes(version, depuis=None):
    """Les nouveautés depuis la dernière version vue (« depuis »), jusqu'à la version installée comprise.
    Sans version vue (première installation ou ancienne version sans veille) : les trois dernières sections au plus."""
    try:
        texte = (PLUGIN / "ressources/nouveautes.md").read_text(encoding="utf-8")
    except OSError:
        return None
    sections = []
    for m in texte.split("\n## ")[1:]:
        titre, _, corps = m.partition("\n")
        titre = titre.strip()
        if en_nombres(titre) <= en_nombres(version) and (depuis is None or en_nombres(titre) > en_nombres(depuis)):
            sections.append((en_nombres(titre), titre, corps.strip()))
    sections.sort(reverse=True)
    if depuis is None:
        sections = sections[:3]
    if not sections:
        return None
    return "\n".join(f"{titre} :\n{corps}" for _, titre, corps in sections if corps)


def vu():
    nom, version = identite()
    memo_chemin = dossier_etat() / f"veille-{nom}.json"
    memo = lire_json(memo_chemin, {})
    memo["derniere_vue"] = version
    memo_chemin.write_text(json.dumps(memo, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"outil": nom, "derniere_vue": version}


def rythme(valeur):
    if valeur not in RYTHMES:
        raise SystemExit("Rythme : semaine, mois ou jamais")
    nom, _ = identite()
    memo_chemin = dossier_etat() / f"veille-{nom}.json"
    memo = lire_json(memo_chemin, {})
    memo["rythme"] = valeur
    memo["choisi"] = True
    memo_chemin.write_text(json.dumps(memo, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"outil": nom, "rythme": valeur}


def choisir_miroir(dossier):
    """Note le choix de la personne. Avec ou sans magasinier, c'est le même endroit : il le reprendra."""
    dossier = Path(dossier).expanduser()
    if not dossier.is_dir():
        return {"ok": False, "raison": f"ce dossier n'existe pas : {dossier}"}
    chemin = chemin_config()
    config = config_magasinier()
    ancien = config.get("miroir")
    config["miroir"] = str(dossier)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(config, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"ok": True, "miroir": str(dossier), "ancien": ancien}


def empreintes(racine):
    return {str(p.relative_to(racine)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(racine.rglob("*")) if p.is_file() and not exclu(p.relative_to(racine))}


def miroir(vers=None):
    nom, version = identite()
    base = vers or config_magasinier().get("miroir")
    if not base:
        return {"ok": False, "outil": nom, "raison": "aucun dossier de miroir choisi : demande-le à la personne "
                "(le magasinier peut proposer le plus logique), puis lance « choisir-miroir »"}
    base = Path(base).expanduser()
    if not base.is_dir():
        return {"ok": False, "outil": nom, "raison": f"le dossier de miroir n'existe pas : {base}"}
    # Le nom du dossier dans le miroir est fixé par l'outil (« nom_miroir » dans veille.json), sinon son nom technique.
    dossier = lire_json(PLUGIN / "ressources/veille.json", {}).get("nom_miroir") or nom
    cible = base / dossier / f"v{version}"
    deja = cible.exists()
    source = empreintes(PLUGIN)
    present = empreintes(cible) if deja else {}
    # Une version déjà en miroir n'est jamais réécrite : on ajoute seulement ce qui manque.
    differents = [k for k, v in source.items() if k in present and present[k] != v]
    if differents:
        return {"ok": False, "outil": nom, "version": version, "miroir": str(cible), "deja_present": True,
                "differences": differents[:20],
                "conseil": "le miroir de cette version diffère de l'outil : monte le numéro de version avant de sauvegarder à nouveau"}
    ajoutes = 0
    for relatif in source:
        if relatif not in present:
            arrivee = cible / relatif
            arrivee.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PLUGIN / relatif, arrivee)
            ajoutes += 1
    apres = empreintes(cible)
    manquants = [k for k, v in source.items() if apres.get(k) != v]
    return {"ok": not manquants, "outil": nom, "version": version, "miroir": str(cible), "deja_present": deja,
            "fichiers": len(apres), "ajoutes": ajoutes, "differences": manquants[:20]}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    action = sys.argv[1]
    if action == "etat":
        sortie = etat(forcer="--forcer" in sys.argv)
    elif action == "rythme" and len(sys.argv) > 2:
        sortie = rythme(sys.argv[2])
    elif action == "vu":
        sortie = vu()
    elif action == "choisir-miroir" and len(sys.argv) > 2:
        sortie = choisir_miroir(sys.argv[2])
    elif action == "miroir":
        vers = sys.argv[sys.argv.index("--vers") + 1] if "--vers" in sys.argv else None
        sortie = miroir(vers)
    else:
        raise SystemExit(__doc__)
    print(json.dumps(sortie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

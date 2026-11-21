"""Renommer des fichiers déjà là, sur liste validée, avec un journal pour revenir en arrière.

    python3 renommer.py proposer <dossier> --tiers <nom court> [--type facture] [--espace <espace>]
        → écrit une liste « ancien → nouveau » (CSV) sans rien renommer, et l'affiche.
    python3 renommer.py appliquer <liste.csv>
        → renomme seulement les lignes « ok » (que la personne a pu corriger ou retirer), écrit un journal.
    python3 renommer.py annuler <journal.json>
        → remet les anciens noms.

Les listes et journaux vont dans ~/Socle/chantier-renommages/. Ne jamais appliquer une liste
qui n'a pas été montrée et validée. Une ligne « à vérifier » n'est jamais renommée.
Pour lire les PDF, le Socle utilise son environnement ~/Socle/.venv (pypdf) s'il existe.
"""
import argparse
import csv
import datetime
import json
import re
import sys
import unicodedata
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import nommage  # noqa: E402

for site in (Path.home() / "Socle/.venv/lib").glob("python3*/site-packages"):
    sys.path.append(str(site))
try:
    import pypdf
except ImportError:
    pypdf = None

CHANTIER = Path.home() / "Socle" / "chantier-renommages"
MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "janv": 1, "févr": 2, "fevr": 2, "avr": 4, "juil": 7, "sept": 9, "oct": 10, "nov": 11, "déc": 12, "dec": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9}
ETIQUETTES_DATE = r"(?:date de (?:la )?facture|date de facturation|date d'émission|invoice date|date)"


def texte_pdf(chemin):
    if pypdf is None or chemin.suffix.lower() != ".pdf":
        return ""
    try:
        return pypdf.PdfReader(str(chemin)).pages[0].extract_text() or ""
    except Exception:
        return ""


def date_dans(texte):
    """La première date trouvée : 2026-11-03, 03/11/2026, 11172026 (mmjjaaaa), 3 novembre 2026, Nov 17, 2026."""
    essais = [
        (r"(20\d\d)-(\d\d)-(\d\d)", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
        (r"\b(\d{1,2})/(\d{1,2})/(20\d\d)\b", lambda m: (int(m[3]), int(m[2]), int(m[1]))),
        (r"(?<!\d)(\d\d)(\d\d)(20\d\d)(?!\d)", lambda m: (int(m[3]), int(m[1]), int(m[2]))),
        (r"\b(\d{1,2})\s+([a-zéû]+)\s+(20\d\d)", lambda m: (int(m[3]), MOIS.get(m[2].lower(), 0), int(m[1]))),
        (r"\b([A-Za-zéû]+)\.?\s+(\d{1,2}),\s+(20\d\d)", lambda m: (int(m[3]), MOIS.get(m[1].lower(), 0), int(m[2]))),
    ]
    for motif, lire in essais:
        for m in re.finditer(motif, texte):
            try:
                return datetime.date(*lire(m))
            except (ValueError, TypeError):
                continue
    return None


def date_etiquetee(texte):
    """La date qui suit une étiquette « date de la facture », « invoice date »… sur la même ligne."""
    for ligne in texte.splitlines():
        m = re.search(ETIQUETTES_DATE + r"[^\n]*?[:\s](.*)", ligne, re.I)
        if m and re.search(r"(?i)factur|invoice|émission|^\s*date\s*:", ligne):
            d = date_dans(m.group(1))
            if d:
                return d
    return None


def reference_dans(nom, texte):
    jeton = r"((?=[A-Z-]*\d)[A-Z0-9][A-Z0-9-]{3,})"
    etiquette = r"(?:num[ée]ro de (?:la )?facture|facture\s*n°|invoice\s*(?:#|no\.?|number|n°)?\s*:?|receipt\s*(?:#|no\.?|number))"
    for source in (texte, nom):
        m = re.search(etiquette + r"\s*:?\s*" + jeton, source, re.I)
        if m:
            return m.group(1)
    for motif, sources in ((r"FBADS-\d+-\d+", (nom, texte)), (r"INV[A-Z]*\d+", (nom, texte)),
                           (r"\b\d{3}-\d{7}-\d{7}\b", (nom,)), (r"(?<!\d)\d{6,}(?!\d)", (nom,))):
        for source in sources:
            m = re.search(motif, source)
            if m:
                return m.group(0)
    return None


def proposer(dossier, tiers, type_, espace_nom):
    espace = nommage.charger_espace(espace_nom)
    dossier = Path(dossier)
    lignes, pris = [], set()
    for fichier in sorted(p for p in dossier.iterdir() if p.is_file() and not p.name.startswith(".")):
        nom = unicodedata.normalize("NFC", fichier.name)
        if nommage.analyser(nom, espace=espace)["ok"]:
            lignes.append({"ancien": nom, "nouveau": "", "statut": "déjà conforme", "raison": ""})
            continue
        if fichier.suffix.lower() not in (".pdf", ".png", ".jpg", ".jpeg"):
            lignes.append({"ancien": nom, "nouveau": "", "statut": "garde son nom", "raison": "pas une pièce (export, archive…)"})
            continue
        texte = texte_pdf(fichier)
        date = date_etiquetee(texte) or date_dans(nom) or date_dans(texte)
        ref = reference_dans(nom, texte)
        manque = [m for m, v in (("date", date), ("référence", ref)) if not v]
        if manque:
            lignes.append({"ancien": nom, "nouveau": "", "statut": "à vérifier", "raison": "introuvable : " + ", ".join(manque)})
            continue
        if texte and nommage.sans_accents(tiers) not in nommage.sans_accents(texte) and nommage.sans_accents(tiers) not in nommage.sans_accents(nom):
            nouveau = nommage.nom_piece(tiers, type_, date, ref, fichier.suffix, None, espace)
            lignes.append({"ancien": nom, "nouveau": nouveau, "statut": "à vérifier", "raison": f"« {tiers} » absent de la pièce : autre fournisseur ?"})
            continue
        nouveau = nommage.nom_piece(tiers, type_, date, ref, fichier.suffix, None, espace)
        while nouveau in pris or (dossier / nouveau).exists():
            infos = nommage.analyser(nouveau)
            nouveau = nommage.nom_fichier(infos["mois"], tiers, type_, infos["sujet"], infos["numero"] + 1, fichier.suffix)
        pris.add(nouveau)
        source = "la pièce" if date_etiquetee(texte) else "le nom du fichier" if date_dans(nom) else "le PDF (sans étiquette)"
        lignes.append({"ancien": nom, "nouveau": nouveau, "statut": "ok", "raison": f"date lue dans {source}"})
    CHANTIER.mkdir(parents=True, exist_ok=True)
    liste = CHANTIER / f"{datetime.datetime.now():%Y%m%d-%H%M%S}-{nommage.sujet(dossier.name)}.csv"
    with liste.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# dossier: {dossier}\n")
        ecrivain = csv.DictWriter(f, fieldnames=["ancien", "nouveau", "statut", "raison"])
        ecrivain.writeheader()
        ecrivain.writerows(lignes)
    for l in lignes:
        print(f"{l['statut']:14} {l['ancien']}" + (f"  →  {l['nouveau']}" if l["nouveau"] else f"  ({l['raison']})" if l["raison"] else ""))
    print(f"\nListe : {liste}")
    return liste


def lire_liste(liste):
    lignes = Path(liste).read_text(encoding="utf-8").splitlines()
    dossier = Path(lignes[0].split(":", 1)[1].strip())
    return dossier, list(csv.DictReader(lignes[1:]))


def appliquer(liste):
    dossier, lignes = lire_liste(liste)
    a_faire = [l for l in lignes if l["statut"] == "ok" and l["nouveau"]]
    for l in a_faire:
        if not nommage.analyser(l["nouveau"])["ok"]:
            sys.exit(f"Nom non conforme dans la liste : {l['nouveau']}. Rien n'a été renommé.")
        if not (dossier / l["ancien"]).exists():
            sys.exit(f"Introuvable : {l['ancien']}. Rien n'a été renommé.")
        if (dossier / l["nouveau"]).exists():
            sys.exit(f"Existe déjà : {l['nouveau']}. Rien n'a été renommé.")
    journal = {"dossier": str(dossier), "date": datetime.datetime.now().isoformat(timespec="seconds"), "renommages": []}
    for l in a_faire:
        (dossier / l["ancien"]).rename(dossier / l["nouveau"])
        journal["renommages"].append([l["ancien"], l["nouveau"]])
    chemin = Path(liste).with_suffix(".journal.json")
    chemin.write_text(json.dumps(journal, ensure_ascii=False, indent=1), encoding="utf-8")
    manquants = [n for _, n in journal["renommages"] if not (dossier / n).exists()]
    print(f"{len(journal['renommages'])} fichier(s) renommé(s), {len(manquants)} problème(s). Journal : {chemin}")
    return chemin


def annuler(journal):
    donnees = json.loads(Path(journal).read_text(encoding="utf-8"))
    dossier = Path(donnees["dossier"])
    for ancien, nouveau in reversed(donnees["renommages"]):
        if (dossier / nouveau).exists() and not (dossier / ancien).exists():
            (dossier / nouveau).rename(dossier / ancien)
    print(f"{len(donnees['renommages'])} nom(s) remis comme avant.")


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    p = actions.add_parser("proposer")
    p.add_argument("dossier")
    p.add_argument("--tiers", required=True)
    p.add_argument("--type", default="facture")
    p.add_argument("--espace")
    actions.add_parser("appliquer").add_argument("liste")
    actions.add_parser("annuler").add_argument("journal")
    args = parser.parse_args()
    if args.action == "proposer":
        proposer(args.dossier, args.tiers, args.type, args.espace)
    elif args.action == "appliquer":
        appliquer(args.liste)
    else:
        annuler(args.journal)


if __name__ == "__main__":
    main()

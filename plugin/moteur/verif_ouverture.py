"""Dit si la vérification des légendes Notion est à faire, pour ne la lancer qu'une fois par période.

    python3 verif_ouverture.py etat
    python3 verif_ouverture.py marquer

La date de la dernière vérification est gardée dans l'espace personnel.
"""
import datetime
import json
import sys

import commun

FICHIER = commun.ESPACE / ".verification-notion.json"
HEURES = 6


def maintenant():
    return datetime.datetime.now(datetime.timezone.utc)


def etat():
    depuis = None
    if FICHIER.is_file():
        try:
            depuis = json.loads(FICHIER.read_text(encoding="utf-8")).get("derniere")
        except (json.JSONDecodeError, OSError):
            depuis = None
    a_faire = True
    if depuis:
        try:
            a_faire = maintenant() - datetime.datetime.fromisoformat(depuis) >= datetime.timedelta(hours=HEURES)
        except ValueError:
            depuis, a_faire = None, True
    return {"a_faire": a_faire, "derniere": depuis}


def marquer():
    FICHIER.write_text(json.dumps({"derniere": maintenant().isoformat()}), encoding="utf-8")
    return {"ok": True}


if __name__ == "__main__":
    actions = {"etat": etat, "marquer": marquer}
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        sys.exit(__doc__)
    print(json.dumps(actions[sys.argv[1]](), ensure_ascii=False))

"""Crée ou retire les commandes courtes (/start, /montage...) dans ~/.claude/skills.

    python3 raccourcis.py --creer
    python3 raccourcis.py --retirer

Ne remplace jamais une commande qui n'a pas été créée par le Studio.
"""
import argparse
import json
import shutil

import commun

MODELE = """---
name: {nom}
description: Raccourci du Studio IA, lance /studio:{nom}.
disable-model-invocation: true
---

Lance immédiatement le skill `studio:{nom}` avec l'outil Skill, en lui transmettant : $ARGUMENTS
"""


def creer():
    crees, pris = [], []
    for nom in commun.noms_raccourcis():
        dossier = commun.SKILLS_PERSO / nom
        if dossier.exists() and not (dossier / commun.MARQUE_RACCOURCI).exists():
            pris.append(nom)
            continue
        dossier.mkdir(parents=True, exist_ok=True)
        (dossier / "SKILL.md").write_text(MODELE.format(nom=nom), encoding="utf-8")
        (dossier / commun.MARQUE_RACCOURCI).touch()
        crees.append(nom)
    print(json.dumps({"crees": crees, "deja_pris": pris}, ensure_ascii=False))


def retirer():
    retires = []
    if commun.SKILLS_PERSO.is_dir():
        for dossier in commun.SKILLS_PERSO.iterdir():
            if (dossier / commun.MARQUE_RACCOURCI).exists():
                shutil.rmtree(dossier)
                retires.append(dossier.name)
    print(json.dumps({"retires": retires}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--creer", action="store_true")
    groupe.add_argument("--retirer", action="store_true")
    args = parser.parse_args()
    creer() if args.creer else retirer()


if __name__ == "__main__":
    main()

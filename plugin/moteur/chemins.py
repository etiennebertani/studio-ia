"""Affiche, au format JSON, l'emplacement de chaque dossier de l'espace personnel.

    python3 chemins.py

C'est ici que les recettes du Studio trouvent les vrais noms des dossiers.
"""
import json

import commun

chemins = {cle: str(commun.ESPACE / nom) for cle, nom in commun.NOMS.items()}
chemins.update(espace=str(commun.ESPACE), archive=str(commun.ARCHIVE), config=str(commun.CONFIG))
print(json.dumps(chemins, ensure_ascii=False, indent=2))

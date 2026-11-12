"""Relit les légendes publiées sur Instagram et les compare aux légendes du Studio.

    python3 relire_publications.py <lien de post> [<lien> ...]            compare, ne modifie rien
    python3 relire_publications.py --ecrire <lien> [<lien> ...]           met à jour les contenus certains

Les liens viennent du profil de la personne, lus dans un navigateur (Chrome d'abord, sinon le navigateur de l'app).
Pour chaque post, l'outil lit la légende publiée (yt-dlp, sans connexion), cherche le contenu le plus proche dans
les dossiers Reels et Carrousels (fichier final/legendes.txt), et dit :
- "a_jour"    : la légende publiée est déjà enregistrée ;
- "certain"   : un seul contenu correspond clairement (très proche, ou même accroche que l'une des
                versions proposées, avec une nette avance sur les autres), et la légende publiée a changé ;
- "doute"     : un contenu ressemble, mais pas assez pour être sûr : on demande à la personne ;
- "inconnu"   : aucun contenu du Studio ne correspond (post fait avant ou en dehors du Studio).

Avec --ecrire, seuls les cas "certain" sont mis à jour : la légende publiée passe en tête de legendes.txt, avec la
date et le lien du post, et les versions proposées restent en dessous. Rien n'est jamais effacé.
Affiche le résultat au format JSON.
"""
import argparse
import datetime
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

import commun

SEUIL_CERTAIN = 0.6     # ressemblance mini avec le meilleur contenu
ECART_CERTAIN = 0.15    # avance mini sur le deuxième contenu
SEUIL_DOUTE = 0.3
TITRE_PUBLIEE = "PUBLIÉE sur Instagram"
SEPARATEUR = "=== PROPOSÉES AVANT PUBLICATION ==="


def mots(texte):
    return re.findall(r"\w+", texte.lower().replace("’", "'"))


def lire_post(lien):
    """Légende, date et code du post, sans connexion."""
    r = subprocess.run(["yt-dlp", "--skip-download", "--ignore-no-formats-error", "--dump-json", lien],
                       capture_output=True, text=True, timeout=120)
    lignes = [l for l in r.stdout.splitlines() if l.strip().startswith("{")]
    if not lignes:
        return None
    d = json.loads(lignes[-1])
    ts = d.get("timestamp")
    code = re.search(r"/(?:p|reel)/([^/?]+)", lien)
    return {"lien": f"https://www.instagram.com/{'reel' if '/reel/' in lien else 'p'}/{code.group(1)}/" if code else lien,
            "legende": (d.get("description") or "").strip(),
            "date": datetime.datetime.fromtimestamp(ts).strftime("%d/%m/%Y") if ts else None,
            "compte": d.get("channel") or d.get("uploader")}


def contenus():
    for cle in ("reels", "carrousels"):
        racine = commun.ESPACE / commun.NOMS[cle]
        for f in sorted(racine.glob("*/final/legendes.txt")):
            yield f.parent.parent, f


def meme_accroche(pub, fichier):
    """Vrai si la légende publiée commence comme l'une des versions proposées (5 premiers mots)."""
    if len(pub) < 5:
        return False
    for bloc in re.split(r"\n(?:LONGUE|MOYENNE|COURTE)\n", "\n" + fichier.read_text(encoding="utf-8")):
        if mots(bloc)[:5] == pub[:5]:
            return True
    return False


def comparer(post, base):
    pub = mots(post["legende"])
    scores = []
    for dossier, fichier in base:
        texte = fichier.read_text(encoding="utf-8")
        deja = post["lien"] in texte or (post["legende"] and post["legende"] in texte)
        scores.append((difflib.SequenceMatcher(None, pub, mots(texte), autojunk=False).ratio(), deja, dossier, fichier))
    scores.sort(key=lambda s: s[0], reverse=True)
    if not scores or not pub:
        return {"etat": "inconnu"}
    meilleur, deja, dossier, fichier = scores[0]
    second = scores[1][0] if len(scores) > 1 else 0
    res = {"contenu": dossier.name, "dossier": str(dossier), "ressemblance": round(meilleur, 2),
           "deuxieme": round(second, 2)}
    if deja:
        res["etat"] = "a_jour"
    elif (meilleur >= SEUIL_CERTAIN or meme_accroche(pub, fichier)) and meilleur - second >= ECART_CERTAIN:
        res["etat"] = "certain"
    elif meilleur >= SEUIL_DOUTE:
        res["etat"] = "doute"
    else:
        res = {"etat": "inconnu", "ressemblance": round(meilleur, 2)}
    return res


def ecrire(post, fichier):
    """Met la légende publiée en tête de legendes.txt, garde tout le reste."""
    ancien = fichier.read_text(encoding="utf-8")
    if ancien.startswith(TITRE_PUBLIEE):          # une ancienne version publiée : on la garde sous les propositions
        tete, _, reste = ancien.partition(SEPARATEUR)
        ancien = reste.lstrip("\n") + "\n\nANCIENNE VERSION PUBLIÉE\n\n" + tete.strip() + "\n"
    neuf = (f"{TITRE_PUBLIEE} le {post['date']} : {post['lien']}\n\n{post['legende']}\n\n\n"
            f"{SEPARATEUR}\n\n{ancien}")
    fichier.write_text(neuf, encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("liens", nargs="+")
    p.add_argument("--ecrire", action="store_true")
    a = p.parse_args()
    base = list(contenus())
    sortie = []
    for lien in a.liens:
        post = lire_post(lien)
        if post is None:
            sortie.append({"lien": lien, "etat": "illisible"})
            continue
        res = {"lien": post["lien"], "date": post["date"], "compte": post["compte"],
               "debut": post["legende"][:90], **comparer(post, base)}
        if a.ecrire and res["etat"] == "certain":
            ecrire(post, Path(res["dossier"]) / "final" / "legendes.txt")
            res["ecrit"] = True
        if res["etat"] in ("certain", "doute"):
            res["legende_publiee"] = post["legende"]
        sortie.append(res)
    print(json.dumps(sortie, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()

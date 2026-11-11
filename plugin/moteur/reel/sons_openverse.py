"""Chercher et télécharger un vrai son sur Openverse, premier réflexe avant de fabriquer un son.

    sons_openverse.py chercher "water drop" [--max 20] [--duree-max 4]
    sons_openverse.py telecharger <id> <dossier>

Licences gardées : CC0 et CC BY (auteur à citer dans la légende). Jamais NC ni ND. Chaque son téléchargé garde sa fiche
(titre, auteur, licence, page d'origine) à côté du fichier : c'est elle qui dit s'il faut créditer quelqu'un.
"""
import json, sys, urllib.parse, urllib.request
from pathlib import Path
API = "https://api.openverse.org/v1/audio/"
ENTETE = {"User-Agent": "studio-ia-plugin"}

def lire(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=ENTETE), timeout=30) as r:
        return r.read()

def chercher(q, maxi=20, duree_max=4.0):
    d = json.loads(lire(API + "?" + urllib.parse.urlencode({"q": q, "license": "cc0,by", "page_size": maxi})))
    return [{"id": r["id"], "titre": r["title"], "auteur": r["creator"], "licence": f"{r['license']} {r['license_version']}",
             "duree": round((r.get("duration") or 0) / 1000, 2), "page": r["foreign_landing_url"],
             "a_crediter": r["license"] != "cc0"} for r in d.get("results", []) if 0 < (r.get("duration") or 0) / 1000 <= duree_max]

def telecharger(ident, dossier):
    fiche = json.loads(lire(API + ident + "/")); d = Path(dossier); d.mkdir(parents=True, exist_ok=True)
    if fiche["license"] not in ("cc0", "by"):
        raise SystemExit("licence refusée : " + fiche["license"])
    ext = (fiche.get("filetype") or "mp3").split("/")[-1]
    f = d / f"{ident}.{ext}"; f.write_bytes(lire(fiche["url"]))
    (d / f"{ident}.json").write_text(json.dumps({k: fiche.get(k) for k in ("id", "title", "creator", "license", "license_version",
        "license_url", "foreign_landing_url", "attribution")}, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(f)

if __name__ == "__main__":
    if sys.argv[1] == "chercher":
        args = sys.argv[2:]; q = args[0]
        maxi = int(args[args.index("--max") + 1]) if "--max" in args else 20
        dm = float(args[args.index("--duree-max") + 1]) if "--duree-max" in args else 4.0
        print(json.dumps(chercher(q, maxi, dm), ensure_ascii=False, indent=1))
    else:
        print(telecharger(sys.argv[2], sys.argv[3]))

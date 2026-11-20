#!/usr/bin/env python3
"""Studio IA : la marque de la personne est la seule source de vérité du style.

Le module n'a plus d'accueil ni de style à lui. À chaque nouveau projet, ce fichier relit la marque définie dans le
Studio IA (mon-espace/00. Branding/<marque>/ : marque.json, montage.json, polices/, photo de profil) et en déduit le
style du module ($STUDIO_PO_HOME/style/ : style.json, STYLE.md, brand.css, fonts/, headshot). Ce dossier est
régénéré à chaque fois : on ne le modifie jamais à la main, et on n'écrit jamais rien dans le dossier de la marque.

Run: PY pipeline/marque.py [--marque <dossier>]   (sans --marque : $STUDIO_MARQUE, sinon la seule marque du Branding)
"""
import argparse, json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style as ST  # noqa: E402

ESPACE = os.path.expanduser(os.environ.get("STUDIO_ESPACE", "~/Studio/mon-espace"))
BRANDING = os.path.join(ESPACE, "00. Branding")


def trouver_marque(dossier=None):
    dossier = dossier or os.environ.get("STUDIO_MARQUE")
    if dossier:
        return dossier if os.path.isabs(dossier) else os.path.join(BRANDING, dossier)
    marques = [os.path.join(BRANDING, d) for d in sorted(os.listdir(BRANDING))
               if os.path.isfile(os.path.join(BRANDING, d, "marque.json"))]
    if len(marques) != 1:
        sys.exit(f"{len(marques)} marques dans {BRANDING} : préciser --marque ou STUDIO_MARQUE")
    return marques[0]


def lire(chemin):
    return json.load(open(chemin)) if os.path.isfile(chemin) else {}


def police(dossier, fichier, poids, famille):
    """une police locale de la marque (fichier .ttf/.otf de polices/), sinon une famille Google Fonts"""
    chemin = os.path.join(dossier, "polices", fichier) if fichier else ""
    if chemin and os.path.isfile(chemin):
        return {"family": famille, "italic": False, "weight": poids, "file": chemin}
    return {"family": famille, "italic": False, "weight": poids}


def css_marque(V, encre):
    """La DA des vidéos face caméra du Studio IA (montage-base.json + montage.json de la marque) appliquée au module :
    sous-titres blancs sans boîte avec une ombre, 3 mots, accroche dans une boîte blanche à texte noir en police de titre."""
    return """
.kc, .cap.onfoot { background:transparent !important; color:#ffffff !important; font-size:76px !important;
  text-shadow:0 3px 3px rgba(0,0,0,.55); padding:4px 20px 9px; }
.kc .em, .cap .em, .cap.onfoot .em { color:inherit !important; }
.kw, .capw { top:1126px !important; }
.nb { top:250px !important; }
#hook { top:250px !important; }
#hook .eb, #hook-tag { display:none !important; }
#hook .h1, #hook .h2 { display:table !important; margin:0 auto !important; font-family:var(--font-display) !important; font-style:normal !important;
  font-weight:700 !important; font-size:64px !important; line-height:1.36 !important; color:#000000 !important; background:#ffffff !important;
  border-radius:24px !important; padding:6px 33px 8px !important; text-shadow:none !important; letter-spacing:0 !important; }
.nb .ln { font-family:var(--font-display) !important; font-style:normal; font-weight:700 !important; font-size:64px !important;
  line-height:1.36; color:#000000 !important; background:#ffffff !important; border-radius:24px !important; letter-spacing:0; }
"""


def style_depuis_marque(dossier):
    M, V = lire(os.path.join(dossier, "marque.json")), lire(os.path.join(dossier, "montage.json"))
    C = M.get("couleurs", {})
    titre = (V.get("titre") or {}).get("police")
    sous = (V.get("sous_titres") or {}).get("police")
    texte_carrousel = M.get("police", "Poppins")
    clair, sombre = C.get("papier", "#efede7"), C.get("papier_sombre", "#141412")
    encre, encre_claire = C.get("texte", "#0f1010"), C.get("texte_clair", "#f4f2ec")
    accent_sombre, accent_clair = C.get("surlignage_clair", "#fbf32d"), C.get("surlignage_sombre", "#2f6bff")
    return {
        "creator": {"name": M.get("nom", ""), "handle": M.get("pseudo", ""), "site": M.get("site", "")},
        "fonts": {
            "display": police(dossier, titre, 700, "Marque Titre"),
            "text": police(dossier, sous, 700, "Marque Texte"),
            "caption": police(dossier, sous, 700, "Marque Texte"),
            "mono": {"family": texte_carrousel, "italic": False, "weight": 500},
        },
        "colors": {
            "light": clair, "dark": sombre, "ink": encre,
            "muted_light": "#6e6d69", "muted_dark": "rgba(244,242,236,.58)",
            "hair_light": "#d6d4ce", "hair_dark": "rgba(244,242,236,.22)",
            "accent": accent_sombre, "accent_on_light": accent_clair,
            "caption_box": "rgba(0,0,0,0)", "caption_ink": "#ffffff", "caption_dim": "#ffffff",
            "textbox_bg": "#ffffff", "textbox_ink": "#000000",
            # pas de rouge ni de vert hors de la marque : baisse en bleu, hausse en jaune
            "negative": accent_clair, "negative_on_light": accent_clair, "positive": accent_sombre, "positive_on_light": encre,
            "series": [accent_sombre, accent_clair, encre_claire],
        },
        "grounds": {"grid": False, "radius": 24},
        "captions": {"hifi": {"box": False, "uppercase": False, "size": 76, "y": 1126},
                     "lofi": {"box": False, "size": 76, "y": 1126}},
        "modes": {
            "hifi": {"hook": "one-line", "captions": "phrases", "emphasis": [], "behind_head": "sometimes",
                     "cards": "sometimes", "camera": "still", "bw": False, "j_lead": 0},
            "lofi": {"captions": "phrase", "max_words": 3, "max_chars": 24, "text_boxes": True,
                     "overlays": "sometimes", "backdrops": "sometimes", "zooms": False, "bw": False, "j_lead": 0},
            "showcase": {"emphasis_word": "stamp", "transitions": ["push", "reveal"], "density": "medium",
                         "motif": "", "j_lead": 0},
        },
        "css_marque": css_marque(V, encre),
        "grade": "none",            # la couleur de ses vidéos ne change jamais sans qu'elle le demande
        "motion": "calm",           # sobriété
        "sound": {"sfx": "light", "music": "none"},
        "_marque": dossier,
    }


STYLE_MD = """# Style de {nom} (déduit de sa marque par le Studio IA, ne pas modifier ici)

Source de vérité : {dossier}. Toute modification se fait dans la marque, jamais dans ce fichier.

- Polices : titres en {titre}, texte et sous-titres en {texte}. Chiffres et petites mentions en {mono}.
- Couleurs : clair {clair}, sombre {sombre}, encre {encre}. Accent : {accent} sur fond sombre, {accent_clair} sur fond clair.
- Sobriété : une seule idée à l'écran, de l'air autour, mouvements calmes, peu de bruitages et toujours sous la voix.
- La couleur de la vidéo ne change jamais sans demande. Rien sur les yeux, rien sous la barre Instagram.
- Signature : {pseudo}.

## Hi-fi
Accroche sur deux lignes, sous-titres par petits groupes de mots, texte derrière la tête de temps en temps.

## Lo-fi
Sous-titres mot à mot, captures posées sur la personne quand elles servent le propos.

## Showcase
Un effet par idée forte, jamais pour décorer.
"""


def preparer(dossier=None):
    dossier = trouver_marque(dossier)
    S = ST.merge(ST.DEFAULT, style_depuis_marque(dossier))
    os.makedirs(ST.STYLE_DIR, exist_ok=True)
    propre = {k: v for k, v in S.items() if not k.startswith("_")}
    json.dump(propre, open(os.path.join(ST.STYLE_DIR, "style.json"), "w"), ensure_ascii=False, indent=1)
    F = S["fonts"]; C = S["colors"]
    open(os.path.join(ST.STYLE_DIR, "STYLE.md"), "w").write(STYLE_MD.format(
        nom=S["creator"]["name"], dossier=dossier, titre=os.path.basename(F["display"].get("file", F["display"]["family"])),
        texte=os.path.basename(F["text"].get("file", F["text"]["family"])), mono=F["mono"]["family"],
        clair=C["light"], sombre=C["dark"], encre=C["ink"], accent=C["accent"], accent_clair=C["accent_on_light"],
        pseudo=S["creator"]["handle"]))
    M = lire(os.path.join(dossier, "marque.json"))
    photo = os.path.join(dossier, M.get("photo", "photo-profil.png")) if M.get("photo") else os.path.join(dossier, "photo-profil.png")
    if os.path.isfile(photo):
        shutil.copy(photo, os.path.join(ST.STYLE_DIR, "headshot" + os.path.splitext(photo)[1].lower()))
    ST.write(S, ST.STYLE_DIR)
    return dossier


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--marque"); a = p.parse_args()
    print(json.dumps({"ok": True, "marque": preparer(a.marque), "style": ST.STYLE_DIR}, ensure_ascii=False))

"""Fabrique les slides d'un carrousel à partir d'un fichier slides.json.

    <python du moteur> rendre_carrousel.py <slides.json> <dossier de sortie>

Le texte est repris tel quel. Si un texte déborde, le rendu s'arrête avec une erreur :
le moteur ne raccourcit jamais un texte.
"""
import html
import io
import json
import random
import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
LARGEUR, HAUTEUR = 1080, 1350
MARGE_X, MARGE_Y = 60, 40
QUALITE_JPEG = 97
COULEURS_DEFAUT = {"papier": "#efede7", "papier_sombre": "#141412", "texte": "#0f1010", "texte_clair": "#f4f2ec",
                   "surlignage_clair": "#fbf32d", "surlignage_sombre": "#2f6bff"}

CHECK = ('<svg class="check" viewBox="0 0 24 24"><path fill="#3b97f3" d="M12 1l2.9 2.2 3.6-.3 1 3.5 3 2-1.4 '
         '3.4 1.4 3.4-3 2-1 3.5-3.6-.3L12 23l-2.9-2.2-3.6.3-1-3.5-3-2 1.4-3.4L1.5 8.4l3-2 1-3.5 3.6.3z"/>'
         '<path fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" '
         'd="M7.5 12.4l3 3 6-6.4"/></svg>')


def papier():
    """Papier artisanal : grain fin, légères taches et petites fibres, toujours identique."""
    alea = random.Random(7)
    fibres = []
    for _ in range(260):
        x, y = alea.uniform(0, 1080), alea.uniform(0, 1350)
        a, b = alea.uniform(-34, 34), alea.uniform(-34, 34)
        c, d = alea.uniform(-34, 34), alea.uniform(-34, 34)
        fibres.append('<path d="M{:.0f} {:.0f}q{:.0f} {:.0f} {:.0f} {:.0f}" opacity="{:.2f}"/>'.format(
            x, y, a, b, c, d, alea.uniform(.12, .42)))
    return ('<svg class="papier" width="1080" height="1350"><filter id="grain"><feTurbulence type="fractalNoise" '
            'baseFrequency=".9" numOctaves="3" seed="7"/><feColorMatrix values="0 0 0 0 .42 0 0 0 0 .4 0 0 0 0 .34 '
            '0 0 0 .3 -.08"/></filter><filter id="taches"><feTurbulence type="fractalNoise" baseFrequency=".012" '
            'numOctaves="3" seed="3"/><feColorMatrix values="0 0 0 0 .55 0 0 0 0 .5 0 0 0 0 .4 0 0 0 .4 -.14"/></filter>'
            '<filter id="bord"><feTurbulence type="fractalNoise" baseFrequency=".07 .35" numOctaves="2" seed="5"/>'
            '<feDisplacementMap in="SourceGraphic" scale="14"/></filter>'
            '<rect width="1080" height="1350" filter="url(#taches)"/><rect width="1080" height="1350" filter="url(#grain)"/>'
            '<g fill="none" stroke="#7d7461" stroke-width="1.1">' + "".join(fibres) + '</g></svg>')


PAPIER_TEXTURE = papier()
FILTRE_SEUL = ('<svg width="0" height="0" style="position:absolute"><filter id="bord"><feTurbulence type="fractalNoise" '
               'baseFrequency=".07 .35" numOctaves="2" seed="5"/><feDisplacementMap in="SourceGraphic" scale="14"/></filter></svg>')
PAPIER = PAPIER_TEXTURE


def police(famille, fichier, graisse, style="normal"):
    return ("@font-face{{font-family:'{}';src:url('{}');font-weight:{};font-style:{}}}"
            .format(famille, (ICI / "polices" / fichier).as_uri(), graisse, style))


POLICES = "".join([
    police("Poppins", "Poppins-Regular.ttf", 400), police("Poppins", "Poppins-Medium.ttf", 500),
    police("Poppins", "Poppins-SemiBold.ttf", 600), police("Poppins", "Poppins-Bold.ttf", 700),
    police("Poppins", "Poppins-Italic.ttf", 400, "italic"), police("Poppins", "Poppins-BoldItalic.ttf", 700, "italic"),
])

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
.slide{position:relative;width:1080px;height:1350px;overflow:hidden;font-family:var(--police);color:var(--texte);
  display:flex;flex-direction:column}
.papier{position:absolute;inset:0}
.clair{background:var(--papier)}
.sombre{background:var(--papier-sombre);color:var(--texte-clair)}
.sombre .papier{filter:invert(1);opacity:.45}
.journal{align-items:center;justify-content:center;padding:70px 90px}
.journal>*:not(.papier),.texte>*:not(.papier){position:relative}
.j-titre{font-weight:700;font-size:133.33px;line-height:1;text-align:center;letter-spacing:-.019em;width:900px;flex-shrink:0}
.j-sous{font-size:53.33px;line-height:1.3;text-align:center;margin-top:8px;width:900px;flex-shrink:0}
.s-jaune{background:var(--jaune);color:var(--texte);padding:0 .14em;margin:0 -.08em;border-radius:3px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.s-bleu{background:var(--bleu);color:#fff;padding:0 .14em;margin:0 -.08em;border-radius:3px;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.j-titre .s-jaune,.x-titre .s-jaune,.j-titre .s-bleu,.x-titre .s-bleu{background:none;position:relative;z-index:0;display:inline-block;margin:0;padding:0 .12em}
.j-titre .s-jaune::before,.x-titre .s-jaune::before{content:'';position:absolute;inset:.14em -.02em .06em;background:var(--jaune);z-index:-1;filter:url(#bord)}
.j-titre .s-bleu::before,.x-titre .s-bleu::before{content:'';position:absolute;inset:.14em -.02em .06em;background:var(--bleu);z-index:-1;filter:url(#bord)}
.j-img{object-fit:contain;flex-shrink:0;margin-top:36px}
.clair .j-img{mix-blend-mode:multiply;opacity:.79}
.sombre .j-img{filter:invert(1) hue-rotate(180deg);mix-blend-mode:screen;opacity:.85}
.j-img.haut{order:-1;margin-top:0;margin-bottom:36px}
.fondu{-webkit-mask-image:radial-gradient(closest-side,#000 80%,transparent)}
.j-texte{font-weight:500;font-size:45.33px;line-height:1.3;width:835px;flex-shrink:0}
.j-texte p+p{margin-top:58.9px}
.fleche{position:absolute!important;left:828px;top:1210px;font-size:26.67px;line-height:1.3;width:112px;display:flex;flex-direction:column;align-items:center;white-space:nowrap}
.fleche svg{display:block;width:112px;height:18px;margin-top:6px}
.texte{align-items:center;justify-content:center;padding:0 84px;text-align:center}
.x-titre{font-weight:400;font-size:89.33px;line-height:1;letter-spacing:-.019em;width:912px}
.x-titre b{font-weight:600}
.x-texte{font-weight:600;font-style:italic;font-size:33.33px;line-height:1.3;margin-top:12px;width:912px}
.x-texte p+p{margin-top:36px}
.tweet{justify-content:center;padding:0 100px}
.tweet.noir{background:#16181c;color:#f5f5f5}.tweet.blanc{background:#fff;color:var(--texte)}
.t-tete{display:flex;align-items:center;gap:30px;margin-bottom:60px}
.t-avatar{width:130px;height:130px;border-radius:50%;object-fit:cover;background:#8c8c8c;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:46px;font-weight:600}
.t-nom{display:flex;align-items:center;gap:14px;font-size:52px;font-weight:500;line-height:1.2}
.t-pseudo{font-size:36px;opacity:.55;margin-top:4px}
.check{width:46px;height:46px}
.t-texte{font-size:56px;line-height:1.42}
.t-texte p+p{margin-top:36px}
.t-stats{display:flex;gap:80px;margin-top:70px;font-size:42px;opacity:.75}
.punch{justify-content:center;align-items:center;text-align:center;padding:0 115px 40px}
.punch.blanc{background:#fff;color:var(--texte)}.punch.noir{background:#000;color:#fff}
.p-texte{font-weight:500;font-size:53.33px;line-height:1.3;width:850px}
.p-texte p+p{margin-top:69.3px}
.p-pseudo{position:absolute;top:1147px;font-size:33.59px;font-weight:500;opacity:.6}
"""


def e(texte):
    return html.escape(texte, quote=False).replace("\n", "<br>")


def surligner(texte, mot, couleur):
    sortie = e(texte)
    if mot:
        if e(mot) not in sortie:
            sys.exit("Mot à surligner introuvable dans le texte : {}".format(mot))
        sortie = sortie.replace(e(mot), '<span class="s-{}">{}</span>'.format(couleur, e(mot)), 1)
    return sortie


def gras(texte, mots):
    for mot in mots or []:
        if e(mot) not in texte:
            sys.exit("Mot à mettre en gras introuvable dans le texte : {}".format(mot))
        texte = texte.replace(e(mot), "<b>{}</b>".format(e(mot)), 1)
    return texte


def paragraphes(liste, mot=None, couleur="jaune"):
    return "".join("<p>{}</p>".format(surligner(p, mot if mot and mot in p else None, couleur)) for p in liste)


def fleche(texte):
    if texte is None:
        return ""
    return ('<div class="fleche">{}<svg viewBox="0 0 112 18"><path d="M0 9h110M101 2l9 7-9 7" fill="none" '
            'stroke="currentColor" stroke-width="1.8"/></svg></div>').format(e(texte) or "&nbsp;")


def theme_papier(s):
    return "sombre" if s.get("theme") == "sombre" else "clair"


def couleur_surlignage(theme):
    return "bleu" if theme in ("sombre", "noir") else "jaune"


def image(s, position):
    if not s.get("image"):
        return ""
    classes = "j-img" + (" haut" if position == "haut" else "") + (" fondu" if s.get("fondu") else "")
    return '<img class="{}" src="{}">'.format(classes, Path(s["image"]).expanduser().resolve().as_uri())


def image_alignee(s):
    return bool(s.get("image")) and s.get("image_position", "haut") == "haut"


def couverture(s, m):
    theme = theme_papier(s)
    return ('<div class="slide journal {}">{}<div class="j-titre" data-mesure data-ajuste>{}</div>{}{}{}</div>').format(
        theme + (" couv" if s.get("image_position", "bas") == "bas" else ""), PAPIER, surligner(s["titre"], s.get("surligne"), couleur_surlignage(theme)),
        '<div class="j-sous" data-mesure>{}</div>'.format(e(s["sous_titre"])) if s.get("sous_titre") else "",
        image(s, s.get("image_position", "bas")), fleche(s.get("fleche")))


def texte_image(s, m):
    theme = theme_papier(s)
    return '<div class="slide journal {}">{}{}<div class="j-texte" data-mesure data-corps>{}</div>{}{}</div>'.format(
        theme + (" aligne" if image_alignee(s) else ""), PAPIER, "", paragraphes(s["paragraphes"], s.get("surligne"), couleur_surlignage(theme)),
        image(s, s.get("image_position", "haut")), fleche(s.get("fleche")))


def texte(s, m):
    theme = theme_papier(s)
    return '<div class="slide texte {}">{}<div class="x-titre" data-mesure>{}</div><div class="x-texte" data-mesure>{}</div></div>'.format(
        theme, PAPIER, gras(surligner(s["titre"], s.get("surligne"), couleur_surlignage(theme)), s.get("gras")),
        paragraphes(s.get("paragraphes", [])))


def tweet(s, m):
    avatar = ('<img class="t-avatar" src="{}">'.format(Path(m["photo"]).expanduser().resolve().as_uri()) if m.get("photo")
              else '<div class="t-avatar">{}</div>'.format(e(m.get("initiales", ""))))
    stats = ""
    if s.get("interactions"):
        stats = '<div class="t-stats">' + "".join(
            "<span>{} {}</span>".format(e(n), e(str(v))) for n, v in s["interactions"].items()) + "</div>"
    return ('<div class="slide tweet {}"><div class="t-tete">{}<div><div class="t-nom">{}{}</div><div class="t-pseudo">{}</div></div></div>'
            '<div class="t-texte" data-mesure>{}</div>{}</div>').format(
        s.get("theme", "noir"), avatar, e(m["nom"]), CHECK if m.get("coche") else "", e(m.get("pseudo", "")),
        paragraphes(s["paragraphes"]), stats)


def punchline(s, m):
    theme = s.get("theme", "blanc")
    return '<div class="slide punch {}"><div class="p-texte" data-mesure>{}</div><div class="p-pseudo">{}</div></div>'.format(
        theme, paragraphes(s["paragraphes"], s.get("surligne"), couleur_surlignage(theme)), e(m.get("pseudo", "")))


STYLES = {"texte-image-couverture": couverture, "texte-image": texte_image,
          "texte": texte, "punchline": punchline, "tweet": tweet}

AJUSTE = """(r) => {
  const utile = 1350 - 140, ecart = 36;
  const img = document.querySelector('.j-img');
  const titre = document.querySelector('[data-ajuste]');
  const corps = document.querySelector('[data-corps]');
  if (titre) {
    const sous = document.querySelector('.j-sous');
    const mini = img ? 340 : 0;
    const espace = r.titre_haut && document.querySelector('.couv') ? (r.couverture_image_bas || 1170) - r.titre_haut : utile;
    const tailles = r.titre_tailles || [133.33, 128, 122, 116, 110, 104, 98, 92, 86];
    const mesurer = () => titre.getBoundingClientRect().height + (sous ? sous.getBoundingClientRect().height + 8 : 0);
    for (const taille of tailles) {
      titre.style.fontSize = taille + 'px';
      const h = mesurer();
      const lignes = Math.round(titre.getBoundingClientRect().height / parseFloat(getComputedStyle(titre).lineHeight));
      if (titre.scrollWidth <= titre.clientWidth + 1 && (!r.titre_lignes_max || lignes <= r.titre_lignes_max)
          && h + (img ? ecart : 0) + mini <= espace) {
        if (img) img.style.height = Math.min(espace - h - ecart, r.couverture_image_max || 520) + 'px';
        return taille;
      }
    }
    if (img && r.titre_tailles) img.style.height = Math.max(espace - mesurer() - ecart, 180) + 'px';
    return tailles[tailles.length - 1];
  }
  if (corps && img && !(r.image_hauteur && document.querySelector('.aligne'))) {
    img.style.height = Math.max(Math.min(utile - corps.getBoundingClientRect().height - ecart - 60, 390), 180) + 'px';
  }
  return null;
}"""

MESURE = """() => [...document.querySelectorAll('[data-mesure]')].map(el => {
  const r = el.getBoundingClientRect();
  return {g: r.left, d: r.right, h: r.top, b: r.bottom};
})"""


def polices_marque(marque, dossier):
    """Déclare les polices propres à une marque. Sans police propre, Poppins est utilisée."""
    famille = marque.get("police", "Poppins")
    css = ""
    if famille != "Poppins":
        for p in marque.get("polices", []):
            chemin = (dossier / p["fichier"]).resolve()
            if not chemin.is_file():
                sys.exit("Police introuvable : {}".format(chemin))
            css += "@font-face{{font-family:'{}';src:url('{}');font-weight:{};font-style:{}}}".format(
                famille, chemin.as_uri(), p.get("graisse", "400"), p.get("style", "normal"))
    return css + ":root{{--police:'{}',Poppins}}".format(famille)


TYPOGRAPHIE = {"couverture_titre": ".j-titre", "couverture_sous_titre": ".j-sous", "texte_image": ".j-texte",
               "texte_titre": ".x-titre", "texte_sous_titre": ".x-texte", "punchline": ".p-texte", "pseudo": ".p-pseudo"}


def css_typographie(r):
    """Tailles et graisses réglées par la personne. Sans réglage, le moteur garde ses valeurs."""
    css = ""
    for cle, selecteur in TYPOGRAPHIE.items():
        v = r.get(cle, {})
        regles = []
        if v.get("taille"):
            regles.append("font-size:{}px".format(v["taille"]))
        if v.get("graisse"):
            regles.append("font-weight:{}".format(v["graisse"]))
        if v.get("interligne"):
            regles.append("line-height:{}".format(v["interligne"]))
        if v.get("approche") is not None:
            regles.append("letter-spacing:{}em".format(v["approche"]))
        if regles:
            css += "{}{{{}}}".format(selecteur, ";".join(regles))
    return css


def css_marque(marque):
    c = dict(COULEURS_DEFAUT, **marque.get("couleurs", {}))
    return (":root{{--papier:{papier};--papier-sombre:{papier_sombre};--texte:{texte};--texte-clair:{texte_clair};"
            "--jaune:{surlignage_clair};--bleu:{surlignage_sombre}}}").format(**c)


def css_tweet(r):
    """Réglages du style Tweet enregistrés dans la marque. Sans réglages, rien ne change."""
    css = ""
    if r.get("nom_taille"):
        css += ".t-nom{{font-size:{0}px}}.check{{width:{1}px;height:{1}px}}".format(r["nom_taille"], round(r["nom_taille"] * .88))
    if r.get("pseudo_taille"):
        css += ".t-pseudo{{font-size:{}px}}".format(r["pseudo_taille"])
    if r.get("texte_taille"):
        css += ".t-texte{{font-size:{}px}}".format(r["texte_taille"])
    if r.get("texte_interligne"):
        css += ".t-texte{{line-height:{}}}".format(r["texte_interligne"])
    return css


def css_reglages(r):
    """Traduit les réglages enregistrés dans la marque. Sans réglages, rien ne change."""
    css = ""
    if r.get("titre_haut"):
        css += ".journal.couv{{justify-content:flex-start;padding-top:{}px}}".format(r["titre_haut"])
    if r.get("titre_lignes_max"):
        css += ".j-titre{text-wrap:balance}"
    if r.get("titre_interligne"):
        css += ".j-titre{{line-height:{}}}".format(r["titre_interligne"])
    if r.get("image_hauteur"):
        css += (".journal.aligne{{justify-content:flex-start;padding-top:{}px}}"
                ".aligne .j-img.haut{{height:{}px;margin-bottom:{}px}}").format(
            r.get("image_haut", 150), r["image_hauteur"], r.get("image_ecart", 40))
    return css


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    donnees = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    marque = donnees.get("marque")
    dossier_marque = Path(sys.argv[1]).expanduser().resolve().parent
    if donnees.get("marque_fichier"):
        fichier_marque = Path(donnees["marque_fichier"]).expanduser().resolve()
        marque = json.loads(fichier_marque.read_text(encoding="utf-8"))
        dossier_marque = fichier_marque.parent
    global PAPIER
    PAPIER = PAPIER_TEXTURE if marque.get("fond_papier", True) else FILTRE_SEUL
    sortie = Path(sys.argv[2]).expanduser().resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    erreurs, fichiers = [], []
    reglages = marque.get("reglages", {}).get("texte-image", {})
    entete = (POLICES + polices_marque(marque, dossier_marque) + css_marque(marque) + CSS + css_reglages(reglages)
              + css_tweet(marque.get("reglages", {}).get("tweet", {}))
              + css_typographie(marque.get("reglages", {}).get("typographie", {})))

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        page = navigateur.new_page(viewport={"width": LARGEUR, "height": HAUTEUR})
        for numero, slide in enumerate(donnees["slides"], 1):
            contenu = STYLES[slide["style"]](slide, marque)
            fichier_html = sortie / ".slide.html"
            fichier_html.write_text("<!doctype html><meta charset=utf-8><style>{}</style>{}".format(entete, contenu),
                                    encoding="utf-8")
            page.goto(fichier_html.as_uri())
            page.evaluate("document.fonts.ready")
            page.wait_for_load_state("networkidle")
            page.evaluate("Promise.all([...document.images].map(i => i.decode()))")
            taille = page.evaluate(AJUSTE, reglages)
            if taille and taille < (reglages.get("titre_tailles") or [133])[0]:
                print("Slide {} : titre long, taille réduite à {} px".format(numero, taille))
            bas_max = HAUTEUR - MARGE_Y
            if slide["style"] == "texte-image" and image_alignee(slide) and reglages.get("image_hauteur"):
                bas_max = reglages.get("texte_bas_max", 1195)
            for boite in page.evaluate(MESURE):
                if (boite["g"] < MARGE_X or boite["d"] > LARGEUR - MARGE_X
                        or boite["h"] < MARGE_Y or boite["b"] > bas_max):
                    erreurs.append("Slide {} : le texte déborde ({})".format(numero, boite))
            image_capturee = Image.open(io.BytesIO(page.screenshot(type="png"))).convert("RGB")
            jpeg = sortie / "slide-{:02d}.jpg".format(numero)
            image_capturee.save(jpeg, format="JPEG", quality=QUALITE_JPEG, subsampling=0, optimize=True)
            fichiers.append(jpeg)
        fichier_html.unlink()
        navigateur.close()

    colonnes = min(5, len(fichiers))
    lignes = (len(fichiers) + colonnes - 1) // colonnes
    largeur, hauteur, ecart = 400, 500, 16
    planche = Image.new("RGB", (colonnes * (largeur + ecart) + ecart, lignes * (hauteur + ecart) + ecart), "#777")
    for i, png in enumerate(fichiers):
        planche.paste(Image.open(png).convert("RGB").resize((largeur, hauteur), Image.LANCZOS),
                      (ecart + (i % colonnes) * (largeur + ecart), ecart + (i // colonnes) * (hauteur + ecart)))
    dossier_travail = sortie.parent / "travail"
    planche.save((dossier_travail if dossier_travail.is_dir() else sortie) / "planche.jpg", quality=90)

    if erreurs:
        print("\n".join(erreurs))
        sys.exit(1)
    print("{} slides fabriquées dans {}".format(len(fichiers), sortie))


if __name__ == "__main__":
    main()

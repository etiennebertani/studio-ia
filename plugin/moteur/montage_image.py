"""Ce qui se voit : position de la tête, titre, images, sous-titres."""
import re
import statistics

import cv2
import pillow_heif
from PIL import Image, ImageDraw, ImageFont, ImageOps


pillow_heif.register_heif_opener()
L, H = 1080, 1920
X = 3
BAS_UTILE = 1484
DROITE_UTILE = 1018
GAUCHE_UTILE = 58
HAUT_ENGAGEMENT = 907


def position_tete(rushes, instants):
    """Regarde les images données ([(rush, temps, pendant_le_titre)]) et renvoie le haut de la tête et le menton."""
    fichiers = {}
    face = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    profil = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    hauts, mentons = [], []
    for rush, temps, pendant_titre in instants:
        lecteur = fichiers.setdefault(rush, cv2.VideoCapture(str(rushes[rush])))
        lecteur.set(cv2.CAP_PROP_POS_MSEC, temps * 1000)
        ok, image = lecteur.read()
        if not ok:
            continue
        echelle = max(L / image.shape[1], H / image.shape[0])
        taille = (round(image.shape[1] * echelle), round(image.shape[0] * echelle))
        decalage_x, decalage_y = (taille[0] - L) // 2, (taille[1] - H) // 2
        gris = cv2.cvtColor(cv2.resize(image, taille), cv2.COLOR_BGR2GRAY)[decalage_y:decalage_y + H, decalage_x:decalage_x + L]
        boites = [*face.detectMultiScale(gris, 1.1, 6, minSize=(180, 180)),
                  *profil.detectMultiScale(gris, 1.1, 6, minSize=(180, 180))]
        if len(boites) == 0:
            continue
        _, y, _, hauteur = max(boites, key=lambda b: b[2] * b[3])
        mentons.append(y + hauteur * 1.02)
        if pendant_titre:
            hauts.append(y - 0.22 * hauteur)
    for lecteur in fichiers.values():
        lecteur.release()

    def sans_erreurs(valeurs):
        if not valeurs:
            return []
        milieu = statistics.median(valeurs)
        return [v for v in valeurs if abs(v - milieu) <= 150]

    hauts, mentons = sans_erreurs(hauts), sans_erreurs(mentons)
    return {"haut": int(min(hauts)) if hauts else None, "menton": int(max(mentons)) if mentons else None, "vues": len(mentons)}


def separer_titre(texte):
    """« mon titre (deuxième ligne) » : la parenthèse devient l'encadré noir."""
    trouve = re.match(r"^(.*?)\s*\(([^()]+)\)\s*$", texte.strip())
    return (trouve.group(1), trouve.group(2)) if trouve else (texte.strip(), None)


def _lignes(texte, police, largeur):
    def couper(limite):
        sortie, courant = [], ""
        for mot in texte.split(" "):
            essai = (courant + " " + mot).strip()
            if courant and police.getlength(essai) > limite:
                sortie.append(courant)
                courant = mot
            else:
                courant = essai
        return sortie + [courant]

    nombre = len(couper(largeur))
    bas, haut = largeur * 0.3, largeur
    for _ in range(24):
        milieu = (bas + haut) / 2
        if len(couper(milieu)) <= nombre:
            haut = milieu
        else:
            bas = milieu
    return couper(haut)


def dessiner_titre(texte, r, police, place, sortie):
    """Dessine le titre, réduit par paliers jusqu'à tenir dans la place disponible."""
    blanc, noir = separer_titre(texte)
    blanc = re.sub(r" ([?!:;»])", "\u00a0\\1", blanc).replace("« ", "«\u00a0")
    fixe = r.get("echelle_fixe")
    echelle = fixe or 1.0
    while True:
        e = echelle * X
        fonte = ImageFont.truetype(str(police), round(r["taille"] * e))
        pad_x, pad_y, pas = r["pad_x"] * e, r["pad_y"] * e, r["interligne"] * e
        for largeur_cadre in (r["largeur_max"], r["largeur_etendue"]):
            lignes = _lignes(blanc, fonte, largeur_cadre * X - 2 * pad_x)
            h_blanc = len(lignes) * pas + 2 * pad_y
            h_noir = (r["noir_interligne"] + 2 * r["noir_pad_y"]) * e if noir else 0
            total = h_blanc + (h_noir - r["noir_chevauchement"] * e if noir else 0)
            if total / X <= place:
                break
        if total / X <= place or fixe or echelle <= r["echelle_min"]:
            break
        echelle = round(echelle - 0.02, 2)
    image = Image.new("RGBA", (L * X, int(total)), (0, 0, 0, 0))
    dessin = ImageDraw.Draw(image)
    centre = L * X / 2
    largeur = max(fonte.getlength(l) for l in lignes) + 2 * pad_x
    rayon = r["rayon"] * e
    dessin.rounded_rectangle((centre - largeur / 2, 0, centre + largeur / 2, h_blanc), radius=rayon, fill="#FFFFFF")
    y = pad_y
    for ligne in lignes:
        dessin.text((centre, y + pas / 2), ligne, font=fonte, fill="#000000", anchor="mm")
        y += pas
    if noir:
        fonte_noir = ImageFont.truetype(str(police), round(r["noir_taille"] * e))
        largeur_noir = fonte_noir.getlength(noir) + 2 * r["noir_pad_x"] * e
        haut_noir = h_blanc - r["noir_chevauchement"] * e
        dessin.rounded_rectangle((centre - largeur_noir / 2, haut_noir, centre + largeur_noir / 2, haut_noir + h_noir),
                                 radius=rayon, fill="#000000")
        dessin.text((centre, haut_noir + h_noir / 2), noir, font=fonte_noir, fill="#FFFFFF", anchor="mm")
    image.resize((L, int(total / X)), Image.LANCZOS).save(sortie)
    return {"hauteur": int(total / X), "echelle": echelle, "lignes": lignes, "cache_la_tete": total / X > place}


def dessiner_image(source, r, sortie, hauteur_max=None):
    """Une petite image dans un cadre blanc aux coins arrondis. Renvoie (largeur, hauteur)."""
    limite_h = min(r["hauteur_max"], hauteur_max or r["hauteur_max"])
    photo = ImageOps.exif_transpose(Image.open(source)).convert("RGBA")
    pad = r["pad"]
    rapport = min((r["largeur_max"] - 2 * pad) / photo.width, (limite_h - 2 * pad) / photo.height)
    photo = photo.resize((round(photo.width * rapport), round(photo.height * rapport)), Image.LANCZOS)
    w, h = photo.width + 2 * pad, photo.height + 2 * pad
    grand = Image.new("RGBA", (w * X, h * X), (0, 0, 0, 0))
    ImageDraw.Draw(grand).rounded_rectangle((0, 0, w * X - 1, h * X - 1), radius=r["rayon"] * X, fill="#FFFFFF")
    carte = grand.resize((w, h), Image.LANCZOS)
    carte.alpha_composite(photo, (pad, pad))
    carte.save(sortie)
    return w, h


def place_image(hauteur, tete, y_sous_titres, y_haut, r):
    """Choisit où poser l'image : au-dessus de la tête, sinon en bas, sinon à côté de la tête.

    Renvoie (endroit, hauteur maximale), ou None si aucune place n'est assez grande pour qu'on voie l'image.
    """
    dessus = tete["haut"] - y_haut - 2 * r["marge"] if tete["haut"] is not None else 0
    bas = BAS_UTILE - (y_sous_titres + r["ecart_sous_titres"])
    if dessus >= hauteur:
        return "dessus", hauteur
    if bas >= hauteur:
        return "bas", hauteur
    endroit, place = ("dessus", dessus) if dessus >= bas else ("bas", bas)
    if place >= r["hauteur_min"]:
        return endroit, place
    if tete["haut"] is not None:
        return "cote", min(hauteur, r["hauteur_cote"], HAUT_ENGAGEMENT - tete["haut"])
    return None


def _temps_ass(t):
    t = max(0, t)
    return "{}:{:02d}:{:05.2f}".format(int(t // 3600), int(t % 3600 // 60), t % 60)


def _couleur(hexa):
    h = hexa.lstrip("#")
    return "&H00{}{}{}".format(h[4:6], h[2:4], h[0:2]).upper()


def blocs_sous_titres(mots, nombre, fonte=None, largeur_max=None):
    """Blocs de sous-titres : au plus `nombre` mots, coupés en fin de phrase et sur les blancs. Avec une fonte et une
    largeur maximale, un bloc ne dépasse jamais cette largeur (les icônes d'Instagram commencent à x 839)."""
    blocs, courant = [], []
    for i, mot in enumerate(mots):
        if fonte is not None and largeur_max and courant and \
                fonte.getlength(" ".join(m["w"].rstrip(".,;:") for m in courant + [mot])) > largeur_max:
            blocs.append(courant)
            courant = []
        courant.append(mot)
        fin_phrase = mot["w"][-1:] in ".?!,;:"
        trou = i + 1 < len(mots) and mots[i + 1]["s"] - mot["e"] > 0.45
        long = sum(len(m["w"]) + 1 for m in courant) > 20
        if len(courant) >= nombre or fin_phrase or trou or long:
            blocs.append(courant)
            courant = []
    if courant:
        blocs.append(courant)
    return blocs


def ecrire_sous_titres(mots, r, police, y, total, sortie):
    """Écrit le fichier de sous-titres. Le nom de la police est lu dans son fichier."""
    famille, graisse = ImageFont.truetype(str(police), 20).getname()
    gras = -1 if "bold" in (graisse or "").lower() else 0
    couleur = _couleur(r["couleur"])
    lignes = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {L}", f"PlayResY: {H}", "WrapStyle: 2",
              "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              f"Style: Sous,{famille},{r['taille']},{couleur},{couleur},&H00000000,&H80000000,{gras},0,0,0,100,100,0,0,1,0,{r['ombre']},5,60,60,0,1",
              "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    fonte = ImageFont.truetype(str(police), r["taille"])
    blocs = blocs_sous_titres(mots, r["mots_par_bloc"], fonte, r.get("largeur_max"))
    for i, bloc in enumerate(blocs):
        fin = min(bloc[-1]["e"] + 0.25, blocs[i + 1][0]["s"] if i + 1 < len(blocs) else total)
        texte = " ".join(m["w"].rstrip(".,;:") for m in bloc).replace("{", "(").replace("}", ")")
        texte = re.sub(r" ([?!:;»])", r"\\h\1", texte)
        lignes.append("Dialogue: 1,{},{},Sous,,0,0,0,,{{\\an5\\pos({},{})}}{}".format(
            _temps_ass(bloc[0]["s"]), _temps_ass(fin), L // 2, y, texte))
    sortie.write_text("\n".join(lignes) + "\n", encoding="utf-8")

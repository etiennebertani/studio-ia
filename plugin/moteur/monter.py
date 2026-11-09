"""Le montage du Studio. À lancer avec le Python du moteur.

    monter.py styles
    monter.py reglages --marque <dossier de marque>
    monter.py analyser --dossier <contenu> --style yap --marque <marque> --rush <fichier> [--rush <fichier>]
    monter.py couper   --dossier <contenu>
    monter.py rendre   --dossier <contenu>
    monter.py controler --dossier <contenu>
    monter.py valider  --dossier <contenu> [--aussi-sans-illustrations]
    monter.py affiner  --dossier <contenu> [--debut <mot> "<texte>"] [--fin <mot> "<texte>"]
    monter.py essai    --dossier <contenu> --numero 2
    monter.py exemple  --dossier <contenu> [--note "..."]
    monter.py matiere  --dossier <contenu> [--depuis <dossier>] [--cherche "mots"]

Les règles de base sont dans ressources/montage-base.json. La personnalisation est dans
00. Branding/<marque>/montage.json. Les choix d'une vidéo sont dans travail/plan.json.
"""
import argparse
import copy
import datetime
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

import commun
import montage_image as visuel
import nommage
import montage_son as son

BASE = commun.RACINE_PLUGIN / "ressources" / "montage-base.json"
POLICES = commun.RACINE_PLUGIN / "moteur" / "polices"
TONEMAP = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv"
L, H, FPS = 1080, 1920, son.FPS
EXT_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
EXT_VIDEOS = {".mp4", ".mov", ".m4v"}
MATIERE_MAX = 24


def lire(chemin):
    return json.loads(Path(chemin).read_text(encoding="utf-8"))


def ecrire(chemin, valeur):
    Path(chemin).write_text(json.dumps(valeur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def repondre(**valeurs):
    print(json.dumps(valeurs, ensure_ascii=False, indent=1))


def fusionner(base, ajout):
    sortie = copy.deepcopy(base)
    for cle, valeur in (ajout or {}).items():
        if isinstance(valeur, dict) and isinstance(sortie.get(cle), dict):
            sortie[cle] = fusionner(sortie[cle], valeur)
        else:
            sortie[cle] = valeur
    return sortie


def dossier_marque(marque):
    return commun.ESPACE / commun.NOMS["branding"] / marque


def reglages(marque, style=None, ajustements=None):
    """Base, puis personnalisation de la marque, puis ajustements de cette vidéo."""
    base = lire(BASE)
    fichier = dossier_marque(marque) / "montage.json"
    perso = lire(fichier) if fichier.is_file() else {}
    r = fusionner({c: v for c, v in base.items() if c not in ("styles", "_note")},
                  {c: v for c, v in perso.items() if c != "styles"})
    if style:
        fiche = next(s for s in base["styles"] if s["id"] == style)
        r["blanc_max"] = (perso.get("styles") or {}).get(style, {}).get("blanc_max", fiche["blanc_max"])
        r["habillage"] = fiche["habillage"]
        r["regles"] = fusionner(r["regles"], fiche.get("regles"))
    return fusionner(r, ajustements)


def police_de(marque, nom, alertes):
    for dossier in (dossier_marque(marque) / "polices", POLICES):
        if (dossier / nom).is_file():
            return dossier / nom
    alertes.append(f"Police {nom} introuvable : Poppins à la place.")
    return POLICES / "Poppins-Bold.ttf"


def sonde(source):
    sortie = subprocess.run([commun.outil("ffprobe"), "-v", "error", "-show_entries",
                             "stream=codec_type,color_transfer,width,height:format=duration", "-of", "json", str(source)],
                            capture_output=True, text=True, check=True).stdout
    infos = json.loads(sortie)
    video = next((s for s in infos["streams"] if s["codec_type"] == "video"), {})
    return {"duree": float(infos["format"]["duration"]), "largeur": video.get("width"), "hauteur": video.get("height"),
            "hdr": video.get("color_transfer") in ("smpte2084", "arib-std-b67"),
            "son": any(s["codec_type"] == "audio" for s in infos["streams"])}


def texte_lisible(mots, retraits):
    """Une ligne par phrase, chaque mot avec son numéro. Les mots proposés au retrait sont entre crochets."""
    lignes, ligne, debut = [], [], None
    for i, mot in enumerate(mots):
        debut = mot["s"] if debut is None else debut
        ligne.append(f"{i}:[{mot['w']}]" if i in retraits else f"{i}:{mot['w']}")
        if mot["w"][-1:] in ".?!" or len(ligne) >= 14:
            lignes.append(f"[{debut:7.2f} → {mot['e']:7.2f}] " + " ".join(ligne))
            ligne, debut = [], None
    if ligne:
        lignes.append(f"[{debut:7.2f}] " + " ".join(ligne))
    return "\n".join(lignes) + "\n"


def cmd_styles(_):
    repondre(styles=[{c: s[c] for c in ("id", "nom", "pour", "disponible", "habillage", "prerequis")} for s in lire(BASE)["styles"]])


def cmd_reglages(args):
    print(json.dumps(reglages(args.marque), ensure_ascii=False, indent=1))


def cmd_analyser(args):
    dossier = Path(args.dossier).resolve()
    travail = dossier / "travail"
    travail.mkdir(parents=True, exist_ok=True)
    (dossier / "final").mkdir(exist_ok=True)
    fiche = next((s for s in lire(BASE)["styles"] if s["id"] == args.style), None)
    if not fiche or not fiche["disponible"]:
        raise SystemExit(f"Le style {args.style} n'est pas encore disponible.")
    r = reglages(args.marque, args.style)
    if r["habillage"]:
        (dossier / "images").mkdir(exist_ok=True)
        (dossier / "b-roll").mkdir(exist_ok=True)
    rushes = [str(Path(x).expanduser().resolve()) for x in args.rush]
    for rush in rushes:
        if not Path(rush).is_file():
            raise SystemExit(f"Vidéo introuvable : {rush}")
    mots, infos, voix_rushes = [], [], []
    for rang, rush in enumerate(rushes):
        info = sonde(rush)
        if not info["son"]:
            raise SystemExit(f"Cette vidéo n'a pas de son : {Path(rush).name}")
        infos.append(info)
        voix = son.Voix(rush)
        voix_rushes.append(voix)
        trouves = son.reparer_mots(son.transcrire(rush, r["regles"]["invite_transcription"], args.langue, voix.prises()), voix)
        mots += [{**m, "r": rang} for m in trouves]
    if not mots:
        raise SystemExit("Aucune parole trouvée dans cette vidéo.")
    retraits = son.proposer_retraits(mots, r["regles"])
    ecrire(travail / "projet.json", {"style": args.style, "marque": args.marque, "rushes": rushes, "langue": args.langue})
    ecrire(travail / "mots.json", mots)
    (travail / "transcription.txt").write_text(texte_lisible(mots, retraits), encoding="utf-8")
    plan = travail / "plan.json"
    if not plan.exists() or args.remplacer:
        ecrire(plan, {"passages": son.passages_depuis(mots, retraits), "titre": "", "images": [], "plans_de_coupe": [],
                      "corrections": {}, "ajustements": {}})
    repondre(mots=len(mots), retraits_proposes={str(k): {"mot": mots[k]["w"], "raison": v} for k, v in sorted(retraits.items())},
             reprises_probables=son.proposer_reprises(mots, voix_rushes, r["regles"]),
             rushes=[{"nom": Path(x).name, **i} for x, i in zip(rushes, infos)],
             transcription=str(travail / "transcription.txt"), plan=str(plan))


def dossier_essai(travail, essai):
    return travail / f"essai-{essai:02d}" if essai and essai > 1 else travail


def charger(dossier, essai=None):
    dossier = Path(dossier).resolve()
    travail = dossier_essai(dossier / "travail", essai)
    if not (travail / "projet.json").is_file():
        raise SystemExit("Lance d'abord l'analyse de ce contenu.")
    projet, plan = lire(travail / "projet.json"), lire(travail / "plan.json")
    r = reglages(projet["marque"], projet["style"], plan.get("ajustements"))
    return dossier, travail, projet, plan, lire(travail / "mots.json"), r


def controler_plan(plan, mots):
    passages = plan["passages"]
    for i, j in passages:
        if not 0 <= i <= j < len(mots):
            raise SystemExit(f"Passage impossible dans plan.json : {i} à {j}.")
    decoupes = []
    for i, j in passages:
        debut = i
        for k in range(i + 1, j + 1):
            if mots[k]["r"] != mots[debut]["r"]:
                decoupes.append([debut, k - 1])
                debut = k
        decoupes.append([debut, j])
    return decoupes


def cmd_couper(args):
    _, travail, projet, plan, mots, r = charger(args.dossier, args.essai)
    passages = controler_plan(plan, mots)
    voix = [son.Voix(x) for x in projet["rushes"]]
    for rang, v in enumerate(voix):
        v.recaler([(mots[i]["s"], mots[j]["e"]) for i, j in passages if mots[i]["r"] == rang])
    plans = son.couper(mots, voix, passages, r["regles"], r["blanc_max"])
    garde = sorted({k for i, j in passages for k in range(i, j + 1)})
    enleve = [i for i in range(len(mots)) if i not in set(garde)]
    avant = sum(sonde(x)["duree"] for x in projet["rushes"])
    apres = sum(son.duree_plan(p) for p in plans)
    ecrire(travail / "montage.json", {"plans": plans, "passages": passages})
    corrections = plan.get("corrections") or {}
    ordre = [corrections.get(str(k), mots[k]["w"]) for i, j in passages for k in range(i, j + 1)]
    repondre(plans=len(plans), avant=round(avant, 1), apres=round(apres, 1), texte_garde=" ".join(ordre),
             mots_enleves=" ".join(mots[i]["w"] for i in enleve))


def clip_plan(projet, plan, cache):
    source = Path(projet["rushes"][plan["r"]])
    info = sonde(source)
    duree = son.duree_plan(plan)
    cle = hashlib.md5(json.dumps([str(source), source.stat().st_mtime, plan["debut"], duree]).encode()).hexdigest()[:12]
    sortie = cache / f"plan-{cle}.mkv"
    if sortie.exists():
        return sortie
    filtre_video = (TONEMAP + "," if info["hdr"] else "") + \
        f"fps={FPS}:start_time=0,scale={L}:{H}:force_original_aspect_ratio=increase,crop={L}:{H},setsar=1,format=yuv420p"
    filtre_son = (f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{duree:.4f},afade=t=in:d=0.008,"
                  f"afade=t=out:st={max(0, duree - 0.012):.4f}:d=0.012")
    son.lancer([son.ffmpeg(), "-y", "-v", "error", "-ss", f"{plan['debut']:.3f}", "-i", source, "-filter_complex",
                f"[0:v:0]{filtre_video}[v];[0:a:0]{filtre_son}[a]", "-map", "[v]", "-map", "[a]",
                "-frames:v", round(duree * FPS), "-t", f"{duree:.4f}", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", 14, "-g", FPS, "-c:a", "pcm_s16le", sortie])
    return sortie


def clip_coupe(dossier, element, cache, duree):
    source = chemin_fichier(dossier, element["fichier"])
    info = sonde(source)
    depart = float(element.get("debut_source", 0))
    if depart + duree > info["duree"]:
        raise SystemExit(f"Ce b-roll est trop court : {source.name}.")
    cle = hashlib.md5(json.dumps([str(source), source.stat().st_mtime, depart, duree, "lanczos"]).encode()).hexdigest()[:12]
    sortie = cache / f"coupe-{cle}.mkv"
    if not sortie.exists():
        filtre = (TONEMAP + "," if info["hdr"] else "") + \
            f"fps={FPS},scale={L}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={L}:{H},setsar=1,format=yuv420p"
        son.lancer([son.ffmpeg(), "-y", "-v", "error", "-ss", f"{depart:.3f}", "-t", f"{duree:.3f}", "-i", source, "-an",
                    "-vf", filtre, "-c:v", "libx264", "-preset", "veryfast", "-crf", 14, sortie])
    return sortie


def chemin_fichier(dossier, nom):
    chemin = Path(nom).expanduser()
    chemin = chemin if chemin.is_absolute() else dossier / chemin
    if not chemin.is_file():
        raise SystemExit(f"Fichier introuvable : {nom}")
    return chemin


def instants_tete(plans, duree_titre):
    instants, temps = [], 0.0
    total = sum(son.duree_plan(p) for p in plans)
    for plan in plans:
        duree = son.duree_plan(plan)
        pas, t = 0.15, 0.0
        while t < duree:
            pendant = temps + t <= duree_titre or temps + t >= total - 3.5
            if pendant or t == 0.0:
                instants.append((plan["r"], plan["debut"] + (t or min(0.1, duree / 2)), pendant))
            t = t + pas
        temps += duree
    return instants


def duree_element(element, finaux, defaut):
    """La durée d'une illustration : jusqu'à un mot précis si demandé, sinon sa durée propre."""
    if "jusqu_au_mot" in element:
        return round(finaux[int(element["jusqu_au_mot"])]["s"] - finaux[int(element["mot"])]["s"], 3)
    return float(element.get("duree", defaut))


def verifier_illustrations(images, coupes, finaux, total, r):
    """Refuse ce qui ne respecte pas les règles : mot retiré, durée, chevauchement, fin de vidéo."""
    creneaux = []
    for nature, liste, defaut in (("image", images, r["images"]["duree"]), ("b-roll", coupes, r["plans_de_coupe"]["duree"])):
        for element in liste:
            if int(element["mot"]) not in finaux:
                raise SystemExit(f"Une {nature} est placée sur un mot retiré : {element['mot']}.")
            debut = finaux[int(element["mot"])]["s"]
            duree = duree_element(element, finaux, defaut)
            if nature == "b-roll" and not r["plans_de_coupe"]["duree_min"] <= duree <= r["plans_de_coupe"]["duree_max"]:
                raise SystemExit(f"Un b-roll doit durer de {r['plans_de_coupe']['duree_min']} à {r['plans_de_coupe']['duree_max']} secondes (ici {duree:.1f}).")
            if debut + duree > total:
                raise SystemExit(f"Une {nature} dépasse la fin de la vidéo.")
            creneaux.append((debut, debut + duree))
    creneaux.sort()
    if any(b[0] < a[1] - 0.01 for a, b in zip(creneaux, creneaux[1:])):
        raise SystemExit("Deux illustrations se chevauchent : il faut les espacer.")


def fabriquer(dossier, travail, projet, plan, mots, r, sortie, avec_sous_titres=True, illustrations=True):
    """Assemble la vidéo et renvoie ce qui a été décidé pour la contrôler."""
    montage = lire(travail / "montage.json")
    plans, passages = montage["plans"], montage["passages"]
    alertes = []
    rendu = travail / "rendu"
    cache = rendu / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    liste, total = [], 0.0
    for p in plans:
        duree = son.duree_plan(p)
        liste += [f"file '{clip_plan(projet, p, cache).name}'", f"duration {duree:.6f}"]
        total += duree
    (cache / "liste.txt").write_text("\n".join(liste) + "\n", encoding="utf-8")

    finaux = son.mots_finaux(mots, passages, plans, plan.get("corrections") or {})
    images, coupes = plan.get("images") or [], plan.get("plans_de_coupe") or []
    if (images or coupes) and not r["habillage"]:
        raise SystemExit("Ce style reste sans image ni b-roll : choisis Yap+.")
    if not illustrations:
        images, coupes = [], []
    verifier_illustrations(images, coupes, finaux, total, r)
    tete = visuel.position_tete(projet["rushes"], instants_tete(plans, r["titre"]["duree"]))
    if tete["vues"] == 0:
        alertes.append("Visage non repéré : le hook text et les sous-titres sont placés par défaut. À vérifier à l'œil.")
    st = r["sous_titres"]
    y_st = min(tete["menton"] + st["ecart_menton"], st["y_max"]) if tete["menton"] else st["y_defaut"]

    commande = [son.ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", cache / "liste.txt"]
    filtres, etiquette, entree = [], "[0:v]", 1
    for rang, element in enumerate(coupes):
        if int(element["mot"]) not in finaux:
            raise SystemExit(f"Plan de coupe placé sur un mot retiré : {element['mot']}.")
        debut = finaux[int(element["mot"])]["s"]
        if debut < r["plans_de_coupe"]["debut_min"]:
            raise SystemExit("Un plan de coupe ne peut pas démarrer dans les 3 premières secondes.")
        duree = duree_element(element, finaux, r["plans_de_coupe"]["duree"])
        commande += ["-i", clip_coupe(dossier, element, cache, duree)]
        filtres.append(f"[{entree}:v]setpts=PTS-STARTPTS+{debut}/TB[c{rang}]")
        filtres.append(f"{etiquette}[c{rang}]overlay=0:0:enable='between(t,{debut},{debut + duree})':eof_action=pass[pc{rang}]")
        etiquette, entree = f"[pc{rang}]", entree + 1

    infos_titre, y_titre = None, r["titre"]["y"]
    fin_titre = min(r["titre"]["duree"], total)
    if plan.get("titre"):
        police = police_de(projet["marque"], r["titre"]["police"], alertes)
        place = (tete["haut"] - r["titre"]["marge_tete"] - y_titre) if tete["haut"] else visuel.BAS_UTILE - y_titre
        png_titre = rendu / "titre.png"
        infos_titre = visuel.dessiner_titre(plan["titre"], r["titre"], police, place, png_titre)
        if infos_titre["cache_la_tete"]:
            alertes.append("Le hook text reste trop grand pour passer au-dessus de la tête, même réduit. Il faut le raccourcir.")
    bas_titre = y_titre + infos_titre["hauteur"] if infos_titre else y_titre
    for rang, element in enumerate(images):
        if int(element["mot"]) not in finaux:
            raise SystemExit(f"Image placée sur un mot retiré : {element['mot']}.")
        debut = finaux[int(element["mot"])]["s"]
        duree = duree_element(element, finaux, r["images"]["duree"])
        carte = rendu / f"image-{rang}.png"
        source = chemin_fichier(dossier, element["fichier"])
        reglage_image = {**r["images"], **(element.get("taille") or {})}
        largeur, hauteur = visuel.dessiner_image(source, reglage_image, carte)
        if "position" in element:
            x = int(min(max(element["position"]["x"] - largeur // 2, visuel.GAUCHE_UTILE), visuel.DROITE_UTILE - largeur))
            y = int(element["position"]["y"])
        else:
            choix = visuel.place_image(hauteur, tete, y_st, bas_titre if debut < fin_titre else y_titre, reglage_image)
            if choix is None:
                alertes.append(f"Pas assez de place pour l'image {source.name} : elle n'est pas affichée.")
                continue
            endroit, maximum = choix
            if maximum < hauteur:
                largeur, hauteur = visuel.dessiner_image(source, reglage_image, carte, maximum)
            y = {"dessus": tete["haut"] - r["images"]["marge"] - hauteur, "cote": tete["haut"]}.get(endroit, y_st + r["images"]["ecart_sous_titres"])
            x = visuel.DROITE_UTILE - largeur if endroit == "cote" else "(W-w)/2"
        if tete["vues"] == 0:
            alertes.append("Image posée sans repère de tête : à vérifier à l'œil.")
        commande += ["-loop", 1, "-t", f"{total:.3f}", "-i", carte]
        filtres.append(f"{etiquette}[{entree}:v]overlay={x}:{y}:enable='between(t,{debut},{debut + duree})':shortest=1[im{rang}]")
        etiquette, entree = f"[im{rang}]", entree + 1

    if plan.get("titre"):
        commande += ["-loop", 1, "-t", f"{total:.3f}", "-i", png_titre]
        filtres.append(f"{etiquette}[{entree}:v]overlay=0:{y_titre}:enable='between(t,0,{fin_titre})':shortest=1[ti]")
        etiquette, entree = "[ti]", entree + 1

    appel = plan.get("appel_ecrit")
    if appel and illustrations:
        police = police_de(projet["marque"], r["titre"]["police"], alertes)
        place = (tete["haut"] - r["titre"]["marge_tete"] - y_titre) if tete["haut"] else visuel.BAS_UTILE - y_titre
        png = rendu / "appel.png"
        infos_appel = visuel.dessiner_titre(appel["texte"], r["titre"], police, place, png)
        if infos_appel["cache_la_tete"]:
            alertes.append("L'appel écrit reste trop grand pour passer au-dessus de la tête. Il faut le raccourcir.")
        debut_appel = max(total - float(appel.get("duree", r["titre"]["duree_appel"])), fin_titre)
        commande += ["-loop", 1, "-t", f"{total:.3f}", "-i", png]
        filtres.append(f"{etiquette}[{entree}:v]overlay=0:{y_titre}:enable='between(t,{debut_appel},{total})':shortest=1[ap]")
        etiquette, entree = "[ap]", entree + 1

    polices = rendu / "polices"
    if polices.exists():
        shutil.rmtree(polices)
    polices.mkdir()
    if avec_sous_titres:
        police = police_de(projet["marque"], st["police"], alertes)
        shutil.copy2(police, polices / police.name)
        ordre = [finaux[k] for k in sorted(finaux, key=lambda x: finaux[x]["s"])]
        visuel.ecrire_sous_titres(ordre, st, police, y_st, total, rendu / "textes.ass")
        filtres.append(f"{etiquette}subtitles=textes.ass:fontsdir=polices,format=yuv420p[vout]")
    else:
        filtres.append(f"{etiquette}format=yuv420p[vout]")
    filtres.append(f"[0:a]apad=pad_dur=4,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{total:.4f}[aout]")
    sortie = Path(sortie).resolve()
    sortie.parent.mkdir(parents=True, exist_ok=True)
    commande = [str(c).replace(str(cache / "liste.txt"), "cache/liste.txt") for c in commande]
    commande += ["-filter_complex", ";".join(filtres), "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium",
                 "-crf", "16", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(sortie)]
    son.lancer(commande, cwd=rendu)
    return {"video": str(sortie), "duree": round(total, 2), "tete": tete, "sous_titres_y": y_st, "titre": infos_titre, "alertes": alertes}


def derniere_version(travail):
    versions = sorted((travail / "export").glob("montage-v*.mp4"), key=lambda f: int(f.stem.split("-v")[1]))
    return versions[-1] if versions else None


def cmd_rendre(args):
    dossier, travail, projet, plan, mots, r = charger(args.dossier, args.essai)
    if not (travail / "montage.json").is_file():
        raise SystemExit("Lance d'abord la coupe.")
    derniere = derniere_version(travail)
    numero = int(derniere.stem.split("-v")[1]) + 1 if derniere else 1
    resultat = fabriquer(dossier, travail, projet, plan, mots, r, travail / "export" / f"montage-v{numero}.mp4")
    ecrire(travail / "rendu" / "dernier.json", resultat)
    repondre(**resultat)


def planche_controle(video, instants, sortie):
    images = []
    with tempfile.TemporaryDirectory() as dossier:
        for rang, t in enumerate(instants):
            png = Path(dossier) / f"{rang}.png"
            son.lancer([son.ffmpeg(), "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-frames:v", 1, "-vf", "scale=270:-2", png])
            with Image.open(png) as image:
                images.append(image.convert("RGB"))
    planche = Image.new("RGB", (270 * len(images) + 10 * (len(images) - 1), images[0].height), "#FFFFFF")
    for rang, image in enumerate(images):
        planche.paste(image, (280 * rang, 0))
    planche.save(sortie, quality=90)


def cmd_controler(args):
    dossier, travail, projet, plan, mots, r = charger(args.dossier, args.essai)
    video = derniere_version(travail)
    if not video:
        raise SystemExit("Aucune vidéo à contrôler.")
    montage = lire(travail / "montage.json")
    corrections = plan.get("corrections") or {}
    attendu = [son.normaliser(corrections.get(str(k), mots[k]["w"])) for i, j in montage["passages"] for k in range(i, j + 1)]
    attendu = [m for m in attendu if m]
    entendu = [son.normaliser(m["w"]) for m in son.transcrire(video, "", projet["langue"])]
    entendu = [m for m in entendu if m]
    manquants, en_trop = [], []
    for code, a, b, c, d in difflib.SequenceMatcher(None, attendu, entendu, autojunk=False).get_opcodes():
        if code in ("replace", "delete"):
            manquants += attendu[a:b]
        if code in ("replace", "insert"):
            en_trop += entendu[c:d]
    voix = son.Voix(video)
    zones = voix.zones(0, voix.duree)
    prises = voix.prises()
    silences = voix.zones(prises[0][0], prises[-1][1], valeur=False) if prises else []
    duree = sonde(video)["duree"]
    instants = [0.3, min(r["titre"]["duree"] - 0.3, duree / 3), duree / 2, duree - 0.5]
    finaux = son.mots_finaux(mots, montage["passages"], montage["plans"], corrections)
    for element in (plan.get("images") or []) + (plan.get("plans_de_coupe") or []):
        instants.append(finaux[int(element["mot"])]["s"] + 0.4)
    planche = travail / "rendu" / "controle.jpg"
    planche_controle(video, sorted(instants), planche)
    marge_totale = r["regles"]["marge"] + r["regles"].get("marge_apres", r["regles"]["marge"])
    blanc_limite = max(r["blanc_max"], marge_totale) + 0.1
    raccords, temps = [], 0.0
    for p in montage["plans"][:-1]:
        temps += son.duree_plan(p)
        raccords.append(round(temps, 1))
    (travail / "rendu" / "raccords.txt").write_text("\n".join(f"{t:.1f} s" for t in raccords) + "\n", encoding="utf-8")
    repondre(video=str(video), duree=round(duree, 2), voix_demarre_a=round(zones[0][0], 2) if zones else None,
             plus_long_blanc=round(max([b - a for a, b in silences] or [0]), 2), blanc_limite=round(blanc_limite, 2),
             mots_attendus=len(attendu), mots_manquants=manquants, mots_en_trop=en_trop, planche=str(planche),
             raccords=raccords, doublons_son=son.doublons_son(video))


def cmd_essai(args):
    """Prépare une variante d'essai dans le dossier du contenu, à partir de l'analyse déjà faite."""
    dossier = Path(args.dossier).resolve()
    source = dossier / "travail"
    if args.numero < 2:
        raise SystemExit("Le numéro 1 est la version originale.")
    cible = dossier_essai(source, args.numero)
    if cible.exists():
        raise SystemExit(f"L'essai {args.numero:02d} existe déjà.")
    cible.mkdir(parents=True)
    for nom in ("mots.json", "projet.json", "transcription.txt"):
        shutil.copy2(source / nom, cible / nom)
    plan = lire(source / "plan.json")
    plan["numero"] = args.numero
    ecrire(cible / "plan.json", plan)
    repondre(essai=args.numero, plan=str(cible / "plan.json"))


def cmd_affiner(args):
    _, travail, projet, _, mots, _ = charger(args.dossier, args.essai)
    demandes = [("debut", int(m), t) for m, t in args.debut or []] + [("fin", int(m), t) for m, t in args.fin or []]
    if not demandes:
        raise SystemExit("Indique au moins un --debut ou un --fin.")
    resultats = []
    for rang, rush in enumerate(projet["rushes"]):
        pour_ce_rush = [d for d in demandes if mots[d[1]]["r"] == rang]
        if pour_ce_rush:
            resultats += son.affiner_coupes(rush, son.Voix(rush), mots, pour_ce_rush, projet["langue"])
    ecrire(travail / "mots.json", mots)
    repondre(coupes=resultats)


def fichier_catalogue():
    return commun.ESPACE / commun.NOMS["b_roll"] / "catalogue.jsonl"


def dossier_exemples():
    return commun.ESPACE / commun.NOMS["references"] / "Exemples de montage"


def lire_catalogue():
    fichier = fichier_catalogue()
    if not fichier.is_file():
        return []
    return [json.loads(l) for l in fichier.read_text(encoding="utf-8").splitlines() if l.strip()]


def ecrire_catalogue(lignes):
    fichier = fichier_catalogue()
    fichier.parent.mkdir(parents=True, exist_ok=True)
    temporaire = fichier.with_suffix(".tmp")
    temporaire.write_text("".join(json.dumps(l, ensure_ascii=False) + "\n" for l in lignes), encoding="utf-8")
    temporaire.replace(fichier)


def chemin_espace(chemin):
    """Le chemin à l'intérieur de l'espace : il reste valable sur Drive, qui a les mêmes dossiers."""
    chemin = Path(chemin).resolve()
    try:
        return str(chemin.relative_to(commun.ESPACE.resolve()))
    except ValueError:
        return str(chemin)


def encoder_extrait(source, info, debut, duree, sortie):
    """Un extrait léger : 1080 sur le petit côté au maximum, la taille finale des vidéos."""
    filtre = (TONEMAP + "," if info["hdr"] else "") + \
        "scale='if(lt(iw,ih),min(1080,iw),-2)':'if(lt(iw,ih),-2,min(1080,ih))',setsar=1,format=yuv420p"
    son.lancer([son.ffmpeg(), "-y", "-v", "error", "-ss", f"{debut:.3f}", "-t", f"{duree:.3f}", "-i", source, "-map", "0:v:0",
                "-map", "0:a:0?", "-vf", filtre, "-c:v", "libx264", "-preset", "veryfast", "-crf", 20,
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", sortie])


def identite(projet, plan):
    """Le client et le sujet qui entrent dans le nom des fichiers finaux."""
    fichier = dossier_marque(projet["marque"]) / "marque.json"
    client = lire(fichier).get("client") if fichier.is_file() else None
    if not client:
        raise SystemExit("Il manque le nom court dans marque.json (clé client).")
    if not plan.get("sujet"):
        raise SystemExit("Il manque le sujet dans plan.json (clé sujet).")
    return client, nommage.sujet(plan["sujet"])


def garder_extraits(dossier, plan, r, client):
    """Garde un extrait de chaque b-roll utilisé dans le dossier de la vidéo et l'inscrit au catalogue."""
    coupes = plan.get("plans_de_coupe") or []
    if not coupes:
        return []
    index = {ligne["fichier"]: ligne for ligne in lire_catalogue()}
    longueur = r["plans_de_coupe"]["extrait"]
    contenu, jour = chemin_espace(dossier), datetime.date.today().isoformat()
    fenetres, retenus = {}, []
    (dossier / "b-roll").mkdir(exist_ok=True)
    for element in coupes:
        source = chemin_fichier(dossier, element["fichier"])
        fiche = index.get(chemin_espace(source))
        if fiche is None:
            info = sonde(source)
            depart = float(element.get("debut_source", 0))
            duree = float(element.get("duree", r["plans_de_coupe"]["duree"]))
            existants = fenetres.setdefault(str(source), [])
            trouve = next((f for f in existants if f["a"] <= depart and depart + duree <= f["b"]), None)
            if trouve:
                fiche = trouve["fiche"]
            else:
                a = max(0.0, min(depart + duree / 2 - longueur / 2, info["duree"] - longueur))
                b = min(a + longueur, info["duree"])
                deja = next((e for e in index.values() if e["source"] == source.name and e["contenu"] == contenu
                             and e.get("debut_extrait") == round(a, 3)), None)
                if deja:
                    sortie = commun.ESPACE / deja["fichier"]
                else:
                    sujet_broll = nommage.sujet(element.get("sujet") or element.get("vu") or source.stem)
                    mois = nommage.periode()
                    numero = nommage.prochain_numero(dossier / "b-roll", [f"{mois}-{client}-broll-{sujet_broll}"])
                    sortie = dossier / "b-roll" / nommage.nom_fichier(mois, client, "broll", sujet_broll, numero, ".mp4")
                encoder_extrait(source, info, a, b - a, sortie)
                cle = chemin_espace(sortie)
                fiche = index.setdefault(cle, {"fichier": cle, "vu": "", "themes": [], "source": source.name, "contenu": contenu,
                                               "duree": round(b - a, 1), "date": jour, "debut_extrait": round(a, 3), "utilise": []})
                existants.append({"a": a, "b": b, "fiche": fiche})
        fiche["vu"] = element.get("vu") or fiche["vu"]
        fiche["themes"] = sorted(set(fiche["themes"]) | set(element.get("themes") or []))
        fiche["utilise"] = [u for u in fiche["utilise"] if u["contenu"] != contenu] + [{"contenu": contenu, "date": jour}]
        if fiche["fichier"] not in retenus:
            retenus.append(fiche["fichier"])
    ecrire_catalogue(list(index.values()))
    return retenus


def dernier_reel_sous_titre(final, numero=None):
    """La version validée la plus récente de ce numéro, avec sous-titres et avec ses illustrations."""
    candidats = []
    for fichier in final.glob("*.mp4"):
        infos = nommage.analyser(unicodedata.normalize("NFC", fichier.name))
        if infos["ok"] and infos["type"] == "reel-cc" and not infos["sujet"].endswith("-sans-illustrations") and (not numero or infos["numero"] == numero):
            candidats.append((infos["mois"], infos["numero"], fichier))
    return max(candidats)[2] if candidats else None


def cmd_exemple(args):
    """Fait de cette vidéo validée l'exemple de son style. Elle remplace le précédent."""
    dossier, _, projet, plan, _, _ = charger(args.dossier, args.essai)
    source = dernier_reel_sous_titre(dossier / "final", plan.get("numero"))
    if not source:
        raise SystemExit("Valide d'abord cette vidéo.")
    nom = next(s["nom"] for s in lire(BASE)["styles"] if s["id"] == projet["style"])
    dossier_cible = dossier_exemples()
    dossier_cible.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dossier_cible / f"{nom}.mp4")
    registre = dossier_cible / "exemples.json"
    exemples = lire(registre) if registre.is_file() else {}
    exemples[nom] = {"fichier": f"{nom}.mp4", "contenu": chemin_espace(dossier), "date": datetime.date.today().isoformat(), "note": args.note}
    ecrire(registre, exemples)
    repondre(exemple=str(dossier_cible / f"{nom}.mp4"))


def ecrire_texte(dossier, plan, mots, passages):
    """Le script gardé, mot pour mot, une phrase par ligne, dans final/texte.txt."""
    corrections = plan.get("corrections") or {}
    phrases, courant = [], []
    for i, j in passages:
        for k in range(i, j + 1):
            mot = corrections.get(str(k), mots[k]["w"])
            if not mot:
                continue
            courant.append(mot)
            if mot[-1:] in ".?!":
                phrases.append(" ".join(courant))
                courant = []
    if courant:
        phrases.append(" ".join(courant))
    lignes = ([f"HT: {plan['titre']}", ""] if plan.get("titre") else []) + phrases
    nom = f"texte-essai-{plan['numero']:02d}.txt" if (plan.get("numero") or 1) > 1 else "texte.txt"
    (dossier / "final" / nom).write_text("\n".join(lignes) + "\n", encoding="utf-8")


def vignette(fichier, largeur, hauteur):
    if fichier.suffix.lower() in EXT_VIDEOS:
        with tempfile.TemporaryDirectory() as dossier:
            png = Path(dossier) / "image.png"
            son.lancer([son.ffmpeg(), "-y", "-v", "error", "-ss", f"{sonde(fichier)['duree'] / 2:.3f}", "-i", fichier, "-frames:v", 1, png])
            with Image.open(png) as image:
                source = image.convert("RGB")
    else:
        with Image.open(fichier) as image:
            source = ImageOps.exif_transpose(image).convert("RGB")
    return ImageOps.fit(source, (largeur, hauteur))


def cmd_matiere(args):
    """Montre en une planche numérotée les images et b-rolls disponibles, pour choisir où les placer."""
    dossier = Path(args.dossier).resolve()
    fichiers = []
    for source in [dossier / "images", dossier / "b-roll"] + [Path(x).expanduser() for x in args.depuis or []]:
        if source.is_dir():
            fichiers += [f for f in source.iterdir() if f.suffix.lower() in EXT_IMAGES | EXT_VIDEOS]
    trouves = {}
    if args.cherche:
        cherches = {son.normaliser(m) for m in args.cherche.split()} - {""}
        for ligne in lire_catalogue():
            texte = {son.normaliser(m) for m in (ligne["vu"] + " " + " ".join(ligne["themes"])).split()}
            chemin = commun.ESPACE / ligne["fichier"]
            if cherches & texte and chemin.is_file():
                trouves[str(chemin.resolve())] = ligne
                fichiers.append(chemin.resolve())
    fichiers = sorted(set(fichiers), key=lambda f: (str(f) not in trouves, -f.stat().st_mtime))[:MATIERE_MAX]
    if not fichiers:
        repondre(fichiers=[], planche=None)
        return
    largeur, hauteur, colonnes = 200, 356, 6
    lignes = (len(fichiers) + colonnes - 1) // colonnes
    planche = Image.new("RGB", (colonnes * (largeur + 8), lignes * (hauteur + 8)), "#FFFFFF")
    dessin = ImageDraw.Draw(planche)
    fonte = ImageFont.truetype(str(POLICES / "Poppins-Bold.ttf"), 34)
    liste = []
    for rang, fichier in enumerate(fichiers):
        x, y = (rang % colonnes) * (largeur + 8), (rang // colonnes) * (hauteur + 8)
        planche.paste(vignette(fichier, largeur, hauteur), (x, y))
        dessin.rectangle((x, y, x + 70, y + 50), fill="#000000")
        dessin.text((x + 35, y + 25), str(rang + 1), font=fonte, fill="#FFFFFF", anchor="mm")
        video = fichier.suffix.lower() in EXT_VIDEOS
        liste.append({"numero": rang + 1, "chemin": str(fichier), "type": "b-roll" if video else "image",
                      "duree": round(sonde(fichier)["duree"], 1) if video else None})
        if str(fichier) in trouves:
            fiche = trouves[str(fichier)]
            liste[-1]["catalogue"] = {"vu": fiche["vu"], "themes": fiche["themes"], "derniere_utilisation": fiche["utilise"][-1]["date"] if fiche["utilise"] else None}
    sortie = dossier / "travail" / "rendu" / "matiere.jpg"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    planche.save(sortie, quality=88)
    repondre(fichiers=liste, planche=str(sortie))


def cmd_valider(args):
    dossier, travail, projet, plan, mots, r = charger(args.dossier, args.essai)
    video = derniere_version(travail)
    if not video:
        raise SystemExit("Aucune vidéo à valider.")
    client, sujet_video = identite(projet, plan)
    code_style = next(s["code"] for s in lire(BASE)["styles"] if s["id"] == projet["style"])
    sujet_video = f"{code_style}-{sujet_video}"
    final = dossier / "final"
    final.mkdir(exist_ok=True)
    mois = nommage.periode()
    numero = plan.get("numero") or nommage.prochain_numero(final, [f"{mois}-{client}-reel-cc-{sujet_video}", f"{mois}-{client}-reel-nocc-{sujet_video}"])

    def nom(type_, sujet_):
        return final / nommage.nom_fichier(mois, client, type_, sujet_, numero, ".mp4")

    shutil.copy2(video, nom("reel-cc", sujet_video))
    resultat = fabriquer(dossier, travail, projet, plan, mots, r, nom("reel-nocc", sujet_video), avec_sous_titres=False)
    if args.aussi_sans_illustrations:
        sans = f"{sujet_video}-sans-illustrations"
        fabriquer(dossier, travail, projet, plan, mots, r, nom("reel-cc", sans), illustrations=False)
        fabriquer(dossier, travail, projet, plan, mots, r, nom("reel-nocc", sans), avec_sous_titres=False, illustrations=False)
    ecrire_texte(dossier, plan, mots, lire(travail / "montage.json")["passages"])
    extraits = garder_extraits(dossier, plan, r, client)
    fichier_droits = dossier / "images" / "sources.json"
    droits = lire(fichier_droits) if fichier_droits.is_file() else {}
    repondre(final=str(final), fichiers=sorted(f.name for f in final.iterdir() if f.is_file()), alertes=resultat["alertes"],
             droits_a_verifier=[nom for nom, info in droits.items() if info.get("droits") != "libre"], extraits_b_roll=extraits)


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("styles").set_defaults(fonction=cmd_styles)
    p = actions.add_parser("reglages")
    p.add_argument("--marque", required=True)
    p.set_defaults(fonction=cmd_reglages)
    p = actions.add_parser("analyser")
    p.add_argument("--dossier", required=True)
    p.add_argument("--style", default="yap")
    p.add_argument("--marque", required=True)
    p.add_argument("--rush", action="append", required=True)
    p.add_argument("--langue", default="fr")
    p.add_argument("--remplacer", action="store_true")
    p.set_defaults(fonction=cmd_analyser)
    for nom, fonction in (("couper", cmd_couper), ("rendre", cmd_rendre), ("controler", cmd_controler), ("valider", cmd_valider)):
        p = actions.add_parser(nom)
        p.add_argument("--dossier", required=True)
        p.add_argument("--essai", type=int)
        if nom == "valider":
            p.add_argument("--aussi-sans-illustrations", action="store_true")
        p.set_defaults(fonction=fonction)
    p = actions.add_parser("essai")
    p.add_argument("--dossier", required=True)
    p.add_argument("--numero", type=int, required=True)
    p.set_defaults(fonction=cmd_essai)
    p = actions.add_parser("affiner")
    p.add_argument("--dossier", required=True)
    p.add_argument("--essai", type=int)
    p.add_argument("--debut", nargs=2, action="append", metavar=("MOT", "TEXTE"))
    p.add_argument("--fin", nargs=2, action="append", metavar=("MOT", "TEXTE"))
    p.set_defaults(fonction=cmd_affiner)
    p = actions.add_parser("exemple")
    p.add_argument("--dossier", required=True)
    p.add_argument("--essai", type=int)
    p.add_argument("--note", default="")
    p.set_defaults(fonction=cmd_exemple)
    p = actions.add_parser("matiere")
    p.add_argument("--dossier", required=True)
    p.add_argument("--depuis", action="append")
    p.add_argument("--cherche", default="")
    p.set_defaults(fonction=cmd_matiere)
    args = parser.parse_args()
    args.fonction(args)


if __name__ == "__main__":
    sys.exit(main())

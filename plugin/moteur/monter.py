"""Le montage du Studio. À lancer avec le Python du moteur.

    monter.py styles
    monter.py reglages --marque <dossier de marque>
    monter.py analyser --dossier <contenu> --style yap --marque <marque> --rush <fichier> [--rush <fichier>]
    monter.py couper   --dossier <contenu>
    monter.py rendre   --dossier <contenu>
    monter.py controler --dossier <contenu>
    monter.py valider  --dossier <contenu>

Les règles de base sont dans ressources/montage-base.json. La personnalisation est dans
00. Branding/<marque>/montage.json. Les choix d'une vidéo sont dans travail/plan.json.
"""
import argparse
import copy
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

import commun
import montage_image as visuel
import montage_son as son

BASE = commun.RACINE_PLUGIN / "ressources" / "montage-base.json"
POLICES = commun.RACINE_PLUGIN / "moteur" / "polices"
TONEMAP = "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv"
L, H, FPS = 1080, 1920, son.FPS


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
    repondre(styles=[{c: s[c] for c in ("id", "nom", "pour", "disponible", "prerequis")} for s in lire(BASE)["styles"]])


def cmd_reglages(args):
    print(json.dumps(reglages(args.marque), ensure_ascii=False, indent=1))


def cmd_analyser(args):
    dossier = Path(args.dossier).resolve()
    travail = dossier / "travail"
    travail.mkdir(parents=True, exist_ok=True)
    (dossier / "final").mkdir(exist_ok=True)
    r = reglages(args.marque, args.style)
    rushes = [str(Path(x).expanduser().resolve()) for x in args.rush]
    mots, infos = [], []
    for rang, rush in enumerate(rushes):
        info = sonde(rush)
        if not info["son"]:
            raise SystemExit(f"Cette vidéo n'a pas de son : {Path(rush).name}")
        infos.append(info)
        voix = son.Voix(rush)
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
             rushes=[{"nom": Path(x).name, **i} for x, i in zip(rushes, infos)],
             transcription=str(travail / "transcription.txt"), plan=str(plan))


def charger(dossier):
    dossier = Path(dossier).resolve()
    travail = dossier / "travail"
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
    _, travail, projet, plan, mots, r = charger(args.dossier)
    passages = controler_plan(plan, mots)
    voix = [son.Voix(x) for x in projet["rushes"]]
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
    cle = hashlib.md5(json.dumps([str(source), source.stat().st_mtime, depart, duree]).encode()).hexdigest()[:12]
    sortie = cache / f"coupe-{cle}.mkv"
    if not sortie.exists():
        filtre = (TONEMAP + "," if info["hdr"] else "") + \
            f"fps={FPS},scale={L}:{H}:force_original_aspect_ratio=increase,crop={L}:{H},setsar=1,format=yuv420p"
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
    for plan in plans:
        duree = son.duree_plan(plan)
        pas, t = 0.15, 0.0
        while t < duree:
            pendant = temps + t <= duree_titre
            if pendant or t == 0.0:
                instants.append((plan["r"], plan["debut"] + (t or min(0.1, duree / 2)), pendant))
            t = t + pas
        temps += duree
    return instants


def fabriquer(dossier, travail, projet, plan, mots, r, sortie, avec_sous_titres=True):
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
    tete = visuel.position_tete(projet["rushes"], instants_tete(plans, r["titre"]["duree"]))
    if tete["vues"] == 0:
        alertes.append("Visage non repéré : le titre et les sous-titres sont placés par défaut. À vérifier à l'œil.")
    st = r["sous_titres"]
    y_st = min(tete["menton"] + st["ecart_menton"], st["y_max"]) if tete["menton"] else st["y_defaut"]

    commande = [son.ffmpeg(), "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", cache / "liste.txt"]
    filtres, etiquette, entree = [], "[0:v]", 1
    for rang, element in enumerate(plan.get("plans_de_coupe") or []):
        if int(element["mot"]) not in finaux:
            raise SystemExit(f"Plan de coupe placé sur un mot retiré : {element['mot']}.")
        debut = finaux[int(element["mot"])]["s"]
        if debut < r["plans_de_coupe"]["debut_min"]:
            raise SystemExit("Un plan de coupe ne peut pas démarrer dans les 3 premières secondes.")
        duree = float(element.get("duree", r["plans_de_coupe"]["duree"]))
        commande += ["-i", clip_coupe(dossier, element, cache, duree)]
        filtres.append(f"[{entree}:v]setpts=PTS-STARTPTS+{debut}/TB[c{rang}]")
        filtres.append(f"{etiquette}[c{rang}]overlay=0:0:enable='between(t,{debut},{debut + duree})':eof_action=pass[pc{rang}]")
        etiquette, entree = f"[pc{rang}]", entree + 1

    infos_titre, y_titre = None, r["titre"]["y"]
    fin_titre = min(r["titre"]["duree"], total)
    for rang, element in enumerate(plan.get("images") or []):
        if int(element["mot"]) not in finaux:
            raise SystemExit(f"Image placée sur un mot retiré : {element['mot']}.")
        debut = finaux[int(element["mot"])]["s"]
        duree = float(element.get("duree", r["images"]["duree"]))
        carte = rendu / f"image-{rang}.png"
        source = chemin_fichier(dossier, element["fichier"])
        _, hauteur = visuel.dessiner_image(source, r["images"], carte)
        y, maximum = visuel.place_image(hauteur, tete, y_st, y_titre, debut < fin_titre, r["images"])
        if maximum < hauteur:
            _, hauteur = visuel.dessiner_image(source, r["images"], carte, maximum)
        if tete["vues"] == 0:
            alertes.append("Image posée sans repère de tête : à vérifier à l'œil.")
        commande += ["-loop", 1, "-t", f"{total:.3f}", "-i", carte]
        filtres.append(f"{etiquette}[{entree}:v]overlay=(W-w)/2:{y}:enable='between(t,{debut},{debut + duree})':shortest=1[im{rang}]")
        etiquette, entree = f"[im{rang}]", entree + 1

    if plan.get("titre"):
        police = police_de(projet["marque"], r["titre"]["police"], alertes)
        place = (tete["haut"] - r["titre"]["marge_tete"] - y_titre) if tete["haut"] else visuel.BAS_UTILE - y_titre
        png = rendu / "titre.png"
        infos_titre = visuel.dessiner_titre(plan["titre"], r["titre"], police, place, png)
        if infos_titre["cache_la_tete"]:
            alertes.append("Le titre reste trop grand pour passer au-dessus de la tête, même réduit. Il faut le raccourcir.")
        commande += ["-loop", 1, "-t", f"{total:.3f}", "-i", png]
        filtres.append(f"{etiquette}[{entree}:v]overlay=0:{y_titre}:enable='between(t,0,{fin_titre})':shortest=1[ti]")
        etiquette, entree = "[ti]", entree + 1

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
                 "-crf", "18", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(sortie)]
    son.lancer(commande, cwd=rendu)
    return {"video": str(sortie), "duree": round(total, 2), "tete": tete, "sous_titres_y": y_st, "titre": infos_titre, "alertes": alertes}


def derniere_version(travail):
    versions = sorted((travail / "export").glob("montage-v*.mp4"), key=lambda f: int(f.stem.split("-v")[1]))
    return versions[-1] if versions else None


def cmd_rendre(args):
    dossier, travail, projet, plan, mots, r = charger(args.dossier)
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
    dossier, travail, projet, plan, mots, r = charger(args.dossier)
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
    for element in plan.get("images") or []:
        instants.append(finaux[int(element["mot"])]["s"] + 0.4)
    planche = travail / "rendu" / "controle.jpg"
    planche_controle(video, sorted(instants), planche)
    blanc_limite = max(r["blanc_max"], 2 * r["regles"]["marge"]) + 0.1
    repondre(video=str(video), duree=round(duree, 2), voix_demarre_a=round(zones[0][0], 2) if zones else None,
             plus_long_blanc=round(max([b - a for a, b in silences] or [0]), 2), blanc_limite=round(blanc_limite, 2),
             mots_attendus=len(attendu), mots_manquants=manquants, mots_en_trop=en_trop, planche=str(planche))


def cmd_valider(args):
    dossier, travail, projet, plan, mots, r = charger(args.dossier)
    video = derniere_version(travail)
    if not video:
        raise SystemExit("Aucune vidéo à valider.")
    final = dossier / "final"
    final.mkdir(exist_ok=True)
    shutil.copy2(video, final / "avec-sous-titres.mp4")
    resultat = fabriquer(dossier, travail, projet, plan, mots, r, final / "sans-sous-titres.mp4", avec_sous_titres=False)
    repondre(final=str(final), fichiers=sorted(f.name for f in final.iterdir() if f.is_file()), alertes=resultat["alertes"])


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
        p.set_defaults(fonction=fonction)
    args = parser.parse_args()
    args.fonction(args)


if __name__ == "__main__":
    sys.exit(main())

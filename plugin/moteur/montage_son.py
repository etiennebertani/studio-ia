"""Le son d'un rush : transcription au mot, vraie place de la voix, propositions de coupe."""
import difflib
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

import commun

TAUX = 16000
PAS = 0.02
FPS = 30
MARGE_ECOUTE = 0.15
ECART_PRISES = 0.35
DUREE_MORCEAU_MIN = 0.3
MOTS_COLLES = 0.15
FANTOME = ["soustitrage", "société", "radiocanada"]
REPRISE_ECART = 60
DOUBLON_SEUIL = 0.7
AFFINER_RAYON = 0.7
AFFINER_ESSAIS = 16


def lancer(commande, cwd=None):
    resultat = subprocess.run([str(c) for c in commande], capture_output=True, text=True, cwd=cwd)
    if resultat.returncode != 0:
        raise SystemExit("Échec de {} :\n{}".format(Path(str(commande[0])).name, resultat.stderr[-1500:]))
    return resultat


def ffmpeg():
    return commun.outil("ffmpeg")


def vers_wav(source, sortie, filtre=None):
    commande = [ffmpeg(), "-y", "-v", "error", "-i", source, "-vn", "-ac", "1", "-ar", TAUX]
    if filtre:
        commande += ["-af", filtre]
    lancer(commande + [sortie])


def _lire_mots(chemin, decalage):
    donnees = json.loads(Path(chemin).read_text(encoding="utf-8", errors="replace"))
    mots = []
    for segment in donnees.get("transcription", []):
        texte = segment["text"].strip()
        if not texte or texte.startswith("["):
            continue
        if mots and not any(c.isalnum() for c in texte):
            mots[-1]["w"] += texte
            continue
        mots.append({"s": segment["offsets"]["from"] / 1000 + decalage, "e": segment["offsets"]["to"] / 1000 + decalage, "w": texte})
    return mots


def transcrire(source, invite, langue="fr", zones=None):
    """Les mots d'un fichier : [{"s": début, "e": fin, "w": texte}].

    Avec des zones, chaque prise de parole est écoutée à part : sinon la transcription fond deux prises
    d'une même phrase en une seule, et la répétition devient impossible à repérer.
    """
    exe, modele = commun.outil("whisper-cli"), commun.modele_whisper()
    if not exe or not modele:
        raise SystemExit("La transcription n'est pas installée.")
    with tempfile.TemporaryDirectory() as dossier:
        dossier = Path(dossier)
        son = dossier / "son.wav"
        vers_wav(source, son)
        morceaux = [(son, 0.0)]
        if zones:
            with wave.open(str(son), "rb") as fichier:
                brut = fichier.readframes(fichier.getnframes())
            morceaux = []
            for rang, (a, b) in enumerate(zones):
                debut = max(a - MARGE_ECOUTE, 0.0)
                chemin = dossier / f"zone{rang:04d}.wav"
                with wave.open(str(chemin), "wb") as fichier:
                    fichier.setnchannels(1)
                    fichier.setsampwidth(2)
                    fichier.setframerate(TAUX)
                    fichier.writeframes(brut[int(debut * TAUX) * 2:int((b + MARGE_ECOUTE) * TAUX) * 2])
                morceaux.append((chemin, debut))
        commande = [exe, "-m", modele, "-l", langue, "-ml", 1, "-sow", "-oj", "-np"]
        for chemin, _ in morceaux:
            commande += ["-f", chemin]
        if invite:
            commande += ["--prompt", invite]
        lancer(commande)
        mots = []
        for chemin, decalage in morceaux:
            mots += _lire_mots(str(chemin) + ".json", decalage)
    return enlever_fantomes(mots)


def enlever_fantomes(mots):
    """Retire les génériques que la transcription invente sur les silences."""
    gardes = []
    i = 0
    while i < len(mots):
        if [normaliser(m["w"]) for m in mots[i:i + 3]] == FANTOME:
            i += 3
            continue
        gardes.append(mots[i])
        i += 1
    return gardes


class Voix:
    """Où la personne parle vraiment. Le niveau du silence est mesuré sur chaque vidéo."""

    def __init__(self, source):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "voix.wav"
            vers_wav(source, chemin, "highpass=f=150,lowpass=f=4000")
            with wave.open(str(chemin), "rb") as fichier:
                brut = fichier.readframes(fichier.getnframes())
        echantillons = np.frombuffer(brut, dtype=np.int16).astype(np.float64) / 32768
        taille = int(TAUX * PAS)
        n = max(1, len(echantillons) // taille)
        cadres = echantillons[:n * taille].reshape(n, taille)
        niveau = 20 * np.log10(np.sqrt((cadres ** 2).mean(axis=1)) + 1e-6)
        niveau = np.convolve(niveau, np.ones(3) / 3, "same")
        bas, haut = np.percentile(niveau, 10), np.percentile(niveau, 95)
        self.niveau = niveau
        self.seuil = float(bas + 0.4 * (haut - bas))
        self.parle = self._nettoyer(niveau > self.seuil)
        self.duree = n * PAS

    def recaler(self, morceaux):
        """Remesure le silence sur les seuls passages gardés : les longues pauses d'un rush faussent le niveau."""
        cadres = [self.niveau[self._indice(a):self._indice(b) + 1] for a, b in morceaux if b > a]
        if not cadres:
            return
        niveau = np.concatenate(cadres)
        bas, haut = np.percentile(niveau, 10), np.percentile(niveau, 95)
        self.seuil = float(bas + 0.4 * (haut - bas))
        self.parle = self._nettoyer(self.niveau > self.seuil)

    @staticmethod
    def _nettoyer(parle):
        parle = parle.copy()
        for valeur, longueur in ((False, round(0.1 / PAS)), (True, round(0.06 / PAS))):
            debut = None
            for i, v in enumerate(list(parle) + [not valeur]):
                if v == valeur and debut is None:
                    debut = i
                elif v != valeur and debut is not None:
                    if i - debut < longueur and debut > 0 and i < len(parle):
                        parle[debut:i] = not valeur
                    debut = None
        return parle

    def _indice(self, t):
        return min(max(int(t / PAS), 0), len(self.parle) - 1)

    def zones(self, a, b, valeur=True):
        """Les morceaux de [a, b] où la voix est présente (ou absente si valeur vaut False)."""
        i, j = self._indice(a), self._indice(b)
        sortie, debut = [], None
        for k in range(i, j + 1):
            if self.parle[k] == valeur and debut is None:
                debut = k
            elif self.parle[k] != valeur and debut is not None:
                sortie.append((max(debut * PAS, a), min(k * PAS, b)))
                debut = None
        if debut is not None:
            sortie.append((max(debut * PAS, a), b))
        return [(x, y) for x, y in sortie if y > x]

    def creux(self, t, rayon=0.06):
        """Le moment le plus calme autour de t : là où une coupe ne mord sur aucun mot."""
        a, b = self._indice(t - rayon), self._indice(t + rayon) + 1
        return round((a + int(np.argmin(self.niveau[a:b]))) * PAS, 3)

    def prises(self):
        """Les prises de parole : les zones de voix, réunies quand le blanc entre elles est court."""
        sortie = []
        for a, b in self.zones(0, self.duree):
            if b - a < 0.1:
                continue
            if sortie and a - sortie[-1][1] < ECART_PRISES:
                sortie[-1] = (sortie[-1][0], b)
            else:
                sortie.append((a, b))
        return sortie

    def debut(self, s, e, limite=0.0):
        """Le vrai début de la voix d'un mot que la transcription place à s."""
        i = self._indice(s)
        if not self.parle[i]:
            zones = self.zones(s, e)
            return max(zones[0][0] if zones else s, limite)
        while i > 0 and self.parle[i - 1] and s - (i - 1) * PAS <= 0.3:
            i -= 1
        return max(i * PAS, limite)

    def fin(self, s, e, limite):
        i = self._indice(e - 1e-6)
        if not self.parle[i]:
            zones = self.zones(s, e)
            return min(zones[-1][1] if zones else e, limite)
        while i + 1 < len(self.parle) and self.parle[i + 1] and (i + 1) * PAS - e <= 0.3:
            i += 1
        return min((i + 1) * PAS, limite)


def reparer_mots(mots, voix):
    """Recale les mots sur la voix. Ceux sans durée fiable sont répartis sur le temps parlé autour d'eux."""
    for mot in mots:
        zones = voix.zones(mot["s"], mot["e"]) if mot["e"] > mot["s"] else []
        if zones:
            mot["s"], mot["e"] = zones[0][0], zones[-1][1]
        mot["ok"] = bool(zones) and mot["e"] - mot["s"] >= 0.04
    for avant, mot in zip(mots, mots[1:]):
        if mot["s"] < avant["e"] - 0.02:
            mot["ok"] = False
    i = 0
    while i < len(mots):
        if mots[i]["ok"]:
            i += 1
            continue
        j = i
        while j + 1 < len(mots) and not mots[j + 1]["ok"]:
            j += 1
        a = mots[i - 1]["e"] if i else voix.prises()[0][0]
        b = mots[j + 1]["s"] if j + 1 < len(mots) else max(mots[j]["e"], a + 0.1 * (j - i + 1))
        _repartir(mots[i:j + 1], voix.zones(a, b) or [(a, max(b, a + 0.05 * (j - i + 1)))])
        i = j + 1
    for mot in mots:
        mot.pop("ok", None)
        mot["s"], mot["e"] = round(mot["s"], 3), round(mot["e"], 3)
    return mots


def _repartir(groupe, zones):
    total = sum(y - x for x, y in zones)
    poids = sum(max(len(m["w"]), 1) for m in groupe)

    def position(reste):
        for x, y in zones:
            if reste <= y - x:
                return x + reste
            reste -= y - x
        return zones[-1][1]

    avance = 0.0
    for mot in groupe:
        part = total * max(len(mot["w"]), 1) / poids
        mot["s"], mot["e"] = position(avance + 0.001), position(avance + part - 0.001)
        avance += part


def normaliser(mot):
    return re.sub(r"[^\w']", "", mot.lower().replace("’", "'"))


def proposer_retraits(mots, regles):
    """Les mots à enlever d'office : {indice: raison}. Claude et la personne ont le dernier mot."""
    retraits = {}
    formes = [normaliser(m["w"]) for m in mots]
    for i, forme in enumerate(formes):
        if forme in regles["mots_parasites"]:
            retraits[i] = "hésitation"
    for n in range(8, 0, -1):
        for i in range(len(mots) - 2 * n + 1):
            if not all(formes[i:i + n]) or formes[i:i + n] != formes[i + n:i + 2 * n]:
                continue
            ecart = mots[i + n]["s"] - mots[i + n - 1]["e"]
            if n == 1 and (formes[i] in regles["repetitions_permises"] or ecart >= regles["repetition_max"]):
                continue
            if n > 1 and ecart >= regles["reprise_max"]:
                continue
            for k in range(i, i + n):
                retraits.setdefault(k, "reprise : on garde la dernière")
    return retraits


def proposer_reprises(mots, voix, regles):
    """Les passages dits plusieurs fois, même avec des mots un peu différents : [{"prise", "reprise", "ressemblance"}]."""
    ignores = set(regles["mots_parasites"]) | {"donc", "bon", "alors", "voila", "enfin", "hein"}
    groupes = []
    for rang, v in enumerate(voix):
        for debut, fin in v.prises():
            indices = [i for i, m in enumerate(mots) if m["r"] == rang and debut <= (m["s"] + m["e"]) / 2 <= fin]
            if indices:
                formes = [normaliser(mots[i]["w"]) for i in indices]
                groupes.append({"r": rang, "premier": indices[0], "dernier": indices[-1], "debut": debut, "fin": fin,
                                "formes": [f for f in formes if f and f not in ignores]})
    reprises = []
    for k, groupe in enumerate(groupes):
        if len(groupe["formes"]) < 3:
            continue
        for suivant in groupes[k + 1:k + 5]:
            if suivant["r"] != groupe["r"] or suivant["debut"] - groupe["fin"] > REPRISE_ECART or not suivant["formes"]:
                continue
            ressemblance = difflib.SequenceMatcher(None, groupe["formes"], suivant["formes"]).ratio()
            faux_depart = len(groupe["formes"]) < len(suivant["formes"]) and suivant["formes"][:len(groupe["formes"])] == groupe["formes"]
            if faux_depart or (ressemblance >= 0.6 and len(suivant["formes"]) >= 0.6 * len(groupe["formes"])):
                reprises.append({"prise": [groupe["premier"], groupe["dernier"]], "reprise": [suivant["premier"], suivant["dernier"]],
                                 "ressemblance": round(ressemblance, 2)})
                break
    return reprises


def doublons_son(source, seuil=DOUBLON_SEUIL):
    """Compare le son à lui-même : deux passages presque identiques qui se suivent trahissent un bafouillage."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = Path(dossier) / "son.wav"
        vers_wav(source, chemin)
        with wave.open(str(chemin), "rb") as fichier:
            echantillons = np.frombuffer(fichier.readframes(fichier.getnframes()), dtype=np.int16).astype(float) / 32768
    fenetre, saut = 400, 320
    n = (len(echantillons) - fenetre) // saut
    if n <= 0:
        return []
    forme = np.hanning(fenetre)
    spectre = np.array([np.abs(np.fft.rfft(echantillons[i * saut:i * saut + fenetre] * forme)) for i in range(n)])
    frequences = np.fft.rfftfreq(fenetre, 1 / TAUX)
    bandes = np.geomspace(100, 6000, 41)
    filtre = np.array([spectre[:, (frequences >= bandes[b]) & (frequences < bandes[b + 1])].sum(axis=1) for b in range(40)]).T
    empreinte = np.log(filtre + 1e-6)
    empreinte -= empreinte.mean(axis=0)
    energie = 20 * np.log10(np.sqrt((spectre ** 2).mean(axis=1)) + 1e-9)
    parle = energie > np.percentile(energie, 35)
    pas = saut / TAUX

    def centrer(bloc):
        bloc = bloc - bloc.mean(axis=0)
        return bloc / (np.linalg.norm(bloc) + 1e-9)

    trouves = []
    for longueur in (12, 16, 20, 25, 30, 38, 48, 60):
        for i in range(0, n - 2 * longueur - 30, 2):
            if parle[i:i + longueur].mean() < 0.8:
                continue
            bloc = centrer(empreinte[i:i + longueur])
            meilleur = (0.0, None)
            for ecart in range(0, 31):
                j = i + longueur + ecart
                if j + longueur <= n and parle[j:j + longueur].mean() >= 0.8:
                    score = float((bloc * centrer(empreinte[j:j + longueur])).sum())
                    if score > meilleur[0]:
                        meilleur = (score, j)
            if meilleur[0] > seuil:
                trouves.append((round(meilleur[0], 2), round(i * pas, 2), round(meilleur[1] * pas, 2)))
    gardes = []
    for score, a, b in sorted(trouves, reverse=True):
        if not any(abs(a - g["debut"]) < 0.4 for g in gardes):
            gardes.append({"score": score, "debut": a, "reprise": b})
    return sorted(gardes, key=lambda g: g["debut"])


def affiner_coupes(rush, voix, mots, demandes, langue="fr"):
    """Essaie plusieurs creux du son autour d'une coupe et garde celui où l'on entend exactement les mots attendus."""
    exe, modele = commun.outil("whisper-cli"), commun.modele_whisper()
    resultats, essais = [], []

    def formes(texte):
        return [f for f in (normaliser(x) for x in re.split(r"[\s'’-]+", texte)) if f]

    with tempfile.TemporaryDirectory() as dossier:
        dossier = Path(dossier)
        son = dossier / "son.wav"
        vers_wav(rush, son)
        with wave.open(str(son), "rb") as fichier:
            brut = fichier.readframes(fichier.getnframes())
        for rang, (sens, mot, attendu) in enumerate(demandes):
            nominal = mots[mot]["s"] if sens == "debut" else mots[mot]["e"]
            a, b = int((nominal - AFFINER_RAYON) / PAS), int((nominal + AFFINER_RAYON) / PAS)
            creux = [k * PAS for k in range(max(a, 1), min(b, len(voix.niveau) - 1))
                     if voix.niveau[k] <= voix.niveau[k - 1] and voix.niveau[k] <= voix.niveau[k + 1]]
            for numero, point in enumerate(sorted(creux, key=lambda c: abs(c - nominal))[:AFFINER_ESSAIS]):
                x, y = (point, point + 1.6) if sens == "debut" else (max(point - 1.6, 0.0), point)
                chemin = dossier / f"essai{rang:03d}{numero:03d}.wav"
                with wave.open(str(chemin), "wb") as sortie:
                    sortie.setnchannels(1)
                    sortie.setsampwidth(2)
                    sortie.setframerate(TAUX)
                    sortie.writeframes(brut[int(x * TAUX) * 2:int(y * TAUX) * 2])
                essais.append((rang, point, chemin))
        commande = [exe, "-m", modele, "-l", langue, "-oj", "-np"]
        for _, _, chemin in essais:
            commande += ["-f", chemin]
        lancer(commande)
        for rang, (sens, mot, attendu) in enumerate(demandes):
            cible = formes(attendu)
            trouve = None
            for _, point, chemin in (e for e in essais if e[0] == rang):
                donnees = json.loads(Path(str(chemin) + ".json").read_text(encoding="utf-8", errors="replace"))
                entendu = formes(" ".join(s["text"] for s in donnees.get("transcription", [])))
                extrait = entendu[:len(cible)] if sens == "debut" else entendu[-len(cible):]
                if extrait == cible:
                    trouve = round(point, 3)
                    break
            if trouve is not None:
                if sens == "debut":
                    mots[mot]["s"] = trouve
                    if mot:
                        mots[mot - 1]["e"] = trouve
                else:
                    mots[mot]["e"] = trouve
                    if mot + 1 < len(mots):
                        mots[mot + 1]["s"] = trouve
            resultats.append({"mot": mot, "sens": sens, "attendu": attendu, "coupe": trouve})
    return resultats


def passages_depuis(mots, retraits):
    passages, debut = [], None
    for i, mot in enumerate(mots):
        rupture = i in retraits or (debut is not None and mot["r"] != mots[debut]["r"])
        if rupture and debut is not None:
            passages.append([debut, i - 1])
            debut = None
        if i not in retraits and debut is None:
            debut = i
    if debut is not None:
        passages.append([debut, len(mots) - 1])
    return passages


def couper(mots, voix, passages, regles, blanc_max):
    """Transforme les passages gardés en plans, en temps du rush."""
    plans = []
    for rang, (i, j) in enumerate(passages):
        rush = mots[i]["r"]
        v = voix[rush]
        lim_avant = mots[i - 1]["e"] if i and mots[i - 1]["r"] == rush else 0.0
        lim_apres = mots[j + 1]["s"] if j + 1 < len(mots) and mots[j + 1]["r"] == rush else v.duree
        debut_voix = v.debut(mots[i]["s"], mots[i]["e"], lim_avant)
        fin_voix = v.fin(mots[j]["s"], mots[j]["e"], lim_apres)
        avant = regles["attaque"] if rang == 0 else regles["marge"]
        marge_apres = regles.get("marge_apres", regles["marge"])
        apres = regles["fin"] if rang == len(passages) - 1 else marge_apres
        courant = max(debut_voix - avant, lim_avant, 0.0)
        limite_fin = min(fin_voix + apres, lim_apres, v.duree)
        if i and mots[i - 1]["r"] == rush and mots[i]["s"] - mots[i - 1]["e"] < MOTS_COLLES:
            courant = debut_voix = v.creux(mots[i]["s"])
        if j + 1 < len(mots) and mots[j + 1]["r"] == rush and mots[j + 1]["s"] - mots[j]["e"] < MOTS_COLLES:
            limite_fin = fin_voix = v.creux(mots[j]["e"])
        for x, y in v.zones(debut_voix, fin_voix, valeur=False):
            if y - x <= blanc_max:
                continue
            coupe_a, coupe_b = x + marge_apres, y - regles["marge"]
            if coupe_b - coupe_a > 0.05:
                if coupe_a - courant > 0.05:
                    plans.append({"r": rush, "debut": round(courant, 3), "fin": round(coupe_a, 3)})
                courant = coupe_b
        if limite_fin - courant > 0.05:
            plans.append({"r": rush, "debut": round(courant, 3), "fin": round(limite_fin, 3)})
    gardes = [mots[k] for i, j in passages for k in range(i, j + 1)]

    def contient_un_mot(plan):
        return any(m["r"] == plan["r"] and plan["debut"] <= (m["s"] + m["e"]) / 2 <= plan["fin"] for m in gardes)

    return [p for p in plans if p["fin"] - p["debut"] >= DUREE_MORCEAU_MIN or contient_un_mot(p)]


def duree_plan(plan):
    return round((plan["fin"] - plan["debut"]) * FPS) / FPS


def mots_finaux(mots, passages, plans, corrections):
    """Les mots gardés, replacés sur le temps de la vidéo finale : {indice: mot}."""
    table, temps = [], 0.0
    for plan in plans:
        table.append((plan, temps))
        temps += duree_plan(plan)
    sortie = {}
    for i, j in passages:
        for k in range(i, j + 1):
            mot = mots[k]
            if corrections.get(str(k)) == "":
                continue
            milieu = (mot["s"] + mot["e"]) / 2
            candidats = [t for t in table if t[0]["r"] == mot["r"]]

            def distance(entree):
                return max(entree[0]["debut"] - milieu, milieu - entree[0]["fin"], 0)

            plan, origine = min(candidats, key=distance)
            duree = duree_plan(plan)
            debut = origine + min(max(mot["s"] - plan["debut"], 0), duree)
            fin = origine + min(max(mot["e"] - plan["debut"], 0), duree)
            sortie[k] = {"s": round(debut, 3), "e": round(max(fin, debut + 0.03), 3),
                         "w": corrections.get(str(k), mot["w"])}
    return sortie

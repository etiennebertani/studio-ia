"""Style Infographie minimale : fabrique la page d'animation et la liste des sons à partir d'un storyboard.

    fabrique.py storyboard.json voix.wav mots.json dossier_sortie

- storyboard.json : la signature (le pseudo de marque.json) et les scènes dans l'ordre ; chaque scène = un geste de la bibliothèque (gestes.js), ses phrases
  (texte exact de la voix), ses mots repères et ses textes affichés. Voir GESTES ci-dessous.
- mots.json : les mots calés (calage_mots.py).
Sortie : page.html (rendu par rendu.py), reperes.json (sons, pour sons.py), donnees.json (contrôles).
"""
import json, re, subprocess, sys, unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _base import commun  # noqa: E402

ICI = Path(__file__).resolve().parent
AV = 0.08            # les animations partent 80 ms avant leur mot
GESTES = {           # geste : mots repères attendus (dans l'ordre de la voix)
    "ouverture": ["ferme", "trait", "pointille"],        # le point tombe et dessine le cercle ; glisse, trait, cercle en pointillé
    "liste": ["items"],                                   # des mots s'écrivent dans le cercle (5 au plus), puis deviennent des points
    "envol": ["points"],                                  # 7 points s'envolent hors du cercle
    "personne": ["pulsations"],                           # le point de la personne apparaît au centre, pulsations sur des mots
    "sortie": ["depart", "arrivee", "retrecit"],          # le point sort du cercle puis rétrécit en trois fois
    "escalier": ["marches"],                              # escalier qui se dessine, le point tombe de marche en marche
    "anneaux": ["anneaux"],                               # anneaux en pointillé autour de la personne
    "colonne": [],                                        # colonne de phrases, un mot fort reste allumé
    "autres": ["coupe"],                                  # les autres autour, liens, coupure
    "mots_autour": ["mots"],                              # 4 mots apparaissent dans le cercle puis s'en échappent
    "final": ["repere"],                                  # halo final en pointillé, appel à l'action
}
CLES = {("ouverture", "ferme"): "s1", ("liste", "items"): "s2", ("envol", "points"): "s3", ("personne", "pulsations"): "s4",
        ("sortie", "depart"): "s5", ("sortie", "arrivee"): "s5f", ("sortie", "retrecit"): "s5b", ("escalier", "marches"): "s6",
        ("anneaux", "anneaux"): "s7", ("autres", "coupe"): "s9", ("mots_autour", "mots"): "s10", ("final", "repere"): "s11"}


def n(x):
    x = unicodedata.normalize("NFD", x.lower().replace("’", "'"))
    return re.sub(r"[^a-z0-9']", "", "".join(c for c in x if unicodedata.category(c) != "Mn"))


def charger(voix, mots_json):
    dur = float(subprocess.run([commun.outil("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(voix)],
                               capture_output=True, text=True).stdout)
    M = [(s["offsets"]["from"] / 1000, s["offsets"]["to"] / 1000, s["text"].strip())
         for s in json.load(open(mots_json, encoding="utf-8"))["transcription"] if s["text"].strip()]
    return [m for m in M if m[0] < dur - 0.3]


def phrases(sb, M):
    """Retrouve le début de chaque phrase du storyboard dans la voix."""
    W = [(a, b, n(t)) for a, b, t in M]; ptr = 0; out = []

    def trouve(mots, ptr):
        for j in range(ptr, min(len(W), ptr + 40)):
            if all(j + k < len(W) and W[j + k][2] == mots[k] for k in range(len(mots))):
                return j
    for si, sc in enumerate(sb["scenes"]):
        for ph in sc["phrases"]:
            mots = [n(x) for x in ph.split() if n(x)]; j = None
            for k in range(min(3, len(mots))):
                j = trouve(mots[k:k + 2], ptr)
                if j is not None:
                    j = max(ptr, j - k); break
            if j is None:
                raise SystemExit(f"phrase introuvable dans la voix : {ph}")
            out.append({"seg": si, "texte": ph, "debut": W[j][0], "i": j}); ptr = j + len(mots) - 1
    for k, c in enumerate(out):
        c["fin"] = W[(out[k + 1]["i"] - 1) if k + 1 < len(out) else len(W) - 1][1]
    return out, W[-1][1]


def mot(M, m, apres):
    m = n(m)
    for a, b, t in M:
        t = n(t)
        if a >= apres - .05 and (t == m or (len(m) > 4 and (t.startswith(m) or m.startswith(t)) and len(t) > 3)):
            return a
    raise SystemExit("mot repère introuvable : " + m)


def blocs(c, fin_aff, Mx):
    j = next(k for k, m in enumerate(Mx) if m[0] >= c["a"] - .02); ws = c["t"].split(); W_ = []
    for k, w in enumerate(ws):
        m = Mx[min(j + k, len(Mx) - 1)]; W_.append({"w": w, "s": m[0], "e": m[1]})
    B = []; cur = []
    for k, x in enumerate(W_):
        if cur and sum(len(y["w"]) + 1 for y in cur) + len(x["w"]) > 21:
            B.append(cur); cur = []
        cur.append(x); fin = x["w"][-1] in ".?!,;:"; trou = k + 1 < len(W_) and W_[k + 1]["s"] - x["e"] > 0.45
        if len(cur) >= 3 or fin or trou or sum(len(y["w"]) + 1 for y in cur) > 20:
            B.append(cur); cur = []
    if cur:
        B.append(cur)
    k = 0
    while k + 1 < len(B):                     # un bloc dure au moins 0,35 s, sinon il rejoint le suivant (ligne courte)
        if B[k + 1][0]["s"] - B[k][0]["s"] < 0.35 and sum(len(y["w"]) + 1 for y in B[k] + B[k + 1]) <= 24:
            B[k] = B[k] + B[k + 1]; del B[k + 1]
        else:
            k += 1
    out = []
    for q, b in enumerate(B):
        nxt = B[q + 1][0]["s"] if q + 1 < len(B) else fin_aff
        out.append({"m": [{"w": y["w"], "s": y["s"]} for y in b], "a": b[0]["s"], "b": min(b[-1]["e"] + 0.25, nxt) if q + 1 == len(B) else nxt})
    return out


def compiler(sb, M):
    ch_brut, fin = phrases(sb, M)
    scenes = sb["scenes"]; debut = [min(c["debut"] for c in ch_brut if c["seg"] == s) for s in range(len(scenes))]
    K, G, T = {}, {}, {}
    for si, sc in enumerate(scenes):
        g = sc["geste"]
        if g not in GESTES:
            raise SystemExit(f"geste inconnu : {g} (bibliothèque : {', '.join(GESTES)})")
        G[g] = debut[si]; apres = debut[si]
        for role in GESTES[g]:
            v = sc.get("mots", {}).get(role)
            if v is None:
                continue
            liste = v if isinstance(v, list) else [v]; t = []
            for m in liste:
                apres = mot(M, m, apres); t.append(apres)
            cle = CLES.get((g, role))
            if g == "ouverture":
                K.setdefault("s1", []).extend(t)
            elif cle:
                K[cle] = t if isinstance(v, list) else t[0]
        if g in ("liste", "escalier", "mots_autour"):
            T[g] = sc.get("textes", [])
        if g == "colonne":
            T["mot_fort"] = sc.get("mot_fort", "")
            K["s8"] = [c["debut"] for c in ch_brut if c["seg"] == si]
        if g == "final":
            K.setdefault("s11", []).append([c["debut"] for c in ch_brut if c["seg"] == si][-1])
    ch = []
    for c in ch_brut:
        sc = scenes[c["seg"]]; i = sum(1 for x in ch if x["seg"] == c["seg"]); cache = sc.get("sous_titres_caches", [])
        ch.append({"seg": c["seg"], "i": i, "t": c["texte"].lower(), "a": c["debut"], "f": c["fin"],
                   "cache": cache == "toutes" or i in cache})
    for k, c in enumerate(ch):
        nxt = ch[k + 1]["a"] if k + 1 < len(ch) else fin + 0.8
        c["b"] = nxt if (k + 1 < len(ch) and ch[k + 1]["seg"] == c["seg"]) else min(nxt, c["f"] + 0.6)
    sous = [b for c in ch if not c["cache"] for b in blocs(c, c["b"], M)]
    seg_col = next((si for si, sc in enumerate(scenes) if sc["geste"] == "colonne"), None)
    seg_esc = next((si for si, sc in enumerate(scenes) if sc["geste"] == "escalier"), None)
    col = [c for c in ch if c["seg"] == seg_col]
    st5 = [c["a"] for c in ch if c["seg"] == seg_esc][:4]
    dec = lambda x: x - AV if x > 0.1 else x                                                    # noqa: E731
    K = {k: ([x - AV for x in v] if isinstance(v, list) else v - AV) for k, v in K.items()}
    G = {g: dec(v) for g, v in G.items()}
    for g in GESTES:
        G.setdefault(g, 1e9)                          # geste absent : il ne se déclenche jamais
    return {"signature": sb.get("signature", ""), "G": G, "K": K, "T": T, "debuts": [dec(x) for x in debut], "st5": [x - AV for x in st5],
            "col": [dict(c, a=c["a"] - AV) for c in col], "sous": sous, "FIN": fin}


def sons(D):
    """Les sons de chaque geste (règles de la fiche du style). Niveaux : accent, petit, tres_petit."""
    G, K = D["G"], D["K"]; R = []
    add = lambda t, son, niv, **kw: R.append({"t": round(t, 4), "son": son, "niveau": niv, **kw})      # noqa: E731
    MW = [m for b in D["sous"] for m in b["m"]]
    if G["ouverture"] < 1e8:
        IA = min(range(len(MW)), key=lambda j: abs(MW[j]["s"] - K["s1"][1] - .08))
        GL0 = MW[IA - 1]["s"] - .08; PAS = [MW[IA + j]["s"] for j in range(4)]; PT0 = MW[IA + 4]["s"] - .08; PT1 = MW[IA + 5]["s"] - .08
        add(0.2, "ui:zen/drop", "accent"); add(0.23, "ui:zen/expand", "accent"); add(K["s1"][0], "ui:zen/select", "petit")
        add(GL0 + .03, "rsfx:whoosh.air", "accent"); add(PAS[0] - .24, "ui:zen/swipe", "accent"); add((PAS[0] - .24 + PT0) / 2, "rsfx:whoosh.soft", "petit")
        for k in range(6):
            add(PT0 + (PT1 - PT0) * k / 5, f"gouttes/goutte-{k + 1}.wav", "accent" if k in (0, 5) else "petit")
    if G["liste"] < 1e8:
        add(G["liste"] + .3, "ui:zen/collapse", "accent"); add(G["liste"] + .45, "montees/montee-A.wav", "accent")
        for t in K.get("s2", [])[:5]:
            add(t, "rsfx:tick.clock", "petit")
    if G["envol"] < 1e8:
        add(G["envol"] - .2, "rsfx:whoosh.soft", "petit")
        for t in K.get("s3", []):
            add(t, "rsfx:pop.short", "petit")
    if G["personne"] < 1e8:
        add(G["personne"] + .15, "ui:minimal/select", "accent")
    if G["sortie"] < 1e8:
        add(K["s5"] + .15, "rsfx:whoosh.air", "accent")
        for t, f in zip(K.get("s5b", []), (1.0, .9, .8)):
            add(t, "ui:zen/deselect", "petit", hauteur=f)
    if G["escalier"] < 1e8:
        add(G["escalier"] - .6 + .08, "rsfx:whoosh.air", "petit")
        for t in D["st5"]:
            add(t - .05, "ui:zen/swipe", "petit")
        m = K.get("s6", [])
        if m:
            add(m[0], "rsfx:tock.wood", "accent"); add(m[-1], "rsfx:tock.wood", "accent")
            for t in m[1:3]:
                add(t, "rsfx:tock.wood", "accent")
    if G["anneaux"] < 1e8:
        add(G["anneaux"] - .3, "rsfx:whoosh.air", "petit")
    if G["colonne"] < 1e8:
        add(G["colonne"] - .3, "rsfx:whoosh.soft", "accent")
        for t in K.get("s8", []):
            add(t, "ui:minimal/press", "petit")
    if G["autres"] < 1e8:
        add(G["autres"] - .4, "ui:zen/open", "accent"); add(K["s9"][0], "ui:minimal/disconnect", "accent")
        for k in range(6):
            add(G["autres"] + .25 + k * .12, "rsfx:pop.short", "tres_petit")
    if G["mots_autour"] < 1e8:
        for t in K.get("s10", []):
            add(t, "rsfx:whoosh.swipe", "petit")
    if G["final"] < 1e8:
        s11 = K["s11"]; add(s11[-1], "rsfx:bell.ding", "accent")
        for k, f in enumerate((0, .15, .3, .45, .6, .75)):
            add(s11[1] + 1.2 * (1 - (1 - f) ** (1 / 3)), f"gouttes/goutte-{k + 1}.wav", "accent" if k in (0, 5) else "petit")
    return sorted(R, key=lambda r: r["t"])


def main():
    sb_p, voix, mots_json, sortie = sys.argv[1:5]
    sb = json.load(open(sb_p, encoding="utf-8")); M = charger(voix, mots_json); D = compiler(sb, M)
    out = Path(sortie); out.mkdir(parents=True, exist_ok=True)
    polices = (ICI.parent.parent / "polices").as_uri()
    js = (ICI / "gestes.js").read_text(encoding="utf-8").replace("__DATA__", json.dumps(D, ensure_ascii=False))
    html = ('<!doctype html><meta charset=utf-8><style>@font-face{font-family:P;src:url("%s/Poppins-Regular.ttf");font-weight:400}'
            '@font-face{font-family:P;src:url("%s/Poppins-Medium.ttf");font-weight:500}html,body{margin:0}</style>'
            '<canvas id=c width=1080 height=1920></canvas><script>' % (polices, polices)) + js + "</script>"
    (out / "page.html").write_text(html, encoding="utf-8")
    (out / "reperes.json").write_text(json.dumps(sons(D), ensure_ascii=False, indent=0), encoding="utf-8")
    (out / "donnees.json").write_text(json.dumps(D, ensure_ascii=False), encoding="utf-8")
    print(len(sb["scenes"]), "scènes,", len(D["sous"]), "sous-titres, durée", round(D["FIN"] + 0.8, 1), "s")


if __name__ == "__main__":
    main()

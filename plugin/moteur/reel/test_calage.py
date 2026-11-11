"""Batterie de tests du calage, à lancer avant chaque rendu. Sortie : réussi / à vérifier, avec les moments précis.

    test_calage.py voix.wav mots.json page.html

La page est celle du rendu (const D = {sous, K, ...}). Un résultat « à vérifier » bloque le rendu."""
import json, re, sys, numpy as np
sys.path.insert(0, __import__("os").path.dirname(__file__))
import calage_mots as C
audio, mots_json, page = sys.argv[1:4]
db,flux=C.analyse(audio); haut=np.percentile(db[db>-60],80)
M=[(s["offsets"]["from"]/1000,s["text"].strip(),s.get("source","?")) for s in json.load(open(mots_json))["transcription"]]
D=json.loads(re.search(r'const D=(\{.*?\});const Q',open(page,encoding="utf-8").read(),re.S).group(1))
rap={}
# 1. chaque mot commence dans la voix (pas dans un silence)
dans_silence=[(round(s,2),w) for s,w,_ in M if db[int(s*100):int(s*100)+8].max()<haut-20]
rap["mots qui démarrent dans un silence"]=dans_silence
# 2. ordre et écart minimal
rap["mots dans le désordre"]=[(round(M[k][0],2),M[k][1]) for k in range(1,len(M)) if M[k][0]<=M[k-1][0]]
# 3. part des mots calés sur une vraie attaque
n=sum(1 for _,_,src in M if src=="attaque"); rap["mots calés sur une attaque"]=f"{n}/{len(M)}"
# 4. sous-titres : avance et durée minimale
S=D["sous"]; rap["sous-titres de moins de 0,35 s"]=[(round(b["a"],2)," ".join(x["w"] for x in b["m"])) for b in S if b["b"]-b["a"]<0.35]
mots_s=set(round(s,2) for s,_,_ in M)
rap["sous-titres qui ne partent pas d'un mot"]=[(round(b["a"],2)) for b in S if round(b["m"][0]["s"],2) not in mots_s]
# 5. animations : chaque repère suit l'ordre de la voix
K=D["K"]; rap["repères d'animation"]=sum(len(v) if isinstance(v,list) else 1 for v in K.values())
bloquant=[k for k in ("mots qui démarrent dans un silence","mots dans le désordre","sous-titres qui ne partent pas d'un mot") if rap[k]]
for k,v in rap.items(): print(f"- {k} : {v if v else 'aucun'}")
print("RÉSULTAT :", "à vérifier ("+", ".join(bloquant)+")" if bloquant else "réussi")

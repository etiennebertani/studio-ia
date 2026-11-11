"""Minutage chirurgical des mots, pour sous-titres, animations et sons.

Règle (calibrée le 11 novembre 2026 sur 14 mots mesurés à la main : erreur moyenne 0,045 s, pire 0,14 s) :
1. Temps fin de whisper (option -dtw, sans flash attention -nfa).
2. Mot dont le premier morceau est long (6 lettres ou plus) : le temps fin tombe dans le mot, donc on prend
   la première attaque franche (creux d'énergie ou rupture du spectre) après la fin du mot précédent.
3. Sinon : temps fin moins 0,04 s, recalé sur l'attaque d'énergie la plus proche (fenêtre -0,08 / +0,12 s).
4. Toujours dans l'ordre, au moins 0,03 s entre deux mots.

    calage_mots.py voix.wav dtw.json sortie.json [--verite verite.json]
"""
import json, sys, numpy as np, subprocess
from _base import ffmpeg
LONG, FLUX_MIN, DECALAGE, AVANT, APRES, COLLE = 6, 0.6, 0.04, 0.08, 0.12, 0.03
def analyse(audio):
    sr=16000; r=subprocess.run([ffmpeg(),"-v","error","-i",audio,"-ac","1","-ar",str(sr),"-f","s16le","-"],capture_output=True).stdout
    a=np.frombuffer(r,dtype=np.int16).astype(float)/32768; hop,win=160,512
    fr=np.lib.stride_tricks.sliding_window_view(np.pad(a,(0,win)),win)[::hop]*np.hanning(win)
    L=np.log1p(np.abs(np.fft.rfft(fr,axis=1))*100); flux=np.concatenate([[0],np.maximum(0,np.diff(L,axis=0)).sum(1)]); flux/=np.percentile(flux,99)
    db=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9); return db,flux
def attaques(db,flux,avec_spectre):
    haut=np.percentile(db[db>-60],80); out=set()
    for i in range(2,len(db)):
        if db[i]>=haut-11 and db[i-1]<haut-11 and min(db[max(0,i-6):i])<haut-14: out.add(i)
        if avec_spectre and flux[i]>=FLUX_MIN and flux[i]>=flux[i-1] and flux[i]>=flux[min(len(flux)-1,i+1)] and db[i]>haut-25: out.add(i)
    return np.array(sorted(out))*0.01
def mots_dtw(path):
    d=json.load(open(path)); toks=[t for s in d["transcription"] for t in s["tokens"] if not t["text"].startswith("[")]
    M=[]
    for t in toks:
        tt=t["t_dtw"]/100
        if t["text"].startswith(" ") or not M: M.append({"w":t["text"].strip(),"dtw":tt,"fin_dtw":tt,"premier":len(t["text"].strip())})
        else: M[-1]["w"]+=t["text"]; M[-1]["fin_dtw"]=tt
    return [m for m in M if any(c.isalnum() for c in m["w"])]
def caler(M,db,flux):
    AE,AF=attaques(db,flux,False),attaques(db,flux,True); prec=-1.0; prec_fin=-1.0; out=[]
    for m in M:
        if m["premier"]>=LONG and prec_fin>0:
            c=AF[(AF>=prec_fin)&(AF<=m["dtw"]+.06)&(AF>prec+COLLE)]; s=float(c[0]) if len(c) else prec_fin+COLLE; m["source"]="attaque" if len(c) else "suite"
        else:
            s=m["dtw"]-DECALAGE; c=AE[(AE>=s-AVANT)&(AE<=s+APRES)&(AE>prec+COLLE)]
            if len(c): s=float(c[np.argmin(np.abs(c-s))]); m["source"]="attaque"
            else: m["source"]="temps fin"
        s=max(s,prec+COLLE); m["s"]=round(s,3); out.append(m); prec=s; prec_fin=m["fin_dtw"]
    return out
if __name__=="__main__":
    audio,dtw,dst=sys.argv[1:4]; db,flux=analyse(audio); M=caler(mots_dtw(dtw),db,flux)
    json.dump({"transcription":[{"offsets":{"from":int(m["s"]*1000),"to":int((M[k+1]["s"] if k+1<len(M) else m["s"]+0.4)*1000)},"text":" "+m["w"],"source":m["source"]} for k,m in enumerate(M)]},open(dst,"w"),ensure_ascii=False)
    if "--verite" in sys.argv:
        V=json.load(open(sys.argv[sys.argv.index("--verite")+1])); e=[abs(M[int(k)]["s"]-v) for k,v in V.items()]
        print("vérité terrain :",len(e),"mots, erreur moyenne",round(float(np.mean(e)),3),"s, pire",round(float(max(e)),3),"s")
    print("mots",len(M))

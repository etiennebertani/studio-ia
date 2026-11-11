"""Volume final : intégré cible, plafond fixe, limiteur qui anticipe les crêtes. Ne compresse rien d'autre.

    master.py entree.wav sortie.wav -18
"""
import sys, subprocess, numpy as np
from _base import ffmpeg
sr=48000
def lire(p):
    r=subprocess.run([ffmpeg(),"-v","error","-i",p,"-ac","2","-ar",str(sr),"-f","f32le","-"],capture_output=True).stdout
    return np.frombuffer(r,dtype=np.float32).reshape(-1,2).astype(np.float64)
def lufs(x):
    p=subprocess.run([ffmpeg(),"-nostats","-f","f32le","-ar",str(sr),"-ac","2","-i","-","-af","ebur128=framelog=quiet","-f","null","-"],input=x.astype(np.float32).tobytes(),capture_output=True).stderr.decode()
    return float([l for l in p.splitlines() if l.strip().startswith("I:")][-1].split()[1])
def limiteur(x,plafond_db=-3.0,anticipe=0.005,relache=0.08):
    c=10**(plafond_db/20); pk=np.abs(x).max(1); g=np.minimum(1.0,c/np.maximum(pk,1e-9))
    n=int(anticipe*sr); from numpy.lib.stride_tricks import sliding_window_view as sw
    gp=np.concatenate([g,np.ones(n)]); gmin=sw(gp,n+1).min(1)[:len(g)]          # anticipe : la baisse commence avant la crête
    r=np.exp(-1/(relache*sr)); out=np.empty_like(gmin); s=1.0
    for i,v in enumerate(gmin):
        s=v if v<s else r*s+(1-r)*v; out[i]=s
    return x*out[:,None], int((gmin<0.999).sum())
src,dst,cible=sys.argv[1],sys.argv[2],float(sys.argv[3])
x=lire(src); x*=10**((cible-lufs(x))/20)
for _ in range(2):
    y,n=limiteur(x); x*=10**((cible-lufs(y))/20)
y,n=limiteur(x)
subprocess.run([ffmpeg(),"-y","-v","error","-f","f32le","-ar",str(sr),"-ac","2","-i","-","-c:a","pcm_s24le",dst],input=y.astype(np.float32).tobytes(),check=True)
print("intégré",round(lufs(y),1),"LUFS | crête",round(20*np.log10(np.abs(y).max()),2),"dBFS | part du temps limitée",round(100*n/len(y),2),"%")

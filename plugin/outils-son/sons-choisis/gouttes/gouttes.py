"""Gouttes d'eau synthétisées (code maison, aucun échantillon tiers) : une sinusoïde dont la hauteur
monte très vite, comme une bulle qui se referme, avec une petite queue d'écho. Libre de droits."""
import numpy as np, wave, sys
from pathlib import Path
sr=48000
def goutte(f0, monte=1.7, duree=.16, graine=0):
    rng=np.random.default_rng(graine); t=np.arange(int(duree*sr))/sr
    f=f0*(1+(monte-1)*(1-np.exp(-t/.010)))
    x=np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t/.028)*(1-np.exp(-t/.0008))
    x+=.18*np.sin(4*np.pi*np.cumsum(f)/sr)*np.exp(-t/.012)
    queue=rng.standard_normal(int(.12*sr))*np.exp(-np.arange(int(.12*sr))/sr/.03)*.002
    x=np.convolve(x,np.r_[1,np.zeros(int(.019*sr)),.22,np.zeros(int(.023*sr)),.12])[:len(t)+len(queue)]
    x[:len(queue)]+=0; x/=np.abs(x).max(); return x
def ecrire(p,x):
    w=wave.open(str(p),"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x*.9*32767).astype(np.int16).tobytes()); w.close()
if __name__=="__main__":
    d=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent
    for k,(f0,mo) in enumerate([(820,1.7),(980,1.6),(760,1.8),(1100,1.55),(900,1.7),(1250,1.5)]):
        ecrire(d/f"goutte-{k+1}.wav",goutte(f0,mo,graine=k))
    print("6 gouttes")

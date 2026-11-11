"""Revue des moments sans son : Real SFX repère les mouvements à l'image, on garde ceux qui n'ont pas de son.

    revue_sons.py video_muette.mp4 reperes.json dossier_travail [--zone 58,320,960,800]

--zone limite la recherche à l'animation (sans les sous-titres). Sortie : la liste des moments sans son, avec l'image
de chacun. Le Studio regarde chaque image, garde les vrais manques, propose la nature du son ; la personne valide.
"""
import argparse, json, subprocess, sys
from _base import SONS

def main():
    a = argparse.ArgumentParser(); a.add_argument("video"); a.add_argument("reperes"); a.add_argument("travail")
    a.add_argument("--zone", default="58,320,960,800"); a.add_argument("--ecart", type=float, default=0.3); o = a.parse_args()
    script = SONS / "real-sfx" / "scripts" / "find_moments.py"
    subprocess.run([sys.executable, str(script), o.video, "--out", f"{o.travail}/moments", "--roi", o.zone], check=True, capture_output=True)
    M = json.load(open(f"{o.travail}/moments/moments.json")); mom = M["moments"] if isinstance(M, dict) else M
    poses = [r["t"] for r in json.load(open(o.reperes, encoding="utf-8"))]
    trous = [{"t": m["t"], "genre": m["kind"], "force": m["strength"], "image": f"{o.travail}/moments/{m['frame']}"}
             for m in sorted(mom, key=lambda m: m["t"]) if not any(abs(t - m["t"]) < o.ecart for t in poses)]
    print(json.dumps({"moments": len(mom), "sans_son": trous}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()

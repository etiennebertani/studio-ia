"""Veille sur les mises à jour du module d'effets que Théo offre (plugin editeur, dossier skills/studio).

    python3 effets_veille.py                 dit ce qui a changé chez Théo depuis notre dernière reprise
    python3 effets_veille.py --diff <fichier> montre le détail d'un fichier (chemin relatif au module)
    python3 effets_veille.py --noter          note que la version actuelle de Théo a été examinée et reprise

Le module est intégré chez nous (plugin/effets/kit/) et on l'adapte librement : rien n'est jamais écrasé
automatiquement. La veille compare trois versions de chaque fichier :
- celle de Théo au moment de notre dernière reprise (commit noté dans plugin/effets/SOURCE.json),
- celle de Théo aujourd'hui (~/.editeur, mis à jour par son plugin),
- la nôtre.
Pour chaque fichier changé chez Théo, elle dit si on l'a aussi modifié chez nous (« à fusionner à la main ») ou non
(« reprise directe possible »). On choisit ensemble ce qu'on reprend, puis --noter.
Licence MIT de Justyn Berkovits : kit/LICENSE reste toujours en place.
"""
import argparse, datetime, json, subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
NOTRE = PLUGIN / "effets" / "kit"
SOURCE = PLUGIN / "effets" / "SOURCE.json"
DEPOT = Path.home() / ".editeur"
SOUS = "skills/studio"

def git(*a):
    return subprocess.run(["git", "-C", str(DEPOT), *a], capture_output=True, text=True).stdout

def chez_theo(commit, chemin):
    r = subprocess.run(["git", "-C", str(DEPOT), "show", f"{commit}:{SOUS}/{chemin}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None

def main():
    p = argparse.ArgumentParser(); p.add_argument("--diff"); p.add_argument("--noter", action="store_true"); a = p.parse_args()
    src = json.loads(SOURCE.read_text())
    base = src["commit_editeur"].split()[0]
    tete = git("log", "-1", "--format=%H").strip()
    if a.diff:
        print(subprocess.run(["git", "-C", str(DEPOT), "diff", base, tete, "--", f"{SOUS}/{a.diff}"], capture_output=True, text=True).stdout or "aucun changement chez Théo")
        return
    if a.noter:
        src["commit_editeur"] = git("log", "-1", "--format=%H %ci").strip()
        src["version"] = (DEPOT / SOUS / "VERSION").read_text().strip()
        src["examine_le"] = datetime.date.today().isoformat()
        SOURCE.write_text(json.dumps(src, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps({"ok": True, "note": src["commit_editeur"]}, ensure_ascii=False)); return
    lignes = [l.split("\t") for l in git("diff", "--name-status", base, tete, "--", SOUS).splitlines() if l]
    changes = []
    for etat, *chemins in lignes:
        chemin = chemins[-1][len(SOUS) + 1:]
        avant = chez_theo(base, chemin)
        notre = (NOTRE / chemin).read_bytes() if (NOTRE / chemin).is_file() else None
        modifie_chez_nous = avant is not None and notre is not None and notre != avant
        changes.append({"fichier": chemin, "chez_theo": {"A": "ajouté", "M": "modifié", "D": "supprimé"}.get(etat[0], etat),
                        "action": "à fusionner à la main" if modifie_chez_nous else "reprise directe possible"})
    print(json.dumps({"version_reprise": src["version"], "version_theo": (DEPOT / SOUS / "VERSION").read_text().strip(),
                      "commits_depuis": git("log", "--oneline", f"{base}..{tete}", "--", SOUS).splitlines(),
                      "fichiers": changes}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()

# Infographie minimale : écrire le storyboard d'un reel

Le moteur (`moteur/reel/infographie/`) assemble des **gestes** sur les mots de la voix. Le Studio écrit un storyboard pour chaque script, le montre à la personne, puis lance la fabrique. Les règles du style (`infographie-minimale-reel.md`) et les règles fondamentales s'appliquent toujours.

## 1. Le storyboard

```json
{"titre": "…", "signature": "<pseudo de marque.json>", "scenes": [
  {"geste": "ouverture", "phrases": ["texte exact de la voix", "…"], "mots": {"ferme": "…", "trait": "…", "pointille": "…"}},
  …
]}
```

- **phrases** : le texte exact dit dans la voix, découpé en phrases courtes, dans l'ordre. Toutes les phrases de la voix appartiennent à une scène.
- **mots** : les mots repères du geste, dans l'ordre où ils sont dits. Une animation arrive en butée sur son mot.
- **textes** : ce que le geste écrit à l'écran (liste, marches, mots autour), avec les mots de la personne.
- **sous_titres_caches** : les numéros des phrases (à partir de 0) dont les sous-titres se cachent parce que l'écran les écrit déjà, ou `"toutes"`.

## 2. La bibliothèque de gestes

| Geste | Ce qu'on voit | Mots repères | Pour illustrer |
|---|---|---|---|
| `ouverture` | le point tombe et dessine le cercle ; il glisse, tire un trait, un cercle en pointillé se dessine, les deux fusionnent | `ferme` (le cercle se ferme), `trait` (début du trait), `pointille` | une opposition de départ : deux catégories, deux mondes |
| `liste` | des mots s'écrivent dans le cercle, puis deviennent des points | `items` (5 mots + le mot qui conclut) | ce qui est dedans, ce qu'on possède |
| `envol` | 7 points s'envolent hors du cercle | `points` (7 mots) | ce qui échappe, ce qui est dehors |
| `personne` | le point de la personne apparaît au centre, pulse | `pulsations` (3 mots) | la personne, sa force |
| `sortie` | le point sort du cercle puis rétrécit en trois fois | `depart`, `arrivee`, `retrecit` (3 mots) | perdre sa force hors de sa zone |
| `escalier` | un escalier se dessine, le point tombe de marche en marche | `marches` (4 mots), `textes` | une chute, une conséquence en étapes |
| `anneaux` | des anneaux en pointillé tournent autour de la personne | `anneaux` (2 mots) | se recentrer, l'attention |
| `colonne` | une colonne de phrases ; un mot fort reste allumé | `mot_fort` | une répétition, une litanie |
| `autres` | les autres apparaissent autour, liés à la personne, puis les liens se coupent | `coupe` (2 mots) | les autres, se détacher |
| `mots_autour` | 4 mots apparaissent dans le cercle puis s'en échappent | `mots` (4 mots), `textes` | ce qui ne dépend pas de nous |
| `final` | pulsations, halo final en pointillé, appel à l'action | `repere` (2 mots) | la conclusion et l'appel à l'action |

Chaque geste a déjà ses sons (table du style) : ils se posent tout seuls dans `reperes.json`. Un geste absent du storyboard ne s'affiche jamais.

## 3. Choisir les gestes

1. Découper le script en idées ; une idée = une scène.
2. Pour chaque idée, prendre le geste dont la colonne « Pour illustrer » correspond au sens. Le sens d'abord, jamais la décoration.
3. Garder la continuité : une seule forme principale (le cercle) qui se transforme d'une scène à l'autre.
4. Si aucune idée n'a de geste juste, le dire à la personne et proposer un nouveau geste : on le dessine, on le valide avec elle, puis il entre dans la bibliothèque (code dans `gestes.js`, sons dans `fabrique.py`, une ligne dans ce tableau).
5. Montrer le storyboard à la personne (scène, phrases, geste, mots repères) avant de fabriquer.

## 4. Fabriquer

```
$PY "$M/reel/infographie/fabrique.py" storyboard.json voix.wav mots.json <travail>
$PY "$M/reel/infographie/rendu.py" <travail>/page.html noir <travail>/noir-muet.mp4
$PY "$M/reel/sons.py" <travail>/reperes.json voix.wav <travail>/son.wav
```

Puis les contrôles des règles fondamentales (calage, safe zone, volume, revue des moments sans son, origine), et le montage final : `ffmpeg -i noir-muet.mp4 -i son.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest`.

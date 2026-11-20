# Convention de nommage du Studio

Le moteur l'applique avec `moteur/nommage.py`. C'est là que se trouve la liste des types.

```
aa-mm-client-type-sujet-numéro.ext
```

| Champ | Règle |
|---|---|
| `aa-mm` | année et mois de **validation**, sur 2 chiffres. Le mois de publication se note à part, dans la banque de contenu. |
| `client` | nom court, toujours écrit pareil. Il se trouve dans `client` de `marque.json`. |
| `type` | `post`, `story`, `reel-nocc`, `reel-cc`, `video-nocc`, `video-cc`, `broll`, `visuel`, `carrousel`. Liste fermée. |
| `sujet` | description courte. |
| `numéro` | version de ce contenu dans le mois, sur 2 chiffres. |

Un carrousel ajoute le numéro de slide : `26-11-marie-carrousel-mon-sujet-01-slide-01.jpg`.
Un carrousel en plusieurs variantes range chacune dans son dossier de `final/` (`final/noir/`, `final/blanc/`), avec `texte.txt` et `legendes.txt` à côté. Les slides portent une date de prise de vue décalée d'une seconde, dans l'ordre (`moteur/ranger_variantes.py`).

## Code de format

Le sujet commence toujours par le code du format. Le type reste dans la liste fermée.

- Reels : `yap`, `yapp` (Yap+), `fce` (face caméra éducatif), `vlog`, `clean`, `os` (one shot), `tenshots`, `infographie` (reel animé), `temoignage` (témoignage vidéo).
- Carrousels : `tweet`, `txt` (texte), `txti` (texte + image), `punchline`, `infographie`.

Exemples : `26-11-marie-reel-cc-yapp-mon-sujet-01.mp4`, `26-11-marie-carrousel-txti-mon-sujet-01-slide-01.jpg`.

## Écriture

Toujours en minuscules, séparé par des tirets. Accents autorisés. Aucun espace, underscore, point ni autre caractère spécial dans le nom. Un client s'écrit toujours de la même façon : on compare les noms sans tenir compte des accents.

## Ce qui suit la convention

Les fichiers finaux (reels, carrousels, slides, posts) et les extraits de b-roll de 30 secondes.

## Ce qui garde son nom

Les dossiers (numéro et titre), les rushs, les musiques, les images ajoutées aux vidéos, les photos sources, `texte.txt` et `legendes.txt`.

Une déclinaison d'un contenu le même mois prend le numéro suivant.

## B-roll

Le type reste `broll`. Pour un client restaurant uniquement, le sujet commence par `1-cuisine`, `2-boissons`, `3-salle` ou `4-dehors`.

## Avant de renommer des fichiers existants

Lister ce qui serait renommé, faire valider, puis agir. Ne jamais étendre la liste des types sans décision explicite.

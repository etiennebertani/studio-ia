# Style « Infographie minimale » : le reel animé

Règles propres à ce style, en plus de `ressources/montage-regles-fondamentales.md`. Validées par Etienne le 11 novembre 2026 sur le reel « Sphère de contrôle » (version noire, test 11 : exemple de référence).

## 0. Le moteur
Le reel se fabrique à partir d'un storyboard : voir `infographie-storyboard.md` (bibliothèque de gestes, choix des gestes, commandes). Exemple de référence : `moteur/reel/infographie/exemples/sphere-de-controle.storyboard.json`, qui redonne le reel validé à l'image près.

## 1. Le principe
Une voix off ; des formes géométriques simples (cercle, point, trait, pointillé, escalier) qui illustrent chaque idée en se transformant l'une en l'autre ; des sous-titres ; aucune image. Deux thèmes : noir (fond #16181c, traits #f5f5f5) et blanc (fond #ffffff, traits #0f1010).

## 2. La grille
- Format 1080 × 1920, 60 images par seconde, flou de mouvement par 4 sous-images.
- Centre de l'action : x 540, y 760 ; cercle principal de rayon 260 ; tout reste centré comme un seul bloc lisible.
- Sous-titres centrés à y 1175 : 48 px, Poppins Regular sur noir, Medium sur blanc ; largeur au plus 598 px ; une ligne, au plus 3 mots, coupée avant 21 caractères (24 si on fusionne deux blocs trop courts).
- Signature @ de la personne à y 1440, 36 px, opacité 0,55. Barre de progression « chemin » à y 300.
- Épaisseurs : trait 5 px (noir) ou 6 px (blanc), pointillés 3 / 3,5 px.
- Cercle et point sont réservés à la personne (voir la grille du style minimal du carrousel).

## 3. Le début (hook)
- Quelque chose bouge dès la première image : le point est déjà là et tombe.
- Le point qui tombe devient la pointe du crayon et dessine le premier cercle pendant la première phrase ; le cercle se ferme sur le mot clé.
- Chaque mouvement des 10 premières secondes a son son, sans trou de tempo.

## 4. Le mouvement
- Arriver lentement, repartir net : arrivée sur une longue décélération, sortie 40 à 50 % plus courte, en un seul geste.
- Ressort discret (environ 5 % de dépassement) pour la position et la taille ; jamais pour l'opacité.
- Une forme posée reste immobile ; seuls des éléments secondaires (pointillés, orbites) bougent lentement.
- Métamorphose continue : une forme devient la suivante, fusionne ou s'échappe ; jamais de coupure nette ni de fondu entre deux compositions chargées.
- Deux formes qui se rejoignent partagent une seule courbe (même départ, même fin) : pas de poursuite ni de rebond décalé.
- Chute : le point roule jusqu'au bord, tombe tout droit (gravité), se pose avec un petit rebond.
- Un trait se tire d'un seul geste fluide, jamais par à-coups.

## 5. Le son
- Réflexe : chercher d'abord un vrai son sur Openverse (puis Real SFX, uisfx, reel-sfx), faire écouter des exemples, ne fabriquer qu'en dernier recours. Les auteurs à créditer sont signalés au moment de la légende.
 (une famille : uisfx « zen » et « minimal », reel-sfx ; tout en CC0)
| Mouvement | Son | Placement |
|---|---|---|
| Un point tombe et se pose | zen/drop | à l'impact |
| Un cercle plein se dessine | zen/expand | au départ du tracé (le point qui tombe devient la pointe du crayon) |
| Un cercle en pointillé se dessine | série de 6 gouttes d'eau (« Single Water Drop », paespedro, CC0, via Openverse : `outils-son/sons-choisis/gouttes`) | une goutte par groupe de pointillés, accent sur la première et la dernière |
| Un trait se tire | zen/swipe au départ + whoosh.soft léger | le trait se tire d'un seul geste fluide ; pic du souffle au milieu du trait |
| Une forme glisse ou se déplace | whoosh.air | pic du souffle sur l'instant le plus rapide |
| Deux formes fusionnent | zen/collapse | au contact |
| Un point se pose sur une marche, une butée | tock.wood | à l'impact |
| Des points s'envolent | pop.short | à l'arrivée, accent sur le premier et le dernier |
| Un mot apparaît (liste, colonne) | tick.clock / minimal/press | sur le mot |
| Un cercle s'ouvre et s'échappe | whoosh.soft | pic au plus rapide |
| Des liens se coupent | minimal/disconnect | à la coupure |
| Fin, appel à l'action | bell.ding | sur le mot |

- Le même mouvement garde toujours le même son.
- Le hook (10 premières secondes) : chaque mouvement est sonorisé, sans trou de tempo.
- Niveaux : accents 8 dB sous la voix, petits sons 13 dB sous la voix, atténuation 3 dB quand la voix parle ; master -18 LUFS (réglages complets dans les règles fondamentales).

### La logique du choix (voir aussi les règles fondamentales)
- **Le mouvement d'abord** : sa nature (tracé, glissement, traversée, chute, fusion, apparition) donne la famille du son (table ci-dessus). Toute forme qui traverse l'écran a son souffle, pic sur l'instant le plus rapide.
- **Puis l'énergie du script et du message** : un passage calme garde des sons courts et feutrés ; une montée de tension vers une révélation peut recevoir une montée (riser, swell inversé) qui s'arrête net sur le mot révélé. À l'occasion, quand ça s'y prête, jamais en série.
- **Puis le dynamisme du montage** : plus le rythme est serré, plus les sons sont courts et bas.
- **Le but** : l'immersion, le ressenti physique du mouvement (kinesthésique, VAKOG), sans rien d'artificiel. Le son doit transpirer la sobriété : s'il s'entend comme un effet, il est trop fort ou de trop.
- **Revue automatique après chaque rendu** : Real SFX (find_moments, zone de l'animation seulement) liste les mouvements ; ceux qui n'ont pas de son sont regardés image par image ; le Studio propose la nature de chaque son manquant d'après cette logique, et la personne valide avant l'ajout.
- **Calage de chaque son (Real SFX + règles Hyperframes)** : le point du son qui se pose sur l'image est mesuré, jamais supposé. Son de mouvement (souffle, swipe, montée) : son arrivée, ou son pic s'il monte vers un sommet ; le pic tombe sur l'instant le plus rapide, une montée s'arrête net à l'arrivée du mouvement. Autres sons : leur début audible, sur l'impact ou le départ du mouvement.
- **Source des sons** : Openverse en priorité (CC0, ou CC BY avec auteur noté pour la légende), puis Real SFX, uisfx, reel-sfx.

Sons ajoutés après validation : montée « reverse fx 9 » (neezen., CC0, `outils-son/sons-choisis/montees`) sur un zoom de cercle, qui s'arrête net à l'arrivée.

## 6. Les contrôles propres à ce style
- Les repères d'animation (apparitions, arrivées en butée, chutes) se calculent sur les mots calés, avec 0,08 s d'avance.
- Après rendu : `controle_zone.py` (safe zone), `test_calage.py`, `master.py`, puis `revue_sons.py` limité à la zone de l'animation (x 58 à 1018, y 320 à 1120) pour ne pas compter les sous-titres.

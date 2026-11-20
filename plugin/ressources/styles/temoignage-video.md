# Style : Témoignage vidéo (reel)

Validé par Etienne le 18 novembre 2026 sur un vrai témoignage client (exemple dans 07. Références / Exemples de montage de la personne qui l'a validé).
Les règles fondamentales du montage (`montage-regles-fondamentales.md`) s'appliquent toujours ; celles-ci s'ajoutent.

## Ce que c'est
Une personne raconte son expérience (une cliente, un élève, un partenaire), tirée d'une visio ou d'une interview.
On garde seulement ses mots, sans voix off ni texte ajouté, en 9:16, en moins d'une minute.

## 1. Le texte, avant tout montage
1. **Repérer le passage** : sous-titres de la visio s'ils existent (ils disent qui parle), sinon transcription.
2. **Transcript complet mot par mot** de tout ce que dit la personne sur le sujet, avec les questions en repère et les
   temps. Livré à la personne, même s'il dépasse la minute : il sert à d'autres contenus. Un mot mal entendu est
   corrigé seulement si le sens ne fait aucun doute, avec la forme entendue entre crochets ; sinon il est marqué (?).
3. **Script proposé**, un passage par ligne, chacun avec la raison de son choix, et ce qui est laissé de côté avec
   la raison. Rien n'est monté avant la validation du script.
4. **Accord de la personne filmée** : le noter (moment de la visio ou message). Sans accord, on ne monte pas.

## 2. La construction du script
- **Moins d'une minute.** Les blancs entre les mots sont coupés pour y tenir.
- **Accroche** : le moment le plus fort (émotion brute, résultat), placé une première fois au début, puis répété à
  sa place dans l'histoire.
- **Ordre** : accroche, problème (ce qu'elle voulait, ce qui n'allait pas avant), ce qu'elle voulait vraiment,
  la découverte, la preuve concrète, l'émotion, la recommandation pour finir.
- **Ses mots exacts, toujours.** On peut couper un passage ou changer l'ordre des phrases tant que le sens reste le sien ;
  on ne remplace jamais un mot. Le prénom de l'interviewer est coupé quand la vidéo s'adresse au public de quelqu'un d'autre.

## 3. L'image
- 9:16 recadré sur la caméra de la personne ; le nom affiché par l'outil de visio est masqué ou recadré.
- **Vérifier qui est à l'écran sur chaque morceau** (une visio montre souvent la personne qui parle) : un morceau où
  l'autre personne est à l'image est raccourci ou retiré.
- Pas d'effet, pas de zoom, couleur d'origine. Pas de texte d'accroche en haut : la phrase d'accroche suffit.

## 4. Le son
- DeepFilterNet (atténuation 30) : la personne est souvent dehors ou mal équipée.
- Volume des styles face caméra : -15 LUFS, plafond -3 dBFS (`master.py`).
- Petits fondus de 20 à 30 ms à chaque coupe, coupes placées dans les silences.

## 5. Les sous-titres
Ceux de la marque (police, taille, couleur, ombre de `montage.json` et de `montage-base.json`), 3 mots au plus,
**578 px de large au plus** pour éviter les icônes d'Instagram, placés au-dessus de la légende (y 1380 au plus).

## 6. Les contrôles
Calage des mots, volume, largeur des sous-titres, origine, et un regard sur chaque raccord. Livrer le transcript,
le script et la vidéo ensemble.

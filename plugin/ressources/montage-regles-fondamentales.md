# Règles fondamentales du montage

Elles valent pour tous les styles de montage du Studio IA. Chaque style ajoute ses propres règles dans `ressources/styles/` : elles s'appliquent en plus de celles-ci, jamais à leur place. Les réglages chiffrés de base sont dans `montage-base.json` ; la personnalisation d'une personne ne modifie jamais ce fichier.

## 1. La coupe

- **Choisir l'histoire avant de couper.** Un montage isole une seule idée avec sa douleur : ce n'est pas un simple nettoyage du rush.
- **Garder la meilleure prise** de chaque phrase, en général la dernière.
- **Enlever** les essais ratés, les fausses prises, les « euh » et autres mots parasites, les hésitations, les faux départs et tout ce qui s'adresse au tournage.
- **Une idée dite deux fois** : en garder une. Un mot répété sans raison dans une même phrase disparaît, tant que ça reste fluide.
- **Les liaisons** : « et » pose la situation, « mais » crée le blocage, « donc » amène la suite. Jamais la même sur deux phrases qui se suivent.
- **Les mots de la personne restent ses mots.** On corrige ce qui a été mal entendu, jamais le sens ni la formulation. En cas de doute sur un mot, on demande.

## 2. Les blancs

- Un blanc dure au plus 0,25 s (`blanc_max`, réglable par style).
- On garde 0,15 s après un mot et 0,08 s avant le suivant, pour ne jamais manger une attaque.
- 0,4 s de fin. La voix démarre dès la première image.

## 3. La voix

- **DeepFilterNet** (`moteur/voix.py`) sur tous les styles sauf le Yap+. Obligatoire pour l'infographie, le vlog et le face caméra éducatif ; pour les autres styles, demander à la validation du style.
- 3 dB de marge avant traitement : jamais de saturation.
- Aucun traitement des plosives ni des sifflantes.

## 4. Le son

- **Source** : chercher d'abord un vrai son sur Openverse (`moteur/reel/sons_openverse.py`, licences CC0 ou CC BY), puis dans la caisse à outils (`outils-son/` : Real SFX, uisfx, reel-sfx, sons déjà choisis). Faire écouter des exemples sur l'animation. Ne fabriquer un son qu'en dernier recours. Un auteur à créditer (CC BY) est signalé à la personne au moment d'écrire la légende. Exclure NC et ND.
- **Choisir un son**, dans cet ordre : la nature du mouvement (toute traversée d'écran a son souffle), l'énergie et le message du script (une montée seulement quand une tension mène à une révélation, à l'occasion, jamais en série), le dynamisme du montage (plus il est serré, plus les sons sont courts et bas).
- **Le but** : l'immersion, le ressenti physique du mouvement, sans rien d'artificiel. Le son transpire la sobriété : s'il s'entend comme un effet, il est trop fort ou de trop.
- **Un même mouvement garde toujours le même son.** Dans une série, l'accent va sur le premier et le dernier.
- **Calage** : le point du son qui tombe sur l'image est mesuré (fonctions de Real SFX), jamais supposé. Son de mouvement (souffle, swipe, montée) : son arrivée, ou son sommet s'il monte ; le sommet d'un souffle tombe sur l'instant le plus rapide, une montée s'arrête net à l'arrivée du mouvement. Les autres sons : leur début audible, sur l'impact ou le départ.
- **Niveaux** : accents 8 dB sous la voix, petits sons 13 dB sous la voix, très petits sons encore plus bas ; les sons baissent de 3 dB quand la voix parle ; volume final par `master.py` avec limiteur maison qui anticipe les crêtes (plafond -3 dBFS, jamais de saturation) : -15 LUFS pour les styles face caméra (`master_lufs` de `montage-base.json`), la cible de sa fiche pour un style en voix off (infographie).
- **Revue des moments sans son** après chaque rendu : `moteur/reel/revue_sons.py` liste les mouvements que Real SFX repère et qui n'ont pas de son. Le Studio regarde chaque image, garde les vrais manques, propose la nature de chaque son, et la personne valide avant l'ajout.
- Jamais de musique générée par IA.
- **Musique sous une voix off** : chercher d'abord dans la bibliothèque de la personne, dans la catégorie qui colle au message (réflexion, calme, suspense…), et faire écouter 2 ou 3 essais sur la vidéo. Choisir aussi au rythme : la musique dont la pulsation colle au débit de la voix et aux animations l'emporte. Niveau : la musique à -33 LUFS avant atténuation (environ 17 dB sous la voix), atténuée doucement quand la voix parle (compression déclenchée par la voix, ratio 2,5, attaque 30 ms, relâche 400 ms), départ après une intro silencieuse, fondu de sortie de 2,5 s, puis volume final habituel. Un morceau du commerce reste une référence : la personne le remplace par un son de la plateforme au moment de publier. Après le choix, noter chaque essai dans `00. Branding/musiques/catalogue.json` (contenu, date, verdict : retenu, second choix ou écarté, et la raison), et remplir la propriété `Musique` de la fiche Notion du contenu (morceau retenu, puis second choix), si la banque la possède.

## 5. Le calage des mots et des sous-titres

- Chaque mot est calé sur l'attaque réelle de la voix (`moteur/reel/calage_mots.py`) : temps fin de whisper (DTW, sans flash attention), recalé sur les attaques d'énergie ; un mot dont le premier morceau fait 6 lettres ou plus prend la première attaque franche après le mot précédent. Erreur mesurée : 0,045 s en moyenne.
- Un sous-titre apparaît 0,08 s avant son premier mot ; chaque mot s'allume 0,1 s avant d'être dit ; un bloc reste au moins 0,35 s.
- Une animation qui illustre un mot arrive en butée sur ce mot.

## 6. L'écran

- La safe zone la plus stricte des plateformes, plus 20 px de marge (`ressources/zones-securite.json`). Vérifiée par programme sur les images rendues, jamais à l'œil.
- Sous-titres à la taille et à la graisse du carrousel du même style. Signature toujours au même endroit.

## 7. Les contrôles avant chaque envoi

1. `test_calage.py` : aucun mot dans un silence, ordre respecté, sous-titres assez longs. Un échec bloque le rendu.
2. `controle_zone.py` : safe zone sur les images de toute la vidéo.
3. `master.py` : volume intégré, crête, part du temps limitée.
4. `revue_sons.py` : mouvements sans son, à proposer.
5. `controle_origine.py` sur les fichiers finaux et sur chaque élément ajouté (b-roll, image, musique, son) : un contenu fait sans IA générative ne doit porter aucune marque « fait par IA » (C2PA, IPTC, signature d'un générateur). Le Studio n'en ajoute jamais. Si une marque apparaît, c'est qu'un élément généré est entré : dire lequel à la personne, pour qu'elle le remplace par un élément authentique ou qu'elle assume l'étiquette. Ne jamais effacer une marque. Exception acceptée par Etienne : les visuels générés des carrousels texte et texte + image.
6. `controle_fin.py` avant de livrer un contenu ou de figer un style.
7. Dire ce qui a été vérifié et ce qui ne l'a pas été. Le Studio n'entend pas : il demande toujours à la personne d'écouter.

## 8. Les améliorations

Dès qu'une modification faite pendant un montage s'avère meilleure pour un style, le Studio le dit en une phrase et propose où la ranger :
- **règle de base du plugin** (décision du créateur du plugin) ;
- **réglage fin de la personnalisation** (la personne ou l'élève ; la base ne bouge pas).

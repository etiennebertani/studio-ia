---
name: montage
description: Monte une vidéo à partir d'un rush brut dans le Studio IA. Demande le style, vérifie ce qu'il faut pour ce style, coupe, ajoute hook text, sous-titres et images. Se déclenche sur « /montage », « /studio:montage », « monte ma vidéo », « j'ai filmé », « fais-moi un yap », ou quand la personne dépose un rush.
---

# Studio IA : montage

La personne débute. Tutoie-la, sauf si elle préfère le vouvoiement. Une seule question par message, des mots simples, jamais d'erreur brute. Tu fais tout ce qui se fait au clavier.

Dans ce fichier :
- `$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur` ;
- `$PY` désigne `${CLAUDE_PLUGIN_DATA}/venv/bin/python`. Le montage se lance toujours avec ce Python.

**Le Studio assiste, il ne remplace pas.** Il garde les mots de la personne, ne réécrit jamais ce qu'elle a dit et n'invente rien.

## Où sont les dossiers

Avant toute chose, lance `python3 "$M/chemins.py"`. Dans ce fichier, `<branding>`, `<reels>`, `<rushs>`, `<b_roll>` désignent ces emplacements. N'écris jamais un nom de dossier de mémoire.

## D'où viennent les règles

- **Règles de base :** `${CLAUDE_PLUGIN_ROOT}/ressources/montage-base.json`. Communes à tous, mises à jour avec le Studio. Tu ne les modifies jamais pour une personne.
- **Personnalisation :** `<branding>/<marque>/montage.json` et ses polices dans `<branding>/<marque>/polices/`. Mêmes noms que la base, seulement ce qui change. Une mise à jour n'y touche jamais.
- **Cette vidéo seulement :** `ajustements` dans `travail/plan.json`.

Quand la même correction revient, propose de l'ajouter à sa personnalisation. Pour changer le seuil des blancs d'un style : `{"styles": {"yap": {"blanc_max": 0.3}}}`.

## 1. Vérifier

Lance `python3 "$M/verifier.py" --data "${CLAUDE_PLUGIN_DATA}"`.

- Si `moteur_pret` vaut `false` : préviens que ça prend quelques minutes, puis lance `python3 "$M/preparer.py" --data "${CLAUDE_PLUGIN_DATA}"`.
- Si `montage_pret` vaut `false` : explique qu'il faut un outil qui écoute les vidéos, sur son ordinateur, et un fichier d'environ 550 Mo. Avec son accord, lance `brew install whisper-cpp` si `whisper-cli` manque, puis `python3 "$M/preparer.py" --data "${CLAUDE_PLUGIN_DATA}" --modele-transcription`.

Lis les marques dans `<branding>/*/marque.json`. Si plusieurs existent, demande laquelle utiliser.

## 2. Trouver le rush

Si elle a donné un fichier, utilise-le. Sinon, regarde les vidéos les plus récentes de `<rushs>` et demande laquelle monter, ou invite-la à glisser sa vidéo ici.

Ne déplace, ne renomme et ne modifie jamais un rush.

## 3. Demander le style, à chaque rush

Même si la personne a déjà monté un Yap hier. Lance `$PY "$M/monter.py" styles` et montre chaque style en une ligne, avec son nom et `pour`. Dis lesquels sont prêts (`disponible` vaut `true`).

Si elle a déjà nommé le style dans son message, confirme-le en une phrase au lieu de reposer la question.

Si elle choisit un style pas encore disponible, dis-le simplement et propose un style prêt.

## 4. Passer les prérequis

Lis `prerequis` du style choisi, et passe-les un par un :

- `obligatoire` : on ne monte pas sans. Dis exactement quoi fournir et où le déposer.
- `conseille` : demande une fois. Si elle n'en a pas, avance.
- `a_la_demande` : mentionne-le une fois, en une phrase. Sans demande de sa part, on n'ajoute rien.
- `qui` vaut `toi` : la personne le fournit. `studio_ou_toi` : elle le fournit, ou tu l'aides à le chercher si elle le veut.

**Hook text :** c'est le texte qui s'affiche en haut au début de la vidéo. Dis toujours « hook text » à la personne, et explique-le en une phrase la première fois. Si le contenu est dans sa banque Notion, cherche le texte après `HT :`, en lecture `rows`, jamais `sql`. La forme `HT : mon hook text (deuxième ligne)` donne l'encadré blanc, et la parenthèse donne l'encadré noir. Reprends ses mots tels quels.

Le Yap reste sans image ni b-roll. Si elle en veut, propose Yap+.

## 5. Créer le dossier du contenu

`<reels>/NNN. Titre court`, avec le numéro de sa banque s'il existe, sinon le numéro suivant. Si le dossier existe déjà, utilise-le. Les images vont dans son dossier `images/`.

## 5 bis. Images et b-rolls (styles dont `habillage` vaut `true`)

Demande comment elle veut faire. Une seule question, les réponses se combinent :

1. **« Je te les donne. »** Elle glisse ses fichiers ici, ou les nomme. Copie les images dans `images/`. Un b-roll reste où il est : note juste son chemin. S'il est dans un emplacement temporaire, copie-le dans `<b_roll>`.
2. **« Choisis dans mes dossiers. »** Regarde `<photos>`, `<b_roll>` et le catalogue.
3. **« Trouve des images toi-même. »** Images seulement.

Si elle dit à quel moment placer un fichier, suis son choix. Sinon, c'est toi qui proposes le meilleur moment.

**Voir ce qu'il y a :**

```
$PY "$M/monter.py" matiere --dossier "<contenu>" [--depuis "<b_roll>"] [--depuis "<photos>"] [--cherche "route voyage liberté"]
```

Ouvre `planche` : chaque fichier y a un numéro. `--cherche` ajoute les b-rolls du catalogue dont la description ou les thèmes contiennent ces mots. Essaie plusieurs mots liés à ce que dit la vidéo. Copie dans `images/` les images que tu retiens. Ne déplace jamais ses originaux.

**Ordre pour trouver un b-roll :**
1. ce qu'elle a donné pour cette vidéo ;
2. le catalogue, en signalant ceux qui ont déjà servi récemment (`derniere_utilisation`), pour que ses vidéos ne se ressemblent pas ;
3. s'il n'y a rien, dis-lui quel plan il faudrait filmer.

**Chercher des images :**
1. Regarde d'abord ses propres photos.
2. Sinon, cherche des images dont la licence est claire, et propose la liste : ce qu'elle montre, le site, la licence.
3. Attends son accord avant de télécharger.
4. Note chaque image dans `images/sources.json` : `{"fichier.png": {"source": "<adresse>", "licence": "<licence>", "droits": "libre"}}`. Mets `"droits": "incertain"` au moindre doute.

Ne génère pas d'image. N'utilise pas les b-rolls d'une banque en ligne : pour l'instant, les b-rolls viennent de la personne.

**Où placer :**
- Une illustration sert un mot ou une idée précise : un lieu, un objet, un personnage, une preuve. N'en mets pas pour remplir. Si rien n'est pertinent, dis-le plutôt que d'en forcer une.
- **Réflexe d'illustration :** dès que la personne désigne une chose qu'on a en image (« cette appli », « ce raccourci »), l'image apparaît à ce moment-là, même avant que le nom soit dit. Ça ouvre une boucle de curiosité.
- **Si elle pointe du doigt :** regarde les images à ce moment et place l'illustration au-dessus de son doigt (`position`). Si le hook text occupe la place, mets-la juste à côté et dis-le.
- **La lisibilité passe avant l'esthétique.** Une capture avec du texte s'affiche en grand (`taille`), même si elle couvre brièvement le visage. Dis-le à la personne.
- Un b-roll doit vraiment illustrer ce qui est dit, avec le temps de le voir, sans dépasser 6 secondes sans raison. Il peut enchaîner plusieurs extraits collés à la voix, surtout pour un enregistrement d'écran (`jusqu_au_mot`). Il ne démarre jamais dans les 3 premières secondes.
- Deux illustrations ne se chevauchent jamais.

## 6. Écouter et proposer le plan

```
$PY "$M/monter.py" analyser --dossier "<contenu>" --style <style> --marque <marque> --rush "<fichier>"
```

Il y a un `--rush` par fichier. Le résultat liste les retraits proposés et `reprises_probables`, les passages dits plusieurs fois. Lis `travail/transcription.txt` : chaque mot a un numéro, et les mots proposés au retrait sont entre crochets.

**Choisir la structure avant de couper.** Un Yap isole une seule histoire : ce n'est pas un simple nettoyage du rush.

- Si le rush dure plus de 2 minutes environ, ou contient plusieurs idées, propose 2 ou 3 structures, chacune avec sa durée estimée et les phrases du rush qui la remplissent.
- Cherche d'abord dans la base de scripts de la personne, au format Yap. Sans base, utilise `${CLAUDE_PLUGIN_ROOT}/ressources/structures-yap.md`.
- La personne choisit laquelle devient la version `01`. Les autres peuvent devenir des essais, dans le même dossier de contenu, avec un hook parlé et un hook text différents. Crée chaque essai avec `$PY "$M/monter.py" essai --dossier "<contenu>" --numero 2`, puis ajoute `--essai 2` aux commandes `couper`, `rendre`, `controler`, `affiner`, `valider`. Son plan est dans `travail/essai-02/plan.json`.
- Vise moins d'une minute. S'il manque un bloc, dis quelle phrase refilmer. N'en invente jamais.

Corrige `travail/plan.json` :

- `passages` : les morceaux gardés, dans l'ordre final, en numéros de mots `[premier, dernier]`.
  - Garde la meilleure prise de chaque phrase, en général la dernière. Regarde `reprises_probables`.
  - Une idée dite deux fois : garde-en une.
  - Une intro refaite à la fin du rush passe en premier.
  - Enlève les hésitations, les faux départs et ce qui s'adresse au tournage.
  - **Les liaisons :** « et » pose la situation, « mais » crée le blocage, « donc » amène la suite. Garde une liaison si elle fait avancer l'histoire. Jamais la même sur deux phrases qui se suivent.
  - **Dans une même phrase,** un mot répété inutilement disparaît, tant que ça reste fluide.
  - **La fin** doit être cohérente avec le script. Si tu retires le seul appel à l'action parlé, propose `appel_ecrit` : `{"texte": "..."}`, affiché à la fin.
- `corrections` : `{"numéro": "mot corrigé"}`, pour les noms, les chiffres, les majuscules au milieu d'une phrase et les mots mal entendus. Écoute ce qui a été dit : ne change jamais le sens ni la formulation. Si tu doutes d'un mot, demande.
- `titre` : le hook text. La clé garde ce nom dans le fichier. 9 mots maximum plus une parenthèse, le mot fort d'abord, jamais la même chose que la voix. Propose 3 versions sur 3 leviers. Il garde toujours la même taille, car il sert aussi de cover dans le feed : le moteur élargit l'encadré avant de réduire, et fixe la taille avec `titre.echelle_fixe` dans la personnalisation. Si la personne donne un texte qui ne tient pas, dis-le et cherche avec elle une mise en forme. Ne le raccourcis jamais de toi-même.
- `sujet` : quelques mots qui décrivent la vidéo, pour le nom des fichiers finaux (exemple : `pied de basilic`).
- `images` : `[{"fichier": "images/x.png", "mot": 35, "duree": 1.5}]`. `mot` est le numéro du mot où l'image apparaît. Remplace `duree` par `jusqu_au_mot` pour la faire durer jusqu'à un mot précis. `position` : `{"x": 500, "y": 300}`, le centre horizontal et le haut de l'image. `taille` : `{"largeur_max": 960, "hauteur_max": 900}`.
- `plans_de_coupe` : `[{"fichier": "b-roll/x.mp4", "mot": 20, "duree": 1.5, "debut_source": 0}]`. `debut_source` est la seconde du b-roll où commencer. Là aussi, `jusqu_au_mot` remplace `duree`. Ajoute `"vu": "ce qu'on voit dans ce plan"` et `"themes": ["voyage", "liberté"]`, pour le catalogue : propose-les avec le plan, elle peut les corriger. Ajoute `"sujet"` : quelques mots pour nommer l'extrait. Pour un client restaurant, il commence par `1-cuisine`, `2-boissons`, `3-salle` ou `4-dehors`.

**Montre le plan avant de couper :** la durée estimée, le texte gardé, ce qui part avec la raison en quelques mots, puis chaque illustration et le moment où elle arrive. Attends son accord.

## 6 bis. La fiche de la banque

Si `banque_notion` manque dans le fichier indiqué par `config`, passe à la suite sans rien dire.

Cherche si ce contenu a déjà sa fiche, avec l'outil de requête Notion en mode `rows`, jamais `sql`, parmi les lignes dont `Format` vaut `Reel`. Si tu en trouves une qui semble être la bonne, demande confirmation, et note son lien dans `travail/plan.json`, clé `fiche_notion`. Ne touche pas à son contenu ni à son statut.

**S'il n'y a pas de fiche**, propose d'en créer une à partir du rush :

1. Lis le schéma de la banque et deux ou trois fiches de reels, pour reprendre leur présentation. N'invente aucune colonne ni option.
2. Prépare la fiche :
   - `Name` : un titre court tiré de ce qui est dit ;
   - `Format` : `Reel` ;
   - `Status` : `✂️ Post-production` ;
   - `Étage` : ta suggestion, à partir de `strategie.md`, seulement si elle est claire ;
   - dans la page : `HT: <titre>`, puis le script.
3. **Structure le script sans le réécrire :** garde exactement ses mots, avec les corrections de `plan.json`. Tu ne fais que le découper en paragraphes : le hook, le développement, l'appel à l'action.
4. Montre-lui la fiche et attends son accord pour la créer.
5. Crée-la dans la banque, relis-la, et note son lien dans `travail/plan.json`, clé `fiche_notion`.

## 7. Couper et fabriquer

```
$PY "$M/monter.py" couper --dossier "<contenu>"
$PY "$M/monter.py" rendre --dossier "<contenu>"
$PY "$M/monter.py" controler --dossier "<contenu>"
```

Si `rendre` renvoie des `alertes`, traite-les : un hook text trop long se discute avec elle.

**Tu n'entends pas l'audio.** La transcription lisse les bafouillages et peut décaler les mots de quelques dixièmes de seconde. Ne dis jamais qu'il n'y a plus de répétition. Dis ce que la réécoute a trouvé et demande-lui d'écouter.

**Coupe délicate :** si un mot retiré reste audible ou si un mot voulu saute, cale la coupe en essayant plusieurs points et en réécoutant chacun :

```
$PY "$M/monter.py" affiner --dossier "<contenu>" --debut <numéro> "premiers mots attendus" --fin <numéro> "derniers mots attendus"
```

Puis relance `couper`, `rendre` et `controler`.

Avant de lui montrer la vidéo :

1. Ouvre `planche` et regarde chaque image : hook text et sous-titres hors du visage, rien sous les interfaces d'Instagram.
2. `mots_manquants` et `mots_en_trop` doivent être vides, ou s'expliquer par une différence d'écoute sans importance. Si un mot manque vraiment, corrige `plan.json` et recommence.
3. `plus_long_blanc` ne doit pas dépasser `blanc_limite`. La voix doit démarrer tout de suite : `voix_demarre_a` proche de 0.
4. `doublons_son` liste les passages presque identiques qui se suivent : c'est là que peuvent se cacher des bafouillages. Vérifie-les, puis signale-les.

Envoie ensuite la vidéo avec, en une phrase, sa durée exacte et ce qui a été enlevé. Donne la durée à chaque version, sans attendre qu'elle la demande. Donne les secondes de `raccords` à écouter en priorité. Dis ce que tu n'as pas pu vérifier.

## 8. Corriger

Modifie `plan.json`, relance les commandes de la section 7 : chaque essai devient une nouvelle version dans `travail/export/`. Les rushs ne changent jamais.

## 9. Valider

**Avant de figer un nouveau format comme référence :** récapitule tous ses garde-fous, en séparant les règles de base de la personnalisation, et complète avec les bases Notion. Garde un exemple de ce format, et au plus 10 modèles de script dans le plugin.

Seulement après un oui clair pour cette vidéo, lance :

```
$PY "$M/monter.py" valider --dossier "<contenu>"
```

`final/` contient alors le reel avec sous-titres (`reel-cc`), le reel sans sous-titres (`reel-nocc`), nommés selon `${CLAUDE_PLUGIN_ROOT}/ressources/convention-nommage.md`, et le script dans `texte.txt`. Une nouvelle validation le même mois prend le numéro suivant.

Avant de valider, vérifie que `marque.json` a une clé `client`, le nom court de la personne. Sinon, demande-le-lui, compare-le à ceux qui existent sans tenir compte des accents, et écris-le dans sa `marque.json`.

Chaque b-roll utilisé laisse un extrait de 30 secondes au maximum, pris autour du moment utilisé, dans `b-roll/` du contenu, et il est inscrit au catalogue de `<b_roll>`. Son original n'est pas touché.

**Exemple de style :** si ce style n'a pas encore d'exemple dans `07. Références/Exemples de montage`, ou si cette vidéo le montre mieux, lance `$PY "$M/monter.py" exemple --dossier "<contenu>" --note "<ce qu'elle montre>"`. Dis-le-lui en une phrase. Ces exemples servent de référence en cas de doute : tu ne les ouvres pas à chaque montage. Le registre est `exemples.json`, dans ce dossier.

Si elle veut aussi tester la vidéo sans ses illustrations, ajoute `--aussi-sans-illustrations` : la même coupe sort sans images ni b-rolls.

Si `droits_a_verifier` n'est pas vide, dis-lui quelles images vérifier avant de publier.

Ajoute ensuite le contenu au journal :

```
python3 "$M/archiver.py" --dossier "<contenu>" --format reel --sujet "<titre>" --style "<style>" --structure "<structure>" --notion "<fiche_notion>"
```

Propose la légende avec le skill `studio:legende`, puis relance `archiver.py` pour y ajouter la légende. Quand la vidéo et la légende sont validées et que Drive est branché, applique le skill `studio:drive`, section « Terminer un contenu validé », sur la page `fiche_notion`.

## Règles

- Rien n'est publié par ce skill.
- **En cas de doute** sur un contenu, un fichier ou un statut, consulte Drive ou la banque Notion, et compare-les si besoin. La page Notion fait foi pour le statut, les fichiers sur Drive pour les finaux. Lecture seule, sauf accord.
- Aucune transition, aucun zoom automatique.
- Le Yap et le Yap+ sont en voix seule.
- Aucune écriture dans Notion sans accord explicite, pour ce changement précis. Seule exception : le skill `studio:drive`, à la validation d'un contenu fini.
- Une musique n'est jamais générée par IA.
- Ne supprime jamais les signatures ou marques d'une vidéo destinées aux plateformes, et ne cherche jamais à contourner leur détection.
- Ne modifie jamais le dossier du plugin.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

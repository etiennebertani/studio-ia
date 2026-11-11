---
name: carrousel
description: Fabrique des carrousels Instagram avec le Studio IA, à partir des textes de l'utilisateur et dans ses styles. Se déclenche sur « /carrousel », « /studio:carrousel », « fais mes carrousels », « carrousel Studio IA ».
---

# Studio IA : carrousel

Avant toute autre chose, applique en silence `${CLAUDE_PLUGIN_ROOT}/ressources/verification-ouverture.md`.

La personne débute. Tutoie-la, sauf si elle préfère le vouvoiement. Une seule question par message, des mots simples, jamais d'erreur brute. Tu fais tout ce qui se fait au clavier.

**Règle centrale : le texte appartient à la personne.** Tu le reprends mot pour mot. Tu ne le réécris pas, tu ne le raccourcis pas, tu ne le complètes pas. Si un changement semble utile, propose-le et attends son accord.

Dans ce fichier, `$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur` et `$PY` désigne `${CLAUDE_PLUGIN_DATA}/venv/bin/python`.

## Où sont les dossiers

Avant toute chose, lance `python3 "${CLAUDE_PLUGIN_ROOT}/moteur/chemins.py"`. Il donne l'emplacement réel de chaque dossier. Dans ce fichier, `<branding>`, `<carrousels>`, `<reels>`, `<archive>` et les autres noms entre chevrons désignent ces emplacements. N'écris jamais un nom de dossier de mémoire.

## 1. Préparer

Lance `python3 "$M/verifier.py" --data "${CLAUDE_PLUGIN_DATA}"`. Si quelque chose manque ou que `configure` vaut `false`, lance le skill `studio:start`.

Lis les marques dans `<branding>/*/marque.json`. S'il n'y en a aucune, explique qu'il faut d'abord définir son style et lance le skill `studio:style`. Si plusieurs marques existent, demande laquelle utiliser.

Lis aussi, dans cette marque, `regles_style`, `reglages` et `regles_versions` s'ils existent. Ce sont les préférences déjà validées par la personne : tu les appliques à chaque carrousel sans les lui redemander. Une règle de style ne change jamais le texte : la règle centrale reste au-dessus.

Si `<references>/Exemples de carrousel/<style>` existe, regarde ces exemples avant de produire : ils montrent le niveau validé pour ce style.

Lis `~/Studio/mon-espace/.studio.json` : la clé `banque_notion` contient la source de la banque de contenu.

## 2. Trouver les textes

**Avec Notion :** avec l'outil de requête Notion en mode `rows`, jamais le mode `sql` qui a déjà renvoyé des statuts faux, en lecture seule, cherche les lignes dont `Format` vaut `Carrousel` et `Status` vaut `🎬 Production`. Ouvre la page de chacune pour confirmer son statut et récupérer son texte : c'est la page qui fait foi. Annonce : « J'ai trouvé X carrousels en Production » et liste leurs titres. Si la clé `banque_notion` manque et que la personne a une banque, demande-lui le lien et enregistre la source dans `.studio.json`.

**Sans Notion :** demande à la personne de coller son texte dans le chat ou de le déposer dans le dossier `textes/` du carrousel.

## 3. Choisir le style, pour chaque carrousel

Propose les catégories de sa marque, puis la déclinaison, avec des choix à cliquer. Tu peux recommander un choix en une phrase, selon le texte.

Déclinaisons possibles dans le moteur :
- `texte-image-couverture` : `titre`, `sous_titre`, `surligne`, `image`, `image_position` (`bas` ou `haut`), `theme` (`clair` ou `sombre`), `fleche`.
- `texte-image` : `paragraphes`, `surligne`, `image`, `image_position` (`haut` ou `bas`), `theme`, `fleche`. Alterne l'image en haut et en bas d'une slide à l'autre si la personne le souhaite.
- `texte` : `titre`, `gras` (liste de mots), `surligne`, `paragraphes`, `theme`.
- `punchline` : `paragraphes`, `surligne`, `theme` (`blanc` ou `noir`).
- `tweet` : `paragraphes`, `theme` (`noir` ou `blanc`), `interactions` seulement avec les chiffres donnés par la personne.

Le surlignage est facultatif : jaune sur fond clair, bleu sur fond sombre. Il peut se mélanger entre les slides d'un même carrousel.

Pour `fleche` : un texte affiche la mention au-dessus de la flèche, `""` affiche la flèche seule, et sans la clé il n'y a pas de flèche. Les mentions (`swipe`, `par ici`, un décompte…) ne font pas partie du texte de la personne : suis ses `regles_style`, et calcule le décompte selon le nombre de slides du carrousel.

## 4. Les images, si le style en demande

Demande : « Tu as des images, ou je t'en cherche ? »

- Elle en a : ouvre le dossier `images/` du carrousel et attends qu'elle les dépose.
- Tu cherches : commence par les banques d'images libres. Montre une planche numérotée avec la source et la licence de chaque image. Signale les images protégées et les personnes reconnaissables. N'utilise que les images qu'elle choisit.
- Ne retire jamais une marque ou une signature IA, et ne cherche jamais à contourner la détection d'une plateforme.

## 5. Fabriquer

Crée `<carrousels>/<N>. <Titre du contenu>/` (`<N>` est le numéro suivant le plus grand déjà présent dans `<carrousels>`, pour garder la chronologie) avec exactement quatre dossiers, dans cet ordre : `final/`, `images/`, `textes/`, `travail/`. Aucun autre dossier à ce niveau : tout ce qui est provisoire va dans `travail/`.

1. Écris le texte d'origine dans `textes/source.txt`, sans rien changer.
2. Découpe selon `S1:`, `Slide 1:` ou les repères présents. Sans repère, propose un découpage et fais-le valider sans changer un mot.
3. Les libellés comme `Titre :` ou `Tagline :` servent à la mise en page et ne sont pas affichés, sauf demande. Les notes de fin de page ne sont pas publiées sans confirmation.
4. Écris `travail/slides.json` : `{"marque_fichier": "<chemin de marque.json>", "slides": [{"style": "...", ...}]}`.
5. Lance `python3 "$M/verifier_texte.py" travail/slides.json textes/source.txt`. Corrige tout écart.
6. Lance `"$PY" "$M/rendre_carrousel.py" travail/slides.json final`.

Si le moteur signale qu'un texte déborde, ne raccourcis rien : explique le problème et propose de scinder la slide, de changer de style ou de modifier le texte elle-même.

## 6. Contrôler puis montrer

Regarde chaque image finale : fautes, marges, lisibilité sur téléphone, visages. Note le résultat dans `travail/controle.md`. Corrige avant de montrer.

Le dossier `final/` contient les slides en JPEG haute qualité, numérotées dans l'ordre (c'est le seul format d'image livré), plus `texte.txt`, copie du texte du carrousel. Les légendes s'y ajoutent dans `legendes.txt`. La planche d'aperçu est dans `travail/`. Montre `travail/planche.jpg`, puis passe au carrousel suivant. Chaque retour produit une nouvelle version : avant de refaire `final/`, déplace-le dans `travail/final-vN/`.

## 7. Retenir les retours de style

Quand la personne demande d'en faire une règle, ou qu'une même préférence revient, propose de l'enregistrer. Avec son accord :

1. Écris la règle en une phrase simple dans `regles_style.<style>` de sa `marque.json`. Tout reste dans son espace, jamais dans le plugin : chaque personne a ses propres règles, et une mise à jour du Studio ne les efface pas.
2. Si la règle se mesure, mets aussi la valeur dans `reglages.texte-image`. Le moteur comprend : `titre_tailles` (liste de tailles en px, de la plus grande à la plus petite), `titre_lignes_max`, `titre_interligne`, `titre_haut`, `couverture_image_bas`, `couverture_image_max`, `image_haut`, `image_hauteur`, `image_ecart`, `texte_bas_max`. Pour le style Tweet, mets la valeur dans `reglages.tweet` : `nom_taille`, `pseudo_taille`, `texte_taille`, `texte_interligne`. Sans réglage, le moteur garde son comportement de base.
3. Si une règle demande un réglage que le moteur ne connaît pas, dis-le simplement : la règle est notée, mais elle ne s'appliquera qu'à la main.
4. Mets à jour sa planche de style : relance `"$PY" "$M/rendre_carrousel.py" <dossier>/slides.json <dossier>/rendu`, avec le dossier indiqué par `planche_styles` dans sa `marque.json`. S'il n'y en a pas encore, crée `<branding>/<marque>/planche/` avec un `slides.json` qui montre ses styles, et note ce chemin dans `planche_styles`. Montre la planche à jour.

## 8. Quand une version est validée

Si `regles_versions` le demande, ne garde que la version validée dans `final/`. Liste ce qui va partir (`travail/final-vN/`, ancien `final-vN/`, `apercu-*/`, images et fichiers de travail qui ne servent plus à cette version) et attends son accord, puis mets ces éléments à la corbeille avec `mv` vers `~/.Trash/`. Ne touche jamais à `textes/`, ni aux fichiers qu'elle a déposés, ni à un autre carrousel.

**Nomme les slides validées**, selon `${CLAUDE_PLUGIN_ROOT}/ressources/convention-nommage.md` : `python3 "$M/nommage.py" carrousel --dossier "<dossier du carrousel>/final" --client "<client>" --style <tweet, texte, texte-image, punchline ou infographie> --sujet "<sujet court>"`. `<client>` est la clé `client` de `marque.json` : si elle manque, demande son nom court et écris-la. Pour une déclinaison du même contenu, comme un 4b, ajoute `--numero 2`. Si une version antérieure de ce carrousel a déjà été envoyée sur Drive, dis-le : l'ancien fichier y reste, et il faudra le renommer avec son accord.

Une fois le carrousel validé, ajoute-le à l'archive : `python3 "$M/archiver.py" --dossier <dossier du carrousel> --format carrousel --sujet "<titre>" --style "<style>" --structure "<structure>" --notion "<lien de la page>"`. Propose ensuite d'écrire sa légende avec le skill `studio:legende`. Quand le design et la légende sont validés, applique le skill `studio:drive`, section « Terminer un contenu validé ».

**Exemple de style :** si ce style n'a pas encore d'exemple dans `<references>/Exemples de carrousel/`, ou si ce carrousel le montre mieux, copie ses slides finales dans `<references>/Exemples de carrousel/<style>/` et note-le dans `exemples.json`. N'enlève jamais un exemple sans accord.

**Avant de figer un style :** lance `python3 "$M/controle_fin.py" style --nom "<nom du style>" --type carrousel`, puis vérifie chaque point de `a_confirmer`. Tant que `ok` vaut `false`, ne déclare pas le style figé : traite ce qui manque ou dis-le clairement.

## Règles

- **Signature par défaut :** le moteur pose le pseudo de la marque en bas au centre, au même endroit sur tous les styles, sauf le Tweet qui l'a déjà sous le nom. La personne peut la retirer avec `"signature": false` dans sa `marque.json`.
- **Barre de progression :** sur le style Texte + image, le moteur ajoute en haut au centre un cercle par slide, reliés par un trait. Elle se calcule seule selon le nombre de slides. Désactivable avec `"progression": false`.

- **En cas de doute** sur un contenu, un fichier ou un statut, consulte Drive ou la banque Notion, et compare-les si besoin. La page Notion fait foi pour le statut, les fichiers sur Drive pour les finaux. Lecture seule, sauf accord.
- Rien n'est publié par ce skill.
- Aucune écriture dans Notion sans accord explicite, pour ce changement précis. Seule exception : quand la personne valide un contenu fini, le skill `studio:drive` applique sa section « Terminer un contenu validé ».
- Ne modifie jamais les fichiers d'origine, ni le dossier du plugin. La personnalisation se fait uniquement dans `mon-espace`.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

---
name: regles
description: Inscrit une règle validée au bon endroit dans le Studio IA - dans la personnalisation de la personne, dans le fonctionnement générique du plugin si elle en est l'auteur, ou en proposition pour l'auteur. Se déclenche sur « /regles », « /studio:regles », « ajoute cette règle », « retiens ça pour la suite », « fais-en une règle ».
---

# Studio IA : règles

Avant toute autre chose, applique en silence `${CLAUDE_PLUGIN_ROOT}/ressources/verification-ouverture.md`.

Tutoie la personne, une seule question par message, des mots simples. Une règle n'entre que si la personne a dit « Ajouter » (voir `${CLAUDE_PLUGIN_ROOT}/ressources/proposer-une-regle.md`).

## 1. Où va la règle ?

Si ce n'est pas déjà dit, demande avec des boutons : **Personnalisation** (pour elle seulement), **Fonctionnement générique** (pour tout le monde), **Règle commune de la famille** (stockage, sécurité, nommage). Recommande le plus logique en premier et dis pourquoi en une phrase.

## 2. Écrire

- **Personnalisation** : dans `~/Studio/mon-espace`. Une règle de style va dans `regles_style.<style>` de sa `marque.json` (et la valeur mesurable dans `reglages`, voir `studio:carrousel`, « Retenir les retours de style ») ; une règle de voix suit `studio:legende` ; le reste va dans `~/Studio/mon-espace/regles.md`. Le plugin ne bouge pas.
- **Fonctionnement générique, et `~/Studio/mon-espace/auteur.json` existe** : modifie le fichier concerné dans les sources du plugin (le skill ou la ressource qui porte cette règle), montre le passage modifié avant de garder, puis, si `~/Socle/moteur/socle.py` existe, lance `python3 ~/Socle/moteur/socle.py tester` et dis le résultat. La règle partira avec la prochaine version stable : ne publie jamais rien toi-même.
- **Fonctionnement générique, sans `auteur.json`** : ne touche pas au plugin. Ajoute la proposition, datée, dans `~/Studio/mon-espace/propositions.md`, puis propose de l'envoyer à l'auteur (par exemple en ouvrant une demande sur le dépôt public du Studio). N'envoie rien sans son accord.
- **Règle commune de la famille** : dépose un signalement au Socle comme le dit `${CLAUDE_PLUGIN_ROOT}/ressources/contrat-magasinier.md`. Si le Socle n'est pas sur cet ordinateur, dis-le simplement.

## 3. Vérifier

Relis ce qui a été écrit et dis en une phrase où se trouve la règle et à partir de quand elle s'applique.

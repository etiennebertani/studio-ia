---
name: start
description: Point d'entrée du Studio IA par Etienne Bertani. Vérifie que tout est installé, accueille l'utilisateur la première fois, puis affiche le menu. Se déclenche sur « /start », « /studio:start », « lance le Studio IA », « démarre le Studio IA ».
---

# Studio IA : démarrage

La personne débute. Parle-lui simplement et tutoie-la, sauf si elle préfère le vouvoiement.

Chaque message :
- dit en une phrase ce qui vient d'être fait ;
- ne demande qu'une seule chose à la fois ;
- ne contient aucun mot technique sans explication ;
- ne montre jamais une erreur brute : tu la corriges, ou tu expliques simplement quoi faire.

Tu fais tout ce qui se fait au clavier. La personne ne tape jamais de commande.

## Où sont les dossiers

Avant toute chose, lance `python3 "${CLAUDE_PLUGIN_ROOT}/moteur/chemins.py"`. Il donne l'emplacement réel de chaque dossier. Dans ce fichier, `<branding>`, `<carrousels>`, `<reels>`, `<archive>` et les autres noms entre chevrons désignent ces emplacements. N'écris jamais un nom de dossier de mémoire.

## 1. Vérifier

Lance cette commande, sans en parler à la personne :

```
python3 "${CLAUDE_PLUGIN_ROOT}/moteur/verifier.py" --data "${CLAUDE_PLUGIN_DATA}"
```

Elle affiche un état au format JSON.

- Si `manque_systeme` n'est pas vide : dis en une phrase ce qu'il manque et à quoi ça sert, demande l'accord, puis installe-le (Mac : `brew install`, un seul paquet par nom). Si Homebrew manque aussi, explique que c'est l'installateur d'outils du Mac et guide l'installation étape par étape.
- Si `moteur_pret` vaut `false` : préviens que ça prend quelques minutes, puis lance :

```
python3 "${CLAUDE_PLUGIN_ROOT}/moteur/preparer.py" --data "${CLAUDE_PLUGIN_DATA}"
```

Relance ensuite la vérification. Si elle échoue encore, lis l'erreur, corrige ce que tu peux, et ne continue pas tant que ce n'est pas réglé.

## 2. Première fois (`configure` vaut `false`)

Une étape par message, dans cet ordre :

1. **Bienvenue.** Présente le Studio en deux phrases : il fabrique des carrousels, des reels, des stories et des posts dans le style de la personne.
2. **Raccourcis.** Propose d'ajouter les commandes courtes, en montrant lesquelles, et attends son accord. Avec son accord, lance :

```
python3 "${CLAUDE_PLUGIN_ROOT}/moteur/raccourcis.py" --creer
```

Si le résultat indique qu'un nom est déjà pris, dis que ce raccourci n'a pas été créé pour ne pas remplacer une commande existante, et que la version longue reste disponible.

3. **Fin de l'accueil.** Lance la commande suivante, puis affiche le menu :

```
python3 "${CLAUDE_PLUGIN_ROOT}/moteur/preparer.py" --data "${CLAUDE_PLUGIN_DATA}" --terminer-accueil
```

## 3. Le menu (`configure` vaut `true`)

Affiche uniquement ce qui existe dans `modules_disponibles`. Si la liste est vide, dis : « Ton Studio est prêt. Les premiers outils de création arrivent bientôt. »

Si `style` est disponible et que `<branding>/` ne contient aucune marque, propose de commencer par créer son style avec le skill `studio:style`.

Termine toujours en disant ce que la personne peut faire ensuite.

## Règles

- Rien ne se publie sans un oui explicite, pour ce contenu précis.
- Ne modifie jamais les fichiers d'origine de la personne.
- Les fichiers personnels vont dans `~/Studio/mon-espace`, jamais dans le dossier du plugin.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

---
name: montage
description: Monte une vidéo à partir d'un rush brut dans le Studio IA. Demande le style, vérifie ce qu'il faut pour ce style, coupe, ajoute titre, sous-titres et images. Se déclenche sur « /montage », « /studio:montage », « monte ma vidéo », « j'ai filmé », « fais-moi un yap », ou quand la personne dépose un rush.
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

**Titre :** si le contenu est dans sa banque Notion, cherche le texte après `HT :`, en lecture `rows`, jamais `sql`. La forme `HT : mon titre (deuxième ligne)` donne l'encadré blanc, et la parenthèse donne l'encadré noir. Reprends ses mots tels quels.

**Images cherchées par le Studio :** seulement à sa demande. Choisis des images libres de droits quand c'est possible, range-les dans `travail/images/` du contenu, et dis clairement ce que tu sais des droits de chaque image. Si les droits sont incertains, dis-lui de ne pas publier sans vérifier.

**Plans de coupe :** elle les dépose dans `<b_roll>`. Tu ne vas pas en chercher à sa place.

## 5. Créer le dossier du contenu

`<reels>/NNN. Titre court`, avec le numéro de sa banque s'il existe, sinon le numéro suivant. Si le dossier existe déjà, utilise-le.

## 6. Écouter et proposer le plan

```
$PY "$M/monter.py" analyser --dossier "<contenu>" --style <style> --marque <marque> --rush "<fichier>"
```

Il y a un `--rush` par fichier. Le résultat liste les retraits proposés. Lis `travail/transcription.txt` : chaque mot a un numéro, et les mots proposés au retrait sont entre crochets.

Corrige `travail/plan.json` :

- `passages` : les morceaux gardés, dans l'ordre final, en numéros de mots `[premier, dernier]`.
  - Garde la meilleure prise de chaque phrase, en général la dernière.
  - Une idée dite deux fois : garde-en une.
  - Une intro refaite à la fin du rush passe en premier.
  - Enlève les hésitations, les faux départs et ce qui s'adresse au tournage.
- `corrections` : `{"numéro": "mot corrigé"}`, pour les noms, les chiffres, les majuscules au milieu d'une phrase et les mots mal entendus. Écoute ce qui a été dit : ne change jamais le sens ni la formulation. Si tu doutes d'un mot, demande.
- `titre` : le texte du titre.
- `images` : `[{"fichier": "travail/images/x.png", "mot": 35, "duree": 1.5}]`, seulement si elle l'a demandé. `mot` est le numéro du mot où l'image apparaît.
- `plans_de_coupe` : `[{"fichier": "<chemin>", "mot": 20, "duree": 1.5}]`, seulement si elle l'a demandé.

**Montre le plan avant de couper :** le texte gardé, puis ce qui part, avec la raison en quelques mots. Attends son accord.

## 7. Couper et fabriquer

```
$PY "$M/monter.py" couper --dossier "<contenu>"
$PY "$M/monter.py" rendre --dossier "<contenu>"
$PY "$M/monter.py" controler --dossier "<contenu>"
```

Si `rendre` renvoie des `alertes`, traite-les : un titre trop long se raccourcit avec son accord.

Avant de lui montrer la vidéo :

1. Ouvre `planche` et regarde chaque image : titre et sous-titres hors du visage, rien sous les interfaces d'Instagram.
2. `mots_manquants` et `mots_en_trop` doivent être vides, ou s'expliquer par une différence d'écoute sans importance. Si un mot manque vraiment, corrige `plan.json` et recommence.
3. `plus_long_blanc` ne doit pas dépasser `blanc_limite`. La voix doit démarrer tout de suite : `voix_demarre_a` proche de 0.

Envoie ensuite la vidéo avec, en une phrase, sa durée et ce qui a été enlevé. Dis ce que tu n'as pas pu vérifier.

## 8. Corriger

Modifie `plan.json`, relance les commandes de la section 7 : chaque essai devient une nouvelle version dans `travail/export/`. Les rushs ne changent jamais.

## 9. Valider

Seulement après un oui clair pour cette vidéo, lance :

```
$PY "$M/monter.py" valider --dossier "<contenu>"
```

`final/` contient alors la version avec sous-titres et la version sans sous-titres. Propose ensuite la légende avec le skill `studio:legende`. Quand la vidéo et la légende sont validées et que Drive est branché, applique le skill `studio:drive`, section « Terminer un contenu validé ».

## Règles

- Rien n'est publié par ce skill.
- Aucune transition, aucun zoom automatique.
- Le Yap est en voix seule.
- Une musique n'est jamais générée par IA.
- Ne supprime jamais les signatures ou marques d'une vidéo destinées aux plateformes, et ne cherche jamais à contourner leur détection.
- Ne modifie jamais le dossier du plugin.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

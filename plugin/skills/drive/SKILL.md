---
name: drive
description: Branche le Studio IA sur un dossier Google Drive et termine un contenu validé dans Drive et dans la banque Notion. Se déclenche sur « /drive », « /studio:drive », « branche mon Drive », « envoie sur mon Drive ».
---

# Studio IA : Drive

La personne débute. Tutoie-la, sauf si elle préfère le vouvoiement. Une seule question par message, des mots simples, jamais d'erreur brute.

Dans ce fichier, `$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur`.

Ce branchement est facultatif. Sans Drive ou sans le template Notion, le Studio fonctionne normalement et ne réclame rien.

## Où sont les dossiers

Lance `python3 "$M/chemins.py"`. Il donne l'emplacement réel de chaque dossier local. Lis `drive_contenu` et `banque_notion` dans le fichier indiqué par `config`.

## 1. Brancher Drive (une seule fois)

1. Demande si l'application Google Drive pour ordinateur est installée. Sinon, explique comment l'installer et attends.
2. Demande quel dossier de son Drive doit recevoir ses contenus. Il se trouve dans `~/Library/CloudStorage/GoogleDrive-…`.
3. Lance `python3 "$M/drive.py" configurer --dossier "<dossier>"`. Les dossiers numérotés manquants sont créés, sans rien toucher à l'existant.
4. Si ce dossier contient déjà des fichiers en vrac, ne range rien de ta propre initiative. Propose une liste « ancien emplacement / nouvel emplacement », et ne déplace rien sans son accord pour cette liste. Ne supprime jamais rien. Vérifie ensuite que le nombre de fichiers n'a pas changé.

## 2. Terminer un contenu validé

Applique cette section quand la personne valide un contenu fini. Cette validation vaut accord pour les opérations de cette section, sur ce contenu. Ne repose pas la question, sauf dans les cas indiqués.

Si `drive_contenu` n'est pas réglé, arrête-toi ici sans rien dire.

1. **Envoyer.** Lance `python3 "$M/drive.py" envoyer --contenu "<dossier du contenu>"`. Si le design ou la légende manque (`design_absent`, `legende_absente`), dis-le simplement et arrête-toi.
2. **Attendre l'arrivée.** Lance `python3 "$M/drive.py" etat --contenu "<dossier du contenu>"`. Tant que `arrive` vaut `false`, réessaie toutes les 30 secondes, pendant 5 minutes au maximum. Si ce n'est toujours pas arrivé, dis que l'envoi continue et que tu finiras quand elle relancera la commande. N'écris rien dans Notion.
3. **Sauvegarder.** Lance `python3 "$M/drive.py" sauvegarder`.

Si `banque_notion` n'est pas réglé, ou si le contenu ne vient pas d'une page de la banque, arrête-toi ici et donne le lien du dossier.

4. **Lire la page Notion.** Ouvre la page du contenu : c'est elle qui fait foi. Pour lire la banque, utilise toujours le mode `rows`, jamais `sql`, qui a déjà renvoyé des statuts faux. Vérifie que la propriété `Lien Drive` et l'option `📦 Prêt` de `Status` existent. Sinon, arrête-toi sans rien écrire : ce n'est pas le template.
5. **Ne rien écraser.** Arrête-toi et demande à la personne si :
   - `Lien Drive` contient déjà un autre lien ;
   - `Status` vaut `✅ Publié`, `♻️ Recyclage` ou `🗂 Archives`.
6. **Écrire.**
   - Si la page n'a pas de section `✍️ Légende`, ajoute les légendes de `final/legendes.txt` à la fin. Si elle en a une différente, garde-la et signale-le.
   - Mets le lien renvoyé par l'étape 2 dans `Lien Drive`.
   - Passe `Status` à `📦 Prêt`.
   - Ne change aucune autre propriété.
7. **Vérifier.** Relis la page. Si le lien ou le statut ne correspond pas, dis-le clairement.
8. **Fêter.** Compte les fiches au statut `📦 Prêt`, en mode `rows`, et dis par exemple : « C'est prêt ! Tu as 3 contenus en stock. » Donne le lien du dossier.

## Depuis Drive vers l'ordinateur

Seulement à la demande : quand la personne demande un fichier précis de son Drive, copie-le dans le bon dossier local du contenu. Il n'y a jamais de synchronisation automatique dans ce sens.

## Règles

- La copie va de l'ordinateur vers Drive et ne supprime rien sur Drive.
- Le plugin et les brouillons ne vont jamais sur Drive.
- Rien n'est publié par ce skill.
- Ne passe jamais un contenu à `✅ Publié`.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

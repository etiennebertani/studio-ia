---
name: drive
description: Branche le Studio IA sur un dossier Google Drive et termine un contenu validé dans Drive et dans la banque Notion. Se déclenche sur « /drive », « /studio:drive », « branche mon Drive », « envoie sur mon Drive ».
---

# Studio IA : Drive

Avant toute autre chose, applique en silence `${CLAUDE_PLUGIN_ROOT}/ressources/verification-ouverture.md`.

La personne débute. Tutoie-la, sauf si elle préfère le vouvoiement. Une seule question par message, des mots simples, jamais d'erreur brute.

Dans ce fichier, `$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur`.

Ce branchement est facultatif. Sans Drive ou sans le template Notion, le Studio fonctionne normalement et ne réclame rien.

## Contrat du magasinier

Version attendue : contrat v6.

Avant de ranger, renommer ou déplacer un fichier dans un stockage, lis `${CLAUDE_PLUGIN_ROOT}/ressources/contrat-magasinier.md` s'il existe :
- s'il porte la version attendue, applique ses règles en plus de celles de ce skill ; si deux règles se contredisent, la plus prudente gagne ;
- s'il est absent, travaille comme d'habitude, sans rien réclamer ;
- s'il porte une autre version, travaille comme d'habitude et dis en une phrase : « le contrat du magasinier n'est pas celui attendu ».

Au début de ce skill, lis aussi `${CLAUDE_PLUGIN_ROOT}/ressources/annonces-magasinier.md` s'il existe, et présente à la personne les annonces `ouverte`. Pour une incohérence, dépose un signalement comme le dit le contrat, sans changer la règle toi-même.

Quand une règle du contrat t'empêche de faire ce que la personne demande, refuse en trois temps : ce que tu ne fais pas, pourquoi (ce que la règle protège), et ce que tu peux faire à la place, à son choix, en boutons. N'insiste pas et ne fais jamais l'action refusée.

Emplacements propres : le dossier du plugin et les dossiers `chantier-*` de l'ordinateur. Ils ne vont jamais dans le Drive des contenus. Seul le miroir de sauvegarde du plugin, choisi par la personne avec le magasinier, en reçoit une copie.

Dossier personnel : `~/Studio/mon-espace` (marque, styles, voix, contenus, réglages). Les mises à jour ne le touchent jamais.

Commande d'entrée : `/studio:start`.

Proposer une règle : quand une façon de faire durable apparaît, propose-la comme le dit `${CLAUDE_PLUGIN_ROOT}/ressources/proposer-une-regle.md` (personnalisation, fonctionnement générique ou règle commune de la famille, avec des boutons), puis écris-la avec `/studio:regles`.

Choix en boutons : chaque fois que tu proposes des choix (y compris après un refus), affiche-les en boutons avec l'outil de question à choix, quatre au plus, ta recommandation en premier.

Compte rendu de fin de session : pas de compte rendu après chaque réponse. Quand la personne s'arrête, fais le compte rendu de fin de session du contrat (Fait, État, Reste à faire, La prochaine fois) et garde-le dans `~/Studio/mon-espace/derniere-session.md`.

Mises à jour et miroir : la veille tourne à chaque ouverture (voir `ressources/verification-ouverture.md`). Si la personne demande de sauvegarder le Studio, lance `python3 "$M/veille.py" miroir`. S'il répond qu'aucun dossier n'est choisi, explique pourquoi tu ne copies rien, puis **choisis avec la logique du magasinier**, dans cette session :
1. Le miroir est commun à toute la famille : cherche d'abord où les autres outils ont déjà leur sauvegarde ou leur miroir (par exemple un dossier `Skills` qui contient déjà `Secrétaire` ou `Socle`) et propose ce dossier-là comme base. Sinon, propose le dossier le plus logique dans l'espace personnel de la personne, jamais chez un client.
2. Dis en une phrase pourquoi, et demande avec des boutons : ce dossier (recommandé), un autre dossier, plus tard.
3. Après son accord seulement : `python3 "$M/veille.py" choisir-miroir "<dossier>"`, puis `python3 "$M/veille.py" miroir`, et dis le résultat de la vérification (nombre de fichiers, différences).

Ne modifie jamais ce contrat ni ses annonces : ce sont des copies.

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
8. **Contrôler.** Lance `python3 "$M/controle_fin.py" contenu --dossier "<dossier du contenu>"`, puis vérifie chaque point de `a_confirmer`. Tant que `ok` vaut `false`, traite ce qui manque ou dis-le clairement, et ne dis jamais que le contenu est prêt. Si le contrôle donne un Lien Drive différent de celui de la fiche (dossier renommé, déplacé ou fusionné), montre l'ancien et le nouveau, puis mets la fiche à jour avec l'accord de la personne.
9. **Fêter.** Compte les fiches au statut `📦 Prêt`, en mode `rows`, et dis par exemple : « C'est prêt ! Tu as 3 contenus en stock. » Donne le lien du dossier.

## Depuis Drive vers l'ordinateur

Seulement à la demande : quand la personne demande un fichier précis de son Drive, copie-le dans le bon dossier local du contenu. Il n'y a jamais de synchronisation automatique dans ce sens.

## Règles

- **Chaque mise à jour d'un contenu déjà livré** (nouvelle version, slides remplacées, dossier renommé ou fusionné) repasse par l'envoi, l'attente et le contrôle de fin. Remplacer un fichier garde le même dossier Drive : le lien de la fiche reste bon, mais le contrôle le vérifie quand même.

- La copie va de l'ordinateur vers Drive et ne supprime rien sur Drive.
- Le plugin et les brouillons ne vont jamais dans le Drive des contenus (seul le miroir de sauvegarde, choisi par la personne, reçoit une copie du plugin).
- Rien n'est publié par ce skill.
- Ne passe jamais un contenu à `✅ Publié`.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.

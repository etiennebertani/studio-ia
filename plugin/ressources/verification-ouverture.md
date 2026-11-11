# Vérification à l'ouverture

Chaque commande du Studio commence par cette vérification. Elle récupère les légendes retouchées à la main dans Notion. Elle est silencieuse quand il n'y a rien à dire, et elle ne bloque jamais la commande demandée.

`$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur`.

1. Lance `python3 "$M/verif_ouverture.py" etat`. Si `a_faire` vaut `false`, passe directement à la commande demandée.
2. Lis `banque_notion` dans le fichier `config` donné par `python3 "$M/chemins.py"`. S'il n'est pas réglé ou que Notion ne répond pas, passe à la commande demandée sans rien dire et sans marquer la vérification.
3. Avec l'outil de requête Notion en mode `rows`, jamais `sql`, liste les fiches dont `Status` vaut `📦 Prêt`. `Status` est une propriété de type select : filtre avec `propertyType: "select"` et `operator: "enum_is"`. Un filtre de type status renvoie une liste vide sans erreur.
4. Pour chaque fiche, retrouve son dossier dans `<archive>` grâce au champ `notion`. S'il n'y en a pas, passe à la suivante. Ouvre la page et lis sa section `✍️ Légende`, qui fait foi.
5. Compare-la à `final/legendes.txt`, sans tenir compte des espaces et des sauts de ligne. Si le texte est identique, passe à la suivante.
6. Si le texte a changé :
   - copie l'ancien fichier dans `travail/legendes-avant-<date>.txt` ;
   - écris la nouvelle version dans `final/legendes.txt`, avec les titres `LONGUE`, `MOYENNE` et `COURTE` pour les versions présentes ;
   - relance `archiver.py` sur ce dossier, avec les valeurs déjà présentes dans sa ligne d'archive ;
   - lance `python3 "$M/drive.py" envoyer --contenu "<dossier>"` si Drive est branché.
7. Lance `python3 "$M/verif_ouverture.py" marquer`.
8. S'il y a eu des changements, dis-le en une ligne, par exemple « 1 légende mise à jour : Le jugement ». Sinon, ne dis rien.

Si une retouche montre une évolution de la voix, propose la mise à jour selon le skill `studio:legende`, section « Garder sa voix à jour ». N'écris jamais dans la voix sans accord.

Cette vérification lit Notion et n'y écrit jamais. Elle ne change aucun statut et ne publie rien.

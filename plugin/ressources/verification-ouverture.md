# Vérification à l'ouverture

Chaque commande du Studio commence par cette vérification. Elle récupère les légendes retouchées à la main dans Notion. Elle est silencieuse quand il n'y a rien à dire, et elle ne bloque jamais la commande demandée.

`$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur`.

0. **Mises à jour.** Lance `python3 "$M/veille.py" etat`.
   - Si `nouveautes` existe (le Studio vient d'être installé ou mis à jour) : dis en une ligne « Tu es en version <installee>. Ce qui change : » puis les points de `nouveautes`, en trois lignes au plus. Lance ensuite `python3 "$M/veille.py" vu`.
   - Si `choix_fait` vaut `false` : demande une seule fois, avec des boutons, « Comment veux-tu recevoir les nouvelles versions du Studio ? » :
     **Me prévenir chaque semaine (recommandé)** — le Studio te dit quand une version sort et te guide ;
     **Mises à jour automatiques** — Claude Code les installe seul, le Studio te dit ensuite ce qui a changé ;
     **Chaque mois** ; **Jamais** (tu peux changer d'avis plus tard).
     Puis lance `python3 "$M/veille.py" rythme semaine|auto|mois|jamais`. Pour « Mises à jour automatiques », guide la personne pas à pas, une étape par message : 1) tape `/plugin` ; 2) ouvre l'onglet des catalogues (marketplaces) ; 3) choisis `studio-ia` ; 4) active la mise à jour automatique. Demande-lui ensuite ce qu'elle voit. Si l'option n'apparaît pas (c'est le cas quand le Studio est installé depuis un dossier de l'ordinateur et non depuis GitHub), dis-le franchement : les nouvelles versions lui seront alors annoncées chaque semaine, et elle les installera avec ton guide.
   - Si `nouvelle` vaut `true` : dis en trois lignes « Une nouvelle version du Studio est disponible (<installee> → <publiee>). Tu veux l'installer ? », avec des boutons. Si oui, guide pas à pas : taper `/plugin`, mettre à jour le catalogue `studio-ia`, puis le plugin `studio`, puis ouvrir une nouvelle session. N'installe jamais rien toi-même.
   - Dans tous les autres cas (déjà vérifié, `erreur`, veille coupée), ne dis rien et continue.
0b. **Annonces.** Si `${CLAUDE_PLUGIN_ROOT}/ressources/annonces-magasinier.md` existe et contient une annonce `ouverte`, présente-la en deux lignes et demande si on l'applique maintenant. Sinon, ne dis rien.
0c. **La dernière fois.** Seulement pour `/studio:start` : si `~/Studio/mon-espace/derniere-session.md` existe, rappelle-le en deux lignes (« La dernière fois… », puis ce qui reste à faire) avant le menu.
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

## Pour toutes les commandes du Studio

- **Choix en boutons** : chaque fois que tu proposes des choix, affiche-les en boutons avec l'outil de question à choix (quatre au plus, ta recommandation en premier). Sans cet outil, une liste numérotée courte.
- **Proposer une règle** : quand une façon de faire durable apparaît, suis `${CLAUDE_PLUGIN_ROOT}/ressources/proposer-une-regle.md`, puis `/studio:regles` sur « Ajouter ».
- **Compte rendu de fin de session** seulement, jamais après chaque réponse : quand la personne s'arrête, écris Fait, État, Reste à faire, La prochaine fois, dans `~/Studio/mon-espace/derniere-session.md` (le précédent est remplacé), puis montre-le.

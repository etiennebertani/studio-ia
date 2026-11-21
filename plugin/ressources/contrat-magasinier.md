# Contrat du magasinier v6

Version du contrat : 6

État : le magasinier est en construction. Aucune commande du magasinier n'existe encore. Ce contrat donne les règles communes que chaque outil applique dès maintenant quand il touche au stockage (Drive, dossier synchronisé, disque), et la façon dont les outils et le Socle se parlent.

Ce fichier est une copie. La source est dans le Socle et seul son propriétaire la change. Un outil ne modifie jamais ce contrat.

## La famille d'outils

**Commande d'entrée.** Chaque outil a une commande `/<outil>:start`. La première fois, elle installe, configure et personnalise ; ensuite, elle vérifie et affiche le menu. C'est elle (ou la vérification qu'elle lance) qui fait la veille des mises à jour et lit les annonces.

**Dossier personnel.** Toute la personnalisation d'une personne (marque, style, voix, espaces, règles, choix) vit dans `~/<Outil>/mon-espace/`, jamais dans le plugin. Une mise à jour remplace le plugin et ne touche jamais ce dossier. Si une nouvelle version doit changer la forme des données personnelles, elle en fait d'abord une copie de secours et demande l'accord de la personne. Chaque outil déclare son dossier personnel dans ses règles, sous la forme « Dossier personnel : … ».

**Choix en boutons.** Chaque fois qu'un outil propose des choix (y compris les solutions de remplacement après un refus), il les affiche en boutons avec l'outil de question à choix quand il existe : quatre au plus, celui qu'il recommande en premier, et la réponse libre (« Autre ») toujours possible. Là où les boutons n'existent pas, il donne une liste numérotée courte.

**Compte rendu de fin de session.** Pas de compte rendu après chaque réponse : le résultat d'une action se dit en une phrase quand il compte. À la fin d'une session (quand la personne dit qu'elle s'arrête, ou quand l'outil le propose une fois la tâche finie), l'outil fait un compte rendu de fin de session, en quelques lignes et en mots simples :
- **Fait** : ce qui a été fait (ou refusé) pendant la session ;
- **État** : ce qui est vérifié, et ce qui ne l'est pas ;
- **Reste à faire** ;
- **La prochaine fois** : ce qui se passera au prochain lancement.
Il dit la vérité : rien n'est annoncé comme fait ou vérifié s'il ne l'est pas. Il est gardé dans `~/<Outil>/mon-espace/derniere-session.md` (le précédent est remplacé). Au prochain `/<outil>:start`, l'outil le rappelle en deux lignes (« La dernière fois… ») avant le menu.

**Proposer une règle.** Quand un outil découvre une façon de faire qui va durer (une correction de la personne, un cas tranché qui reviendra, une manière de faire qui s'avère meilleure), il propose de l'inscrire. Il écrit la règle telle qu'elle entrerait, en une ou deux phrases, dit où elle irait, et demande avec des boutons : **Ajouter**, **Modifier le texte**, **Pas maintenant**, **Jamais pour ce cas**. Trois propositions au plus par session, les plus utiles d'abord. Aucune règle n'entre sans « Ajouter ».

Il y a trois endroits possibles, et l'outil dit lequel il propose et pourquoi :
1. **Personnalisation** : la règle n'a de sens que pour cette personne. Elle va dans `~/<Outil>/mon-espace/`, le plugin ne bouge pas, et une mise à jour ne l'efface pas.
2. **Fonctionnement générique** : la règle serait meilleure pour tout le monde.
   - Si la personne est l'auteur de l'outil (son dossier personnel contient `auteur.json`), la règle entre dans les sources du plugin avec `/<outil>:regles`, passe la batterie, et partira avec la prochaine version stable publiée ; tout le monde la recevra par la veille.
   - Sinon, l'outil ne touche pas au plugin : il note la proposition dans `~/<Outil>/mon-espace/propositions.md` et propose de l'envoyer à l'auteur. Rien n'est envoyé sans l'accord de la personne.
3. **Règle commune de la famille** (stockage, sécurité, nommage) : un signalement au Socle, comme ci-dessous.

Chaque outil a la commande `/<outil>:regles` pour écrire une règle validée au bon endroit.

**Publication.** Chaque outil a un dépôt public générique (`<outil>-ia`), sans aucune personnalisation, qui ne reçoit que des versions stables étiquetées ; et un dépôt privé (`<outil>-ia-perso`) pour le travail et les personnalisations de son auteur. La veille ne lit que le dépôt public : elle ne propose donc jamais une version en essai.

## Qui le lit

Tout outil qui le reçoit (le Studio, la Secrétaire, et les suivants), avant de ranger, renommer, déplacer ou nettoyer un fichier dans un stockage.

## Les trois cas

1. **Contrat présent, version attendue** : l'outil applique les règles ci-dessous en plus des siennes. Si deux règles se contredisent, la plus prudente gagne.
2. **Contrat absent** : l'outil travaille comme avant, seul. Il ne réclame rien et ne s'arrête pas.
3. **Contrat d'une autre version** : l'outil travaille comme avant, seul, et le signale en une phrase : « le contrat du magasinier n'est pas celui attendu ». Il ne plante jamais.

## Le stockage et ses espaces

- **Un espace a une liste blanche de dossiers de départ.** Elle est écrite nommément dans la description de l'espace (un ou plusieurs dossiers). L'outil ne range, ne renomme et ne déplace que dans ces dossiers et leurs sous-dossiers.
- **Un dossier hors de toute liste blanche n'appartient à aucun espace** : on n'y écrit pas. Un nouveau dossier n'entre dans un espace que quand la personne l'ajoute à la liste.
- **Un espace sans liste blanche** n'a pas encore de frontière : l'outil n'y renomme et n'y déplace rien, il range seulement les fichiers neufs aux chemins déjà prévus par ses règles, et il le signale.
- **Les emplacements propres d'un outil** (ses copies de travail, sa sauvegarde, sa copie source) ne font partie d'aucun espace. Chaque outil les déclare dans ses règles. Il peut y remplacer ses fichiers, ou mettre à la corbeille ses propres fichiers de travail, seulement si leur historique existe ailleurs (GitHub, versions). Jamais un fichier d'un espace dans un emplacement propre.

## Règles communes

1. **Un seul espace à la fois.**
2. **Rien n'est perdu.** Aucune suppression définitive. Jamais écraser un fichier que l'outil n'a pas produit lui-même : si le nom existe déjà, l'outil s'arrête et le dit.
3. **Ranger un fichier neuf** est permis : au bon endroit, nommé selon la convention de nommage.
4. **Renommer ou déplacer un fichier existant** se fait seulement après une liste « ancien → nouveau » validée par la personne, avec le nombre de fichiers compté avant et après.
5. **Corbeille.** Dans un espace, elle est réservée à la fin d'un audit du magasinier, validé par la personne. Cet audit n'existe pas encore : aucun outil ne met un fichier d'un espace à la corbeille.
6. **Compta, contrats et juridique** ne sont jamais réorganisés sans accord explicite, un dossier à la fois.
7. **Ce qui pointe vers un fichier** (fiche Notion, règle, document) est mis à jour en même temps que lui. Sinon, le renommage n'a pas lieu.

## Refuser, expliquer, proposer

Dans toutes les zones sensibles (suppression, corbeille, écrasement, renommage ou déplacement en masse, dossier hors liste blanche, compta, contrats, juridique), quand une règle empêche ce que la personne demande, l'outil ne dit jamais seulement « non ». Il répond toujours en trois temps, avec des mots simples :

1. **Ce qu'il ne fait pas** : « Je ne mets pas ce doublon à la corbeille. »
2. **Pourquoi** : la règle et ce qu'elle protège. Par exemple : « Une facture se garde dix ans, et deux fichiers qui se ressemblent ne sont pas toujours identiques. Une erreur ici ferait perdre une preuve. »
3. **Ce qu'il peut faire à la place**, au choix de la personne. Par exemple : « Je peux vérifier si les deux fichiers sont exactement identiques, le mettre de côté dans « À supprimer » avec une note, ou te signaler le doublon pour l'audit de fin. Lequel veux-tu ? »

La personne apprend ainsi les règles de sécurité en s'en servant, sans mode d'emploi. L'outil n'insiste pas et ne fait jamais l'action refusée, même si on lui redemande : la seule façon de changer une règle est un signalement au Socle.

## Se parler : signalements et annonces

Les outils ne s'appellent pas entre eux. Ils se laissent des messages, lus au démarrage. Rien ne change sans l'accord de la personne.

**Signalement (outil → Socle).** Quand un outil voit une incohérence (une règle qui manque ou se contredit, un chemin hors liste blanche, une copie pas à jour), il ne corrige pas la règle lui-même. Il dépose un fichier dans `~/Socle/boites/signalements/`, nommé `aaaa-mm-jj-<outil>-<sujet-court>.md`, avec :
- `Outil :` son nom ;
- `Vu :` ce qu'il a constaté, avec le chemin ou la règle ;
- `Proposition :` ce qu'il propose ;
- `Statut : ouvert`.

Si ce dossier n'existe pas (le Socle n'est pas sur cet ordinateur), il le dit simplement à la personne.

**Mise à jour directe par le Socle.** Quand la session d'un outil est en pause (la personne le confirme) et qu'il n'a aucun travail non sauvegardé, le Socle peut appliquer lui-même une annonce dans cet outil, en passant par la sauvegarde de l'outil, puis la marquer « faite par le Socle ». Quand la session de l'outil travaille, le Socle laisse une annonce et n'écrit pas chez lui.

**Annonce (Socle → outil).** Le Socle laisse à chaque outil un fichier `annonces-magasinier.md`, à côté de ce contrat. Au démarrage, l'outil lit les annonces `ouverte`, les présente à la personne, et applique ce qui le concerne après son accord. Quand c'est fait, il dépose un signalement « annonce <numéro> faite ». Seul le Socle ferme une annonce.

## Mises à jour et miroir

Chaque outil de la famille suit la même logique, avec le module commun `moteur/veille.py` (une copie du Socle, à ne jamais modifier) et un fichier à lui, `ressources/veille.json`, qui dit où sa version est publiée (`depot`, ou `null` s'il n'est pas public).

**Veille.** Au démarrage, l'outil lance `veille.py etat`. Le module ne vérifie qu'une fois par rythme (une semaine par défaut ; la personne peut choisir mois ou jamais). S'il y a une version plus récente :
1. l'outil le dit en trois lignes : la version installée, la nouvelle, et ce que la personne doit faire ;
2. il demande : « Tu veux l'installer ? » ;
3. si oui, il guide la personne pas à pas (mettre à jour le catalogue, puis le plugin, puis ouvrir une nouvelle session) ; il n'installe jamais rien tout seul.
Une erreur réseau ne bloque jamais l'outil : il passe à la suite sans rien dire.

**Miroir.** Sur demande de la personne, l'outil lance `veille.py miroir`. Le dossier du miroir n'est jamais choisi par l'outil : c'est le magasinier qui le propose (le plus logique dans l'arborescence de la personne, en expliquant pourquoi), la personne qui décide, et le choix est noté dans `~/Magasinier/mon-espace/config.json`. Sans magasinier, l'outil demande directement le dossier à la personne et note son choix avec `veille.py choisir-miroir`, au même endroit : le magasinier le reprendra s'il est installé plus tard. Sans choix, l'outil ne copie rien et le demande. La veille et le miroir marchent donc aussi quand l'outil est téléchargé seul. Le miroir garde chaque version dans son propre dossier ; une version déjà en miroir est vérifiée, jamais écrasée. La copie est vérifiée par empreintes.

## Ce que l'outil ne fait pas

- Appeler une commande du magasinier qui n'est pas listée ici. En v6, il n'y en a aucune. Le module commun `moteur/veille.py` n'est pas une commande du magasinier : c'est une copie du Socle, comme le moteur de nommage.
- Inventer une règle de rangement qui manque : il la signale, et elle devient une question à la personne.
- Modifier ce contrat ou ses annonces : ce sont des copies.

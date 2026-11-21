# CONVENTION DE NOMMAGE — v1.5

**Document de référence unique**, pour les contenus, les pièces comptables et les documents. Tous les skills (Studio, Secrétaire, assistant Drive) l'appliquent avec le même moteur.

**Deux couches :**
1. **Cette convention** dit la **forme** des noms. Elle est la même pour tout le monde.
2. **L'espace** de chaque personne ou entreprise dit **sa réalité** : ses noms courts de clients et de fournisseurs, ses règles en plus, ses chemins d'archivage. **L'espace passe toujours avant.**

Source : le Socle (`~/Socle`), recopié dans chaque skill et sur le Drive à chaque mise à jour. Ne modifie jamais une copie : modifie le Socle.

> **Nouveautés**
> - **v1.5 (21/11/2026) :** une seule convention pour SPEAK, le Studio et la Secrétaire (fusion de la v1.4 SPEAK, de la v1.1 et de la convention du Studio). Nouveaux types **pièces comptables** (`facture`, `avoir`, `recu`, `releve`, `devis`, `contrat`) et **`doc`**. Le numéro d'un réel est son **rang dans le mois**. Codes de format du Studio intégrés. Noms courts et chemins déplacés dans l'espace.
> - **v1.4 (18/11/2026) :** type `carte`, noms courts `lsj` et `bdp`.
> - **v1.3 (16/11/2026) :** dossiers de rushs.
> - **v1.2 (16/11/2026) :** les réels ont leur propre ordre ; cc et nocc dans deux dossiers.

---

## CONSIGNES POUR L'ASSISTANT QUI APPLIQUE CE DOCUMENT

Cette convention est décidée. Elle ne se rediscute pas sur le fond. Mais **avant de l'appliquer quelque part, inspecte l'endroit** et remonte les conflits :
- des fichiers portent-ils déjà un autre nommage ? combien, selon quelle logique ?
- un outil, un script ou des liens lisent-ils les noms actuels ? un renommage les casserait ;
- un fichier n'entre-t-il dans aucun type ?
- les noms courts sont-ils dans l'espace, et sous quelle orthographe ?

**Tu listes, l'utilisateur valide, tu agis. Jamais l'inverse.**
- Aucun renommage sans validation, fichier par fichier ou par lot (liste « ancien nom → nouveau nom »).
- N'étends pas la liste des types : demande.
- En cas de doute sur un champ, demande. Un nom inventé devient une incohérence permanente.

---

## FORMAT GÉNÉRAL

```
aa-mm-[qui]-[type]-[sujet]-[numéro].ext
```

| Champ | Règle | Exemple |
|---|---|---|
| `aa-mm` | année et mois sur 2 chiffres (voir « Quel mois ? ») | `26-11` |
| `qui` | nom court du client ou du fournisseur, acté dans l'espace | `lsj`, `asana` |
| `type` | valeur obligatoire, prise dans la liste fermée | `post` |
| `sujet` | description courte (pour une pièce : sa référence) | `terrasse-coucher-soleil` |
| `numéro` | numéro d'ordre sur 2 chiffres | `01` |

**Quel mois ?**
- Contenu : le mois de **validation**. Le mois de publication se note à part (banque de contenu).
- Carte de restaurant : le mois où elle entre en service.
- Pièce comptable : le mois de la **pièce** (date de la facture), jamais le mois d'archivage.
- Document vivant (`doc`) : le mois de sa création. Il garde son nom à chaque mise à jour, pour ne pas casser les liens.

---

## RÈGLES D'ÉCRITURE — sans exception

- **TOUJOURS en minuscules**
- **TOUJOURS séparé par des tirets**, jamais d'espace ni d'underscore
- **Les accents sont autorisés** — on travaille en français
- **AUCUN point dans le nom.** Le seul point est celui qui précède l'extension
- **Aucune virgule**, aucun caractère spécial autre que le tiret
- Numéro toujours sur 2 chiffres : `01`, `02`…

> ⚠️ Un nom court s'écrit toujours de la même façon. On n'écrit pas `café` une fois et `cafe` la suivante. Le moteur compare les noms **sans tenir compte des accents** pour détecter ces doublons.

---

## TYPES AUTORISÉS — liste fermée

**Aucune autre valeur n'est acceptée.** Un espace peut ajouter ses propres types (`types_en_plus`), jamais en retirer.

### Contenus

| Type | Signification | Ordre des champs |
|---|---|---|
| `post` | publication image au format feed | général |
| `story` | story | général |
| `reel-nocc` | reel **sans** sous-titres | **réel** (numéro puis sujet) |
| `reel-cc` | reel **avec** sous-titres | **réel** (numéro puis sujet) |
| `video-nocc` | vidéo **sans** sous-titres | général |
| `video-cc` | vidéo **avec** sous-titres | général |
| `broll` | plan de b-roll | général |
| `visuel` | visuel graphique | général |
| `carrousel` | carrousel multi-slides | carrousel |
| `carte` | menu ou carte de restaurant (imprimé ou digital) | général, sujet = saison-support-format |

### Pièces comptables et administratives

| Type | Signification |
|---|---|
| `facture` | facture fournisseur ou client |
| `avoir` | avoir ou remboursement |
| `recu` | reçu ou preuve de paiement qui n'est pas une facture |
| `releve` | relevé bancaire ou relevé de compte |
| `devis` | devis envoyé ou reçu |
| `contrat` | contrat ou avenant signé, avec sa preuve de signature |

### Documents

| Type | Signification |
|---|---|
| `doc` | document de référence vivant : process, convention, guide |

---

## LES RÉELS — le numéro est le rang du réel dans le mois

```
aa-mm-[client]-reel-nocc-[numéro]-[sujet].ext
aa-mm-[client]-reel-cc-[numéro]-[sujet].ext
```

**Le numéro vient juste après `cc` / `nocc`** : `01` est le premier réel du mois, `02` le deuxième… Placé là, il garde les réels **dans l'ordre alphabétique** du mois. Le sujet est toujours le dernier champ.

```
26-11-lsj-reel-nocc-01-plat-signature.mp4
26-11-lsj-reel-cc-01-plat-signature.mp4
26-11-lsj-reel-cc-02-terrasse.mp4
```

- Seul `cc` / `nocc` change entre les deux versions d'un même réel.
- **Rangement :** les versions sans et avec sous-titres vont dans **deux dossiers distincts**.
- Avec le Studio, le sujet commence par le **code du format** : `26-11-etienne-reel-cc-03-yapp-mon-sujet.mp4`.

**Codes de format des réels :** `yap`, `yapp` (Yap+), `fce` (face caméra éducatif), `vlog`, `clean` (coupe propre), `os` (one shot), `tenshots`, `infographie` (reel animé), `temoignage`.

---

## LES CARROUSELS

Le numéro de slide s'ajoute à la fin, après le numéro d'ordre du carrousel.

```
aa-mm-[client]-carrousel-[sujet]-[numéro]-slide-[nn].ext
26-11-andrea-carrousel-nouvelle-carte-01-slide-01.jpg
26-11-etienne-carrousel-txti-mon-sujet-01-slide-02.jpg
```

**Codes de format des carrousels** (en tête du sujet, avec le Studio) : `tweet`, `txt` (texte), `txti` (texte + image), `punchline`, `infographie`.

Un carrousel en plusieurs variantes range chacune dans son dossier (`final/noir/`, `final/blanc/`).

---

## LES CARTES DE RESTAURANT

```
aa-mm-[client]-carte-[saison]-[support]-[format]-[numéro].ext
```

| Partie du sujet | Règle | Exemples |
|---|---|---|
| `saison` | saison ou édition | `hiver`, `été` |
| `support` | ce que contient la carte | `food-complète`, `réduite`, `vins-boissons`, `petit-déj`, `vitrine-food` |
| `format` | format **réel** : normalisé, ou largeur x hauteur en mm ; `digitale` pour l'écran | `a4`, `a5`, `140x297`, `465x345` |

- Le format est obligatoire et doit correspondre au fichier réel.
- Pas de virgule : `46,5 x 34,5 cm` s'écrit `465x345`.
- Une seule version à jour par carte dans le dossier de la saison ; la référence est le design Canva.

```
26-11-lsj-carte-hiver-food-complète-a4-01.pdf
26-11-bdp-carte-hiver-digitale-food-boissons-01.pdf
```

**Rangement :** dossier menus du client → année → un dossier par saison `aa-mm-[client]-cartes-[saison]`.

---

## LES B-ROLLS

Le type reste `broll`. Pour un **client restaurant** (marqué dans l'espace), le sujet commence par une catégorie : `1-cuisine`, `2-boissons`, `3-salle`, `4-dehors`.

```
26-11-lsj-broll-1-cuisine-dressage-03.mp4
```

Pour les autres, le sujet décrit le plan.

---

## LES PIÈCES COMPTABLES

```
aa-mm-[fournisseur ou client]-[type]-[référence]-[numéro].ext
```

- `aa-mm` : le mois de la pièce (date de facture).
- `fournisseur ou client` : son nom court, acté dans l'espace (`asana`, `dougs`, `meta`, `lsj`…).
- `référence` : le numéro du document, en minuscules ; tout autre caractère devient un tiret (`INV-EU-10940503` → `inv-eu-10940503`). Sans numéro : un sujet court (`octobre`, `carte-7189`).
- `numéro` : `01` ; `02` seulement si la même pièce a plusieurs fichiers (facture + annexe).
- **Le montant n'est jamais dans le nom** (virgules et points interdits). Il reste dans le journal des pièces et dans le suivi.

```
26-11-asana-facture-inv-eu-10940503-01.pdf
26-08-dougs-facture-1524498-01.pdf
26-10-revolut-releve-octobre-01.pdf
26-11-meta-recu-carte-7189-01.pdf
26-11-moulin-contrat-prestation-cm-01.pdf
```

**Rangement :** dans les dossiers d'archivage de l'espace. Le nom porte l'information ; on ne crée pas de dossier pour classer.

---

## LES DOCUMENTS VIVANTS

```
26-11-speak-doc-convention-de-nommage-01.md
```

Le mois est celui de la création. Le nom ne change pas aux mises à jour : la version est écrite **dans** le document.

---

## DOSSIERS

Les dossiers nommés par la convention suivent les mêmes règles d'écriture, sans numéro d'ordre en préfixe.

```
aa-mm-[client]-rushs-mensuels     ← un dossier par mois de tournage
aa-[client]-rushs-extra           ← rushs rattachés à aucun mois, un par année
aa-mm-[client]-cartes-[saison]    ← cartes d'une saison
```

- Le mois n'est porté que par `aa-mm`, jamais en lettres.
- On écrit toujours `rushs-mensuels`, jamais `rush` seul.
- Les autres dossiers gardent leur nom (numéro et titre).

### Arborescence

**Tout est géré par le nommage, jamais par l'arborescence.** Deux sous-dossiers par client (`Contenu/`, `Archives/`). Exceptions : cc / nocc des réels, dossiers de rushs, saisons des cartes, et les dossiers d'archivage comptable de l'espace.

---

## CE QUI SUIT LA CONVENTION, CE QUI GARDE SON NOM

**Suit :** les fichiers finaux (réels, carrousels, slides, posts, visuels, cartes), les extraits de b-roll de 30 secondes, les pièces comptables archivées, les documents vivants.

**Garde son nom :** les rushs, les musiques, les images ajoutées aux vidéos, les photos sources, `texte.txt`, `legendes.txt`, les fichiers de travail.

**Fichiers déjà là avant la v1.5 :** renommés seulement après une liste validée.

---

## EXEMPLES INVALIDES

| Nom | Pourquoi |
|---|---|
| `26-11-Saint Jean-reel-cc-01-Plat Signature.mp4` | majuscules, espaces, nom court non acté |
| `26-11-lsj-reel-cc-plat-signature-01.mp4` | réel à l'ancien format — le numéro doit suivre `cc` |
| `26-11-andrea-reel-01-nouvelle-carte.mp4` | `reel` seul n'existe pas |
| `26-11-lsj-broll-1.cuisine-dressage-03.mp4` | point dans le nom |
| `26-11-andrea-carrousel-carte-slide-02.jpg` | numéro du carrousel manquant |
| `26_11_andrea_post_terrasse_01.jpg` | underscores |
| `26-11-bdp-carte-hiver-vitrine-46,5x34,5-01.pdf` | virgule |
| `26-11-lsj-menu-hiver-a4-01.pdf` | `menu` n'est pas un type — utiliser `carte` |
| `26-11-asana-facture-01.pdf` | référence manquante |
| `26-11-dougs-facture-26,98-01.pdf` | montant dans le nom |
| `26-09-andrea-rushs-mensuels-septembre` | mois écrit deux fois |

---

## RÈGLES DE DÉCOUPAGE (pour le moteur)

Chaque champ se reconnaît par sa **forme**, pas par sa position :
1. Retirer l'extension, puis le suffixe `slide-NN` s'il existe (carrousel).
2. Les 2 premiers segments = `aa`, `mm`.
3. Chercher le type qui apparaît **le plus tôt** ; à égalité, le plus long (`reel-cc` avant `reel`, `carrousel` avant `carte`).
4. Avant le type = `qui`.
5. Réel : le segment après le type = numéro, le reste = sujet. Un réel avec le numéro à la fin est **signalé** comme ancien format, jamais corrigé en silence.
6. Autres : le dernier segment = numéro, entre les deux = sujet (ou référence).
7. Avec un espace : `qui` doit y être acté ; client restaurant → catégorie de b-roll obligatoire.

---

## POINTS OUVERTS

- `video-cc` / `video-nocc` gardent le numéro à la fin tant que rien d'autre n'est décidé.
- Sous-dossiers de vidéos dans les rushs : non normalisés.
- Noms exacts des deux dossiers cc / nocc à consigner dans l'espace.
- Fichiers d'avant la v1.5 (réels du Studio au numéro final, anciennes factures, anciennes cartes) : à renommer sur liste validée.

---

*Convention de nommage — v1.5 · 21 novembre 2026. Source : le Socle.*

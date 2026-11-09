---
name: style
description: Crée, modifie ou fait varier les styles de carrousel d'une personne dans le Studio IA, à partir de ses inspirations. Se déclenche sur « /style », « /studio:style », « crée mon style », « change mon style », « change ma couleur », « ajoute un style ».
---

# Studio IA : style

La personne débute. Tutoie-la, sauf si elle préfère le vouvoiement. Une seule question par message, des mots simples, jamais d'erreur brute. Montre plutôt que d'expliquer : un aperçu vaut mieux qu'une question sur les couleurs. Tu fais tout ce qui se fait au clavier.

Dans ce fichier, `$M` désigne `${CLAUDE_PLUGIN_ROOT}/moteur` et `$PY` désigne `${CLAUDE_PLUGIN_DATA}/venv/bin/python`.

Tout est enregistré dans `<branding>/<marque>/`, jamais dans le plugin. Une mise à jour du Studio n'y touche pas.

## Où sont les dossiers

Avant toute chose, lance `python3 "${CLAUDE_PLUGIN_ROOT}/moteur/chemins.py"`. Il donne l'emplacement réel de chaque dossier. Dans ce fichier, `<branding>`, `<carrousels>`, `<reels>`, `<archive>` et les autres noms entre chevrons désignent ces emplacements. N'écris jamais un nom de dossier de mémoire.

## 1. Préparer

Lance `python3 "$M/verifier.py" --data "${CLAUDE_PLUGIN_DATA}"`. Si quelque chose manque, lance le skill `studio:start`.

Regarde les marques dans `<branding>/*/marque.json`.
- Aucune marque : passe à « Créer ».
- Une ou plusieurs marques : demande ce que la personne veut faire : modifier un style, ajouter une variante, ou créer une nouvelle marque. Si la demande est déjà claire, ne la repose pas.

## 2. Créer une marque

Une étape par message.

1. **Identité.** Son nom et son pseudo. Sa photo de profil, seulement si elle veut le style Tweet. La coche bleue seulement si son compte est réellement certifié.
2. **Inspirations.** Demande 3 à 5 captures de carrousels qu'elle aime, et ce qui lui plaît dans chacune. Si elle crée déjà dans Canva et que le connecteur est disponible, propose de lire ses propres designs en lecture seule : n'enregistre jamais de modification dans Canva. Ferme toute session d'édition ouverte en l'annulant.
3. **Lecture.** Regarde chaque inspiration. Déduis les couleurs, le type de police, les proportions et la mise en page.
4. **Catégories.** Propose celles qui correspondent à ses inspirations, avec des choix à cliquer. Elle peut en garder de 1 à 4 : `texte-image`, `texte`, `punchline`, `tweet`.
5. **Police.** Propose une police libre proche, puis installe-la : `"$PY" "$M/police.py" "Nom" "<dossier de la marque>"`. Recopie le résultat dans `police` et `polices` de `marque.json`. Si elle veut une police payante, elle doit fournir le fichier et disposer d'une licence adaptée.
6. **Fichier.** Écris `marque.json` (voir plus bas).
7. **Aperçu.** Lance `"$PY" "$M/apercu_styles.py" "<marque.json>" "<dossier de la marque>/planche"`. Si elle a donné un texte à elle, ajoute `--titre` et `--texte`. Regarde le résultat, corrige ce qui est raté, puis montre `<dossier de la marque>/planche/rendu/planche.jpg`.
8. **Ajustements.** Modifie, refais l'aperçu, jusqu'à ce qu'elle valide. Note ensuite `"valide": "<date>"` et `"planche_styles"` dans `marque.json`.

S'inspirer ne veut pas dire copier. Reprends l'esprit, jamais le logo, les illustrations ou l'identité d'un autre compte. Le résultat doit être son style à elle.

## 3. Modifier ou faire varier un style

La personne parle normalement : « change mon jaune », « titres plus gros », « ajoute une version sombre ».

1. Copie `marque.json` dans un dossier temporaire du dossier de la marque, `planche/essai/`, et applique le changement à la copie. Si elle utilise des polices propres, copie aussi le dossier `polices/` à côté.
2. Fabrique l'aperçu à partir de cette copie, dans `planche/essai/`.
3. Montre l'avant et l'après.
4. Seulement après son accord : applique le changement à `marque.json`, écris la règle en une phrase dans `regles_style.<style>`, refais la planche, puis mets `planche/essai/` à la corbeille avec `mv` vers `~/.Trash/`.
5. Sans accord : ne change rien à `marque.json`.

Si elle a déjà validé des carrousels, ne les refais pas d'office. Demande-lui si elle veut en refaire un.

## Le fichier marque.json

```json
{
  "nom": "...",
  "pseudo": "@...",
  "initiales": "..",
  "photo": "chemin de la photo, facultatif",
  "coche": false,
  "police": "Nom de la police",
  "polices": [{"fichier": "polices/....ttf", "graisse": "400", "style": "normal"}],
  "fond_papier": true,
  "couleurs": {
    "papier": "#...", "papier_sombre": "#...", "texte": "#...", "texte_clair": "#...",
    "surlignage_clair": "#...", "surlignage_sombre": "#..."
  },
  "categories": {"texte-image": ["..."], "punchline": ["..."]},
  "regles_style": {},
  "reglages": {
    "typographie": {
      "couverture_titre": {"taille": 120, "graisse": 700, "interligne": 1, "approche": -0.02},
      "couverture_sous_titre": {}, "texte_image": {}, "texte_titre": {}, "texte_sous_titre": {}, "punchline": {}, "pseudo": {}
    },
    "texte-image": {},
    "tweet": {}
  }
}
```

- `fond_papier` à `false` retire la texture : le fond devient une couleur unie, celle de `papier`.
- Pour les titres de couverture, règle aussi `reglages.texte-image.titre_tailles`, de la plus grande à la plus petite.
- Les réglages acceptés dans `reglages.texte-image` et `reglages.tweet` sont listés dans le skill `studio:carrousel`, section « Retenir les retours de style ».

## Limites à dire clairement

Le moteur sait fabriquer ces mises en page : `texte-image` (couverture et slide), `texte`, `punchline`, `tweet`. Si une inspiration demande une mise en page très différente, dis-le simplement, propose la plus proche, et note la demande dans `regles_style`. Ne promets pas ce que le moteur ne sait pas faire.

## Règles

- Ne modifie jamais le dossier du plugin.
- Ne demande jamais de mot de passe ni de jeton dans la conversation.
- Un style ne change jamais le texte de la personne.

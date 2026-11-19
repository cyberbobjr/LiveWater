# ADR-007 — Démontage des équipements et butin

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-007-DEMONTAGE-ET-BUTIN` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | Terminé le 2026-11-19 ; voir le [plan 007](../../ADR-plans/termines/plan-007-demontage-et-butin.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : recettes (`LWT_recipes.txt`), propriétés des tuiles (`source/tiles/build_livewater_tiles.py`, `.tiles`), définitions de démontage du jeu (`ISMoveableDefinitions`), tables de butin (`ProceduralDistributions`), traductions, tests, documentation |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (Q01 : ramassage à la clé), [ADR-004](004-goutte-a-goutte.md) (D05 : recette du goutte-à-goutte), [ADR-005](005-filtre-a-l-arrivee-d-eau.md) |
| Références | `ISMoveableDefinitions.lua` (`addScrapDefinition`, `addScrapItem`, 42.22) ; `ISMoveableSpriteProps.lua:3691-3790` (`scrapObjectInternal` : `transmitRemoveItemFromSquare`, objets rendus selon `ScrapSize`) ; `IsoGridSquare.java:4902` (`OnObjectAboutToBeRemoved`) ; `ProceduralDistributions.lua` |
| Origine | question de l'utilisateur du 2026-11-19 (« est-ce que tous les équipements ont une recette de fabrication et une recette de destruction ? sont-ils dans les tables de butin ? ») et accord sur les deux propositions (« ok pour les deux ») |

## Contexte

Les dix objets du mod ont une recette de fabrication. Aucun ne se détruit : une pièce posée se ramasse entière (clé, ou
à la main pour le goutte-à-goutte), les tuiles n'ont pas `CanScrap` et aucune recette ne démonte un objet de
l'inventaire. Aucun objet n'est dans les tables de butin : tout se fabrique.

## Décisions

- **D01 — Démonter dans l'inventaire** : une recette `Dismantle …` (catégorie Démontage) par équipement :
  - les pièces posables (tuyau, vanne, compteur, arrivée d'eau, pompe, arroseur, arroseur automatique, raccord de
    baril, goutte-à-goutte) ;
  - la cartouche filtrante : elle rend le tissu, jamais le charbon brûlé.

  Chaque recette rend **au plus ce que la fabrication a coûté**, en matériaux dégradés : ferraille, vis, ferraille
  électronique, fil. Une pièce découpée en quatre (tuyau, goutte-à-goutte) ne rend jamais une matière première entière,
  pour qu'on ne puisse pas fabriquer puis démonter en boucle et gagner de la matière.
- **D02 — Démonter sur place, avec le geste du jeu** : les tuiles des pièces posables reçoivent `CanScrap`, un matériau
  propre à LiveWater (`LiveWater<Pièce>`) et `ScrapSize`. Au démarrage, le mod déclare ces matériaux dans
  `ISMoveableDefinitions`, avec l'outil et la compétence de la recette D01 et les mêmes objets rendus. Une seule table
  de données nourrit les deux chemins, et un test vérifie que recette et matériau rendent les mêmes objets.

  Démonter retire la tuile par `transmitRemoveItemFromSquare`, donc par l'événement `OnObjectAboutToBeRemoved`, comme
  le ramassage : la pièce quitte le réseau par le même chemin (`Placement:removed`). Le goutte-à-goutte, qui se ramasse
  à la main et ne rend rien d'utile, n'a pas de démontage sur place : on le ramasse, puis on le démonte dans
  l'inventaire.
- **D03 — Outils et compétences** :
  - pièces de plomberie (tuyau, vanne, compteur, arrivée d'eau, raccord de baril, arroseur) : clé à tuyau (ou clé),
    compétence Entretien ;
  - pièces électriques (pompe, arroseur automatique) : tournevis, compétence Électricité ;
  - goutte-à-goutte et cartouche filtrante : couteau, sans compétence.
- **D04 — Butin, rare et à sa place** : tuyaux, vannes et raccords de baril dans les fournitures de plomberie et les
  caisses à outils ; arroseurs, goutte-à-goutte et cartouches filtrantes dans les jardineries et le matériel agricole.
  La pompe d'étang, l'arrivée d'eau, le compteur et l'arroseur automatique ne se trouvent pas : ils restent des
  fabrications (Électricité 2 pour la pompe et la minuterie). Les poids sont faibles (de l'ordre d'un outil rare de la
  même liste). Les objets sont ajoutés aux listes vanilla au moment de la fusion des tables (`OnPreDistributionMerge`),
  sans en remplacer aucune.

## Conséquences

- Les nouvelles recettes et les matériaux de démontage apparaissent dans la fenêtre d'artisanat et dans le menu
  « Démonter » du jeu ; leurs noms sont traduits dans les onze langues.
- Les tuiles sont réempaquetées (seules les propriétés changent, les images restent les mêmes).
- Démonter une arrivée d'eau qui porte une cartouche fait comme la ramasser : même chemin de retrait.

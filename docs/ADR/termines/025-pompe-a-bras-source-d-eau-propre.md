# ADR-025 — La pompe à bras du jeu est une source d'eau propre

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-025-POMPE-A-BRAS-SOURCE-D-EAU-PROPRE` |
| Date de création et de mise à jour | 2026-11-22 |
| Statut | Accepté (2026-11-22) |
| Avancement | Terminé le 2026-11-22 ; voir le [plan 025](../../ADR-plans/termines/plan-025-pompe-a-bras-source-d-eau-propre.md) |
| Décideur | l'utilisateur (« ADR-025 […] puis l'implémentation avec un passage en jeu : oui », 2026-11-22) |
| Portée | `batman_LiveWater` : sorte de source `well` (`Sources/LWT_SourceWell.lua`), wiki, spécifications, CHANGELOG, scénario en jeu |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D16 sources, D24 puits, P02) |
| Références | définitions de tuiles du jeu 42.22 (`media/tile_definitions/newtiledefinitions.tiles`) : `camping_01_16` (puits en pierre) et `camping_01_64` à `camping_01_67` (pompe à bras, une tuile par orientation) portent `waterAmount = 999999`, `waterMaxAmount = 999999`, sans `taintedWater` |
| Origine | question d'un joueur du 2026-11-22 (la pompe se branche-t-elle sur le puits à pompe métallique ?) |

## Contexte

La pompe à eau de LiveWater puise dans une eau naturelle, un baril, une pompe de station-service ou un puits. Seul le
puits en pierre du jeu était reconnu comme puits. Le jeu a un second point d'eau propre et sans fond sur sa carte, la
pompe à bras en métal : une pompe posée contre elle était refusée (« Doit être posée au bord d'une eau naturelle… »).

## Décisions

- **D01 — La pompe à bras est un puits.** Les quatre tuiles `camping_01_64` à `camping_01_67` rejoignent la sorte de
  source `well` : une pompe à eau se pose sur une des 8 cases autour, tire de l'eau propre, et la maison la reçoit
  sans filtre, comme contre le puits en pierre.
- **D02 — Pas de nouvelle sorte ni de nouveau texte.** Les informations de la pompe disent « Source : puits (eau
  propre) » dans les deux cas, et le message de refus garde « contre un puits ». Aucune traduction à ajouter.
- **D03 — Même règle que le puits en pierre.** L'eau est sans limite et ne dépend ni de la pluie ni de la coupure
  de l'eau de ville ; le débit reste celui de la pompe.

## Hors périmètre

Les puits et pompes d'autres mods : ils s'inscrivent eux-mêmes par `LiveWater.API.registerSource`.

# Plan 002 — Tuyaux et barrières

ADR : [ADR-002](../../ADR/termines/002-tuyaux-et-barrieres.md) (Accepté le 2026-11-18).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| B01 | Domaine : port `edges` dans le graphe (mur plein coupe le raccord) et dans les sprites (manchon), champ `crossings` | Terminée (2026-11-18) | ADR accepté | D01, D02, D04 | M | B02 |
| B02 | Tuiles : 20 tuyaux à manchon (index 104-123), propriétés, carte de profondeur | Terminée (2026-11-18) | ADR accepté | D03 | M | B01 |
| B03 | Adaptateur monde : `blocks` et `fenced` lus dans le jeu ; réévaluation à la pose ou au retrait d'un mur ou d'une clôture | Terminée (2026-11-18) | B01 | D01, D02, D05 | M | — |
| B04 | Test en jeu : tuyau à travers une clôture (manchon), refusé à travers un mur ; documentation | Terminée (2026-11-18) | B02, B03 | D01-D05 | S | — |

## Fiches

### B01 — Domaine

- `LWT_Network` : `linksOf` ne garde pas un lien coupé sur l'une des deux pièces (`cuts`) ; `relink` relabellise les
  réseaux d'une case et de ses quatre voisines.
- `LWT_Sprites` : un tuyau dont le côté N ou W passe une clôture (port `edge`) prend `crossings[masque][bords]`.
- `LWT_Parts` : champ `crossings` contrôlé, sprites comptés comme ceux de la pièce.
- Les coupures sont enregistrées sur la pièce (`cuts`, registre) : le graphe ne lit pas le monde (cases non chargées
  au chargement de la partie).
- Preuve du vert : `python -B -m unittest discover -s tests` → « Ran 307 tests … OK » (tests/test_barriers.py).

### B02 — Tuiles

- Recette `source/tiles/build_livewater_tiles.py` : groupes `pipe_m<masque>_x<bords>`, manchon sur le bord N ou W.
- Preuve du vert : « packed 118 sprites », profondeur « hits outside the sprite 0, left without depth 0 » ; test
  `PipeTiles` (pièce et recette d'accord sur les 20 manchons).

### B03 — Adaptateur monde

- `LWT_GameWorld` : `edge(x, y, z, nord)` (règle de `hasNonHoppableWall` ; clôture = `HoppableN/W`, `TallHoppableN/W`),
  `isEdgeObject`, `without`.
- `LWT_Placement` : un objet de bord ajouté ou retiré réévalue les raccords autour (D05) ; le jeu ne signale pas un mur
  construit en solo : l'horloge (`edgeWatch`, `Topology:refreshCuts`) le trouve au pas suivant.
- Preuve du vert : « Ran 307 tests … OK » (tests/test_placement.py, mur posé puis retiré, clôture).

### B04 — Test en jeu et documentation

- Preuve : `pzdev sp LiveWater` → code 0, `summary=34/34 PASS`, `runs/20261118-201202-sp-b543290efc6e` (manchon
  sous la clôture, mur qui coupe, mur retiré qui rebranche, mur construit plus tard trouvé par l'horloge).

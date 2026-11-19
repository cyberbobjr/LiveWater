# Plan 004 — Arrosage au sol : la ligne de goutte-à-goutte

ADR : [ADR-004](../../ADR/termines/004-goutte-a-goutte.md) (Accepté le 2026-11-18).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| G01 | Arroseur : perte d'eau (`loss`) et bruit pour les zombies à chaque pas d'arrosage | Terminée (2026-11-18) | ADR accepté | D03, D06 | S | G02 |
| G02 | Domaine : sortie au sol (cases voisines non raccordées), coût de pression partagé par réseau, pression de gravité réservée au goutte-à-goutte | Terminée (2026-11-18) | ADR accepté | D02, D04, D05 | L | G01 |
| G03 | Pièce `LiveWater:DripLine`, objet posable, recette, traductions | Terminée (2026-11-18) | G02 | D01, D07 | M | G04 |
| G04 | Tuiles : 16 formes de la ligne, propriétés, carte de profondeur | Terminée (2026-11-18) | ADR accepté | D01 | M | G03 |
| G05 | Test en jeu et documentation | Terminée (2026-11-18) | G01-G04 | D01-D07 | M | — |

## Fiches

### G01 — Arroseur

- Preuve du vert : « Ran 310 tests … OK » (tests/test_sprinkler.py : 0,75 L tirés pour 0,6 L donnés, bruit de rayon 10 ;
  tests/test_timer.py rebasés pour la même raison, D03).

### G02 — Domaine

- Fait : type de sortie `drip` (eau propre seulement, groupe de coût `drip` payé une fois par réseau et par pas, marche par gravité), crochets `costGroup`, `byGravity` (sortie), `gravity` (raccord en « Pomper », réglage `gravity` 1), `Network:reach(id, rootHook)`, `Flow` (gravité sur un réseau sans pompe, coût partagé), `Clock:isAwake` (réseau sans pompe réveillé par sa gravité), `LWT_DripArea` (voisines non raccordées), `LWT_Plants` à stratégie de zone injectée (`LWT_SprayArea.reach`, `LWT_DripArea.reach`), capacité `drip` (dose 0,2 L), API révision 15. Tests : `tests/test_drip.py`.
- Preuve du vert : `python -B -m unittest discover -s tests` : « Ran 324 tests ... OK » ; `python -B tools/check_mod.py` : « OK: 102 Lua file(s) checked ».

### G03 — Pièce

- Fait : `Parts/LWT_PartDripLine.lua` (`LiveWater:DripLine`, sprites 160 + masque, `conduit`, `outlet` `drip`, `drip`), `Mov_LiveWater_DripLine` (`LWT_moveables.txt`), `LWTMakeDripLine` (`LWT_recipes.txt`, catégorie `Farming`), traductions des 11 langues (`Recipes`, `ItemName`, `Moveables`, `IGUI_LWT_Drip_<état>`), 20 lignes dans le kit de test.
- Preuve du vert : `python -B -m unittest discover -s tests` : « Ran 324 tests ... OK » ; `python -B tools/check_mod.py` : « OK: 102 Lua file(s) checked ».

### G04 — Tuiles

- Fait : 16 groupes `drip_m00` … `drip_m15` (indices 160-175, `TOTAL` 176), propriétés sans outil (`_moveable(..., tools={})`), vitrine limitée à `drip_m10` ; paquet « packed 142 sprites », profondeur « total: 142 sprites, hits outside the sprite 0, left without depth 2 » (les 2 px connus du sprite 135) ; `tuiles-contrat.md` mis à jour.
- Preuve du vert : `python -B -m unittest discover -s tests` : « Ran 324 tests ... OK » ; `python -B tools/check_mod.py` : « OK: 102 Lua file(s) checked ».

### G05 — Test en jeu et documentation

- Preuve : `pzdev sp LiveWater` → code 0, `summary=36/36 PASS`, `runs/20261118-203017-sp-dd33f69d38bf` (ligne posée
  par la pose vanilla à côté d'un tuyau, le plant voisin passe de 0 à 70 d'eau). Couleur validée par l'utilisateur le
  2026-11-18 : beige du tuyau à siphonner vanilla, plus fin que le tuyau galvanisé.
- Aussi dans `visual` : code 0, `summary=47/47 PASS`, `runs/20261118-203759-sp-62219add6a94`.
- Non couvert en jeu : arrosage par gravité depuis un baril sans pompe (couvert hors jeu, tests/test_drip.py).

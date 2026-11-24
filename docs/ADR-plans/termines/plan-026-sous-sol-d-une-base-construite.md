# Plan 026 — Une base construite sert aussi son sous-sol

ADR : [ADR-026](../../ADR/termines/026-sous-sol-d-une-base-construite.md) (Accepté le 2026-11-24).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| S0 | ADR-026, plan, ligne dans l'état d'ensemble, renvoi daté dans ADR-023 | Terminée (2026-11-24) | — | Toutes | S | — |
| P1 | Règle pure : la zone d'une base descend à `-BASEMENT_LEVELS`, tests rouges puis verts | Terminée (2026-11-24) | S0 | D01, D02 | S | — |
| P2 | Adaptateur : borne basse au plus bas niveau réel des chunks | Terminée (2026-11-24) | P1 | D03 | S | P3 |
| P3 | Documents et version : architecture, spécifications, wiki EN/FR, CHANGELOG 1.0.2 | Terminée (2026-11-24) | P1 | D01, D02, D04 | S | P2 |
| P4 | Passage en jeu : sous-sol creusé sous une base, relais au-dessus, eau | Terminée (2026-11-24) | P2 | D01, D03, D04 | M | — |

## Fiches

### S0 — Décision et plan

Statut : Terminée (2026-11-24).
- `docs/ADR/termines/026-sous-sol-d-une-base-construite.md` (Accepté) et son plan, archivés le même jour ;
  `docs/ADR/README.md` : ligne 026. `docs/ADR/termines/023-arrivee-d-eau-sans-limite-d-etages.md` : renvoi daté dans D01.

Preuve du vert : sans objet (documents seuls).

### P1 — Règle pure et tests

Statut : Terminée (2026-11-24).
- `shared/LiveWater/LWT_InletArea.lua` : `InletArea.base` prend `minZ = math.min(z, -InletArea.BASEMENT_LEVELS)` ;
  commentaire d'en-tête du fichier et de `base` mis à jour.
- `tests/test_base.py` : `test_away_from_a_map_building_the_inlet_serves_a_range` (‑1 et ‑2 dedans, ‑3 dehors) ;
  `test_a_basement_under_the_base_gets_a_relay_above_it`, `test_a_second_basement_level_gets_its_own_relay`,
  `test_a_third_basement_level_is_out_of_the_area`.
- `tests/test_basement.py` : `PlayerBaseBasements` (‑1 et ‑2 dedans, ‑3 dehors, portée horizontale tenue sous terre,
  `BASEMENT_LEVELS` = 2).

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 640 tests in 4.192s` / `OK` (rouge constaté avant :
5 échecs, ceux des nouvelles attentes). `python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked`.

### P2 — Adaptateur et bornes réelles

Statut : Terminée (2026-11-24).
- `server/LiveWater/LWT_GamePlumbing.lua` : `topLevel` devient `levels(area)` (bas et haut des chunks de la zone en une
  boucle, `IsoChunk:getMinLevel` et `IsoChunk:getMaxLevel`, bornés par `area.minZ` et `area.maxZ`) ; `fixtures` parcourt
  de ce bas à ce haut. Commentaire du port mis à jour.

Preuve du vert : `python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked` ; borne basse prouvée en jeu (P4), le
banc hors jeu ne prouvant que la logique Lua.

### P3 — Documents et version

Statut : Terminée (2026-11-24).
- `docs/architecture.md` (description de `LWT_InletArea`), `docs/specifications-fonctionnelles.md` (F16),
  `docs/specifications-techniques.md` (paragraphe des réservoirs relais), `docs/wiki/fr/02-base-du-joueur.md` et
  `docs/wiki/en/02-player-base.md` (puce des niveaux), `docs/ameliorations-et-idees.md` (I13),
  `CHANGELOG.md` (1.0.2), `Contents/mods/batman_LiveWater/42.21/mod.info` (`modversion=1.0.2`).
- Aucune retouche des `README.steam.*` : la description dit déjà « 2 basement levels down ».

Preuve du vert : `python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked` ; relecture des textes.

### P4 — Passage en jeu

Statut : Terminée (2026-11-24). Scénario ajouté à `autotest/lwt_hooks.lua` (solo), après la phase du toit : un second
inlet posé par le placement vanilla sur une case libre hors de tout bâtiment de la carte, à côté d'un tuyau du réseau
vivant (mode base) ; une cartouche filtrante y est montée par la vraie commande `fitFilter` (la pompe tire l'eau
croupie de l'étang) ; une case est créée au niveau ‑1 à côté de l'inlet (`chunk:setMinMaxLevel(-1, …)` puis
`createNewGridSquare`) et un évier y est posé, raccordé comme le fait l'action vanilla. Vérifié : le relevé trouve
l'évier à ‑1, le relais se pose au niveau 0 au-dessus, `FindExternalWaterSource` le renvoie depuis l'évier, l'évier
reçoit 25 L ; puis l'évier et l'inlet sont retirés et le relais suit.
- Solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code de sortie 0, `summary=96/96 PASS`, dossier
  `runs/20261124-133538-sp-3ce4ceb2cba4`.

Non joué en jeu : la ligne « Raccorder » du jeu dans le sous-sol, qui exige une pièce (`isInARoom`) ; le scénario
n'enregistre pas de pièce au niveau ‑1 (c'est le mod de sous-sol qui le fait). L'état obtenu par le scénario est
celui d'après raccordement. Multijoueur non rejoué : le changement est dans le relevé d'autorité, sans message ni
protocole nouveau.

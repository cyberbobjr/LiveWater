# Plan 023 — L'arrivée d'eau sert tous les étages au-dessus d'elle

ADR : [ADR-023](../../ADR/termines/023-arrivee-d-eau-sans-limite-d-etages.md) (Accepté le 2026-11-22).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| H1 | Zone sans limite vers le haut, relevé borné au plus haut niveau des chunks, constante du dernier niveau | Terminée (2026-11-22) | ADR accepté | D01, D02, D03, D04 | S | — |
| H2 | Textes : options de partie (11 langues), descriptions Workshop (11 langues), wiki EN/FR, images, spécifications, CHANGELOG | Terminée (2026-11-22) | H1 | D01 | S | — |
| H3 | Passage en jeu | Terminée (2026-11-22) | H1 | D01, D03 | S | — |

## Fiches

### H1 — Zone et relevé

Statut : Terminée (2026-11-22).
- `shared/LiveWater/LWT_Grid.lua` : `Grid.TOP = 31`, seul propriétaire du dernier niveau ; `LWT_RelayPlan.TOP` le lit.
- `shared/LiveWater/LWT_InletArea.lua` : `LEVELS_UP` retiré, `maxZ = Grid.TOP` dans les deux modes.
- `server/LiveWater/LWT_GamePlumbing.lua` : `fixtures(area)` s'arrête au plus haut niveau des chunks de la zone
  (`getCell():getChunkForGridSquare`, `IsoChunk:getMaxLevel`).
- Tests : `tests/test_inlet.py` (étage 4 servi, tour de 31 niveaux, constante, relais au-dessus d'un point d'eau du
  4e étage), `tests/test_base.py` (base : niveaux 4 et 31 servis, niveau sous l'arrivée non servi, relais au 7e).

### H2 — Textes

Statut : Terminée (2026-11-22). `Translate/*/Sandbox.json` (11 langues, deux infobulles), `README.steam*` et
`workshop.txt`, `docs/wiki/{en,fr}/01-*`, `02-*`, `05-*`, `tools/make_doc_images.py` et
`docs/images/diagrams/equipment_*.png` régénérées, `docs/specifications-*.md`, `docs/architecture.md`, `CHANGELOG.md`.

Preuves du vert (2026-11-22, après H1 et H2) : `python -B -m unittest discover -s tests` → `Ran 599 tests` / `OK` ;
`python -B tools/check_mod.py` → `OK: 114 Lua file(s) checked`.

### H3 — Passage en jeu

Statut : Terminée (2026-11-22). Le relevé appelle deux fonctions du jeu nouvelles pour le mod
(`getChunkForGridSquare`, `getMaxLevel`) : le parcours nominal en jeu (maison de la carte, arrivée d'eau, évier
raccordé, réservoir rempli) les exerce. `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code de sortie 0,
`summary=69/69 PASS`, dossier `runs/20261122-114907-sp-23ecc559f826`.

Non joué en jeu : un bâtiment de cinq niveaux ou plus (couvert par les tests hors jeu de H1), le serveur dédié.

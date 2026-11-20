# Plan 016 — « Retirer LiveWater de ce monde » : mode debug en solo, admin en multijoueur

ADR : [ADR-016](../../ADR/termines/016-retrait-debug-ou-admin.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Module partagé du droit de retrait ; menu et `GamePlayers:isAdmin` l'utilisent ; tests | Terminée (2026-11-20) | ADR accepté | D01, D02 | S | — |
| E02 | Wiki EN/FR, CHANGELOG | Terminée (2026-11-19) | E01 | D03 | S | — |
| E03 | Passage en jeu par l'utilisateur | Terminée (2026-11-20) | E01 | D01 | S | — |

## Fiches

### E01 — Code

Fichiers : nouveau `shared/LiveWater/LWT_RemovalRight.lua` (règle unique), `client/LiveWater/LWT_AdminMenu.lua`,
`server/LiveWater/LWT_GamePlayers.lua` (`isAdmin` délègue), `tests/test_removal.py` (classe `RemovalRight`, 4 tests :
solo sans debug refusé, solo debug accepté, multijoueur admin seulement même en debug, menu masqué en solo normal,
autorité branchée sur la même règle).

Preuve du vert : `python -B tests/test_removal.py` → `OK` ; `python -B -m unittest discover -s tests` → `Ran 545 tests`,
`OK` ; `python -B tools/check_mod.py` → `OK: 109 Lua file(s) checked`.

### E02 — Documentation

Wiki EN/FR 07 (mode debug en solo, admin en multijoueur), CHANGELOG (Unreleased). Descriptions Steam inchangées : la
ligne « un admin choisit... » reste juste, et la page russe n'a plus de place (7 947 octets).

### E03 — Passage en jeu

Protocole court, par l'utilisateur : partie solo normale, clic droit : pas d'option « Retirer LiveWater de ce
monde » ; partie solo lancée avec `-debug` : l'option est là ; en multijoueur, un joueur ne la voit pas, un admin oui.

# Plan 013 — Raccord de remplissage : barils, récupérateurs d'eau et mangeoires

ADR : [ADR-013](../../ADR/termines/013-raccord-de-remplissage-et-abreuvoirs.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| R01 | Nom « Raccord de remplissage », infobulle, mangeoires vanilla (`KINDS.trough`, tuile maîtresse, `addWater`, nourriture) ; traductions ; tests | Terminée (2026-11-20) | ADR accepté | D01-D04 | M | — |
| R02 | Passages en jeu (communs aux ADR-011 à 013), documentation | Terminée (2026-11-20) | R01 | toutes | S | — |

## Fiches

### R01 — Raccord de remplissage et mangeoires

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : noms d'objet, de meuble et de recettes dans les 11 langues ; `Tooltip = Tooltip_LWT_FillFitting` sur
  `Mov_LiveWater_BarrelFitting` ; `LWT_GameContainers` : mangeoire (`IsoFeedingTrough`, tuile maîtresse,
  `addWater`/`removeWater` + `sendSyncEntity`, dessin d'eau), mangeoire plein de nourriture → `blocked = "feed"`,
  ligne `IGUI_LWT_Fitting_TroughFeed`.
- Tests : `tests/test_trough.py` (9).

### R02 — Preuves en jeu et documentation

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Correction du banc : le bloc pompe-sur-baril réutilisait `S.B` d'une étape antérieure (erreur Lua au premier
  passage, `runs/20261119-174052-sp-c648562b6dee`, 41/42) ; renommé `S.BP`.
- Passages :
  - solo, code 0, `summary=60/60 PASS`, `runs/20261119-174300-sp-ea58bc782ebb` (« the fill fitting fills the feeding
    trough with the barrel's water » : mangeoire 0 → 50 L, baril 100 → 50 L) ;
  - visuel FR, code 0, `summary=76/76 PASS`, `runs/20261119-174452-sp-88e6fa5119b6` ;
  - multijoueur, code 0, serveur `22/22 PASS`, client `6/6 PASS`, `runs/20261119-174950-mp-b9f3dd05846a` ;
  - Live Wire, code 0, `summary=61/61 PASS`, `runs/20261119-175821-sp-0c0ad160984d`.
- Documentation : wiki FR/EN, spécifications, architecture, README, 11 descriptions Steam, CHANGELOG ; « mangeoire »
  et termes vanilla de la mangeoire dans chaque langue (`ContextMenu_FeedingTrough` du jeu).
- Hors jeu : `python -B -m unittest discover -s tests` → `Ran 509 tests`, `OK` ; `python -B tools/check_mod.py` →
  `OK: 108 Lua file(s) checked`.

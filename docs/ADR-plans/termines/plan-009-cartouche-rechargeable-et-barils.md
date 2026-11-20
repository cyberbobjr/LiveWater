# Plan 009 — Cartouche rechargeable ; plus de baril raccordé directement à la maison

ADR : [ADR-009](../../ADR/termines/009-cartouche-rechargeable-et-barils.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| C01 | Cartouche usée rendue, objet `WaterFilterSpent`, recette de recharge, démontage, icône, traductions ; tests | Terminée (2026-11-20) | ADR accepté | D01, D02 | M | C02 |
| C02 | Retrait du raccordement direct des barils à la maison (serveur, commandes, menu, diagnostic, traductions, tests) | Terminée (2026-11-20) | ADR accepté | D03 | M | C01 |
| C03 | Passages en jeu, documentation joueur | Terminée (2026-11-20) | C01, C02 | toutes | S | — |

## Fiches

### C01 — Cartouche rechargeable

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : objet `LiveWater.WaterFilterSpent` (`LWT_items.txt`, sans état, pas de butin), icône
  `Item_LWT_WaterFilterSpent.png` tirée de celle de la cartouche (`python source/tiles/make_item_icons.py --spent .`).
  Champ `spent` de la capacité filtre et quatrième résultat du crochet `cartridge` (API révision 20) ; l'arrivée
  d'eau le déclare ; `LWT_CmdCartridge.takeOut` rend la cartouche usée par `players:give` au retrait comme au
  remplacement. Le montage prend le type exact `LiveWater.WaterFilter` : une cartouche usée n'est jamais montée
  (une cartouche neuve à état 0 n'existe pas : `give` arrondit l'état à 1 au moins). Recette
  `LWTRechargeWaterFilter` (1 usée + 2 `tags[base:charcoal]` + 1 `Base.RippedSheets` → 1 cartouche, mêmes
  action et temps que la fabrication), démontage `LWTDismantleWaterFilterSpent` (couteau, 1 chiffon, table
  `LWT_Dismantle.lua`) ; noms dans les 11 `Recipes.json` et `ItemName.json`.
- Preuves : `tests/test_filter.py` (cartouche usée rendue au retrait et au remplacement, jamais montée, recette),
  `tests/test_dismantle.py` (coût d'une usée = celui d'une neuve, la recharge n'est pas une recette de fabrication),
  `tests/test_api.py` (révision 20). `python -B -m unittest discover -s tests` : `Ran 484 tests`, `OK` ;
  `python -B tools/check_mod.py` : `OK: 106 Lua file(s) checked`.
- Reste : page modding du wiki (révision 20, champ `spent`) et passages en jeu (C03).

### C02 — Barils

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Supprimés : `server/LiveWater/LWT_HouseBarrels.lua`, `shared/LiveWater/LWT_Reserve.lua`,
  `client/LiveWater/LWT_BarrelMenu.lua`, `Commands/LWT_CmdConnectBarrel.lua`, `LWT_CmdDisconnectBarrel.lua`,
  `LWT_CmdReserveBarrel.lua` ; leur câblage dans `LWT_Server.lua` (commandes, service `barrels`, tâche de
  l'horloge, `lifted`, événements de pose, retrait et `partRemoved`) ; commandes `connectBarrel`,
  `disconnectBarrel`, `reserveBarrel` de `LWT_Protocol` ; `barrel`, `markBarrel`, `transfer` de
  `LWT_GamePlumbing` ; `BARREL_KEY`, `MIN_BARREL_LITRES`, `isBarrel`, `isWaterOnly` de `LWT_WaterObjects` ;
  `reaches` et `topZ` de `LWT_InletArea` ; raisons `not_barrel`, `no_inlet`, `not_connected` de `LWT_Reasons`.
- Diagnostic : `Diagnosis.inlet(state, pumped)` ; sans pompe dans le réseau, l'arrivée d'eau dit `no_pressure`
  (« pression insuffisante dans les tuyaux ») ; raisons `gravity`, `empty`, `no_supply` retirées.
- Traductions retirées des 11 langues : `ContextMenu_LWT_ConnectBarrel`, `_DisconnectBarrel`, `_ReserveBarrel`,
  `_UseBarrel` ; `IGUI_LWT_NotBarrel`, `IGUI_LWT_NoInlet`, `IGUI_LWT_NotConnected`, `IGUI_LWT_Why_gravity`,
  `_empty`, `_no_supply` (aucun usage restant dans le code, les tests ni les outils).
- Tests : `tests/test_barrels.py` supprimé ; retirés de `test_combo_barrels.py` (baril de maison avec un raccord),
  `test_persistence.py` (enregistrement d'un baril), `test_base.py` (rattachement au ramassage, `reaches`, raisons des
  barils) ; `test_base.py` vérifie qu'une arrivée d'eau sans pompe dit `no_pressure`. Le raccord de baril est intact.
- Docs : `docs/architecture.md`, `docs/specifications-techniques.md`. Restent F15, F17, F18 de
  `docs/specifications-fonctionnelles.md` et le wiki (C03).
- Preuves : `python -B -m unittest discover -s tests` : `Ran 484 tests`, `OK` (avec C01 en cours) ;
  `python -B tools/check_mod.py` : `OK: 106 Lua file(s) checked`. `autotest/` ne teste pas le raccordement direct.

### C03 — Preuves et documentation

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Passages de non-régression sur le code de l'ADR-009 :
  - solo, code 0, `summary=49/49 PASS`, `runs/20261119-140425-sp-bf0af9067719` ;
  - visuel FR, code 0, `summary=65/65 PASS`, `runs/20261119-140546-sp-e705b9e9f5a3` ;
  - multijoueur, code 0, serveur `20/20 PASS`, client `6/6 PASS`, `runs/20261119-140958-mp-2fdc71f8acea`.
- Hors jeu : `python -B -m unittest discover -s tests` → `Ran 484 tests` … `OK` ; `python -B tools/check_mod.py` →
  `OK: 106 Lua file(s) checked`.
- Documentation : CHANGELOG, wiki FR/EN (01, 02, 03, 06, 07, Home), spécifications fonctionnelles (F15, F18 retirées,
  F05, F13, F16, F17) et techniques, idées (I07 retirée), README et les onze descriptions Steam.

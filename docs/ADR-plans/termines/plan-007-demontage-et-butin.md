# Plan 007 — Démontage des équipements et butin

ADR : [ADR-007](../../ADR/termines/007-demontage-et-butin.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| R01 | Table de démontage unique, recettes `Dismantle …` de l'inventaire, matériaux de démontage déclarés au démarrage ; tests | Terminée (2026-11-19) | ADR accepté | D01-D03 | M | R02 |
| R02 | Butin : ajouts aux listes vanilla à la fusion des tables ; tests | Terminée (2026-11-19) | ADR accepté | D04 | S | R01 |
| R03 | Propriétés `CanScrap`, `Material`, `ScrapSize` des tuiles, réempaquetage ; scénario en jeu (démonter une pièce posée la retire du réseau) ; documentation | Terminée (2026-11-19) | R01 | D02 | M | — |

## Fiches

### R01 — Démonter

- Statut : Terminée (2026-11-19).
- Fait : table unique `shared/LiveWater/LWT_Dismantle.lua` (outils D03 par genre `plumbing`/`electrical`/`knife`,
  une entrée par équipement : objet, outil, durée, `scrap` = `ScrapSize` ou rien, objets rendus) ; dix recettes
  `LWTDismantle<Pièce>` dans `media/scripts/LWT_dismantle.txt` (préfixe `LWT` des conventions du projet), traduites
  dans les onze langues (`Recipes.json`) ; adaptateur `shared/LiveWater/LWT_GameScrap.lua` qui déclare à `OnGameBoot`
  (après `ISMoveableDefinitions.load` vanilla) huit matériaux `LiveWater<Pièce>` par `addScrapDefinition` et
  `addScrapItem` statiques, quantités corrigées du facteur `ScrapSize` du jeu (à pleine chance : les objets de la
  recette). Rendus en débris (`Base.IronPiece`, `Base.ScrapMetal`, `Base.Screws`, `Base.ElectronicsScrap`,
  `Base.ElectricWire`) ; cartouche → 1 `Base.RippedSheets` ; goutte-à-goutte → 1 `Base.RubberBand` (rebut qu'aucune
  recette vanilla n'utilise), sans démontage sur place. Tests `tests/test_dismantle.py` : une recette par équipement
  égale à la table, rendu ≤ coût (même type, et poids par famille de matériau, coût développé depuis
  `LWT_recipes.txt`), aucune matière première entière rendue par une pièce qui n'en contient qu'une fraction, matériaux
  du jeu = sorties des recettes, `Material`/`ScrapSize` des tuiles = table Lua.
- Preuve du vert :
  - `python -B -m unittest discover -s tests -p "test_dismantle.py"` → `Ran 10 tests` … `OK` ;
  - `python -B -m unittest discover -s tests` → `Ran 444 tests` … `OK` ;
  - `python -B tools/check_mod.py` → `OK: 105 Lua file(s) checked` ;
  - `python PZDevKit/pzdev.py check LiveWater` (depuis le dossier parent) → `sp: hooks ok`, `server: hooks ok`,
    `mp: hooks ok`.

### R02 — Butin

- Statut : Terminée (2026-11-19).
- Fait : `server/LiveWater/LWT_Loot.lua`, table `Loot.GROUPS` et `Loot.apply(lists)` appelée à
  `OnPreDistributionMerge` : ajout en fin de `ProceduralDistributions.list.<Liste>.items`, liste absente ignorée.
  Plomberie (`PlumbingSupplies`, `CrateTools`, `GarageTools`, `ToolStoreTools`) : tuyau 2, vanne 1, raccord de baril 1 ;
  arrosage (`GardenStoreTools`, `GardenStoreMisc`, `CrateGardening`, `GigamartFarming`, `ToolStoreFarming`) :
  arroseur 1, goutte-à-goutte 2, cartouche filtrante 1 (outils rares de ces listes : 0,5 à 2). Tests
  `tests/test_loot.py` : entrées vanilla intactes et en tête, chaque pièce dans ses listes seulement, poids 0,5-2,
  aucune pièce exclue, liste absente ignorée.
- Preuve du vert :
  - `python -B -m unittest discover -s tests -p "test_loot.py"` → `Ran 4 tests` … `OK` ;
  - suite complète et `tools/check_mod.py` : voir R01.

### R03 — Tuiles, jeu, documentation

- Statut : Terminée (2026-11-19).
- Déjà fait dans le code (2026-11-19) : `source/tiles/build_livewater_tiles.py` donne `CanScrap`,
  `Material = LiveWater<Pièce>` et `ScrapSize` (`SCRAP_SIZES`, miroir de la table Lua vérifié par
  `tests/test_dismantle.py`) à toutes les tuiles posables sauf le goutte-à-goutte ; documentation (CHANGELOG, wiki
  premiers pas EN/FR, spécifications techniques) à jour.
- Fait ensuite : réempaquetage (`python source/tiles/build_livewater_tiles.py package <cases> .` → `packed 150 sprites`,
  102 tuiles `CanScrap`, huit matériaux `LiveWater<Pièce>` dans le `.tiles`) ; étape solo de `autotest/lwt_hooks.lua` :
  l'arroseur automatique démonté par `ISMoveableSpriteProps:scrapObject` quitte la case et le réseau (matériau
  `LiveWaterSprinklerAuto`, rendu `ScrapMetal`, `IronPiece` ×2, `ElectronicsScrap`, `ElectricWire`).
- Preuve en jeu (2026-11-19) :
  - solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code 0, `summary=47/47 PASS`, `runs/20261119-005256-sp-7ac436c52094` ;
  - visual : `python PZDevKit/pzdev.py sp LiveWater/autotest/scenarios/visual.json --wait-idle 3600` → code 0, `summary=58/58 PASS`, `runs/20261119-005417-sp-6496fd0c65f5` ;
  - multijoueur : `python PZDevKit/pzdev.py mp LiveWater --clients 1 --client-run --wait-idle 3600` → code 0, serveur `20/20 PASS`, client 1 `6/6 PASS`, `runs/20261119-005810-mp-202a8d9e9990`.
- Non vu en jeu : les recettes `LWTDismantle…` dans la fenêtre d'artisanat et le butin qui apparaît (tests hors jeu
  seulement).

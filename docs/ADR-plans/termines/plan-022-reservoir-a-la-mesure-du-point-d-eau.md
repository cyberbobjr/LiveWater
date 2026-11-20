# Plan 022 — Réservoir relais à la mesure du point d'eau

ADR : [ADR-022](../../ADR/termines/022-reservoir-a-la-mesure-du-point-d-eau.md) (Accepté le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| R1 | Constat : comment Take a Bath and Shower reconnaît une douche et une cuve, comment sa cuve puise ; un réservoir sert-il plusieurs points d'eau (`LWT_RelayPlan`) | Terminée (2026-11-20) | ADR accepté | D02, D03 | S | — |
| R2 | Registre des fournisseurs, API `registerFixtureNeed`, taille voulue d'un réservoir, plafond, redimensionnement | Terminée (2026-11-20) | R1 | D01, D02, D04, D05 | M | — |
| R3 | Fournisseur Take a Bath and Shower | Terminée (2026-11-20) | R2 | D03 | S | — |
| R4 | Option de partie (11 langues), wiki EN/FR, CHANGELOG, spécifications | Terminée (2026-11-20) | R2 | D04 | S | R3 |
| R5 | Passage en jeu par l'utilisateur (avec Take a Bath and Shower) | Terminée (2026-11-20) | R3 | toutes | S | — |

## Fiches

### R1 — Constat

Statut : Terminée (2026-11-20). Lecture seule de Take a Bath and Shower 42.20 (`TakeABathAndShowerNew`, Workshop
3592172476) :
- douche : `TABAS_Iso.isShowerObject(obj, true)` (planche de sprites du mod, baignoire avec douche comprise) ; elle
  puise peu à peu jusqu'à l'option `TakeABathAndShower.ShowerConsumeWater` (80 L par défaut, 0 à 200) et s'arrête quand
  le robinet se vide (`TABAS_TakeShower.lua:236-290, 580`) ;
- baignoire : `TABAS_Iso.isBathObject(obj)` ; sa cuve (`FluidContainer` du mod, contenance
  `TakeABathAndShower.TubWaterCapacity`, 200 L par défaut, 100 à 1 000) se remplit depuis le robinet
  (`v.bath:useFluid`, `TABAS_STubFluidContainerSystem.lua:135-140`) et s'arrête quand il est vide ;
- `TABAS_Iso` est un module partagé (`require "TABAS_Iso"`), chargé aussi sur un serveur dédié ;
- un réservoir sert son point d'eau et les 8 voisins de l'étage du dessous (`LWT_RelayPlan`, `FindExternalWaterSource`) :
  sa taille est le plus grand besoin des points d'eau qui puisent ou puiseront à lui.

### R2 — Registre et taille

Statut : Terminée (2026-11-20).
- `shared/LiveWater/LWT_FixtureNeeds.lua` : registre (ids triés, scellé à `OnInitGlobalModData`), `need(obj)` = plus
  grand nombre positif rendu.
- `LWT_API.lua` : révision 25, `registerFixtureNeed(id, fn)`, `LiveWater.FixtureNeeds`.
- `LWT_GamePlumbing.lua` : `new(needs)`, champ `need` des points d'eau relevés, `capacity` du relais, `resizeRelay`
  (`setCapacity` puis `sync`) ; `LWT_Server.lua` lui passe `LiveWater.FixtureNeeds`.
- `LWT_Relays.lua` : `size(pos, served)` (25 L au moins, `RelayMaxLitres` au plus, 300 par défaut) ; pose à cette
  taille, redimensionnement au relevé quand elle change.
- Tests : `tests/test_relay_size.py` (17) ; double de plomberie de `tests/test_inlet.py` (`need`, `capacity`,
  `resizeRelay`) ; `test_api.py` révision 25 ; `test_linked_pump.py` révision 24 au moins.

### R3 — Fournisseur Take a Bath and Shower

Statut : Terminée (2026-11-20). `shared/LiveWater/Needs/LWT_NeedTakeABath.lua` : actif seulement si les options
de partie du mod existent ; douche → `ShowerConsumeWater`, baignoire → `TubWaterCapacity`, baignoire avec douche → le
plus grand ; fonctions du mod (`TABAS_Iso`), pas de copie.

### R4 — Documentation

Statut : Terminée (2026-11-20). `sandbox-options.txt` (`RelayMaxLitres`, entier 25 à 1 000, 300) ; `Sandbox.json` des
11 langues ; `docs/wiki/{en,fr}/05-*`, `06-*` ; `docs/specifications-techniques.md`, `specifications-fonctionnelles.md`
(F13) ; `CHANGELOG.md` (Unreleased).

Preuves du vert (2026-11-20, après les étapes R2 à R4) : `python -B -m unittest discover -s tests` → `Ran 593 tests` /
`OK` ; `python -B tools/check_mod.py` → `OK: 114 Lua file(s) checked`.

### R5 — Passage en jeu

Statut : Terminée (2026-11-20), confirmé en jeu par l'utilisateur (« ok ca fonctionne »). Protocole : maison raccordée à une arrivée d'eau, Take a Bath and Shower actif ; le menu de la douche
montre « Eau : … / 80 L » une fois rempli ; une douche complète sans coupure ; un évier reste à 25 L ; une cuve de
baignoire se remplit jusqu'au bout.

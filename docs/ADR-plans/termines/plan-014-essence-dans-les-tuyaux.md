# Plan 014 — Essence dans les tuyaux : pompe sur une station-service, un seul liquide par réseau

ADR : [ADR-014](../../ADR/termines/014-essence-dans-les-tuyaux.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Pompe contre une pompe à essence (`isFuelPump`, `KINDS.fuelPump`, `vessel` tire l'essence) | Terminée (2026-11-20) | ADR accepté | D01 | M | — |
| E02 | Un seul liquide par zone : première pompe dans l'ordre de pose (`Flow:supply`, `otherFluid`, ligne de pompe) | Terminée (2026-11-20) | E01 | D02 | M | — |
| E03 | `takes` des consommateurs, raccord qui ne mélange jamais, textes ; API révision 23 ; tests | Terminée (2026-11-20) | E02 | D03, D04 | M | — |
| E04 | Passages en jeu, documentation | Terminée (2026-11-20) | E03 | toutes | S | — |

## Fiches

### E01 à E03 — Code

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : `WaterObjects.isFuelPump` (propriété de sprite `fuelAmount`, sans effet de bord de `getPipedFuelAmount`),
  `GameSite:hasVessel` accepte une pompe à essence, `LWT_GameContainers` par sorte (`vessel`, `trough`, `fuelPump` :
  `getPipedFuelAmount`, `setPipedFuelAmount` en unités entières, jamais une cible de remplissage), `Vessel.draw` eau ou
  essence, `Flow:supply` (première pompe qui donne fixe la famille ; les autres → `otherFluid`), `Pump.stepped`
  (`otherFluid`, ne tourne pas, pas d'usure), `outlet.takes` (« water » par défaut), `Fitting` (`holds` avec
  `takes` du récipient : mangeoire eau seule), textes `IGUI_LWT_Pump_OtherFluid`, `IGUI_LWT_Outlet_WrongLiquid`,
  `IGUI_LWT_Fitting_NotWater`, `IGUI_LWT_Vessel_Tank`, `*_wrong_fluid` (« Ce n'est pas de l'eau »),
  `IGUI_LWT_Why_wrong_fluid`, `IGUI_LWT_NoSource` (quatre possibilités) dans les 11 langues ; API révision 23.
- Tests : `tests/test_fuel_station.py` (30).
- Preuves : `python -B -m unittest discover -s tests` → `Ran 538 tests`, `OK` ; `python -B tools/check_mod.py` →
  `OK: 108 Lua file(s) checked`.

### E04 — Preuves en jeu et documentation

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Scénario solo : pompe à essence vanilla (`location_shop_fossoil_01_12`, 200 unités) ; pompe posée contre elle ;
  raccord de remplissage sur un récupérateur vide → 50 L d'essence ; station 200 → 150 ; arroseur `wrong_fluid`.
  Premier passage 51/52 (`runs/20261119-181324-sp-e9d78808948a` : le banc ne donnait pas assez de pompes), corrigé.
- Passages :
  - solo, code 0, `summary=69/69 PASS`, `runs/20261119-181459-sp-94a087e749b6` ;
  - visuel, multijoueur, Live Wire : à compléter.
- Documentation : wiki FR/EN (Home, 01, 03, 06), spécifications, architecture, README, 11 descriptions Steam,
  `workshop.txt`, CHANGELOG.

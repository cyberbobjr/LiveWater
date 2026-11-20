# Plan 010 — Pompe à eau ; une vanne agit tout de suite

ADR : [ADR-010](../../ADR/termines/010-pompe-a-eau-et-vanne-immediate.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| V01 | Nom affiché « Pompe à eau » dans les 11 langues, `mod.info`, README, descriptions Steam, wiki, spécifications, CHANGELOG | Terminée (2026-11-20) | ADR accepté | D01 | S | V02 |
| V02 | Manœuvre de vanne immédiate : pas avancé et sauté par l'horloge, coupure au-delà d'une heure d'avance, relais vidés ; tests | Terminée (2026-11-20) | ADR accepté | D02, D03, D04 | M | V01 |
| V03 | Passages en jeu, documentation joueur | Terminée (2026-11-20) | V01, V02 | toutes | S | — |

## Fiches

### V01 — Pompe à eau

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : valeurs des clés `Base.Mov_LiveWater_PondPump` (`ItemName.json`), `Live_Water_Pond_Pump` (`Moveables.json`),
  `LWTBuildPondPump`, `LWTDismantlePondPump` (`Recipes.json`), `IGUI_LWT_Window_Pump` (`IG_UI.json`) et l'infobulle
  de `Sandbox.json`, dans les 11 langues ; `description=` du `mod.info`, `README.md`, `workshop.txt`, `README.steam*`,
  wiki FR/EN (01, 04, Home), spécifications fonctionnelles, CHANGELOG. Identifiants internes inchangés ; « eau
  d'étang », « lac, étang, rivière » gardés (ce sont des étangs).
- Preuves : `python -B -m unittest discover -s tests` → `Ran 489 tests`, `OK` ; `python -B tools/check_mod.py` →
  `OK: 106 Lua file(s) checked`.

### V02 — Vanne immédiate

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : `LWT_Clock` : `step(id)` (un pas d'un réseau, extrait de `tick`), `switched(part, open)`, `behindClosed(id)`,
  marque `ahead` par réseau (non sauvegardée), `Clock.MAX_AHEAD = 6` ; `tick` saute un réseau tant qu'il a de
  l'avance. `LWT_Outlets:cut(part)` (point d'extension facultatif), `LWT_Relays:cut(part)`,
  `LWT_GamePlumbing:emptyRelay`. `LWT_Server` : `valveChanged` → bruit, `clock:switched`, `outlets:cut` des parties
  coupées.
- Tests : `tests/test_valve.py` classe `Immediate` (fermer coupe tout de suite et nomme les parties coupées ; ouvrir
  donne l'eau tout de suite et l'horloge saute le pas suivant ; chaque manœuvre avance un pas et l'horloge en saute
  autant ; au-delà de six pas d'avance, une manœuvre coupe sans donner d'eau) ; `tests/test_inlet.py`
  (`test_a_house_cut_by_a_valve_loses_the_water_of_its_relays_at_once`).
- Preuves : `python -B -m unittest discover -s tests` → `Ran 489 tests`, `OK` ; `python -B tools/check_mod.py` →
  `OK: 106 Lua file(s) checked`.

### V03 — Preuves en jeu et documentation

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Scénario (`autotest/lwt_hooks.lua`) : l'arroseur ouvert arrose aussitôt (« opened sprinkler sprays at once ») ;
  la vanne de conduite fermée coupe la maison aussitôt, relais vidés par le mod (« closed inline valve cuts the house
  at once », solo et serveur MP ; l'ancien vidage par le banc est retiré) ; l'arroseur fermé s'arrête aussitôt.
- Banc : `waitSteps` et `serverWait` ne comptent plus les pas que l'horloge saute pour rattraper son avance
  (`clockAhead`) ; le niveau de la culture est relevé avant l'ouverture de l'arroseur (elle arrose aussitôt).
- Passages :
  - solo, code 0, `summary=52/52 PASS`, `runs/20261119-163237-sp-0f33b30532c6` ;
  - visuel FR, code 0, `summary=68/68 PASS`, `runs/20261119-163403-sp-4a538232aa48` ;
  - multijoueur, code 0, serveur `22/22 PASS`, client `6/6 PASS`, `runs/20261119-164534-mp-1a5790da8d7f`.
- Hors jeu : `python -B -m unittest discover -s tests` → `Ran 489 tests`, `OK` ; `python -B tools/check_mod.py` →
  `OK: 106 Lua file(s) checked`.
- Reste à voir par l'utilisateur : le nom « Pompe à eau » dans les menus et le panneau d'artisanat, la sensation de
  la vanne en jeu.
- Documentation : wiki FR/EN 01 (vanne d'arrêt), CHANGELOG.

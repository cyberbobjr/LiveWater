# Plan 005 — Le filtre passe de la pompe à l'arrivée d'eau

ADR : [ADR-005](../../ADR/termines/005-filtre-a-l-arrivee-d-eau.md) (Accepté le 2026-11-18).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| F01 | Pièces : filtre déplacé de la pompe à l'arrivée d'eau, lampe, goutte-à-goutte sans exigence d'eau propre ; tests | Terminée (2026-11-18) | ADR accepté | D01-D04 | M | — |
| F02 | Scénarios en jeu (solo, visual, multijoueur) : la cartouche se monte sur l'arrivée d'eau | Terminée (2026-11-19) | F01 | D01 | S | F03 |
| F03 | Documentation : wiki, spécifications, pages Steam, CHANGELOG | Terminée (2026-11-18) | F01 | D01-D04 | S | F02 |

## Fiches

### F01 — Pièces

- Fait : capacité `filter` déplacée de `LiveWater:PondPump` (variantes `off` 24, `on` 28) à `LiveWater:HouseInlet`
  (variantes `filtered` 40, `unfiltered` 44, `filter_filtered` 176, `filter_unfiltered` 180) ; sortie `drip` sans
  exigence d'eau propre ; `Flow.family` : toute qualité autre que `clean`, `tainted`, `fuel` est `other` (jamais de
  l'eau), un filtre ne purifie que l'eau ; arrosage (arroseur, goutte-à-goutte) : eau propre ou non, `wrong_fluid` pour
  l'essence et tout autre fluide. Tuiles 176-183 (arrivée d'eau avec boîtier de filtre, voyant vert / ambre) ajoutées à
  la recette, rendues, empaquetées (150 sprites) avec la carte de profondeur (aucun impact hors sprite). Traductions
  (11 langues) : infobulle de la cartouche, raison `IGUI_LWT_Why_unfiltered` ; clé `IGUI_LWT_Drip_unfiltered` retirée.
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 329 tests ... OK` ; `python -B tools/check_mod.py`
  → `OK: 102 Lua file(s) checked`.

### F02 — Scénarios en jeu

- Statut : Terminée (2026-11-19).
- Code fait (`autotest/lwt_hooks.lua`) : la cartouche se monte sur l'arrivée d'eau (solo, visual, multijoueur) ;
  contrôles : pompe 28 + orientation, arrivée d'eau ambre 44 + orientation sans filtre, verte avec filtre 176 +
  orientation. `python PZDevKit/pzdev.py check LiveWater` → `sp: hooks ok`, `server: hooks ok`, `mp: hooks ok`.
- Preuve en jeu (2026-11-19) :
  - solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code 0, `summary=47/47 PASS`, `runs/20261119-005256-sp-7ac436c52094` ;
  - visual : `python PZDevKit/pzdev.py sp LiveWater/autotest/scenarios/visual.json --wait-idle 3600` → code 0, `summary=58/58 PASS`, `runs/20261119-005417-sp-6496fd0c65f5` ;
  - multijoueur : `python PZDevKit/pzdev.py mp LiveWater --clients 1 --client-run --wait-idle 3600` → code 0, serveur `20/20 PASS`, client 1 `6/6 PASS`, `runs/20261119-005810-mp-202a8d9e9990`.

### F03 — Documentation

- Fait : CHANGELOG (Unreleased), wiki EN/FR (premiers pas, diagnostic, moddeurs, multijoueur), spécifications
  fonctionnelles et techniques, architecture, contrat des tuiles (32-39 inutilisées, 176-183, 184 sprites),
  README.steam et ses 11 langues, workshop.txt (chacun sous 8 000 octets ; le plus long : README.steam.ru, 6 703).
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 329 tests ... OK` ; `python -B tools/check_mod.py`
  → `OK: 102 Lua file(s) checked`.

# Plan 027 — Arrosage jusqu'à la capacité de la plante

ADR : [ADR-027](../../ADR/termines/027-arrosage-jusqu-a-la-capacite.md) (Accepté le 2026-11-24).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| S0 | ADR-027, plan, ligne dans l'état d'ensemble, renvoi daté dans ADR-001 | Terminée (2026-11-24) | — | Toutes | S | — |
| A1 | Règle et port : cible = capacité de la plante, `max` exposé par l'adaptateur, tests rouges puis verts | Terminée (2026-11-24) | S0 | D01, D02, D03 | M | — |
| A2 | Comportement de bout en bout : arroseur, goutte-à-goutte, hors chargement ; cas 95 → 100 et capacité déclarée | Terminée (2026-11-24) | A1 | D01-D04 | M | A3 |
| A3 | Documents : spécifications F21/F33/techniques, wiki EN/FR, page Workshop (11 langues), CHANGELOG | Terminée (2026-11-24) | A1 | D01-D04 | M | A2 |
| A4 | Passage en jeu : arroseur (69 → 100), arroseur automatique, goutte-à-goutte | Terminée (2026-11-24) | A2, A3 | Toutes | S | — |

## Fiches

### S0 — Décision et plan

Statut : Terminée (2026-11-24).
- `docs/ADR/027-arrosage-jusqu-a-la-capacite.md` (Accepté) et son plan ; `docs/ADR/README.md` : ligne 027.
- `docs/ADR/termines/001-reseau-eau-ouvert.md` : en-tête (date de mise à jour) et renvoi daté dans D19.

Preuve du vert : sans objet (documents seuls).

### A1 — Règle et port

Statut : Terminée (2026-11-24).
- `server/LiveWater/LWT_GameFarming.lua` : `plant(x, y, z)` rend aussi la capacité de la plante
  (`max = p.waterNeededMax`), documentée dans l'en-tête du port.
- `server/LiveWater/LWT_Plants.lua` : `Plants.capacity` et `dosesFor` visent la capacité au lieu du besoin de stade.
  Règle exacte (D01) : `waterNeededMax` déclaré et positif → `min(100, max(waterNeeded, waterNeededMax))`, sinon 100 ;
  doses `ceil((capacité - waterLvl) / 10)` ; aucune dose à 100. L'en-tête du fichier (les deux paragraphes qui décrivent
  la règle et le port) est réécrit.
- `tests/test_plants.py` (nouveau) : 12 cas de la règle pure — capacité absente (100), capacité déclarée (85), capacité
  aberrante (0 → 100 ; 60 avec besoin 70 → 70 ; 120 → 100), plante à 95 (1 dose), plante à 100 (0 dose), plante morte
  (0 dose), besoin 0 (capacité 100).
- `tests/test_sprinkler.py` : le double `plant` gagne le champ `max`.

Preuve du vert : rouge constaté (`test_plants` : 7 échecs sur 12, dont `doses(70, 70, nil) = 0` au lieu de 3), puis
`python -B -m unittest discover -s tests` → `Ran 653 tests` / `OK` après le rebasage d'A2 ;
`python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked`.

### A2 — Comportement de bout en bout

Statut : Terminée (2026-11-24).
- `tests/test_sprinkler.py` : `test_open_it_fills_the_plants_under_their_capacity_by_200_ml_doses` (45 → 100, 6 doses) ;
  nouveau `test_a_plant_is_filled_up_to_its_capacity` (95 → 100 en une dose ; 80 avec capacité 85 → 90 ; 85 avec
  capacité 85 → rien) ; le test de rayon part de 95/100 pour rester un test de zone.
- `tests/test_drip.py` : les deux cases arrosées prennent les deux doses que leur débit permet (2 au lieu de 1 pour la
  plante à 10).
- `tests/test_combo_outlets.py` : la première sortie remplit la plante (10 doses), la seconde prélève son débit sans
  dose à donner ; le nom du test suit.
- `tests/test_timer.py` : 6 doses au premier pas (40 → 100), rien aux deux suivants.
- `tests/test_away.py` : la culture hors chargement monte à 100 (10 doses) ; la sauvegarde, le jet et le débit ne
  changent pas.

Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 653 tests` / `OK` (rouge constaté avant : 8 échecs sur
les anciennes attentes) ; `python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked`.

### A3 — Documents et version

Statut : Terminée (2026-11-24).
- `docs/specifications-fonctionnelles.md` : F21 et F33 (plantes sous leur capacité, remplies jusqu'à 100/100 ou
  `waterNeededMax`, sources ADR-027).
- `docs/specifications-techniques.md` : section d'arrosage (capacité, port `farming`, deux sorties sur une plante).
- `docs/architecture.md` : description de `LWT_Plants` et de l'adaptateur.
- `docs/wiki/fr/01-premiers-pas.md` (§ 7) et `docs/wiki/en/01-getting-started.md` (§ 7) : la plante se remplit jusqu'à
  100/100 comme à l'arrosoir.
- `docs/wiki/fr/05-options-sandbox.md` et `docs/wiki/en/05-sandbox-options.md` : « se remplissent jusqu'à 100/100 ».
- `README.steam` et ses 10 traductions : une phrase dans la puce de l'arroseur.
- `CHANGELOG.md` : entrée 1.0.3 avec le rapport du joueur.

Preuve du vert : `python -B tools/check_mod.py` → `OK: 121 Lua file(s) checked` ; relecture des textes.

### A4 — Passage en jeu

Statut : Terminée (2026-11-24).
- `autotest/lwt_hooks.lua` : après les deux pas « sans filtre », la culture du scénario est mise à 69 avec
  `waterNeeded` 70 (fixture), un pas de dix minutes passe, puis le contrôle lit le niveau : 100. Le reste du scénario
  passe sans changement : arroseur automatique (trois pas servis puis fermé) et ligne de goutte-à-goutte (culture
  arrosée). La règle de capacité est commune aux deux sorties (`LWT_Plants`) ; le passage en jeu prouve le remplissage
  à 100 sur l'arroseur manuel, et le câblage des deux autres sorties par leurs contrôles existants.

Preuve du vert : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code de sortie 0,
`summary=98/98 PASS`, dossier `runs/20261124-223759-sp-cda714f6f0ac` ; lignes de `result.txt` :
`PASS crop set to 69 under a stage need of 70 (ADR-027) - level 69` et
`PASS a crop at 69 under a stage need of 70 is filled to 100 (ADR-027 D01) - level 100`.

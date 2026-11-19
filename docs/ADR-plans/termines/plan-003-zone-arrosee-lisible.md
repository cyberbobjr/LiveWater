# Plan 003 — Zone arrosée lisible

ADR : [ADR-003](../../ADR/termines/003-zone-arrosee-lisible.md) (Accepté le 2026-11-18).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| Z01 | Zone carrée : fonction partagée des cases arrosées, utilisée par `LWT_Plants` | Terminée (2026-11-18) | ADR accepté | D01 | S | Z03 |
| Z02 | Surlignage à la demande : « Voir / Masquer la zone arrosée » au clic droit d'un arroseur | Terminée (2026-11-18) | Z01 | D02 | M | Z03 |
| Z03 | Jet qui fait le tour : 8 images (S, SE, E, NE, N, NW, W, SW), tuiles et carte de profondeur, boucle du client | Terminée (2026-11-18) | ADR accepté | D03 | M | Z01 |
| Z04 | Test en jeu et documentation | Terminée (2026-11-18) | Z01-Z03 | D01-D03 | S | — |

## Fiches

### Z01 — Zone carrée

- `LWT_SprayArea.squares` partagé (serveur et client).
- Preuve du vert : « Ran 307 tests … OK » (tests/test_sprinkler.py, coin du carré arrosé, case à 3 de distance non).

### Z02 — Surlignage

- `client/LiveWater/LWT_AreaView.lua` ; `LWT_GameSettings` passé dans `shared` (le client lit le même multiplicateur).
- Preuve du vert : « Ran 310 tests … OK » (tests/test_area_view.py : 25 cases, 49 avec ×1,5, rien sur un tuyau).

### Z03 — Jet

- 8 images × 4 orientations aux index 128-159 (80-103 libérés : 104-123 portent les manchons d'ADR-002).
- Preuve du vert : « Ran 310 tests … OK » ; carte de profondeur « hits outside the sprite 0 » (2 px de brume sans
  profondeur sur la tuile 135, sans effet visible).

### Z04 — Test en jeu et documentation

- Preuve : `pzdev sp LiveWater/autotest/scenarios/visual.json` → code 0, `summary=47/47 PASS`,
  `runs/20261118-203759-sp-62219add6a94` (jet qui change d'image en tournant : sprites 139, 151, 131).
- Non couvert par l'automate : le clic sur « Afficher la zone arrosée » (couvert hors jeu, tests/test_area_view.py).

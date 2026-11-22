# Plan 025 — La pompe à bras du jeu est une source d'eau propre

ADR : [ADR-025](../../ADR/termines/025-pompe-a-bras-source-d-eau-propre.md) (Accepté le 2026-11-22).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| P1 | Tuiles de la pompe à bras dans la sorte `well`, test, wiki EN/FR, spécifications, CHANGELOG | Terminée (2026-11-22) | ADR accepté | D01, D02, D03 | S | — |
| P2 | Passage en jeu : pompe à eau posée contre une pompe à bras | Terminée (2026-11-22) | P1 | D01 | S | — |

## Fiches

### P1 — Sorte de source et textes

Statut : Terminée (2026-11-22).
- `shared/LiveWater/Sources/LWT_SourceWell.lua` : `camping_01_64` à `camping_01_67` ajoutées.
- Test : `tests/test_well.py`, `test_a_pump_next_to_a_hand_pump_draws_clean_water` (les quatre orientations).
- `docs/wiki/{en,fr}/01-*` (section Puits), `docs/specifications-fonctionnelles.md` (F12),
  `docs/specifications-techniques.md`, `CHANGELOG.md` (Unreleased).

Preuves du vert : `python -B -m unittest discover -s tests` → `Ran 617 tests` / `OK` ; `python -B tools/check_mod.py` →
`OK: 120 Lua file(s) checked`.

### P2 — Passage en jeu

Statut : Terminée (2026-11-22). Scénario ajouté à `autotest/lwt_hooks.lua` (solo) : une pompe à bras du jeu posée loin
de toute eau, la tuile porte de l'eau non croupie, la pompe à eau posée à côté par le placement vanilla relève la
source `well`, eau propre ; puis tout est repris.
- Solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code de sortie 0, `summary=83/83 PASS`, dossier
  `runs/20261122-143717-sp-eb3a6eff2331` (2 vérifications « hand pump »).

Non joué en jeu : une pompe à bras d'origine de la carte (le scénario en pose une, même tuile) ; les trois autres
orientations (couvertes par le test hors jeu) ; le serveur dédié (la reconnaissance d'une source est le même code
qu'en solo).

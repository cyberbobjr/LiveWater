# Plan 015 — Expérience gagnée par les recettes : Travail des métaux et Électricité

ADR : [ADR-015](../ADR/015-experience-des-recettes.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | `xpAward` des recettes de fabrication et de démontage, test | À valider (passage en jeu E03) | ADR accepté | D01 à D04 | S | — |
| E02 | Wiki EN/FR, CHANGELOG | Terminée (2026-11-19) | E01 | D01, D02 | S | — |
| E03 | Passage en jeu par l'utilisateur | À faire | E01 | D01, D02 | S | — |

## Fiches

### E01 — Recettes

Fichiers : `scripts/LWT_recipes.txt`, `scripts/LWT_dismantle.txt`, nouveau `tests/test_xp_awards.py` (3 tests : chaque recette classée, `xpAward` attendu ou absent, niveaux requis
inchangés).

Preuve du vert : `python -B tests/test_xp_awards.py` → `Ran 3 tests`, `OK` ; `python -B -m unittest discover -s tests` →
`Ran 541 tests`, `OK` ; `python -B tools/check_mod.py` → `OK: 108 Lua file(s) checked`.

### E02 — Documentation

Wiki EN/FR 01 (§ 13, sous-section « Experience » / « Expérience », tableau), CHANGELOG (Unreleased).
Preuve du vert : suite complète ci-dessus.

### E03 — Passage en jeu

Protocole court, par l'utilisateur : fabriquer une vanne (Travail des métaux +5), une pompe (Électricité +15),
démonter un tuyau (Travail des métaux +2) ; une cartouche filtrante ne donne rien.

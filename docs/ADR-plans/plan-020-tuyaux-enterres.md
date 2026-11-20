# Plan 020 — Tuyaux enterrés

ADR : [ADR-020](../ADR/020-tuyaux-enterres.md) (Proposé le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| T1 | Constat sur le code : potager et règles de pose autour d'un tuyau (D08), index libres du contrat des tuiles (D02) | À faire | ADR accepté | D02, D08 | S | T2 |
| T2 | 16 tuiles enterrées, intensité « A » (ADR D02) : générateur 2D dans `source/tiles/`, tiledef, pack, contrat des tuiles ; pas de liaison Viewpoint | À faire | T1 | D02, D09 | M | T3 |
| T3 | État `buried`, choix de l'image par `LWT_Sprites`, champ d'API `buried` (révision 25), ramassage et démontage refusés | À faire | ADR accepté | D01, D05, D06, D07 | M | T2 |
| T4 | Action Enterrer / Déterrer : menu, outil, sol (D04), action chronométrée, commande vers l'autorité | À faire | T3 | D03, D04 | M | — |
| T5 | Traductions (11 langues), wiki EN/FR, CHANGELOG, spécifications | À faire | T4 | toutes | S | — |
| T6 | Passage en jeu par l'utilisateur | À faire | T2, T4 | toutes | S | — |

## Fiches

### T6 — Passage en jeu

Protocole : poser trois tuyaux en L sur de l'herbe, les enterrer à la pelle, vérifier la trace tout juste visible et
l'eau qui passe ; ajouter un tuyau au bout (la trace suit) ; essayer sur l'asphalte (option grisée) ; essayer de
ramasser un tuyau enterré (refusé) ; le déterrer et le ramasser.

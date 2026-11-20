# Plan 021 — Le raccord de remplissage fait le plein d'un groupe électrogène

ADR : [ADR-021](../ADR/021-plein-des-groupes-electrogenes.md) (Proposé le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| G1 | Constat Java : ordre entre `LoadChunk` / `LoadGridsquare` et la première mise à jour d'un `IsoGenerator` (Q01) | À faire | ADR proposé | D05, Q01 | S | — |
| G2 | Genre de récipient « groupe électrogène » : lecture, plein près du joueur, essence seulement | À faire | ADR accepté | D01, D02, D03 | M | — |
| G3 | Compte d'absence et reprise au chargement (arrêt, essence, usure, redémarrage) ; groupes de secours LiveWire exclus | À faire | G1, G2 | D04, D05, D06 | M | — |
| G4 | Information du raccord, traductions (11 langues), wiki EN/FR, CHANGELOG, spécifications | À faire | G3 | D07 | S | — |
| G5 | Passage en jeu par l'utilisateur | À faire | G3 | toutes | S | — |

## Fiches

### G5 — Passage en jeu

Protocole : baril d'essence, pompe à eau contre le baril, trois tuyaux, raccord de remplissage contre un groupe
électrogène en marche ; vérifier le plein ; partir loin plusieurs heures de jeu, revenir : le groupe tourne encore, le
baril a baissé d'autant ; recommencer avec le baril vide : le groupe s'arrête comme dans le jeu de base.

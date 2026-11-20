# Plan 011 — La pompe à eau puise dans un baril

ADR : [ADR-011](../../ADR/termines/011-pompe-sur-baril.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| P01 | Capacité `vessel`, champ `orVessel` d'intake, `GameSite:hasVessel`, `LWT_Sensed`, `Flow:supply` par pompe (D05) ; API révision 21 ; traductions ; tests | Terminée (2026-11-20) | ADR accepté | D01-D05 | M | — |
| P02 | Passage en jeu : pompe posée contre un récupérateur d'eau loin de l'eau, arrosage depuis le baril | Terminée (2026-11-20) | P01 | toutes | S | — |

## Fiches

### P01 — Pompe contre un baril

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Fait : `Capabilities/LWT_CapVessel.lua` (`sense`, `container` → "draw", `draw` eau seule, `lines` « Baril : N L »
  quand un baril est là), `LWT_Sensed.lua` (enregistrement commun au raccord), `intake.orVessel`,
  `GameSite:hasVessel()` (4 côtés, `WaterObjects.isBarrel`), `LWT_GameSettings.listedContainers`, `LWT_Flow:supply`
  (chaque pompe : l'eau de son baril, sinon sa source ; D05), `LWT_PartPondPump` (`intake = { orVessel = true }`,
  `vessel = { rate = 50 }`), `IGUI_LWT_NoSource` et `IGUI_LWT_Vessel_Content` dans les 11 langues.
- Tests : `tests/test_pump_barrel.py` (pose, pompage, qualité, carburant refusé, baril vide, baril avant l'étang, deux
  pompes sur un réseau, transferts sans création d'eau, partage, information, API, `hasVessel`).
- Preuves : voir P02 (suite complète après ADR-012 et 013).

### P02 — Preuves en jeu

- Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
- Scénario solo : « pump set down against the rain collector away from water (vanilla placement) » (source nil), « the
  pump against the barrel waters from the barrel » (baril 50 → 30 L).
- Passages : voir plan 013, fiche R02 (passages communs aux ADR-011 à 013).

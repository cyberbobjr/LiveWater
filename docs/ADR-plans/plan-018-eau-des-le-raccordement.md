# Plan 018 — L'eau arrive dès qu'un point d'eau est raccordé

ADR : [ADR-018](../ADR/018-eau-des-le-raccordement.md) (Accepté le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Méthode de pas immédiat de `LWT_Clock` (vanne et raccordement), enveloppe de `ISPlumbItem.complete`, tests | À valider (passage en jeu E03) | ADR accepté | D01, D02, D03 | M | — |
| E02 | CHANGELOG, spécifications | Terminée (2026-11-20) | E01 | D01 | S | — |
| E03 | Passage en jeu par l'utilisateur : raccorder un évier d'une maison déjà alimentée, l'eau coule tout de suite | À faire | E01 | D01 | S | — |

## Fiches

### E01 — Code

Statut : À valider (passage en jeu E03).

- `server/LiveWater/LWT_Clock.lua` : `Clock:bringForward(id)` extrait de `switched` (seul pas immédiat, plafond
  `MAX_AHEAD`, D02) ; `Clock:hasten(parts)` avance une fois chaque réseau distinct ; `switched` appelle `bringForward`.
- `server/LiveWater/LWT_PlumbWatch.lua` (nouveau) : `PlumbWatch.wrap(class, probe, react)` (une seule enveloppe, champ
  `LiveWaterPlumbWatch` ; original d'abord, mêmes arguments, mêmes résultats ; réaction seulement si le point d'eau
  passe de « sans source extérieure » à « avec ») ; `PlumbWatch:plumbed(x, y, z)` : `Relays:touched` puis
  `Clock:hasten(Relays:covering(x, y, z))` (D01).
- `server/LiveWater/LWT_Relays.lua` : `covering(x, y, z)` (arrivées d'eau chargées dont la zone couvre la case).
- `server/LiveWater/LWT_GamePlumbing.lua` : `GamePlumbing.plumbedFixture(obj)` (sonde : `waterPiped` et
  `getUsesExternalWaterSource`).
- `server/LiveWater/LWT_Server.lua` : `plumbWatch` construit dans `build` ; enveloppe posée à `OnInitGlobalModData`.
- Où tourne `complete` : solo `LuaTimedActionNew.java:161-167` (hors client) ; multijoueur, serveur seulement
  (`NetTimedAction.java:134-136`, action reconstruite `145-169`) ; `ISPlumbItem.lua` est un fichier `shared`.
- Tests : `tests/test_plumb_watch.py` (9 : eau tout de suite et relevé, pas sauté ensuite, action ratée ou point d'eau
  déjà raccordé sans effet, hors zone sans effet, plafond partagé avec les vannes, enveloppe unique, câblage) ;
  `tests/test_valve.py` (pas immédiat de la vanne) inchangé et vert.
- Preuves (2026-11-20) : `python -B -m unittest discover -s tests` → `Ran 566 tests` / `OK` ;
  `python -B tools/check_mod.py` → `OK: 112 Lua file(s) checked`.

### E02 — Documentation

Statut : Terminée (2026-11-20).

- `CHANGELOG.md` (Unreleased) : une ligne joueur (eau dès le raccordement à la clé).
- `docs/specifications-techniques.md` : section « Pas immédiat : vanne et raccordement » ; relevé des relais au
  raccordement.
- `docs/architecture.md` : module `LWT_PlumbWatch.lua`.
- `docs/ADR/README.md` : ligne ADR-018.

### E03 — Passage en jeu

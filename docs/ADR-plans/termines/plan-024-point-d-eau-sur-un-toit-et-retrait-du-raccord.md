# Plan 024 — Point d'eau sur un toit ; « Supprimer le raccord »

ADR : [ADR-024](../../ADR/termines/024-point-d-eau-sur-un-toit-et-retrait-du-raccord.md) (Accepté le 2026-11-22).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| T1 | Zone du mode bâtiment : cases au-dessus d'une pièce du bâtiment | Terminée (2026-11-22) | ADR accepté | D03 | S | T3 |
| T2 | Menu « Raccorder » sur un toit (règle pure « sur un toit », entrée de menu, pas de doublon avec le jeu) | Terminée (2026-11-22) | T1 | D01, D02 | S | T3 |
| T3 | Action « Supprimer le raccord » (action, commande, menu, lave-linge, traductions 11 langues) | Terminée (2026-11-22) | ADR accepté | D04, D05 | M | T1 |
| T4 | Tests du point d'eau démonté ou déplacé sur un toit | Terminée (2026-11-22) | T1 | D06 | S | — |
| T5 | Wiki EN/FR, spécifications, CHANGELOG | Terminée (2026-11-22) | T2, T3 | toutes | S | — |
| T6 | Passage en jeu : scénario automatique (évier sur un toit raccordé, eau reçue, raccord supprimé, évier ramassé), solo puis serveur avec un client | Terminée (2026-11-22) | T2, T3, T4 | toutes | M | — |

## Fiches

### T1 — Zone du mode bâtiment

Statut : Terminée (2026-11-22).
- `shared/LiveWater/LWT_InletArea.lua` : `above(b, x, y, z)` (une pièce du bâtiment sous la case, à un niveau du
  bâtiment) ajouté à `holds` du mode bâtiment.
- `server/LiveWater/LWT_GamePlumbing.lua` : `fixtures(area)` cherche d'abord le point d'eau de la case, puis demande
  à la zone (peu de cases en portent un ; la zone interroge le bâtiment).
- Tests : `tests/test_roof.py` classe `RoofArea` (toit, étages construits au-dessus, case à côté du bâtiment, toit
  d'une aile basse, portée, réservoir au-dessus d'un point d'eau du toit) ; `tests/test_inlet.py` mis à jour (le toit
  est dans la zone).

### T2 — « Raccorder » sur un toit

Statut : Terminée (2026-11-22).
- `shared/LiveWater/LWT_Plumbing.lua` (pur) : `onRoof`, `plumbOffer`, `unplumbRefusal`.
- `shared/LiveWater/LWT_WaterObjects.lua` : `plumbInfo(obj)` (raccordé, réservoir au-dessus, pièce, pièce en dessous).
- `client/LiveWater/LWT_RoofPlumbMenu.lua` : option du jeu (`ContextMenu_PlumbItem`, `onPlumbItem`) ;
  `client/LiveWater/LWT_WrenchMenu.lua` : nom, clé, icône et infobulle communs.
- Tests : `tests/test_roof.py` classe `PlumbRule`.

### T3 — « Supprimer le raccord »

Statut : Terminée (2026-11-22).
- `client/LiveWater/LWT_UnplumbAction.lua` (dérive `LWT_PartAction` : clé équipée, 100 ticks, son
  `RepairWithWrench`), `client/LiveWater/LWT_UnplumbMenu.lua`.
- `server/LiveWater/Commands/LWT_CmdUnplumb.lua` (arguments, `not_plumbed`, portée, `need_tool`), inscrit dans
  `LWT_Server.lua` ; `LWT_Protocol.UNPLUMB` ; raison `not_plumbed` → `IGUI_LWT_NoPlumbing`.
- `server/LiveWater/LWT_GamePlumbing.lua` : `plumbInfo(x, y, z)`, `unplumb(x, y, z)`.
- Traductions : `ContextMenu_LWT_Unplumb`, `IGUI_LWT_NoPlumbing` dans les 11 langues.
- Tests : `tests/test_roof.py` classe `UnplumbCommand`.

### T4 — Point d'eau démonté ou déplacé

Statut : Terminée (2026-11-22). Aucun code : `tests/test_roof.py` classe `RoofFixtureMoved` (le réservoir part avec
le point d'eau du toit et revient au-dessus du nouvel emplacement).

### T5 — Documentation

Statut : Terminée (2026-11-22). `docs/wiki/{en,fr}/01-*` (sur un toit, supprimer le raccord),
`docs/specifications-fonctionnelles.md` (F37), `docs/specifications-techniques.md` (commande `unplumb`, zone),
`docs/architecture.md`, `CHANGELOG.md` (Unreleased). ADR D04 précisé (action cliente puis commande).

Preuves du vert (2026-11-22, après T1 à T5) : `python -B -m unittest discover -s tests` → `Ran 616 tests` / `OK` ;
`python -B tools/check_mod.py` → `OK: 120 Lua file(s) checked`.

### T6 — Passage en jeu

Statut : Terminée (2026-11-22). Scénario ajouté à `autotest/lwt_hooks.lua` (solo : menu réel du monde, action
vanilla `ISPlumbItem`, commande réelle `unplumb`, ramassage vanilla ; multijoueur : évier posé et raccordé par le
serveur, raccord supprimé par le client 1 depuis le toit).
- Solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code de sortie 0, `summary=81/81 PASS`, dossier
  `runs/20261122-125956-sp-24896ea92d8c` (12 vérifications « roof »).
- Serveur dédié et un client : `python PZDevKit/pzdev.py mp LiveWater --clients 1 --client-run --wait-idle 3600` →
  code de sortie 0, serveur `28/28 PASS`, client 1 `8/8 PASS`, dossier `runs/20261122-124829-mp-8fb76a1ec46e`.

Mise au point du scénario (défauts du test, pas du mod) : l'objet du point d'eau de la maison gardé avant le trajet du
joueur n'a plus d'image une fois la maison déchargée puis rechargée ; le scénario relit le point d'eau sur sa case.

Non joué en jeu : le geste complet à la souris (marcher jusqu'à l'évier, équiper la clé, barre de progression) ; un
étage construit par le joueur au-dessus d'un bâtiment de la carte ; une base construite ; un lave-linge.

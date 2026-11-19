# Plan 012 — Producteurs et consommateurs : seule une pompe met l'eau dans le réseau ; API ouverte

ADR : [ADR-012](../ADR/012-producteurs-et-consommateurs.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| Q01 | Mode Pomper du raccord supprimé (capacité, commande, protocole, traductions, variantes) ; crochet `container` | À valider | ADR accepté | D02 | M | — |
| Q02 | Gravité supprimée (`Flow:gravity`, `byGravity`, `gravity`, racines de l'horloge et du réseau) | À valider | Q01 | D01, D03 | M | — |
| Q03 | `LiveWater.API.registerOutlet`, registre `LWT_OutletTypes`, `Outlets:adopt` ; API révision 22 | À valider | Q02 | D04 | M | — |
| Q04 | Live Wire : la pompe contre un baril reste consommatrice ; passages en jeu ; documentation | À valider | Q03 | D05 | S | — |

## Fiches

### Q01 — Mode Pomper supprimé

- Statut : À valider.
- Fait : `LWT_CapFitting` ne fait plus que Remplir ; supprimés : `LWT_CmdSwitchFitting.lua`, `Protocol.SWITCH_FITTING`,
  `Reasons.not_fitting`, `ContextMenu_LWT_FittingToPump/ToFill`, `IGUI_LWT_Fitting_fill/pump`, variantes `pump*` de
  `LWT_PartBarrelFitting` (tuiles laissées dans le jeu de tuiles), branche des pompes à carburant de
  `LWT_GameContainers` ; `fittingMode` remplacé par `container` ("fill" ou "draw"). Tests supprimés avec leur code.

### Q02 — Gravité supprimée

- Statut : À valider.
- Fait : `Flow:gravity`, `draws`, `byGravity`, argument gravité de `zone`/`step`, `rootHook` de `Network:reach`,
  repli gravité de `Clock:isAwake`/`behindClosed` ; `Flow:produce` (ce que donne une pompe).

### Q03 — API des consommateurs

- Statut : À valider.
- Fait : `shared/LiveWater/LWT_OutletTypes.lua` (contrat need/deliver, release/cut facultatifs, types réservés,
  scellé à `OnInitGlobalModData`), `API.registerOutlet`, `Outlets:adopt`, révision 22.
- Tests : `tests/test_outlet_api.py` (abreuvoir d'un autre mod servi après un pas, doublons et types réservés refusés,
  gestionnaires invalides refusés, fermeture, révision).

### Q04 — Live Wire, preuves, documentation

- Statut : À valider.
- Tests : `tests/test_pump.py` `test_a_pump_against_a_barrel_is_a_live_wire_consumer_too`.
- Passages : voir plan 013, fiche R02.

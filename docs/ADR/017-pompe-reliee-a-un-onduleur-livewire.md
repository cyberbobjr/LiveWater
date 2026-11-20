# ADR-017 — Pompe à eau reliée par fil à un onduleur LiveWire

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-017-POMPE-RELIEE-A-UN-ONDULEUR-LIVEWIRE` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | voir le [plan 017](../ADR-plans/plan-017-pompe-reliee-a-un-onduleur-livewire.md) |
| Décideur | l'utilisateur (portée retenue : « Portée du câble », 2026-11-20) |
| Portée | `batman_LiveWater` : inscription LiveWire de la pompe (`LWT_Power.lua`, passage en `shared`), règle « la pompe a du courant », wiki LiveWire EN/FR, descriptions Steam, CHANGELOG |
| Documents liés | ADR-004 de LiveWire (consommateurs reliés par fil, API révision 9), [ADR-010](010-pompe-a-eau-et-vanne-immediate.md) |
| Références | `server/LiveWater/LWT_Power.lua` (inscription à `OnInitWorld`, `MIN_REVISION = 6`, repli `gridAt` hors chargement) |
| Origine | demande de l'utilisateur du 2026-11-20 : « pouvoir connecter une pompe à eau à un onduleur de LiveWire, mais cela doit rester facultatif si LiveWire n'est pas installé, dans ce cas utiliser le courant présent sur la case » |

## Décisions

- **D01 — Pompe reliable.** Avec LiveWire révision 9 ou plus, la pompe s'inscrit avec `link = { level = 2 }`
  (Électricité 2, le niveau de sa recette). Elle se relie par fil à un onduleur comme un appareil LiveWire, jusqu'à la
  portée du câble, même hors de sa zone alimentée. L'arroseur automatique (5 W) n'est pas reliable : il garde le courant
  de sa case.
- **D02 — Courant de la pompe.** Reliée : courant et facturation de son onduleur (`API.consumerPowered`, et
  `API.consumerLinkPowered` quand sa case n'est pas chargée). Non reliée, LiveWire de révision 6 à 8, ou sans LiveWire :
  courant de sa case, comme aujourd'hui (générateur, réseau public, zone d'un onduleur).
- **D03 — Inscription partagée.** L'inscription passe dans un fichier `shared`, faite des deux côtés, pour que les menus
  du client reconnaissent la pompe ; elle reste faite avant le scellé de LiveWire (`OnInitGlobalModData`).
- **D04 — Textes.** Wiki « LiveWire » EN/FR et descriptions Steam : la pompe se relie par fil à un onduleur, sinon elle
  prend le courant de sa case.

## Mise à jour du 2026-11-20

Consommation de la pompe en marche : **150 W** au lieu de 250 W (demande de l'utilisateur : « 250W c'est beaucoup
trop, c'est plus que un congélateur, réduit à 150W »). Valeur de la pièce (`LWT_PartPondPump.lua`) et défaut de la
capacité `pump` (`LWT_CapPump.lua`) ; tests `test_pump.py` ; wiki, spécifications et 11 descriptions Steam.

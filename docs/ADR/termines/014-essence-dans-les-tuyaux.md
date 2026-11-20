# ADR-014 — Essence dans les tuyaux : pompe sur une station-service, un seul liquide par réseau

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-014-ESSENCE-DANS-LES-TUYAUX` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 014](../../ADR-plans/termines/plan-014-essence-dans-les-tuyaux.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : pompe contre une pompe de station-service (récipients, capacité `vessel`, site de pose), liquide d'un réseau (`LWT_Flow`), liquides acceptés par les consommateurs (capacité `outlet`, raccord de remplissage, mangeoires), traductions, tests, scénario en jeu, documentation |
| Documents liés | [ADR-011](011-pompe-sur-baril.md), [ADR-012](012-producteurs-et-consommateurs.md) (D04 API des consommateurs), [ADR-013](013-raccord-de-remplissage-et-abreuvoirs.md), [ADR-005](005-filtre-a-l-arrivee-d-eau.md) (D03 familles de liquides) |
| Références | `IsoObject.getPipedFuelAmount` / `setPipedFuelAmount` (Java 42.22, `IsoObject.java:2461, 2534`) ; `LWT_Flow` (familles « water », « fuel », « other », état `wrong_fluid`) ; `IsoFeedingTrough.createFluidContainer` (liste blanche eau et eau souillée) |
| Origine | demande de l'utilisateur du 2026-11-19 : « il faudrait que l'on puisse brancher une pompe à eau sur une station service pour alimenter un circuit, mais il est évident que le circuit sera rempli d'essence, donc les consommateurs (connecteur maison et arroseur et mangeoire) ne peuvent pas accepter ce type de liquide. Ce qui veut dire que l'API devra demander aux consommateurs ce qu'ils acceptent comme liquide » ; choix : « un seul liquide par réseau » |

## Décisions

- **D01 — Pompe contre une pompe à essence.** La pompe à eau se pose aussi contre une pompe de station-service (objet
  qui a du carburant canalisé, `getPipedFuelAmount`) et y puise l'essence, jusqu'à son débit, avec du courant comme
  toujours. La station se vide (`setPipedFuelAmount`) ; vide, la pompe ne donne rien.
- **D02 — Un seul liquide par réseau.** Un réseau transporte une seule famille de liquide par pas (eau — propre ou
  souillée —, essence, ou autre). La pompe posée la première (ordre de pose) impose la famille ; une pompe qui donnerait
  une autre famille ne donne rien ce pas et son information dit « Un autre liquide est dans les tuyaux ». Pour avoir
  les deux, on sépare les réseaux (ou on ferme une vanne : chaque zone a sa première pompe).
- **D03 — Les consommateurs disent ce qu'ils acceptent.** La capacité `outlet` reçoit un champ `takes` (« water » par
  défaut, « fuel », « other », « any »). LiveWater ne livre à un consommateur que ce qu'il accepte ; sinon il ne prend
  rien et son état est `wrong_fluid` (« Ce n'est pas de l'eau » pour un consommateur d'eau, « Mauvais liquide »
  sinon). Arrivée d'eau de la maison, arroseurs, goutte-à-goutte : eau seulement. Un consommateur d'un autre mod
  (`registerOutlet`) sans `takes` ne reçoit que de l'eau.
- **D04 — Le raccord de remplissage ne mélange jamais.** Il remplit un récipient vide de n'importe quel liquide
  transporté, un récipient qui contient de l'eau avec de l'eau, un récipient qui contient de l'essence avec de
  l'essence ; jamais une mangeoire avec autre chose que de l'eau (liste blanche du jeu).

## Conséquences

- API révision 23 (`takes`, D01 sur la capacité `vessel`).
- Réutilise les familles et l'état `wrong_fluid` qui existent déjà dans `LWT_Flow`.

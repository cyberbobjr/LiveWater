# ADR-013 — Raccord de remplissage : barils, récupérateurs d'eau et mangeoires

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-013-RACCORD-DE-REMPLISSAGE-ET-ABREUVOIRS` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | En cours ; voir le [plan 013](../ADR-plans/plan-013-raccord-de-remplissage-et-abreuvoirs.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : nom affiché et infobulle du raccord, remplissage des mangeoires vanilla (adaptateur des récipients, état du raccord), traductions, tests, scénario en jeu, documentation |
| Documents liés | [ADR-012](012-producteurs-et-consommateurs.md) (le raccord ne fait plus que remplir), [ADR-005](termines/005-filtre-a-l-arrivee-d-eau.md) (D07 : l'eau entre souillée dans un récipient) |
| Références | `IsoFeedingTrough` (Java 42.22 : `createFluidContainer` l. 495, réservoir d'eau propre ou souillée qui attrape la pluie ; `onFoodAdded` retire le réservoir, `onRemoveFood` le remet ; `checkOverlayFull` l. 261) ; `FeedingTroughDefinitions.lua` (50 à 150 L) ; `AnimalData` l. 910-913 (la bête boit `removeWater` sans regarder la qualité de l'eau) |
| Origine | demande de l'utilisateur du 2026-11-19 : « le raccord de baril sur l'abreuvoir, mais il faut changer son nom dans ce cas, et mettre dans les tooltips qu'il alimente les barils, les récupérateurs d'eau et les abreuvoirs » ; puis « remplace "abreuvoir" par "mangeoire" pour respecter le terme français » |

## Décisions

- **D01 — Nouveau nom.** Le raccord de baril s'appelle **Raccord de remplissage** (EN **Fill Fitting**, et
  l'équivalent dans les autres langues) : objet, meuble, recettes de fabrication et de démontage, fenêtre,
  documentation. Les identifiants internes (`BarrelFitting`, `Mov_LiveWater_BarrelFitting`, recettes, sprites) ne
  changent pas.
- **D02 — Infobulle.** L'objet du raccord porte une infobulle : il remplit, depuis le réseau, le baril, le
  récupérateur d'eau de pluie ou la mangeoire posée contre lui.
- **D03 — Les mangeoires se remplissent.** Une mangeoire vanilla posée contre un raccord de remplissage reçoit l'eau du
  réseau, sans dépasser sa contenance. Son dessin d'eau suit le niveau (`checkOverlayFull`). L'eau y entre souillée,
  comme dans tout récipient (ADR-005 D07) : le jeu laisse les bêtes la boire (vérifié dans le code Java, pas en jeu),
  et une mangeoire attrape déjà de l'eau de pluie souillée.
- **D04 — Mangeoire pleine de nourriture.** Une mangeoire qui contient de la nourriture n'a pas de réservoir d'eau (règle
  du jeu) : le raccord ne lui donne rien et l'information dit « la mangeoire contient de la nourriture ». Une fois la
  nourriture finie, le remplissage reprend.

## Conséquences

- Pas de nouvelle pièce, recette ni tuile. Traductions des onze langues mises à jour.
- Un mod qui ajoute ses propres mangeoires les branche par `registerContainer` (récipient) ou `registerOutlet`
  (consommateur, ADR-012 D04).

# ADR-022 — Réservoir relais à la mesure du point d'eau

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-022-RESERVOIR-A-LA-MESURE-DU-POINT-D-EAU` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 022](../../ADR-plans/termines/plan-022-reservoir-a-la-mesure-du-point-d-eau.md) |
| Décideur | l'utilisateur (« ok pour A », 2026-11-20) |
| Portée | `batman_LiveWater` : taille des réservoirs relais (`LWT_Relays`, `LWT_GamePlumbing`), registre des fournisseurs de besoin et API (révision suivante), fournisseur pour Take a Bath and Shower, option de partie du plafond, traductions, tests, wiki, CHANGELOG |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D18, D21 réservoirs relais), [ADR-012](012-producteurs-et-consommateurs.md) (API ouverte), [ADR-018](018-eau-des-le-raccordement.md) |
| Références | `LWT_Relays.lua:42` (`CAPACITY` = `WaterObjects.RELAY_LITRES` = 25) ; LiveWire `LW_PumpTransfer.lua:130-137` (`resizeRelay` : `setCapacity` puis `sync`) ; Java 42.22 `ClothingWasherLogic.java:40, 74-88` (cycle de 90 min, 1 L par minute, arrêt à sec) ; Take a Bath and Shower 42.20 (Workshop 3592172476, lecture seule) : `TABAS_TakeShower.lua:236-290, 580` (douche puisée peu à peu jusqu'à `SandboxVars.TakeABathAndShower.ShowerConsumeWater`, 80 L par défaut, arrêtée si le robinet se vide), `TABAS_TubFluidContainerBase.lua:291` (`getCapacity` de la cuve) |
| Origine | demande de l'utilisateur du 2026-11-20 : le réservoir invisible de 25 L ne suffit pas à la douche (80 L) ni à la baignoire du mod Take a Bath and Shower ; LiveWire a une option de taille ; choix de la solution « demander le besoin au mod qui le connaît » |

## Contexte

Chaque point d'eau branché par une arrivée d'eau est servi par un réservoir invisible de 25 L posé un niveau au-dessus.
Le jeu n'expose nulle part le besoin en eau d'un équipement.

Constat sur le code (lecture, pas en jeu) :
- **Lave-linge** : il puise 1 L par minute de jeu pendant un cycle de 90 minutes, soit 10 L par pas de 10 minutes,
  et s'arrête seulement si son robinet est à sec. Un réservoir de 25 L rempli à chaque pas suffit tant que le réseau
  lui donne 10 L par pas.
- **Évier, toilettes, baignoire du jeu de base** : boire, se laver, laver un vêtement prennent quelques litres. Remplir
  un grand récipient au robinet s'arrête à ce que contient le réservoir, puis reprend au pas suivant : pas un besoin
  fixe, et grossir chaque évier immobiliserait de l'eau partout.
- **Douche de Take a Bath and Shower** : elle puise peu à peu jusqu'à 80 L (option du mod) et s'arrête quand le
  robinet se vide : avec 25 L, elle coupe au premier quart.

## Décisions

- **D01 — Le besoin vient de celui qui le connaît.** LiveWater tient un registre de fournisseurs de besoin : une
  fonction qui reçoit un point d'eau du jeu et rend des litres, ou rien. API publique `registerFixtureNeed(id, fn)`
  (révision suivante de l'API, additive). Aucun `if` sur un mod ou un type d'équipement dans le cœur.
- **D02 — Taille d'un réservoir.** Un réservoir prend la plus grande valeur entre 25 L et les besoins des points d'eau
  qu'il sert, bornée par le plafond (D04). Sans fournisseur, rien ne change : 25 L. Éviers, toilettes et lave-linge
  restent à 25 L (constat ci-dessus).
- **D03 — Fournisseur livré : Take a Bath and Shower.** Présent seulement si ce mod est chargé. Une douche demande
  `ShowerConsumeWater` ; une baignoire, la contenance de sa cuve. La façon dont le mod reconnaît une douche et une cuve
  est relevée dans son code à l'étape 1 du plan, et réutilisée telle quelle (ses fonctions, pas une copie).
- **D04 — Plafond.** Option de partie `LiveWater.RelayMaxLitres` (entier, 25 à 1 000, 300 par défaut) : aucun
  fournisseur ne fait dépasser ce volume à un réservoir.
- **D05 — Réservoirs déjà posés.** Un réservoir dont la taille voulue a changé est redimensionné au relevé suivant
  (`setCapacity`, puis synchronisation), comme dans LiveWire. Réduit, il perd l'eau au-dessus de sa nouvelle taille.
  Le relevé reste déclenché par les événements (ADR-001 D10) ; une option de partie changée prend effet au chargement.
- **D06 — Rien d'autre ne change.** Le débit de la pompe, le filtre et l'ordre de remplissage restent tels quels : une
  cuve de 300 L se remplit en une heure de jeu environ avec une pompe seule.

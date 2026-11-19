# ADR-005 — Le filtre passe de la pompe à l'arrivée d'eau ; l'arrosage prend toute eau

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-005-FILTRE-A-L-ARRIVEE-D-EAU` |
| Date de création et de mise à jour | 2026-11-18 |
| Statut | Accepté (2026-11-18) |
| Avancement | Terminé le 2026-11-19 ; voir le [plan 005](../../ADR-plans/termines/plan-005-filtre-a-l-arrivee-d-eau.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : tuiles de l'arrivée d'eau (176-183), pièces `LiveWater:PondPump`, `LiveWater:HouseInlet`, `LiveWater:DripLine`, capacité `outlet` (type `drip`), scénarios de test, documentation ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D17, Q02), [ADR-004](004-goutte-a-goutte.md) (D04, D05) |
| Références | `LWT_Flow.lua` : `Flow:purifierOf` cherche le premier filtre actif **de la sortie incluse** jusqu'à la pompe (le filtre agit déjà s'il est porté par la sortie) |
| Origine | remarque de l'utilisateur du 2026-11-18 : « comment tu peux alimenter un goutte-à-goutte sans pompe s'il faut filtrer l'eau, ce n'est pas logique » ; choix : « supprime le filtre pour l'arrosage, place le filtre plutôt au niveau du connecteur de maison, c'est plus logique » |

## Contexte

Le seul filtre (cartouche `LiveWater.WaterFilter`, ADR-001 D17) est dans la pompe. ADR-004 D05 exige de l'eau propre pour
le goutte-à-goutte, et ADR-004 D04 permet de l'alimenter sans pompe depuis un baril : sans pompe, pas de filtre, donc
jamais d'eau propre. Les deux décisions se contredisent.

## Décisions

- **D01 — Le filtre est dans l'arrivée d'eau de la maison.** La capacité `filter` (cartouche `LiveWater.WaterFilter`,
  500 L, usure au volume, menus Monter / Remplacer / Retirer le filtre) passe de `LiveWater:PondPump` à
  `LiveWater:HouseInlet`. Elle ne filtre que l'eau qui entre dans la maison. Remplace ADR-001 D17 pour l'emplacement ;
  la cartouche, sa recette et sa capacité ne changent pas.
- **D02 — La pompe n'a plus de filtre.** Elle n'est plus dessinée que par marche / arrêt (24-27, 28-31) ; les tuiles
  « avec filtre » 32-39 ne servent plus.
- **D03 — L'arrosage prend toute eau.** Le goutte-à-goutte n'exige plus d'eau propre (remplace ADR-004 D05) ; comme
  l'arroseur, il arrose avec l'eau du réseau, propre ou non. L'essence reste refusée (« mauvais fluide »).
- **D04 — Lampe de l'arrivée d'eau.** Verte (40-43) : l'eau qui entre est propre (cartouche active, ou source déjà
  propre). Orange (44-47) : l'eau non filtrée est refusée (pas de cartouche, ou cartouche usée), comme aujourd'hui.
- **D05 — Le filtre se voit sur l'arrivée d'eau** (demande de l'utilisateur, 2026-11-18 : « le connecteur de maison
  doit faire apparaître le filtre dans son modèle »). Une cartouche montée ajoute un boîtier de filtre au modèle :
  176-179 (filtre, lampe verte), 180-183 (filtre, lampe orange : cartouche usée, eau non filtrée refusée). Sans
  cartouche : 40-43 / 44-47 comme avant. Le tileset passe à 184 sprites.
- **D06 — L'arrosage ne prend que de l'eau** (demande de l'utilisateur, 2026-11-18 : « uniquement l'eau normale et
  l'eau tainted, refuse tout le reste »). Arroseur et goutte-à-goutte acceptent l'eau propre et l'eau croupie ;
  tout autre fluide (essence, ou ce qu'un baril contient d'autre) est refusé (« mauvais fluide »). Précise D03.
- **D07 — Le réseau transporte de l'eau impure, sauf dans la maison** (demande de l'utilisateur, 2026-11-18 : « il faut
  simplifier : toute eau de mare ou d'un baril dont la fonction est remplir prend de l'eau impure. Donc on a un circuit
  d'eau impure partout dans le circuit, sauf à l'arrivée de la maison »). Un raccord de baril réglé sur « Remplir »
  verse toujours de l'eau impure (croupie), quelle que soit l'eau du réseau ; une fontaine à eau (`WaterDispenser`) ou
  un contenant de l'option `FillContainers` l'accepte (choix « b » de l'utilisateur) : plus aucun contenant n'exige
  d'eau propre. Dans la maison, l'eau propre vient de la cartouche de l'arrivée d'eau (ou d'une source déjà propre :
  puits, eau de la ville). L'essence reste de l'essence.

## Arbitrages rendus

- Q01 — Rendu par l'utilisateur le 2026-11-18 : filtre à l'arrivée d'eau, aucune exigence de filtre pour l'arrosage.
  Écartés : filtre en ligne posé sur un tuyau, goutte-à-goutte qui se bouche.

## Arbitrages ouverts

Aucun.

## Conséquences

- Un baril sans pompe alimente le goutte-à-goutte (ADR-004 D04) sans condition sur la qualité de l'eau.
- Une cartouche ne s'use plus pour l'arrosage : seule l'eau de la maison l'use.
- Mod non publié : une pompe déjà posée avec une cartouche n'est pas reprise.

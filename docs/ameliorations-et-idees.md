# LiveWater — améliorations et idées

Ce document propose ; il n'autorise aucune implémentation sans validation de l'utilisateur.

## Améliorations de code

Aucune pour l'instant.

## Idées de fonctionnalités

| # | Idée | Intérêt pour le joueur | Faisabilité | Effort |
|---|---|---|---|---|
| I01 | Gel des tuyaux et de la pompe en hiver | Saisons qui comptent | point d'extension `available(context)` de `intake` (D16) | M |
| I02 | Surpresseur (`booster`) | Réseaux plus longs | capacité `pump` existante (D14) | S |
| I03 | Tuyaux en cuivre ou en PVC | Variété de matériaux | nouvelle définition de pièce, 16 sprites (D12) | S |
| I04 | Fuites et casse des tuyaux | Entretien du réseau | nouvelle capacité ; hors portée de l'ADR-001 | M |
| I05 | Pompe manuelle à levier sans courant | Début de partie | pièce `intake` + `pump` sans consommation | S |
| I06 | Piscine comme source | Sources en ville | `intake` sur case de piscine (D16) | S |
| I07 | Récupérateur d'eau de pluie sur toit raccordé (retirée : ADR-009 D03) | Eau propre gratuite | ~~D28, baril raccordé~~ | M |
| I08 | Abreuvoir pour animaux alimenté | Élevage B42 | sortie « Remplir » d'un conteneur inscrit (D26) | M |
| I09 | Douche extérieure posable | Hygiène en base | point d'eau posable + arrivée d'eau | S |
| I10 | Reprise de la pompe aux barils de Live Wire | Un seul mod de l'eau | ADR distinct (D21) | L |
| I11 | Point d'eau en plein air : menu « Raccorder » de LiveWater (toit seul : [ADR-024](ADR/termines/024-point-d-eau-sur-un-toit-et-retrait-du-raccord.md) ; le jardin reste une idée) | Évier sur le toit ou dehors | voir l'analyse ci-dessous, piste A | S à M |
| I12 | Colonne montante : un tuyau qui relie deux niveaux | Réseau de tuyaux à l'étage (robinet, arroseur, raccord de remplissage sur un toit) | voir l'analyse ci-dessous, piste C | L |

## Analyse — évier sur un toit en terrasse (2026-11-22)

Constat, confirmé statiquement (lecture du code, rien en jeu) :

- **Le jeu ne propose pas « Raccorder » en plein air.** Le menu vanilla exige que la case soit dans une pièce (pièce
  de la carte, ou pièce fermée et couverte construite par le joueur) : Java 42.22
  `ISWorldObjectContextMenuLogic.java:467-471`, `IsoGridSquare.isInARoom` (`IsoGridSquare.java:8533`). Sur une terrasse,
  l'option n'apparaît jamais, avec ou sans LiveWater. L'action elle-même (`ISPlumbItem.lua`) n'a pas cette condition.
- **Sur le toit d'un bâtiment de la carte, l'arrivée d'eau ne regarde pas.** En mode bâtiment, sa zone ne contient que
  les cases d'une pièce du bâtiment (`BuildingDef.containsXYZ`, `LWT_InletArea.building`) : un toit n'est pas une
  pièce. Un étage ajouté par le joueur au-dessus d'un bâtiment de la carte est exclu pour la même raison.
- **Dans une base construite, la zone couvre déjà la terrasse** (mode base : toute case du cercle, à tous les niveaux
  au-dessus depuis ADR-023) et le réservoir invisible se pose en l'air au-dessus de l'évier (case créée,
  `LWT_GamePlumbing.placeRelay`). Seul le menu « Raccorder » manque.
- Le réservoir se pose un niveau au-dessus : un point d'eau au niveau 31 reste sans eau (limite du moteur).

Pistes :

| Piste | Ce que voit le joueur | Travail | Limites |
|---|---|---|---|
| A — menu « Raccorder » de LiveWater | Clic droit sur l'évier du toit ou du jardin, clé à molette : la même action que dans une pièce, proposée quand une arrivée d'eau couvre la case | entrée de menu côté client (même action vanilla `ISPlumbItem`), zone du mode bâtiment étendue aux cases hors pièce situées au-dessus de l'emprise du bâtiment, contrôle côté autorité ; ADR à écrire | l'emprise d'un bâtiment est un rectangle : à décider, toit seul ou aussi le jardin dans la portée |
| B — rien à coder | Le joueur construit une pièce fermée et couverte autour de l'évier | aucun | ne vaut que dans une base construite ; sur le toit d'un bâtiment de la carte, il faut en plus une seconde arrivée d'eau posée sur ce toit, avec son baril et sa pompe au même niveau |
| C — colonne montante (I12) | Un tuyau vertical : le réseau monte, on pose robinet, arroseur ou raccord de remplissage sur le toit | le graphe ne relie que des voisins du même niveau (`LWT_Network`) : nouvelle capacité, tuiles, règles de pose, vue du réseau | ne donne pas l'eau à un évier vanilla en plein air sans la piste A |

Recommandation : piste A, qui règle le cas demandé avec le geste que le joueur connaît déjà. La piste C répond à une
autre envie (un vrai réseau à l'étage) et se décide à part.

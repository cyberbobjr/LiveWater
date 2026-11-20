# ADR-020 — Tuyaux enterrés : une tuile de terre tout juste visible

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-020-TUYAUX-ENTERRES` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Proposé |
| Avancement | voir le [plan 020](../ADR-plans/plan-020-tuyaux-enterres.md) |
| Décideur | l'utilisateur (« oui ok pour les 2 ADR », « un petit overlay tout juste visible […] une tuile dédiée à l'enterrement », 2026-11-20) |
| Portée | `batman_LiveWater` : état « enterré » du tuyau (pièce `LiveWater:PipeGalvanized`), choix de l'image (`LWT_Sprites`), champ d'API `buried` (révision 25), action Enterrer / Déterrer (menu, action chronométrée, commande vers l'autorité), 16 tuiles neuves (recette Blender, tiledef, pack), ramassage et démontage, vue du réseau, traductions, tests, wiki, CHANGELOG ; sous-mod Viewpoint (aucune liaison pour ces tuiles) |
| Documents liés | [ADR-001](termines/001-reseau-eau-ouvert.md) (D11, D12 : l'image suit les liaisons), [ADR-002](termines/002-tuyaux-et-barrieres.md) (D03 manchons de clôture), [ADR-007](termines/007-demontage-et-butin.md), [ADR-016](termines/016-retrait-debug-ou-admin.md), [ADR-019](termines/019-modeles-3d-viewpoint.md), [contrat des tuiles](../annexes/conception/tuiles-contrat.md) |
| Références | `LWT_PartPipe.lua` (images 0-15 par masque, manchons 104-123) ; `LWT_Sprites.lua` (`refresh`, `crossing`) ; vanilla `ISFarmingMenu.canDigHereSquare` (`ISFarmingMenu.lua:514-534` : tombe, plante, étage, `ISShovelGroundCursor.GetDirtGravelSand`) |
| Origine | suggestion d'un joueur sur la page Workshop (2026-11-20) : pouvoir enterrer les tuyaux pour ne pas avoir de tuyaux visibles partout |

## Contexte

Un tuyau LiveWater est un objet posé au sol. Son image suit les côtés qu'il relie (16 masques) et prend un manchon
quand il passe sous une clôture. Un grand réseau d'arrosage couvre donc le terrain de tuyaux bien visibles. Le joueur
veut pouvoir les cacher sans perdre son réseau.

## Décisions

- **D01 — Un état, pas une nouvelle pièce.** Un tuyau enterré reste la même pièce, au même endroit, avec les mêmes
  liaisons, le même débit et la même vie loin du joueur. Seul un état `buried` (sauvegardé avec la pièce, recopié sur
  l'objet du jeu comme le reste de son état) change son image et ce qu'on peut en faire.
- **D02 — Une tuile dédiée, tout juste visible.** Seize tuiles neuves, une par masque de côtés reliés : une fine trace
  de terre remuée qui suit le tracé du tuyau, à peine plus sombre que le sol, avec quelques mottes. On devine le
  réseau en regardant bien ; on ne le voit pas en passant. Intensité retenue par l'utilisateur le 2026-11-20 sur
  planche d'essai : la plus discrète des trois (« A ») — bande de terre (74, 56, 38) d'environ 0,11 case de large,
  opacité 0,30, bords adoucis et ondulés (ondulation périodique d'une case : pas de raccord visible d'une case à
  l'autre), une motte par branche ; tuile dessinée en 2D semi-transparente, pas un rendu Blender, pour se fondre dans
  tout sol. Index neufs pris après le dernier utilisé (256-271 dans
  `batman_livewater_01`, à confirmer au contrat des tuiles), jamais un index déjà publié. Sous une clôture, la même
  tuile (pas de manchon : le tuyau passe dessous).
- **D03 — Le geste : une pelle.** Clic droit sur un tuyau, « Enterrer le tuyau » ; sur un tuyau enterré, « Déterrer le
  tuyau ». Les deux demandent un outil qui creuse au sens du jeu de base (pelle, bêche ou truelle) et une action
  chronométrée avec l'animation de creuser. Ni niveau ni expérience. L'action se décide sur l'autorité (solo ou
  serveur) par une commande, qui revérifie les conditions de D04.
- **D04 — Seulement en pleine terre.** Enterrer n'est possible que là où le jeu laisse creuser : rez-de-chaussée (ou
  étage si l'option de partie du jeu le permet), sol de terre, de gravier ou de sable
  (`ISShovelGroundCursor.GetDirtGravelSand` non vide), pas de tombe. Sur l'asphalte, un plancher, du carrelage ou dans
  une maison, l'option est grisée avec la raison. Déterrer est toujours possible.
- **D05 — Seuls les tuyaux s'enterrent.** Vannes, compteur, arroseurs, raccords, arrivée d'eau et pompe restent
  visibles. Une pièce d'un autre mod peut s'enterrer si elle le déclare : champ `buried` de `registerPart` (images par
  masque), révision d'API 25, additive. Aucun `if` sur le type de pièce.
- **D06 — Enterré veut dire hors d'atteinte.** Un tuyau enterré ne se ramasse pas et ne se démonte pas : il faut le
  déterrer d'abord (la tuile enterrée n'a pas les propriétés de meuble du jeu). Le retrait de LiveWater de ce monde
  (ADR-016) retire aussi les tuyaux enterrés.
- **D07 — Le réseau se retrouve.** La vue « Afficher le réseau d'eau » montre les tuyaux enterrés comme les autres.
  Leur menu donne « Information » et « Déterrer le tuyau ». Quand un voisin s'ajoute ou part, le tuyau enterré prend la
  tuile enterrée de son nouveau masque.
- **D08 — Rien d'autre ne change.** Débits, liaisons, passages sous les clôtures, règles de pose des autres pièces et
  potager restent tels quels : un tuyau enterré ne gêne ni plus ni moins qu'un tuyau visible (vérifié à l'étape 1 du
  plan, sans changement voulu).
- **D09 — Viewpoint.** Les tuiles enterrées n'ont pas de modèle 3D : Viewpoint les dessine à plat, comme le sol.

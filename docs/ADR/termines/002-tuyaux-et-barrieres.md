# ADR-002 — Tuyaux et barrières : passer sous les clôtures, jamais à travers un mur plein

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-002-TUYAUX-ET-BARRIERES` |
| Date de création et de mise à jour | 2026-11-18 |
| Statut | Accepté (2026-11-18) |
| Avancement | Terminé le 2026-11-18 ; voir le [plan 002](../../ADR-plans/termines/plan-002-tuyaux-et-barrieres.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : graphe du réseau (`LWT_Network`), sprites (`LWT_Sprites`), adaptateur monde (`LWT_GameWorld`), pose (`LWT_Placement`), tuiles des tuyaux ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D10, D12, D14, Q01 mis à jour le 2026-11-18), [contrat des tuiles](../../annexes/conception/tuiles-contrat.md) |
| Références | Java 42.22 `IsoGridSquare.hasNonHoppableWall` (`IsoGridSquare.java:3878-3891`), `getHoppableWall` (`:3840-3852`), `isHoppableTo` (`:1040-1049`) ; base de connaissances `pathfinding-and-obstacles.md` (« Classer le bord commun de deux cases »), `map-files.md:61` (une case ne porte que ses bords N et W) |
| Origine | question de l'utilisateur du 2026-11-18 (« comment on pourrait gérer les barrières avec le tuyau ? »), pistes 1, 2 et 4 retenues : « 1,2 et 4 (interdiction de traverser les murs pleins) » |

## Contexte

Le graphe d'ADR-001 (D10) relie deux pièces voisines orthogonales dès que chacune offre le côté qui fait face à
l'autre, sans regarder le bord commun des deux cases. Un tuyau traverse donc une clôture, mais aussi un mur de maison.
Une case ne porte que ses bords nord et ouest ; le bord sud ou est d'une case est le bord nord ou ouest de sa voisine.

## Décisions

- **D01 — Un mur plein coupe le raccord.** Deux pièces voisines ne se raccordent pas quand leur bord commun porte un
  mur plein : un objet du bord qui est un mur (`WallN/W`, `WallNTrans/WTrans`, coupe `cutN/W`, cadre de porte ou de
  fenêtre, fenêtre) **et** n'est pas une clôture (ni `HoppableN/W`, ni `TallHoppableN/W`). C'est la règle du moteur
  `IsoGridSquare.hasNonHoppableWall(nord)`, lue sur la case qui porte le bord. Une porte dans un mur est un mur plein.
  L'arrivée d'eau de la maison reste la seule pièce qui fait entrer l'eau dans un bâtiment (ADR-001 D18).
- **D02 — Une clôture laisse passer le tuyau.** Clôtures basses (`HoppableN/W`), clôtures hautes et palissades
  (`TallHoppableN/W`), portails et bords sans objet ne coupent rien : le tuyau passe dessous.
- **D03 — Manchon dessiné automatiquement.** Un tuyau raccordé par son côté nord ou ouest à travers une clôture portée
  par sa propre case est dessiné avec un manchon sur ce bord. Une case ne porte que ses bords N et W, donc chaque
  clôture traversée est dessinée par une seule case. Variantes : manchon nord pour les 8 masques qui contiennent N,
  manchon ouest pour les 8 masques qui contiennent W, les deux pour les 4 masques qui contiennent N et W : 20 sprites,
  index 104 à 123 du tileset `batman_livewater_01`. **Un seul manchon pour toutes les clôtures** (demande de l'utilisateur,
  2026-11-18 : « ne fais pas un manchon pour chaque type de clôture ») : un collier sombre au bord de la case, le même
  quels que soient la clôture, sa hauteur ou son matériau. Les autres pièces (vanne, compteur…) gardent leur image.
- **D04 — Le domaine reste pur.** Le graphe et les sprites ne connaissent pas le jeu : un port `edges` injecté répond
  `blocks(x, y, z, side)` (mur plein, D01) et `fenced(x, y, z)` (masque des bords N et W de la case qui portent une
  clôture, D03). Sans port (tests, autre mod), rien ne coupe et rien n'est dessiné. La définition d'une pièce déclare
  ses images de manchon dans un champ facultatif `crossings = { [masque] = { [bords] = sprite } }` (révision d'API
  additive) ; une pièce sans ce champ garde l'image de son masque.
- **D05 — Mur ou clôture posé ou retiré plus tard.** Quand un objet de bord (mur, clôture) apparaît ou part sur une
  case, l'autorité réévalue les raccords des pièces de cette case et de ses voisines nord et ouest (scission ou fusion
  des réseaux, sprites recalculés), comme pour une pièce posée ou retirée.

## Arbitrages rendus

- Q01 — Pistes retenues par l'utilisateur le 2026-11-18 : passer sous les clôtures (1), manchon automatique (2),
  interdiction de traverser les murs pleins (4). Écartées : pièce « traversée de clôture » à fabriquer (3).

## Arbitrages ouverts

Aucun.

## Conséquences

- Un tuyau posé contre un mur reste un bout de ligne : sa forme le montre, sans message.
- Les réseaux déjà posés à travers un mur se coupent au chargement du monde (reconstruction du graphe) : mod non
  publié, rien à reprendre.
- 20 tuiles de plus à rendre, avec leur carte de profondeur.

## Hors portée

- Tuyaux à travers un plancher ou un plafond (ADR-001 Q06).

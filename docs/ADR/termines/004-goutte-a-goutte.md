# ADR-004 — Arrosage au sol : la ligne de goutte-à-goutte

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-004-GOUTTE-A-GOUTTE` |
| Date de création et de mise à jour | 2026-11-18 |
| Statut | Accepté (2026-11-18) |
| Avancement | Terminé le 2026-11-18 ; voir le [plan 004](../../ADR-plans/termines/plan-004-goutte-a-goutte.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : nouvelle pièce, capacité de sortie au sol, flux (pression, pertes), raccord de baril (gravité), bruit de l'arroseur, tuiles, recette, traductions ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D12, D14, D15, D17, D19, D26), [ADR-002](002-tuyaux-et-barrieres.md), [ADR-003](003-zone-arrosee-lisible.md) |
| Références | `LWT_Flow.lua` (service des sorties, pression), `LWT_Plants.lua` (doses), `LWT_CapSpray.lua` (son de l'arroseur), base de connaissances `food-production.md` |
| Origine | demande de l'utilisateur du 2026-11-18 : « un système d'irrigation "au sol" à la différence des sprinkler qui sont aériens » ; choix : arrosage des cases de chaque côté du tuyau (« b »), et les quatre différences proposées (économe en eau, peu de pression, filtre obligatoire, silence / bruit) |

## Décisions

- **D01 — Une ligne de goutte-à-goutte.** Pièce `LiveWater:DripLine`, objet posable `Base.Mov_LiveWater_DripLine`, posée
  et ramassée comme un tuyau (curseur vanilla, une par case), 16 formes qui suivent les voisins (ADR-001 D12). Elle se
  raccorde aux tuyaux et aux autres lignes ; l'eau la traverse (`conduit`). Pas de manchon de clôture (ADR-002 D03).
- **D02 — Cases arrosées.** Chaque case de la ligne arrose les cases voisines (N, E, S, W) qui ne lui sont **pas**
  raccordées : une ligne droite arrose les deux cases de chaque côté, posée entre deux rangs. La case du tuyau elle-même
  n'est pas arrosée. Mêmes doses que l'arroseur (200 ml).
- **D03 — Économe en eau.** Toute l'eau de la ligne va aux plantes. L'arroseur en perd une partie : il prélève
  **1,25 fois** l'eau qu'il donne aux plantes (réglage `loss` de `spray`, 0,25 par défaut).
- **D04 — Peu de pression.** Toutes les lignes raccordées d'un même réseau ne coûtent ensemble que **1** de pression
  (l'arroseur coûte 1 chacun, l'arrivée d'eau 2). Un baril relié par un raccord réglé sur « Pomper », **sans pompe**,
  donne une pression de gravité de 1 qui ne sert qu'aux lignes de goutte-à-goutte : un arroseur ou une maison ne
  reçoivent rien de cette seule pression.
- **D05 — Filtre obligatoire.** *Remplacée le 2026-11-18 par ADR-005 D03 : l'arrosage prend toute eau.* La ligne n'accepte que l'eau propre (comme l'arrivée d'eau) : sans filtre en amont, elle
  reste à sec avec l'état « eau non filtrée ».
- **D06 — Silence et bruit.** La ligne ne fait aucun bruit. L'arroseur qui arrose fait un bruit que les zombies
  entendent, une fois par pas de dix minutes (rayon 10, volume 10 par défaut, réglages `noiseRadius`, `noiseVolume` de
  `spray`), en plus de son bruit d'ambiance pour les joueurs.
- **D07 — Recette propre** (demande de l'utilisateur, 2026-11-18 : « tuyau en caoutchouc avec du scotch (duct tape)
  pour faire X rouleaux »). 1 `Base.RubberHose`, 2 utilisations de `Base.DuctTape` et un couteau gardé
  (`tags[base:sharpknife]`, on perce le tuyau) donnent **4** lignes de goutte-à-goutte, une par case. Aucune
  section de tuyau métallique n'y entre.

## Arbitrages rendus

- Q01 — Cases arrosées : « b », les cases de chaque côté de la ligne (l'utilisateur, 2026-11-18 : « le tuyau sera au
  milieu d'une tuile de sol, donc forcément ça sera les tuiles de chaque côté »).
- Q02 — Différences gardées : économe en eau, peu de pression, filtre obligatoire, silence / bruit.

## Arbitrages ouverts

Aucun.

## Conséquences

- L'arroseur coûte plus d'eau et devient audible par les zombies : changement visible des parties en cours (mod non
  publié).
- Une seule pression de gravité ne sert qu'au goutte-à-goutte : le flux distingue cette pression de celle des pompes.

## Hors portée

- Minuterie propre à la ligne (une vanne en amont la commande) ; nettoyage d'une ligne bouchée.

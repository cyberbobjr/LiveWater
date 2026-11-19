# ADR-006 — Vision débit : une sortie d'arrosage ouverte consomme son débit

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-006-VISION-DEBIT` |
| Date de création et de mise à jour | 2026-11-18 |
| Statut | Accepté (2026-11-18) |
| Avancement | Terminé le 2026-11-19 ; voir le [plan 006](../../ADR-plans/termines/plan-006-vision-debit.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : horloge (réseaux hors chargement), courant (`LWT_Power`), raccords de baril, capacités `spray`, `drip`, `controller` (minuterie), service des plantes (`LWT_Plants`), options sandbox, raccords d'une pièce dont les ports sont pleins (`LWT_Topology`), tests, documentation ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D09, D14, D19), [ADR-002](002-tuyaux-et-barrieres.md) (D05), [ADR-003](003-zone-arrosee-lisible.md), [ADR-004](004-goutte-a-goutte.md) (D02-D04), [ADR-005](005-filtre-a-l-arrivee-d-eau.md) |
| Références | campagne de cas combinés (tests/test_combo_*.py, 2026-11-18) : trois cas mis de côté en attente de décision |
| Origine | réponses de l'utilisateur du 2026-11-18 aux trois questions de la campagne « joueurs tordus » |

## Contexte

Jusqu'ici une sortie d'arrosage ne prélève que l'eau dont ses plantes ont soif (ADR-001 D09 : « pas de besoin → au
repos »). Une plante couverte par deux sorties fait prélever deux fois son besoin, et la seconde eau est perdue sans
logique de débit. Deux autres cas restaient ouverts : une ligne de goutte-à-goutte au bout d'un circuit à court de
pression, et une vanne déjà pleine qu'un mur démoli met au contact d'un troisième tuyau.

## Décisions

- **D01 — Une sortie d'arrosage ouverte consomme son débit** (l'utilisateur : « pour moi les deux sont gaspillés du
  montant de leur débit respectif, il faut une vision débit d'eau »). À chaque pas de dix minutes, un arroseur ouvert
  prélève son débit, que les plantes aient soif ou non, tant que le réseau a de l'eau et de la pression ; une ligne de
  goutte-à-goutte prélève son débit par case. Les plantes de la zone prennent ce qu'il leur faut dans cette eau (doses
  de 200 ml, plus proches d'abord) ; le reste est perdu. Deux sorties qui couvrent la même plante prélèvent chacune leur
  débit. Remplace, pour l'arrosage, la règle « pas de besoin → au repos » d'ADR-001 D09 ; l'arrivée d'eau et le
  remplissage des barils gardent le besoin (place libre).
- **D02 — Débits réglables** (l'utilisateur : « la quantité doit être définie dans les options sandbox, arroseur 10 L
  et goutte 0,5 L »). Options sandbox `LiveWater.SprinklerFlow` (litres par pas de dix minutes, 10 par défaut) et
  `LiveWater.DripFlow` (litres par case de ligne et par pas, 0,5 par défaut). L'arroseur perd toujours un quart de son
  eau dans l'air (ADR-004 D03) : sur 10 L, 7,5 L peuvent aller aux plantes ; la ligne ne perd rien.
- **D03 — Quand une sortie coule.** Arroseur manuel : tant que sa vanne est ouverte. Arroseur automatique : sa
  minuterie l'ouvre 30 minutes (3 pas) toutes les N heures (réglage existant `every`), avec du courant. Ligne de
  goutte-à-goutte : dès que le réseau lui donne eau et pression ; une vanne en amont la commande.
- **D04 — Bout de circuit sans pression** (l'utilisateur : « si c'est en bout de circuit la pression est tombée, donc
  ça devrait être sec »). La règle d'ADR-001 D14 s'applique aussi au goutte-à-goutte : une ligne servie après une
  sortie à court de pression reste à sec, même si une autre ligne a déjà payé le coût commun.
- **D05 — Ports pleins après un mur démoli.** Quand un mur disparaît entre deux pièces dont l'une a déjà tous ses
  ports pris, le nouveau raccord n'est pas fait : la pièce posée en dernier reste à part, comme une pose refusée, et le
  reste après une sauvegarde (même résultat qu'à la reconstruction du réseau).

- **D06 — Les réseaux tournent hors chargement** (l'utilisateur a accepté, 2026-11-18). À chaque pas de dix minutes,
  l'autorité fait tourner tous les réseaux, chargés ou non, sur le registre (les modules purs ne lisent jamais le
  monde). Hors chargement : une mare ou un puits donne de l'eau (source notée à la pose) ; un baril donne ce que son
  raccord a lu au dernier passage, décompté à chaque pas, et le contenant réel reçoit ce compte au chargement de son
  chunk ; les plantes sont arrosées par leur objet global vanilla (`SFarmingSystem`, comme `checkPlant` le fait
  hors chargement) ; les réservoirs invisibles de la maison attendent le retour du joueur ; images, jet et son
  reprennent l'état enregistré au retour. Le multijoueur suit la même règle (tout se passe sur le serveur).
- **D07 — Courant hors chargement.** Avec LiveWire (révision d'API suffisante), le courant d'une pièce déchargée est
  celui du réseau LiveWire qui alimente sa case (`gridAt(x, y, z)`, onduleur en marche), coupure par circuit ou
  disjoncteur au dernier état connu ; LiveWire facture lui-même sa demande hors chargement. Courant de la ville : état
  global du monde (coupure au jour prévu). Générateur vanilla (l'utilisateur, 2026-11-18 : « continuer à alimenter
  les plantes et que l'eau soit quand même déversée me semble être la solution la moins punitive ») : la pièce garde
  l'état de courant de son dernier pas chargé ; le générateur ne brûle rien pendant l'absence (le jeu ne le fait pas
  tourner) et reprend sa consommation au retour.
- **D08 — Au retour.** Dès le premier pas chargé, la règle normale reprend (courant lu sur l'objet, contenu réel des
  barils, réservoirs de la maison).

- **D09 — Le joueur voit le débit** (l'utilisateur, 2026-11-18 : « il faut absolument donner l'information du débit
  d'arrosage au joueur »). L'« Information » d'un arroseur dit « Débit : 10 L toutes les 10 min, dont 7,5 L pour les
  plantes » ; celle d'une ligne de goutte-à-goutte « Débit : 0,5 L toutes les 10 min par case de ligne » ; valeurs des
  options sandbox ou du réglage `flow` de la pièce. Le crochet `lines` reçoit le contexte des réglages (révision 16,
  additif).

## Arbitrages rendus

- Q01 — Bout de circuit : à sec (D04). Q02 — Plante couverte deux fois : vision débit (D01-D02). Q03 — Vanne pleine :
  le troisième tuyau reste à part (D05). L'utilisateur, 2026-11-18.

## Arbitrages ouverts

Aucun.

## Conséquences

- Un arroseur manuel oublié ouvert vide un baril ou use la pompe : à l'utilisateur de le fermer, ou d'utiliser
  l'arroseur automatique.
- Une pompe de 50 L par pas alimente au plus cinq arroseurs à plein débit ; les suivants reçoivent le reste, puis rien.

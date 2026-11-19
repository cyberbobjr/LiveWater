# LiveWater — architecture

Décisions de référence : [ADR-001](ADR/termines/001-reseau-eau-ouvert.md) ; débit des sorties d'arrosage :
[ADR-006](ADR/termines/006-vision-debit.md). Ce document décrit l'état réel du code ; il suit
le [plan 001](ADR-plans/termines/plan-001-reseau-eau-ouvert.md) étape par étape.

## Vue d'ensemble

Architecture hexagonale légère (D22) : un domaine pur (graphe du réseau, pression, distribution, qualité) sans API du
jeu, testé hors jeu ; des adaptateurs PZ autour (pose, horloge, réservoirs, plantes, sprites, Live Wire).

## Arborescence du mod

`Contents/mods/batman_LiveWater/` : `common/` (vide) et `42.21/` (`mod.info`, `media/`). `mod.info` : `id=batman_LiveWater`,
sans `require=` (Live Wire facultatif, D20), `incompatible=\LGExtendedPlumbing,\LGMainsWater` (Q09).

## Modules Lua

`shared/LiveWater/` :
- `LWT_API.lua` : façade publique `LiveWater.API` et racine de composition : crée le registre des capacités (y
  inscrit les capacités de départ listées en données), le registre des pièces, le bus `LiveWater.Events`, et scelle
  les registres à `OnInitGlobalModData`. `LiveWater.Parts` et `LiveWater.Capabilities` sont internes.
- `LWT_Capabilities.lua` : registre des capacités (pattern strategy : chaque capacité est une table de crochets copiée
  par liste blanche).
- `Capabilities/LWT_Cap<Nom>.lua` : un fichier par capacité (`conduit`, `intake`, `pump`, `valve`, `filter`,
  `outlet`, `controller`, `meter`, `spray`, `fitting`, `drip`), réglages et valeurs par défaut de la capacité.
- `Parts/LWT_Part<Nom>.lua` : un fichier par pièce de LiveWater, inscrite par l'API publique comme celle d'un autre
  mod (`LWT_PartPipe.lua` : `LiveWater:PipeGalvanized` ; `LWT_PartPondPump.lua` : `LiveWater:PondPump` ; `LWT_PartFlowMeter.lua` :
  `LiveWater:FlowMeter` ; `LWT_PartHouseInlet.lua` : `LiveWater:HouseInlet` ; `LWT_PartSprinkler.lua` : `LiveWater:Sprinkler` ; `LWT_PartSprinklerAuto.lua` : `LiveWater:SprinklerAuto` ; `LWT_PartBarrelFitting.lua` : `LiveWater:BarrelFitting` ; `LWT_PartValve.lua` : `LiveWater:Valve` ; `LWT_PartDripLine.lua` : `LiveWater:DripLine`, ADR-004).
  `LWT_Containers.lua` (pur) : registre des conteneurs d'un raccord de baril (forme, par sprite ou entité ; tout
  conteneur reçoit l'eau croupie comme un baril, ADR-005 D07 ; conteneurs admis : 20 L ou plus, inscrits, ou listés dans l'option `FillContainers`). `LWT_Tiles.lua` : noms des sprites du
  tileset et `variants` d'une pièce dessinée par état et orientation.
- `LWT_InletArea.lua` (pur) : cases servies par une arrivée d'eau (bâtiment de la carte touché, cercle de portée,
  jusqu'à 3 étages au-dessus, sous-sols jusqu'à 2 niveaux sous l'emprise du rez-de-chaussée ; hors bâtiment de la carte,
  base du joueur : cercle de portée), lues par une sonde injectée ; `LWT_RelayPlan.lua` (pur) : relais voulus au-dessus des
  points d'eau (partage 3 × 3, sources d'autrui laissées).
- `LWT_Sources.lua` (pur) : registre des sortes de source d'eau (données : qualité, drapeau d'une case voisine ou
  sprites d'un objet voisin) ; `Sources/LWT_Source<Nom>.lua` : une sorte par fichier (`water` : eau naturelle,
  croupie ; `well` : puits vanilla, propre) ; un autre mod en ajoute par `LiveWater.API.registerSource`. La capacité
  `intake` relève la sorte trouvée à la pose et donne la qualité de cette sorte (`ctx.sources` du pas).
- `LWT_Settings.lua` (pur) : options sandbox lues dans le contexte d'un pas (`ctx.scale`) : multiplicateurs
  (`scale`) et valeurs (`value`, débits `SprinklerFlow` et `DripFlow`, ADR-006 D02).
- Adaptateurs partagés (client et autorité) : `LWT_GameSite.lua` (les 8 cases voisines d'une place : drapeau, sprite,
  source trouvée), `LWT_PlaceRules.lua` (règles de pose au curseur de meuble vanilla : enveloppe
  `canPlaceMoveableInternal` et le panneau d'information, refus seulement pour nos tuiles), `LWT_Mirror.lua` (état
  d'une pièce recopié dans `movableData` de son objet), `LWT_Reasons.lua` (raison de refus → clé de traduction).
- `LWT_WaterObjects.lua` (adaptateur partagé) : règles des objets d'eau (point d'eau, réservoir utilisable, marque
  `LiveWaterRelay`, marques d'autres mods jamais touchées, eau de la ville).
- `LWT_CityWater.lua` (pur) : règle du raccord d'un point d'eau posé au réseau public (menu et commande).
- `LWT_Diagnosis.lua` (pur) : raison du manque d'eau d'une arrivée d'eau et ligne d'un point d'eau sans eau.
- `LWT_Protocol.lua` : noms du module et des commandes réseau partagés par client et serveur ; `LWT_Notice.lua` : note
  traduite au-dessus du joueur (refus d'une commande).
- `LWT_Parts.lua` : registre des types de pièce, copie par liste blanche, unicité des sprites (formes et
  `variants`) ; requêtes du catalogue : `look` (variante d'après les jetons des capacités), `attach` (la place
  convient-elle ?), `lines` (lignes d'information), `hasHook`, `spritesOf`.
- `LWT_Events.lua` : bus d'événements public (D06).
- `LWT_Check.lua` : contrôles de valeurs et copie de champs par règles ; `LWT_Grid.lua` : côtés, masque de 4 bits,
  clé de case `"x,y,z"`, `edgeOf` (case qui porte le bord d'un côté : une case ne porte que ses bords N et O, ADR-002).
- `LWT_Network.lua` (domaine pur) : graphe d'une case par pièce, liens entre voisins qui s'offrent le côté commun,
  ports, fusion et scission des réseaux, masque et sprite, eau partie des pièces qui mettent sous pression (distance
  en tuyau, ordre de service : distance puis ordre de pose ; zone de chaque nœud : départs d'eau qui se rejoignent par
  des pièces ouvertes, une vanne fermée entre deux pompes en fait deux zones). Le registre des pièces lui est injecté comme catalogue ;
  il interroge des crochets (`carries`, `pressurizes`, `ports`, fermeture par `Parts:closed` : `blocks` sans `opens`)
  et ne nomme aucune capacité. Un côté noté dans `cuts` de la pièce (mur plein, ADR-002) ne se raccorde pas ; le graphe
  ne lit que cette note, jamais le monde. Un côté noté dans `apart` (ADR-006 D05 : lien apparu à la disparition d'un
  mur alors qu'un port était plein, la pièce posée en dernier perd) ne se raccorde pas non plus ; `relink(x, y, z,
  before)` reçoit les masques d'avant (`masksAround`) et pose cette note, `remove` l'efface chez les voisines.
- `LWT_Flow.lua` (domaine pur) : un pas de dix minutes d'un réseau, zone par zone (`Network:reach`) : pression et débit additionnés des pompes,
  qualité, sorties servies dans l'ordre de service selon leur besoin, réserve de pression, filtre sur le chemin et
  son usure ; litres et qualité de l'eau servie portés sur chaque pièce de son chemin (`through`, `qualityAt` ; part
  de chaque pompe). Crochets `supply`, `source`, `outlet`, `purifies`, `wear` ; le besoin vient des adaptateurs.
  Révision 11 : pièces qui puisent (`draw`, raccord en « Pomper ») à la place des prises des pompes, un fluide par
  réseau (eau ou essence), sortie qui refuse ce fluide (`wrong_fluid`), litres puisés (`drawn`). ADR-005 : famille
  `other` pour toute qualité qui n'est ni eau (`clean`, `tainted`) ni essence, jamais vue comme de l'eau ; le filtre
  porté par la sortie elle-même (arrivée d'eau) compte, puisque la recherche du filtre part de la sortie incluse.
  Révision 15 (ADR-004) : sorties d'un même groupe de coût (`costGroup`, goutte-à-goutte) qui paient leur pression une
  fois par pas ; réseau sans pompe : les pièces qui donnent une pression de gravité (`gravity`, raccord en « Pomper »)
  sont le départ de l'eau (`Network:reach(id, "gravity")`), seules les sorties qui marchent par gravité (`byGravity`) la
  prennent.
- `LWT_SprayArea.lua` (pur, ADR-003 D01) : cases arrosées par un arroseur (carré de `radius` cases sur chaque axe,
  rayon 2 → 5 × 5) ; `squares` est partagé par l'autorité et le client (surlignage), `reach` est la stratégie de zone
  de `LWT_Plants` pour l'arroseur (rayon mis à l'échelle, dose, part perdue en l'air, débit).
- `LWT_DripArea.lua` (pur) : cases arrosées par une ligne de goutte-à-goutte (voisines N, E, S, O non raccordées) et
  stratégie de zone de `LWT_Plants` pour la ligne (masque des liens lu dans le graphe, aucune perte, débit par case).

`server/LiveWater/` (chaque fichier commence par `if isClient() then return end`) :
- `LWT_Server.lua` : racine de composition sur l'autorité. À `OnInitGlobalModData`, construit les services avec leurs
  adaptateurs sur `ModData.getOrCreate("LiveWater")` (relue à chaque partie) et reconstruit le graphe ; seul fichier
  abonné aux événements du jeu (`OnObjectAdded`, `OnObjectAboutToBeRemoved`, `OnClientCommand`, `EveryTenMinutes`).
  `LiveWater.Server` expose les services de la partie en cours (`registry`, `network`, `topology`, `commands`,
  `placement`, `clock`) aux adaptateurs des étapes suivantes.
- `LWT_Registry.lua` : registre persistant des pièces posées, sur un magasin injecté (la ModData globale en jeu).
- `LWT_Topology.lua` (service d'application) : registre et graphe changés ensemble, sprites recalculés, événements
  `partAdded`, `partRemoved`, `networkChanged` ; `canAdd` sans effet pour les contrôles des commandes. Murs et clôtures
  (ADR-002) : `cutsAt`, `recordCuts` (note `cuts` à la pose), `relink` (la case d'un objet de bord et ses voisines
  nord et ouest jugées à nouveau), `refreshCuts` (tâche d'horloge `edgeWatch`, le jeu n'annonçant pas un mur ou une
  clôture construits en solo).
- `LWT_Placement.lua` : une tuile apparue ou retirée est une pièce si son sprite appartient à un type inscrit
  (`Parts:typeOfSprite`) ; idempotent ; `edgeChanged` : un mur ou une clôture apparu ou sur le point de partir relie à
  nouveau les pièces autour (`Topology:relink`).
- `LWT_Sprites.lua` : la pièce et ses quatre voisins prennent le sprite de leur masque, appliqué seulement s'il change ;
  un type sans sprite pour ce masque garde celui de sa pose (orientation d'un meuble) ; un type dessiné par état
  qui donne une orientation pour ce masque (`facings`, vanne d'arrêt) prend la variante de son état tournée selon
  son tuyau. `crossed` : une forme raccordée à travers une clôture portée par son bord N ou O prend son image à manchon
  (`Parts:crossing`), d'après le port monde `edge`.
- `LWT_Commands.lua` : répartiteur, table de gestionnaires par nom (un fichier par commande sous `Commands/`, plus
  `LWT_CmdChecks.lua` pour les contrôles d'arguments et de portée, `LWT_CmdCartridge.lua` pour ce que partagent les
commandes du filtre) ; un refus est dit au joueur par clé de traduction.
- `LWT_Clock.lua` : tâches injectées (`chores`, travail borné du même pas), puis pas de dix minutes de chaque réseau
  qui a un départ d'eau (une pièce sous pression, sinon une pièce qui donne une pression de gravité), chargé ou non
  (ADR-006 D06 : coût, une distribution par réseau toutes les dix minutes de jeu, bornée par le registre ; ce qu'une
  pièce peut faire hors chargement est décidé par les ports et adaptateurs, jamais par l'horloge) :
  courant de chaque pièce qui en a besoin (port `power`, crochet `powered`), préparation (`prepare` : une minuterie
  d'arroseur tient sa vanne ouverte `duration` pas, 30 minutes, ADR-006 D03, `ctx.hours`), distribution, crochet `stepped` de chaque
  membre (litres passés), présentation (port `publisher`), `waterDelivered` pour chaque sortie servie ; besoin des
  sorties injecté (0 par défaut), multiplicateurs sandbox par `scale`. `settle(id)` (sur `networkChanged`) : un
  réseau resté sans départ d'eau reçoit un bilan vide une fois (aucune sortie ne reste servie).
- `LWT_Outlets.lua` : où va l'eau d'une sortie, par type de sortie (gestionnaire : `need`, `deliver`, `release`) ;
  besoin injecté dans l'horloge, `waterDelivered` et `partRemoved` relayés par la racine de composition.
- `LWT_Relays.lua` : réservoirs relais des arrivées d'eau (gestionnaire `houseInlet` et tâche de l'horloge) : pose,
  retrait, besoin, remplissage, relais en attente d'une case chargée (`orphans`) ; `LWT_GamePlumbing.lua` : adaptateur
  du jeu (bâtiment, points d'eau, objets relais).
- `LWT_Plants.lua` : plantes d'un arroseur ou d'une ligne de goutte-à-goutte (gestionnaires `sprinkler` et `drip`, une
  instance par type avec sa stratégie de zone injectée : besoin = débit de la sortie, que les plantes aient soif ou non,
  ADR-006 D01 ; l'eau reçue moins la part perdue en l'air donne des doses entières aux plantes qui ont besoin d'eau, les
  plus proches d'abord, le reste est perdu) ; `LWT_GameFarming.lua` : adaptateur de l'agriculture vanilla
  (`SFarmingSystem.instance:getLuaObjectAt`, `SPlantGlobalObject:water`).
- `LWT_Fittings.lua` : raccords de baril (tâche de l'horloge : conteneur relevé et présenté ; gestionnaire
  `barrelFill` ; litres puisés retirés sur `waterDrawn`, conteneurs relevés à nouveau ; deux raccords d'un même baril
  se partagent son contenu en « Pomper » et sa place libre en « Remplir » ; hors chargement, décompte dans l'état
  relevé, écrit une fois dans le vrai conteneur au `LoadChunk` ou au premier pas chargé, ADR-006 D06) ; `LWT_GameContainers.lua` : adaptateur (baril,
  récupérateur, pompe à essence d'une station).
- `LWT_Removal.lua` : retrait de LiveWater d'un monde (P21) : pièces des cases chargées retirées, les autres au
  chargement de leur zone (tâche de l'horloge, drapeau persistant), relais par `partRemoved`.
- `LWT_Diagnostics.lua` : tâche de l'horloge, raison du manque d'eau notée sur les relais vides (`LWT_Diagnosis` ;
  sans pompe dans son réseau, une arrivée d'eau n'a pas de pression, ADR-009 D03).
- `LWT_WasherFix.lua` : tâche de l'horloge, serveur seulement : état des lave-linge servis par nos relais renvoyé aux
  clients (arrêt à sec, raccord), option `WasherFix`.
- `LWT_Power.lua` : seul adaptateur du courant. À `OnInitWorld`, si `LiveWire.API.revision >= 6`, inscrit chaque type
  qui a besoin de courant comme consommateur de Live Wire (`powerConsumption`, `display`, `summary` lus dans l'état
  recopié sur l'objet) ; `powered(part)` : `consumerPowered` de Live Wire, sinon la règle vanilla de la case.
- `LWT_Publisher.lua` : après un pas ou une action, sprite selon l'état (`Sprites:show`), état recopié sur l'objet
  seulement quand il change (rien pour une pièce sans état), boucle sonore annoncée aux joueurs quand elle change et
  répétée après chaque pas, bruit pour les zombies après chaque pas (port `sounds`, crochet `sound`).
- `LWT_GameSounds.lua` : port des sons (ordre `sound` à tous les clients, `addSound` pour les zombies) ;
  `LWT_GameVisuals.lua` : port `visuals` (ordre `jet` à tous les clients quand un arroseur démarre ou s'arrête) ;
  `LWT_GameBroadcast.lua` : envoi d'une commande serveur à tous ou à un joueur (en solo, `triggerEvent`).
- `LWT_GameSettings.lua` : lecture des options sandbox `LiveWater.*` (`getSandboxOptions`).
- Adaptateurs du jeu, minces : `LWT_GameWorld.lua` (port monde : case chargée, objet d'une pièce par son
  sprite, `setSpriteFromName` + `transmitUpdatedSpriteToClients`, `transmitAddObjectToSquare`,
  `transmitRemoveItemFromSquare`, place (`LWT_GameSite`), courant vanilla, état recopié + `transmitModData`, bords des cases : `edge` → mur, clôture ou
  rien selon la règle du moteur `hasNonHoppableWall`, `isEdgeObject`, `without` pour juger « comme parti » un objet
  retiré) et `LWT_GamePlayers.lua` (port joueurs : position, inventaire, outil par étiquette,
  note). Les services ne reçoivent que ces ports ; les tests les remplacent par des doublures (`tests/lwt_fakes.py`).

`client/LiveWater/` : `LWT_PartAction.lua` (action chronométrée des menus : marche, durée, puis commande ; sans
`complete`, donc jamais confiée au serveur), `LWT_PartMenu.lua` (menu générique : les actions que les capacités d'une pièce proposent, crochet
`actions`, lues dans l'état recopié sur l'objet ; une action qui demande un objet n'apparaît que si le joueur le
porte) `LWT_PumpSounds.lua` (boucle sonore jouée localement sur un émetteur libre, à l'ordre du serveur, aucun abonnement
par image) et `LWT_NoticeClient.lua` (affiche les notes `notice` du serveur), `LWT_FixtureMenu.lua` (ligne « Pas d'eau : raison » d'un point d'eau sans eau), `LWT_CityWaterMenu.lua`
(« Raccorder au réseau public »), `LWT_WasherClient.lua` (état « raccordé » d'un lave-linge marqué par le serveur,
appliqué à son menu et à son interrupteur), `LWT_SprinklerJet.lua` (jet animé des arroseurs, **seul abonnement par image
du mod**, D08a : `OnTick` seulement tant qu'un arroseur en marche est chargé, 6 images par seconde au plus, un tour
complet en 8 images (ADR-003 D03), option de mod pour un jet fixe ; jamais sur un serveur dédié), `LWT_AreaView.lua`
(zones arrosées, ADR-003 D02, D04 : une seule option « Afficher toutes les zones arrosées » au clic droit d'un
arroseur ou d'une ligne de goutte-à-goutte, puis « Masquer la zone arrosée » ; cases calculées par les stratégies du
serveur, `LWT_SprayArea` et `LWT_DripArea`, liens d'une ligne lus sur son image ; une seule couleur, surbrillance
persistante du sol, aucun abonnement par image), `LWT_AdminMenu.lua` (« Retirer LiveWater de ce monde », administrateur, confirmation),
`LWT_NetworkView.lua` (vue du réseau : cases demandées au
serveur, surbrillance persistante colorée par le crochet `status`, retirée à la fermeture, aucun abonnement par image),
`LWT_DebugMenu.lua` (sous-menu « LiveWater (debug) » > « Give the Test Kit », seulement avec `-debug` : chaque objet
de LiveWater, 20 tuyaux, une clé à tuyau ; solo : ajout à l'inventaire, serveur : `/additem`, administrateurs).

## Flux, persistance, extension

- Extension : un autre mod inscrit des types de pièce et des capacités par `LiveWater.API` (fichier `shared`, avant
  `OnInitGlobalModData`) et suit `LiveWater.Events`.
- Persistance : une entrée par pièce posée, indexée par `"x,y,z"`, versionnée (`v`), jamais recopiée ; une pièce de
  type absent reste inerte dans le registre (`active()` l'écarte) et revient avec son type. Le graphe
  (`LWT_Network`) se construit à partir des entrées actives, gardées par référence : l'état d'une capacité (vanne,
  usure du filtre) écrit par le domaine est l'état sauvegardé.
- Chargement : `OnInitGlobalModData` (autorité) → registre sur la ModData globale `LiveWater` → `Topology:rebuild`
  (entrées actives, ordre de pose, aucun événement) ; un événement reçu avant est ignoré.
- Pose d'un meuble (vanilla, `placeMoveableInternal`) → `OnObjectAdded` → `Placement:added` → `Topology:add`
  (registre, graphe, sprites, événements). Ramassage ou retrait d'un objet → `OnObjectAboutToBeRemoved` →
  `Placement:removed` → `Topology:remove` (scission). Un objet de bord (mur, clôture, `world:isEdgeObject`) ajouté ou
  retiré appelle en plus `Placement:edgeChanged` → `Topology:relink` (au retrait, sous `world:without`) ; un mur ou une
  clôture construits sans événement sont vus par la tâche d'horloge `edgeWatch`.
- Tuyau : meuble `Base.Mov_LiveWater_Pipe` comme les autres pièces, il suit le flux du meuble décrit juste au-dessus
  (pose au curseur, une pièce par case par `LWT_PlaceRules`, ramassage vanilla à la clé).
- Commande d'un menu client → `sendClientCommand("LiveWater", <commande>, …)` → `OnClientCommand` →
  `Commands:dispatch`. Refus → note traduite (solo : directement ; serveur : `sendServerCommand("LiveWater", "notice", { key })`).
- Pose d'un meuble de LiveWater (pompe) : le curseur vanilla demande `LWT_PlaceRules` (refus loin de l'eau ou sur une
  case qui porte déjà une pièce, ligne rouge du panneau ; ports pleins dits aux joueurs proches par `LWT_Placement`) ; l'autorité refait le contrôle à la fin de l'action, puis `OnObjectAdded` → `Placement:added` →
  `Topology:add` avec l'état rapporté par l'objet (`movableData`) → `attach` (sorte de source relevée) → `partAdded` →
  `Publisher:present`.
- Horloge : `EveryTenMinutes` → `Clock:tick` → par réseau qui a un départ d'eau, chargé ou non : courant
  (`LWT_Power`), `Flow:step`, `stepped`, `Publisher:present`, `waterDelivered`. Aucun abonnement par image (D08), sauf
  le jet des arroseurs côté client (D08a).
- Hors chargement (ADR-006 D06-D08), chaque adaptateur décide par le port monde `isLoaded` : prise d'eau = sorte de
  source notée à la pose (aucune lecture du monde) ; raccord de baril = contenu relevé décompté, rapproché au
  `LoadChunk` (`Fittings:chunkLoaded`) ou au premier pas chargé ; plantes = objet global vanilla
  (`SFarmingSystem.instance:getLuaObjectAt`, `SPlantGlobalObject:water`, sans case) ; arrivée d'eau = besoin 0 ;
  `Publisher` = rien n'est écrit (image, état recopié, son, bruit, jet), la pièce attend dans `away` puis se montre au
  `LoadChunk` (`Publisher:chunkLoaded`) ; courant = `LWT_Power` (Live Wire `gridAt`, réseau de la ville, générateur au
  dernier pas chargé).
- Arroseur : `waterDelivered` → `LWT_Outlets` → `LWT_Plants:deliver` (doses de 0,2 L, `plant:water` ; besoin = débit,
  un quart perdu en l'air, ADR-006) ; `Publisher:present` → ordre `jet` → `LWT_SprinklerJet` relit l'état recopié de la
  case ; au pas de dix minutes, `Publisher` fait entendre l'arroseur aux zombies (`GameSounds:noise`).
- Ligne de goutte-à-goutte : même chemin par le gestionnaire `drip` de `LWT_Plants` (zone `LWT_DripArea`), sans perte,
  sans jet ni son.
- Live Wire (facultatif) : `OnInitWorld` → `Power:register` ; Live Wire appelle ensuite `powerConsumption`, `display`
  et `summary` sur l'autorité, qui lisent l'état recopié sur l'objet de la pompe.

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (Python + `lupa`, Lua 5.1 embarqué).
- Contrôle du mod : `python -B tools/check_mod.py` (ASCII, compilation, chargement, garde serveur, traductions,
  événements par image interdits).
- Tuiles provisoires : `source/tiles/build_livewater_tiles.py` (Blender, sans interface) puis
  `tools/make_tile_board.py` (planche de présentation).

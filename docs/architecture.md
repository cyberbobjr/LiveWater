# LiveWater — architecture

Décisions de référence : [ADR-001](ADR/001-reseau-eau-ouvert.md). Ce document décrit l'état réel du code ; il suit
le [plan 001](ADR-plans/plan-001-reseau-eau-ouvert.md) étape par étape.

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
  `outlet`, `controller`, `layable`, `meter`), réglages et valeurs par défaut de la capacité.
- `Parts/LWT_Part<Nom>.lua` : un fichier par pièce de LiveWater, inscrite par l'API publique comme celle d'un autre
  mod (`LWT_PartPipe.lua` : `LiveWater:PipeGalvanized` ; `LWT_PartPondPump.lua` : `LiveWater:PondPump` ; `LWT_PartFlowMeter.lua` :
  `LiveWater:FlowMeter` ; `LWT_PartHouseInlet.lua` : `LiveWater:HouseInlet`). `LWT_Tiles.lua` : noms des sprites du
  tileset et `variants` d'une pièce dessinée par état et orientation.
- `LWT_InletArea.lua` (pur) : cases servies par une arrivée d'eau (bâtiment de la carte touché, cercle de portée,
  jusqu'à 3 étages au-dessus), lues par une sonde injectée ; `LWT_RelayPlan.lua` (pur) : relais voulus au-dessus des
  points d'eau (partage 3 × 3, sources d'autrui laissées).
- `LWT_Sources.lua` (pur) : registre des sortes de source d'eau (données : qualité, drapeau d'une case voisine ou
  sprites d'un objet voisin) ; `Sources/LWT_Source<Nom>.lua` : une sorte par fichier (`water` : eau naturelle,
  croupie ; `well` : puits vanilla, propre) ; un autre mod en ajoute par `LiveWater.API.registerSource`. La capacité
  `intake` relève la sorte trouvée à la pose et donne la qualité de cette sorte (`ctx.sources` du pas).
- `LWT_Settings.lua` (pur) : multiplicateurs sandbox lus dans le contexte d'un pas (`ctx.scale`).
- Adaptateurs partagés (client et autorité) : `LWT_GameSite.lua` (les 8 cases voisines d'une place : drapeau, sprite,
  source trouvée), `LWT_PlaceRules.lua` (règles de pose au curseur de meuble vanilla : enveloppe
  `canPlaceMoveableInternal` et le panneau d'information, refus seulement pour nos tuiles), `LWT_Mirror.lua` (état
  d'une pièce recopié dans `movableData` de son objet), `LWT_Reasons.lua` (raison de refus → clé de traduction).
- `LWT_Protocol.lua` : noms du module et des commandes réseau partagés par client et serveur ; `LWT_Notice.lua` : note
  traduite au-dessus du joueur (refus d'une commande).
- `LWT_Parts.lua` : registre des types de pièce, copie par liste blanche, unicité des sprites (formes et
  `variants`) ; requêtes du catalogue : `look` (variante d'après les jetons des capacités), `attach` (la place
  convient-elle ?), `lines` (lignes d'information), `hasHook`, `spritesOf`.
- `LWT_Events.lua` : bus d'événements public (D06).
- `LWT_Check.lua` : contrôles de valeurs et copie de champs par règles ; `LWT_Grid.lua` : côtés, masque de 4 bits,
  clé de case `"x,y,z"`.
- `LWT_Network.lua` (domaine pur) : graphe d'une case par pièce, liens entre voisins qui s'offrent le côté commun,
  ports, fusion et scission des réseaux, masque et sprite, eau partie des pièces qui mettent sous pression (distance
  en tuyau, ordre de service : distance puis ordre de pose). Le registre des pièces lui est injecté comme catalogue ;
  il interroge des crochets (`carries`, `blocks`, `pressurizes`, `ports`) et ne nomme aucune capacité.
- `LWT_Flow.lua` (domaine pur) : un pas de dix minutes d'un réseau : pression et débit additionnés des pompes,
  qualité, sorties servies dans l'ordre de service selon leur besoin, réserve de pression, filtre sur le chemin et
  son usure ; litres et qualité de l'eau servie portés sur chaque pièce de son chemin (`through`, `qualityAt` ; part
  de chaque pompe). Crochets `supply`, `source`, `outlet`, `purifies`, `wear` ; le besoin vient des adaptateurs.

`server/LiveWater/` (chaque fichier commence par `if isClient() then return end`) :
- `LWT_Server.lua` : racine de composition sur l'autorité. À `OnInitGlobalModData`, construit les services avec leurs
  adaptateurs sur `ModData.getOrCreate("LiveWater")` (relue à chaque partie) et reconstruit le graphe ; seul fichier
  abonné aux événements du jeu (`OnObjectAdded`, `OnObjectAboutToBeRemoved`, `OnClientCommand`, `EveryTenMinutes`).
  `LiveWater.Server` expose les services de la partie en cours (`registry`, `network`, `topology`, `commands`,
  `placement`, `clock`) aux adaptateurs des étapes suivantes.
- `LWT_Registry.lua` : registre persistant des pièces posées, sur un magasin injecté (la ModData globale en jeu).
- `LWT_Topology.lua` (service d'application) : registre et graphe changés ensemble, sprites recalculés, événements
  `partAdded`, `partRemoved`, `networkChanged` ; `canAdd` sans effet pour les contrôles des commandes.
- `LWT_Placement.lua` : une tuile apparue ou retirée est une pièce si son sprite appartient à un type inscrit
  (`Parts:typeOfSprite`) ; idempotent.
- `LWT_Sprites.lua` : la pièce et ses quatre voisins prennent le sprite de leur masque, appliqué seulement s'il change ;
  un type sans sprite pour ce masque garde celui de sa pose (orientation d'un meuble).
- `LWT_Commands.lua` : répartiteur, table de gestionnaires par nom (un fichier par commande sous `Commands/`, plus
  `LWT_CmdChecks.lua` pour les contrôles d'arguments et de portée, `LWT_CmdCartridge.lua` pour ce que partagent les
commandes du filtre) ; un refus est dit au joueur par clé de traduction.
- `LWT_Clock.lua` : tâches injectées (`chores`, travail borné du même pas), puis pas de dix minutes de chaque réseau éveillé (une pièce sous pression sur une case chargée) :
  courant de chaque pièce qui en a besoin (port `power`, crochet `powered`), distribution, crochet `stepped` de chaque
  membre (litres passés), présentation (port `publisher`), `waterDelivered` pour chaque sortie servie ; besoin des
  sorties injecté (0 par défaut), multiplicateurs sandbox par `scale`.
- `LWT_Outlets.lua` : où va l'eau d'une sortie, par type de sortie (gestionnaire : `need`, `deliver`, `release`) ;
  besoin injecté dans l'horloge, `waterDelivered` et `partRemoved` relayés par la racine de composition.
- `LWT_Relays.lua` : réservoirs relais des arrivées d'eau (gestionnaire `houseInlet` et tâche de l'horloge) : pose,
  retrait, besoin, remplissage, relais en attente d'une case chargée (`orphans`) ; `LWT_GamePlumbing.lua` : adaptateur
  du jeu (bâtiment, points d'eau, objets relais).
- `LWT_Power.lua` : seul adaptateur du courant. À `OnInitWorld`, si `LiveWire.API.revision >= 6`, inscrit chaque type
  qui a besoin de courant comme consommateur de Live Wire (`powerConsumption`, `display`, `summary` lus dans l'état
  recopié sur l'objet) ; `powered(part)` : `consumerPowered` de Live Wire, sinon la règle vanilla de la case.
- `LWT_Publisher.lua` : après un pas ou une action, sprite selon l'état (`Sprites:show`), état recopié sur l'objet
  seulement quand il change (rien pour une pièce sans état), boucle sonore annoncée aux joueurs quand elle change et
  répétée après chaque pas, bruit pour les zombies après chaque pas (port `sounds`, crochet `sound`).
- `LWT_GameSounds.lua` : port des sons (ordre `sound` à tous les clients, ou au client local en solo par
  `triggerEvent`, `addSound` pour les zombies).
- `LWT_GameSettings.lua` : lecture des options sandbox `LiveWater.*` (`getSandboxOptions`).
- Adaptateurs du jeu, minces : `LWT_GameWorld.lua` (port monde : case chargée, case libre, objet d'une pièce par son
  sprite, `setSpriteFromName` + `transmitUpdatedSpriteToClients`, `transmitAddObjectToSquare`,
  `transmitRemoveItemFromSquare`, place (`LWT_GameSite`), courant vanilla, état recopié + `transmitModData`) et `LWT_GamePlayers.lua` (port joueurs : position, inventaire, outil par étiquette,
  note). Les services ne reçoivent que ces ports ; les tests les remplacent par des doublures (`tests/lwt_fakes.py`).

`client/LiveWater/` : `LWT_PipeMenu.lua` (menu minimal : poser ou démonter une pièce `layable`, envoi de la commande
seulement), `LWT_PartMenu.lua` (menu générique : les actions que les capacités d'une pièce proposent, crochet
`actions`, lues dans l'état recopié sur l'objet ; une action qui demande un objet n'apparaît que si le joueur le
porte) `LWT_PumpSounds.lua` (boucle sonore jouée localement sur un émetteur libre, à l'ordre du serveur, aucun abonnement
par image) et `LWT_NoticeClient.lua` (affiche les notes `notice` du serveur). Interface complète : E13.

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
  `Placement:removed` → `Topology:remove` (scission).
- Tuyau : menu client → `sendClientCommand("LiveWater", "lay", { x, y, z, part })` → `OnClientCommand` →
  `Commands:dispatch` → `LWT_CmdLay` (tous les contrôles, section retirée, tuile créée, `Topology:add`).
  `dismantle { x, y, z }` → `LWT_CmdDismantle` (clé à tuyau, `Topology:remove`, tuile retirée, section rendue).
  Refus → note traduite (solo : directement ; serveur : `sendServerCommand("LiveWater", "notice", { key })`).
- Pose d'un meuble de LiveWater (pompe) : le curseur vanilla demande `LWT_PlaceRules` (refus loin de l'eau, ligne
  rouge du panneau) ; l'autorité refait le contrôle à la fin de l'action, puis `OnObjectAdded` → `Placement:added` →
  `Topology:add` avec l'état rapporté par l'objet (`movableData`) → `attach` (sorte de source relevée) → `partAdded` →
  `Publisher:present`.
- Horloge : `EveryTenMinutes` → `Clock:tick` → par réseau éveillé : courant (`LWT_Power`), `Flow:step`, `stepped`,
  `Publisher:present`, `waterDelivered`. Aucun abonnement par image (D08).
- Live Wire (facultatif) : `OnInitWorld` → `Power:register` ; Live Wire appelle ensuite `powerConsumption`, `display`
  et `summary` sur l'autorité, qui lisent l'état recopié sur l'objet de la pompe.

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (Python + `lupa`, Lua 5.1 embarqué).
- Contrôle du mod : `python -B tools/check_mod.py` (ASCII, compilation, chargement, garde serveur, traductions,
  événements par image interdits).
- Tuiles provisoires : `source/tiles/build_livewater_tiles.py` (Blender, sans interface) puis
  `tools/make_tile_board.py` (planche de présentation).

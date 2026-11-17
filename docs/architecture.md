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
  `outlet`, `controller`, `layable`), réglages et valeurs par défaut de la capacité.
- `Parts/LWT_Part<Nom>.lua` : un fichier par pièce de LiveWater, inscrite par l'API publique comme celle d'un autre
  mod (`LWT_PartPipe.lua` : `LiveWater:PipeGalvanized`).
- `LWT_Protocol.lua` : noms du module et des commandes réseau partagés par client et serveur ; `LWT_Notice.lua` : note
  traduite au-dessus du joueur (refus d'une commande).
- `LWT_Parts.lua` : registre des types de pièce, copie par liste blanche, unicité des sprites.
- `LWT_Events.lua` : bus d'événements public (D06).
- `LWT_Check.lua` : contrôles de valeurs et copie de champs par règles ; `LWT_Grid.lua` : côtés, masque de 4 bits,
  clé de case `"x,y,z"`.
- `LWT_Network.lua` (domaine pur) : graphe d'une case par pièce, liens entre voisins qui s'offrent le côté commun,
  ports, fusion et scission des réseaux, masque et sprite, eau partie des pièces qui mettent sous pression (distance
  en tuyau, ordre de service : distance puis ordre de pose). Le registre des pièces lui est injecté comme catalogue ;
  il interroge des crochets (`carries`, `blocks`, `pressurizes`, `ports`) et ne nomme aucune capacité.
- `LWT_Flow.lua` (domaine pur) : un pas de dix minutes d'un réseau : pression et débit additionnés des pompes,
  qualité, sorties servies dans l'ordre de service selon leur besoin, réserve de pression, filtre sur le chemin et
  son usure. Crochets `supply`, `source`, `outlet`, `purifies`, `wear` ; le besoin vient des adaptateurs.

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
  `LWT_CmdChecks.lua` pour les contrôles d'arguments et de portée) ; un refus est dit au joueur par clé de traduction.
- `LWT_Clock.lua` : pas de dix minutes de chaque réseau éveillé (une pièce sous pression sur une case chargée), besoin
  des sorties injecté (0 par défaut), `waterDelivered` pour chaque sortie servie.
- Adaptateurs du jeu, minces : `LWT_GameWorld.lua` (port monde : case chargée, case libre, objet d'une pièce par son
  sprite, `setSpriteFromName` + `transmitUpdatedSpriteToClients`, `transmitAddObjectToSquare`,
  `transmitRemoveItemFromSquare`) et `LWT_GamePlayers.lua` (port joueurs : position, inventaire, outil par étiquette,
  note). Les services ne reçoivent que ces ports ; les tests les remplacent par des doublures (`tests/lwt_fakes.py`).

`client/LiveWater/` : `LWT_PipeMenu.lua` (menu minimal : poser ou démonter une pièce `layable`, envoi de la commande
seulement) et `LWT_NoticeClient.lua` (affiche les notes `notice` du serveur). Interface complète : E13.

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
- Horloge : `EveryTenMinutes` → `Clock:tick` → `Flow:step` par réseau éveillé → `waterDelivered`. Aucun abonnement
  par image (D08).

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (Python + `lupa`, Lua 5.1 embarqué).
- Contrôle du mod : `python -B tools/check_mod.py` (ASCII, compilation, chargement, garde serveur, traductions,
  événements par image interdits).
- Tuiles provisoires : `source/tiles/build_livewater_tiles.py` (Blender, sans interface) puis
  `tools/make_tile_board.py` (planche de présentation).

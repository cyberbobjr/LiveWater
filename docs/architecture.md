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
  `outlet`, `controller`), réglages et valeurs par défaut de la capacité.
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

À venir : `server/LiveWater/` (autorité, persistance, horloge `EveryTenMinutes`), `client/LiveWater/` (menus, vue).

## Flux, persistance, extension

À compléter avec les étapes E02 (API), E05 (persistance) et E07 (commandes). Aucun abonnement par image (D08).

## Outillage

- Tests hors jeu : `python -B -m unittest discover -s tests` (Python + `lupa`, Lua 5.1 embarqué).
- Contrôle du mod : `python -B tools/check_mod.py` (ASCII, compilation, chargement, garde serveur, traductions,
  événements par image interdits).
- Tuiles provisoires : `source/tiles/build_livewater_tiles.py` (Blender, sans interface) puis
  `tools/make_tile_board.py` (planche de présentation).

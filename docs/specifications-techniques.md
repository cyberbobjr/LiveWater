# LiveWater — spécifications techniques

Contrats précis du mod (objets, commandes réseau, ModData, options sandbox, traductions, API publique). Ils sont
écrits ici à mesure que les étapes du [plan 001](ADR-plans/plan-001-reseau-eau-ouvert.md) les livrent.

## Identité

| Élément | Valeur |
|---|---|
| `id` | `batman_LiveWater` |
| Version minimale du jeu | 42.21 (cible 42.22) |
| `require=` | aucun |
| `incompatible=` | `\LGExtendedPlumbing,\LGMainsWater` |
| Table Lua globale | `LiveWater` |
| Préfixes | fichiers `LWT_*.lua`, recettes `LWT`, traductions `*_LWT_*`, ids de pièces `"<Mod>:<Nom>"` |

## API publique (`LiveWater.API`, révision 1)

Inscription depuis un fichier `shared`, pendant le chargement, avant `OnInitGlobalModData` (ensuite :
`registration_closed`). Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console.

| Fonction | Rôle | Raisons de refus |
|---|---|---|
| `registerPart(id, definition)` | type de pièce `"<Mod>:<Nom>"` | `invalid_id`, `duplicate_part`, `invalid_definition`, `invalid_sprites`, `duplicate_sprite`, `invalid_sides`, `invalid_capabilities`, `unknown_capability`, `invalid_field` |
| `registerCapability(kind, implementation)` | nouvelle capacité ; `kind` nom simple ou `"<Mod>:<nom>"` ; `implementation.define(params)` obligatoire | `invalid_kind`, `duplicate_capability`, `invalid_implementation` |
| `part(id)` | copie de la définition contrôlée, ou `nil` | — |
| `revision` | entier, 1 | — |

Définition d'une pièce (copiée champ par champ, le reste est ignoré) : `sprites` (`{ [masque] = sprite }`, masques
0 à 15, un sprite n'appartient qu'à un type), `sides` (masque des côtés raccordables, 15 par défaut),
`capabilities` (`{ kind = réglages ou true }`).

| Capacité | Réglages (défaut) |
|---|---|
| `conduit` | aucun |
| `intake` | `quality` : `"tainted"` (défaut) ou `"clean"` |
| `pump` | `ports` 1-4 (4), `pressure` (6), `flow` litres par pas de dix minutes (50) |
| `valve` | `open` à la pose (`true`) |
| `filter` | `capacity` litres par cartouche (500) |
| `outlet` | `type` obligatoire ; `pressureCost` et `needsClean` : `houseInlet` 2 et vrai, `sprinkler` 1 et faux, autre type 1 et faux |
| `controller` | `mode` : `"manual"` (défaut) ou `"timer"` |
| `layable` | `item` obligatoire (type complet de l'objet posé, `"LiveWater.PipeSection"`) ; `tool` étiquette d'outil du démontage (`"base:pipewrench"`) |

Crochets d'une capacité (tous facultatifs sauf `define`), appelés avec les réglages contrôlés puis l'état de la
pièce pour cette capacité (`part.data[kind]`, éventuellement `nil`) : `carries` (l'eau traverse), `blocks` (coupe
l'eau, vanne fermée), `pressurizes` (l'eau part de là), `ports` (nombre maximal de tuyaux raccordés), `supply`
(pression et litres par pas), `source` (qualité `"clean"` ou `"tainted"`, `nil` à sec), `outlet` (coût de pression,
eau propre exigée), `purifies` (le filtre agit), `wear(p, d, litres)` (seul crochet qui écrit son état), `layable` (objet posé et outil
du démontage).

## Pièces de LiveWater

| Id | Sprites | Capacités |
|---|---|---|
| `LiveWater:PipeGalvanized` | `batman_livewater_01_<masque>`, masques 0 à 15 | `conduit`, `layable` (`LiveWater.PipeSection`, `base:pipewrench`) |

## Objets et recettes

| Élément | Contrat |
|---|---|
| `LiveWater.PipeSection` | `media/scripts/LWT_items.txt`, `base:normal`, 0,4 kg, icône `Item_LWT_PipeSection` ; une par case de tuyau |
| `LWTCutPipeSections` | `media/scripts/LWT_recipes.txt` : 1 `Base.MetalPipe` et un outil `tags[base:metalsaw]` gardé donnent 4 `LiveWater.PipeSection` (action `SawSmallItemMetal`) |

## Commandes réseau (module `LiveWater`, `LWT_Protocol`)

Tout argument est recontrôlé sur l'autorité. Portée : 3 cases (Tchebychev) sur l'étage du joueur.

| Sens | Commande | Arguments | Contrôles, dans l'ordre (raison du refus) | Effet |
|---|---|---|---|---|
| client → serveur | `lay` | `x`, `y`, `z` entiers, `part` id | arguments (`invalid`), type `layable` (`not_layable`), portée (`too_far`), case chargée (`not_loaded`), case libre : sol, ni eau, ni solide, ni arbre (`blocked`), case sans pièce (`occupied`), ports (`ports_full`), objet dans l'inventaire (`no_item`) | objet retiré, tuile `sprites[0]` créée, pièce ajoutée, sprites recalculés |
| client → serveur | `dismantle` | `x`, `y`, `z` entiers | arguments (`invalid`), pièce présente (`nothing_here`), type `layable` (`not_layable`), portée (`too_far`), outil de l'étiquette (`need_tool`) | pièce retirée, tuile retirée, objet rendu (au sol si trop lourd) |
| serveur → client | `notice` | `key` (clé de traduction) | — | note au-dessus du joueur (en solo, affichée directement) |

Clés des refus (`IG_UI.json`) : `IGUI_LWT_Invalid`, `IGUI_LWT_NotLayable`, `IGUI_LWT_TooFar` (`too_far`,
`not_loaded`), `IGUI_LWT_Blocked`, `IGUI_LWT_Occupied`, `IGUI_LWT_PortsFull`, `IGUI_LWT_NoItem`, `IGUI_LWT_NeedTool`,
`IGUI_LWT_NothingHere`, autre raison `IGUI_LWT_Refused`. Menu : `ContextMenu_LWT_Lay`, `ContextMenu_LWT_Dismantle`
(`%1` = nom de l'objet posé).

## Registre persistant (ModData globale `LiveWater`, `LWT_Registry`)

Table `ModData.getOrCreate("LiveWater")`, lue sur l'autorité à chaque `OnInitGlobalModData` (jamais gardée d'une
partie à l'autre) ; le graphe en est reconstruit à ce moment.

| Clé | Contenu |
|---|---|
| `seq` | dernier ordre de pose attribué (jamais réutilisé) |
| `parts["x,y,z"]` | entrée d'une pièce posée |

Entrée : `v` (version du schéma, 1), `type` (id `"<Mod>:<Nom>"`), `x`, `y`, `z`, `order` (ordre de pose), `data`
(`{ [capacité] = état }`, par exemple `valve = { open = false }`, `filter = { used = 120 }`). Tout autre champ est
conservé tel quel. Une pièce dont le type n'est pas inscrit reste dans le registre, inerte. Refus d'ajout :
`unknown_part`, `occupied`.

États d'une sortie après un pas (`LWT_Flow`) : `served`, `idle` (aucun besoin), `closed`, `no_water`, `unfiltered`
(« eau non filtrée »), `no_pressure` (« sans pression »).

Masque de raccord : N = 1, E = 2, S = 4, O = 8 ; le sprite affiché est `sprites[masque]`, sinon `sprites[0]`.

Événements `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` (rendent `true`, ou `false` et `unknown_event`,
`invalid_handler`), émis sur l'autorité : `partAdded` (entrée), `partRemoved` (entrée), `networkChanged` (id du
réseau ; au retrait, une fois par réseau resté raccordé), `waterDelivered` (pièce, litres, qualité ; à chaque pas de
dix minutes, par sortie servie), `valveChanged`. La reconstruction au chargement n'émet rien.

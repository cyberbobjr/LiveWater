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

## API publique (`LiveWater.API`, révision 2)

Inscription depuis un fichier `shared`, pendant le chargement, avant `OnInitGlobalModData` (ensuite :
`registration_closed`). Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console.

| Fonction | Rôle | Raisons de refus |
|---|---|---|
| `registerPart(id, definition)` | type de pièce `"<Mod>:<Nom>"` | `invalid_id`, `duplicate_part`, `invalid_definition`, `invalid_sprites`, `duplicate_sprite`, `invalid_sides`, `invalid_capabilities`, `unknown_capability`, `invalid_field` |
| `registerCapability(kind, implementation)` | nouvelle capacité ; `kind` nom simple ou `"<Mod>:<nom>"` ; `implementation.define(params)` obligatoire | `invalid_kind`, `duplicate_capability`, `invalid_implementation` |
| `part(id)` | copie de la définition contrôlée, ou `nil` | — |
| `revision` | entier ; 2 : champ `variants`, crochets `look`, `attach`, `power`, `powered`, `stepped`, `output`, `lines` | — |

Définition d'une pièce (copiée champ par champ, le reste est ignoré) : `sprites` (`{ [masque] = sprite }`, masques
0 à 15, redessinés selon les raccords), `variants` (révision 2 : `{ [clé] = { sprite S, E, N, O } }`, sprites
choisis par l'état de la pièce, jamais par le masque ; `sprites` devient facultatif), `sides` (masque des côtés
raccordables, 15 par défaut), `capabilities` (`{ kind = réglages ou true }`). Un sprite n'appartient qu'à un type
(formes et variantes). La variante affichée est la clé formée des jetons `look` des capacités dans l'ordre des noms
de capacité, joints par `_` (filtre `filter` + pompe `on` → `filter_on`). Refus ajouté : `invalid_variants`.

| Capacité | Réglages (défaut) |
|---|---|
| `conduit` | aucun |
| `intake` | `quality` : `"tainted"` (défaut) ou `"clean"` ; ne se pose qu'à côté d'une source (`attach`, refus `no_source`), dont la sorte est relevée dans son état (`source`) |
| `pump` | `ports` 1-4 (4), `pressure` (6), `flow` litres par pas de dix minutes (50, × option `PumpFlowMultiplier`), `watts` en marche (250 ; 0 = sans courant) |
| `valve` | `open` à la pose (`true`) |
| `filter` | `capacity` litres par cartouche (500) |
| `outlet` | `type` obligatoire ; `pressureCost` et `needsClean` : `houseInlet` 2 et vrai, `sprinkler` 1 et faux, autre type 1 et faux |
| `controller` | `mode` : `"manual"` (défaut) ou `"timer"` |
| `layable` | `item` obligatoire (type complet de l'objet posé, `"LiveWater.PipeSection"`) ; `tool` étiquette d'outil du démontage (`"base:pipewrench"`) |

Crochets d'une capacité (tous facultatifs sauf `define`), appelés avec les réglages contrôlés puis l'état de la
pièce pour cette capacité (`part.data[kind]`, éventuellement `nil`) : `carries` (l'eau traverse), `blocks` (coupe
l'eau, vanne fermée), `pressurizes` (l'eau part de là), `ports` (nombre maximal de tuyaux raccordés), `supply`
(pression et litres par pas), `source` (qualité `"clean"` ou `"tainted"`, `nil` à sec), `outlet` (coût de pression,
eau propre exigée), `purifies` (le filtre agit), `wear(p, d, litres)` (écrit son état), `layable` (objet posé et outil
du démontage). Révision 2 : `look` (jeton de la variante), `attach(p, d, place)` (la place convient-elle ? `true`, ou
`false` et une raison ; peut relever ce qu'elle trouve), `power` (besoin de courant, watts tirés maintenant),
`powered(p, d, oui)` (l'autorité dit si la pièce a du courant pour ce pas), `stepped(p, d, bilan, ctx)` (fin de pas :
`bilan.through` = litres passés par la pièce, `bilan.quality`), `output` (litres donnés au dernier pas), `lines`
(lignes d'information `{ clé, arg…, rank = n }`). `supply`, `purifies` et `wear` reçoivent en dernier le contexte du
pas (`ctx.scale(nom)` : multiplicateur sandbox).

Sortes de source d'eau (`LiveWater.Sources`, interne en révision 2) : `water` (eau naturelle : drapeau `water` d'une
des 8 cases voisines, eau croupie). Une sorte est une donnée `{ quality, flag?, sprites? }` ; les sortes propres
sont essayées d'abord.

## Pièces de LiveWater

| Id | Sprites | Capacités |
|---|---|---|
| `LiveWater:PipeGalvanized` | `batman_livewater_01_<masque>`, masques 0 à 15 | `conduit`, `layable` (`LiveWater.PipeSection`, `base:pipewrench`) |
| `LiveWater:PondPump` | `variants` : `off` 24-27, `on` 28-31, `filter_on` 32-35, `filter_off` 36-39 (S, E, N, O) | `intake`, `pump` (4 ports, pression 6, 50 L, 250 W) |

## Objets et recettes

| Élément | Contrat |
|---|---|
| `LiveWater.PipeSection` | `media/scripts/LWT_items.txt`, `base:normal`, 0,4 kg, icône `Item_LWT_PipeSection` ; une par case de tuyau |
| `LWTCutPipeSections` | `media/scripts/LWT_recipes.txt` : 1 `Base.MetalPipe` et un outil `tags[base:metalsaw]` gardé donnent 4 `LiveWater.PipeSection` (action `SawSmallItemMetal`) |
| `Base.Mov_LiveWater_PondPump` | `media/scripts/LWT_moveables.txt`, `base:moveable`, `WorldObjectSprite = batman_livewater_01_24` (objet `CustomItem` des tuiles 24-39) |
| `LWTBuildPondPump` | Électricité 2, action `MakingElectrical` : tournevis et clé gardés, 1 `Base.MetalPipe`, 2 `Base.SmallSheetMetal`, 3 `Base.ElectronicsScrap`, 2 `Base.ElectricWire`, 4 `Base.Screws` → 1 `Base.Mov_LiveWater_PondPump` ; 15 XP d'Électricité |

## Options sandbox (`media/sandbox-options.txt`, page `LiveWater`)

| Option | Type, bornes, défaut | Effet |
|---|---|---|
| `LiveWater.PumpFlowMultiplier` | double 0,1-10, 1,0 | multiplie le débit des pompes (`flow`) |

Traductions `Sandbox_LWT_<Option>` et `_tooltip` dans `Sandbox.json`, onglet `Sandbox_LiveWater`.

## Électricité (`LWT_Power`, D20)

- Avec Live Wire (`LiveWire.API.revision >= 6`), à `OnInitWorld`, sur l'autorité : un consommateur par type de pièce
  qui a le crochet `power`, id `LiveWater_` suivi de l'id du type où `:` devient `_` (`LiveWater_LiveWater_PondPump`),
  `sprites` = tous les sprites du type, catégorie `other`, circuit `equipment`. `powerConsumption(o)` : watts de
  l'état recopié (250 en marche, 0 arrêtée). `display(o)` : `{ lines }`, les 4 premières lignes d'information (sans
  `name`). `summary(objets)` : `{ "IGUI_LWT_LW_Pumps", en marche, total }`, `{ "IGUI_LWT_LW_Flow", litres }`.
  Courant : `LiveWire.API.consumerPowered(objet)`.
- Sans Live Wire : courant si `square:haveElectricity()` (générateur) ou `square:hasGridPower()` (réseau public).
- Sans courant, une pompe ne donne ni pression ni eau ; elle ne marche que si une sortie a pris de l'eau au pas.

## État recopié sur l'objet (`LWT_Mirror`)

`objet:getModData().movableData.LiveWater = { type, data }` (copie de l'entrée du registre), écrit sur l'autorité
quand il change, envoyé par `transmitModData()` (serveur). Lu par les menus, Live Wire, et à la pose d'un meuble :
l'état revient avec la pompe ramassée puis reposée (le vanilla recopie `movableData` dans l'objet d'inventaire).

## Commandes réseau (module `LiveWater`, `LWT_Protocol`)

Tout argument est recontrôlé sur l'autorité. Portée : 3 cases (Tchebychev) sur l'étage du joueur.

| Sens | Commande | Arguments | Contrôles, dans l'ordre (raison du refus) | Effet |
|---|---|---|---|---|
| client → serveur | `lay` | `x`, `y`, `z` entiers, `part` id | arguments (`invalid`), type `layable` (`not_layable`), portée (`too_far`), case chargée (`not_loaded`), case libre : sol, ni eau, ni solide, ni arbre (`blocked`), case sans pièce (`occupied`), ports (`ports_full`), objet dans l'inventaire (`no_item`) | objet retiré, tuile `sprites[0]` créée, pièce ajoutée, sprites recalculés |
| client → serveur | `dismantle` | `x`, `y`, `z` entiers | arguments (`invalid`), pièce présente (`nothing_here`), type `layable` (`not_layable`), portée (`too_far`), outil de l'étiquette (`need_tool`) | pièce retirée, tuile retirée, objet rendu (au sol si trop lourd) |
| serveur → client | `notice` | `key` (clé de traduction) | — | note au-dessus du joueur (en solo, affichée directement) |

Clés des refus (`IG_UI.json`, table partagée `LWT_Reasons`) : `IGUI_LWT_NoSource` (`no_source`), `IGUI_LWT_Invalid`, `IGUI_LWT_NotLayable`, `IGUI_LWT_TooFar` (`too_far`,
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
(`{ [capacité] = état }`, par exemple `valve = { open = false }`, `filter = { used = 120 }`, `intake = { source =
"water" }`, `pump = { powered, running, litres }`). Tout autre champ est
conservé tel quel. Une pièce dont le type n'est pas inscrit reste dans le registre, inerte. Refus d'ajout :
`unknown_part`, `occupied`.

États d'une sortie après un pas (`LWT_Flow`) : `served`, `idle` (aucun besoin), `closed`, `no_water`, `unfiltered`
(« eau non filtrée »), `no_pressure` (« sans pression »).

Masque de raccord : N = 1, E = 2, S = 4, O = 8 ; le sprite affiché est `sprites[masque]`, sinon `sprites[0]`.

Événements `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` (rendent `true`, ou `false` et `unknown_event`,
`invalid_handler`), émis sur l'autorité : `partAdded` (entrée), `partRemoved` (entrée), `networkChanged` (id du
réseau ; au retrait, une fois par réseau resté raccordé), `waterDelivered` (pièce, litres, qualité ; à chaque pas de
dix minutes, par sortie servie), `valveChanged`. La reconstruction au chargement n'émet rien.

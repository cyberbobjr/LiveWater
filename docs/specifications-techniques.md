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

## API publique (`LiveWater.API`, révision 7)

Inscription depuis un fichier `shared`, pendant le chargement, avant `OnInitGlobalModData` (ensuite :
`registration_closed`). Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console.

| Fonction | Rôle | Raisons de refus |
|---|---|---|
| `registerPart(id, definition)` | type de pièce `"<Mod>:<Nom>"` | `invalid_id`, `duplicate_part`, `invalid_definition`, `invalid_sprites`, `duplicate_sprite`, `invalid_sides`, `invalid_capabilities`, `unknown_capability`, `invalid_field` |
| `registerCapability(kind, implementation)` | nouvelle capacité ; `kind` nom simple ou `"<Mod>:<nom>"` ; `implementation.define(params)` obligatoire | `invalid_kind`, `duplicate_capability`, `invalid_implementation` |
| `part(id)` | copie de la définition contrôlée, ou `nil` | — |
| `registerSource(kind, definition)` | révision 6 : sorte de source d'eau `{ quality = "clean" ou "tainted", flag = drapeau IsoFlagType d'une case voisine, sprites = { sprite d'un objet voisin } }` (au moins `flag` ou `sprites`) ; `kind` nom simple ou `"<Mod>:<Nom>"` | `registration_closed`, `invalid_kind`, `duplicate_source`, `invalid_definition` |
| `revision` | entier ; 2 : champ `variants`, crochets `look`, `attach`, `power`, `powered`, `stepped`, `output`, `lines` ; 3 : réglage `item` du filtre, crochets `cartridge`, `fit`, `unfit`, `actions` ; 4 : réglages d'entretien de la pompe, crochets `switchable`, `switch`, `repairable`, `repair`, `sound` ; 5 : capacité `meter`, réglage `ports` de `conduit`, qualité par pièce dans le bilan de `stepped` ; 6 : `registerSource`, qualité de l'eau d'une prise selon la sorte de source relevée ; 7 : type de sortie en troisième résultat du crochet `outlet`, `outcome.outlet` de `stepped` (ce que le pas a fait d'une sortie), gardé comme état de la sortie | — |

Définition d'une pièce (copiée champ par champ, le reste est ignoré) : `sprites` (`{ [masque] = sprite }`, masques
0 à 15, redessinés selon les raccords), `variants` (révision 2 : `{ [clé] = { sprite S, E, N, O } }`, sprites
choisis par l'état de la pièce, jamais par le masque ; `sprites` devient facultatif), `sides` (masque des côtés
raccordables, 15 par défaut), `capabilities` (`{ kind = réglages ou true }`). Un sprite n'appartient qu'à un type
(formes et variantes). La variante affichée est la clé formée des jetons `look` des capacités dans l'ordre des noms
de capacité, joints par `_` (filtre `filter` + pompe `on` → `filter_on`). Refus ajouté : `invalid_variants`.

| Capacité | Réglages (défaut) |
|---|---|
| `conduit` | `ports` facultatif 1-4 (révision 5 : pièce en ligne, 2 pour un compteur) |
| `meter` | aucun (révision 5) ; état `{ litres, quality }` du dernier pas |
| `intake` | `quality` : `"tainted"` (défaut) ou `"clean"` ; ne se pose qu'à côté d'une source (`attach`, refus `no_source`), dont la sorte est relevée dans son état (`source`) |
| `pump` | `ports` 1-4 (4), `pressure` (6), `flow` litres par pas de dix minutes à plein rendement (50, × rendement, × option `PumpFlowMultiplier`), `watts` en marche (250 ; 0 = sans courant) ; révision 4 : `wear` points de rendement perdus par minute de marche (0,01, × option `PumpWearMultiplier`), `breakdownBelow` (20), `breakdownChance` par pas de marche (0,02), `repairItem` (`Base.ScrapMetal`), `repairCount` (2), `repairTool` étiquette facultative, `sound` boucle en marche (`GeneratorLoop`), `noiseRadius` et `noiseVolume` (20, 20) |
| `valve` | `open` à la pose (`true`) |
| `filter` | `capacity` litres par cartouche (500, × option `FilterCapacityMultiplier`, notée à la pose de la cartouche) ; `item` (révision 3) : type complet d'une cartouche amovible, le filtre n'agit que cartouche montée |
| `outlet` | `type` obligatoire ; `pressureCost` et `needsClean` : `houseInlet` 2 et vrai, `sprinkler` 1 et faux, autre type 1 et faux ; état (révision 7) `{ state }` du dernier pas ; `look` `filtered` ou `unfiltered` pour une sortie qui exige de l'eau propre ; ligne `IGUI_LWT_Outlet_<état>` |
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
pas (`ctx.scale(nom)` : multiplicateur sandbox). Révision 3 : `cartridge(p, d, ctx)` (objet de la cartouche, montée
ou non, part restante 0-1), `fit(p, d, part, ctx)`, `unfit(p, d)`, `actions(p, d)` (actions du menu : `{ command,
key, item }`, `item` = objet à porter). Révision 4 : `switchable` (position de l'interrupteur, ou `nil`), `switch(p, d, oui)`, `repairable` (matériau, nombre, outil, raison du refus `running` ou `not_needed` ou `nil`), `repair`, `sound` (nom de la boucle, rayon et volume du bruit tant que la pièce en fait).

Sortes de source d'eau (`LiveWater.Sources`, publiques par `registerSource` en révision 6) : `water` (eau
naturelle : drapeau `water` d'une des 8 cases voisines, eau croupie), `well` (puits vanilla : objet `camping_01_16`
sur une des 8 cases voisines, eau propre). Une sorte est une donnée `{ quality, flag?, sprites? }` ; les sortes
propres sont essayées d'abord. La prise (`intake`) relève la sorte à la pose (`source`) et donne sa qualité ; une
sorte qui n'est plus inscrite donne le réglage `quality` de la capacité.

## Pièces de LiveWater

| Id | Sprites | Capacités |
|---|---|---|
| `LiveWater:PipeGalvanized` | `batman_livewater_01_<masque>`, masques 0 à 15 | `conduit`, `layable` (`LiveWater.PipeSection`, `base:pipewrench`) |
| `LiveWater:FlowMeter` | `sprites` : 20 (masques 2, 8, 10), 21 (masques 1, 4, 5) ; seul ou en coude, garde le sprite de sa pose | `conduit` (2 ports), `meter` |
| `LiveWater:HouseInlet` | `variants` : `filtered` 40-43, `unfiltered` 44-47 (S, E, N, O) | `outlet` (`houseInlet`) |
| `LiveWater:PondPump` | `variants` : `off` 24-27, `on` 28-31, `filter_on` 32-35, `filter_off` 36-39 (S, E, N, O) | `filter` (`LiveWater.WaterFilter`, 500 L), `intake`, `pump` (4 ports, pression 6, 50 L, 250 W, réparation 2 `Base.ScrapMetal` + `base:wrench`, boucle `GeneratorLoop`) |

## Objets et recettes

| Élément | Contrat |
|---|---|
| `LiveWater.PipeSection` | `media/scripts/LWT_items.txt`, `base:normal`, 0,4 kg, icône `Item_LWT_PipeSection` ; une par case de tuyau |
| `LWTCutPipeSections` | `media/scripts/LWT_recipes.txt` : 1 `Base.MetalPipe` et un outil `tags[base:metalsaw]` gardé donnent 4 `LiveWater.PipeSection` (action `SawSmallItemMetal`) |
| `LiveWater.WaterFilter` | `base:normal`, 0,5 kg, icône `Item_LWT_WaterFilter`, `ConditionMax = 100` : l'état est la part restante (100 neuve) ; infobulle `Tooltip_LWT_WaterFilter` |
| `LWTMakeWaterFilter` | action `Making`, 2 `tags[base:charcoal]`, 2 `Base.RippedSheets` → 1 `LiveWater.WaterFilter` |
| `Base.Mov_LiveWater_FlowMeter` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_20` (objet `CustomItem` des tuiles 20-21) |
| `LWTBuildFlowMeter` | action `Making` : tournevis gardé, 1 `LiveWater.PipeSection`, 1 `Base.SmallSheetMetal`, 2 `Base.Screws` → 1 `Base.Mov_LiveWater_FlowMeter` |
| `Base.Mov_LiveWater_HouseInlet` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_40` (objet `CustomItem` des tuiles 40-47) |
| `LWTBuildHouseInlet` | action `Making` : clé à tuyau gardée, 2 `LiveWater.PipeSection`, 1 `Base.SmallSheetMetal`, 4 `Base.Screws` → 1 `Base.Mov_LiveWater_HouseInlet` |
| `Base.Mov_LiveWater_PondPump` | `media/scripts/LWT_moveables.txt`, `base:moveable`, `WorldObjectSprite = batman_livewater_01_24` (objet `CustomItem` des tuiles 24-39) |
| `LWTBuildPondPump` | Électricité 2, action `MakingElectrical` : tournevis et clé gardés, 1 `Base.MetalPipe`, 2 `Base.SmallSheetMetal`, 3 `Base.ElectronicsScrap`, 2 `Base.ElectricWire`, 4 `Base.Screws` → 1 `Base.Mov_LiveWater_PondPump` ; 15 XP d'Électricité |

## Options sandbox (`media/sandbox-options.txt`, page `LiveWater`)

| Option | Type, bornes, défaut | Effet |
|---|---|---|
| `LiveWater.PumpFlowMultiplier` | double 0,1-10, 1,0 | multiplie le débit des pompes (`flow`) |
| `LiveWater.FilterCapacityMultiplier` | double 0,1-10, 1,0 | multiplie les litres d'une cartouche (`capacity`) |
| `LiveWater.PumpWearMultiplier` | double 0-10, 1,0 | multiplie la perte de rendement en marche (`wear`) ; 0 = aucune usure |
| `LiveWater.InletRange` | entier 1-100, 20 | portée (cercle, en cases) d'une arrivée d'eau dans le bâtiment qu'elle touche |
| `LiveWater.BaseRange` | entier 1-50, 12 | portée d'une arrivée d'eau hors bâtiment de la carte (base du joueur, L11) |

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
| client → serveur | `fitFilter` | `x`, `y`, `z` entiers | arguments (`invalid`), pièce (`nothing_here`), emplacement de cartouche (`no_filter_slot`), portée (`too_far`), cartouche dans l'inventaire (`no_cartridge`) | cartouche prise (son état = part restante) ; l'ancienne ressort d'abord (rendue avec sa part restante, jetée si usée) |
| client → serveur | `removeFilter` | `x`, `y`, `z` entiers | mêmes contrôles jusqu'à la portée, puis cartouche montée (`no_filter`) | cartouche rendue avec sa part restante, ou jetée si usée |
| client → serveur | `switchPump` | `x`, `y`, `z` entiers | arguments, pièce, interrupteur (`not_switchable`), portée | interrupteur basculé ; éteinte, la pompe s'arrête aussitôt |
| client → serveur | `repairPump` | `x`, `y`, `z` entiers | arguments, pièce, réparable (`not_repairable`), à l'arrêt (`running`), usée ou en panne (`not_needed`), portée, outil (`need_wrench`), matériau (`no_parts`) | matériau consommé, rendement 100 %, panne effacée |
| client → serveur | `connectBarrel` | `x`, `y`, `z` entiers | arguments, portée, clé à tuyau (`need_tool`), baril raccordable (`not_barrel`), arrivée d'eau dont la zone atteint la case (`no_inlet`) | baril raccordé à l'arrivée d'eau la plus proche, marque `LiveWaterBarrel` |
| client → serveur | `disconnectBarrel` | `x`, `y`, `z` entiers | arguments, portée, clé à tuyau, baril raccordé (`not_connected`) | raccord et marque effacés |
| client → serveur | `reserveBarrel` | `x`, `y`, `z` entiers | arguments, portée, baril raccordé | « en réserve » basculé |
| serveur → client | `sound` | `x`, `y`, `z`, `name` (absent = arrêt) | — | boucle jouée ou arrêtée localement (en solo, par `triggerEvent`) |
| serveur → client | `notice` | `key` (clé de traduction) | — | note au-dessus du joueur (en solo, affichée directement) |

Clés des refus (`IG_UI.json`, table partagée `LWT_Reasons`) : `IGUI_LWT_NoSource` (`no_source`), `IGUI_LWT_NoFilter` (`no_cartridge`), `IGUI_LWT_NoFilterFitted` (`no_filter`), `IGUI_LWT_NoFilterSlot` (`no_filter_slot`), `IGUI_LWT_StillRunning` (`running`), `IGUI_LWT_NotNeeded` (`not_needed`), `IGUI_LWT_NeedWrench` (`need_wrench`), `IGUI_LWT_NoScrap` (`no_parts`), `IGUI_LWT_Invalid`, `IGUI_LWT_NotLayable`, `IGUI_LWT_TooFar` (`too_far`,
`not_loaded`), `IGUI_LWT_Blocked`, `IGUI_LWT_Occupied`, `IGUI_LWT_PortsFull`, `IGUI_LWT_NoItem`, `IGUI_LWT_NeedTool`,
`IGUI_LWT_NothingHere`, `IGUI_LWT_NotBarrel` (`not_barrel`), `IGUI_LWT_NoInlet` (`no_inlet`), `IGUI_LWT_NotConnected` (`not_connected`), autre raison `IGUI_LWT_Refused`. Menu : `ContextMenu_LWT_Lay`, `ContextMenu_LWT_Dismantle`
(`%1` = nom de l'objet posé) ; menu des pièces : `ContextMenu_LWT_FitFilter`, `ContextMenu_LWT_ReplaceFilter`, `ContextMenu_LWT_RemoveFilter`, `ContextMenu_LWT_TurnOn`, `ContextMenu_LWT_TurnOff`, `ContextMenu_LWT_Repair`, `ContextMenu_LWT_Info` (infobulle : lignes d'information traduites, `IGUI_LWT_Pump_*`, `IGUI_LWT_Filter_*`, `IGUI_LWT_Source_<sorte>`).

## Registre persistant (ModData globale `LiveWater`, `LWT_Registry`)

Table `ModData.getOrCreate("LiveWater")`, lue sur l'autorité à chaque `OnInitGlobalModData` (jamais gardée d'une
partie à l'autre) ; le graphe en est reconstruit à ce moment.

| Clé | Contenu |
|---|---|
| `seq` | dernier ordre de pose attribué (jamais réutilisé) |
| `parts["x,y,z"]` | entrée d'une pièce posée |
| `relays["x,y,z"]` | relais d'une arrivée d'eau (clé de sa case) : `{ ["x,y,z"] = { x, y, z } }` |
| `barrels["x,y,z"]` | barils raccordés à une arrivée d'eau (clé de sa case) : `{ ["x,y,z"] = { x, y, z, reserve } }` |
| `orphans["x,y,z"]` | relais à retirer dès que sa case est chargée : `{ x, y, z, owner }` |

Entrée : `v` (version du schéma, 1), `type` (id `"<Mod>:<Nom>"`), `x`, `y`, `z`, `order` (ordre de pose), `data`
(`{ [capacité] = état }`, par exemple `valve = { open = false }`, `filter = { used = 120 }`, `intake = { source =
"water" ou "well" }`, `pump = { on, powered, running, litres, efficiency, broken }`, `meter = { litres, quality }`). Tout autre champ est
conservé tel quel. Une pièce dont le type n'est pas inscrit reste dans le registre, inerte. Refus d'ajout :
`unknown_part`, `occupied`.

États d'une sortie après un pas (`LWT_Flow`) : `served`, `idle` (aucun besoin), `closed`, `no_water`, `unfiltered`
(« eau non filtrée »), `no_pressure` (« sans pression »).

Masque de raccord : N = 1, E = 2, S = 4, O = 8 ; le sprite affiché est `sprites[masque]`, sinon `sprites[0]`.

Événements `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` (rendent `true`, ou `false` et `unknown_event`,
`invalid_handler`), émis sur l'autorité : `partAdded` (entrée), `partRemoved` (entrée), `networkChanged` (id du
réseau ; au retrait, une fois par réseau resté raccordé), `waterDelivered` (pièce, litres, qualité ; à chaque pas de
dix minutes, par sortie servie), `valveChanged`. La reconstruction au chargement n'émet rien.

## Réservoirs relais des arrivées d'eau (`LWT_Relays`, D18, D21)

- Objet : `IsoThumpable` traversable, sprite `batman_livewater_01_76` (tuile définie sans image), composant
  `FluidContainer` de 25 L nommé `LiveWaterRelay`, ModData `LiveWaterRelay = { inlet = "x,y,z", why = raison }` ;
  posé un niveau au-dessus d'un point d'eau (le moteur y cherche la source : case au-dessus puis les 8 autour).
- Points d'eau servis : sprite `waterPiped`, raccordés (`getUsesExternalWaterSource`) ou raccordables (ModData
  `canBeWaterPiped`, ou d'origine après la coupure de l'eau de la ville), dans la zone de l'arrivée d'eau
  (`LWT_InletArea` : bâtiment de la carte touché, cercle de portée, jusqu'à 3 étages au-dessus, et 2 niveaux de sous-sol
  sous l'emprise du rez-de-chaussée). Lave-linge compris (tuiles `waterPiped` en 42.22). Un point d'eau dont la source n'est pas un relais de LiveWater est laissé tel quel ; un relais de
  Live Wire (`LiveWireRelay`) n'est jamais posé, rempli ni retiré.
- Besoin de l'arrivée d'eau = place libre de ses relais qui servent un point d'eau raccordé ; l'eau livrée les remplit
  (eau propre). Points d'eau relevés à la pose puis toutes les heures de jeu ; relais retirés avec l'arrivée d'eau.

## Barils raccordés à la maison (`LWT_HouseBarrels`, `LWT_Reserve`, D28)

- Baril raccordable (`LWT_WaterObjects.isBarrel`) : objet du monde avec un `FluidContainer` d'au moins 20 L, ni point
  d'eau, ni relais, ni marqué par un autre mod (`LiveWireRelay`, `LiveWireBarrel`). Marque sur le baril :
  `LiveWaterBarrel = { inlet = "x,y,z", reserve }` (menus du client). Menu : `ContextMenu_LWT_ConnectBarrel`,
  `_DisconnectBarrel`, `_ReserveBarrel`, `_UseBarrel`.
- Zone : dans le bâtiment de l'arrivée d'eau ou juste au-dessus d'une de ses cases (toit), dans sa portée.
- Toutes les dix minutes, après les relais : les barils remplissent les relais qui servent un point d'eau raccordé ;
  gravité (un baril sert son niveau et ceux du dessous), levée par une pompe du réseau de l'arrivée d'eau ou le
  courant de la case du baril ; prorata de l'eau des barils, ceux en réserve en dernier ; un baril qui contient autre
  chose que de l'eau ne donne rien. Le réseau complète ensuite. Fluides gardés en proportion (`FluidContainer.Transfer`).

## Diagnostic d'un point d'eau (`LWT_Diagnosis`, `LWT_Diagnostics`, L09)

- Serveur, chaque pas, après les relais et les barils : une raison par arrivée d'eau, notée dans `LiveWaterRelay.why`
  de ses relais vides (effacée sur un relais qui a de l'eau) : `unfiltered`, `no_pressure`, `no_water`, `closed`
  (dernier pas du réseau, si une pompe est dans le réseau), `gravity`, `empty` (barils), `no_supply` (ni pompe ni
  baril).
- Client : au clic droit d'un point d'eau sans eau qui tire ou peut tirer sur une source extérieure, option grisée
  `ContextMenu_LWT_NoWater` (« Pas d'eau : %1 ») avec `IGUI_LWT_Why_NoInlet`, `_NotPlumbed`, `_Other`, `_<raison>` ou
  `_Waiting`.


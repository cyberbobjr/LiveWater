# LiveWater — spécifications techniques

Contrats précis du mod (objets, commandes réseau, ModData, options sandbox, traductions, API publique). Ils sont
écrits ici à mesure que les étapes du [plan 001](ADR-plans/termines/plan-001-reseau-eau-ouvert.md) les livrent.

## Identité

| Élément | Valeur |
|---|---|
| `id` | `batman_LiveWater` |
| Version minimale du jeu | 42.21 (cible 42.22) |
| `require=` | aucun |
| `incompatible=` | `\LGExtendedPlumbing,\LGMainsWater` |
| Table Lua globale | `LiveWater` |
| Préfixes | fichiers `LWT_*.lua`, recettes `LWT`, traductions `*_LWT_*`, ids de pièces `"<Mod>:<Nom>"` |

## API publique (`LiveWater.API`, révision 23)

Inscription depuis un fichier `shared`, pendant le chargement, avant `OnInitGlobalModData` (ensuite :
`registration_closed`). Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console.

| Fonction | Rôle | Raisons de refus |
|---|---|---|
| `registerPart(id, definition)` | type de pièce `"<Mod>:<Nom>"` | `invalid_id`, `duplicate_part`, `invalid_definition`, `invalid_sprites`, `duplicate_sprite`, `invalid_facings`, `invalid_crossings`, `invalid_sides`, `invalid_capabilities`, `unknown_capability`, `invalid_field` |
| `registerCapability(kind, implementation)` | nouvelle capacité ; `kind` nom simple ou `"<Mod>:<nom>"` ; `implementation.define(params)` obligatoire | `invalid_kind`, `duplicate_capability`, `invalid_implementation` |
| `part(id)` | copie de la définition contrôlée, ou `nil` | — |
| `registerSource(kind, definition)` | révision 6 : sorte de source d'eau `{ quality = "clean" ou "tainted", flag = drapeau IsoFlagType d'une case voisine, sprites = { sprite d'un objet voisin } }` (au moins `flag` ou `sprites`) ; `kind` nom simple ou `"<Mod>:<Nom>"` | `registration_closed`, `invalid_kind`, `duplicate_source`, `invalid_definition` |
| `revision` | entier ; 2 : champ `variants`, crochets `look`, `attach`, `power`, `powered`, `stepped`, `output`, `lines` ; 3 : réglage `item` du filtre, crochets `cartridge`, `fit`, `unfit`, `actions` ; 4 : réglages d'entretien de la pompe, crochets `switchable`, `switch`, `repairable`, `repair`, `sound` ; 5 : capacité `meter`, réglage `ports` de `conduit`, qualité par pièce dans le bilan de `stepped` ; 6 : `registerSource`, qualité de l'eau d'une prise selon la sorte de source relevée ; 7 : type de sortie en troisième résultat du crochet `outlet`, `outcome.outlet` de `stepped` (ce que le pas a fait d'une sortie), gardé comme état de la sortie ; 8 : capacité `spray`, crochets `spray`, `jet`, `opened`, `open` ; événement `valveChanged` émis par la commande `switchValve` ; 9 : minuterie (`controller` `timer` : `every`, `watts`, `choices`), crochets `prepare`, `opens`, `timer`, `setTimer`, `Parts:closed`, `choices` des actions, `ctx.hours` ; 10 : crochet `status` (vue du réseau ; une sortie rend son état), commandes `showNetwork` et `network` ; 11 : capacité `fitting`, crochets `draw`, `sense`, `fittingMode`, `setFittingMode`, fluide accepté en quatrième résultat de `outlet`, événement `waterDrawn`, qualité `fuel`, `registerContainer` ; 12 : `clean` de `registerContainer` ; 13 : champ `facings` de la définition, réglage `look` de `valve`, réglage `sound` de `spray` ; 14 : champ `crossings` de la définition (manchon de clôture, ADR-002), `Parts:crossing` ; 15 (ADR-004) : capacité `drip` (crochet `drip`), réglages `costGroup` et `byGravity` de `outlet` (crochets `costGroup`, `byGravity`), type de sortie `drip`, réglage `gravity` de `fitting` (crochet `gravity`), réglages `loss`, `noiseRadius`, `noiseVolume` de `spray` ; 16 (ADR-006) : réglage `flow` de `spray` (4e résultat du crochet `spray`) et de `drip` (2e résultat du crochet `drip`), `loss` de `spray` devenu part de l'eau prélevée, réglage `duration` de `controller` ; 21 (ADR-011) : capacité `vessel`, champ `intake.orVessel`, `GameSite:hasVessel()` ; 22 (ADR-012, ADR-013) : `registerOutlet`, type de sortie `"Mod:Nom"`, crochet `container` (en place de `fittingMode` et `setFittingMode`), crochets `gravity` et `byGravity`, champs `byGravity` des sorties et `gravity` du raccord retirés ; 23 (ADR-014) : champ `takes` de `outlet` (« water » par défaut, « fuel », « other », « any » ; quatrième résultat du crochet `outlet`), `vessel` tire aussi l'essence, `outcome.otherFluid` du crochet `stepped`, `info.takes` du crochet `sense` | — |
| `registerOutlet(outletType, handler)` | révision 22 (ADR-012 D04) : consommateur d'un autre mod ; `outletType` `"Mod:Nom"` (types réservés `houseInlet`, `sprinkler`, `drip`, `barrelFill`) ; `handler.need(part)` (litres voulus ce pas) et `handler.deliver(part, litres, quality)` obligatoires, `release(part)` et `cut(part)` facultatifs, appelés sur l'autorité | `registration_closed`, `invalid_type`, `invalid_handler`, `duplicate_outlet` |
| `registerContainer(name, definition)` | révision 11 : conteneur d'un raccord de remplissage, ou d'une pompe à eau qui y puise (révision 21, `vessel`), `name` = sprite de l'objet ou nom de son entité, `{ shape = "tall" ou "low" }` ; révision 12 : `clean` (ignoré depuis ADR-005 D07 : tout conteneur reçoit l'eau comme un baril) ; un conteneur inscrit est servi quelle que soit sa taille (`WaterDispenser` inscrit d'office) | `registration_closed`, `invalid_name`, `invalid_definition` |

Définition d'une pièce (copiée champ par champ, le reste est ignoré) : `sprites` (`{ [masque] = sprite }`, masques
0 à 15, redessinés selon les raccords), `variants` (révision 2 : `{ [clé] = { sprite S, E, N, O } }`, sprites
choisis par l'état de la pièce ; `sprites` devient facultatif), `facings` (révision 13 : `{ [masque] = orientation 1-4 }`,
l'orientation de la variante dessinée pour un masque : une pièce en ligne tournée selon son tuyau ; un masque sans
orientation garde celle affichée), `crossings` (révision 14 : `{ [masque] = { [bords] = sprite } }`, bords 1 = N,
8 = O, 9 = les deux, pris dans le masque : l'image d'une forme raccordée à travers une clôture portée par son propre
bord N ou O ; contrôlé, refus `invalid_crossings` ; ces sprites comptent parmi ceux du type ; lus par
`Parts:crossing(id, masque, bords)`, `nil` sans image), `sides` (masque des côtés
raccordables, 15 par défaut), `capabilities` (`{ kind = réglages ou true }`). Un sprite n'appartient qu'à un type
(formes et variantes). La variante affichée est la clé formée des jetons `look` des capacités dans l'ordre des noms
de capacité, joints par `_` (filtre `filter` + sortie `filtered` → `filter_filtered`, arrivée d'eau). Refus ajouté : `invalid_variants`.

| Capacité | Réglages (défaut) |
|---|---|
| `conduit` | `ports` facultatif 1-4 (révision 5 : pièce en ligne, 2 pour un compteur) |
| `meter` | aucun (révision 5) ; état `{ litres, quality }` du dernier pas |
| `intake` | `quality` : `"tainted"` (défaut) ou `"clean"` ; ne se pose qu'à côté d'une source (`attach`, refus `no_source`), dont la sorte est relevée dans son état (`source`) ; révision 21 : `orVessel` (faux) : se pose aussi contre un récipient (capacité `vessel`) sans source, son état porte alors `vessel = true` |
| `pump` | `ports` 1-4 (4), `pressure` (6), `flow` litres par pas de dix minutes à plein rendement (50, × rendement, × option `PumpFlowMultiplier`), `watts` en marche (250 ; 0 = sans courant) ; révision 4 : `wear` points de rendement perdus par minute de marche (0,01, × option `PumpWearMultiplier`), `breakdownBelow` (20), `breakdownChance` par pas de marche (0,02), `repairItem` (`Base.ScrapMetal`), `repairCount` (2), `repairTool` étiquette facultative, `sound` boucle en marche (`GeneratorLoop`), `noiseRadius` et `noiseVolume` (20, 20) |
| `vessel` | révision 21 (ADR-011) : `rate` litres par pas (50) ; la pièce tire l'eau du récipient posé contre elle, sur l'un de ses quatre côtés, avant sa propre source (hook `draw` : `min(litres, part du récipient)`) ; eau propre ou souillée ; révision 23 (ADR-014 D01) : aussi l'essence d'une pompe de station-service (`GameSite:hasVessel`), jamais une autre famille ; `container` = « draw » ; état `{ found, shape, fluid, amount, free, share, cx, cy, cz, offline }` ; ligne `IGUI_LWT_Vessel_Content` (« Baril : N L »), `sense` |
| `valve` | `open` à la pose (`true`) ; état `{ open }` ; révision 8 : `opened`, `open`, actions « Ouvrir la vanne » / « Fermer la vanne », ligne `IGUI_LWT_Valve_Open`/`_Closed` ; révision 13 : `look` (`false`) : pièce dessinée par l'état de la vanne, variantes `open` / `closed` ; crochet `status` : `closed` pour la vue du réseau |
| `spray` | révision 8 : `radius` cases de chaque côté sur chaque axe (2, × option `SprinklerRadiusMultiplier`, arrondi, 10 au plus ; zone carrée, distance de Tchebychev, ADR-003 D01 : rayon 2 → 5 × 5 cases), `dose` litres (0,2), `jetSheet`, `jetFirst`, `jetFrames` (6) : image f, orientation k = `jetSheet .. (jetFirst + 4 f + k)` ; révision 13 : `sound` facultatif (boucle des joueurs pendant l'arrosage ; arroseurs de LiveWater : `WaterCrops`) ; révision 15 : `loss` part de l'eau prélevée perdue en l'air, 0 à 1 (0,25 : sur 10 L, 7,5 L peuvent aller aux plantes, ADR-004 D03, ADR-006 D02 ; révision 16 : part de l'eau prélevée, plus « (1 + `loss`) fois l'eau donnée »), révision 16 : `flow` facultatif, litres prélevés par pas tant que la pièce est ouverte, 0 à 1000 (absent : option `SprinklerFlow`, 10 L ; ADR-006 D01), `noiseRadius` et `noiseVolume` 0 à 100 (10, 10 : bruit entendu par les zombies à chaque pas où elle arrose avec un son, crochet `sound`, ADR-004 D06) ; état `{ on }` (a arrosé au dernier pas) ; `look` `on`/`off` |
| `filter` | `capacity` litres par cartouche (500, × option `FilterCapacityMultiplier`, notée à la pose de la cartouche) ; `item` (révision 3) : type complet d'une cartouche amovible, le filtre n'agit que cartouche montée |
| `outlet` | `type` obligatoire ; `pressureCost` et `needsClean` : `houseInlet` 2 et vrai, `sprinkler` 1 et faux, `drip` 1 et faux (ADR-005 D03), autre type 1 et faux ; révision 15 (ADR-004 D04) : `costGroup` nom facultatif (les sorties servies d'un même groupe dans un réseau ne paient leur coût de pression qu'une fois par pas ; `drip` par défaut pour le type `drip`) ; révision 22 (ADR-012 D04) : `type` peut valoir `"Mod:Nom"`, consommateur d'un autre mod (`registerOutlet`), qui n'est servi que par une pompe ; état (révision 7) `{ state }` du dernier pas ; `look` `filtered` ou `unfiltered` pour une sortie qui exige de l'eau propre ; ligne `IGUI_LWT_Outlet_<état>` (`IGUI_LWT_Sprinkler_<état>` pour un arroseur, `IGUI_LWT_Drip_<état>` pour une ligne de goutte-à-goutte) ; révision 23 (ADR-014 D03) : `takes` (« water » par défaut, « fuel », « other », « any ») : le fluide que la sortie prend, quatrième résultat du crochet `outlet` ; un autre fluide dans les tuyaux donne l'état `wrong_fluid` (« Ce n'est pas de l'eau ») ; sans `takes`, eau seulement |
| `controller` | `mode` : `"manual"` (défaut) ou `"timer"` ; révision 9 : `every` heures (6), `watts` d'une minuterie (5), `choices` heures du menu (1, 2, 3, 4, 6, 8, 12, 24) ; révision 16 : `duration` pas de dix minutes, 1 à 144 (3 : 30 minutes, ADR-006 D03) ; état `{ every, slice, watering, left, powered }` ; une minuterie avec courant tient la pièce ouverte (`opens`) à chaque nouvelle tranche `floor(heures / every)` pendant `duration` pas, servie ou non (`left` : pas restants) ; lignes `IGUI_LWT_Timer_Every`, `IGUI_LWT_Timer_NoPower` |
| `fitting` | révision 11 : `rate` litres par pas (50) ; révision 22 (ADR-012 D02) : remplissage seul, `container` = « fill » ; état `{ found, shape (« tall » ou « low »), fluid, amount, free, cx, cy, cz, offline, blocked, state }` (`free` : place libre, partagée entre les raccords d'un même baril sur le pas, `LWT_Fittings` ; `blocked` = « feed » : une mangeoire pleine de nourriture ne reçoit rien, ADR-013 D04) ; sortie `barrelFill` (coût 1, place libre au plus, fluide du baril ; jamais d'eau propre exigée, l'eau versée est toujours croupie, ADR-005 D07, l'essence reste de l'essence) ; `look` `fill`, `fill_low` ; révision 23 (ADR-014 D04) : remplit un récipient vide avec le fluide transporté, un récipient d'eau avec de l'eau seulement, un récipient d'essence avec de l'essence seulement ; jamais une mangeoire avec autre chose que de l'eau, jamais une pompe de station-service |
| `drip` | révision 15 (ADR-004) : `dose` litres (0,2) ; arrose les cases voisines (N, E, S, O) auxquelles la pièce n'est pas raccordée, jamais sa propre case, sans perte (`LWT_DripArea`) ; aucun son ; révision 16 : `flow` facultatif, litres prélevés par case et par pas quand le réseau la sert, 0 à 100 (absent : option `DripFlow`, 0,5 L ; ADR-006 D01) |

Crochets d'une capacité (tous facultatifs sauf `define`), appelés avec les réglages contrôlés puis l'état de la
pièce pour cette capacité (`part.data[kind]`, éventuellement `nil`) : `carries` (l'eau traverse), `blocks` (coupe
l'eau, vanne fermée), `pressurizes` (l'eau part de là), `ports` (nombre maximal de tuyaux raccordés), `supply`
(pression et litres par pas), `source` (qualité `"clean"` ou `"tainted"`, `nil` à sec), `outlet` (coût de pression,
eau propre exigée), `purifies` (le filtre agit), `wear(p, d, litres)` (écrit son état). Révision 2 : `look` (jeton de la variante), `attach(p, d, place)` (la place convient-elle ? `true`, ou
`false` et une raison ; peut relever ce qu'elle trouve), `power` (besoin de courant, watts tirés maintenant),
`powered(p, d, oui)` (l'autorité dit si la pièce a du courant pour ce pas), `stepped(p, d, bilan, ctx)` (fin de pas :
`bilan.through` = litres passés par la pièce, `bilan.quality`), `output` (litres donnés au dernier pas), `lines`
(lignes d'information `{ clé, arg…, rank = n }`). `supply`, `purifies` et `wear` reçoivent en dernier le contexte du
pas (`ctx.scale(nom)` : multiplicateur sandbox). Révision 3 : `cartridge(p, d, ctx)` (objet de la cartouche, montée
ou non, part restante 0-1), `fit(p, d, part, ctx)`, `unfit(p, d)`, `actions(p, d)` (actions du menu : `{ command,
key, item }`, `item` = objet à porter). Révision 4 : `switchable` (position de l'interrupteur, ou `nil`), `switch(p, d, oui)`, `repairable` (matériau, nombre, outil, raison du refus `running` ou `not_needed` ou `nil`), `repair`, `sound` (nom de la boucle, rayon et volume du bruit tant que la pièce en fait). Révision 21-22 : `draw(p, d)` (eau que la pièce tire d'un récipient voisin, capacité `vessel`), `container(p, d)` (« fill » ou « draw » : ce que fait `LWT_Fittings` du récipient), `sense`, `lines`. Révision 22 : `fittingMode`, `setFittingMode`, `gravity` et `byGravity` supprimés.

Sortes de source d'eau (`LiveWater.Sources`, publiques par `registerSource` en révision 6) : `water` (eau
naturelle : drapeau `water` d'une des 8 cases voisines, eau croupie), `well` (puits vanilla : objet `camping_01_16`
sur une des 8 cases voisines, eau propre). Une sorte est une donnée `{ quality, flag?, sprites? }` ; les sortes
propres sont essayées d'abord. La prise (`intake`) relève la sorte à la pose (`source`) et donne sa qualité ; une
sorte qui n'est plus inscrite donne le réglage `quality` de la capacité.

## Pièces de LiveWater

| Id | Sprites | Capacités |
|---|---|---|
| `LiveWater:PipeGalvanized` | `batman_livewater_01_<masque>`, masques 0 à 15 ; `crossings` : 104-123 (manchon nord, ouest ou les deux, contrat des tuiles) | `conduit` ; meuble `Base.Mov_LiveWater_Pipe` (`CustomItem` des 16 tuiles), posé au curseur et ramassé à la clé comme les autres pièces |
| `LiveWater:FlowMeter` | `sprites` : 20 (masques 2, 8, 10), 21 (masques 1, 4, 5) ; seul ou en coude, garde le sprite de sa pose | `conduit` (2 ports), `meter` |
| `LiveWater:Valve` | `variants` : `open` 17 (S, `ns`), 16 (E, `ew`), `closed` 19, 18 ; `facings` : masques 2, 8, 10 → E, 1, 4, 5 → S ; seule ou en coude, garde l'axe affiché | `conduit` (2 ports), `valve` (ouverte à la pose, `look`), `controller` (`manual`) |
| `LiveWater:HouseInlet` | `variants` : `filtered` 40-43, `unfiltered` 44-47 ; cartouche montée (ADR-005 D04) : `filter_filtered` 176-179, `filter_unfiltered` 180-183 (S, E, N, O) ; clé = jetons de `look` joints dans l'ordre des capacités : `filter` (cartouche montée) puis `outlet` | `filter` (`LiveWater.WaterFilter`, 500 L, ADR-005 D01), `outlet` (`houseInlet`) |
| `LiveWater:Sprinkler` | `variants` : `off` 48-51, `on` 52-55 (S, E, N, O) ; jet 128-159 dessiné par le client (8 images d'un tour complet × 4 orientations, ADR-003 D03 ; 80-103 inutilisées) | `outlet` (`sprinkler`), `valve` (fermée à la pose), `controller` (`manual`), `spray` (rayon 2, 0,2 L, perte 0,25, bruit 10 / 10) |
| `LiveWater:SprinklerAuto` | `variants` : `off` 56-59, `on` 60-63 (S, E, N, O) ; jet 128-159 | comme `LiveWater:Sprinkler`, `controller` `timer` (6 h, 5 W) |
| `LiveWater:BarrelFitting` (« Raccord de remplissage ») | `variants` : `fill` 64-67, `fill_low` 68-71 (S, E, N, O ; raccordements 184-236 ; tuiles 72-75 de l'ancien mode Pomper inutilisées) | `fitting` (50 L, remplissage seul) |
| `LiveWater:DripLine` | `batman_livewater_01_<160 + masque>`, masques 0 à 15 (tuiles 160-175, brun clair, plus fines que le tuyau) ; pas de manchon de clôture | `conduit`, `outlet` (`drip`), `drip` (0,2 L) ; meuble `Base.Mov_LiveWater_DripLine`, posé au curseur comme un tuyau, une par case, ramassé à la main (ADR-004 D01) |
| `LiveWater:PondPump` (« Pompe à eau ») | `variants` : `off` 24-27, `on` 28-31 (S, E, N, O) ; 32-39 inutilisées depuis l'ADR-005 D02 | `intake` (`orVessel`), `pump` (4 ports, pression 6, 50 L, 250 W, réparation 2 `Base.ScrapMetal` + `base:wrench`, boucle `GeneratorLoop`), `vessel` (`rate` 50, ADR-011) |

## Objets et recettes

| Élément | Contrat |
|---|---|
| `Base.Mov_LiveWater_Pipe` | `media/scripts/LWT_moveables.txt`, `base:moveable`, 0,4 kg, `WorldObjectSprite = batman_livewater_01_10` (droit est-ouest) ; objet `CustomItem` des tuiles 0-15 et 104-123 (`IsMoveAble`, `PickUpWeight` 4, `PickUpTool`/`PlaceTool` `Wrench`, sans `Facing`) ; un par case de tuyau, règles de `LWT_PlaceRules` |
| `LWTCutPipeSections` | `media/scripts/LWT_recipes.txt` : 1 `Base.MetalPipe` et un outil `tags[base:metalsaw]` gardé donnent 4 `Base.Mov_LiveWater_Pipe` (action `SawSmallItemMetal`) |
| `LiveWater.WaterFilter` | `base:normal`, 0,5 kg, icône `Item_LWT_WaterFilter`, `ConditionMax = 100` : l'état est la part restante (100 neuve) ; infobulle `Tooltip_LWT_WaterFilter` |
| `LWTMakeWaterFilter` | action `Making`, 2 `tags[base:charcoal]`, 2 `Base.RippedSheets` → 1 `LiveWater.WaterFilter` |
| `Base.Mov_LiveWater_FlowMeter` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_20` (objet `CustomItem` des tuiles 20-21) |
| `Base.Mov_LiveWater_Valve` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_16` (objet `CustomItem` des tuiles 16-19) |
| `LWTBuildValve` | action `Making` : clé anglaise gardée, 1 `Base.Mov_LiveWater_Pipe`, 1 `Base.ScrapMetal` → 1 `Base.Mov_LiveWater_Valve` |
| `LWTBuildFlowMeter` | action `Making` : tournevis gardé, 1 `Base.Mov_LiveWater_Pipe`, 1 `Base.SmallSheetMetal`, 2 `Base.Screws` → 1 `Base.Mov_LiveWater_FlowMeter` |
| `Base.Mov_LiveWater_HouseInlet` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_40` (objet `CustomItem` des tuiles 40-47) |
| `LWTBuildHouseInlet` | action `Making` : clé à tuyau gardée, 2 `Base.Mov_LiveWater_Pipe`, 1 `Base.SmallSheetMetal`, 4 `Base.Screws` → 1 `Base.Mov_LiveWater_HouseInlet` |
| `Base.Mov_LiveWater_Sprinkler` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_48` (tuiles 48-55) |
| `LWTBuildSprinkler` | action `Making` : clé à tuyau gardée, 2 `Base.Mov_LiveWater_Pipe`, 1 `Base.ScrapMetal`, 1 `Base.Plank` → 1 `Base.Mov_LiveWater_Sprinkler` |
| `Base.Mov_LiveWater_SprinklerAuto` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_56` (tuiles 56-63) |
| `LWTUpgradeSprinkler` | Électricité 2, action `MakingElectrical` : tournevis gardé, 1 `Base.Mov_LiveWater_Sprinkler`, 2 `Base.ElectronicsScrap`, 1 `Base.ElectricWire` → 1 `Base.Mov_LiveWater_SprinklerAuto` ; 10 XP d'Électricité |
| `Base.Mov_LiveWater_BarrelFitting` | `base:moveable`, `WorldObjectSprite = batman_livewater_01_64` (tuiles 64-75) |
| `LWTBuildBarrelFitting` | action `Making` : clé à tuyau gardée, 1 `Base.Mov_LiveWater_Pipe`, 1 `Base.RubberHose` → 1 `Base.Mov_LiveWater_BarrelFitting` |
| `Base.Mov_LiveWater_DripLine` | `base:moveable`, 0,2 kg, `WorldObjectSprite = batman_livewater_01_170` (ligne droite est-ouest) ; objet `CustomItem` des tuiles 160-175, sans outil pour poser ni ramasser ; « Ligne de goutte-à-goutte » / « Drip Line » |
| `LWTMakeDripLine` | catégorie `Farming`, action `Making` : 1 `Base.RubberHose`, 2 utilisations de `Base.DuctTape`, un outil `tags[base:sharpknife]` gardé → 4 `Base.Mov_LiveWater_DripLine` (ADR-004 D07) |
| `Base.Mov_LiveWater_PondPump` | `media/scripts/LWT_moveables.txt`, `base:moveable`, `WorldObjectSprite = batman_livewater_01_24` (objet `CustomItem` des tuiles 24-39) |
| `LWTBuildPondPump` | Électricité 2, action `MakingElectrical` : tournevis et clé gardés, 1 `Base.MetalPipe`, 2 `Base.SmallSheetMetal`, 3 `Base.ElectronicsScrap`, 2 `Base.ElectricWire`, 4 `Base.Screws` → 1 `Base.Mov_LiveWater_PondPump` ; 15 XP d'Électricité |
| `LWTDismantle<Pièce>` | `media/scripts/LWT_dismantle.txt`, une recette par équipement (ADR-007 D01, D03), tirée de la table `shared/LiveWater/LWT_Dismantle.lua` (`tests/test_dismantle.py` vérifie l'accord) ; outil gardé, objet détruit : |
| — `Pipe` | clé à tuyau ou clé (`tags[base:pipewrench;base:wrench]`), `Assembly`, `Making`, 60 → 1 `Base.IronPiece` |
| — `Valve` | clé, 100 → 1 `Base.ScrapMetal`, 1 `Base.IronPiece` |
| — `FlowMeter` | clé, 100 → 2 `Base.IronPiece`, 1 `Base.Screws` |
| — `HouseInlet` | clé, 150 → 1 `Base.ScrapMetal`, 1 `Base.IronPiece`, 2 `Base.Screws` |
| — `Sprinkler` | clé, 100 → 1 `Base.ScrapMetal`, 2 `Base.IronPiece` |
| — `BarrelFitting` | clé, 80 → 1 `Base.IronPiece` |
| — `PondPump` | tournevis (`tags[base:screwdriver]`), `Electrical`, `DismantleElectrical`, 200 → 2 `Base.ScrapMetal`, 2 `Base.Screws`, 2 `Base.ElectronicsScrap`, 1 `Base.ElectricWire` |
| — `SprinklerAuto` | tournevis, 150 → 1 `Base.ScrapMetal`, 2 `Base.IronPiece`, 1 `Base.ElectronicsScrap`, 1 `Base.ElectricWire` |
| — `DripLine` | couteau (`tags[base:sharpknife]`), `Assembly`, `Making`, 40 → 1 `Base.RubberBand` |
| — `WaterFilter` | couteau, 40, cartouche usée acceptée (`AllowDestroyedItem`) → 1 `Base.RippedSheets` |
| Matériaux `LiveWater<Pièce>` | `shared/LiveWater/LWT_GameScrap.lua`, à `OnGameBoot` (après `ISMoveableDefinitions.load` vanilla) : `addScrapDefinition` (outils `Base.PipeWrench`/`Base.Wrench`, Entretien, 300, `RepairWithWrench`, chance de base 40 ; ou `Base.Screwdriver`, Électricité, 500, `Dismantle`, 20) et `addScrapItem` statiques, chance 100 par tirage, quantité divisée par le facteur de `ScrapSize` (`Small` ×2, `Large` ÷2) : à pleine chance, les objets de la recette, jamais plus. Tuiles : `CanScrap`, `Material = LiveWater<Pièce>`, `ScrapSize` (`Small` tuyau, vanne, compteur, raccord, arroseur ; `Medium` arrivée d'eau, arroseur automatique ; `Large` pompe) ; goutte-à-goutte sans démontage sur place |
| Butin | `server/LiveWater/LWT_Loot.lua`, à `OnPreDistributionMerge`, ajout en fin de `ProceduralDistributions.list.<Liste>.items` (liste absente ignorée, rien de remplacé ; ADR-007 D04) : `PlumbingSupplies`, `CrateTools`, `GarageTools`, `ToolStoreTools` ← `Base.Mov_LiveWater_Pipe` 2, `Base.Mov_LiveWater_Valve` 1, `Base.Mov_LiveWater_BarrelFitting` 1 ; `GardenStoreTools`, `GardenStoreMisc`, `CrateGardening`, `GigamartFarming`, `ToolStoreFarming` ← `Base.Mov_LiveWater_Sprinkler` 1, `Base.Mov_LiveWater_DripLine` 2, `LiveWater.WaterFilter` 1 |

## Options sandbox (`media/sandbox-options.txt`, page `LiveWater`)

| Option | Type, bornes, défaut | Effet |
|---|---|---|
| `LiveWater.PumpFlowMultiplier` | double 0,1-10, 1,0 | multiplie le débit des pompes (`flow`) |
| `LiveWater.FilterCapacityMultiplier` | double 0,1-10, 1,0 | multiplie les litres d'une cartouche (`capacity`) |
| `LiveWater.PumpWearMultiplier` | double 0-10, 1,0 | multiplie la perte de rendement en marche (`wear`) ; 0 = aucune usure |
| `LiveWater.InletRange` | entier 1-100, 20 | portée (cercle, en cases) d'une arrivée d'eau dans le bâtiment qu'elle touche |
| `LiveWater.BaseRange` | entier 1-50, 12 | portée d'une arrivée d'eau hors bâtiment de la carte (base du joueur, L11) |
| `LiveWater.WasherFix` | booléen, vrai | correctif des lave-linge raccordés en multijoueur (L13, E28) |
| `LiveWater.FillContainers` | chaîne, `WaterDispenser` | noms d'entités ou de sprites séparés par `;` : conteneurs qu'un raccord de remplissage sert quelle que soit leur taille, avec de l'eau croupie comme un baril (L08, ADR-005 D07) |
| `LiveWater.SprinklerTimerMin` | entier 1-168, 1 | intervalle le plus court d'une minuterie d'arroseur (heures) |
| `LiveWater.SprinklerTimerMax` | entier 1-168, 24 | intervalle le plus long d'une minuterie d'arroseur (heures) |
| `LiveWater.SprinklerRadiusMultiplier` | double 0,5-5, 1,0 | multiplie le rayon des arroseurs (2 cases, arrondi, 10 au plus) |
| `LiveWater.SprinklerFlow` | double 0-100, 10,0 | litres prélevés par un arroseur ouvert à chaque pas de dix minutes, que les plantes aient soif ou non (ADR-006 D02) |
| `LiveWater.DripFlow` | double 0-10, 0,5 | litres prélevés par case de ligne de goutte-à-goutte servie à chaque pas (ADR-006 D02) |

Traductions `Sandbox_LWT_<Option>` et `_tooltip` dans `Sandbox.json`, onglet `Sandbox_LiveWater`.

## Électricité (`LWT_Power`, D20)

- Avec Live Wire (`LiveWire.API.revision >= 6`), à `OnInitWorld`, sur l'autorité : un consommateur par type de pièce
  qui a le crochet `power`, id `LiveWater_` suivi de l'id du type où `:` devient `_` (`LiveWater_LiveWater_PondPump`),
  `sprites` = tous les sprites du type, catégorie `other`, circuit `equipment`. `powerConsumption(o)` : watts de
  l'état recopié (250 en marche, 0 arrêtée). `display(o)` : `{ lines }`, les 4 premières lignes d'information (sans
  `name`). `summary(objets)` : `{ "IGUI_LWT_LW_Pumps", en marche, total }` (pompes seulement : les pièces qui mettent sous pression), `{ "IGUI_LWT_LW_Flow", litres }`.
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
| client → serveur | `fitFilter` | `x`, `y`, `z` entiers | arguments (`invalid`), pièce (`nothing_here`), emplacement de cartouche (`no_filter_slot`), portée (`too_far`), cartouche dans l'inventaire (`no_cartridge`) | cartouche prise (son état = part restante) ; l'ancienne ressort d'abord (rendue avec sa part restante, ou en cartouche usée `LiveWater.WaterFilterSpent` si épuisée, ADR-009 D01) |
| client → serveur | `removeFilter` | `x`, `y`, `z` entiers | mêmes contrôles jusqu'à la portée, puis cartouche montée (`no_filter`) | cartouche rendue avec sa part restante, ou en cartouche usée `LiveWater.WaterFilterSpent` si épuisée (ADR-009 D01) |
| client → serveur | `switchPump` | `x`, `y`, `z` entiers | arguments, pièce, interrupteur (`not_switchable`), portée | interrupteur basculé ; éteinte, la pompe s'arrête aussitôt |
| client → serveur | `repairPump` | `x`, `y`, `z` entiers | arguments, pièce, réparable (`not_repairable`), à l'arrêt (`running`), usée ou en panne (`not_needed`), portée, outil (`need_wrench`), matériau (`no_parts`) | matériau consommé, rendement 100 %, panne effacée |
| client → serveur | `cityWater` | `x`, `y`, `z` entiers | arguments, point d'eau posé par un joueur et pas raccordé (`not_fixture`), portée, pièce d'un bâtiment de la carte (`not_map_building`), eau de la ville qui coule et case sans `isNoWater` (`no_city_water`) | ModData `canBeWaterPiped` effacée, `setUsesExternalWaterSource(false)`, `transmitModData` : point d'eau d'origine (M01) |
| client → serveur | `switchValve` | `x`, `y`, `z` entiers | arguments, pièce, vanne (`not_valve`), portée | vanne ouverte ou fermée, `valveChanged` |
| client → serveur | `setTimer` | `x`, `y`, `z`, `hours` entiers | arguments (`invalid`), pièce, minuterie (`not_timer`), bornes sandbox (`out_of_bounds`), portée | intervalle de la minuterie |
| client → serveur | `showNetwork` | `x`, `y`, `z` entiers | arguments, pièce (`nothing_here`), portée | réponse `network` au seul joueur |
| serveur → client | `network` | `parts` = liste de `{ x, y, z }` (500 au plus) | — | surbrillance persistante des pièces de ces cases (`LWT_NetworkView`) |
| client → serveur | `removeLiveWater` | aucun | administrateur (`not_admin` ; rôle `UseDebugContextMenu` sur un serveur, toujours en solo) | retrait de LiveWater du monde (`LWT_Removal`), note `IGUI_LWT_Removing` |
| serveur → client | `jet` | `x`, `y`, `z` | — | le client relit l'état recopié des pièces de la case et anime ou arrête le jet (D08a) |
| serveur → client | `sound` | `x`, `y`, `z`, `name` (absent = arrêt) | — | boucle jouée ou arrêtée localement (en solo, par `triggerEvent`) |
| serveur → client | `notice` | `key` (clé de traduction) | — | note au-dessus du joueur (en solo, affichée directement) |

Clés des refus (`IG_UI.json`, table partagée `LWT_Reasons`) : `IGUI_LWT_NoSource` (`no_source`), `IGUI_LWT_NoFilter` (`no_cartridge`), `IGUI_LWT_NoFilterFitted` (`no_filter`), `IGUI_LWT_NoFilterSlot` (`no_filter_slot`), `IGUI_LWT_StillRunning` (`running`), `IGUI_LWT_NotNeeded` (`not_needed`), `IGUI_LWT_NeedWrench` (`need_wrench`), `IGUI_LWT_NoScrap` (`no_parts`), `IGUI_LWT_Invalid`, `IGUI_LWT_TooFar` (`too_far`),
`IGUI_LWT_Occupied`, `IGUI_LWT_PortsFull`, `IGUI_LWT_NeedTool`,
`IGUI_LWT_NothingHere`, `IGUI_LWT_NotFixture` (`not_fixture`), `IGUI_LWT_NotMapBuilding` (`not_map_building`), `IGUI_LWT_NoCityWater` (`no_city_water`), autre raison `IGUI_LWT_Refused`. Menu des pièces : `ContextMenu_LWT_FitFilter`, `ContextMenu_LWT_ReplaceFilter`, `ContextMenu_LWT_RemoveFilter`, `ContextMenu_LWT_TurnOn`, `ContextMenu_LWT_TurnOff`, `ContextMenu_LWT_Repair`, `ContextMenu_LWT_Info` (infobulle : lignes d'information traduites, `IGUI_LWT_Pump_*`, `IGUI_LWT_Filter_*`, `IGUI_LWT_Source_<sorte>`).

## Registre persistant (ModData globale `LiveWater`, `LWT_Registry`)

Table `ModData.getOrCreate("LiveWater")`, lue sur l'autorité à chaque `OnInitGlobalModData` (jamais gardée d'une
partie à l'autre) ; le graphe en est reconstruit à ce moment.

| Clé | Contenu |
|---|---|
| `seq` | dernier ordre de pose attribué (jamais réutilisé) |
| `parts["x,y,z"]` | entrée d'une pièce posée |
| `relays["x,y,z"]` | relais d'une arrivée d'eau (clé de sa case) : `{ ["x,y,z"] = { x, y, z } }` |
| `orphans["x,y,z"]` | relais à retirer dès que sa case est chargée : `{ x, y, z, owner }` |

Entrée : `v` (version du schéma, 1), `type` (id `"<Mod>:<Nom>"`), `x`, `y`, `z`, `order` (ordre de pose), `data`
(`{ [capacité] = état }`, par exemple `valve = { open = false }`, `filter = { used = 120 }`, `intake = { source =
"water" ou "well" }`, `pump = { on, powered, running, litres, efficiency, broken }`, `meter = { litres, quality }`), `cuts` (ADR-002 :
masque des côtés de la case qu'un mur plein coupe, absent quand aucun ; noté à la pose et quand un mur ou une clôture
change autour). Tout autre champ est conservé tel quel. Une pièce dont le type n'est pas inscrit reste dans le registre, inerte. Refus d'ajout :
`unknown_part`, `occupied`.

États d'une sortie après un pas (`LWT_Flow`) : `served`, `idle` (aucun besoin ; une sortie d'arrosage, dont le besoin est son débit, ADR-006 D01, ne l'est qu'à débit 0), `closed`, `no_water`, `unfiltered`
(« eau non filtrée »), `no_pressure` (« sans pression »), `wrong_fluid` (la sortie ne prend pas ce fluide). Familles
de fluides (`Flow.family`, ADR-005 D03) : `clean` et `tainted` = eau, `fuel` = essence, toute autre qualité = `other` ;
une sortie sans 4e résultat à `outlet` (maison, arroseur, goutte-à-goutte) ne prend que l'eau ; un filtre ne purifie
que l'eau. Les sorties d'un même `costGroup` ne paient leur coût de pression qu'une fois par pas (la première servie). Seul un
producteur met l'eau dans le réseau (ADR-012 D01) : un réseau sans pompe ne donne rien, ses sorties sont `no_pressure`.
Une pompe qui touche un baril (capacité `vessel`) puise d'abord dans ce baril, jusqu'à son débit (`rate`, 50 L par pas),
eau propre ou souillée seulement, jamais de carburant ; sa source naturelle (étang, puits) ne sert qu'ensuite, baril vide.
Une pompe ne tire que sa propre source : aucune autre pompe ne vide son baril. Deux pompes d'un même réseau additionnent
leurs litres, la qualité est mélangée (souillée si l'une l'est). Révision 23 (ADR-014 D02) : un seul fluide par réseau, par zone et par pas ; `LWT_Flow:supply` retient la famille de la première pompe de la zone, dans l'ordre de pose, et une pompe d'une autre famille ne donne rien ce pas (`outcome.otherFluid`, ligne `IGUI_LWT_Pump_OtherFluid`). Zones (ADR-001 D02, D15) : les départs d'eau qui se
rejoignent par des pièces ouvertes (un tuyau ou une sortie atteints depuis deux pompes, sans vanne fermée entre elles)
forment une zone ; chaque zone sert ses sorties avec sa propre pression et sa propre eau, ses pompes sont créditées de leur part de l'eau qu'elle a servie : deux pompes de part et d'autre d'une vanne fermée
servent chacune leur côté. Un réseau resté sans départ d'eau (pompe ramassée, mur construit) n'est jamais avancé par
l'horloge : à `networkChanged`, ses pièces reçoivent un bilan vide une fois (`Clock:settle` : plus aucune sortie
`served`, l'arroseur s'arrête).

Masque de raccord : N = 1, E = 2, S = 4, O = 8 ; le sprite affiché est `sprites[masque]`, sinon `sprites[0]`.

Événements `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` (rendent `true`, ou `false` et `unknown_event`,
`invalid_handler`), émis sur l'autorité : `partAdded` (entrée), `partRemoved` (entrée), `networkChanged` (id du
réseau ; au retrait, une fois par réseau resté raccordé), `waterDelivered` (pièce, litres, qualité ; à chaque pas de
dix minutes, par sortie servie), `valveChanged`. La reconstruction au chargement n'émet rien.

## Murs et clôtures (ADR-002)

- Règle : un mur plein sur le bord commun de deux cases coupe le raccord ; c'est la règle du moteur
  `IsoGridSquare.hasNonHoppableWall`, lue sur la case qui porte le bord : drapeaux `cutN`/`cutW`, `WallN`/`WallW`,
  `WallNTrans`/`WallWTrans`, `WallNW`, ou une fenêtre ; une porte dans un mur compte comme un mur. Les clôtures
  (`HoppableN`/`W` basses, `TallHoppableN`/`W` hautes et palissades, portails) laissent passer le tuyau dessous.
  L'arrivée d'eau de la maison reste la seule entrée de l'eau dans un bâtiment.
- `LWT_Grid.edgeOf(x, y, côté)` : case qui porte le bord d'un côté et `true` pour son bord N (sinon O) ; une case ne
  porte que ses bords N et O.
- Port monde (`LWT_GameWorld`) : `edge(x, y, z, nord)` → `"wall"`, `"fence"` ou `nil` (bord N ou O de la case,
  `nil` hors chargement) ; `isEdgeObject(objet)` (objet de bord : mur, clôture) ; `without(objet, fn)` (`fn()` comme
  si l'objet était parti, pour un objet sur le point d'être retiré).
- Graphe (`LWT_Network`) : il lit seulement `cuts` et `apart` de l'entrée (les cases lointaines ne sont pas chargées
  au chargement du monde) ; deux voisins dont l'un coupe le côté commun ne se raccordent pas. `apart` (ADR-006 D05) :
  masque des côtés tenus à part parce qu'un raccord apparu là (mur démoli) dépasserait les ports d'une des deux
  pièces ; noté sur la pièce posée en dernier, gardé dans le registre (même graphe à la reconstruction), effacé quand
  la voisine de ce côté part (`Network:forget`).
- Topologie (`LWT_Topology`) : `cutsAt(x, y, z)` (masque des côtés coupés, 0 sans port), `recordCuts(entrée)` (à la
  pose), `relink(x, y, z)` (coupures de la case et de ses voisines nord et ouest, les seules qui partagent un bord
  qu'elle porte, notées à nouveau ; raccords et réseaux jugés à nouveau, sprites autour, `networkChanged`), `refreshCuts(isLoaded)` (coupures de chaque pièce sur une case chargée jugées à nouveau ; une
  pièce changée est reliée à nouveau). Les deux passent à `Network:relink` les masques des liens d'avant
  (`masksAround`) : un lien nouveau qui dépasse un port n'est pas fait (`holdPorts`, liens les plus récents jugés
  d'abord, la pièce posée en dernier reçoit `apart`, ADR-006 D05). `LWT_Placement:edgeChanged(x, y, z)` appelle `relink`.
- Événements : `OnObjectAdded` d'un objet de bord relie aussitôt ; `OnObjectAboutToBeRemoved` aussi, traité « comme
  parti » par `world:without`. Le jeu n'émet aucun événement quand un joueur construit un mur ou une clôture en solo :
  la tâche d'horloge `edgeWatch` lance `refreshCuts` toutes les dix minutes.
- Manchon (`LWT_Sprites:crossed`) : côtés N et O raccordés d'une case qui traversent une clôture portée par cette case
  (0, 1, 8 ou 9, lu par le port monde `edge`) ; la pièce prend alors `Parts:crossing`, sinon l'image de son masque.

Tâches de l'horloge (`chores` de `LWT_Clock`, avant les réseaux, au même pas `EveryTenMinutes`) : retrait
(`LWT_Removal`), relais des arrivées d'eau (`LWT_Relays`), diagnostic, correctif des
lave-linge, raccords de remplissage, `edgeWatch` (murs et clôtures).

## Réseaux hors chargement (ADR-006 D06-D08)

- Horloge : à chaque pas de dix minutes, tout réseau qui a un départ d'eau est avancé, chargé ou non (coût : une
  distribution par réseau, bornée par le registre ; aucun nouvel abonnement). Un réseau sans départ d'eau ne l'est
  jamais (`Clock:settle`).
- Prise d'eau (`intake`) : qualité de la sorte de source notée à la pose (`data.intake.source`), aucune lecture du
  monde : une mare ou un puits donne de l'eau hors chargement.
- Pompe contre un baril et raccord de remplissage : si la case de l'un ou de son conteneur n'est pas chargée, la pompe donne au plus le contenu
  relevé (`amount`, `share`), le raccord de remplissage prend au plus la place relevée (`free`) ; chaque pas décompte dans l'état
  (`Fittings:count` → crochet `sense`) et cumule `offline = { taken, added, quality }`. Au `LoadChunk` qui couvre le
  raccord ou son conteneur (seuls les raccords en attente, `pending`, sont regardés), sinon au premier pas chargé,
  `offline` est écrit une fois dans le vrai conteneur (`take` puis `add`, bornés par ce qu'il contient et sa place :
  aucune eau créée), puis le relevé normal reprend.
- Plantes : `LWT_GameFarming` passe par l'objet global vanilla (`SFarmingSystem.instance:getLuaObjectAt`,
  `SPlantGlobalObject:water` : `waterLvl`, `lastWaterHour`, `saveData` n'écrit l'objet iso que s'il est chargé ; les
  champs sont gardés par le système d'objets globaux, `setObjectModDataKeys`, et recopiés sur l'objet au chargement).
- Arrivée d'eau de la maison : besoin 0 tant que sa case n'est pas chargée (les relais attendent le retour).
- Présentation : `Publisher:present` n'écrit rien pour une case non chargée (image, état recopié, son, bruit, jet) ;
  la pièce attend dans `away` ; `LoadChunk` → `Publisher:chunkLoaded` la présente avec son état du moment (images,
  état recopié, ordre `jet` si l'arroseur a changé).
- Courant hors chargement (`LWT_Power:powered`) : sur une case chargée, la lecture normale (Live Wire
  `consumerPowered`, sinon générateur ou réseau de la case) est notée dans l'état de la pièce sous la clé `_power`
  (`{ generator, grid, live }` ; une sorte de capacité commence par une lettre : aucune collision). Hors chargement :
  avec Live Wire (`LiveWire.API.gridAt(x, y, z)`, autorité, lit seulement le registre de Live Wire, copie de
  l'instantané, `LW_API.lua`), courant si `inverter.powered` et si le dernier `consumerPowered` chargé ne l'a pas
  refusé (circuit, disjoncteur) ; sans réseau Live Wire (`nil`) : générateur à portée au dernier pas chargé, sinon
  réseau de la ville s'il passait sur la case au dernier pas chargé et s'il marche encore dans le monde
  (`getSandboxOptions():doesPowerGridExist()`, `SandboxOptions.java:1223` : âge du monde en jours ≤
  `ElecShutModifier`). Le générateur n'est ni lu ni touché hors chargement. De retour sur une case chargée, la lecture
  normale reprend dès le premier pas (D08).
- Port monde (`LWT_GameWorld`) : `powerAt(x, y, z)` → générateur (`haveElectricity`), réseau (`hasGridPower`), `nil`
  hors chargement ; `gridRuns()`.

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
  (eau propre). Points d'eau relevés sur événement seulement (D10) : à la pose ou au rechargement de l'arrivée d'eau, à la pose ou au retrait d'un point d'eau ou d'un réservoir à portée (`OnObjectAdded`, `OnObjectAboutToBeRemoved`), au chargement d'un chunk à portée (`LoadChunk`) et à la coupure de l'eau de la ville, au plus un relevé par pas ; en mode base, jamais les points d'eau d'un bâtiment de la carte ; relais retirés avec l'arrivée d'eau.

## Barils, raccord de remplissage et maison (ADR-009 D03, ADR-011 à 013)

- Le raccord de remplissage (`LiveWater:BarrelFitting`, EN « Fill Fitting ») ne fait que remplir, depuis le réseau, le
  baril, le récupérateur d'eau de pluie ou la mangeoire vanilla posée contre lui (ADR-012 D02, ADR-013 D02, D03) ; il ne
  donne jamais d'eau et ne dépasse pas la place libre. L'eau y entre souillée. Une mangeoire pleine de nourriture ne
  reçoit rien (« La mangeoire contient de la nourriture ») ; le remplissage reprend quand elle est vide (ADR-013 D04).
- Un baril ne rejoint le réseau que par une pompe à eau posée contre lui (ADR-011 D01, D02). Sans pompe dans le réseau,
  rien ne sort : l'arrivée d'eau, les arroseurs et le goutte-à-goutte n'ont rien. Le baril vanilla posé au-dessus d'un évier reste au jeu.

## Diagnostic d'un point d'eau (`LWT_Diagnosis`, `LWT_Diagnostics`, L09)

- Serveur, chaque pas, après les relais : une raison par arrivée d'eau, notée dans `LiveWaterRelay.why` de ses relais
  vides (effacée sur un relais qui a de l'eau) : `unfiltered`, `no_pressure`, `no_water`, `closed`, `wrong_fluid`
  (dernier pas du réseau, si une pompe est dans le réseau) ; `no_pressure` aussi quand aucune pompe n'est dans le
  réseau (ADR-009 D03).
- Client : au clic droit d'un point d'eau sans eau qui tire ou peut tirer sur une source extérieure, option grisée
  `ContextMenu_LWT_NoWater` (« Pas d'eau : %1 ») avec `IGUI_LWT_Why_NoInlet`, `_NotPlumbed`, `_Other`, `_<raison>` ou
  `_Waiting`.

## Lave-linge raccordés en multijoueur (`LWT_WasherFix`, `LWT_WasherClient`, L13)

- Serveur seulement, option `WasherFix` : pour chaque lave-linge (`IsoClothingWasher`, `IsoCombinationWasherDryer`)
  servi par un relais de LiveWater : arrêté sur le serveur → `sendObjectChange(WASHER_STATE)` une fois par arrêt ;
  lave-linge simple → ModData `LiveWaterWasher = { plumbed = true }` (`transmitModData`), une fois.
- Client : un `IsoClothingWasher` marqué prend `setUsesExternalWaterSource(true)` à son menu et à son interrupteur.

## Arrosage des plantes (`LWT_Plants`, `LWT_SprayArea`, `LWT_DripArea`, ADR-003, ADR-004)

- Serveur (autorité) : à chaque pas de dix minutes, une sortie d'arrosage ouverte prélève son débit, que les plantes
  aient soif ou non (ADR-006 D01) : besoin = `flow` de la stratégie de zone (arroseur : option `SprinklerFlow`, 10 L ;
  ligne de goutte-à-goutte : option `DripFlow`, 0,5 L par case). Le réseau lui donne ce débit ou ce qui reste
  (`LWT_Flow`). `LWT_Plants:deliver` retire la part perdue en l'air (`loss`, 0,25 pour l'arroseur : 7,5 L sur 10 ; 0
  pour la ligne) et donne aux plantes vivantes qui ont besoin d'eau des doses entières de 200 ml, cases les plus
  proches d'abord ; le reste est perdu. Deux sorties sur une même plante prélèvent chacune leur débit, la plante ne
  reçoit que son besoin. Zone par stratégie : `spray` → `LWT_SprayArea.reach` (carré de `radius` cases sur chaque axe,
  rayon mis à l'échelle de l'option sandbox), `drip` → `LWT_DripArea.reach` (cases voisines non raccordées, masque des
  liens lu dans le graphe du réseau) ; chaque stratégie rend cases, dose, perte et débit.
- Arroseur automatique : la minuterie (`controller`, `duration` 3) le tient ouvert 3 pas de dix minutes à chaque
  nouvelle tranche de `every` heures, avec du courant ; une ligne de goutte-à-goutte coule dès que le réseau la sert
  (ADR-006 D03), et reste à sec après une sortie à court de pression (ADR-006 D04, ADR-001 D14).
- Bruit : un arroseur qui arrose fait entendre aux zombies `noiseRadius` / `noiseVolume` à chaque pas
  (`LWT_Publisher`, `addSound`), en plus de sa boucle `WaterCrops` pour les joueurs. La ligne de goutte-à-goutte n'a
  pas de son.
- Zones visibles (client, `LWT_AreaView`, ADR-003 D02, D04) : au clic droit d'une pièce qui arrose (stratégies de
  zone `LWT_SprayArea.reach` et `LWT_DripArea.reach`, liens d'une ligne lus sur son image, `AreaView.addStrategy` pour
  un autre mod), une seule option, `ContextMenu_LWT_ShowAllAreas` (« Afficher toutes les zones arrosées »), surligne en
  bleu le sol de chaque case arrosée par les pièces à moins de `AreaView.RANGE` (25) cases du joueur ;
  `ContextMenu_LWT_HideArea` (« Masquer la zone arrosée ») l'enlève ; surbrillance persistante
  (`setHighlighted(true, false)`), sans abonnement par image ; un nouvel affichage remplace l'ancien.
- Jet (client, `LWT_SprinklerJet`, ADR-003 D03) : 8 images d'un tour complet (S, SE, E, NE, N, NO, O, SO), 6 images
  par seconde au plus, tuiles 128-159.
- Clés ajoutées (`IG_UI.json`) : `IGUI_LWT_Drip_served`, `_idle`, `_no_water`, `_no_pressure`,
  `_closed`, `_wrong_fluid` ; (`ContextMenu.json`) `ContextMenu_LWT_ShowAllAreas`, `ContextMenu_LWT_HideArea` ;
  (`ItemName.json`) `Base.Mov_LiveWater_DripLine` ; (`Recipes.json`) `LWTMakeDripLine`.

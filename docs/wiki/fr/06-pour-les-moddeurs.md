# Pour les moddeurs : l'API publique

LiveWater est un **réseau d'eau ouvert**, construit comme Live Wire : des **producteurs** mettent l'eau dans les tuyaux,
des **consommateurs** la prennent, et les uns comme les autres sont inscrits par la même API publique qu'un autre mod
utilise. Une nouvelle pièce est un fichier de données ; un nouveau comportement est une capacité.

## Règles

- Inscrire depuis un fichier de `media/lua/shared`, pendant le chargement, **avant `OnInitGlobalModData`**. Ensuite,
  toute inscription est refusée avec `registration_closed`.
- Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console. Rien ne lève d'erreur.
- Les identifiants portent un espace de noms : `"<VotreMod>:<Nom>"`.
- Vérifiez `LiveWater.API.revision` avant d'utiliser une fonction ou un champ ajouté après la révision 1. La révision
  actuelle est **24**.

## Fonctions

| Fonction | Rôle |
|---|---|
| `LiveWater.API.registerPart(id, definition)` | un type de pièce : `sprites` (`{ [masque] = sprite }`, masques 0-15, redessinés selon les raccords) ou `variants` (sprites choisis par l'état, 4 orientations S, E, N, O), `crossings` (révision 14 : `{ [masque] = { [bords] = sprite } }`, bords 1 = N, 8 = O, 9 = les deux, pris dans le masque : la forme dessinée avec un manchon là où elle traverse une clôture portée par son propre bord N ou O ; refus `invalid_crossings`), `sides` (masque des côtés raccordables, 15 par défaut), `link` (révision 24 : `{ level = 0..10 }`, la pièce se raccorde par fil électrique à un onduleur LiveWire à ce niveau d'Électricité, révision 9 de l'API de LiveWire ; refus `invalid_link`), `capabilities` (`{ kind = réglages ou true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | une capacité ; `implementation.define(params)` obligatoire, tous les crochets facultatifs |
| `LiveWater.API.part(id)` | copie contrôlée d'une définition de pièce, ou `nil` |
| `LiveWater.API.registerSource(kind, definition)` | révision 6 : une sorte d'eau qu'un producteur peut puiser (une source à côté de la pompe) `{ quality = "clean" ou "tainted", flag = IsoFlagType d'une case voisine, sprites = { sprites d'objets voisins } }` |
| `LiveWater.API.registerContainer(name, definition)` | révision 11 : un conteneur qu'un raccord de remplissage remplit, ou qu'une pompe puise (`vessel`), par sprite ou nom d'entité, `{ shape = "tall" ou "low" }` ; rempli comme un baril, d'eau souillée (ADR-005 D07 ; le champ `clean` de la révision 12 est ignoré) |
| `LiveWater.API.registerOutlet(outletType, handler)` | révision 22 : un consommateur, `outletType` `"<VotreMod>:<Nom>"`, voir plus bas |
| `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` | événements sur l'autorité : `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (pièce, litres, qualité), `valveChanged`, `waterDrawn` (révision 11) |

Capacités fournies : `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `drip` (révision 15), `vessel` (révision 21). Leurs réglages et valeurs par défaut sont dans les
spécifications techniques du dépôt.

## Producteurs et consommateurs

Un **producteur** met de l'eau dans les tuyaux de son réseau. La pompe à eau en est un : une pièce qui a la capacité
`pump`, avec `intake` là où elle puise à une source. Un producteur ne puise que ce qu'il touche, et seul un producteur
ajoute de l'eau : un réseau sans producteur ne donne rien.

Un **consommateur** prend du réseau le fluide qu'il accepte, de l'eau par défaut : l'arrivée d'eau de la maison, les arroseurs, les lignes de goutte-à-goutte
et les raccords de remplissage sont intégrés ; le vôtre s'inscrit avec `registerOutlet`. Le réseau dit combien un
consommateur peut prendre et lui donne les litres ; c'est le consommateur qui décide ce qu'il en fait.

Producteurs et consommateurs ne tournent que sur l'autorité : le serveur, ou la partie solo.

- `intake` (champ `orVessel`, révision 21) : `quality` `"clean"` ou `"tainted"` ; `orVessel = true` permet à la pièce de
  se poser contre un conteneur (un baril, un récupérateur d'eau de pluie, un refroidisseur d'eau, une mangeoire) sans autre
  source.
- `vessel` (révision 21) : `rate`, les litres au plus par pas (50 par défaut). La pièce puise l'eau du conteneur posé
  contre elle. De l'eau est prise, propre ou souillée ; depuis la révision 23, aussi du carburant (pompe contre une pompe de station-service), jamais un autre fluide.
- `outlet` (révision 22) : `type` peut valoir `"<VotreMod>:<Nom>"`, le nom d'un consommateur inscrit avec `registerOutlet`.
- `outlet` (révision 23) : `takes`, le fluide que la sortie accepte : `"water"` (par défaut : une sortie sans ce champ ne prend que de l'eau), `"fuel"`, `"other"` ou `"any"`. Une sortie à qui l'on donne un fluide qu'elle ne prend pas passe à l'état `wrong_fluid`. C'est le quatrième résultat du crochet `outlet`.
- Crochet `stepped` (révision 23) : `outcome.otherFluid = true` pour une pompe qui n'a rien donné ce pas parce qu'un autre fluide est dans les tuyaux de sa zone (la première pompe posée dans la zone impose le fluide).
- Crochet `sense` (révision 23) : `info.takes` dit ce qu'un conteneur vide prend (`"water"` pour une mangeoire).

### `registerOutlet` (révision 22)

`LiveWater.API.registerOutlet(outletType, handler)` dit où va l'eau d'un type de sortie. Le gestionnaire est appelé avec
`:` sur l'autorité :

- `need(part)` : obligatoire. Les litres que la sortie veut à ce pas.
- `deliver(part, litres, quality)` : obligatoire. Les litres qu'elle a reçus, et leur qualité (`"clean"` ou `"tainted"`).
- `release(part)` : facultatif. La pièce a quitté le monde (ramassée ou retirée).
- `cut(part)` : facultatif. Une vanne vient de couper la sortie de l'eau.

Rend `true`, ou `false` et `"registration_closed"`, `"invalid_type"`, `"invalid_handler"` ou `"duplicate_outlet"`.
Les types intégrés `houseInlet`, `sprinkler`, `drip` et `barrelFill` sont réservés.

### Exemple : une mangeoire à vous

```lua
-- media/lua/shared/MonMod/MonMod_Mangeoire.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 22 then
    LiveWater.API.registerPart("MonMod:Mangeoire", {
        variants = { off = { "monmod_mangeoire_0", "monmod_mangeoire_1", "monmod_mangeoire_2", "monmod_mangeoire_3" } },
        capabilities = {
            outlet = { type = "MonMod:Mangeoire" },
        },
    })

    LiveWater.API.registerOutlet("MonMod:Mangeoire", {
        need = function(self, part)
            return 20 -- litres que cette mangeoire prend à ce pas
        end,
        deliver = function(self, part, litres, quality)
            -- ajouter les litres au réservoir de la mangeoire ; une eau souillée reste souillée
        end,
        cut = function(self, part)
            -- une vanne est fermée : la mangeoire ne reçoit plus d'eau jusqu'à son ouverture
        end,
    })
end
```

## Exemple : une pièce à vous

```lua
-- media/lua/shared/MonMod/MonMod_MiniArroseur.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 8 then
    LiveWater.API.registerPart("MonMod:MiniArroseur", {
        variants = { off = { "monmod_01_0", "monmod_01_1", "monmod_01_2", "monmod_01_3" },
                     on = { "monmod_01_4", "monmod_01_5", "monmod_01_6", "monmod_01_7" } },
        capabilities = {
            outlet = { type = "sprinkler" },
            valve = { open = false },
            spray = { radius = 1, dose = 0.1 },
        },
    })
end
```

Une pièce dont le mod est retiré reste inerte dans la sauvegarde et revient avec son type quand le mod revient.

## Historique des révisions

| Révision | Ajouts |
|---|---|
| 1 | `registerPart`, `registerCapability`, `part`, `LiveWater.Events` ; crochets `carries`, `blocks`, `pressurizes`, `ports`, `supply`, `source`, `outlet`, `purifies`, `wear` |
| 2 | champ `variants` ; crochets `look`, `attach`, `power`, `powered`, `stepped`, `output`, `lines` |
| 3 | réglage `item` du filtre ; crochets `cartridge`, `fit`, `unfit`, `actions` |
| 4 | réglages d'entretien de la pompe ; crochets `switchable`, `switch`, `repairable`, `repair`, `sound` |
| 5 | capacité `meter`, réglage `ports` de `conduit`, qualité par pièce dans le bilan de `stepped` |
| 6 | `registerSource` ; qualité de l'eau d'une prise selon la sorte de source relevée |
| 7 | type de sortie en troisième résultat du crochet `outlet` ; `outcome.outlet` de `stepped`, gardé comme état de la sortie |
| 8 | capacité `spray` ; crochets `spray`, `jet`, `opened`, `open` ; événement `valveChanged` |
| 9 | minuterie (`controller` `timer` : `every`, `watts`, `choices`) ; crochets `prepare`, `opens`, `timer`, `setTimer` ; `choices` des actions ; `ctx.hours` |
| 10 | crochet `status` (vue du réseau) ; commandes `showNetwork` et `network` |
| 11 | capacité `fitting` ; crochets `draw`, `sense`, `fittingMode`, `setFittingMode` ; fluide accepté en quatrième résultat de `outlet` ; événement `waterDrawn` ; qualité `fuel` ; `registerContainer` |
| 12 | `clean = true` dans `registerContainer` |
| 13 | champ `facings` de la pièce (orientation de la variante selon le masque des côtés : pièce en ligne tournée selon son tuyau) ; réglage `look` de la vanne (dessin selon l'état de la vanne, variantes `open` / `closed`) ; réglage `sound` de `spray` (boucle jouée pendant l'arrosage) |
| 14 | champ `crossings` de la pièce (images à manchon d'une forme qui traverse une clôture sur son bord N ou O ; refus `invalid_crossings`) |
| 15 | capacité `drip` (crochet `drip`) ; réglage `costGroup` de la sortie (crochet `costGroup`), type de sortie `drip` ; réglages `loss`, `noiseRadius`, `noiseVolume` de `spray` |
| 16 | réglage `flow` de `spray` et `drip` (quatrième résultat du crochet `spray`, deuxième de `drip`) ; `loss` de `spray` devient une part de l'eau prélevée ; réglage `duration` de `controller` |
| 17 | crochet `panel` des capacités : « Information » ouvre une fenêtre à la place de l'infobulle ; champ `bends` de la pièce (remplacé par `branches` en révision 18) |
| 18 | champ `branches` de la pièce : variante choisie par le masque des côtés raccordés, relatif à l'orientation (remplace `bends`) |
| 19 | champ `sidesByFacing` de la pièce : côtés que la pièce peut raccorder, selon l'orientation de pose |
| 20 | réglage `spent` du filtre (objet que rend une cartouche usée, ADR-009 D01) ; quatrième résultat du crochet `cartridge` |
| 21 | capacité `vessel` (`rate` ; crochets `sense`, `draw`, `lines`) ; champ `orVessel` de `intake` ; `GameSite:hasVessel()` |
| 22 | `registerOutlet` et types de sortie `"<VotreMod>:<Nom>"` ; le raccord de remplissage ne fait que remplir (crochet `container` remplace `fittingMode`) ; plus d'écoulement par gravité : seul un producteur met l'eau dans un réseau (réglages `gravity` et `byGravity` retirés) |
| 23 | champ `takes` de `outlet` (fluide accepté, quatrième résultat du crochet `outlet`) ; la capacité `vessel` tire aussi l'essence ; `outcome.otherFluid` de `stepped` ; `info.takes` de `sense` ; un seul fluide par réseau, par zone et par pas (ADR-014) |
| 24 | champ `link` de la pièce (`{ level = 0..10 }` : une pièce qui a besoin de courant se raccorde par fil à un onduleur LiveWire, révision 9 de l'API de LiveWire ; refus `invalid_link`, ADR-017) |

Les changements sont seulement additifs : une fonction ou un champ ne change jamais de sens dans une révision suivante.
Deux exceptions avant la première publication : la révision 16 a fait de `loss` de `spray` une part de l'eau prélevée
(ADR-006), et la révision 22 a retiré l'écoulement par gravité et les modes des raccords (ADR-012).

Suite : [Retirer le mod](07-retirer-le-mod.md)

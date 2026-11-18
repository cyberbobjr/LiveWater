# Pour les moddeurs : l'API publique

LiveWater est un **réseau d'eau ouvert** : ses propres tuyaux, pompes, arrivées d'eau et arroseurs sont inscrits par
la même API publique qu'un autre mod utilise. Une nouvelle pièce est un fichier de données ; un nouveau comportement
est une capacité.

## Règles

- Inscrire depuis un fichier de `media/lua/shared`, pendant le chargement, **avant `OnInitGlobalModData`**. Ensuite,
  toute inscription est refusée avec `registration_closed`.
- Tout refus rend `false` et une raison, et écrit un avertissement en anglais dans la console. Rien ne lève d'erreur.
- Les identifiants portent un espace de noms : `"<VotreMod>:<Nom>"`.
- Vérifiez `LiveWater.API.revision` avant d'utiliser une fonction ou un champ ajouté après la révision 1.

## Fonctions

| Fonction | Rôle |
|---|---|
| `LiveWater.API.registerPart(id, definition)` | un type de pièce : `sprites` (`{ [masque] = sprite }`, masques 0-15, redessinés selon les raccords) ou `variants` (sprites choisis par l'état, 4 orientations S, E, N, O), `sides` (masque des côtés raccordables, 15 par défaut), `capabilities` (`{ kind = réglages ou true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | une capacité ; `implementation.define(params)` obligatoire, tous les crochets facultatifs |
| `LiveWater.API.part(id)` | copie contrôlée d'une définition de pièce, ou `nil` |
| `LiveWater.API.registerSource(kind, definition)` | révision 6 : une sorte de source d'eau `{ quality = "clean" ou "tainted", flag = IsoFlagType d'une case voisine, sprites = { sprites d'objets voisins } }` |
| `LiveWater.API.registerContainer(name, definition)` | révision 11 : un conteneur qu'un raccord de baril peut remplir, par sprite ou nom d'entité, `{ shape = "tall" ou "low" }` ; révision 12 : `clean = true` (eau propre seulement) |
| `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` | événements sur l'autorité : `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (pièce, litres, qualité), `valveChanged`, `waterDrawn` (révision 11) |

Capacités fournies : `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `layable`. Leurs réglages et valeurs par défaut sont dans les spécifications techniques du dépôt.

## Exemple : une pièce à vous

```lua
-- media/lua/shared/MonMod/MonMod_GoutteAGoutte.lua
require "LiveWater/LWT_API"

if LiveWater and LiveWater.API and LiveWater.API.revision >= 8 then
    LiveWater.API.registerPart("MonMod:GoutteAGoutte", {
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
| 1 | `registerPart`, `registerCapability`, `part`, `LiveWater.Events` ; crochets `carries`, `blocks`, `pressurizes`, `ports`, `supply`, `source`, `outlet`, `purifies`, `wear`, `layable` |
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
| 13 | champ `facings` de la pièce (orientation de la variante selon le masque des côtés : pièce en ligne tournée selon son tuyau) ; réglage `look` de la vanne (dessin selon l'état de la vanne, variantes `open` / `closed`) |

Les changements sont seulement additifs : une fonction ou un champ ne change jamais de sens dans une révision suivante.

Suite : [Retirer le mod](07-retirer-le-mod.md)

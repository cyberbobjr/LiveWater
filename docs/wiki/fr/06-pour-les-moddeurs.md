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
| `LiveWater.API.registerPart(id, definition)` | un type de pièce : `sprites` (`{ [masque] = sprite }`, masques 0-15, redessinés selon les raccords) ou `variants` (sprites choisis par l'état, 4 orientations S, E, N, O), `crossings` (révision 14 : `{ [masque] = { [bords] = sprite } }`, bords 1 = N, 8 = O, 9 = les deux, pris dans le masque : la forme dessinée avec un manchon là où elle traverse une clôture portée par son propre bord N ou O ; refus `invalid_crossings`), `sides` (masque des côtés raccordables, 15 par défaut), `capabilities` (`{ kind = réglages ou true }`) |
| `LiveWater.API.registerCapability(kind, implementation)` | une capacité ; `implementation.define(params)` obligatoire, tous les crochets facultatifs |
| `LiveWater.API.part(id)` | copie contrôlée d'une définition de pièce, ou `nil` |
| `LiveWater.API.registerSource(kind, definition)` | révision 6 : une sorte de source d'eau `{ quality = "clean" ou "tainted", flag = IsoFlagType d'une case voisine, sprites = { sprites d'objets voisins } }` |
| `LiveWater.API.registerContainer(name, definition)` | révision 11 : un conteneur qu'un raccord de baril peut remplir, par sprite ou nom d'entité, `{ shape = "tall" ou "low" }` ; rempli comme un baril, d'eau croupie (ADR-005 D07 ; le champ `clean` de la révision 12 est ignoré) |
| `LiveWater.Events.on(nom, fn)` / `off(nom, fn)` | événements sur l'autorité : `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (pièce, litres, qualité), `valveChanged`, `waterDrawn` (révision 11) |

Capacités fournies : `conduit`, `meter`, `intake`, `pump`, `valve`, `spray`, `filter`, `outlet`, `controller`,
`fitting`, `drip` (révision 15). Leurs réglages et valeurs par défaut sont dans les spécifications techniques du dépôt.
La révision 15 ajoute aussi :

- les réglages `loss` de `spray` (part de l'eau prélevée perdue en l'air, 0,25 par défaut : sur 10 L, 7,5 L peuvent
  aller aux plantes ; révision 16), `noiseRadius` et `noiseVolume` (ce qu'entendent les zombies à chaque pas tant qu'elle arrose
  avec un son, 10 et 10) ;
- les réglages `costGroup` de `outlet` (les sorties d'un réseau d'un même groupe paient leur coût de pression une seule
  fois par pas, ensemble) et `byGravity` (la sortie fonctionne sur la pression de gravité d'un réseau sans pompe) ; le
  type de sortie `drip` (toute eau, propre ou non, groupe `drip`, fonctionne sur la gravité ; ADR-005) ;
- le réglage `gravity` de `fitting` (pression qu'un baril réglé sur Pomper donne à un réseau sans pompe, 1 par défaut) ;
- la capacité `drip` (réglage `dose`, 0,2 L) : arrose les cases voisines de la pièce auxquelles elle n'est pas
  raccordée, sans perte.

La révision 16 (ADR-006) ajoute `flow` à `spray` et `drip` : les litres qu'une sortie d'arrosage prélève par pas de dix
minutes, que les plantes aient soif ou non (absent : options sandbox `SprinklerFlow`, 10 L, et `DripFlow`, 0,5 L par
case) ; les plantes prennent ce qu'il leur faut, le reste est perdu. Réglage `duration` de `controller` : pas de dix
minutes pendant lesquels une minuterie tient sa pièce ouverte (3 par défaut : 30 minutes).

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
| 15 | capacité `drip` (crochet `drip`) ; réglages `costGroup` et `byGravity` de la sortie (crochets `costGroup`, `byGravity`), type de sortie `drip` ; réglage `gravity` du raccord (crochet `gravity`) ; réglages `loss`, `noiseRadius`, `noiseVolume` de `spray` |
| 16 | réglage `flow` de `spray` et `drip` (quatrième résultat du crochet `spray`, deuxième de `drip`) ; `loss` de `spray` devient une part de l'eau prélevée ; réglage `duration` de `controller` |
| 17 | crochet `panel` des capacités : « Information » ouvre une fenêtre à la place de l'infobulle ; champ `bends` de la pièce (remplacé par `branches` en révision 18) |
| 18 | champ `branches` de la pièce : variante choisie par le masque des côtés raccordés, relatif à l'orientation (remplace `bends`) |
| 19 | champ `sidesByFacing` de la pièce : côtés que la pièce peut raccorder, selon l'orientation de pose |
| 20 | réglage `spent` du filtre (objet que rend une cartouche usée, ADR-009 D01) ; quatrième résultat du crochet `cartridge` |

Les changements sont seulement additifs : une fonction ou un champ ne change jamais de sens dans une révision suivante.
Une exception avant la première publication : la révision 16 a fait de `loss` de `spray` une part de l'eau prélevée
(ADR-006).

Suite : [Retirer le mod](07-retirer-le-mod.md)

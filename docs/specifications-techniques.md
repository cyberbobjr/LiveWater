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

Crochets d'une capacité (tous facultatifs sauf `define`), appelés avec les réglages contrôlés puis l'état de la
pièce pour cette capacité (`part.data[kind]`, éventuellement `nil`) : `carries` (l'eau traverse), `blocks` (coupe
l'eau, vanne fermée), `pressurizes` (l'eau part de là), `ports` (nombre maximal de tuyaux raccordés), `supply`
(pression et litres par pas), `source` (qualité `"clean"` ou `"tainted"`, `nil` à sec), `outlet` (coût de pression,
eau propre exigée), `purifies` (le filtre agit), `wear(p, d, litres)` (seul crochet qui écrit son état).

## Registre persistant (ModData globale, `LWT_Registry`)

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
`invalid_handler`), émis sur l'autorité : `partAdded`, `partRemoved`, `networkChanged`, `waterDelivered` (pièce,
litres, qualité), `valveChanged`.

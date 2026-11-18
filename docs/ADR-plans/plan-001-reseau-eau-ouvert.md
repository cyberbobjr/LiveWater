# Plan 001 — Réseau d'eau ouvert : pompe d'étang, tuyaux visibles, maison et arrosage

ADR : [ADR-001](../ADR/001-reseau-eau-ouvert.md) (Accepté le 2026-11-17).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Squelette du projet : dépôt, `workshop.txt`, `mod.info` (`incompatible=` de Q09), documents obligatoires, banc de tests hors jeu | Terminée (2026-11-17) | ADR accepté | D22 | S | — |
| E02 | API publique : registres des pièces et capacités, validation, scellé, révision, événements | Terminée (2026-11-17) | E01 | D01-D07 | M | — |
| E03 | Domaine : graphe du réseau, masques de raccord, ports, vannes, fusion de réseaux | Terminée (2026-11-17) | E02 | D10, D12-D15 | M | E04 |
| E04 | Domaine : pas de distribution, pression, qualité, filtre, besoin des sorties | Terminée (2026-11-17) | E02 | D09, D14, D16, D17 | M | E03 |
| E05 | Persistance : registre global versionné, pièces de type inconnu conservées | Terminée (2026-11-17) | E03 | D03, D04, D10 | M | E06 |
| E06 | Tuiles provisoires : 16 tuyaux, robinet, arroseurs, arrivée d'eau, pompe, filtre ; planche de présentation validée par l'utilisateur | Terminée (2026-11-18) | E01 | D12, D23 | L | E02-E05 |
| E07 | Adaptateurs serveur : pose et retrait, raccord automatique des sprites, commandes, horloge `EveryTenMinutes` | Terminée (2026-11-18) | E05, E06 | D08-D12 | L | — |
| E08 | Pompe d'étang et électricité : `registerConsumer` (`display`, `summary`), repli vanilla | Terminée (2026-11-18) | E07 | D16, D20 | M | E09 |
| E09 | Arrivée d'eau de la maison : réservoirs invisibles `LiveWaterRelay`, cohabitation Live Wire | Terminée (2026-11-18) | E07 | D18, D21 | M | E08 |
| E10 | Filtre : pièce, usure au volume, remplacement | Terminée (2026-11-18) | E08, E09, E06 | D17, D23 | S | E11 |
| E11 | Arroseur manuel : vanne, rayon, doses de 200 ml | Terminée (2026-11-18) | E07 | D19 | M | E10 |
| E12 | Arroseur automatique : recette (niveau d'Électricité), minuterie consommatrice | Terminée (2026-11-18) | E11, E08 | D19, D20 | M | — |
| E13 | Interface : menus, vue du réseau en surbrillance persistante, états « sans pression » et « eau non filtrée » | Terminée (2026-11-18) | E08-E12 | D11, D14, D17 | M | — |
| E15 | Pompe : interrupteur, usure du rendement, pannes, réparation, fenêtre d'information, son (P03-P05, P08, P15) | Terminée (2026-11-18) | E08 | D24 | M | E16 |
| E16 | Débitmètre (P12) | Terminée (2026-11-18) | E07 | D24 | S | E15 |
| E17 | Puits comme source d'eau propre (P02) | Terminée (2026-11-18) | E08 | D24 | S | E16 |
| E18 | Tuyaux d'un étage à l'autre (P10) | Annulée (Q06 : non repris, l'arrivée d'eau dessert les étages) | — | D24 | — | — |
| E19 | Sous-sols et lave-linge desservis par l'arrivée d'eau (P16, P18) | Terminée (2026-11-18) | E09 | D18, D24 | S | E20 |
| E20 | Raccord de baril « Remplir » ou « Pomper », réseau d'essence (P02, P17) | Terminée (2026-11-18) | E07 | D24, D26 | M | E19 |
| E21 | Retrait propre du mod (P21) | Terminée (2026-11-18) | E09, E11 | D03, D24 | S | — |
| E23 | Baril raccordé à la maison : gravité, courant sur la case, réserve partagée, mise en réserve, baril gardé pour un liquide (L01-L03, L06, L07) | Terminée (2026-11-18) | E09 | D27, D28 | L | E24 |
| E24 | Liquide choisi par point d'eau (L05) | Annulée (Q07 : eau seulement aux points d'eau) | — | D28 | — | — |
| E25 | Conteneurs remplis par la réserve, liste sandbox et API (L08) | Terminée (2026-11-18) | E20 | D26, D28 | S | E23 |
| E26 | Base du joueur (portée), diagnostic au point d'eau, réglages effacés au ramassage (L09, L11, L12) | Terminée (2026-11-18) | E09 | D28 | M | E25 |
| E27 | Raccordement au réseau public (M01) : état d'un point d'eau d'origine (`isWaterInfinite`), contrôles serveur | Terminée (2026-11-18) | E09 | D27, D28 | M | E26 |
| E28 | Correctif du lave-linge raccordé en MP (désactivable), `incompatible=\LGExtendedPlumbing,\LGMainsWater` (L13) | Terminée (2026-11-18) | E19 | D27, Q08, Q09 | S | — |
| E22 | Traductions (11 langues), wiki EN/FR, contrôle de parité P01-P23 et L01-M01, passage automatique en jeu SP et MP | À faire | E13-E21, E23-E28 | toutes | L | — |

## Fiches

Chaque fiche reçoit, à la clôture : fichiers touchés, commande de la suite hors jeu et sa ligne verte (nombre de tests
passés, zéro échec), contrôle du mod, et pour les étapes en jeu : code de sortie, ligne `summary` et dossier `runs/...`.
Rappels communs à toutes les étapes : aucun abonnement par image (D08) ; un fichier par pièce et par capacité ;
aucune modification de Live Wire (D21).

### E01 — Squelette

Fichiers : `Workshop\LiveWater` (dépôt git local), `workshop.txt` sans `id=`, `preview.png` provisoire,
`Contents/mods/batman_LiveWater/common/` et `42.21/` (`mod.info` : `id=batman_LiveWater`, `versionMin=42.21`, sans
`require=`), documents obligatoires de `docs/` (structure commune). Banc de tests hors jeu sur le modèle de Live Wire
(Python + `lupa`, `tests/`), contrôle du mod (`tools/check_mod.py`). Preuve : suite vide verte, contrôle `OK`.

Clôture (2026-11-17). Fichiers : `.gitignore`, `LICENSE`, `README.md`, `CHANGELOG.md`, `workshop.txt` (non listé,
sans `id=`), `preview.png` provisoire (512 px, tiré du rendu du réseau d'exemple), `Contents/mods/batman_LiveWater/`
(`common/media/`, `42.21/mod.info`, `poster.png`, `icon.png`), documents obligatoires de `docs/`, `tests/lwt_harness.py`,
`tests/test_harness.py`, `tools/check_mod.py`. Preuves :
- `python -B -m unittest discover -s tests` → `Ran 2 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 0 Lua file(s) checked`.

### E02 — API publique

Fichiers : `shared/LiveWater/LWT_API.lua` (façade), `LWT_Parts.lua` (registre des pièces), `LWT_Capabilities.lua`
(registre des capacités), `LWT_Events.lua`. Tests rouges : définition valide acceptée ; id hors espace de noms, sprite
en double, capacité inconnue, champ invalide refusés avec raison ; scellé après `OnInitGlobalModData` ; copie par liste
blanche (mutation de l'appelant sans effet) ; `revision` ; abonnement et émission d'événements.

Clôture (2026-11-17). Fichiers : `shared/LiveWater/LWT_API.lua` (façade, racine de composition des registres, scellé
à `OnInitGlobalModData`), `LWT_Parts.lua`, `LWT_Capabilities.lua`, `LWT_Events.lua`, `LWT_Check.lua` (contrôles et
copie par liste blanche), `LWT_Grid.lua` (côtés), un fichier par capacité de départ sous
`shared/LiveWater/Capabilities/` (`LWT_CapConduit`, `Intake`, `Pump`, `Valve`, `Filter`, `Outlet`, `Controller`),
`tests/test_api.py`. Lecture retenue : le type d'une sortie (`houseInlet`, `sprinkler`) est un nom libre ; ses valeurs
par défaut (coût de pression 2 et 1, eau propre exigée ou non) sont des données de `LWT_CapOutlet.lua`, et un type
inconnu prend le coût 1 sans exigence de propreté. Preuves :
- `python -B -m unittest discover -s tests` → `Ran 18 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 13 Lua file(s) checked`.

### E03 — Graphe du réseau

Fichiers : `shared/LiveWater/LWT_Network.lua` (pur). Tests rouges : masque de 4 bits et sprite attendu pour les 16
formes ; raccord refusé au-delà des `ports` ; vanne fermée qui coupe l'aval ; fusion et scission de réseaux à la pose et
au retrait ; distance en tuyau et ordre de service stable.

Clôture (2026-11-17). Fichiers : `shared/LiveWater/LWT_Network.lua` (graphe pur, catalogue des types injecté),
`LWT_Grid.lua` (côtés, `has`, clé `"x,y,z"`), `LWT_Parts.lua` (requêtes du catalogue `sides`, `sprite`, `any`,
`first`), `LWT_Capabilities.lua` (crochets `carries`, `blocks`, `pressurizes`, `ports`), crochets dans
`LWT_CapConduit`, `LWT_CapPump`, `LWT_CapValve`, `tests/test_network.py`. Lectures retenues : `ports` compte les
tuyaux directement raccordés à la pièce (les T et croix plus loin ne comptent pas, Q03) ; avec 4 par défaut et quatre
côtés, la limite ne mord que pour une pompe réglée plus bas. Une pièce sans `conduit` (sortie) termine un chemin ; une
vanne fermée est atteinte mais ne laisse rien passer. Un type sans sprite pour un masque montre `sprites[0]`.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 30 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 14 Lua file(s) checked`.

### E04 — Distribution

Fichiers : `shared/LiveWater/LWT_Flow.lua` (pur). Tests rouges : réserve de pression consommée de la plus proche à la
plus lointaine, sorties « sans pression » ; débit par pas de dix minutes ; eau croupie refusée par l'arrivée d'eau sans
filtre et acceptée par l'arroseur ; filtre qui purifie et s'use au volume ; aucune sortie servie sans besoin.

Clôture (2026-11-17). Fichiers : `shared/LiveWater/LWT_Flow.lua` (pas pur, catalogue injecté, besoin des sorties
fourni par `ctx.need(part)`), `LWT_Parts.lua` (`call`, qui crée l'état d'une capacité avant un crochet qui l'écrit),
`LWT_Capabilities.lua` (crochets `supply`, `source`, `outlet`, `purifies`, `wear`), crochets dans `LWT_CapPump`,
`LWT_CapIntake` (point d'extension `available`, D16), `LWT_CapOutlet`, `LWT_CapFilter`, `tests/test_flow.py`.
Lectures retenues, au plus près du texte de D14 et D17 : dès qu'une sortie manque de pression, toutes les suivantes
qui ont besoin d'eau sont « sans pression », même une moins chère (« les suivantes ») ; une sortie fermée, sans
besoin ou « eau non filtrée » ne prend ni eau ni pression ; l'eau du réseau est croupie dès qu'une source l'est ; le
premier filtre en état sur le chemin depuis la pompe (pompe et sortie comprises) rend propre toute l'eau qui y passe
et s'use de ce volume, la dernière livraison d'une cartouche presque usée passant propre en entier (usure plafonnée
à la capacité) ; le débit d'une pièce sans source (futur surpresseur) ne compte pas, sa pression oui.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 41 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 15 Lua file(s) checked`.

### E05 — Persistance

Fichiers : `server/LiveWater/LWT_Registry.lua`. Tests rouges : entrée versionnée `v` ; champs inconnus conservés ;
pièce de type non inscrit conservée et inerte, réactivée au retour de son type ; index par coordonnées.

Clôture (2026-11-17). Fichiers : `server/LiveWater/LWT_Registry.lua` (garde `isClient()`, magasin ModData injecté,
catalogue réduit à `has`), `tests/test_registry.py`. Les entrées ne sont jamais recopiées : un champ inconnu, une
version `v` plus récente ou l'état d'une capacité absente restent tels quels. Aucune migration n'existe encore
(schéma 1). Le branchement sur `ModData.getOrCreate` et la reconstruction du graphe au chargement viennent avec E07.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 47 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 16 Lua file(s) checked`.

### E06 — Tuiles provisoires

Skill `pz-blender-assets`. Formes simples marquées `placeholder` : 16 tuyaux, robinet ouvert et fermé (2 sens),
arroseur manuel et automatique (actif, inactif), arrivée d'eau (4 orientations), pompe d'étang (4 orientations),
filtre (objet d'inventaire et icône). **Avant toute intégration au mod (D23)** : une planche de présentation (rendus
de chaque tuile et de ses formes, exemple de réseau assemblé étang → robinet → maison et potager, icône du filtre) est
soumise à l'utilisateur ; l'intégration (pack, `.tiles`, noms de meubles posables) n'a lieu qu'après sa validation.

Planche soumise le 2026-11-17 : [tuiles](../images/art/planche-tuiles-provisoires.png) (66 cellules : 16 tuyaux,
robinet ouvert et fermé, débitmètre, pompe arrêtée, en marche et avec filtre, arrivée d'eau filtrée et non filtrée,
arroseurs manuel et automatique au repos et actifs, raccord de baril « Remplir » et « Pomper », objets section de
tuyau et cartouche filtrante) et [réseau d'exemple](../images/art/planche-reseau-exemple.png) étang → robinets →
maison et potager. Rendu : Blender 5.3 sans interface, `source/tiles/build_livewater_tiles.py`, planche par
`tools/make_tile_board.py`. Planche refaite le 2026-11-17 dans le style vanilla (matériaux texturés et passe de style
pzforge comme Live Wire, matériel rural réaliste, première ligne de sprites vanilla pour comparer) ; réseau d'exemple
composé sur sol vanilla par `tools/make_network_scene.py`.

Planche validée par l'utilisateur le 2026-11-17, avec deux remarques :
1. certains récupérateurs d'eau de pluie sont des tonneaux, plus hauts que la caisse bâchée : le raccord « Remplir »
   existe en deux hauteurs, `barrel_fill` (tonneau ou fût rond, rebord vers 0,80 m) et `barrel_fill_low` (caisse bâchée,
   rebord vers 0,60 m), mesurées sur `carpentry_02_122`-`126`, `industry_01_23`, `location_military_generic_01_7` et
   `carpentry_02_52`, `_54`, `_120`, et vérifiées en composition avec le récipient sur la case voisine ;
2. les jets d'eau des arroseurs doivent être animés : le moteur n'avance pas les images du calque d'une tuile ordinaire
   (base de connaissances, « Calque animé (`AttachAnim`) »), donc le jet quitte les tuiles « en marche » et devient
   un calque `sprinkler_jet` de 6 images × 4 orientations (index `80 + 4 * f + k`) que le client fait défiler (D08a) :
   le jet balaie ±36° par crans, avec la gerbe de la palette du marteau une image sur deux.

Clôture (2026-11-18). Tileset `batman_livewater_01`, tiledef **7176** (libre dans le Workshop 108600, `Zomboid\mods` et
`Zomboid\Workshop`, `pzforge.modgen.used_tiledef_ids`), indices du
[contrat des tuiles](../annexes/conception/tuiles-contrat.md) : 98 sprites (22-23 et 76-79 réservés). Fichiers :
`common/media/texturepacks/batman_livewater_01.pack`, `common/media/batman_livewater_01.tiles`,
`common/media/depthmaps/DEPTH_batman_livewater_01.png`, `common/media/tileGeometry.txt`, `pack=` et `tiledef=` dans
`42.21/mod.info`, noms des meubles posables dans `Translate/EN|FR/Moveables.json` (groupe « Live Water »), icônes
`42.21/media/textures/Item_LWT_PipeSection.png` et `Item_LWT_WaterFilter.png`. Propriétés : tuyaux sans
`IsMoveAble` (posés par une action de construction), autres pièces posables à la clé à tuyau (`Wrench`, comme les
éviers vanilla) avec `CustomItem = Base.Mov_LiveWater_<Nom>`, `Facing` et décalages de faces
(`Noffset`/`Soffset`/`Eoffset`/`Woffset`) ; calques du jet sans propriétés. Commandes (en-tête de la recette) :
rendu Blender sans interface, `style`, `package`, puis `build_depthmap.py` du skill `pz-blender-assets`. Contrôles :
`pzforge inspect` relit 98 sprites et 74 tuiles définies ; profondeur « total: 98 sprites, hits outside the sprite 0,
left without depth 0 ». Non vérifié en jeu : rotation à la pose, hauteur des raccords de baril, jet animé (E07).

### E07 — Adaptateurs serveur

Fichiers : `server/LiveWater/LWT_Placement.lua`, `LWT_Sprites.lua`,
`LWT_Commands.lua`, `LWT_Clock.lua`. Pose et retrait (autorité), sprite recalculé pour la pièce et ses voisins
(`setSpriteFromName`, `transmitUpdatedSpriteToClients`), commandes contrôlées côté serveur, un seul abonné
`EveryTenMinutes`. Contrôle : aucun `Events.OnTick`/`OnPlayerUpdate`/`OnRender*`/`OnPostRender` dans le mod (`rg`).

Clôture (2026-11-18). Fichiers : `server/LiveWater/LWT_Server.lua` (racine de composition sur l'autorité : services
construits à `OnInitGlobalModData` sur `ModData.getOrCreate("LiveWater")`, graphe reconstruit du registre ; abonnés
`OnObjectAdded`, `OnObjectAboutToBeRemoved`, `OnClientCommand`, et le seul `EveryTenMinutes`), `LWT_Topology.lua`
(registre et graphe changés ensemble, événements `partAdded`, `partRemoved`, `networkChanged`), `LWT_Placement.lua`
(tuile reconnue par son sprite via le catalogue), `LWT_Sprites.lua` (pièce et quatre voisins, appliqué seulement s'il
change), `LWT_Commands.lua` (répartiteur, table de gestionnaires, refus dits au joueur par clé de traduction),
`Commands/LWT_CmdLay.lua`, `LWT_CmdDismantle.lua`, `LWT_CmdChecks.lua`, `LWT_Clock.lua` (réseaux dont une pièce sous
pression est sur une case chargée, besoin des sorties injecté, 0 par défaut, `waterDelivered`), adaptateurs du jeu
`LWT_GameWorld.lua` et `LWT_GamePlayers.lua` ; `shared/LiveWater/Parts/LWT_PartPipe.lua` (`LiveWater:PipeGalvanized`,
sprites `batman_livewater_01_0` à `_15`), `Capabilities/LWT_CapLayable.lua`, `LWT_Protocol.lua`, `LWT_Notice.lua`,
crochet `layable` (`LWT_Capabilities.lua`), `Parts:typeOfSprite`, `hasShape`, `ids` (`LWT_Parts.lua`),
`Network:canAdd`, `ids` (`LWT_Network.lua`) ; menu minimal `client/LiveWater/LWT_PipeMenu.lua` et
`LWT_NoticeClient.lua` ; `media/scripts/LWT_items.txt` (`LiveWater.PipeSection`), `LWT_recipes.txt`
(`LWTCutPipeSections` : un `Base.MetalPipe` et un outil `tags[base:metalsaw]` gardé donnent 4 sections) ;
traductions EN et FR `IG_UI.json`, `ContextMenu.json`, `Recipes.json`, `ItemName.json` (clé `LiveWater.PipeSection`
seulement) ; tests `test_placement.py`, `test_sprites.py`, `test_commands.py`, `test_clock.py`, doublures
`tests/lwt_fakes.py`.
Lectures retenues :
- « posé avec un objet » est une capacité `layable` (`item`, `tool` = étiquette d'outil, `base:pipewrench` par
  défaut, Java 42.22 `ItemTag.PIPE_WRENCH`), pas une liste de tuyaux : un tuyau d'un autre matériau se pose par la
  même commande. La pose n'exige aucun outil (Q01 ne nomme que la clé au démontage) ;
- un type qui ne définit pas de sprite pour le masque calculé garde le sprite posé (orientation d'un meuble) : seules
  les formes déclarées (tuyaux) sont redessinées ;
- un meuble posé que le graphe refuse (case occupée, ports pleins) reste un décor, signalé dans la console ; le refus
  à la pose avec message (D14) relève de l'interface (E13) ;
- portée d'action : 3 cases (distance de Tchebychev) sur l'étage du joueur ; le menu minimal envoie la commande sans
  marcher ni action chronométrée (E13) ; refus montrés en note au-dessus du joueur (solo : directement ;
  serveur : commande `notice`) ;
- la section de tuyau n'a pas encore de modèle 3D au sol (icône seulement).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 88 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 33 Lua file(s) checked` ;
- `rg "Events\.(OnTick|OnTickEvenPaused|OnPlayerUpdate|OnRender\w*|OnPostRender|OnPreUIDraw)"` dans `media/lua` :
  aucune ligne ; un seul `Events.EveryTenMinutes.Add` (`LWT_Server.lua`).
Non testé en jeu.

### E08 — Pompe d'étang et électricité

Fichiers : `shared/LiveWater/Parts/LWT_PartPondPump.lua`, `server/LiveWater/LWT_Power.lua` (adaptateur unique vers Live
Wire et repli vanilla). Tests rouges : pose refusée loin de l'eau ; inscription `registerConsumer` seulement si
`revision >= 6` ; 250 W en marche, 0 à l'arrêt ; `display` et `summary` au format de l'ADR-002 ; pas de travail sans
courant.

Clôture (2026-11-18). Fichiers : `shared/LiveWater/Parts/LWT_PartPondPump.lua` (`LiveWater:PondPump`, `intake` +
`pump`, 50 L par pas, 250 W ; sprites 24-39 en `variants` `off`, `on`, `filter_on`, `filter_off` × S, E, N, O),
`LWT_Parts.lua` (champ `variants`, `typeOfSprite` les reconnaît, `facingOf`, `variant`, `spritesOf`, `hasHook`,
`look`, `attach`, `lines`), `LWT_Capabilities.lua` (crochets `look`, `attach`, `power`, `powered`, `stepped`, `output`,
`lines` ; `supply`, `purifies`, `wear` reçoivent le contexte du pas), `LWT_API.lua` (révision 2, registre des
sources), `LWT_Sources.lua` + `Sources/LWT_SourceNaturalWater.lua` (sortes de source en données : eau naturelle =
drapeau `water`, croupie), `LWT_GameSite.lua` (8 cases voisines), `LWT_PlaceRules.lua` (curseur de meuble vanilla :
`canPlaceMoveableInternal` et ligne du panneau d'information), `LWT_Reasons.lua` (raisons → clés, partagé),
`LWT_Settings.lua`, `LWT_Mirror.lua` (état recopié dans `movableData` de l'objet), `Capabilities/LWT_CapPump.lua`,
`LWT_CapIntake.lua`, `LWT_Flow.lua` (part de chaque pompe dans l'eau servie, `through`), côté serveur
`LWT_Power.lua` (seul adaptateur du courant), `LWT_Publisher.lua` (sprite selon l'état, état recopié sur l'objet
quand il change), `LWT_GameSettings.lua`, `LWT_Clock.lua` (courant, pas, `stepped`, présentation), `LWT_Topology.lua`
(`attach` à la pose, état rapporté par un meuble), `LWT_Placement.lua`, `LWT_Sprites.lua` (`show`), `LWT_GameWorld.lua`,
`LWT_Server.lua` (`OnInitWorld`, abonnés `partAdded`/`partRemoved`) ; `media/scripts/LWT_moveables.txt`
(`Base.Mov_LiveWater_PondPump`), recette `LWTBuildPondPump`, `media/sandbox-options.txt` (`PumpFlowMultiplier`),
traductions EN et FR ; tests `tests/test_pump.py`, doublures étendues `tests/lwt_fakes.py`.
Choix faits sans l'utilisateur :
- les 16 sprites de la pompe sont des `variants` (état × orientation), jamais redessinés par le masque ; la variante
  affichée est le nom formé par les jetons `look` des capacités (`filter` + `on` → `filter_on`, contrat des tuiles) ;
- règle vanilla sans Live Wire : générateur à portée ou réseau public (`haveElectricity() or hasGridPower()`, règle
  `ExteriorOK` des sons d'objets du moteur, Java 42.22), car `haveElectricity()` seul ne voit que les générateurs ;
- inscription Live Wire à `OnInitWorld` (tous les Lua chargés, Live Wire pas encore scellé), comme le mod de
  compatibilité de Live Wire ; seulement sur l'autorité (le client lit l'état recopié) ; identifiant
  `LiveWater_LiveWater_PondPump`, catégorie `other`, circuit `equipment`, sans `name` (Live Wire garde le nom du
  meuble) ; `display` = les 4 premières lignes d'information ; `summary` = pompes en marche sur le total, eau pompée ;
- la pompe ne marche que si une sortie prend de l'eau (arrêt automatique) ; deux pompes d'un réseau se partagent
  l'eau servie au prorata de leur débit ;
- pose refusée loin de l'eau au curseur (client) et sur l'autorité ; une pompe ramassée puis reposée garde son état
  (ModData `movableData`, recopiée par le vanilla) ;
- recette de fabrication de la pompe (Électricité 2, tournevis et clé gardés, tuyau, tôles, électronique, fils, vis)
  ajoutée pour que la pompe existe en jeu (P19).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 109 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 44 Lua file(s) checked`.
Non testé en jeu.

### E09 — Arrivée d'eau de la maison

Fichiers : `shared/LiveWater/Parts/LWT_PartHouseInlet.lua`, `server/LiveWater/LWT_Relays.lua`. Tests rouges : points
d'eau raccordés du bâtiment touché, portée et étages ; point déjà alimenté laissé ; relais de Live Wire jamais touchés ;
retrait propre des relais.

Clôture (2026-11-18). Fichiers : `Parts/LWT_PartHouseInlet.lua` (`LiveWater:HouseInlet`, `outlet` `houseInlet` ;
`variants` `filtered` 40-43 et `unfiltered` 44-47), `LWT_Tiles.lua` (noms des sprites et `variants` d'après le premier
index, partagé avec la pompe d'étang), `Capabilities/LWT_CapOutlet.lua` (révision 7 : type de sortie en troisième
résultat du crochet `outlet`, état `state` du dernier pas, `look` `filtered`/`unfiltered` pour une sortie qui exige de
l'eau propre, ligne `IGUI_LWT_Outlet_<état>`), `LWT_InletArea.lua` (pur : bâtiment de la carte touché, cercle de
portée, jusqu'à 3 étages au-dessus), `LWT_RelayPlan.lua` (pur : relais voulus), `LWT_API.lua` et
`LWT_Capabilities.lua` (révision 7) ; serveur `LWT_Outlets.lua` (gestionnaire par type de sortie : besoin, livraison,
retrait), `LWT_Relays.lua` (service des relais, tâche de l'horloge), `LWT_GamePlumbing.lua` (adaptateur : bâtiment,
points d'eau, relais), `LWT_Clock.lua` (`chores` avant les réseaux, `outcome.outlet`), `LWT_Server.lua` (besoin des
sorties, `waterDelivered` et `partRemoved` vers `LWT_Outlets`) ; `LWT_moveables.txt`
(`Base.Mov_LiveWater_HouseInlet`), recette `LWTBuildHouseInlet`, option `InletRange`, traductions EN et FR ;
tests `tests/test_inlet.py` ; `test_api.py` (révision 7), `test_well.py` (révision au moins 6).
Choix faits sans l'utilisateur :
- réservoir relais : tuile réservée `batman_livewater_01_76`, définie sans image dans le `.tiles` (invisible, même
  procédé que le relais de Live Wire), `IsoThumpable` traversable avec un `FluidContainer` de 25 L nommé
  `LiveWaterRelay`, ModData `LiveWaterRelay = { inlet = "x,y,z" }` ;
- un relais par point d'eau, posé un niveau au-dessus, partagé par les points d'eau voisins (le moteur cherche la
  source sur la case au-dessus puis les 8 autour, `IsoObject.FindExternalWaterSource`, Java 42.22) ; posé aussi
  au-dessus d'un point d'eau pas encore raccordé (posé par un joueur, ou d'origine après la coupure de l'eau de la
  ville), car le menu vanilla « Raccorder » n'apparaît qu'avec une source au-dessus ; seuls les relais qui servent un
  point d'eau raccordé sont remplis ;
- point d'eau déjà servi par une autre source (relais de Live Wire, baril vanilla, autre mod) : aucun relais, rien
  touché (D21) ; un relais d'une autre arrivée d'eau de LiveWater est laissé à celle-ci ;
- portée `LiveWater.InletRange` 20 cases par défaut (cercle autour de l'arrivée d'eau, limité au bâtiment) ; points
  d'eau relevés à la pose de l'arrivée d'eau puis toutes les heures de jeu, à la tâche de dix minutes, seulement pour
  les arrivées d'eau sur une case chargée ;
- pose libre : aucune règle de pose ; une arrivée d'eau qui ne touche aucun bâtiment de la carte ne dessert rien
  (base du joueur : E26) ;
- retrait : les relais de l'arrivée d'eau partent avec elle ; sur une case non chargée, ils restent notés et sont
  retirés au premier pas où la case est chargée ;
- eau non filtrée : la sortie est « eau non filtrée » (sprite ambre, ligne d'information) et ne remplit rien (D17,
  déjà porté par `LWT_Flow`) ; le robinet montre l'eau de son relais (25 L au plus), pas un total (L03 : réserve
  partagée traitée à E23).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 163 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 62 Lua file(s) checked`.
Non testé en jeu.

### E10 — Filtre

Objet et icône validés sur la planche d'E06 (D23). Fichiers : `shared/LiveWater/Parts/LWT_PartFilter.lua`, objet et recette.

Clôture (2026-11-18). Fichiers : `Capabilities/LWT_CapFilter.lua` (réglage `item` : cartouche amovible ; crochets
`cartridge`, `fit`, `unfit`, `look` → `filter`, `lines`, `actions` ; capacité × option `FilterCapacityMultiplier`,
notée à la pose de la cartouche), `Parts/LWT_PartPondPump.lua` (capacité `filter` : `LiveWater.WaterFilter`, 500 L),
`LWT_Parts.lua` (`actions`), `LWT_Capabilities.lua` et `LWT_API.lua` (révision 3), `LWT_Protocol.lua`,
`LWT_Reasons.lua` (`no_cartridge`, `no_filter`, `no_filter_slot`), serveur `Commands/LWT_CmdCartridge.lua`,
`LWT_CmdFitFilter.lua`, `LWT_CmdRemoveFilter.lua`, `LWT_GamePlayers.lua` (part restante = état de l'objet),
`LWT_Commands.lua`, `LWT_Server.lua` ; client `LWT_PartMenu.lua` (menu générique des actions des capacités, lu dans
l'état recopié) ; `LWT_items.txt` (`LiveWater.WaterFilter`, `ConditionMax = 100`), recette `LWTMakeWaterFilter`
(2 charbons `tags[base:charcoal]`, 2 `Base.RippedSheets`), option sandbox, traductions EN et FR (dont
`Tooltip.json`) ; tests `tests/test_filter.py`.
Choix faits sans l'utilisateur :
- pas de pièce `LWT_PartFilter.lua` à part : la cartouche se monte dans la pompe (capacité `filter` de la pompe,
  sprites `filter_on`/`filter_off` du contrat) ; un filtre en ligne reste possible plus tard par une pièce qui porte
  la même capacité ;
- l'état de la cartouche (0-100) est la part qui reste : une cartouche retirée à moitié usée revient à 50 et reprend
  son usure si on la remonte ; une cartouche usée est jetée au retrait ; « Remplacer » retire l'ancienne puis monte
  la neuve ;
- recette sans outil ni compétence, 2 charbons (de bois ou de fabrication) et 2 bandes de tissu propres (Q02).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 120 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 48 Lua file(s) checked`.
Non testé en jeu.

### E11 — Arroseur manuel

Fichiers : `shared/LiveWater/Parts/LWT_PartSprinkler.lua`, `server/LiveWater/LWT_Plants.lua`. Tests rouges : plantes du
rayon qui ont besoin d'eau seulement ; doses de 200 ml retirées du réseau ; vanne fermée = rien.

Clôture (2026-11-18). Fichiers : `Parts/LWT_PartSprinkler.lua` (`LiveWater:Sprinkler` : `outlet` `sprinkler`, `valve`
posée fermée, `controller` `manual`, `spray` ; `variants` `off` 48-51 et `on` 52-55), nouvelle capacité
`Capabilities/LWT_CapSpray.lua` (rayon 2, dose 0,2 L, images du jet ; crochets `spray`, `jet`, `stepped`, `look`),
`LWT_CapValve.lua` (crochets `opened`, `open`, `actions`, `lines`), `LWT_CapOutlet.lua` (ligne d'état par type de
sortie : `IGUI_LWT_Sprinkler_<état>`), `LWT_Capabilities.lua` et `LWT_API.lua` (révision 8), `LWT_Protocol.lua`
(`switchValve`, `jet`), `LWT_Reasons.lua` (`not_valve`) ; serveur `LWT_Plants.lua` (gestionnaire de sortie
`sprinkler` : besoin et doses), `LWT_GameFarming.lua` (adaptateur de l'agriculture vanilla),
`Commands/LWT_CmdSwitchValve.lua`, `LWT_Publisher.lua` (port `visuals` : jet annoncé quand il démarre ou s'arrête),
`LWT_GameBroadcast.lua` (envoi d'une commande serveur à tous ou à un joueur, solo par `triggerEvent`, repris par
`LWT_GameSounds.lua`), `LWT_GameVisuals.lua`, `LWT_Commands.lua` (`events` dans le contexte), `LWT_Server.lua` ; client
`LWT_SprinklerJet.lua` (jet animé, D08a) ; `tools/check_mod.py` (`Events.OnTick` permis dans ce seul fichier, liste
`PER_FRAME_ALLOWED` qui cite D08a) ; `LWT_moveables.txt` (`Base.Mov_LiveWater_Sprinkler`), recette
`LWTBuildSprinkler`, option `SprinklerRadiusMultiplier`, traductions EN et FR (dont `UI.json` : option de mod) ; tests
`tests/test_sprinkler.py`, `test_api.py` (révision 8).
Vérifié dans le vanilla 42.22 (confirmé statiquement) : `SFarmingSystem.instance:getLuaObjectAt(x, y, z)` donne la
plante ; besoin = `waterNeeded` du stade (`farming_vegetableconf.calcWater` : la plante pousse quand `waterLvl >=
waterNeeded`) ; `SPlantGlobalObject:water(nil, doses)` ajoute 10 par dose, note l'heure et sauvegarde
(`SPlantGlobalObject.lua:501-518`, `saveData` → `transmitModData`) ; dose vanilla 200 ml
(`ZomboidGlobals.farmingFluidContainerMillilitresPerUse`). Calque : `addAttachedAnimSpriteByName`,
`RemoveAttachedAnim(i)`, `setAnimating` (`IsoObject.java:1855, 3210, 5919`) ; options de mod `PZAPI.ModOptions`
(`client/PZAPI/ModOptions.lua`).
Choix faits sans l'utilisateur :
- rayon 2 (D19, champ `radius` de la définition) × option `SprinklerRadiusMultiplier` (0,5 à 5, arrondi, 10 cases au
  plus) ; cercle `dx² + dy² <= r²`, même niveau ; P13 (5 cases) s'obtient avec l'option à 2,5 ;
- une plante a besoin d'eau si elle est vivante, semée (pas un sillon), et `waterLvl < waterNeeded` ; elle reçoit
  `ceil((waterNeeded - waterLvl) / 10)` doses, les plus proches d'abord ; le réseau ne sert que ces doses (0,2 L
  chacune), une eau trop courte ne donne que des doses entières ; l'eau croupie convient (règle vanilla) ;
- l'arroseur se pose fermé ; « Ouvrir la vanne » / « Fermer la vanne » au clic droit (menu générique), sans action
  chronométrée (E13) ; `valveChanged` émis ; il est « en marche » (sprite 52-55, jet) quand il a arrosé au dernier
  pas, sinon arrêté (rien à arroser, vanne fermée, pas d'eau, pression) ;
- jet : images 80-103 attachées par le client (`addAttachedAnimSpriteByName`), 6 par seconde au plus (167 ms) ;
  candidats suivis par `LoadGridsquare`, `ReuseGridsquare`, `OnObjectAdded` et l'ordre serveur `jet { x, y, z }`
  (le client relit l'état recopié de la case) ; un jet resté sauvegardé en solo (sprite de tuile) est retiré au
  chargement de la case ; option de mod « Jet des arroseurs animé » (`PZAPI.ModOptions`, cochée par défaut) : décochée,
  jet fixe sans `OnTick` ;
- recette sans compétence : clé à tuyau gardée, 2 sections de tuyau, 1 ferraille, 1 planche (le piquet).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 220 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 85 Lua file(s) checked`.
Non testé en jeu.

### E12 — Arroseur automatique

Fichiers : capacité `controller` `timer`, recette `LWTUpgradeSprinkler` (niveau d'Électricité 2 par défaut). Tests
rouges : déclenchement par tranche d'heures ; minuterie sans courant inerte ; ouverture manuelle toujours possible.

Clôture (2026-11-18). Fichiers : `Parts/LWT_PartSprinklerAuto.lua` (`LiveWater:SprinklerAuto` : mêmes capacités que
l'arroseur manuel, `controller` `timer` toutes les 6 heures, 5 W ; `variants` `off` 56-59 et `on` 60-63),
`Capabilities/LWT_CapController.lua` (minuterie : réglages `every`, `watts`, `choices` ; crochets `power`, `powered`,
`prepare`, `opens`, `stepped`, `timer`, `setTimer`, `actions` avec sous-menu, `lines`), `LWT_Parts.lua`
(`Parts:closed` : une vanne fermée qu'aucune capacité ne tient ouverte ; `choices` des actions), `LWT_Network.lua` et
`LWT_Flow.lua` (fermeture lue par `Parts:closed`), `LWT_Capabilities.lua` et `LWT_API.lua` (révision 9), `LWT_Tiles.lua`
(`JET_FIRST`, `JET_FRAMES` partagés par les deux arroseurs), `LWT_Protocol.lua` (`setTimer`), `LWT_Reasons.lua`
(`not_timer`, `out_of_bounds`) ; serveur `LWT_Clock.lua` (`prepare` de chaque membre après le courant, `ctx.hours`),
`Commands/LWT_CmdSetTimer.lua`, `LWT_Power.lua` (inscrit un type seulement si une pièce neuve a besoin de courant ; le
résumé de Live Wire ne compte que les pompes), `LWT_Server.lua` ; client `LWT_PartMenu.lua` (sous-menu des `choices`,
arguments envoyés avec la commande) ; `LWT_moveables.txt` (`Base.Mov_LiveWater_SprinklerAuto`), recette
`LWTUpgradeSprinkler`, options `SprinklerTimerMin` et `SprinklerTimerMax`, traductions EN et FR ; tests
`tests/test_timer.py`, doublures `getGameTime` (`test_placement.py`) et `addSubMenu` (`test_upkeep.py`), `test_api.py`
(révision 9).
Choix faits sans l'utilisateur :
- tranche = `floor(heures du monde / X)` comparée au numéro de la dernière tranche arrosée (D09) ; à une tranche
  nouvelle, avec du courant, la minuterie tient la vanne ouverte tant que l'arroseur est servi, et la relâche au
  premier pas où il ne l'est pas (plantes servies, pas d'eau, pression) ; une tranche manquée sans courant n'est pas
  rattrapée ;
- X = 6 heures par défaut, choisi au clic droit (« Minuterie d'arrosage » → toutes les 1, 2, 3, 4, 6, 8, 12 ou 24 h),
  borné par les options `SprinklerTimerMin` (1) et `SprinklerTimerMax` (24) ; refus « intervalle non permis » ;
- la minuterie tire 5 W en permanence (consommateur Live Wire `LiveWater_LiveWater_SprinklerAuto`, sinon règle
  vanilla de la case) ; elle n'est pas comptée parmi les pompes du résumé de Live Wire ; l'arroseur manuel n'est
  plus inscrit à Live Wire (sa capacité `controller` n'a pas besoin de courant) ;
- la vanne reste manœuvrable à la main : ouverte, l'arroseur arrose sans minuterie ni courant ;
- recette : Électricité 2, tournevis gardé, l'arroseur manuel, 2 débris électroniques, 1 fil électrique ; 10 XP ;
  l'état de l'arroseur manuel n'est pas repris (objet neuf).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 231 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 87 Lua file(s) checked`.
Non testé en jeu.

### E13 — Interface

Fichiers : `client/LiveWater/LWT_ContextMenu.lua`, `LWT_NetworkView.lua`. Surbrillance persistante posée et retirée,
aucun abonnement par image.

Clôture (2026-11-18). Fichiers : client `LWT_PartAction.lua` (action chronométrée des menus : marche jusqu'à la case,
`faceLocation`, animation, commande envoyée à la fin), `LWT_PartMenu.lua` (`send` passe par l'action : toutes les
actions des pièces, des barils et du réseau public), `LWT_PipeMenu.lua` (poser, démonter : action de 150),
`LWT_NetworkView.lua` (vue du réseau) ; `shared/LiveWater/LWT_PlaceRules.lua` (curseur : case qui porte déjà une pièce
refusée, ligne rouge), `Capabilities/LWT_CapOutlet.lua` (crochet `status`), `LWT_Capabilities.lua` et `LWT_API.lua`
(révision 10), `LWT_Protocol.lua` (`showNetwork`, `network`) ; serveur `LWT_Placement.lua` (port `notify` : un meuble que
le réseau refuse est dit aux joueurs proches), `LWT_Topology.lua` (`networkOf`), `Commands/LWT_CmdShowNetwork.lua`,
`LWT_GamePlayers.lua` (`all`), `LWT_Commands.lua` (port `replies`), `LWT_Server.lua` ; traductions EN et FR ; tests
`tests/test_interface.py`, banc `tests/lwt_harness.py` (actions chronométrées exécutées aussitôt, marche notée),
`test_api.py` (révision 10). `LWT_ContextMenu.lua` de la fiche n'est pas créé : les menus existants (`LWT_PartMenu`,
`LWT_PipeMenu`) en tiennent lieu.
Vérifié dans Java 42.22 (confirmé statiquement) : une action Lua sans `complete` n'est pas confiée au serveur en
multijoueur (`LuaTimedActionNew` : `useCustomRemoteTimedActionSync`, `LuaTimedActionNew.java:47-48, 126-130`) ;
`perform` s'exécute sur le client (`IsoGameCharacter.java:8476-8479`) ; `IsoObject.setHighlighted(bool, renderOnce)`
et `setHighlightColor(r, g, b, a)` (`IsoObject.java:4684, 4742`).
Choix faits sans l'utilisateur :
- toute action d'un menu de LiveWater (vanne, minuterie, filtre, pompe, baril, réseau public) fait marcher le joueur
  à côté de la case puis dure 60 ; poser ou démonter un tuyau dure 150 ; l'action n'envoie la commande qu'à la fin,
  l'autorité contrôle tout de nouveau ;
- pas de curseur de construction pour les tuyaux : une section par case cliquée, la forme suit les voisins (le
  curseur vanilla n'apporte rien pour une pièce d'une case sans orientation) ;
- refus à la pose (D14) : au curseur, une case qui porte déjà une pièce de LiveWater (ligne rouge « occupée ») ; ce
  que seul le réseau sait (ports pleins, source) est dit, à la pose, aux joueurs à 3 cases de la pièce par une note ;
  la pièce reste un décor (E07) ;
- vue du réseau : « Afficher le réseau d'eau » sur une pièce ; le serveur renvoie les cases de son réseau (500 au
  plus) ; chaque pièce est mise en surbrillance persistante (`setHighlighted(true, false)`) : vert = sortie servie ou
  pleine, rouge = sans pression, ambre = eau non filtrée refusée, gris = fermée ou sans eau, bleu = tuyaux et pompes ;
  « Masquer le réseau d'eau » l'efface, et son infobulle compte les sorties de chaque état ; une nouvelle vue remplace
  l'ancienne ; les états « sans pression » et « eau non filtrée » se lisent aussi dans « Informations » de chaque sortie.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 242 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 90 Lua file(s) checked`.
Non testé en jeu.

### E15 à E21 — Parité avec Water Pipes

Une pièce ou une capacité par fonctionnalité de la liste P01-P23 de l'ADR (D24), un fichier chacune, tests rouges
d'abord. Aucune reprise de code, d'asset, de texte ni de nom (D25). E14 de la version précédente du plan devient E22.

### E15 — Pompe : interrupteur, usure, pannes, réparation, information, son

Clôture (2026-11-18). Fichiers : `Capabilities/LWT_CapPump.lua` (état `on`, `efficiency`, `broken` ; réglages `wear`,
`breakdownBelow`, `breakdownChance`, `repairItem`, `repairCount`, `repairTool`, `sound`, `noiseRadius`,
`noiseVolume` ; crochets `switchable`, `switch`, `repairable`, `repair`, `sound`, lignes état, débit, rendement,
actions), `LWT_CapIntake.lua` (ligne de la source), `LWT_Parts.lua` (`first` rend jusqu'à 4 valeurs),
`LWT_Capabilities.lua` et `LWT_API.lua` (révision 4), `LWT_Protocol.lua` (`switchPump`, `repairPump`, `sound`),
`LWT_Reasons.lua`, `Parts/LWT_PartPondPump.lua` (2 ferrailles et une clé, boucle `GeneratorLoop`), serveur
`Commands/LWT_CmdSwitchPump.lua`, `LWT_CmdRepairPump.lua`, `LWT_Publisher.lua` (boucle sonore annoncée au changement
et répétée à chaque pas, bruit pour les zombies), `LWT_GameSounds.lua` (`sendServerCommand` à tous les clients,
`triggerEvent("OnServerCommand")` en solo, `addSound(nil, …)`), `LWT_Clock.lua` (`random` dans le contexte du pas),
`LWT_GamePlayers.lua` (`count`), `LWT_Server.lua` ; client `LWT_PumpSounds.lua` (un émetteur libre par case,
`playSoundImpl(nom, false, nil)`, arrêt sur ordre), `LWT_PartMenu.lua` (option « Informations » dont l'infobulle
montre les lignes) ; `sandbox-options.txt` (`PumpWearMultiplier`), traductions EN et FR ; tests `tests/test_upkeep.py`.
Choix faits sans l'utilisateur :
- usure par défaut 0,01 point de rendement par minute de marche (environ une semaine de marche continue de 100 à
  0 %), × option sandbox (0 = aucune usure) ; débit proportionnel au rendement ; sous 20 %, 2 % de risque de panne
  par pas de marche ; à 0 % la pompe s'arrête ; une panne arrête seulement (Q05) ;
- réparation complète (100 %) d'une pompe arrêtée (éteinte, en attente ou en panne) : 2 `Base.ScrapMetal`
  consommées et une clé (`tags[base:wrench]`) gardée ; refus si elle tourne (« Éteignez-la d'abord ») ou n'en a pas
  besoin ;
- l'interrupteur coupe aussitôt la pompe (sprite et son), en plus de l'arrêt automatique ;
- fenêtre d'information réduite à l'infobulle d'une option « Informations » du clic droit (état, débit, rendement,
  filtre, source), lue dans l'état recopié ; aucun dessin par image ;
- son : boucle vanilla `GeneratorLoop` (42.22, `sounds_object_generator.txt`), jouée par chaque client sur ordre du
  serveur (ordre répété à chaque pas pour les joueurs arrivés depuis, donc jusqu'à 10 minutes de silence pour eux) ;
  bruit pour les zombies `addSound(nil, x, y, z, 20, 20)` à chaque pas de marche (un générateur vanilla : 40, 60).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 134 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 52 Lua file(s) checked`.
Non testé en jeu.

### E16 — Débitmètre

Clôture (2026-11-18). Fichiers : `Parts/LWT_PartFlowMeter.lua` (`LiveWater:FlowMeter` : sprites par masque des tuyaux
droits, 20 est-ouest pour les masques 2, 8, 10 et 21 nord-sud pour 1, 4, 5 ; `conduit` à 2 ports, `meter`),
`Capabilities/LWT_CapMeter.lua` (nouvelle capacité : litres et qualité du dernier pas, lignes « 10 dernières
minutes » et fluide), `LWT_CapConduit.lua` (réglage facultatif `ports`), `LWT_Flow.lua` (litres et qualité de l'eau
servie portés sur chaque pièce du chemin : `through`, `qualityAt`), `LWT_Clock.lua` (qualité par pièce dans le bilan
de `stepped`), `LWT_API.lua` (capacité de départ `meter`, révision 5), `LWT_Capabilities.lua` ;
`LWT_moveables.txt` (`Base.Mov_LiveWater_FlowMeter`), recette `LWTBuildFlowMeter`, traductions EN et FR ; tests
`tests/test_meter.py` ; `tests/test_api.py` prend `gauge` comme exemple de capacité nouvelle (`meter` est désormais
inscrite).
Choix faits sans l'utilisateur :
- un seul type de pièce : le compteur suit son tuyau (est-ouest ou nord-sud) par la table de formes, comme un tuyau ;
  seul ou dans un coude, il garde le sprite de sa pose ; 2 tuyaux au plus (pièce en ligne) ;
- il compte l'eau qui passe par lui vers les sorties servies au dernier pas de dix minutes ; le fluide est l'eau,
  propre après un filtre, non filtrée avant (réseau d'essence : D26, E20) ;
- « Informations » du clic droit (menu générique d'E15) montre ces lignes ; pas de fenêtre propre ;
- recette sans compétence : une section de tuyau, une petite tôle, 2 vis, tournevis gardé.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 140 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 54 Lua file(s) checked`.
Non testé en jeu.

### E17 — Puits comme source d'eau propre

Clôture (2026-11-18). Fichiers : `Sources/LWT_SourceWell.lua` (sorte `well` : sprite `camping_01_16`, eau propre),
`LWT_API.lua` (`registerSource`, révision 6), `Capabilities/LWT_CapIntake.lua` (qualité de la sorte relevée, lue dans
`ctx.sources`, réglage `quality` en repli), `LWT_Capabilities.lua`, serveur `LWT_Clock.lua` (`sources` dans le
contexte du pas), `LWT_Server.lua` ; client `LWT_PartMenu.lua` (arguments des lignes passés en texte entier à
`getText`, correction d'E15) ; traductions EN et FR (`IGUI_LWT_Source_well`, refus `IGUI_LWT_NoSource` qui cite le
puits) ; tests `tests/test_well.py`.
Choix faits sans l'utilisateur :
- même pièce que la pompe d'étang : posée contre un puits (une des 8 cases voisines porte un objet `camping_01_16`),
  elle relève la sorte `well` et donne de l'eau propre, qui va à la maison sans filtre ; à côté d'un puits et d'une eau
  naturelle, le puits l'emporte (sortes propres essayées d'abord) ;
- seul `camping_01_16` est retenu : c'est le sprite de l'entité vanilla `Well` (42.22, `entity_well.txt`) ; les tuiles
  `camping_01_64`-`67` portent aussi `waterAmount = 999999` mais ressemblent à des abreuvoirs (`CanAttachAnimal`),
  non vérifiées : laissées de côté, un autre mod peut les inscrire par `registerSource` ;
- le puits est une source inépuisable comme l'eau naturelle ; tirer sur la réserve du puits (son `FluidContainer`
  de 10 000 L) reste possible plus tard par le point d'extension `available` de la capacité `intake`.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 147 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 55 Lua file(s) checked`.
Non testé en jeu.

### E19 — Sous-sols et lave-linge

Clôture (2026-11-18). Fichiers : `shared/LiveWater/LWT_InletArea.lua` (niveaux sous terre jusqu'à
`BASEMENT_LEVELS` = 2 ; une case sous terre est servie si elle appartient au bâtiment ou si la case de la même colonne
au rez-de-chaussée lui appartient), tests `tests/test_basement.py`.
Lave-linge (P16), confirmé statiquement : en 42.22 les tuiles `IsoClothingWasher` (4) et `IsoCombinationWasherDryer`
(4) de `appliances_laundry_01` portent le drapeau `waterPiped` (`media/tile_definitions/newtiledefinitions.tiles.txt`,
par exemple `appliances_laundry_01_0`) ; le menu vanilla « Raccorder » vient de Java pour tout objet `waterPiped`
(`ISWorldObjectContextMenuLogic.java:466-471, 1104-1122`) et le lave-linge tire son eau par `getFluidAmount` /
`useFluid` (`ClothingWasherLogic.java:74, 89`). Il est donc servi comme un évier, sans code propre : aucun cas
particulier n'est ajouté.
Choix faits sans l'utilisateur :
- deux niveaux de sous-sol au plus (les sous-sols vanilla de 42.22 descendent d'un niveau, rarement deux) ; le relais
  d'un point d'eau du sous-sol se pose au rez-de-chaussée, au-dessus de lui ;
- « emprise » lue au rez-de-chaussée (niveau 0) : une cave sous un perron ou un garage hors du bâtiment n'est pas
  servie.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 167 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 62 Lua file(s) checked`.
Non testé en jeu.

### E20 — Raccord de baril

Clôture (2026-11-18). Fichiers : `Parts/LWT_PartBarrelFitting.lua` (`LiveWater:BarrelFitting` : `variants` `fill`
64-67, `fill_low` 68-71, `pump` 72-75), nouvelle capacité `Capabilities/LWT_CapFitting.lua` (mode « Remplir » ou
« Pomper », débit 50 L par pas ; crochets `outlet` (type `barrelFill`, fluide accepté en quatrième résultat), `draw`,
`sense`, `fittingMode`, `setFittingMode`, `stepped`, `status`, `look`, `actions`, `lines`), `LWT_Containers.lua`
(registre des conteneurs : forme par sprite ou nom d'entité, `low` pour les caisses bâchées, inconnu = `tall`),
`LWT_Flow.lua` (pièces qui puisent : les pompes tirent le baril au lieu de leur prise, un fluide par réseau, famille
`fuel` jamais purifiée, état `wrong_fluid`, `drawn` dans le bilan), `LWT_Events.lua` (`waterDrawn`),
`LWT_Diagnosis.lua` (`wrong_fluid`), `LWT_Capabilities.lua` et `LWT_API.lua` (révision 11, `registerContainer`),
`LWT_Protocol.lua` (`switchFitting`), `LWT_Reasons.lua` (`not_fitting`) ; serveur `LWT_Fittings.lua` (tâche de
l'horloge : conteneur relevé derrière le raccord ; gestionnaire `barrelFill` ; litres puisés retirés),
`LWT_GameContainers.lua` (adaptateur : baril ou récupérateur, pompe à essence d'une station), `LWT_Clock.lua`
(`waterDrawn`), `Commands/LWT_CmdSwitchFitting.lua`, `LWT_Server.lua` ; client `LWT_NetworkView.lua` (couleur de
`wrong_fluid`) ; `LWT_moveables.txt` (`Base.Mov_LiveWater_BarrelFitting`), recette `LWTBuildBarrelFitting`,
traductions EN et FR ; tests `tests/test_fitting.py`, doublure `tests/lwt_fakes.py` (tous les événements du bus notés),
`test_api.py` (révision 11).
Vérifié dans le vanilla 42.22 (confirmé statiquement) : récupérateurs bas = caisses bâchées `carpentry_02_54`
(`RainCollector`, 400 L) et `carpentry_02_120` (`RainCollector_Tarp`, 400 L), ronds `carpentry_02_122` à `_127`
(600 L) (`generated/entities/outdoors/entity_raincollector*.txt`) ; `FluidContainer` : `addFluid(Fluid, litres)`,
`removeFluid(litres)`, `getSpecificFluidAmount` (`FluidContainer.java:846, 880`) ; pompe à essence : propriété de tuile
`fuelAmount`, `getPipedFuelAmount` (courant exigé sauf essence illimitée) et `setPipedFuelAmount`
(`IsoObject.java:2461-2540`).
Choix faits sans l'utilisateur :
- le conteneur est sur la case derrière le raccord (à l'opposé de son orientation : orienté S, tuyau au sud, baril
  au nord, comme dessiné), sinon sur le premier autre côté qui en porte un ; conteneur = baril raccordable
  (`LWT_WaterObjects.isBarrel` : 20 L ou plus) ou pompe à essence d'une station (« Pomper » seulement) ;
- « Remplir » : sortie de coût 1, au plus 50 L par pas et jamais plus que la place libre (aucune fuite) ; un baril
  vide prend tout fluide, un baril d'eau seulement de l'eau, un baril d'essence seulement de l'essence, un baril d'un
  autre liquide rien (`wrong_fluid`) ;
- « Pomper » : quand un raccord en « Pomper » atteint par l'eau contient de l'eau ou de l'essence, les pompes du réseau
  tirent ce baril au lieu de leur prise (au plus leur débit et 50 L par raccord, le plus proche d'abord) ; un fluide
  par réseau : celui du raccord le plus proche, les autres ne donnent rien ce pas ; baril vide : la pompe reprend sa
  prise ; l'eau du baril garde sa qualité (pluie croupie : le robinet la purifie, règle vanilla) ;
- réseau d'essence : seuls les raccords en « Remplir » le servent ; arrivée d'eau et arroseurs disent « les tuyaux
  transportent de l'essence » (`wrong_fluid`) ; un filtre ne change pas l'essence ; le compteur dit « essence » ;
- sprite choisi par le serveur : `pump` en « Pomper », sinon `fill_low` pour un conteneur inscrit bas, `fill`
  sinon ; forme par sprite ou nom d'entité, extensible par `LiveWater.API.registerContainer` ;
- la cuve d'une station : il faut une pompe de LiveWater dans le réseau (posée près d'une eau ou d'un puits) : la pompe
  d'étang tire alors l'essence de la pompe de la station par le raccord ; pas de pompe propre au raccord ;
- recette sans compétence : clé à tuyau gardée, 1 section de tuyau, 1 `Base.RubberHose`.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 255 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 96 Lua file(s) checked`.
Non testé en jeu.

### E25 — Conteneurs remplis

Clôture (2026-11-18). Fichiers : `shared/LiveWater/LWT_Containers.lua` (champ `clean`, conteneurs inscrits d'office
`WaterDispenser`, `admits`, `cleanOnly`, `parseList`, définition d'un nom de la liste sandbox),
`LWT_WaterObjects.lua` (`isVessel` : objet à `FluidContainer` utilisable ; `isBarrel` = `isVessel` de 20 L ou plus),
`Capabilities/LWT_CapFitting.lua` (conteneur à eau propre : la sortie « Remplir » exige de l'eau propre),
`LWT_API.lua` (révision 12 : champ `clean` de `registerContainer`) ; serveur `LWT_GameContainers.lua` (tout récipient
admis par le registre ou la liste), `LWT_Fittings.lua` (forme et eau propre lues avec la liste), `LWT_Server.lua`
(option lue à chaque pas) ; `sandbox-options.txt` (`FillContainers`, chaîne, `WaterDispenser` par défaut),
traductions EN et FR ; tests `tests/test_containers.py`, `test_api.py` (révision 12).
Vérifié dans le vanilla 42.22 (confirmé statiquement) : fontaine à eau = entité `WaterDispenser`, `FluidContainer` de
15 L (`generated/entities/appliances/workstations/entity_waterdispenser.txt`), sous la limite de 20 L des barils : elle
n'est donc servie que parce qu'elle est inscrite.
Choix faits sans l'utilisateur :
- L08 passe par le raccord de baril en « Remplir » (D28) : un conteneur inscrit se remplit quand un raccord est posé
  contre lui ; aucun remplissage par les réservoirs invisibles de la maison ;
- un conteneur est servi s'il a 20 L ou plus (barils, récupérateurs), ou si son sprite ou le nom de son entité est
  inscrit par l'API ou listé dans l'option `FillContainers` (noms séparés par `;`) ;
- fontaines à eau et noms listés : eau propre seulement (eau non filtrée refusée, « eau non filtrée »), pour ne pas
  rendre une eau à boire croupie ; un conteneur inscrit par l'API choisit (`clean`) ;
- l'option est relue à chaque pas (changement en cours de partie pris en compte).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 260 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 96 Lua file(s) checked`.
Non testé en jeu.

### E21 — Retrait propre du mod

Clôture (2026-11-18). Fichiers : serveur `LWT_Removal.lua` (retrait : départ, tâche de l'horloge placée en premier,
fin), `Commands/LWT_CmdRemoveAll.lua`, `LWT_GamePlayers.lua` (`isAdmin`), `LWT_Commands.lua` (`removal` dans le
contexte), `LWT_Server.lua` ; client `LWT_AdminMenu.lua` (option « Retirer LiveWater de ce monde (admin) » et
confirmation) ; `shared/LiveWater/LWT_Protocol.lua` (`removeLiveWater`), `LWT_Reasons.lua` (`not_admin`) ; traductions
EN et FR ; tests `tests/test_removal.py`.
Vérifié dans le vanilla 42.22 (confirmé statiquement) : droits d'administration côté serveur par le rôle du joueur,
`player:getRole():hasCapability(Capability.UseDebugContextMenu)` (`server/ClientCommands.lua:167`, même capacité que
le menu de débogage).
Choix faits sans l'utilisateur :
- action proposée au clic droit à un administrateur (capacité de rôle `UseDebugContextMenu`) sur un serveur, et au
  joueur en solo, avec une fenêtre de confirmation ; le serveur refait le contrôle du rôle (`not_admin`) ;
- retrait : chaque pièce d'un type inscrit sur une case chargée quitte le réseau et sa tuile est retirée ; l'événement
  `partRemoved` emporte les réservoirs relais de ses arrivées d'eau (ceux d'une case non chargée attendent dans les
  orphelins, retirés au chargement) et débranche ses barils ; les points d'eau gardent leur état vanilla (raccordés,
  sans source) ; les pièces des cases non chargées partent quand leur zone se charge (tâche de l'horloge, drapeau
  `removal` dans la ModData globale : le retrait continue après un redémarrage) ;
- le retrait est définitif pour ce monde : une pièce posée ensuite est retirée au pas suivant ; aucun objet n'est rendu
  (ils disparaîtraient avec le mod) ; les pièces d'un type qui n'est plus inscrit restent dans le registre (D03) ;
- la marche à suivre (retirer, attendre que les zones soient chargées, sauvegarder, se désabonner) ira dans le wiki à
  E22.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 266 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 99 Lua file(s) checked`.
Non testé en jeu.

### E23 — Baril raccordé à la maison

Clôture (2026-11-18). Fichiers : `shared/LiveWater/LWT_Reserve.lua` (pur : réserve partagée, gravité, mise en
réserve), `LWT_WaterObjects.lua` (règles des objets d'eau des deux côtés : point d'eau, baril raccordable, marques,
eau seulement, eau de la ville), `LWT_InletArea.lua` (`reaches` : dans la zone ou juste au-dessus, jusqu'au toit),
`LWT_Protocol.lua`, `LWT_Reasons.lua` (`not_barrel`, `no_inlet`, `not_connected`) ; serveur `LWT_HouseBarrels.lua`
(raccord, débranchement, mise en réserve, tâche de l'horloge après les relais), `LWT_GamePlumbing.lua` (`barrel`,
`markBarrel`, `transfer` par `FluidContainer.Transfer`), `Commands/LWT_CmdConnectBarrel.lua`,
`LWT_CmdDisconnectBarrel.lua`, `LWT_CmdReserveBarrel.lua`, `LWT_CmdChecks.lua` (`PIPE_WRENCH`), `LWT_Server.lua`
(service, commandes, pompe du réseau, baril emporté débranché) ; client `LWT_BarrelMenu.lua`, `LWT_PartMenu.lua`
(`squareOf`, `send` partagés) ; traductions EN et FR ; tests `tests/test_barrels.py`, doublure `hasModData` dans
`tests/test_placement.py`.
Vérifié dans l'API 42.22 (confirmé statiquement) : récupérateurs d'eau de pluie = entités avec un composant
`FluidContainer` (400 et 600 L, `generated/entities/outdoors/entity_raincollector*.txt`) ; `getFluidContainer()`,
`getAmount`, `getCapacity`, `getFreeCapacity`, `getSpecificFluidAmount(Fluid.Water | Fluid.TaintedWater)`,
`FluidContainer.Transfer(source, cible, litres)` qui garde la proportion de chaque fluide
(`FluidContainer.java:1027-1081`).
Choix faits sans l'utilisateur :
- baril raccordable : tout objet du monde avec un `FluidContainer` d'au moins 20 L, ni point d'eau, ni relais, ni
  marqué par Live Wire (`LiveWireRelay`, `LiveWireBarrel`, D21) ;
- « dans le bâtiment ou sur son toit » : case du bâtiment, ou case juste au-dessus d'une case du bâtiment (jusqu'au
  niveau au-dessus du dernier étage), dans la portée de l'arrivée d'eau ; l'arrivée d'eau la plus proche est choisie ;
- raccord et débranchement à la clé à tuyau (gardée) ; mise en réserve sans outil ;
- l'eau des barils passe dans les relais avant que le réseau ne complète ; le baril donne son eau telle quelle (eau de
  pluie croupie : le robinet la purifie, règle vanilla) ;
- gravité : un baril sert les points d'eau de son niveau et des niveaux en dessous ; une pompe dans le réseau de
  l'arrivée d'eau, ou du courant sur la case du baril (générateur ou réseau public, règle vanilla), lève la règle ;
- réserve partagée : les barils qui peuvent servir un relais se vident ensemble au prorata de leur eau ; ceux « en
  réserve » seulement quand les autres n'ont plus rien pour ce relais ; un baril vide reste raccordé ; un baril qui
  contient autre chose que de l'eau ne donne rien jusqu'à ce qu'il soit vidé (il reste raccordé) ;
- un baril retiré (ramassé, détruit) est débranché ; un baril absent d'une case chargée est oublié au pas suivant ;
  le retrait de l'arrivée d'eau débranche ses barils ;
- L03 : le robinet montre l'eau de son relais (25 L au plus), pas le total des barils ; les barils se vident ensemble.
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 180 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 69 Lua file(s) checked`.
Non testé en jeu.

### E26 — Base du joueur, diagnostic, ramassage

Clôture (2026-11-18). Fichiers : `shared/LiveWater/LWT_InletArea.lua` (mode `base` : hors bâtiment de la carte, cercle
de portée, niveau de l'arrivée d'eau et 3 étages au-dessus), `LWT_Diagnosis.lua` (pur : raison d'une arrivée d'eau,
ligne d'un point d'eau) ; serveur `LWT_Diagnostics.lua` (tâche de l'horloge après les relais et les barils : raison
notée sur les relais vides), `LWT_Relays.lua` (`mark`, portée `BaseRange`), `LWT_HouseBarrels.lua` (`placed`, `has`),
`LWT_Server.lua` (tâche, baril reposé) ; client `LWT_FixtureMenu.lua` (ligne « Pas d'eau : raison ») ; option
`BaseRange`, traductions EN et FR ; tests `tests/test_base.py`.
Choix faits sans l'utilisateur :
- base du joueur = arrivée d'eau qui ne touche aucun bâtiment de la carte (un bâtiment construit par les joueurs,
  `BuildingDef:isUserDefined`, compte comme une base) ; portée `LiveWater.BaseRange` 12 par défaut ; niveaux : celui
  de l'arrivée d'eau et 3 au-dessus ; barils raccordables dans ce cercle, jusqu'au niveau au-dessus ; le menu vanilla
  « Raccorder » n'existe que dans une pièce (`isInARoom`, pièces de joueur comprises), règle du jeu gardée ;
- diagnostic : une ligne grisée « Pas d'eau : raison » au clic droit d'un point d'eau sans eau qui tire, ou peut tirer,
  sur une source extérieure ; raisons dans l'ordre : aucune source au-dessus (« aucune arrivée d'eau ne le dessert »),
  pas raccordé, réservoir d'autre chose vide, puis la raison notée par le serveur sur le relais (eau non filtrée,
  pression, pas d'eau dans les tuyaux, vanne fermée, gravité, barils vides, ni pompe ni baril), sinon « l'eau arrive » ;
  la raison est celle du dernier pas (10 minutes au plus) et n'est notée que sur les relais vides ;
- ramassage (L12) : l'arrivée d'eau emporte ses relais et débranche ses barils (E09, E23) ; un baril emporté est
  débranché, et un baril reposé qui porterait encore une marque de raccord l'oublie ; un point d'eau reposé est remis
  « à raccorder » par le vanilla (`canBeWaterPiped`), ce qui efface aussi un raccord à l'eau de la ville (E27).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 191 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 72 Lua file(s) checked`.
Non testé en jeu.

### E27 — Raccordement au réseau public

Clôture (2026-11-18). Fichiers : `shared/LiveWater/LWT_CityWater.lua` (pur : règle partagée par le menu et la
commande), `LWT_WaterObjects.lua` (`cityInfo`), `LWT_Protocol.lua` (`cityWater`), `LWT_Reasons.lua` (`not_fixture`,
`not_map_building`, `no_city_water`) ; serveur `Commands/LWT_CmdCityWater.lua`, `LWT_GamePlumbing.lua`
(`cityWaterRuns`, `cityFixture`, `connectCity`), `LWT_Server.lua` (commande, port `plumbing` dans le contexte des
commandes) ; client `LWT_CityWaterMenu.lua` ; traductions EN et FR ; tests `tests/test_city.py`.
Mécanisme (confirmé statiquement, Java et Lua 42.22) : `IsoObject.isWaterInfinite` (`IsoObject.java:2542-2564`) donne
l'eau de la ville à un point d'eau `waterPiped` dans une pièce de la carte (`getRoom()`), sans source extérieure, case
sans `isNoWater()`, avant la coupure, et sans ModData `canBeWaterPiped = true` ; la pose d'un meuble `waterPiped` écrit
`canBeWaterPiped = true` (`ISMoveableSpriteProps.lua:2491-2493`) ; le raccord vanilla à la clé écrit `false` mais
passe `usesExternalWaterSource` à vrai (`ISPlumbItem.lua:31-37`), d'où un point d'eau sans eau de la ville.
Choix faits sans l'utilisateur :
- l'action efface la clé `canBeWaterPiped` (absente, comme un point d'eau d'origine) et garde
  `usesExternalWaterSource` faux, puis `transmitModData` : le point d'eau se comporte comme un point d'origine (eau de la
  ville, coupure le même jour, réserve vanilla restante après la coupure) ;
- proposée seulement pour un point d'eau posé par un joueur et pas raccordé à la clé (un point d'eau déjà sur un baril
  ou un relais ne l'a pas), dans une pièce d'un bâtiment de la carte, case sans `isNoWater`, avant la coupure ; aucun
  outil ni durée (le point d'eau a déjà été posé à la clé) ;
- contrôles du serveur dans l'ordre : arguments, point d'eau posé et pas raccordé (`not_fixture`), portée
  (`too_far`), bâtiment de la carte (`not_map_building`), eau de la ville (`no_city_water`) ;
- reposer le point d'eau ailleurs le remet « à raccorder » (vanilla), ce qui efface ce raccord (L12).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 195 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 75 Lua file(s) checked`.
Non testé en jeu.

### E28 — Correctif du lave-linge raccordé en MP

Défauts vanilla 42.22, confirmés statiquement :
1. lave-linge à sec : sur le serveur, `ClothingWasherLogic.update` arrête un lave-linge qui n'a plus d'eau
   (`setActivated(false)`, `ClothingWasherLogic.java:74-75`) sans rien envoyer ; seul `cycleFinished` envoie
   `WASHER_STATE` (`:267-269`) ; le client sort de `update` avant ce contrôle (`:70-71`) et le croit en marche : son
   en boucle, linge bloqué (`isRemoveItemAllowedFromContainer` : vide ou arrêté, `:251-253`), et plus d'interrupteur
   puisqu'il n'a pas d'eau (`ClothingWasherToggle.lua:7`) ;
2. raccord d'un lave-linge simple : `ISPlumbItem:complete` envoie `USES_EXTERNAL_WATER_SOURCE`
   (`ISPlumbItem.lua:35`), mais `IsoClothingWasher.saveChange` et `loadChange` confient tout changement à sa logique
   (`IsoClothingWasher.java:62-70`), qui n'écrit que `WASHER_STATE` (`ClothingWasherLogic.java:171-181`) : les clients
   ne savent jamais qu'il est raccordé (le lave-linge séchant combiné, lui, le traite :
   `IsoCombinationWasherDryer.java:72-95`).

Clôture (2026-11-18). Fichiers : serveur `LWT_WasherFix.lua` (tâche de l'horloge, serveur seulement, option
`WasherFix`), `LWT_GamePlumbing.lua` (`washers`, `sendWasherState`, `markWasher`, points d'eau servis par un relais
mis en commun avec `feeds`), `LWT_Relays.lua` (`positions`), `LWT_Server.lua` (tâche, marque effacée quand un
lave-linge est reposé) ; `shared/LiveWater/LWT_WaterObjects.lua` (`WASHER_KEY`) ; client `LWT_WasherClient.lua` ;
option `LiveWater.WasherFix` (booléen, vrai par défaut), traductions EN et FR ; tests `tests/test_washer.py`.
`mod.info` : `incompatible=\LGExtendedPlumbing,\LGMainsWater` déjà présent (E01), vérifié par le test.
Choix faits sans l'utilisateur :
- seuls les lave-linge servis par un relais de LiveWater sont touchés (Q08), et seulement sur un serveur (en solo, une
  seule copie de chaque objet : pas de défaut) ;
- défaut 1 : quand un tel lave-linge est arrêté sur le serveur, son état est envoyé une fois
  (`sendObjectChange(IsoObjectChange.WASHER_STATE)`, comme le vanilla en fin de cycle), à la tâche de dix minutes :
  le client peut le croire en marche jusqu'à 10 minutes ;
- défaut 2 : le serveur pose sur un lave-linge simple ainsi servi la marque `LiveWaterWasher = { plumbed = true }`
  (`transmitModData`, qui arrive bien aux clients) ; le client applique `setUsesExternalWaterSource(true)` quand le
  joueur s'y intéresse : son menu au clic droit et l'interrupteur de sa fenêtre de conteneur (enveloppe de
  `ISLootWindowObjectControlHandler_ClothingWasherToggle.shouldBeVisible`, arguments et résultat gardés) ; aucun
  abonnement par image ;
- un lave-linge reposé perd la marque (L12).
Preuves :
- `python -B -m unittest discover -s tests` → `Ran 200 tests` … `OK` ;
- `python -B tools/check_mod.py` → `OK: 77 Lua file(s) checked`.
Non testé en jeu (le défaut et le correctif ne se voient qu'en multijoueur : E22).

### E22 — Traductions, parité, passage en jeu

Onze langues (comme Live Wire), wiki EN et FR, `autotest.json`. Tableau de parité P01-P23 rempli avec la preuve de
chaque ligne. Passage automatique SP et MP avec code de sortie, `summary` et dossier `runs/...`.

#### Parité

Inventaires de l'ADR-001 (D24 : P01-P23, D27 : L01-L14, M01). Fonctionnalités `F..` de
[specifications-fonctionnelles.md](../specifications-fonctionnelles.md) ; preuve = paragraphe de clôture de l'étape
et fichier de tests hors jeu (`tests/`). Rien de cette table n'est encore vérifié en jeu.

| # | Couverture LiveWater | Preuve |
|---|---|---|
| P01 | F02, F03 : pompe posée à côté d'une source, courant sur sa case (générateur, réseau public) ou Live Wire | E08, `test_pump.py` |
| P02 | F12 (puits, eau propre), F27-F28 (baril et pompe de station-service en « Pomper », essence) ; F02 (eau naturelle croupie) | E17 `test_well.py`, E20 `test_fitting.py` |
| P03 | F06 : interrupteur au clic droit, en plus de l'arrêt automatique | E15, `test_upkeep.py` |
| P04 | F07 : usure du rendement, débit proportionnel, pannes sous 20 %, arrêt à 0 %, option sandbox | E15, `test_upkeep.py` |
| P05 | F08 : réparation à l'arrêt, 2 ferrailles et une clé | E15, `test_upkeep.py` |
| P06 | non repris (Q05) : panne seulement, aucun incendie | ADR Q05 |
| P07 | F05 : cartouche filtrante usée au volume, option sandbox | E10, `test_filter.py` |
| P08 | F09 (« Informations » de la pompe), F03 (`display`, `summary` de Live Wire) | E15 `test_upkeep.py`, E08 `test_pump.py` |
| P09 | F01 : 16 formes raccordées seules | E03 `test_network.py`, E07 `test_sprites.py` |
| P10 | non repris (Q06) : l'arrivée d'eau dessert étages et sous-sols (F13, F14) | ADR Q06, E18 annulée |
| P11 | F31 : vanne d'arrêt `LiveWater:Valve` posée entre deux tuyaux, ouverte ou fermée au clic droit, coupe l'aval ; aussi la vanne de chaque arroseur (F21) | E22 `test_valve.py` (ajout du 2026-11-18), E03 `test_network.py`, E11 `test_sprinkler.py` |
| P12 | F11 : compteur d'eau en ligne, litres et fluide | E16, `test_meter.py` |
| P13 | F21 : arrose les plantes qui en ont besoin, rayon 2 × option (10 au plus) au lieu de 5 (choix d'E11, réglable) | E11, `test_sprinkler.py` |
| P14 | F22 : jet animé (D08a) et son d'arrosage vanilla `WaterCrops` (réglage `sound` de `spray`, boucle des joueurs démarrée et arrêtée par le même changement d'état que le jet, aucun bruit pour les zombies, aucun code par image) ; qu'il boucle bien 10 minutes en jeu (événement FMOD à point de maintien, arrêté par `stopOrTriggerSound` en vanilla) reste une hypothèse | E11, E22 `test_sprinkler.py` (ajout du 2026-11-18) |
| P15 | F10 : boucle sonore de la pompe en marche, bruit entendu par les zombies | E15, `test_upkeep.py` |
| P16 | F13, F14 : tous les points d'eau raccordés du bâtiment, lave-linge compris | E09 `test_inlet.py`, E19 `test_basement.py` |
| P17 | F27 : raccord de baril « Remplir » | E20, `test_fitting.py` |
| P18 | F14 : sous-sols jusqu'à 2 niveaux | E19, `test_basement.py` |
| P19 | recettes de LiveWater (Électricité 2 pour la pompe et la minuterie, XP) à la place du menu de construction | E08, E09, E11, E12, E16, E20 (scripts `LWT_recipes.txt`, contrôlés par `tools/check_mod.py` pour les traductions) |
| P20 | sandbox : `PumpFlowMultiplier` (F04), `FilterCapacityMultiplier` (F05), `PumpWearMultiplier` (F07), et 7 options de plus | E08, E10, E15 ; wiki `05-sandbox-options.md` |
| P21 | F30 : retrait propre par un administrateur ; pièces de type inconnu conservées (D03) | E21 `test_removal.py`, E05 `test_registry.py` |
| P22 | API publique `LiveWater.API` révision 13 (pièces, capacités, sources, conteneurs, événements) | E02 `test_api.py` ; wiki `06-for-modders.md` |
| P23 | 11 langues (CN, DE, EN, ES, FR, JP, KO, PT, PTBR, RU, TR), parité des clés et des arguments contrôlée | E22 : `tools/check_mod.py` |
| L01 | F15 : baril raccordé à la maison à la clé à tuyau, sans pompe | E23, `test_barrels.py` |
| L02 | F15 : gravité, pompe ou courant sur la case pour monter | E23, `test_barrels.py` |
| L03 | F15 : barils vidés ensemble ; le robinet montre l'eau de son réservoir relais (25 L au plus), pas le total (choix d'E09) | E23 `test_barrels.py`, E09 `test_inlet.py` |
| L04 | F13 : plusieurs arrivées d'eau sur un même réseau partagent la pompe | E03 `test_network.py`, E09 `test_inlet.py` |
| L05 | non repris (Q07) : les points d'eau ne donnent que de l'eau | ADR Q07, E24 annulée |
| L06 | F15 : « Garder en réserve (pris en dernier) » | E23, `test_barrels.py` |
| L07 | F15 adapté (Q07) : baril vide gardé dans la réserve, baril d'un autre liquide écarté | E23, `test_barrels.py` |
| L08 | F29 : fontaines à eau et liste sandbox `FillContainers`, `registerContainer` | E25, `test_containers.py` |
| L09 | F17 : diagnostic au clic droit d'un point d'eau | E26, `test_base.py` |
| L10 | partiel : F26 vue du réseau en surbrillance ; pose depuis la vue non reprise ; tuyaux verticaux non repris (Q06) | E13, `test_interface.py` |
| L11 | F16 : base du joueur, portée `BaseRange` (12) | E26, `test_base.py` |
| L12 | F18 : baril emporté débranché, arrivée d'eau ramassée sans réservoirs | E26, `test_base.py` |
| L13 | F20 : correctif du lave-linge raccordé en MP, désactivable ; robinet de boisson non concerné (Q07, Q08) | E28, `test_washer.py` |
| L14 | F30 (désinstallation par l'administrateur), D03 (ajout en cours de partie sans risque), D07 (options) ; ni interrupteur général ni journal de débogage (non repris, aucune décision ne les demande) | E21 `test_removal.py`, E05 `test_registry.py` |
| M01 | F19 : « Raccorder au réseau public », contrôles serveur | E27, `test_city.py` |

#### Vanne d'arrêt (ajout du 2026-11-18)

Pièce `LiveWater:Valve` (`shared/LiveWater/Parts/LWT_PartValve.lua`) : `conduit` (2 ports), `valve` (ouverte à la
pose, `look = true`), `controller` `manual`. Meuble `Base.Mov_LiveWater_Valve` (`WorldObjectSprite` 16, `CustomItem`
des tuiles 16-19), recette `LWTBuildValve` (clé anglaise gardée, 1 `LiveWater.PipeSection`, 1 `Base.ScrapMetal`),
clé `LWTBuildValve` dans les 11 langues. Ouverture et fermeture par le menu générique des pièces, l'action minutée
d'E13 et la commande `switchValve` existantes ; la vue du réseau la montre, grise une fois fermée (crochet `status` de `valve` : `closed`, après
l'état propre d'une sortie).
Dessin : variantes `open` (17 `ns`, 16 `ew`) et `closed` (19, 18) dont l'orientation 1 = S et 2 = E suit la propriété
`Facing` des tuiles ; nouveau champ de définition `facings` (`{ [masque] = orientation }`, API révision 13,
`Parts:facingFor`) : `LWT_Sprites` la tourne selon son tuyau (masques 2, 8, 10 → `ew` ; 1, 4, 5 → `ns`), seule ou
en coude elle garde l'axe affiché ; réglage `look` de `valve` (révision 13) pour que les arroseurs, déjà dessinés
par leur jet, ne changent pas.

Choix faits sans l'utilisateur :
- pose sur une **case vide entre deux tuyaux**, comme le compteur d'eau : le registre garde une pièce par case
  (D14, refus `occupied` au curseur) ; remplacer une section posée aurait demandé un nouveau chemin de pose. Le
  joueur démonte d'abord la section (rendue par la clé anglaise) puis pose la vanne dans le trou ;
- posée ouverte (une vanne de ligne ne doit pas couper l'eau à la pose) ; recette sans compétence, catégorie
  Métallurgie ;
- en coude ou seule, la vanne garde son dernier axe (pas de tuile de coude).

Fichiers : `LWT_PartValve.lua`, `LWT_Parts.lua`, `LWT_CapValve.lua`, `LWT_Sprites.lua`, `LWT_API.lua`,
`LWT_moveables.txt`, `LWT_recipes.txt`, `Translate/*/Recipes.json`, `tests/test_valve.py`, `tests/test_api.py`.
Contrôles : `python -B -m unittest discover -s tests` → `Ran 277 tests` … `OK` ; `python -B tools/check_mod.py` →
`OK: 100 Lua file(s) checked`. Rien de vérifié en jeu.

Choix faits sans l'utilisateur (traductions, wiki, page Workshop) :
- langues CN, DE, ES, JP, KO, PT, PTBR, RU, TR écrites directement en JSON (pas de générateur) ; `tools/check_mod.py`
  exige pour chaque langue exactement les fichiers et clés de EN et les mêmes `%N` et `%%` ;
- wiki en 8 pages par langue ; les captures manquent (lignes `> Capture à faire` / `> Screenshot to do`) ; seules les
  deux planches de `docs/images/art/` sont utilisées ;
- le wiki français nomme les outils comme le jeu en français (« clé anglaise » pour `Base.PipeWrench`, « clé à
  molette » pour `Base.Wrench`) ; les messages FR du mod suivent ces noms depuis le 2026-11-18 (« Il vous faut une clé
  anglaise », « … une clé à molette »), « clé à tuyau » n'y figure plus ;
- page Workshop courte (moins de 4 000 octets en anglais) pour que chaque langue tienne sous 8 000 octets ; aucun lien
  GitHub ni image externe (dépôt privé) ; « multijoueur pas encore testé » ; `workshop.txt` recopie `README.steam`,
  visibilité `unlisted`.

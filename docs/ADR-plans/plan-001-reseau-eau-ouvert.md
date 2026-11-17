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
| E09 | Arrivée d'eau de la maison : réservoirs invisibles `LiveWaterRelay`, cohabitation Live Wire | À faire | E07 | D18, D21 | M | E08 |
| E10 | Filtre : pièce, usure au volume, remplacement | Terminée (2026-11-18) | E08, E09, E06 | D17, D23 | S | E11 |
| E11 | Arroseur manuel : vanne, rayon, doses de 200 ml | À faire | E07 | D19 | M | E10 |
| E12 | Arroseur automatique : recette (niveau d'Électricité), minuterie consommatrice | À faire | E11, E08 | D19, D20 | M | — |
| E13 | Interface : menus, vue du réseau en surbrillance persistante, états « sans pression » et « eau non filtrée » | À faire | E08-E12 | D11, D14, D17 | M | — |
| E15 | Pompe : interrupteur, usure du rendement, pannes, réparation, fenêtre d'information, son (P03-P05, P08, P15) | Terminée (2026-11-18) | E08 | D24 | M | E16 |
| E16 | Débitmètre (P12) | Terminée (2026-11-18) | E07 | D24 | S | E15 |
| E17 | Puits comme source d'eau propre (P02) | À faire | E08 | D24 | S | E16 |
| E18 | Tuyaux d'un étage à l'autre (P10) | Annulée (Q06 : non repris, l'arrivée d'eau dessert les étages) | — | D24 | — | — |
| E19 | Sous-sols et lave-linge desservis par l'arrivée d'eau (P16, P18) | À faire | E09 | D18, D24 | S | E20 |
| E20 | Raccord de baril « Remplir » ou « Pomper », réseau d'essence (P02, P17) | À faire | E07 | D24, D26 | M | E19 |
| E21 | Retrait propre du mod (P21) | À faire | E09, E11 | D03, D24 | S | — |
| E23 | Baril raccordé à la maison : gravité, courant sur la case, réserve partagée, mise en réserve, baril gardé pour un liquide (L01-L03, L06, L07) | À faire | E09 | D27, D28 | L | E24 |
| E24 | Liquide choisi par point d'eau (L05) | Annulée (Q07 : eau seulement aux points d'eau) | — | D28 | — | — |
| E25 | Conteneurs remplis par la réserve, liste sandbox et API (L08) | À faire | E20 | D26, D28 | S | E23 |
| E26 | Base du joueur (portée), diagnostic au point d'eau, réglages effacés au ramassage (L09, L11, L12) | À faire | E09 | D28 | M | E25 |
| E27 | Raccordement au réseau public (M01) : état d'un point d'eau d'origine (`isWaterInfinite`), contrôles serveur | À faire | E09 | D27, D28 | M | E26 |
| E28 | Correctif du lave-linge raccordé en MP (désactivable), `incompatible=\LGExtendedPlumbing,\LGMainsWater` (L13) | À faire | E19 | D27, Q08, Q09 | S | — |
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

### E12 — Arroseur automatique

Fichiers : capacité `controller` `timer`, recette `LWTUpgradeSprinkler` (niveau d'Électricité 2 par défaut). Tests
rouges : déclenchement par tranche d'heures ; minuterie sans courant inerte ; ouverture manuelle toujours possible.

### E13 — Interface

Fichiers : `client/LiveWater/LWT_ContextMenu.lua`, `LWT_NetworkView.lua`. Surbrillance persistante posée et retirée,
aucun abonnement par image.

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

### E22 — Traductions, parité, passage en jeu

Onze langues (comme Live Wire), wiki EN et FR, `autotest.json`. Tableau de parité P01-P23 rempli avec la preuve de
chaque ligne. Passage automatique SP et MP avec code de sortie, `summary` et dossier `runs/...`.

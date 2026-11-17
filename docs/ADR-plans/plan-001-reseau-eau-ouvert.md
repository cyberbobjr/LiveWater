# Plan 001 — Réseau d'eau ouvert : pompe d'étang, tuyaux visibles, maison et arrosage

ADR : [ADR-001](../ADR/001-reseau-eau-ouvert.md) (Accepté le 2026-11-17).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Squelette du projet : dépôt, `workshop.txt`, `mod.info` (`incompatible=` de Q09), documents obligatoires, banc de tests hors jeu | Terminée (2026-11-17) | ADR accepté | D22 | S | — |
| E02 | API publique : registres des pièces et capacités, validation, scellé, révision, événements | Terminée (2026-11-17) | E01 | D01-D07 | M | — |
| E03 | Domaine : graphe du réseau, masques de raccord, ports, vannes, fusion de réseaux | Terminée (2026-11-17) | E02 | D10, D12-D15 | M | E04 |
| E04 | Domaine : pas de distribution, pression, qualité, filtre, besoin des sorties | Terminée (2026-11-17) | E02 | D09, D14, D16, D17 | M | E03 |
| E05 | Persistance : registre global versionné, pièces de type inconnu conservées | Terminée (2026-11-17) | E03 | D03, D04, D10 | M | E06 |
| E06 | Tuiles provisoires : 16 tuyaux, robinet, arroseurs, arrivée d'eau, pompe, filtre ; planche de présentation validée par l'utilisateur | À valider (planche soumise le 2026-11-17, intégration au mod après validation) | E01 | D12, D23 | L | E02-E05 |
| E07 | Adaptateurs serveur : pose et retrait, raccord automatique des sprites, commandes, horloge `EveryTenMinutes` | À faire | E05, E06 | D08-D12 | L | — |
| E08 | Pompe d'étang et électricité : `registerConsumer` (`display`, `summary`), repli vanilla | À faire | E07 | D16, D20 | M | E09 |
| E09 | Arrivée d'eau de la maison : réservoirs invisibles `LiveWaterRelay`, cohabitation Live Wire | À faire | E07 | D18, D21 | M | E08 |
| E10 | Filtre : pièce, usure au volume, remplacement | À faire | E08, E09, E06 | D17, D23 | S | E11 |
| E11 | Arroseur manuel : vanne, rayon, doses de 200 ml | À faire | E07 | D19 | M | E10 |
| E12 | Arroseur automatique : recette (niveau d'Électricité), minuterie consommatrice | À faire | E11, E08 | D19, D20 | M | — |
| E13 | Interface : menus, vue du réseau en surbrillance persistante, états « sans pression » et « eau non filtrée » | À faire | E08-E12 | D11, D14, D17 | M | — |
| E15 | Pompe : interrupteur, usure du rendement, pannes, réparation, fenêtre d'information, son (P03-P05, P08, P15) | À faire | E08 | D24 | M | E16 |
| E16 | Débitmètre (P12) | À faire | E07 | D24 | S | E15 |
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
`tools/make_tile_board.py`.

### E07 — Adaptateurs serveur

Fichiers : `server/LiveWater/LWT_Placement.lua`, `LWT_Sprites.lua`,
`LWT_Commands.lua`, `LWT_Clock.lua`. Pose et retrait (autorité), sprite recalculé pour la pièce et ses voisins
(`setSpriteFromName`, `transmitUpdatedSpriteToClients`), commandes contrôlées côté serveur, un seul abonné
`EveryTenMinutes`. Contrôle : aucun `Events.OnTick`/`OnPlayerUpdate`/`OnRender*`/`OnPostRender` dans le mod (`rg`).

### E08 — Pompe d'étang et électricité

Fichiers : `shared/LiveWater/Parts/LWT_PartPondPump.lua`, `server/LiveWater/LWT_Power.lua` (adaptateur unique vers Live
Wire et repli vanilla). Tests rouges : pose refusée loin de l'eau ; inscription `registerConsumer` seulement si
`revision >= 6` ; 250 W en marche, 0 à l'arrêt ; `display` et `summary` au format de l'ADR-002 ; pas de travail sans
courant.

### E09 — Arrivée d'eau de la maison

Fichiers : `shared/LiveWater/Parts/LWT_PartHouseInlet.lua`, `server/LiveWater/LWT_Relays.lua`. Tests rouges : points
d'eau raccordés du bâtiment touché, portée et étages ; point déjà alimenté laissé ; relais de Live Wire jamais touchés ;
retrait propre des relais.

### E10 — Filtre

Objet et icône validés sur la planche d'E06 (D23). Fichiers : `shared/LiveWater/Parts/LWT_PartFilter.lua`, objet et recette.

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

### E22 — Traductions, parité, passage en jeu

Onze langues (comme Live Wire), wiki EN et FR, `autotest.json`. Tableau de parité P01-P23 rempli avec la preuve de
chaque ligne. Passage automatique SP et MP avec code de sortie, `summary` et dossier `runs/...`.

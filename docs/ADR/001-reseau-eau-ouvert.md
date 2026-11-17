# ADR-001 — Réseau d'eau ouvert : pompe d'étang, tuyaux visibles, maison et arrosage

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-001-RESEAU-EAU-OUVERT` |
| Date de création et de mise à jour | 2026-11-13, 2026-11-17 |
| Statut | Accepté (2026-11-17) |
| Avancement | E01-E08, E10, E15, E16 terminées ; voir le [plan 001](../ADR-plans/plan-001-reseau-eau-ouvert.md) |
| Décideur | l'utilisateur |
| Portée | nouveau mod `batman_LiveWater` (Lua `shared`, `server`, `client`, scripts, tuiles, traductions) ; aucune modification de `batman_LiveWire` |
| Documents liés | [plan 001](../ADR-plans/plan-001-reseau-eau-ouvert.md), [contraintes de développement](../developpement.md) ; Live Wire : ADR-002 (API des consommateurs, révision 6, `display` D07, `summary` D08), `docs/wiki/fr/07-pompe-a-eau.md`, idées I16, I25, I26 de `docs/ameliorations-et-idees.md` |
| Références | Live Wire `LW_PumpTransfer.lua:186-202`, `LW_PumpRelays.lua:232,253`, `LW_Placement.lua:29-56`, `LW_Demand.lua:299-301` ; Java 42.22 `IsoObject.java:2777-2787` et `:3004-3011` ; base de connaissances `food-production.md:17`, `combat-and-xp.md:58-59`, `ui-windows.md:67,166-168`, `api-42-21.md:173,183` |
| Origine | demandes de l'utilisateur du 2026-11-13 : extraire la gestion de l'eau de Live Wire vers un mod frère, « mécanisme le plus ouvert possible », « sans casser l'existant », « évite les OnTick » |

## Contexte

Live Wire porte une pompe à eau électrique : des barils posés à côté d'elle remplissent des réservoirs invisibles
placés au-dessus des points d'eau raccordés (éviers, douches, toilettes) d'une maison. Les demandes des joueurs sur
l'eau (robinet extérieur, pompe en rivière, arrosage du potager) sortent du périmètre d'un mod d'électricité.
LiveWater devient le mod de l'eau. Il tire son courant de Live Wire par l'API publique des consommateurs (ADR-002 de
Live Wire), sans aucun code d'eau dans Live Wire.

Priorités de l'utilisateur, dans l'ordre :
1. pompe posée au bord d'un lac, d'un étang ou d'une rivière ;
2. tuyaux de la pompe vers la maison, avec robinet d'arrêt ;
3. tuyaux de la pompe vers l'arrosage des cultures, avec robinet d'arrêt, **par le même mécanisme**.

Exigences transverses : les joueurs demanderont sans cesse de nouveaux éléments ; chaque ajout doit se faire **sans
casser l'existant** (sauvegardes, autres mods, Live Wire). Aucun abonnement par image, mauvais pour les serveurs comme
pour les clients.

Faits établis :
- **Le robinet purifie toujours** (confirmé statiquement, Java 42.22) : un point d'eau raccordé
  (`usesExternalWaterSource`) dont le réservoir n'est pas vide se déclare propre (`isTaintedWater` rend faux,
  `IsoObject.java:3004-3011`) et convertit l'eau croupie prélevée en eau propre (`createSampleAndPurifyWater`,
  `:2777-2787`). Impossible de faire couler de l'eau sale d'un évier raccordé.
- **Les plantes acceptent l'eau croupie** : `plant:water(nil, doses)` côté serveur, sans joueur, 200 ml par dose,
  +10 par dose (`food-production.md:17`).
- **Une case d'eau se reconnaît à la pose** par le drapeau `IsoFlagType.water` d'une case voisine (règle de la roue à
  aubes de Live Wire, `LW_Placement.lua:29-56`, à réécrire dans LiveWater).
- **Changer l'image d'une tuile en MP** : `setSpriteFromName` puis `transmitUpdatedSpriteToClients()` sur l'autorité
  (`combat-and-xp.md:58-59`).
- **Surbrillance persistante** sans abonnement par image : `setHighlightColor` puis `setHighlighted(true, false)`,
  retirée explicitement (`ui-windows.md:67,166-168`).
- **Consommation électrique relue à chaque mesure** par Live Wire (`LW_Demand.lua:299-301`) : une pompe qui passe de
  la marche à l'arrêt change sa facture sans prévenir Live Wire.

## Décisions

### Ouverture et stabilité (socle de tout le reste)

- **D01 — Tout élément est un type inscrit.** LiveWater ne connaît aucun élément par son nom dans son cœur. Pompe,
  tuyau, robinet, arroseur, arrivée d'eau, filtre sont des **types de pièce** inscrits par
  `LiveWater.API.registerPart(id, definition)` (fichier `shared`, au chargement, scellé à `OnInitGlobalModData` comme
  les API de Live Wire). Les pièces de LiveWater s'inscrivent par cette même API publique, un fichier par pièce : un
  autre mod ajoute une pièce exactement comme LiveWater le fait.
- **D02 — Une pièce est un assemblage de capacités.** La définition d'une pièce liste ses capacités, chacune prise
  dans un registre de capacités (`LiveWater.API.registerCapability(kind, implementation)`). Capacités de départ :
  - `conduit` : relie ses côtés connectés (tuyau, et toute pièce traversée par l'eau) ;
  - `intake` : prend l'eau d'une source (case d'eau naturelle ; plus tard baril, puits) ;
  - `pump` : met le réseau sous pression (`ports`, `pressure`, débit, consommation) ;
  - `valve` : ouvert ou fermé ; fermé, coupe tout ce qui est après lui ;
  - `filter` : rend l'eau propre et s'use au volume ;
  - `outlet` : seul endroit où l'eau sort du réseau (`houseInlet` vers les réservoirs invisibles, `sprinkler` vers les
    plantes) ;
  - `controller` : décide quand une vanne s'ouvre (`manual` ; `timer` toutes les X heures).
  Un nouvel élément est d'abord une nouvelle combinaison de capacités existantes ; un nouveau comportement est une
  nouvelle capacité. Aucune chaîne de `if` sur une liste fermée de types (principe ouvert/fermé).
- **D03 — Identifiants stables et espaces de noms.** Ids `"<Mod>:<Nom>"` (`"LiveWater:PipeMetal"`), jamais
  réattribués ni renommés une fois publiés. Une pièce dont le type n'est plus inscrit (mod retiré) est **conservée
  telle quelle** dans le registre et inerte : jamais effacée, réactivée si le mod revient.
- **D04 — Données versionnées et additives.** Chaque entrée persistée porte `v` (version de son schéma). Les migrations
  ne font qu'ajouter ou convertir ; les champs inconnus sont conservés (données d'un mod plus récent ou d'une capacité
  absente). Chaque capacité range ses données sous sa propre clé dans l'entrée de la pièce.
- **D05 — API à révisions compatibles.** `LiveWater.API.revision` (entier, 1 au départ) ; une révision n'ajoute que
  des fonctions ou des champs facultatifs. Une fonction n'est jamais retirée ni changée de sens : dépréciée, elle reste.
  Définitions recopiées champ par champ (liste blanche), comme `registerSource` de Live Wire.
- **D06 — Événements publics.** `LiveWater.Events` publie, sur l'autorité, `partAdded`, `partRemoved`,
  `networkChanged`, `waterDelivered` (pièce, litres, qualité), `valveChanged`. Un autre mod réagit sans envelopper de
  fonction de LiveWater.
- **D07 — Réglages par définition et par sandbox.** Toute valeur de jeu (débit, pression, ports, portée, intervalle)
  vient de la définition de la pièce, multipliée par une option sandbox globale le cas échéant. Une nouvelle option
  arrive avec une valeur par défaut qui reproduit le comportement précédent.

### Aucun abonnement par image

- **D08 — Interdits.** Aucun abonnement à `OnTick`, `OnTickEvenPaused`, `OnPlayerUpdate`, `OnRenderTick`,
  `OnPostRender`, `OnPreUIDraw` ni à un autre événement par image, y compris pour une vue ouverte.
- **D08a — Exception visuelle : jet animé des arroseurs** (ajout du 2026-11-18, décision prise par l'agent sur la
  carte blanche de l'utilisateur, à confirmer par lui). Demande de l'utilisateur du 2026-11-17 : « assure-toi que les
  jets d'eau des arroseurs soient bien animés ». Le moteur n'anime pas le calque d'une tuile de mod : seuls `IsoFire`,
  `IsoFireplace`, `IsoBarbecue` font avancer les images (confirmé statiquement, Java 42.22, entrée « Calque animé » de
  la base de connaissances). D08 reste la règle ; une seule exception : un module **client** qui ne s'abonne à
  `OnTick` que tant qu'au moins un arroseur en marche est chargé près du joueur, se désabonne dès qu'il n'y en a plus,
  change l'image du jet au plus 6 fois par seconde, et ne fait aucun travail de jeu (aucune donnée, aucune commande).
  Option client pour le couper (jet fixe). Rien de cela ne tourne sur un serveur dédié.
- **D09 — Horloge unique sur l'autorité.** Un seul abonné `Events.EveryTenMinutes` côté serveur (solo : le jeu) fait
  avancer tous les réseaux : distribution, usure, minuteries d'arrosage (comparaison d'un numéro de tranche, pas de
  `getMinutes() == …`, `api-42-21.md:173`). Le travail est borné : seuls les réseaux dont la pompe est sur une case
  chargée travaillent, et seules les sorties qui ont besoin d'eau sont servies.
- **D10 — Topologie sur événement, jamais par balayage.** Le graphe d'un réseau est recalculé seulement quand une
  pièce est posée, retirée, ou qu'une vanne change (actions de LiveWater et `OnObjectAdded` sur l'autorité). Le
  registre persistant (ModData globale) indexe les pièces par coordonnées ; aucun parcours de cases ni de chunks.
- **D11 — Affichage sans image.** Les états visibles (tuyau raccordé, vanne ouverte, arroseur actif) sont des
  **sprites** changés sur l'autorité et diffusés. La vue du réseau utilise la surbrillance persistante, posée à
  l'ouverture et retirée à la fermeture. Les menus lisent l'état synchronisé (ModData de l'objet).

### Réseau, tuyaux et pression

- **D12 — Tuyaux visibles en tuiles, raccord automatique.** Un tuyau est une pièce posée au sol, une par case,
  franchissable. Ses quatre côtés donnent un masque de 4 bits ; la définition de la pièce associe chaque masque à un
  sprite (16 formes : sans voisin, 4 bouts, 2 droits, 4 coudes, 4 T, 1 croix). Poser ou retirer un tuyau recalcule
  son sprite et celui de ses voisins. Robinet d'arrêt, arroseur manuel, arroseur automatique, arrivée d'eau de la
  maison, pompe et filtre ont leurs propres sprites et déclarent par quels côtés ils se raccordent. Un nouveau matériau
  de tuyau est une nouvelle définition avec sa table de 16 sprites.
- **D13 — Un seul mécanisme pour la maison et le potager.** Mêmes tuyaux, mêmes robinets d'arrêt. Seule la sortie
  diffère. **L'eau ne sort qu'aux arroseurs (manuels ou automatiques) et par les réservoirs invisibles des maisons.**
  Un tuyau ou un robinet ne fuit jamais. Exception ajoutée par D26 : un raccord de baril réglé sur « Remplir ».
- **D14 — Ports et pression de la pompe.** Une pompe a un nombre maximal de tuyaux qui en partent (`ports`, 4 par
  défaut, Q03) et une réserve de pression (`pressure`, 6 par défaut, Q03). Chaque sortie a un coût de pression (`pressureCost` : arroseur 1,
  arrivée d'eau de maison 2, valeurs par défaut). La pompe sert ses sorties ouvertes de la plus proche à la plus
  lointaine (distance en tuyau, égalité départagée par l'ordre de pose) tant que la réserve suffit ; les suivantes sont
  « sans pression » et le disent (menu, vue, logiciel). Un raccord au-delà des ports est refusé à la pose, avec un
  message. Ouverture : une future pièce `booster` (surpresseur) ajoute de la pression par la même capacité `pump`.
- **D15 — Plusieurs pompes.** Deux réseaux qui se touchent fusionnent ; leurs pressions et débits s'additionnent.
  Une sortie reçoit son eau du réseau, pas d'une pompe désignée.

### Eau

- **D16 — Pompe d'étang.** Pièce `intake` + `pump`, posée sur une case voisine d'une case d'eau naturelle (lac, étang,
  rivière ; plus tard piscine). Source inépuisable. Débit : 5 L par minute de jeu (50 L par pas de dix minutes),
  réglable. Le gel est hors portée de cet ADR ; la capacité `intake` porte un point d'extension `available(context)`
  pour l'ajouter plus tard sans rien casser.
- **D17 — Qualité de l'eau.** Chaque source déclare la qualité de son eau. Eau de lac, d'étang, de rivière, de
  piscine : **croupie**. Eau de baril (plus tard) : règle vanilla, le robinet la purifie. Comme le robinet purifie
  toujours (voir Contexte), la règle est portée par la sortie :
  - **sans filtre**, de l'eau croupie ne va qu'aux arroseurs (les plantes l'acceptent) ; l'arrivée d'eau de la maison
    l'indique « eau non filtrée » et ne remplit rien ;
  - **avec un filtre** sur la pompe (ou en ligne, même capacité `filter`), l'eau devient propre et va aussi à la
    maison. Le filtre s'use au volume filtré et se remplace.
- **D18 — Arrivée d'eau de la maison.** Pièce `outlet` de type `houseInlet`, posée contre un mur extérieur. Elle
  dessert les points d'eau **raccordés à la clé à tuyau** du bâtiment qu'elle touche, dans une portée réglable,
  jusqu'à 3 étages au-dessus, **sous-sols compris** (points d'eau des niveaux négatifs rattachés au bâtiment de la
  même colonne, P18), par des réservoirs invisibles de 25 L posés à l'étage au-dessus (mécanisme éprouvé de Live Wire,
  réécrit dans LiveWater). ModData propre `LiveWaterRelay`. Un point d'eau déjà alimenté par autre chose (réseau public,
  baril vanilla, pompe de Live Wire, autre mod) est laissé tel quel.
- **D19 — Arrosage.** Arroseur manuel : pièce `outlet` de type `sprinkler` avec un `valve` et un `controller`
  `manual` (ouvrir, fermer d'un clic droit). Ouvert, il arrose les plantes dans son rayon (2 cases par défaut) **qui en
  ont besoin**, par doses de 200 ml prélevées réellement dans le réseau. Une recette avec un niveau d'Électricité
  (2 par défaut) le transforme en **arroseur automatique** : même pièce, `controller` `timer` qui l'ouvre toutes les
  X heures (réglable sur l'arroseur, bornes sandbox) le temps de servir les plantes. La minuterie est un consommateur
  électrique (D20) : sans courant, elle ne déclenche rien ; l'ouverture manuelle reste possible.

### Électricité et Live Wire

- **D20 — Courant par l'API de Live Wire, facultatif.** Si `LiveWire.API.revision >= 6`, chaque pièce électrique
  (pompe, minuterie) s'inscrit avec `registerConsumer` : `powerConsumption` (pompe 250 W en marche, 0 à l'arrêt ;
  minuterie quelques W), `display` (état, débit, sorties servies) et `summary` (pompes en service, débit total du
  réseau). Elle vérifie `consumerPowered` avant de travailler. Sans Live Wire, la règle vanilla
  `square:haveElectricity()` (générateur, réseau public) s'applique. `summary` confirmé disponible par la session de
  Live Wire le 2026-11-13 (ADR-002 D08, révision 6) : appelée sur le serveur une fois par instantané avec les pompes
  que le réseau dessert (à l'arrêt comprises, réseau public exclu), 2 lignes au plus, onglet Équipements. LiveWater **n'exige pas** Live Wire
  (`require=` absent). Tout ce que LiveWater montre dans le logiciel de gestion passe par cette API.
- **D21 — Live Wire existant intact.** Aucun fichier de Live Wire n'est modifié par ce chantier. La pompe aux barils de
  Live Wire, ses barils et ses relais (`LiveWireRelay`, `LiveWireBarrel`) continuent de fonctionner. LiveWater a ses
  propres sprites (l'ADR-002 refuse deux inscriptions d'un même sprite) et ne touche jamais une entrée ni un relais de
  Live Wire. La reprise de la pompe aux barils dans LiveWater fera l'objet d'un ADR distinct.

### Nommage

- **D22 — Conventions.** Mod `batman_LiveWater` ; table Lua globale `LiveWater` ; fichiers `LiveWater/LWT_*.lua` ;
  objets posables `Base.Mov_LiveWater_<Nom>`, objets d'inventaire `LiveWater.<Nom>`, recettes `module LiveWater`
  préfixe `LWT` ; traductions `*_LWT_*` ; messages console en anglais. Architecture hexagonale légère : domaine pur
  (graphe, pression, distribution, qualité) sans API du jeu, testable hors jeu ; adaptateurs PZ (pose, horloge,
  réservoirs, plantes, sprites, Live Wire) autour.

### Parité avec Water Pipes et Basement Water (demande de l'utilisateur, 2026-11-13)

L'utilisateur exige que LiveWater reprenne **au moins toutes les fonctionnalités** de « [B42] Water Pipes » (Workshop
3546314080, id `Waterpipes`, variante 42.20 lue) et de son module « Basement Water » (Workshop 3743352602, id
`WaterPipesBasementWater`, variante 42.1 lue). Inventaire confirmé statiquement dans les fichiers installés.

- **D24 — Inventaire à couvrir.** Chaque ligne devient une pièce, une capacité ou une règle de LiveWater :

  | # | Fonctionnalité de Water Pipes ou Basement Water | Preuve | Couverture LiveWater |
  |---|---|---|---|
  | P01 | Pompe électrique posée à côté d'une source ; marche seulement si sa case a du courant | `WPIso.lua:202-222` | D16, D20 |
  | P02 | Sources : eau naturelle (croupie), **puits** (eau propre, `camping_01_16`, `morebuild_01_0`), **cuves de station-service** (essence) | `WPIso.lua:136-162,224-268` | D16 + sources `well` et `fuelTank` ; essence selon D26 |
  | P03 | Mise en marche et arrêt manuels de la pompe | `WPMenu.lua:77-98`, `TATurnOnPump.lua`, `TATurnOffPump.lua` | capacité `pump` : interrupteur, en plus de l'arrêt automatique quand rien n'a besoin d'eau |
  | P04 | Usure de la pompe (rendement qui baisse par minute de marche, option sandbox), débit proportionnel au rendement, pannes aléatoires sous 20 %, arrêt à 0 % | `WPServer.lua:433-463` | capacité `wear` : rendement, débit, pannes ; réglages sandbox |
  | P05 | Réparation de la pompe à l'arrêt, avec de la ferraille | `TARepairPump.lua`, `WPMenu.lua:99-118` | action de réparation (matériaux par définition) |
  | P06 | Risque d'incendie d'une pompe usée (annoncé par le texte ; seul un drapeau est posé, aucun feu n'est déclenché) | `WPServer.lua:459`, `WPVirtual.lua:17` | Q05 rendu : panne seulement, aucun incendie pour l'instant |
  | P07 | Filtre au charbon ajouté à la pompe, consommé pendant la marche (option sandbox), purifie l'eau croupie | `TAAddFilterPump.lua`, `WPServer.lua:446,470-472` | D17 (filtre usé au volume) |
  | P08 | Fenêtre d'information de la pompe : état, courant, source, rendement, filtre | `ISWaterPumpInfoWindow.lua` | fenêtre ou LCD de la pompe, `display` et `summary` de Live Wire |
  | P09 | Tuyaux en tuiles qui se raccordent seuls : droits, coudes, T, croix | `WPIso.lua:13-35`, `WPObjectHandlers.lua:28-43` | D12 |
  | P10 | Tuyaux qui montent et descendent d'un étage | `WPIso.lua:30-41` (`nd`… `wu`) | **non repris**, choix de l'utilisateur (Q06) : les étages sont desservis par les réservoirs invisibles de l'arrivée d'eau (D18), mécanisme jugé meilleur ; les tuyaux restent sur un seul niveau |
  | P11 | Vanne ouverte ou fermée, posée sur un tuyau, image alignée sur le tuyau | `TASwitchValve.lua`, `WPBuildRecipeCode.lua:305` | capacité `valve` |
  | P12 | **Débitmètre** posé sur un tuyau, fenêtre du débit et du fluide | `entity_flowmeter.txt`, `ISFlowmeterInfoWindow.lua` | pièce `LiveWater:Flowmeter`, capacité `meter` |
  | P13 | Arroseur : arrose les plantes qui en ont besoin dans un cercle de **5 cases**, à chaque pas | `WPServer.lua:493-516` | D19, rayon par définition (5 pour l'arroseur de base) |
  | P14 | Arroseur animé (jet d'eau) et sonore | `WPSprinkler.lua` | animation sans abonnement par image (D11) : sprite animé ou deux états, à vérifier en E06 |
  | P15 | Son en boucle de la pompe en marche | `WPSound.lua` | son de la pompe, bruit entendu par les zombies |
  | P16 | Tuyau qui touche un bâtiment : remplit **tous** les points d'eau du bâtiment, à parts égales (éviers, baignoires, douches, toilettes, **lave-linge**) | `WPIso.lua:95-131,551-578`, `WPVirtual.lua:272-296` | D18 (lave-linge à vérifier : raccordable en vanilla ou non) |
  | P17 | **Remplir un baril** (récupérateur d'eau de pluie) au bout d'un tuyau | `WPIso.lua:417-447`, `WPServer.lua:326-330` | D26 (Q04 rendu) : raccord de baril réglé sur « remplir » ou « pomper » |
  | P18 | **Sous-sols** : les points d'eau des niveaux négatifs sont rattachés au bâtiment de la même colonne | Basement Water `BasementWater.lua:15-17` | D18 étendu : étages négatifs compris |
  | P19 | Construction au menu de construction, compétence Métallurgie 1-2, XP | `entity_*.txt` | recettes LiveWater (compétences par définition) |
  | P20 | Trois réglages sandbox : usure du filtre, perte de rendement, débit maximal | `sandbox-options.txt` | D07 |
  | P21 | Mod compagnon de désinstallation qui garde la sauvegarde lisible | `WaterPipesRemoved` | action de retrait propre (relais, pièces) et pièces de type inconnu conservées (D03) |
  | P22 | Fonction publique de raccord d'un bâtiment utilisée par un autre mod | `WPIso.lua:550` | API publique (D01-D06) |
  | P23 | Traductions en 8 langues | `Translate/` | 11 langues, comme Live Wire |

### Parité avec LG Extended Plumbing et LG Connect To Water Supply (demande de l'utilisateur, 2026-11-13)

Sources : « LG Extended Plumbing » (Workshop 3779561845, id `LGExtendedPlumbing`, 3.3.1, variante 42.20 lue dans les
fichiers installés, confirmé statiquement) ; « LG Connect To Water Supply » (Workshop 3779251515, id `LGMainsWater`,
1.1.2, variante 42.20, installé par l'utilisateur le 2026-11-13 et lu dans ses fichiers, confirmé statiquement).

- **D27 — Inventaire à couvrir.**

  | # | Fonctionnalité | Preuve | Couverture LiveWater |
  |---|---|---|---|
  | L01 | Un récupérateur d'eau de pluie **raccordé au bâtiment à la clé à tuyau** alimente **tous** les points d'eau raccordés du bâtiment (pas seulement le 3 × 3 au-dessous), **sans pompe** | `ContextMenu_LGEP_Plumb`, `LGEPGhost.lua` | D28 : baril raccordé à la maison, source par gravité de l'arrivée d'eau |
  | L02 | Par gravité : un baril sur le toit ou à l'étage alimente les étages **en dessous** ; un baril sur une case qui a du courant pousse l'eau **vers le haut** aussi | `IGUI_LGEP_PipeDownhill`, `LGEPPower.lua` | D28 (la pompe de LiveWater, ou le courant sur la case du baril, lève la règle de gravité) |
  | L03 | Un robinet affiche **le total** de tous les barils qui le servent ; ils se vident **ensemble** | `LGEPGhost.lua` (miroir du total), `ContextMenu_LGEP_LiquidAmount` | D28 : réservoir relais qui reflète le total disponible, prélèvement réparti ; faisabilité à vérifier en E09 |
  | L04 | Tuyaux en fer posés vers un abri, une cour, la maison voisine : tous partagent la même réserve | `IGUI_LGEP_AddPipe`, `LGEPPipes.lua` | D12, D13, D18 (plusieurs arrivées d'eau sur un réseau) |
  | L05 | Chaque point d'eau **choisit le liquide** qu'il tire (eau, whisky, bière, lait… ; un mélange compte comme un liquide) | `ContextMenu_LGEP_PlumbedLiquid` | **non repris**, choix de l'utilisateur (Q07) : les points d'eau ne donnent que de l'eau |
  | L06 | Baril **en réserve** : rien n'y est pris tant que les autres ne sont pas vides ; son eau compte au robinet | `ContextMenu_LGEP_SetReserve` | D28 : priorité de prélèvement des sources |
  | L07 | Baril vide « gardé pour » un liquide : il reste dans la chaîne de ce liquide jusqu'à ce qu'on y verse autre chose | `ContextMenu_LGEP_KeptFor` | adapté (Q07) : un baril vide reste dans la réserve d'eau ; un baril qui contient autre chose que de l'eau en sort jusqu'à ce qu'il soit vidé |
  | L08 | Conteneurs **remplis par** la réserve (fontaines à eau par défaut ; liste de noms de script en sandbox) | `Sandbox_LGExtendedPlumbing_FedFixtures` | D26 « Remplir » généralisé à tout conteneur inscrit (liste par sandbox et par API) |
  | L09 | Diagnostic au clic droit d'un point d'eau : pourquoi il n'a pas d'eau (pas dans une pièce, aucun baril à portée, aucun raccordé, gravité, mauvais liquide, réserve vide) | `ContextMenu_LGEP_NoSupply_*` | D28 : chaque refus a une raison traduite, affichée au point d'eau |
  | L10 | Fenêtre « Zone raccordée » : où l'eau arrive, et pose ou retrait des tuyaux depuis cette fenêtre ; tuyaux **verticaux sur les murs** | `LGEPAreaUI.lua`, `IGUI_LGEP_AddWallPipe` | vue du réseau (D11) ; pose depuis la vue à étudier en E13 ; tuyaux verticaux **non repris** (Q06) |
  | L11 | **Base construite par le joueur** (hors bâtiment de la carte) : portée réglable autour du point d'eau (12 par défaut) | `Sandbox_LGExtendedPlumbing_Reach` | D28 : mode « portée » de l'arrivée d'eau hors bâtiment de la carte |
  | L12 | Ramasser un baril ou un point d'eau efface ses réglages de raccordement (un baril emporté ne reste pas raccordé à l'ancienne maison) | `LGEPCarry.lua` | D28 |
  | L13 | Correctifs vanilla : lave-linge non raccordable sur serveur et qui tourne encore à vide ; robinet de boisson qui vide le baril sans rien remplir | `Sandbox_LGExtendedPlumbing_WasherPatch`, `_FluidPatch` | Q08 rendu : seul le correctif du lave-linge raccordé en MP touche LiveWater (désactivable en sandbox) ; le robinet de boisson ne le concerne pas (Q07) |
  | L14 | Activation générale, journal de débogage, désinstallation depuis le menu de débogage, ajout en cours de partie sans risque | `Sandbox_LGExtendedPlumbing_Enabled`, `_Debug`, `LGEPAdmin.lua` | D07, P21 |
  | M01 | **Raccorder au réseau public** un point d'eau posé par le joueur (évier, baignoire, douche, toilettes, lave-linge), à la clé à tuyau, tant que l'eau de la ville coule : eau illimitée, coupure le même jour que la ville, 20 L restants dans les tuyaux, baril possible ensuite ; seulement dans un bâtiment de la carte ; pas proposé à un point déjà sur un baril | `LGMainsWaterCore.lua:1-31`, `LGPlumbMainsAction.lua:49-97`, `LGMainsWaterContext.lua:158` | D28 ; mécanisme moteur confirmé statiquement (voir sous le tableau) |

  **Réseau public : règle du moteur** (confirmé statiquement, Java 42.22 `IsoObject.java:2542-2564`,
  `isWaterInfinite`). Un point d'eau a l'eau illimitée de la ville si : sa case a une pièce (`getRoom()`, donnée de la
  carte, impossible à créer), son sprite porte `waterPiped`, il n'utilise pas de source externe
  (`getUsesExternalWaterSource()` faux), la case n'est pas `isNoWater()`, la date de coupure n'est pas passée, et sa
  ModData ne porte pas `canBeWaterPiped = true`. Un point d'eau posé par le joueur reçoit `canBeWaterPiped = true` à la
  pose, d'où son absence d'eau. Le raccord au réseau public consiste donc à remettre l'objet dans l'état d'un point
  d'eau d'origine (sur l'autorité, puis diffusion). Contrôles côté serveur à reprendre : point d'eau raccordable,
  bâtiment de la carte, joueur à portée du point d'eau (`LGPlumbMainsAction.lua:60-90`). Option proposée seulement tant
  que l'eau de la ville coule et que le point d'eau n'est pas déjà sur une source externe.

- **D28 — Règles reprises de ces mods**, intégrées au modèle de LiveWater :
  - **Baril raccordé à la maison** (L01, L02) : un baril ou récupérateur posé dans le bâtiment ou sur son toit se
    raccorde à la clé à tuyau à l'arrivée d'eau de ce bâtiment, sans tuyau ni pompe. Il alimente les points d'eau de
    son étage et des étages inférieurs (gravité). Une pompe de LiveWater dans le réseau, ou du courant sur la case du
    baril, permet d'alimenter aussi les étages supérieurs.
  - **Réserve partagée** (L03, L06, L07) : toutes les sources d'eau d'un bâtiment forment une réserve ; elles se
    vident ensemble, sauf celles mises « en réserve », prises en dernier ; un baril vide y reste ; un baril qui contient
    autre chose que de l'eau en sort jusqu'à ce qu'il soit vidé.
  - **Eau seulement aux points d'eau** (Q07) : un point d'eau ne donne que de l'eau (propre ou purifiée par le robinet),
    jamais une boisson, du lait ni de l'essence.
  - **Conteneurs remplis** (L08) : la sortie « Remplir » de D26 s'applique à tout conteneur inscrit (barils, fontaines
    à eau, liste de noms de script en sandbox, inscription par l'API).
  - **Base du joueur** (L11) : hors bâtiment de la carte, l'arrivée d'eau dessert les points d'eau raccordés dans une
    portée réglable (12 par défaut).
  - **Diagnostic** (L09) : un point d'eau sans eau dit pourquoi, en une ligne traduite.
  - **Ramassage** (L12) : ramasser une pièce, un baril ou un point d'eau efface ses réglages de raccordement.
  - **Réseau public** (M01) : action « Raccorder au réseau public » sur un point d'eau posé par le joueur, dans un
    bâtiment de la carte, tant que l'eau de la ville coule, pour qu'il se comporte comme un point d'eau d'origine.

- **D26 — Barils et essence** (Q04 rendu). Un **raccord de baril** se pose entre un tuyau et un baril (récupérateur
  d'eau de pluie ou baril de fluide). Le joueur le règle sur **« Remplir »** (sortie : le réseau remplit le baril,
  sans fuite) ou **« Pomper »** (source : la pompe tire le contenu du baril ; l'eau de pluie suit la règle vanilla, le
  robinet de la maison la purifie). Un réseau ne transporte qu'un seul fluide à la fois. Un réseau d'essence (cuve de
  station-service ou baril d'essence en « Pomper ») ne dessert que des raccords de baril en « Remplir », jamais une
  arrivée d'eau de maison ni un arroseur. Cette décision ajoute une exception à D13 : l'eau sort aussi par un raccord
  de baril en « Remplir ».

- **D25 — Écriture indépendante.** Aucun code, asset (tuiles, textures, sons), texte ni nom n'est repris de Water
  Pipes, Basement Water, LG Extended Plumbing ni LG Connect To Water Supply ; seules les mécaniques de jeu sont reprises, réalisées de façon originale et fondées sur le vanilla.

- **D23 — Validation visuelle avant intégration** (demande de l'utilisateur, 2026-11-13). Les tuiles (tuyaux,
  robinets, arroseurs, arrivée d'eau, pompe) et le filtre (objet et icône) sont présentés à l'utilisateur sur une
  planche de présentation et validés par lui **avant** d'être intégrés au mod.

## Arbitrages rendus

- **Q01 — Matière et coût d'un tuyau** : rendu le 2026-11-13 par l'utilisateur (« une section de tuyau par case :
  ok »). Objet `LiveWater.PipeSection`, 1 par case, fabriqué à partir d'un `Base.MetalPipe` (4 sections, scie à
  métaux), rendu au démontage à la clé à tuyau.
- **Q02 — Objet et recette du filtre** : rendu le 2026-11-13 par l'utilisateur (« filtre : ok »). Cartouche
  `LiveWater.WaterFilter`, fabriquée avec du charbon de bois et du tissu, 500 L par cartouche.

- **Q03 — Nombre de départs de la pompe** (`ports` de D14) : rendu le 2026-11-13 par l'utilisateur (« 4 départs avec
  possibilité de tuyaux en T (pour 2 voies) ou tuyaux 4 voies »). `ports = 4` par défaut ; les tuyaux en T et en croix
  font partie des 16 formes de D12. La longueur d'un tuyau n'est pas limitée (une section par case) ; la réserve de
  pression reste la limite du réseau, **6 par défaut** (une maison et quatre arroseurs).

- **Q04 — Remplir un baril et pomper de l'essence** (P02, P17) : rendu le 2026-11-13 par l'utilisateur (« ok pour
  choisir "remplir" ou "pomper" un baril »). Voir D26.
- **Q05 — Incendie d'une pompe usée** (P06) : rendu le 2026-11-13 par l'utilisateur (« ok juste en panne pour
  l'instant »). Une pompe très usée tombe en panne et s'arrête (P04), sans incendie.
- **Q06 — Tuyaux d'un étage à l'autre** (P10) : rendu le 2026-11-13 par l'utilisateur (« non trop compliqué, le
  mécanisme de la source d'eau invisible au dessus des points d'eau est meilleur » ; « un raccord maison simple suffit
  comme actuellement »). Aucun tuyau entre étages ; l'arrivée d'eau de la maison (D18) dessert les étages et les
  sous-sols par ses réservoirs invisibles.

- **Q07 — Liquides autres que l'eau aux robinets** (L05) : rendu le 2026-11-13 par l'utilisateur (« non »). Les
  points d'eau ne donnent que de l'eau (D28).
- **Q08 — Correctifs de défauts vanilla** (L13) : rendu le 2026-11-13 par l'utilisateur (« ok »). LiveWater corrige
  seulement ce qui touche ses propres points d'eau, chaque correctif désactivable en sandbox ; après Q07, cela se
  réduit au lave-linge raccordé en MP.
- **Q09 — Cohabitation avec les mods LG** : rendu le 2026-11-13 par l'utilisateur (« ok »). `mod.info` de
  `batman_LiveWater` : `incompatible=\LGExtendedPlumbing,\LGMainsWater`, puisque LiveWater couvre leurs
  fonctionnalités et que deux mods qui changent la source d'eau des points d'eau risquent de les alimenter deux fois
  (même choix que Live Wire Extended face à LG Extended Electricity, D-40 de Live Wire).

## Arbitrages ouverts

Aucun.

## Conséquences

- Un nouvel élément demandé par les joueurs se fait par un fichier de pièce, ou au pire une capacité nouvelle, sans
  toucher au cœur, aux données sauvegardées ni à l'API publiée.
- Aucun coût par image ; un pas de travail toutes les dix minutes de jeu, borné aux réseaux chargés.
- Live Wire n'est ni modifié ni requis ; avec Live Wire, la pompe est facturée, coupée par les disjoncteurs et visible
  dans le logiciel comme un appareil de Live Wire.
- Pendant la cohabitation, un joueur peut avoir la pompe aux barils de Live Wire et une pompe d'étang de LiveWater ;
  chacune laisse les points d'eau de l'autre.
- Coût : 16 sprites de tuyau plus les pièces spéciales (formes simples en attendant les modèles définitifs).

## Hors portée

Gel et saisons, robinet extérieur à remplir à la main (I25 de Live Wire), reprise de la pompe de Live Wire, fuites et
casse des tuyaux, tuyaux d'un étage à l'autre (Q06), incendie d'une pompe usée (Q05), boissons ou autres liquides aux
points d'eau (Q07). Le puits et le baril comme
source entrent dans la portée (D24, D26).

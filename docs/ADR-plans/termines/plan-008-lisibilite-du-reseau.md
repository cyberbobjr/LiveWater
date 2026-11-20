# Plan 008 — Lisibilité du réseau : raccord coudé, noms, compteur, pompe, appareils de la maison

ADR : [ADR-008](../../ADR/termines/008-lisibilite-du-reseau.md) (Accepté le 2026-11-19).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| G01 | Noms des objets posables dans les onze langues ; test sur tout objet de script | Terminée (2026-11-20) | ADR accepté | D02 | S | G02, G03, G04 |
| G02 | Menus exclusifs (réseau, zone arrosée) | Terminée (2026-11-20) | ADR accepté | D04 | S | G01, G03, G04 |
| G03 | Raccord coudé : définition, choix du sprite, 24 tuiles, profondeur, contrat ; tests | Terminée (2026-11-20) | ADR accepté | D01 | L | G01, G02, G04 |
| G04 | Totaux du compteur et de la pompe, fenêtres compteur et LCD, eau des appareils, appareils dans la vue du réseau ; tests | Terminée (2026-11-20) | G02 | D03, D05, D06, D07 | L | G03 |
| G03b | Raccord embranchement : l'eau traverse le raccord, 48 tuiles (té, devant + côté, croix) ; tests | Terminée (2026-11-20) | G03 | D01b | L | — |
| G06 | Compteur et vanne en ligne : deux côtés sur l'axe montré, flancs jamais raccordés ; tests | Terminée (2026-11-20) | G03b | D08 | M | — |
| G07 | Arroseurs : manette agrandie, voyant du programmateur (tuiles 48-63) | Terminée (2026-11-20) | — | D09 | M | G06 |
| G08 | Bruit d'ouverture et de fermeture des vannes | Terminée (2026-11-20) | G06 | D10 | S | G07 |
| G09 | Bruit de la pompe lié au courant, à l'événement `OnElectricityChanged` | Terminée (2026-11-20) | G06 | D11 | S | G07 |
| G10 | Recettes : panneau seul, catégorie LiveWater, icônes des objets posables ; tests | Terminée (2026-11-20) | — | D12 | S | — |
| G05 | Passages en jeu (solo, visuel, multijoueur), documentation joueur | Terminée (2026-11-20) | G01-G04 | toutes | M | — |

## Fiches

### G01 — Noms

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : `ItemName.json` des onze langues reçoit la vanne, l'arrivée d'eau, les deux arroseurs et le raccord, avec le
  nom de la tuile de la même langue (`Moveables.json`). Test `tests/test_item_names.py` : tout objet déclaré dans
  `media/scripts/*.txt` a un nom non vide dans chaque langue.
- Preuve du vert : `python -B -m unittest discover -s tests -p "test_item_names.py"` → `Ran 2 tests` … `OK`.

### G02 — Menus exclusifs

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : `LWT_NetworkView.fill` n'ajoute « Afficher le réseau d'eau » que si aucune vue n'est affichée, « Masquer »
  sinon ; `LWT_AreaView.fill` fait de même pour la zone arrosée. Tests : `test_interface.py` (Masquer seul quand le
  réseau est affiché), `test_area_view.py` (Masquer seul quand les zones sont allumées), rouges avant le correctif.
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 444 tests` … `OK` (avant G01).

### G03 — Raccord coudé

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : champ de définition `bends` (révision d'API 17, `shared/LiveWater/LWT_API.lua`) = suffixe de variante par
  côté relatif à l'orientation (1, 2 ou 3), validé dans `shared/LiveWater/LWT_Parts.lua` (`invalid_bends`) ;
  `Parts:bend` (devant prioritaire, puis +1, puis +3 ; repli sur la variante droite) et `Parts:followsLinks` ;
  `server/LiveWater/LWT_Sprites.lua` redessine par son état une pièce qui suit ses liaisons et applique le coude, sans
  `if` sur le type. `Grid.FACINGS` (côté de chaque orientation S, E, N, W), dont `Tiles.FEED_FACINGS` est désormais
  déduit. Raccord : `bends = { [1] = "bend1", [3] = "bend3" }`, variantes `fill_bend1` 184, `fill_bend3` 188,
  `fill_low_bend1` 192, `fill_low_bend3` 196, `pump_bend1` 200, `pump_bend3` 204 (S, E, N, W) ; l'orientation de pose
  reste lue par `facingOf` (baril derrière). Recette : `build_barrel_connector(..., bend=E|W)` (coude galvanisé au
  centre, vanne avancée de 0,11 vers le baril, tuyau souple inchangé), table `BARREL_BENDS`, 6 groupes, propriétés des
  tuiles identiques à 64-75, tileset 208 sprites (8 × 26) ; contrat `docs/annexes/conception/tuiles-contrat.md`.
  Tests `tests/test_fitting.py`, classe `Bends` (coude des deux côtés sur les 4 orientations, devant prioritaire,
  retour au droit, mode Pomper, recette = pièce, champ invalide refusé), rouges avant le code ; banc existant : tuyau
  arrivant de l'ouest d'un raccord orienté S → 188 / 196 / 204.
- Preuve du vert :
  - `python -B -m unittest discover -s tests -p "test_fitting.py"` → `Ran 20 tests` … `OK` ;
  - `python -B -m unittest discover -s tests` → `Ran 452 tests` … `OK` ;
  - `python -B tools/check_mod.py` → `OK: 105 Lua file(s) checked` ;
  - empaquetage : les 184 sprites existants identiques au pixel près à l'ancienne planche ; carte de profondeur :
    `total: 174 sprites, hits outside the sprite 0, left without depth 0` (184-207 compris).

### G03b — Raccord embranchement

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : le raccord porte `conduit = true` (comme la vanne et le compteur) : `Network:reach` passe à travers lui
  (`carries`), il reste sortie `barrelFill` en Remplir (servi dans l'ordre de service, puis l'eau continue vers l'aval,
  `through` crédité comme un tuyau) et pièce qui `draw` en Pomper (ou racine de gravité) ; `LWT_Flow.lua` et
  `LWT_Network.lua` inchangés, aucun `if` sur le type. Dessin : champ `branches` (révision d'API 18,
  `LWT_API.lua` ; remplace `bends` de la révision 17, jamais publiée) = suffixe par masque des côtés raccordés relatifs
  à l'orientation (1 devant, 2 côté +1, 4 derrière, 8 côté +3), validé (`invalid_branches`) ; seuls les côtés nommés
  par une entrée comptent (le côté du baril n'est pas dessiné) ; `Parts:branch` remplace `Parts:bend`. Raccord :
  `{ [2] = "bend1", [8] = "bend3", [10] = "tee", [3] = "front1", [9] = "front3", [11] = "cross" }` ; té 208/224/240,
  devant + 1 212/228/244, devant + 3 216/232/248, croix 220/236/252 (Remplir haut, Remplir bas, Pomper ; S, E, N, W).
  Recette : `build_barrel_connector(..., pipes=...)`, tables `BARREL_MODES` et `BARREL_SHAPES`, 12 groupes, propriétés
  identiques à 64-75, tileset 256 sprites (8 × 32) ; contrat des tuiles à jour. Tests `tests/test_fitting.py` :
  `Branches` (les 8 combinaisons devant / +1 / +3 sur les 4 orientations, tuyau derrière non dessiné, formes qui
  suivent les tuyaux posés et retirés, mode Pomper, recette = pièce, champ invalide refusé) et `Through` (eau qui
  traverse un raccord Remplir vers un arroseur en aval, raccord Pomper en ligne), rouges avant le code.
- Point ouvert : la pièce accepte toujours un tuyau sur ses quatre côtés (`sides` par type, pas par orientation) ; un
  tuyau derrière se raccorde et l'eau y passe, sans être dessiné. Le refuser demanderait des côtés par orientation, ou
  `conduit = { ports = 3 }` (borne le nombre, pas le côté) : décision laissée à l'orchestrateur.
- Preuve du vert :
  - `python -B -m unittest discover -s tests -p "test_fitting.py"` → `Ran 23 tests` … `OK` ;
  - `python -B -m unittest discover -s tests` → `Ran 483 tests` … `OK` ;
  - `python -B tools/check_mod.py` → `OK: 111 Lua file(s) checked` ;
  - empaquetage : les 208 sprites existants identiques au pixel près ; profondeur : `total: 222 sprites, hits outside
    the sprite 0, left without depth 0` (208-255 compris).

### G04 — Compteur, pompe, appareils

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : capacités `meter` et `pump` : champ `total` (litres depuis la pose, cumulé à chaque pas, gardé dans l'état
  mirroré donc au ramassage et à la repose, jamais remis à zéro), republié aux clients par `LWT_Publisher` dès qu'il
  change ; lignes de la pompe : état, débit possible (débit × rendement × multiplicateur), débit du dernier pas, total,
  rendement, source. Nouveau crochet de capacité `panel` (whitelist `LWT_Capabilities`) : nom de la face de fenêtre,
  clé du titre, lecture. Client : registre `LWT_Panels` (faces `counter` et `lcd`, chacune dans son fichier,
  `LWT_FaceCounter.lua`, `LWT_FaceLcd.lua`), fenêtre `LWT_PartWindow.lua` (relit le mirroir toutes les 1 000 ms, se
  ferme si la pièce disparaît ou si le joueur s'éloigne à plus de 4 cases, une seule à la fois), écran `LWT_Lcd.lua`
  (palette propre, police Small en CN/CH/JP/KO/TH), textes partagés `LWT_PartText.lua` ; `LWT_PartMenu` ouvre la
  fenêtre quand la face est inscrite, l'infobulle sinon. Compteur : texture du cadran, sept rouleaux dans
  `ROLLS_BOX` (fractions du cadran), aiguille `DrawTextureAngle` d'angle `(total mod 10) / 10 × 360`, repli sur des
  rouleaux sur fond sombre sans texture ; sous le cadran total, dix dernières minutes, qualité (ambre pour l'eau non
  filtrée). `LWT_FixtureMenu` : ligne grisée « Eau : %1 L / %2 L » pour un appareil plombé alimenté par un relais
  LiveWater qui a de l'eau (capacité lue sur le relais, repli `WaterObjects.RELAY_LITRES`), ligne « pourquoi » gardée
  à sec. `LWT_Relays:fixtureStates` (fed, dry, notPlumbed, other ; `GamePlumbing:fixtures` donne `plumbed`) ;
  `showNetwork` renvoie `fixtures` des arrivées d'eau du réseau (dédoublonnées, 300 au plus) ; `LWT_NetworkView`
  les surligne (vert, rouge, ambre, gris) et la légende les compte quand il y en a. Clés nouvelles dans les onze
  langues (`IG_UI.json`, `ContextMenu.json`).
- Tests : `tests/test_readouts.py` (28 tests, rouges avant le code).
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 480 tests` … `OK` ; `python -B tools/check_mod.py`
  → `OK: 111 Lua file(s) checked`.

### G06 — Pièces en ligne droites

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : champ de définition `sidesByFacing` (révision d'API 19, `shared/LiveWater/LWT_API.lua`) = masque des côtés
  par orientation, validé dans `shared/LiveWater/LWT_Parts.lua` (`invalid_sides_by_facing`) ; `Parts:sidesOf(part)`
  remplace `Parts:sides(id)` et lit l'orientation enregistrée sur la pièce (`part.facing`, repli sur `sides`).
  `LWT_Network.linksOf` demande les côtés de la pièce posée. `LWT_Placement.added` passe `facingOf(spriteName)` à
  `Topology:add`/`canAdd`, qui l'enregistre sur l'entrée du registre (persistée avec `cuts`/`apart`, relue par
  `rebuild`). Compteur : `variants = { straight = { 21, 20 } }` (le dessin ne dépend plus des liens) ; compteur et
  vanne : `sidesByFacing = { [1] = N + S, [2] = E + W }` ; la vanne perd `facings` (elle ne tourne plus, ouverte ou
  fermée elle garde l'axe posé). Posé dans un T, le compteur prend l'axe du curseur et ne se raccorde qu'à ses deux
  côtés (pas de refus). Le raccord de baril n'est pas touché.
- Tests : `tests/test_inline_axis.py` (flanc d'un compteur EW et NS, compteur posé à côté d'un tuyau de flanc, vanne
  ouverte puis fermée sans changer d'axe, compteur dans un T sur ses deux axes, reconstruction depuis le registre,
  définition), rouges avant le code (8 échecs, 2 erreurs) ; bancs de `test_meter.py` et `test_valve.py` posés sur
  l'axe de leur conduite ; deux tests de la vanne qui tournait avec son tuyau supprimés (comportement retiré).
- Preuve du vert :
  - `python -B -m unittest discover -s tests -p "test_inline_axis.py"` → `Ran 10 tests` … `OK` ;
  - `python -B -m unittest discover -s tests` → `Ran 491 tests` … `OK` ;
  - `python -B tools/check_mod.py` → `OK: 111 Lua file(s) checked`.
- À reprendre : `autotest/lwt_hooks.lua` pose toujours la vanne (16) et le compteur (20) en est-ouest sur une case
  à deux voisins de la conduite, qui peut être un coude ou une ligne nord-sud ; il doit choisir une case droite et
  le sprite de son axe (16/17, 20/21), sinon le passage en jeu échoue. Page modder (`docs/wiki/*/06-for-modders.md`)
  à compléter de `sidesByFacing`.

### G07 — Arroseur lisible

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : recette `source/tiles/build_livewater_tiles.py`, `build_sprinkler` : manette rouge de l'arroseur manuel deux
  fois plus longue et épaisse (0,24 × 0,034 × 0,024 m, tige 0,014), le long du tuyau ouvert, en travers fermé ;
  programmateur de l'arroseur automatique avec un voyant (`SPR_LAMP`, boule de 0,026 sur une bague, cadran décalé),
  éteint au repos ; calque `build_sprinkler_lit` (voyant `lit_green`, base en masque) sur `sprinkler_auto_on`,
  composé au style comme les voyants de l'arrivée d'eau. Tête de l'arroseur inchangée (le jet garde sa place) ; mêmes
  index, mêmes propriétés ; contrat des tuiles (lignes 48-63) précisé. Aucun fichier Lua ni test touché.
- Preuve :
  - rendu des seuls groupes `sprinkler_manual_off/on`, `sprinkler_auto_off/on` (+ `__lit`), style, empaquetage
    (`packed 222 sprites`) ; comparaison sprite par sprite à l'ancienne planche : seuls 48-63 changent (jet 128-159
    identique au pixel) ;
  - profondeur : `total: 222 sprites, hits outside the sprite 0, left without depth 0` ;
  - `python -B tools/check_mod.py` → `OK: 111 Lua file(s) checked` ; les tests de la recette passent (les échecs du
    moment dans `test_valve.py`, `test_meter.py`, `test_readouts.py` viennent du chantier réseau en cours d'un autre
    agent, sans lien avec les tuiles).

### G08 — Bruit de vanne

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : quatre `.ogg` mono générés pour le mod (ElevenLabs, effets sonores), normalisés (`loudnorm` −18 LUFS, fondu
  de fin) dans `media/sound/LWT_Valve{Open,Close}{1,2}.ogg` ; scripts `sound LWT_ValveOpen` et `LWT_ValveClose`
  (`media/scripts/LWT_sounds.txt`), deux clips chacun, tirés au hasard par le jeu (`GameSound.getRandomClip`,
  `GameSound.java:50`). Serveur : `LWT_ValveSounds` abonné à `valveChanged`, port `GameSounds:once` (commande `sound`
  avec `once = true`) ; client : `LWT_PumpSounds` joue un son ponctuel sur un émetteur libre, sans toucher la boucle
  de la case.
- Tests `test_upkeep.py` (`ValveSound`, son ponctuel côté client), rouges avant le code.

### G09 — Bruit de la pompe et courant

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : `Pump.sound` rend la boucle tant que la pompe fonctionne (allumée, alimentée, en état), le bruit pour les
  zombies (rayon, volume) seulement quand elle pompe ; `Pump.powered` arrête le pompage dès que le courant tombe ;
  `Publisher:sound` ne fait de bruit pour les zombies qu'avec un rayon positif ; `Clock:powerChanged` relit le courant
  des pièces qui en ont besoin et les présente aussitôt ; `LWT_Server` l'appelle sur `Events.OnElectricityChanged`.
  Scénario en jeu : générateur arrêté puis relancé, le bruit de la pompe doit s'arrêter puis reprendre en moins de
  5 s.
- Tests `test_upkeep.py` (`Sound` : ronronnement sans demande, arrêt et reprise immédiats, pompe éteinte muette),
  rouges avant le code.
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 496 tests` … `OK` ;
  `python -B tools/check_mod.py` → `OK: 112 Lua file(s) checked`.

### G10 — Recettes rangées

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Fait : les 20 recettes (`LWT_recipes.txt`, `LWT_dismantle.txt`) ont `category = LiveWater` et la seule étiquette
  `AnySurfaceCraft` (plus d'`InHandCraft` : plus de doublon au menu contextuel de l'objet) ; la table de démontage
  (`LWT_Dismantle.lua`) donne la même catégorie ; clé `IGUI_CraftingCategories_LiveWater` (« LiveWater ») dans les
  onze `IG_UI.json` ; icônes `Item_LWT_<Pièce>.png` (64 × 64) des neuf objets posables, découpées dans la tuile sud
  stylée par `source/tiles/make_item_icons.py`, et `Icon = LWT_<Pièce>` dans `LWT_moveables.txt`.
- Tests `test_item_names.py` (`Recipes`, `Icons`), rouges avant le changement ; `test_drip.py` attend la catégorie
  LiveWater.
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 499 tests` … `OK` ;
  `python -B tools/check_mod.py` → `OK: 112 Lua file(s) checked`.

### G05 — Preuves en jeu

- Statut : Terminée (2026-11-20). Preuve : passage en jeu validé par l'utilisateur le 2026-11-20 (G05).
- Scénario (`autotest/lwt_hooks.lua`) :
  - raccords du banc : tonneau entre deux tuyaux (té, index 208), caisse au croisement de trois tuyaux (croix,
    236) ;
  - vanne et compteur posés sur une case droite de la conduite, dans l'axe de leurs voisins (`alongAxis`) ;
  - fenêtres « Information » de la pompe (`lcd`) et du compteur (`counter`, après la pose du filtre, total qui
    augmente) ; appareils dans la vue du réseau ; ligne « Eau » de l'évier (grisée) ;
  - courant : le courant de la ville est coupé par l'option `ElecShutModifier` de la copie du monde, la pompe ronronne
    sur son générateur ; générateur arrêté puis relancé, le bruit suit.
- Correctifs issus des passages : ligne « Eau » rouge → grisée ; test qui cherchait une vanne nord-sud dans
  l'inventaire (l'objet est la vanne est-ouest, la tuile tournée se pose comme le fait le curseur).
- Passages finaux (code du 2026-11-19, 13 h) :
  - solo, code 0, `summary=49/49 PASS`, `runs/20261119-130619-sp-f42302fe26a2` (« pump hums on its generator with
    the grid cut - grid false », « pump hum follows the generator at once - off in 261 ms, on in 248 ms ») ;
  - visuel FR, code 0, `summary=65/65 PASS`, `runs/20261119-130740-sp-37a5bef72e41` (« fitting between two pipes drawn
    as a tee - 208 », « fitting at a crossing drawn as a cross - 236 », « water meter total counts the house water -
    25.0 L ») ;
  - multijoueur, code 0, serveur `20/20 PASS`, client `6/6 PASS`, `runs/20261119-131148-mp-d1d4d90a1e9b`.
- Hors jeu : `python -B -m unittest discover -s tests` → `Ran 496 tests` … `OK` ; `python -B tools/check_mod.py` →
  `OK: 112 Lua file(s) checked`.
- Non vus en jeu : son des vannes (aucun test ne l'écoute), fenêtres en multijoueur, noms dans l'inventaire.

# Contrat des tuiles de LiveWater

Contrat entre la recette des tuiles (`source/tiles/`) et le code Lua (définitions des pièces). Un index publié n'est
jamais renuméroté ni réattribué (D03). Tileset `batman_livewater_01` (tiledef **7176**), 8 colonnes, **256 sprites** au total (8 × 32), sprite `batman_livewater_01_<index>`.
Orientations dans l'ordre S, E, N, W. Axe `ew` = tuyau est-ouest, `ns` = nord-sud.

| Index | Tuile | Clé de rendu |
|---|---|---|
| 0-15 | tuyau, index = masque des côtés raccordés (N=1, E=2, S=4, W=8) | `pipe_m00` … `pipe_m15` |
| 16-17 | vanne ouverte `ew`, `ns` | `valve_open_ew`, `valve_open_ns` |
| 18-19 | vanne fermée `ew`, `ns` | `valve_closed_ew`, `valve_closed_ns` |
| 20-21 | compteur d'eau `ew`, `ns` | `flowmeter_ew`, `flowmeter_ns` |
| 24-27 | pompe d'étang arrêtée S E N W | `pump_off` |
| 28-31 | pompe d'étang en marche | `pump_on` |
| 32-35 | inutilisées depuis l'ADR-005 D02 (ancienne pompe avec filtre, en marche ; gardées dans le tileset) | `pump_filter_on` |
| 36-39 | inutilisées depuis l'ADR-005 D02 (ancienne pompe avec filtre, arrêtée ; gardées dans le tileset) | `pump_filter_off` |
| 40-43 | arrivée d'eau, eau filtrée (voyant vert) | `house_inlet` |
| 44-47 | arrivée d'eau, eau non filtrée (voyant ambre) | `house_inlet_unfiltered` |
| 48-51 | arroseur manuel fermé (manette rouge quart de tour, deux fois la taille réelle, en travers du tuyau ; ADR-008 D09) | `sprinkler_manual_off` |
| 52-55 | arroseur manuel ouvert, manette le long du tuyau (sans jet : le jet est un calque animé) | `sprinkler_manual_on` |
| 56-59 | arroseur automatique au repos, voyant du programmateur éteint | `sprinkler_auto_off` |
| 60-63 | arroseur automatique en marche, voyant vert allumé sur le programmateur (calque `__lit` composé au style ; sans jet) | `sprinkler_auto_on` |
| 64-67 | raccord de baril « Remplir », récipient haut (tonneau, fût) | `barrel_fill` |
| 68-71 | raccord de baril « Remplir », récipient bas (caisse bâchée) | `barrel_fill_low` |
| 72-75 | raccord de baril « Pomper » | `barrel_pump` |
| 76 | réservoir relais invisible des arrivées d'eau (défini sans image, posé par le serveur, E09) | — |
| 77-79 | réservés | — |
| 80-103 | inutilisés depuis l'ADR-003 (ancien jet) | — |
| 128-159 | jet d'eau d'arroseur qui fait le tour (ADR-003 D03), image f (0-7), orientation k : `128 + 4 * f + k` (calque, sans propriétés) | `sprinkler_jet` |
| 104-123 | tuyau avec manchon de clôture (ADR-002 D03), masques 0 à 15 dans l'ordre croissant, et pour chaque masque : manchon nord (bords 1) s'il contient N, puis manchon ouest (bords 8) s'il contient O, puis les deux (bords 9) s'il contient N et O ; 104 = masque 1 bords 1 | `pipe_m01_x1` … `pipe_m15_x9` |
| 160-175 | ligne de goutte-à-goutte (ADR-004 D01), index = 160 + masque des côtés raccordés ; tuyau souple noir posé au sol, goutteurs et taches humides ; bout bouché (un côté), rouleau court (masque 0) | `drip_m00` … `drip_m15` |
| 176-179 | arrivée d'eau avec cartouche filtrante montée, eau propre (voyant vert ; boîtier de filtre sous le coffret, ADR-005 D04) | `house_inlet_filter` |
| 180-183 | arrivée d'eau avec cartouche filtrante montée, eau non filtrée refusée (voyant ambre : cartouche usée) | `house_inlet_filter_unfiltered` |
| 184-187 | raccord de baril « Remplir », récipient haut, coudé : tuyau arrivant du côté +1 de l'orientation (E pour S, N pour E, W pour N, S pour W ; ADR-008 D01) | `barrel_fill_bend1` |
| 188-191 | raccord de baril « Remplir », récipient haut, coudé : tuyau arrivant du côté +3 (W pour S, S pour E, E pour N, N pour W) | `barrel_fill_bend3` |
| 192-195 | raccord de baril « Remplir », récipient bas, coudé côté +1 | `barrel_fill_low_bend1` |
| 196-199 | raccord de baril « Remplir », récipient bas, coudé côté +3 | `barrel_fill_low_bend3` |
| 200-203 | raccord de baril « Pomper », coudé côté +1 | `barrel_pump_bend1` |
| 204-207 | raccord de baril « Pomper », coudé côté +3 | `barrel_pump_bend3` |
| 208-211 | raccord de baril « Remplir », récipient haut, en té : tuyaux des côtés +1 et +3 (traversant) ; ADR-008 D01b | `barrel_fill_tee` |
| 212-215 | raccord de baril « Remplir », récipient haut, tuyaux devant et côté +1 | `barrel_fill_front1` |
| 216-219 | raccord de baril « Remplir », récipient haut, tuyaux devant et côté +3 | `barrel_fill_front3` |
| 220-223 | raccord de baril « Remplir », récipient haut, en croix : tuyaux devant, +1 et +3 | `barrel_fill_cross` |
| 224-227 | raccord de baril « Remplir », récipient bas, en té : tuyaux des côtés +1 et +3 (traversant) | `barrel_fill_low_tee` |
| 228-231 | raccord de baril « Remplir », récipient bas, tuyaux devant et côté +1 | `barrel_fill_low_front1` |
| 232-235 | raccord de baril « Remplir », récipient bas, tuyaux devant et côté +3 | `barrel_fill_low_front3` |
| 236-239 | raccord de baril « Remplir », récipient bas, en croix : tuyaux devant, +1 et +3 | `barrel_fill_low_cross` |
| 240-243 | raccord de baril « Pomper », en té : tuyaux des côtés +1 et +3 (traversant) | `barrel_pump_tee` |
| 244-247 | raccord de baril « Pomper », tuyaux devant et côté +1 | `barrel_pump_front1` |
| 248-251 | raccord de baril « Pomper », tuyaux devant et côté +3 | `barrel_pump_front3` |
| 252-255 | raccord de baril « Pomper », en croix : tuyaux devant, +1 et +3 | `barrel_pump_cross` |

Jet d'eau animé des arroseurs : le moteur n'anime pas le calque d'une tuile ordinaire (base de connaissances,
`custom-tiles-entities.md`, « Calque animé (`AttachAnim`) »). Le client attache lui-même l'image courante du jet
(index 128-159) sur un arroseur en marche, par l'exception D08a de l'ADR-001. Les tuiles « en marche » (52-55, 60-63)
ne portent donc pas le jet.

Objet d'inventaire : `LiveWater.WaterFilter` (`Item_LWT_WaterFilter`). Objets posables `Base.Mov_LiveWater_<Nom>` :
`Pipe`, `PondPump`, `Valve`, `FlowMeter`, `HouseInlet`, `Sprinkler`, `SprinklerAuto`, `BarrelFitting`. Le tuyau est
un meuble posable comme les autres (Q01) : ses 16 tuiles (`batman_livewater_01_0` à `_15`) et ses 20 tuiles à manchon (`_104` à `_123`) portent
`CustomItem = Base.Mov_LiveWater_Pipe`, `IsMoveAble`, `PickUpWeight` 4, `PickUpTool`/`PlaceTool` `Wrench`, sans
`Facing` ; le curseur montre la tuile 10 (droit est-ouest), puis la forme suit les voisins.

Ligne de goutte-à-goutte (ADR-004) : objet posable `Base.Mov_LiveWater_DripLine` ; ses 16 tuiles (`_160` à `_175`)
portent `CustomItem = Base.Mov_LiveWater_DripLine`, `CustomName` « Drip Line », `IsMoveAble`, `PickUpWeight` 2, sans
`PickUpTool`/`PlaceTool` (posée et ramassée à la main) ni `Facing`, sans manchon de clôture ; le curseur montre la tuile 170
(droite est-ouest), puis la forme suit les voisins.

Raccord de baril en embranchement (ADR-008 D01, D01b) : l'orientation reste celle de la pose (le baril derrière) ;
l'eau traverse le raccord d'un tuyau à l'autre. Le serveur dessine la forme du masque des côtés raccordés relatifs à
l'orientation (1 devant, 2 côté +1, 8 côté +3 ; derrière non dessiné), champ `branches` de la définition de la pièce :
rien ou devant seul → droit (64-75), 2 → coude +1, 8 → coude +3, 10 → té, 3 → devant + 1, 9 → devant + 3, 11 → croix.
Les tuiles 184-255 portent les mêmes propriétés que 64-75 (`CustomItem =
Base.Mov_LiveWater_BarrelFitting`, `Facing`, décalages vers les tuiles sœurs du même groupe, `CanScrap`) ; l'objet
posable montre toujours la tuile droite 64. Modèle : coude galvanisé au centre, vanne avancée de 0,11 vers le baril,
té ou croix galvanisé au centre pour les autres formes, tuyau souple inchangé.

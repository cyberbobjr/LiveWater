# Contrat des tuiles de LiveWater

Contrat entre la recette des tuiles (`source/tiles/`) et le code Lua (définitions des pièces). Un index publié n'est
jamais renuméroté ni réattribué (D03). Tileset `batman_livewater_01`, 8 colonnes, sprite `batman_livewater_01_<index>`.
Orientations dans l'ordre S, E, N, W. Axe `ew` = tuyau est-ouest, `ns` = nord-sud.

| Index | Tuile | Clé de rendu |
|---|---|---|
| 0-15 | tuyau, index = masque des côtés raccordés (N=1, E=2, S=4, W=8) | `pipe_m00` … `pipe_m15` |
| 16-17 | vanne ouverte `ew`, `ns` | `valve_open_ew`, `valve_open_ns` |
| 18-19 | vanne fermée `ew`, `ns` | `valve_closed_ew`, `valve_closed_ns` |
| 20-21 | compteur d'eau `ew`, `ns` | `flowmeter_ew`, `flowmeter_ns` |
| 24-27 | pompe d'étang arrêtée S E N W | `pump_off` |
| 28-31 | pompe d'étang en marche | `pump_on` |
| 32-35 | pompe avec filtre, en marche | `pump_filter_on` |
| 36-39 | pompe avec filtre, arrêtée | `pump_filter_off` |
| 40-43 | arrivée d'eau, eau filtrée (voyant vert) | `house_inlet` |
| 44-47 | arrivée d'eau, eau non filtrée (voyant ambre) | `house_inlet_unfiltered` |
| 48-51 | arroseur manuel fermé | `sprinkler_manual_off` |
| 52-55 | arroseur manuel ouvert (sans jet : le jet est un calque animé) | `sprinkler_manual_on` |
| 56-59 | arroseur automatique au repos | `sprinkler_auto_off` |
| 60-63 | arroseur automatique en marche (sans jet) | `sprinkler_auto_on` |
| 64-67 | raccord de baril « Remplir », récipient haut (tonneau, fût) | `barrel_fill` |
| 68-71 | raccord de baril « Remplir », récipient bas (caisse bâchée) | `barrel_fill_low` |
| 72-75 | raccord de baril « Pomper » | `barrel_pump` |
| 76-79 | réservés | — |

Jet d'eau animé des arroseurs : calque attaché par le client, images fournies par le mod ; nommage et mécanisme
définis par la recherche moteur de l'étape E06 (voir la fiche E06 du plan).

Objets d'inventaire : `LiveWater.PipeSection` (icône `Item_LWT_PipeSection`), `LiveWater.WaterFilter`
(`Item_LWT_WaterFilter`). Objets posables `Base.Mov_LiveWater_<Nom>` : `PondPump`, `Valve`, `FlowMeter`,
`HouseInlet`, `Sprinkler`, `SprinklerAuto`, `BarrelFitting`. Les tuyaux ne sont pas des meubles posables : ils se
posent par une action de construction qui consomme une `LiveWater.PipeSection` (Q01).

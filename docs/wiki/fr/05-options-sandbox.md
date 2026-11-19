# Options sandbox

Page **LiveWater** des options sandbox (noms `LiveWater.<Option>` dans les `SandboxVars` du serveur).

| Option | Défaut | Bornes | Effet |
|---|---|---|---|
| Débit des pompes (`PumpFlowMultiplier`) | 1,0 | 0,1 à 10 | multiplie les litres qu'une pompe donne toutes les 10 minutes (50 L à 1,0) |
| Durée des cartouches filtrantes (`FilterCapacityMultiplier`) | 1,0 | 0,1 à 10 | multiplie les litres qu'une cartouche nettoie (500 L à 1,0) |
| Usure des pompes (`PumpWearMultiplier`) | 1,0 | 0 à 10 | multiplie le rendement perdu en marche (environ une semaine de 100 % à 0 % à 1,0 ; 0 = sans usure) |
| Portée de l'arrivée d'eau (`InletRange`) | 20 | 1 à 100 | cases autour d'une arrivée d'eau sur un bâtiment de la carte, jusqu'à 3 étages au-dessus |
| Portée de l'arrivée d'eau d'une base (`BaseRange`) | 12 | 1 à 50 | cases autour d'une arrivée d'eau hors bâtiment de la carte (base du joueur) |
| Corriger les lave-linge raccordés (`WasherFix`) | activé | oui/non | multijoueur : les lave-linge alimentés par une arrivée d'eau apparaissent raccordés et s'arrêtent à sec |
| Portée des arroseurs (`SprinklerRadiusMultiplier`) | 1,0 | 0,5 à 5 | multiplie le rayon d'arrosage (2 cases à 1,0, 10 au plus) |
| Débit des arroseurs (`SprinklerFlow`) | 10 | 0 à 100 | litres qu'un arroseur ouvert prélève toutes les 10 minutes, que les plantes aient soif ou non ; un quart se perd en l'air, les plantes prennent ce qu'il leur faut, le reste est perdu |
| Débit du goutte-à-goutte (`DripFlow`) | 0,5 | 0 à 10 | litres que prélève chaque case de ligne toutes les 10 minutes quand le réseau lui donne de l'eau ; les plantes voisines prennent ce qu'il leur faut, le reste est perdu |
| Minuterie d'arroseur : intervalle le plus court (`SprinklerTimerMin`) | 1 | 1 à 168 | heures minimales qu'un joueur peut régler entre deux arrosages |
| Minuterie d'arroseur : intervalle le plus long (`SprinklerTimerMax`) | 24 | 1 à 168 | heures maximales qu'un joueur peut régler entre deux arrosages |
| Conteneurs qu'un raccord de remplissage peut remplir (`FillContainers`) | `WaterDispenser` | texte | noms de scripts d'entité ou de sprites séparés par `;`, remplis d'eau croupie comme un baril, quelle que soit leur taille ; barils, récupérateurs d'eau et mangeoires fonctionnent toujours |

Option du mod (pour chaque joueur, dans les options des mods du jeu) : **Jet des arroseurs animé**, activée par
défaut ; décochez-la pour un jet fixe sur un ordinateur lent.

Suite : [Pour les moddeurs](06-pour-les-moddeurs.md)

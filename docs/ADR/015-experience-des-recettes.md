# ADR-015 — Expérience gagnée par les recettes : Travail des métaux et Électricité

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-015-EXPERIENCE-DES-RECETTES` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | voir le [plan 015](../ADR-plans/plan-015-experience-des-recettes.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : `scripts/LWT_recipes.txt`, `scripts/LWT_dismantle.txt`, tests, wiki, CHANGELOG |
| Documents liés | [ADR-007](termines/007-demontage-et-butin.md) (démontage), [ADR-010](010-pompe-a-eau-et-vanne-immediate.md) (pompe) |
| Références | clé `xpAward` des `craftRecipe` (vanilla : `xpAward = MetalWelding:30`, recettes de métallurgie de `media/scripts/generated`) ; LiveWire : chaque recette, démontage compris, donne de l'expérience d'Électricité |
| Origine | demande de l'utilisateur du 2026-11-19 : « il faut aligner le gain d'experience, "travail des metaux" et "éléctricité" (pompe à eau) pour l'expérience » |

## Contexte

Au 2026-11-19, seules deux recettes de LiveWater sur onze donnent de l'expérience : la pompe à eau (15 XP
d'Électricité) et l'arroseur automatique (10 XP d'Électricité). Les pièces en métal et tous les démontages n'en
donnent aucune, alors que dans LiveWire, le mod frère, chaque recette en donne. Le jeu n'a pas de compétence de
plomberie ; la plus proche pour des tuyaux, vannes et raccords en métal est le Travail des métaux (`MetalWelding`).

## Décisions

- **D01 — Fabrication.** Pièces en métal : Travail des métaux, à proportion de la durée de la recette — tuyaux
  (découpe) 5, vanne 5, raccord de remplissage 5, compteur d'eau 8, arroseur 8, arrivée d'eau de la maison 10. Pièces
  électriques : Électricité, inchangé — pompe à eau 15, arroseur automatique 10.
- **D02 — Démontage.** Même compétence que la fabrication, montant faible comme dans LiveWire : pièces en métal 2 XP
  de Travail des métaux ; pompe à eau 5 et arroseur automatique 3 XP d'Électricité.
- **D03 — Ni métal ni électricité : pas d'expérience.** Cartouche filtrante (charbon et tissu, fabrication, recharge,
  démontage) et goutte-à-goutte (tuyau d'arrosage et ruban adhésif) ne relèvent d'aucune des deux compétences
  demandées : ils n'en donnent pas.
- **D04 — Aucun niveau requis ajouté.** Seule l'expérience change ; les niveaux exigés restent ceux d'aujourd'hui
  (Électricité 2 pour la pompe et l'arroseur automatique).

## Conséquences

- Construire un réseau d'eau fait progresser le Travail des métaux, et l'électricité de la pompe fait progresser
  l'Électricité, comme dans LiveWire.
- Fabriquer puis démonter rapporte peu (2 XP), sans boucle d'expérience rentable.

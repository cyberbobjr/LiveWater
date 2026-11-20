# ADR-009 — Cartouche rechargeable ; plus de baril raccordé directement à la maison

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-009-CARTOUCHE-RECHARGEABLE-ET-BARILS` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 009](../../ADR-plans/termines/plan-009-cartouche-rechargeable-et-barils.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : cartouche filtrante (objet, retrait, recettes, icône, traductions) ; raccordement direct des barils à l'arrivée d'eau (serveur, commandes, menu client, diagnostic, traductions, tests, documentation) |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (L01-L03, L06, L07, L12 remplacés ; P17, D26 raccord de baril), [ADR-004](004-goutte-a-goutte.md) (D04 gravité), [ADR-005](005-filtre-a-l-arrivee-d-eau.md) (cartouche à l'arrivée d'eau), [ADR-007](007-demontage-et-butin.md) (démontage de la cartouche) |
| Références | `IsoObject.createSampleAndPurifyWater` (`IsoObject.java:2777`, robinet vanilla qui purifie l'eau d'un réservoir au-dessus) ; `LWT_CmdCartridge.takeOut` |
| Origine | questions de l'utilisateur du 2026-11-19 sur l'usure du filtre et les barils ; réponses : « solution B, pouvoir la recharger » et « sans pompe [un baril] ne peut pas envoyer l'eau dans la maison (pas de pression), un baril ne peut alimenter que le goutte à goutte sans pompe. Un baril ne peut pas être directement raccordé à une maison par le raccord LiveWater » |

## Contexte

- Une cartouche usée retirée de l'arrivée d'eau est jetée : le joueur ne récupère rien.
- L'ADR-001 (L01-L03, L06, L07, L12) permet de raccorder un baril à l'arrivée d'eau à la clé à tuyau, sans tuyau ni
  pompe : l'eau du baril remplit les réservoirs cachés de la maison par gravité, sans filtre. L'utilisateur refuse ce
  raccourci : sans pompe, pas de pression pour une maison.

## Décisions

- **D01 — La cartouche usée revient au joueur.** Retirer une cartouche usée rend un objet **Cartouche filtrante
  usée** (`LiveWater.WaterFilterSpent`, objet distinct, icône assombrie de la cartouche) au lieu de la jeter. Une
  cartouche usée ne se monte pas dans une arrivée d'eau. Une cartouche qui garde de l'usage revient comme aujourd'hui,
  avec son état.
- **D02 — Recharger la cartouche.** Recette **Recharger une cartouche filtrante** (catégorie LiveWater, panneau
  d'artisanat seul, comme ADR-008 D12) : 1 cartouche usée + 2 charbons + 1 chiffon (les mêmes matières que la
  fabrication, sans l'enveloppe) → 1 cartouche neuve (500 L, option de bac à sable comprise). La cartouche usée se
  démonte aussi (recette de démontage, rend le chiffon), comme une cartouche neuve (ADR-007).
- **D03 — Plus de baril raccordé directement à la maison.** Le raccordement d'un baril à l'arrivée d'eau à la clé à
  tuyau (menu du baril « Raccorder à l'arrivée d'eau », réserve, déconnexion) est retiré, ainsi que le remplissage des
  réservoirs de la maison par ces barils. Un baril ne rejoint le réseau que par un **raccord de baril** posé entre un
  tuyau et lui (ADR-001 D26). Réglé sur Pomper, sans pompe sur le réseau, il ne donne de l'eau qu'au goutte-à-goutte
  (ADR-004 D04, déjà en place) ; l'arrivée d'eau et les arroseurs n'ont rien sans pompe. Le baril vanilla posé
  au-dessus d'un évier reste le comportement du jeu, que LiveWater ne touche pas.
  Remplace L01, L02, L03 (total des barils au robinet), L06, L07 et la partie « baril » de L12 de l'ADR-001. Les
  raisons de diagnostic propres à ces barils disparaissent ; une arrivée d'eau sans pompe dit qu'elle n'a pas de
  pression.

## Conséquences

- Code, commandes, menu, traductions et tests du raccordement direct supprimés (règle : supprimer du code supprime
  aussi ses tests, sans test « garde-fou »). Mod non publié : aucune reprise de sauvegarde (marques `LiveWaterBarrel`
  laissées sans effet).
- Un objet et une recette nouveaux, avec leurs traductions et leur icône.

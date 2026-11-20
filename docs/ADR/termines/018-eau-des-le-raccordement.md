# ADR-018 — L'eau arrive dès qu'un point d'eau est raccordé

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-018-EAU-DES-LE-RACCORDEMENT` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 018](../../ADR-plans/termines/plan-018-eau-des-le-raccordement.md) |
| Décideur | l'utilisateur (« Implémente 2 », 2026-11-20) |
| Portée | `batman_LiveWater` : enveloppe de l'action vanilla de raccordement (autorité), pas immédiat du réseau de l'arrivée d'eau concernée (`LWT_Clock`), relevé des relais (`LWT_Relays.touched`), tests, CHANGELOG |
| Documents liés | [ADR-010](010-pompe-a-eau-et-vanne-immediate.md) (une vanne agit tout de suite : pas immédiat `Clock:switched`), [ADR-006](006-vision-debit.md) |
| Références | vanilla `ISPlumbItem:complete` (`ISPlumbItem.lua:31-38` : `setUsesExternalWaterSource(true)`, `sendObjectChange`, aucun objet ajouté donc aucun `OnObjectAdded`) ; `LWT_Clock.lua` (`switched`, `MAX_AHEAD`) ; `LWT_Relays.lua` (`touched`, `need`, `deliver`) |
| Origine | signalement de l'utilisateur du 2026-11-20 : pompe en marche, arrivée d'eau avec filtre, évier raccordé en dernier ; l'évier reste sans eau (« l'eau arrive dans les 10 minutes ») et l'eau n'arrive qu'après près d'une heure de jeu |

## Contexte

Raccorder un évier, une baignoire, une douche, des toilettes ou un lave-linge avec la clé (action vanilla) ne prévient
pas LiveWater : l'eau n'est envoyée qu'à la tranche suivante de 10 minutes, au mieux. Le diagnostic hors jeu du
2026-11-20 n'a pas reproduit le retard d'une heure (un relais est rempli au premier pas après le raccordement dans une
simulation) ; sa cause reste inconnue. L'utilisateur retient la correction « eau tout de suite au raccordement ».

## Décisions

- **D01 — Raccordement surveillé.** Sur l'autorité (solo ou serveur), LiveWater enveloppe `ISPlumbItem.complete`
  une seule fois, en gardant arguments, retour et comportement vanilla. Après le raccordement réussi d'un point d'eau :
  les relais autour de sa case sont relevés (`touched`) et le réseau de chaque arrivée d'eau dont la zone couvre la case
  avance d'un pas tout de suite, comme quand une vanne s'ouvre (`Clock:switched`, plafonné par `MAX_AHEAD`).
- **D02 — Un seul mécanisme de pas immédiat.** Le pas immédiat d'une vanne et celui d'un raccordement passent par la
  même méthode de `LWT_Clock` (extraite de `switched`), sans copie.
- **D03 — Rien d'autre ne change.** Le diagnostic, l'ordre des tâches d'un pas et le remplissage des relais restent
  tels quels.

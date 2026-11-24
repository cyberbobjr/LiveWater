# ADR-023 — L'arrivée d'eau sert tous les étages au-dessus d'elle

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-023-ARRIVEE-D-EAU-SANS-LIMITE-D-ETAGES` |
| Date de création et de mise à jour | 2026-11-22 (renvoi du 2026-11-24) |
| Statut | Accepté (2026-11-22) |
| Avancement | Terminé le 2026-11-22 ; voir le [plan 023](../../ADR-plans/termines/plan-023-arrivee-d-eau-sans-limite-d-etages.md) |
| Décideur | l'utilisateur (« ne plus limiter la hauteur des bâtiments, à faire », 2026-11-22) |
| Portée | `batman_LiveWater` : zone servie par une arrivée d'eau (`LWT_InletArea`), relevé des points d'eau (`LWT_GamePlumbing`), textes des options de partie (11 langues), wiki, descriptions Workshop, spécifications, CHANGELOG |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D18 arrivée d'eau, D21 réservoirs relais, L11 base du joueur) |
| Références | `LWT_InletArea.lua` (`LEVELS_UP = 3`) ; `LWT_RelayPlan.lua` (`TOP = 31`) ; Java 42.22 `IsoCell.java:157` (`maxHeight = 32`, niveaux 0 à 31), `IsoChunk.java:2870` (`getMaxLevel`), `BuildingDef.java:505` (`containsXYZ` : une pièce du bâtiment à ce niveau) |
| Origine | question d'un joueur du 2026-11-22 (maison de quatre niveaux : les tuyaux montent-ils ?) |

## Contexte

Les tuyaux restent sur un niveau ; l'arrivée d'eau porte l'eau aux étages. ADR-001 D18 la limitait à 3 étages
au-dessus d'elle. Cette limite n'a pas de raison de jeu : un immeuble de cinq niveaux ou une tour construite par les
joueurs restait en partie sans eau, sans que rien ne l'explique au joueur.

## Décisions

- **D01 — Plus de limite vers le haut.** Une arrivée d'eau sert les points d'eau de sa zone depuis son niveau (base
  du joueur) ou depuis le niveau le plus bas du bâtiment (bâtiment de la carte) jusqu'au dernier niveau de la carte.
  Cette décision remplace « jusqu'à 3 étages au-dessus » d'ADR-001 D18 et L11 ; ADR-001 garde sa rédaction d'origine.
  (Renvoi du 2026-11-24 : en base construite, la zone descend aussi à 2 niveaux de sous-sol, voir
  [ADR-026](026-sous-sol-d-une-base-construite.md) D01.)
- **D02 — Le reste de la zone ne change pas.** Portée horizontale (options de partie), pièces du bâtiment de la carte
  seulement, 2 niveaux de sous-sol, points d'eau d'origine d'une maison voisine laissés en mode base : inchangés.
- **D03 — Le relevé ne parcourt pas les niveaux vides.** L'adaptateur du jeu arrête son parcours au plus haut niveau
  qui existe dans les chunks de la zone (`IsoChunk:getMaxLevel`) : le coût du relevé suit la hauteur réelle des
  constructions, pas celle de la carte. La règle pure (`LWT_InletArea`) ne connaît que le dernier niveau de la carte.
- **D04 — Dernier niveau de la carte.** Un point d'eau posé au niveau 31 ne peut pas recevoir de réservoir au-dessus
  de lui : il reste sans eau (règle déjà en place dans `LWT_RelayPlan`). La constante du dernier niveau a un seul
  propriétaire.

## Hors périmètre

Un point d'eau en plein air (toit en terrasse, jardin) : le jeu ne propose pas de le raccorder hors d'une pièce.
Analyse et pistes dans [ameliorations-et-idees.md](../../ameliorations-et-idees.md).

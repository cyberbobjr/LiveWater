# ADR-003 — Zone arrosée lisible : carré, surlignage, jet qui fait le tour

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-003-ZONE-ARROSEE-LISIBLE` |
| Date de création et de mise à jour | 2026-11-18 (D04 ajoutée le même jour) |
| Statut | Accepté (2026-11-18) |
| Avancement | Terminé le 2026-11-18 ; voir le [plan 003](../../ADR-plans/termines/plan-003-zone-arrosee-lisible.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : capacité `spray`, adaptateur des plantes (`LWT_Plants`), menu client de l'arroseur, jet animé (`LWT_SprinklerJet`, tuiles 80-103) ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D08a, D19), [contrat des tuiles](../../annexes/conception/tuiles-contrat.md) |
| Références | vue du réseau (ADR-001 D11, `setHighlightColor` + `setHighlighted(true, false)`, `ui-windows.md:67,166-168`) |
| Origine | remarque de l'utilisateur du 2026-11-18 : « l'animation du sprinkler est trompeuse, on ne sait pas exactement quelles cases sont arrosées » ; pistes retenues : « 1,3,4 » |

## Contexte

L'arroseur arrose un disque de rayon 2 (13 cases, `LWT_Plants`), alors que son jet animé ne vise qu'une direction : le
joueur ne sait pas quelles cases sont arrosées.

## Décisions

- **D01 — Zone carrée.** Un arroseur arrose les cases à `rayon` cases au plus sur chaque axe (distance de Tchebychev) :
  rayon 2 → carré de 5 × 5, 25 cases, centré sur l'arroseur. Le réglage `radius` et l'option sandbox
  `SprinklerRadiusMultiplier` gardent leur sens. Remplace le disque d'ADR-001 D19.
- **D02 — Surlignage à la demande.** Clic droit sur un arroseur : « Afficher la zone arrosée » surligne au sol chaque case de
  la zone (couleur de l'eau), « Masquer la zone arrosée » l'enlève. Mécanisme de la vue du réseau : surbrillance
  persistante, sans abonnement par image, retirée explicitement ou quand la case est déchargée. Le client calcule la zone
  à partir du rayon de la pièce (même calcul que le serveur, fonction partagée).
- **D03 — Jet qui fait le tour.** Le jet animé balaie les quatre côtés à tour de rôle au lieu d'une seule direction :
  8 images par tour (S, SE, E, NE, N, NW, W, SW), même cadence (6 images par seconde au plus, ADR-001 D08a). Le dessin
  reste dans la case de l'arroseur (une tuile ne peut pas déborder) : il montre que l'arroseur tourne ; la zone exacte,
  c'est le surlignage (D02).

- **D04 — Toutes les zones arrosées** (demande de l'utilisateur, 2026-11-18 : « mets une option pour voir toutes les
  zones arrosées, pas seulement celles avec l'arroseur mais aussi les zones arrosées par le goutte-à-goutte »). Clic
  droit sur un arroseur ou une ligne de goutte-à-goutte (et seulement sur eux) : « Afficher toutes les zones arrosées »
  surligne les zones de toutes les pièces qui arrosent dans un rayon de 25 cases autour du joueur, d'une seule couleur
  (l'utilisateur : « pas besoin de dissocier […], tu peux unifier les zones à afficher ») ; une ligne de goutte-à-goutte
  offre aussi « Afficher la zone arrosée » pour elle seule. **Mise à jour du 2026-11-18** (l'utilisateur : « je ne
  voulais qu'un seul menu "voir toutes les zones arrosées" ») : l'option « Afficher la zone arrosée » d'une seule pièce
  (D02) est retirée ; il ne reste que « Afficher toutes les zones arrosées », puis « Masquer la zone arrosée ». Le débit d'une pièce se lit dans son « Information »
  (ADR-006 D09). Mêmes règles de zone que l'autorité (`LWT_SprayArea`, `LWT_DripArea`),
  liens d'une ligne lus sur son image côté client.

## Arbitrages rendus

- Q01 — Pistes retenues par l'utilisateur le 2026-11-18 : surlignage (1), jet qui fait le tour (3), zone carrée (4).
  Écartées : sol mouillé (2), nombre de cases dans « Information » (5).

## Arbitrages ouverts

Aucun.

## Conséquences

- Un arroseur dessert 25 cases au lieu de 13 : il demande plus d'eau par pas quand tout le carré est planté.
- Les tuiles du jet (80-103) sont refaites : 8 images au lieu de 6 × 4 orientations.

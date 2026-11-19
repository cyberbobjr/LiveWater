# ADR-010 — Pompe à eau ; une vanne agit tout de suite

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-010-POMPE-A-EAU-ET-VANNE-IMMEDIATE` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | En cours ; voir le [plan 010](../ADR-plans/plan-010-pompe-a-eau-et-vanne-immediate.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : nom affiché de la pompe (traductions, documentation) ; manœuvre d'une vanne (horloge, relais de l'arrivée d'eau, composition serveur, tests) |
| Documents liés | [ADR-001](termines/001-reseau-eau-ouvert.md) (D02 vanne, D09 pas de dix minutes, D18 relais), [ADR-008](008-lisibilite-du-reseau.md) (D10 bruit de vanne, D11 courant immédiat) |
| Références | `LWT_Clock` (`tick`, `settle`, `powerChanged`), `LWT_CmdSwitchValve`, `Network:reach`, `Network:behindClosed`, `LWT_Relays` |
| Origine | demandes de l'utilisateur du 2026-11-19 : « renommer pompe à étang en "pompe à eau" » ; « l'ouverture/fermeture d'une vanne doit être immédiate avec effet immédiat (coupure / flow de l'eau) » ; « ne pas attendre 10 minutes, effet immédiat (vanne d'arroseur ou vanne générale) » |

## Contexte

- La pompe s'appelle « Pompe d'étang » (« Pond Pump ») alors qu'elle pompe aussi dans une rivière ou un puits.
- Ouvrir ou fermer une vanne change son état tout de suite, mais l'eau ne suit qu'au pas suivant de l'horloge (jusqu'à
  dix minutes de jeu) : un arroseur fermé continue d'arroser, un arroseur ouvert reste sec, la maison garde l'eau.

## Décisions

- **D01 — « Pompe à eau ».** Le nom affiché devient « Pompe à eau » (FR) et « Water Pump » (EN), dans les noms
  d'objet, de meuble, de fenêtre, de recettes et la documentation, et l'équivalent dans les autres langues. Les
  identifiants internes (`PondPump`, `Mov_LiveWater_PondPump`, recettes `LWT…PondPump`, sprites) ne changent pas.
- **D02 — Une manœuvre de vanne fait passer le réseau tout de suite.** Ouvrir ou fermer une vanne (vanne de conduite
  ou vanne d'un arroseur) fait le pas du réseau de la vanne aussitôt : l'eau coule ou s'arrête, les arroseurs arrosent
  ou s'arrêtent, les compteurs et la pompe se mettent à jour. Ce pas est **avancé, pas ajouté** : l'horloge saute ce
  réseau autant de fois qu'il a avancé de pas, de sorte qu'un réseau ne donne jamais plus d'eau, d'usure ni de compteur
  qu'au rythme des dix minutes. Fermer puis rouvrir donne l'eau tout de suite aux deux manœuvres.
- **D03 — Au-delà d'une heure d'avance, une manœuvre coupe sans donner d'eau.** Un réseau avance au plus six pas
  (`Clock.MAX_AHEAD`, une heure). Au-delà, une manœuvre ne fait pas de pas : les parties qu'une vanne fermée prive
  d'eau (`Network:behindClosed`) s'arrêtent aussitôt (arroseur éteint, sortie « fermée »), sans eau donnée ni usure ;
  ce qu'on rouvre reçoit l'eau quand l'horloge a rattrapé son avance. Ouvrir et fermer en boucle ne multiplie donc pas
  l'eau.
- **D04 — Couper la maison vide ses relais.** Quand une manœuvre de vanne prive d'eau une arrivée d'eau, les réservoirs
  relais de cette maison sont vidés aussitôt : les robinets s'arrêtent (l'eau restée dans les tuyaux est perdue). Une
  coupure par l'horloge (pompe éteinte, courant coupé) ne change pas : la maison garde l'eau de ses relais.

## Conséquences

- Horloge : une méthode de manœuvre et une marque « pas avancé » par réseau, non sauvegardée (au pire, après un
  rechargement, un pas d'horloge n'est pas sauté).
- Gestionnaire de sortie : point d'extension facultatif `cut(part)` (relais de l'arrivée d'eau).
- Traductions des onze langues et documentation joueur mises à jour.

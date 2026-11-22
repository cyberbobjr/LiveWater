# ADR-024 — Point d'eau sur un toit ; « Supprimer le raccord »

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-024-POINT-D-EAU-SUR-UN-TOIT-ET-RETRAIT-DU-RACCORD` |
| Date de création et de mise à jour | 2026-11-22 |
| Statut | Accepté (2026-11-22) |
| Avancement | Terminé le 2026-11-22 ; voir le [plan 024](../../ADR-plans/termines/plan-024-point-d-eau-sur-un-toit-et-retrait-du-raccord.md) |
| Décideur | l'utilisateur (« si on part sur A », « il faudrait aussi proposer "Supprimer le raccord" et gérer le cas où un joueur démonte ou déplace l'évier », « toit seul », 2026-11-22) |
| Portée | `batman_LiveWater` : zone d'une arrivée d'eau en mode bâtiment (`LWT_InletArea`), menu des points d'eau (`LWT_FixtureMenu`), nouvelle action « Supprimer le raccord », traductions (11 langues), tests, wiki, CHANGELOG |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D18, D21), [ADR-018](018-eau-des-le-raccordement.md) (eau dès le raccordement), [ADR-023](023-arrivee-d-eau-sans-limite-d-etages.md) ; analyse dans [ameliorations-et-idees.md](../../ameliorations-et-idees.md) (I11) |
| Références | Java 42.22 `ISWorldObjectContextMenuLogic.java:466-471, 1104-1120` (« Raccorder » proposé seulement dans une pièce, avec un réservoir au-dessus) ; `IsoGridSquare.java:8533` (`isInARoom`) ; `IsoObject.java:2425-2459` (recherche du réservoir, sans condition de pièce), `:4399, :4472` (envoi de l'état « source extérieure », vrai ou faux) ; vanilla `ISPlumbItem.lua` (aucune condition de pièce), `ISWorldObjectContextMenu.lua:1523` (`onPlumbItem`), `ISMoveableSpriteProps.lua:2491-2494` (un point d'eau reposé est à raccorder de nouveau) ; `LWT_Server.lua:215, 232` (relevé après pose ou retrait d'un point d'eau) |
| Origine | question d'un joueur du 2026-11-22, puis demande de l'utilisateur |

## Contexte

Le jeu ne propose « Raccorder » que pour un point d'eau situé dans une pièce. Sur un toit en terrasse, l'option
n'apparaît jamais, alors que tout le reste fonctionne sans pièce : l'action de raccordement, la recherche du réservoir
au-dessus, la lecture de l'eau. Par ailleurs le jeu n'a aucun moyen de défaire un raccord, sinon ramasser l'objet.

## Décisions

- **D01 — « Raccorder » sur un toit.** Quand le jeu ne propose pas « Raccorder » pour un point d'eau, LiveWater le
  propose si le point d'eau est **sur un toit** (D02) et qu'un réservoir se trouve au-dessus de lui (la condition du
  jeu ; le réservoir de LiveWater y est dès qu'une arrivée d'eau couvre la case, ADR-018). Même libellé, même icône,
  même clé à molette exigée, même action vanilla (`ISWorldObjectContextMenu.onPlumbItem`) : aucune copie de l'action.
  Jamais en double avec l'option du jeu.
- **D02 — « Sur un toit ».** Une case hors de toute pièce dont la case juste en dessous est dans une pièce (pièce de
  la carte ou pièce construite par le joueur, `isInARoom`). Le jardin et le sol nu ne sont pas concernés (« toit
  seul »).
- **D03 — Zone d'une arrivée d'eau posée sur un bâtiment de la carte.** Elle contient aussi les cases situées
  au-dessus d'une pièce du bâtiment, à tout niveau : le toit, et les étages que les joueurs ont construits par-dessus.
  La portée horizontale ne change pas. En base construite, la zone couvre déjà ces cases.
- **D04 — « Supprimer le raccord ».** Clic droit sur tout point d'eau raccordé, en intérieur comme sur un toit :
  clé à molette en main, même durée et même son que le raccordement. Le point d'eau revient à l'état « posé, à
  raccorder » : il ne donne plus d'eau, « Raccorder » réapparaît. L'action suit le modèle des autres actions de
  LiveWater : action temporisée côté client, puis commande vérifiée par l'autorité (point d'eau raccordé, portée, clé à
  tuyau), qui envoie l'état aux clients comme le fait le jeu. Le lave-linge perd sa marque LiveWater.
  (Précision du 2026-11-22 : la première rédaction disait « action temporisée partagée, terminée côté autorité » ; le
  modèle action cliente puis commande est celui du projet, ADR-001 E13, et donne le même contrôle par l'autorité.)
- **D05 — Réservoir après un retrait de raccord.** Il reste en place tant que le point d'eau est là (règle des points
  d'eau à raccorder, ADR-018) et n'est plus rempli (règle en place : seuls les réservoirs qui servent un point d'eau
  raccordé le sont).
- **D06 — Point d'eau démonté ou déplacé : rien de nouveau.** Le jeu efface le raccord d'un objet reposé ; LiveWater
  refait le relevé de l'arrivée d'eau à la pose et au retrait, retire le réservoir devenu inutile et en pose un
  au-dessus du nouvel emplacement. La règle porte sur tout objet au drapeau « point d'eau » (évier, baignoire, douche,
  toilettes, lave-linge, points d'eau d'autres mods). Ce chantier ajoute seulement les tests du cas « sur un toit ».

## Limites connues

- Un point d'eau d'origine d'une maison, raccordé puis dé-raccordé avant la coupure de l'eau de ville, ne retrouve pas
  l'eau de ville de lui-même : le jeu ne garde pas la trace de son origine. Il se comporte comme un point d'eau posé
  par le joueur.
- Un réservoir qui ne sert plus personne reste jusqu'au pas d'horloge suivant (10 minutes de jeu).
- Un point d'eau au dernier niveau de la carte ne peut pas recevoir de réservoir (ADR-023 D04).

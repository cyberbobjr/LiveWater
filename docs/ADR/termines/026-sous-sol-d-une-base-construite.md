# ADR-026 — Une base construite sert aussi son sous-sol

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-026-SOUS-SOL-D-UNE-BASE-CONSTRUITE` |
| Date de création et de mise à jour | 2026-11-24 |
| Statut | Accepté (2026-11-24) |
| Avancement | Terminé le 2026-11-24 ; voir le [plan 026](../../ADR-plans/termines/plan-026-sous-sol-d-une-base-construite.md) |
| Décideur | l'utilisateur (« option A servi à 2 niveaux pour l'instant (mais on changera peut être le niveau par la suite) », 2026-11-24) |
| Portée | `batman_LiveWater` : zone servie par une arrivée d'eau en mode base (`LWT_InletArea`), relevé des points d'eau (`LWT_GamePlumbing`), tests, wiki, spécifications, CHANGELOG, scénario en jeu |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D18 arrivée d'eau, L11 base du joueur), [ADR-018](018-eau-des-le-raccordement.md) (eau dès le raccordement), [ADR-023](023-arrivee-d-eau-sans-limite-d-etages.md) (D01 haut sans limite, D03 relevé borné par les chunks), [ADR-024](024-point-d-eau-sur-un-toit-et-retrait-du-raccord.md) (un point d'eau sous une pièce) |
| Références | `LWT_InletArea.lua` (`base` : `minZ = math.min(z, -BASEMENT_LEVELS)` ; `building` : `minZ = min(b.minLevel, z, -BASEMENT_LEVELS)`, `holds` : `fz < 0 and b:contains(fx, fy, 0)`, `BASEMENT_LEVELS = 2`) ; `LWT_GamePlumbing.lua` (`building` : un bâtiment `isUserDefined` compte comme une base ; `fixtures` parcourt du plus bas au plus haut niveau des chunks, `levels`) ; `LWT_RelayPlan.lua` (un relais un niveau au-dessus du point d'eau) ; Java 42.22 `IsoObject.java:2425-2445` (`FindExternalWaterSource` cherche au niveau `z + 1`), `ISWorldObjectContextMenuLogic.java:467, 470` (« Raccorder » seulement dans une pièce avec une source au-dessus), `IsoChunk.java:2866` (`getMinLevel`), `IsoGridSquare.java:8533` (`isInARoom`) |
| Origine | rapport d'un joueur du 2026-11-24 sur la page Workshop, avec le mod de sous-sol *Basement Building* (Workshop 3806513504) : l'arrivée d'eau donne l'eau « à tout ce qui est au même étage, mais pas au sous-sol que je viens de creuser » |

## Contexte

Les tuyaux restent sur un niveau ; l'arrivée d'eau porte l'eau aux autres. En mode bâtiment de la carte, la zone
descend déjà à deux niveaux de sous-sol sous l'emprise du rez-de-chaussée (ADR-001 P18, E19). En mode base — une base
construite par les joueurs, y compris un bâtiment `isUserDefined` du jeu — elle part du niveau de l'arrivée d'eau et
monte seulement (ADR-023 D01 : « depuis son niveau (base du joueur) »).

Un sous-sol creusé sous une base construite reste donc hors de la zone. Aucun relais n'est posé au-dessus de ses
points d'eau ; sans réservoir au-dessus, le jeu ne propose pas « Raccorder » (il exige une pièce et une source au
niveau `z + 1`) ; le diagnostic dit « Aucune arrivée d'eau ne le dessert » alors qu'une arrivée est à quelques cases.
Le joueur ne peut ni raccorder ni alimenter son évier de sous-sol, et l'option « eau de ville » du mod de sous-sol
s'arrête à la coupure de l'eau de ville.

Cette limite est la même que celle qu'ADR-023 a retirée vers le haut : elle n'a pas de raison de jeu. Elle est en
revanche bornée par le bas, pour que le relevé garde le coût des constructions réelles.

## Décisions

- **D01 — La zone d'une base construite descend à deux niveaux de sous-sol.** En mode base, l'arrivée d'eau sert les
  points d'eau de son cercle depuis le niveau `-2` jusqu'au dernier niveau de la carte. Cette décision remplace la
  partie « base du joueur » d'ADR-023 D01 ; le haut sans limite et le reste d'ADR-023 D02 ne changent pas, et ADR-023
  garde sa rédaction d'origine avec un renvoi daté vers cet ADR.
- **D02 — Une seule constante de profondeur.** La valeur est celle du mode bâtiment de la carte,
  `InletArea.BASEMENT_LEVELS` (2). La passer à 3 plus tard est un changement d'une ligne, plus les textes ; le chiffre
  n'est recopié nulle part.
- **D03 — Le relevé ne parcourt pas les niveaux vides.** Miroir d'ADR-023 D03 : l'adaptateur du jeu commence au plus
  bas niveau qui existe dans les chunks de la zone (`IsoChunk:getMinLevel`) et ne descend jamais sous le plancher de la
  règle pure. Une base de surface (`getMinLevel` = 0) ne coûte aucun niveau de plus ; un sous-sol creusé n'en coûte
  que ce qu'il occupe.
- **D04 — Rien d'autre ne change.** Portée horizontale, cercle de la base, garde-fou des points d'eau d'origine d'un
  bâtiment de la carte voisin, relais un niveau au-dessus du point d'eau (ici le rez-de-chaussée), absence de nouveau
  texte joueur : inchangés. Un point d'eau de sous-sol raccordé reçoit son eau comme un point d'eau d'étage.

## Limites connues

- **Deux niveaux seulement.** Un sous-sol creusé plus profond n'est pas servi au-delà de `-2`. La profondeur est
  décidée par l'utilisateur et pourra être relevée : voir D02.
- **Un sous-sol hors de l'emprise d'un bâtiment de la carte, arrivée en mode bâtiment.** Le mode bâtiment rattache le
  sous-sol à l'emprise du rez-de-chaussée du bâtiment de la carte ; un sous-sol creusé sous une extension construite
  par les joueurs, hors de cette emprise, n'est pas servi. Couvrir ce cas demanderait de servir la colonne de toute
  case servie : hors périmètre (analyse dans [ameliorations-et-idees.md](../../ameliorations-et-idees.md)).
- **Un sous-sol qui n'est pas une pièce.** Le jeu ne propose « Raccorder » que dans une pièce (`isInARoom`) : un trou
  creusé sans pièce enregistrée reste non raccordable, comme le jardin (ADR-024). Les mods de sous-sol qui
  enregistrent une vraie pièce, tel *Basement Building*, ne sont pas concernés.

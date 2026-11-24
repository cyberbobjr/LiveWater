# ADR-027 — Arrosage : remplir la plante jusqu'à sa capacité

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-027-ARROSAGE-JUSQU-A-LA-CAPACITE` |
| Date de création et de mise à jour | 2026-11-24 |
| Statut | Accepté (2026-11-24) |
| Avancement | Terminé le 2026-11-24 ; voir le [plan 027](../../ADR-plans/termines/plan-027-arrosage-jusqu-a-la-capacite.md) |
| Décideur | l'utilisateur (« go pour l'ADR », 2026-11-24, après l'analyse du rapport du joueur) |
| Portée | `batman_LiveWater` : service des plantes (`LWT_Plants`), adaptateur de l'agriculture (`LWT_GameFarming`), tests, wiki EN/FR, page Workshop (11 langues), spécifications, CHANGELOG, scénario en jeu ; aucune modification de `batman_LiveWire` |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D09 besoin des sorties, D19 arrosage), [ADR-003](003-zone-arrosee-lisible.md) (zone arrosée), [ADR-004](004-goutte-a-goutte.md) (doses, perte en l'air), [ADR-006](006-vision-debit.md) (D01 débit prélevé), [plan 001](../../ADR-plans/termines/plan-001-reseau-eau-ouvert.md) (E11, choix remplacé) |
| Références | vanilla 42.22 : `SPlantGlobalObject.lua:501-514` (une dose ajoute 10, plafond 100), `farming_vegetableconf.lua:130-146,272-273,313,327` (`waterNeeded` du stade, `waterNeededMax`), `farming_vegetableconf_vegetables.lua:38,62` (seuil 70), `ISFarmingMenu.lua:324,357` (l'arrosoir arrose tant que `waterLvl < 100`), `ISFarmingInfo.lua:304-329,343-346` (barre sur 100, « Fine » au-dessus de 60) ; mod : `LWT_Plants.lua:30-44,68-80`, `LWT_GameFarming.lua:21-32`, `LWT_CapSpray.lua` (dose, perte, débit) |
| Origine | rapport d'un joueur du 2026-11-24 : « my sprinklers don't water my plants above a certain level […] they quickly water to 70/100, then stop until the plant reaches 69/100. From there they water to 79/100 » |

## Contexte

Un arroseur ouvert complète aujourd'hui les plantes jusqu'au **besoin de leur stade**, pas jusqu'à leur capacité : une
plante reçoit `ceil((waterNeeded - waterLvl) / 10)` doses, donc s'arrête dès que `waterLvl >= waterNeeded`. Pour la
plupart des cultures, ce seuil vaut 70 (`farming_vegetableconf_vegetables.lua:38,62`) et une dose vaut 10 points
(`SPlantGlobalObject.lua:501-514`). Une plante à 70 ne reçoit plus rien ; à 69 elle reçoit `ceil(1/10) = 1` dose et
monte à 79, puis s'arrête de nouveau. Le joueur voit donc exactement 70 → 69 → 79 sur 100, et croit à une panne.

Ce comportement vient de l'étape E11 (`535dd7c`, 2026-11-18), où il figure sous « choix faits sans l'utilisateur »
(`plan-001-reseau-eau-ouvert.md:345-351`). Il était cohérent avec le modèle d'alors, « pas de besoin → au repos »
(ADR-001 D09) : une sortie ne prélevait que les doses qu'elle utilisait, et remplir à 100 aurait fait tourner la pompe,
usé la pompe, fait du bruit et consommé de l'eau **sans aucun gain de croissance**, puisque vanilla fait pousser la
plante dès que `waterLvl >= waterNeeded` (`farming_vegetableconf.lua:130-146`).

Ce raisonnement a été invalidé par ADR-006 D01, accepté le 2026-11-18 : un arroseur ouvert prélève désormais son débit
**que les plantes aient soif ou non**, et l'excédent est perdu. Depuis, le mod prélève les 10 L, en perd 2,5 L en l'air,
et ne donne au mieux qu'une dose de temps en temps : l'économie d'eau qui justifiait la cible à 70 n'existe plus. La
cible n'a jamais été revue.

Le mot « besoin » a deux sens dans vanilla, et E11 a pris le premier :
- le sens **croissance** : `waterNeeded`, le seuil qui fait pousser (`calcWater`) ;
- le sens **action du joueur** : `waterLvl < 100`, que le menu utilise pour l'arrosoir (`ISFarmingMenu.lua:324,357`).

Un joueur qui arrose à la main remplit donc jusqu'à 100 ; un arroseur du mod s'arrête à 70-79. La barre d'agriculture
est graduée sur 100 (`ISFarmingInfo.lua:343-346`), et une plante n'est « Well watered » qu'au-dessus de 80
(`ISFarmingInfo.lua:304-329`). La phrase du wiki et de la page Workshop « fermez l'arroseur une fois le potager arrosé »
n'est jamais vraie avec la règle actuelle.

## Décisions

- **D01 — La cible d'arrosage est la capacité de la plante.** Une plante vivante et semée reçoit des doses tant que son
  niveau d'eau est inférieur à sa capacité : `min(100, max(waterNeeded, waterNeededMax))` quand `waterNeededMax` est
  déclaré et positif, sinon **100**. Les doses restent celles de vanilla : `ceil((capacité - waterLvl) / 10)`, 10 points
  par dose, plafond 100 ; une plante à 100 ne reçoit rien. Cette décision remplace la cible d'arrosage d'ADR-001 D19 et
  le choix d'E11 (`waterLvl < waterNeeded`, `ceil((waterNeeded - waterLvl) / 10)` doses) ; ADR-001 garde sa rédaction
  d'origine avec un renvoi daté vers cet ADR.
- **D02 — La même règle pour l'arroseur et la ligne de goutte-à-goutte.** Les deux passent par le même service
  (`LWT_Plants`) : la zone (ADR-003), la dose de 200 ml, la perte en l'air (un quart pour l'arroseur, rien pour la
  ligne) et le débit (ADR-006) ne changent pas. Les plantes les plus proches restent servies d'abord, et une eau trop
  courte ne donne que des doses entières.
- **D03 — Pas de nouvelle option, pas de nouveau texte, pas de révision d'API.** La règle suit celle de l'arrosoir du
  jeu ; les options `SprinklerFlow` et `DripFlow` continuent de borner le prélèvement. Le port interne `farming` de
  `LWT_GameFarming` expose en plus la capacité de la plante (`waterNeededMax`) ; l'API publique n'est pas touchée et
  aucun message réseau n'est ajouté.
- **D04 — Ce qui ne change pas.** Un arroseur ouvert prélève toujours son débit et montre son jet et son bruit même
  quand toutes les plantes sont à 100 (ADR-006 D01) ; l'eau non utilisée est perdue ; l'état « en marche » signifie
  toujours « de l'eau est sortie au dernier pas ». La minuterie de l'arroseur automatique, son courant et les valeurs
  sandbox restent inchangés.

## Conséquences

- **Aucun prélèvement supplémentaire.** Le débit est déjà prélevé à chaque pas : l'eau qui arrivait aux plantes sans
  être donnée est désormais utilisée au lieu d'être perdue. Le joueur ferme la vanne quand la barre est à 100, comme le
  dit déjà le wiki.
- **Arroseur automatique.** Une ouverture de 30 minutes (3 pas) fait arriver 22,5 L, soit 112 doses : un carré de 5 × 5
  à 70 demande 75 doses (15 L) et atteint 100 en un cycle ; un potager à 0 en demande 250 (50 L) et lui prend deux à
  trois cycles. La minuterie ne change pas.
- **Ligne de goutte-à-goutte.** 0,5 L par case et par pas, sans perte, soit deux doses par case voisine et par pas :
  remplir prend plus de pas, sans prélèvement supplémentaire.
- **Pas de sur-arrosage en 42.22.** Aucune culture ni herbe du jeu ne déclare `waterLvlMax` (toutes les lignes sont
  commentées dans `farming_vegetableconf_vegetables.lua` et `farming_vegetableconf_herbs.lua`) : remplir à 100 n'ajoute
  aucun retard de croissance, et l'arrosoir vanilla le permet déjà. Une culture de mod qui déclare `waterLvlMax` vise ce
  maximum ; la dose vanilla de 10 points peut le dépasser de moins de 10 points, comme à l'arrosoir du jeu.
- **Ce que voit le joueur.** La barre monte à 100/100, la plante passe « Well watered », la phrase « une fois le potager
  arrosé » devient vraie, et le 70 → 69 → 79 du rapport disparaît.
- **Données et API.** Aucune donnée sauvegardée nouvelle, aucune migration, aucune révision d'API publique ; le port
  `farming` gagne un champ, interne au serveur.
- **Documents à aligner (plan 027).** `specifications-fonctionnelles.md` (F21, F33), `specifications-techniques.md`
  (service des plantes), wiki EN/FR (section arroseurs), `README.steam` et ses 10 traductions (une phrase), `CHANGELOG`,
  et le renvoi daté dans ADR-001 D19.
- **Tests.** La règle pure gagne une table de cas (capacité absente, capacité déclarée, plante à 95, plante à 100) ;
  les attentes de `test_sprinkler.py` (`45/70` → 6 doses → 100), `test_drip.py` et `test_away.py` sont rebasées en le
  justifiant (changement de règle décidé ici, pas une régression).

## Limites connues

- **Plafond 100.** Une culture qui déclarerait `waterNeeded` au-dessus de 100 resterait insatisfaite : le jeu plafonne
  `waterLvl` à 100, le mod ne peut pas aller plus loin.
- **L'eau perdue reste perdue.** Tant que la vanne est ouverte, un potager déjà à 100 continue de coûter son débit
  (7,5 L perdus par pas pour un arroseur) ; c'est le comportement d'ADR-006 D01, pas une régression.
- **La capacité n'est pas affichée.** L'« Information » d'un arroseur donne le débit, pas la cible ; le joueur lit la
  barre d'agriculture. Aucun texte nouveau.
- **Granularité de la dose.** La cible est un seuil, pas une valeur atteinte au point près : une dose vaut 10 points,
  donc une plante à 80 avec une capacité de 85 monte à 90. C'est la granularité de l'arrosoir vanilla ; remplir à 100
  ne dépasse jamais 100 (plafond du jeu).
- **Cultures de mods.** Une capacité déclarée aberrante (zéro, inférieure au besoin, au-dessus de 100) est ramenée dans
  les bornes ; le mod ne devine pas l'intention de l'auteur de la culture.

## Hors périmètre

- Changer la durée ou le débit de l'arroseur automatique, ou les valeurs sandbox.
- Une option sandbox pour choisir la cible d'arrosage.
- Une règle de qualité d'eau à l'arrosage : toute eau convient (ADR-005).
- Le sur-arrosage des cultures de mods au-delà de leur `waterNeededMax` déclaré.

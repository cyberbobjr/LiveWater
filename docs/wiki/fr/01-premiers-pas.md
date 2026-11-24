# Premiers pas

Un réseau LiveWater a toujours la même forme : un **producteur**, une **pompe à eau** posée au bord d'une eau naturelle
(lac, étang, rivière, puits) ou contre un baril ; des **tuyaux** posés au sol ; et des **sorties** au bout (une arrivée
d'eau de maison, des arroseurs, des lignes de goutte-à-goutte, et les **raccords de remplissage** qui remplissent un
baril, un récupérateur d'eau de pluie ou une mangeoire). Seule une pompe met de l'eau dans le réseau. L'eau avance
toutes les 10 minutes de jeu.

![Les tuiles provisoires de LiveWater](../../images/art/planche-tuiles-provisoires.png)

Chaque action d'un menu de LiveWater vous fait marcher jusqu'à la pièce et dure quelques secondes, comme les actions
du jeu.

## 1. Couper des tuyaux d'eau

Un tuyau d'eau couvre une case. Recette **Couper des sections de tuyau** : 1 tuyau en métal, avec une scie à
métaux (gardée), donne **4 tuyaux d'eau**.

> Capture à faire : la recette « Couper des sections de tuyau » dans la fenêtre d'artisanat.

## 2. Fabriquer la pompe à eau

Recette **Fabriquer une pompe à eau** (Électricité 2) : 1 tuyau en métal, 2 petites plaques en métal, 3 pièces
électroniques, 2 fils électriques, 4 vis, avec un tournevis et une clé à molette (gardés). Elle donne une pompe à eau
(15 kg) et 15 XP d'Électricité.

Posez-la comme un meuble (clic droit dans l'inventaire, Placer) **juste au bord d'une eau naturelle** : lac, étang,
rivière, ou contre un puits (voir [Puits](#12-puits)) ; ou **contre un baril** ou **une pompe de station-service** (voir ci-dessous). Ailleurs, le curseur
passe au rouge : *Doit être posée au bord d'une eau naturelle (lac, étang, rivière), contre un puits, un baril ou une pompe de station-service.*

**Contre un baril.** La pompe peut aussi se poser contre un baril, sur l'un de ses quatre côtés : un baril ou un
récupérateur d'eau de pluie d'au moins 20 L, un refroidisseur d'eau, un conteneur listé dans les options sandbox, ou un
mangeoire. Elle pompe alors l'eau du baril dans les tuyaux, jusqu'à son débit (50 L toutes les 10 minutes). Elle ne
pompe que de l'eau, jamais de carburant, et l'eau garde sa qualité : une eau souillée passe, et la maison demande le
filtre de son arrivée d'eau. Un baril vide ne donne rien.

Deux pompes d'un même liquide sur un même réseau additionnent leurs débits (100 L toutes les 10 minutes pour deux), et chacune ne puise
que sa propre source : une pompe au bord d'un étang ne vide jamais le baril d'une pompe posée contre un baril. Une pompe
qui touche à la fois un baril et un étang vide d'abord le baril, puis prend l'étang.

**Contre une pompe de station-service.** La pompe peut aussi se poser contre une pompe à essence de station-service (les pompes vanilla Fossoil et Gas-2-Go). Elle pompe alors l'essence de la station dans les tuyaux, jusqu'à son débit (50 L toutes les 10 minutes), avec du courant comme toujours ; le carburant stocké de la station diminue. Une station vide ne donne rien.

**Un seul liquide par réseau.** Un réseau transporte un seul liquide à la fois : la première pompe posée impose le liquide (eau propre ou souillée, ou essence). Une pompe d'un autre liquide ne donne rien, et son information dit *Pompe : un autre liquide est dans les tuyaux*. Pour avoir les deux, faites deux réseaux, ou fermez une vanne entre les pompes : chaque côté a sa propre première pompe.

Les consommateurs ne prennent que ce qu'ils acceptent. L'arrivée d'eau de la maison, les arroseurs et les lignes de goutte-à-goutte ne prennent que de l'eau : avec de l'essence dans les tuyaux, ils ne prennent rien et disent *Ce n'est pas de l'eau*. Le raccord de remplissage ne mélange jamais : il remplit un récipient vide avec ce que transportent les tuyaux, un récipient d'eau avec de l'eau seulement, un récipient d'essence avec de l'essence seulement. Il ne remplit jamais une mangeoire avec autre chose que de l'eau, ni une pompe de station-service.

La pompe a besoin de **courant** : un générateur ou le réseau public sur sa case, ou LiveWire (voir
[LiveWire](04-livewire.md)). Elle donne **50 L toutes les 10 minutes** tant qu'une sortie a besoin d'eau, et s'arrête
seule sinon. Une pompe allumée et alimentée ronronne, même sans demande d'eau ; ce bruit n'attire les zombies que lorsqu'elle pompe.

Son menu au clic droit :

- **Allumer la pompe** / **Éteindre la pompe** : l'interrupteur, en plus de l'arrêt automatique.
- **Informations** : un écran LCD rétroéclairé : état (en marche, en attente, éteinte, sans courant, en panne), débit
  possible, débit des 10 dernières minutes, total pompé depuis la pose, rendement, source. Quand un baril est posé
  contre elle, une ligne **Baril : N L** indique les litres qu'il contient. L'écran se met à jour pendant qu'il est ouvert.
- **Réparer la pompe** : voir plus bas.

**Usure.** Son rendement baisse quand elle tourne (environ une semaine de marche de 100 % à 0 % avec les réglages par
défaut), et le débit suit. Sous 20 %, elle peut tomber en panne ; à 0 %, elle s'arrête. Éteignez-la, puis réparez-la
avec **2 ferrailles** et une **clé à molette** : rendement remis à 100 %.

Une pompe a 4 départs : jusqu'à 4 tuyaux peuvent en partir. Sa pression suffit pour **une maison et quatre arroseurs**
(une arrivée d'eau compte 2, un arroseur ou un raccord de remplissage compte 1, toutes les lignes de goutte-à-goutte du
réseau comptent 1 ensemble).

**Pendant votre absence.** Votre réseau d'eau continue de tourner quand vous vous éloignez : la pompe puise toujours
dans sa mare, son puits ou son baril, les arroseurs ouverts et les lignes de goutte-à-goutte arrosent toujours les
cultures, et les barils remplis par un raccord de remplissage continuent de se remplir (vous retrouvez la bonne
quantité au retour). L'arrivée d'eau de la maison attend votre retour. Le courant pendant l'absence : avec LiveWire, le
réseau qui alimente la case de la pompe ; sinon le réseau public jusqu'au jour de sa coupure, et un groupe électrogène
compte comme au moment de votre départ (il ne brûle rien entre-temps et reprend sa consommation à votre retour).

![Une pompe à eau en marche au bord d'une rivière, sur son groupe électrogène](../../images/screenshots/pump-running.jpg)

![L'écran LCD d'une pompe en marche](../../images/screenshots/pump-info-fr.jpg)

## 3. Poser les tuyaux

Un tuyau d'eau se pose comme toutes les autres pièces : clic droit dessus dans l'inventaire, **Placer**, puis
posez-le avec le curseur de meuble. Un tuyau par case. Les tuyaux se raccordent à leurs voisins et prennent seuls leur forme (droit, coude, T, croix).
Les tuyaux restent sur un seul niveau : l'arrivée d'eau porte l'eau aux étages et au sous-sol.

Les tuyaux passent sous les clôtures et les portails (un manchon sombre le montre), mais pas à travers un mur plein ni
une porte. Pour faire entrer l'eau dans un bâtiment, utilisez l'arrivée d'eau de la maison.

Un tuyau posé contre le flanc d'un compteur d'eau ou d'une vanne en ligne ne s'y raccorde pas : ces pièces n'ont que
deux côtés, sur l'axe où elles ont été posées.

**Vue du réseau.** Clic droit sur une pièce : **Afficher le réseau d'eau** colore tout le réseau (tuyaux et pompes en
bleu, sorties selon leur état, et les appareils de la maison qu'elles alimentent ; voir [Diagnostic](03-diagnostic.md)).
**Masquer le réseau d'eau** l'éteint ; les deux options ne s'affichent jamais ensemble.

Pour reprendre un tuyau, ramassez-le comme les autres pièces, avec une **clé**. Le tuyau vous est rendu.

![Une ligne de tuyaux de la pompe à une maison, avec un compteur d'eau et une vanne](../../images/screenshots/pipe-line.jpg)

## 4. Vannes

**Vanne d'arrêt.** Recette **Fabriquer une vanne d'arrêt** : 1 tuyau d'eau, 1 ferraille, avec une clé anglaise
(gardée). Posez-la au curseur de meuble sur une case vide entre deux tuyaux d'une ligne droite (elle prend la place
d'un tuyau : ramassez d'abord ce tuyau) ; elle se tourne seule dans le sens du tuyau. Elle se pose
ouverte. Clic droit dessus : **Fermer la vanne** coupe l'eau de tout ce qui est après elle (la maison, les arroseurs
plus loin), **Ouvrir la vanne** la laisse repasser ; son volant montre l'état, et **Informations** le dit aussi.
L'effet est immédiat, pour cette vanne comme pour celle d'un arroseur : l'eau s'arrête ou repart tout de suite, et les
robinets d'une maison coupée se vident (l'eau restée dans les tuyaux est perdue). Elle se ramasse à la clé comme les
autres pièces.

Chaque arroseur a aussi sa vanne (**Ouvrir la vanne** / **Fermer la vanne**). Une vanne fermée ne laisse passer aucune
eau, et le diagnostic le dit (*une vanne est fermée*). Les arroseurs se posent fermés.

La vanne en ligne garde son axe quand on l'ouvre ou la ferme. Ouvrir ou fermer une vanne, en ligne ou d'arroseur, fait
un bruit de vanne, entendu des joueurs proches.

## 5. Arrivée d'eau de la maison

Recette **Fabriquer une arrivée d'eau de maison** : 2 tuyaux d'eau, 1 petite plaque en métal, 4 vis, avec une clé
anglaise (gardée).

Posez-la **contre le mur extérieur** d'un bâtiment de la carte, et amenez-y un tuyau depuis la pompe. Elle alimente les
**éviers, baignoires, douches, toilettes et lave-linge** de ce bâtiment que vous avez raccordés à la clé anglaise
(l'action « Raccorder » du jeu), dans un rayon de **20 cases** (option sandbox), à **tous les étages au-dessus** et
**2 niveaux de sous-sol** en dessous.

La **clé anglaise** peut rester dans le sac : le jeu l'équipe lui-même. Elle doit être **en état** — une clé cassée ne
compte plus, et une simple clé à molette ne convient pas.

Son voyant dit ce qu'elle fait :

- **vert** : eau propre, la maison la reçoit (une cartouche en état dans l'arrivée d'eau, ou de l'eau de puits) ;
- **ambre** : l'eau n'est **pas filtrée**, la maison n'en reçoit **pas** (montez un filtre dans l'arrivée d'eau,
  remplacez une cartouche usée, ou pompez dans un puits).

Un point d'eau déjà alimenté par autre chose (une pompe de LiveWire) est laissé tel quel.

**Sur un toit :** le jeu ne propose **Raccorder** que dans une pièce. LiveWater propose la même option pour un point
d'eau posé sur un toit (en plein air, juste au-dessus d'une pièce) dès qu'une arrivée d'eau l'atteint. L'arrivée d'eau
d'un bâtiment de la carte sert aussi les étages que vous avez construits par-dessus. Un point d'eau dans le jardin,
sans pièce en dessous, ne peut pas être raccordé.

![Une cuisine d'été sur un toit en terrasse : plans de travail, évier raccordé, barbecues, table](../../images/screenshots/rooftop-kitchen.jpg)

**Supprimer le raccord :** clic droit sur un point d'eau raccordé, une clé anglaise dans le sac, puis **Supprimer le
raccord**. Le point d'eau ne donne plus d'eau et peut être raccordé de nouveau. Ramasser ou démonter un point d'eau
supprime aussi son raccord : raccordez-le de nouveau là où vous le reposez.

Un évier, une douche, une baignoire, des toilettes ou un lave-linge alimenté par l'arrivée d'eau affiche dans son menu
clic droit l'eau qu'il contient, par exemple une ligne grisée **Eau : 18 L / 25 L**.

![L'arrivée d'eau contre le mur, voyant vert, alimentée par un compteur d'eau](../../images/screenshots/inlet-filtered.jpg)

## 6. Cartouche filtrante

L'eau d'un étang ou d'une rivière n'est pas propre. Recette **Fabriquer une cartouche filtrante** : 2 charbons de bois
et 2 tissus déchirés donnent une **cartouche filtrante**. Elle nettoie environ **500 L** ; son état montre ce qui reste.

Le filtre se monte dans l'**arrivée d'eau de la maison** : clic droit dessus, **Monter la cartouche filtrante**,
**Remplacer la cartouche filtrante** ou **Retirer la cartouche filtrante**. Une cartouche retirée garde son usure. Une
cartouche usée revient sous le nom de **cartouche filtrante usée** : rechargez-la avec 2 charbons de bois et 1 tissu déchiré (recette **Recharger une cartouche filtrante**), ou démontez-la pour son tissu. L'arrivée d'eau montre le boîtier du filtre sous son coffret. Il ne nettoie que l'eau qui
entre dans la maison : arroseurs, lignes de goutte-à-goutte et raccords de remplissage prennent l'eau du réseau telle
quelle et n'usent jamais la cartouche.

## 7. Arroseurs

**Arroseur manuel.** Recette **Fabriquer un arroseur** : 2 tuyaux d'eau, 1 ferraille, 1 planche, avec une clé
anglaise (gardée). Posez-le comme un meuble et alimentez-le par un tuyau. Clic droit : **Ouvrir la vanne**. Sa manette se lit d'un coup d'œil : le long du tuyau quand
elle est ouverte, en travers quand elle est fermée. Tant que
sa vanne est ouverte, il arrose **10 L toutes les 10 minutes**, que les plantes aient soif ou non. Les plantes vivantes
qui ont besoin d'eau dans le **carré de 5 × 5 cases** autour de lui (2 cases de chaque côté ; l'option sandbox change
cette portée) en prennent des doses de 200 ml, les plus proches d'abord ; le reste est perdu. Toute eau convient,
propre ou non. Fermez-le une fois le potager arrosé : resté ouvert, il vide votre baril ou fait tourner votre pompe.

Pour voir les cases arrosées, faites un clic droit sur un arroseur ou une ligne de goutte-à-goutte : **Afficher toutes
les zones arrosées** éclaire en bleu le sol de chaque case arrosée par les arroseurs et les lignes à moins de 25 cases de
vous ; **Masquer la zone arrosée** l'éteint ; une seule des deux options est proposée à la fois. Leur **Information** donne leur débit : combien de litres elles prennent
toutes les 10 minutes (et, pour un arroseur, combien arrivent aux plantes).

Un arroseur qui arrose montre un jet d'eau animé qui fait tout le tour (option du mod *Jet des arroseurs animé* :
décochez-la pour un jet fixe sur un ordinateur lent). Un quart de son eau se perd en l'air : sur 10 L, 7,5 L peuvent
aller aux plantes. Une pompe à eau (50 L toutes les 10 minutes) alimente au plus cinq arroseurs ouverts à plein
débit ; les suivants reçoivent le reste, puis rien. Il n'est pas discret non plus : on l'entend arroser, et **les
zombies l'entendent** toutes les 10 minutes tant qu'il arrose. Pour un potager silencieux et économe en eau, prenez des
[lignes de goutte-à-goutte](#8-lignes-de-goutte-à-goutte).

**Arroseur automatique.** Recette **Ajouter une minuterie à un arroseur** (Électricité 2) : 1 arroseur, 2 pièces
électroniques, 1 fil électrique, avec un tournevis (gardé) ; 10 XP d'Électricité. Il s'ouvre seul **toutes les
6 heures** et arrose pendant **30 minutes** (10 L toutes les 10 minutes), puis se referme. Changez l'intervalle au clic droit, **Minuterie d'arrosage**, de 1 à
24 heures (bornes dans les options sandbox). La minuterie a besoin d'un peu de courant (5 W : générateur, réseau public
ou LiveWire) ; sans courant elle ne fait rien, mais vous pouvez toujours ouvrir la vanne à la main. Un voyant vert de la minuterie s'allume pendant l'arrosage.

![Un arroseur qui arrose, jet visible (arroseur manuel ; l'automatique arrose de la même façon)](../../images/screenshots/sprinkler-jet.jpg)

## 8. Lignes de goutte-à-goutte

Une ligne de goutte-à-goutte est un fin tuyau brun posé au sol entre vos rangs. Elle arrose les plantes juste à côté
d'elle, sans bruit et sans gaspiller d'eau.

**La fabriquer.** Recette **Fabriquer des lignes de goutte-à-goutte** (Agriculture) : 1 tuyau en caoutchouc et
2 utilisations de ruban adhésif, avec un couteau tranchant (gardé), donnent **4 lignes de goutte-à-goutte**. Une ligne
couvre une case.

**La poser** comme un tuyau : clic droit dessus dans l'inventaire, **Placer**, une par case. Les lignes se raccordent
entre elles et aux tuyaux d'eau et changent de forme toutes seules. On la ramasse à la main, sans outil.

**Ce qu'elle arrose.** Toutes les 10 minutes, chaque case de la ligne prend **0,5 L** au réseau et arrose les cases
voisines qui ne font pas partie de la ligne, par doses de 200 ml. Une ligne droite arrose les cases des deux côtés ; la
case sous le tuyau n'est pas arrosée. Posez donc la ligne dans une allée entre deux rangs de cultures. Rien ne se perd
en l'air ; ce dont les plantes n'ont pas besoin s'infiltre dans le sol. Elle goutte dès que le réseau lui donne de
l'eau : une [vanne](#4-vannes) placée avant elle l'arrête. Une ligne au bout d'un réseau à court de
pression reste à sec.

**Ce qu'il lui faut.**

- **N'importe quelle eau.** Propre ou non, sans filtre. L'essence et tout autre fluide sont refusés.
- **Peu de pression.** Toutes les lignes d'un réseau comptent **1** ensemble, quel que soit leur nombre.
- **Une pompe.** Comme toute sortie, une ligne de goutte-à-goutte ne reçoit de l'eau que d'une [pompe à eau](#2-fabriquer-la-pompe-à-eau)
  de son réseau. Un réseau sans pompe ne lui donne rien.

Une ligne de goutte-à-goutte ne fait aucun bruit.

## 9. Raccord de remplissage

Recette **Fabriquer un raccord de remplissage** : 1 tuyau d'eau, 1 tuyau en caoutchouc, avec une clé anglaise (gardée).
Posez-le entre le bout d'un tuyau et un baril, un récupérateur d'eau de pluie, un refroidisseur d'eau ou une mangeoire, ou
au milieu d'une ligne de tuyaux : il laisse alors passer l'eau d'un tuyau à l'autre. Son dessin suit les tuyaux voisins
(droit, coudé, en té ou en croix) ; le contenant, quand il y en a un, reste derrière lui. Clic droit dessus :
**Informations** montre ce qu'il fait.

Le raccord de remplissage ne fait que **remplir**. Le réseau remplit le contenant posé à côté, jusqu'à 50 L toutes les
10 minutes, sans jamais dépasser sa contenance. L'eau y entre **souillée**, même depuis un puits : les tuyaux transportent
de l'eau non traitée, seule l'arrivée d'eau de la maison donne de l'eau propre. Les animaux peuvent la boire (vérifié
dans le code du jeu, pas encore testé en jeu).

Une mangeoire qui contient de la nourriture n'a pas de réservoir d'eau (une règle du jeu) : le raccord ne lui donne rien, et
ses informations disent *La mangeoire contient de la nourriture*. Le remplissage reprend une fois la nourriture finie. Une
longue mangeoire (2 à 4 cases) reçoit son eau dans son réservoir, et le raccord peut se poser contre n'importe laquelle de
ses cases.

Le raccord ne donne de l'eau au réseau que si une pompe l'y met : un raccord de remplissage ne fait jamais sortir l'eau
d'un contenant. Pour envoyer l'eau d'un baril dans les tuyaux, posez une [pompe à eau](#2-fabriquer-la-pompe-à-eau) contre lui.

Ses informations disent ce qu'il fait : remplir le baril, baril plein (ou absent), aucun baril à côté, un autre fluide
dans le baril, ou *La mangeoire contient de la nourriture*.

![Deux raccords sur des récupérateurs d'eau vanilla : un tonneau rond entre deux tuyaux (té) et une caisse au croisement de trois tuyaux (croix)](../../images/screenshots/barrel-fittings.jpg)

## 10. Réseau public

Tant que l'eau de la ville coule, clic droit sur un évier, une baignoire, une douche, des toilettes ou un lave-linge
**que vous avez posé** dans une pièce d'un bâtiment de la carte : **Raccorder au réseau public**. Il se comporte alors
comme un point d'eau d'origine : eau illimitée jusqu'à la coupure de l'eau de la ville.

## 11. Compteur d'eau

Recette **Fabriquer un compteur d'eau** : 1 tuyau d'eau, 1 petite plaque en métal, 2 vis, avec un tournevis
(gardé). Posez-le en ligne sur un tuyau ; il suit le sens du tuyau et ne se raccorde qu'à ses deux côtés, sur cet axe.

**Informations** ouvre une fenêtre de compteur d'eau, à la manière d'un compteur américain : un totalisateur à rouleaux
(les litres passés depuis la pose), une aiguille de balayage (un tour toutes les 10 litres), les litres des 10 dernières
minutes et la qualité de l'eau (propre ou non filtrée). Le total est gardé quand on ramasse le compteur et qu'on
le repose ; il n'y a pas de remise à zéro.

![La fenêtre du compteur d'eau : rouleaux, aiguille, total et dernières minutes](../../images/screenshots/meter-window-fr.jpg)

## 12. Puits

La même pompe à eau posée contre un **puits** tire de l'**eau propre** : la maison la reçoit sans filtre. Ses
informations disent *Source : puits (eau propre)*.

Deux objets du jeu comptent comme un puits : le **puits en pierre** et la **pompe à bras en métal**.

> Capture à faire : une pompe à eau contre un puits.

## 13. Démonter une pièce

Chaque pièce LiveWater se démonte dans l'inventaire, par une recette **Démonter ...** (fenêtre d'artisanat,
Assemblage ou Électricité) : une clé à tuyau ou une clé pour les pièces de plomberie (tuyau, vanne, compteur, arrivée
d'eau, arroseur, raccord de remplissage), un tournevis pour la pompe à eau et l'arroseur automatique, un couteau pour une
ligne de goutte-à-goutte ou une cartouche filtrante. On ne récupère jamais plus que ce que la pièce a coûté, et
seulement des débris : morceaux de fer, ferraille, vis, ferraille électronique, fil. Une cartouche filtrante, neuve ou usée, rend un
morceau de tissu, une ligne de goutte-à-goutte un élastique.

Une pièce posée se démonte aussi sur place, par le menu **Démonter** du jeu et avec le même outil (l'Entretien augmente
vos chances pour les pièces de plomberie, l'Électricité pour la pompe et l'arroseur automatique). Elle quitte le réseau
comme si vous l'aviez ramassée. Une ligne de goutte-à-goutte se ramasse à la main, puis se démonte dans l'inventaire.

### Expérience

Les pièces en métal font progresser le **Travail des métaux**, la pompe et l'arroseur automatique l'**Électricité** :

| Recette | Fabrication | Démontage |
|---|---|---|
| Découper des tuyaux, vanne d'arrêt, raccord de remplissage | 5 Travail des métaux | 2 Travail des métaux |
| Compteur d'eau, arroseur | 8 Travail des métaux | 2 Travail des métaux |
| Arrivée d'eau de la maison | 10 Travail des métaux | 2 Travail des métaux |
| Pompe à eau | 15 Électricité | 5 Électricité |
| Arroseur automatique | 10 Électricité | 3 Électricité |
| Cartouche filtrante, goutte-à-goutte | aucune | aucune |

## 14. Trouver des pièces

Certaines pièces se trouvent au lieu de se fabriquer, rarement : tuyaux d'eau, vannes d'arrêt et raccords de remplissage
dans les fournitures de plomberie et les caisses à outils ; arroseurs, lignes de goutte-à-goutte et cartouches
filtrantes dans les jardineries et le matériel agricole. La pompe à eau, l'arrivée d'eau, le compteur et l'arroseur
automatique ne se trouvent jamais : on les fabrique.

Suite : [Base du joueur](02-base-du-joueur.md) · [Diagnostic](03-diagnostic.md)

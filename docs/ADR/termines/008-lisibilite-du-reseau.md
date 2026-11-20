# ADR-008 — Lisibilité du réseau : raccord coudé, noms, compteur, pompe, appareils de la maison

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-008-LISIBILITE-DU-RESEAU` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 008](../../ADR-plans/termines/plan-008-lisibilite-du-reseau.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : tuiles du raccord de baril (`source/tiles/`, `.pack`, `.tiles`, profondeur), choix des sprites (`LWT_Sprites`, `LWT_Parts`), traductions, compteur et pompe (capacités, fenêtres client), menus du client (vue du réseau, zone arrosée, appareils de la maison), commande `showNetwork`, tests, documentation |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D11 sprites, D18 relais, D24 compteur, D26 raccord, L09 diagnostic), [ADR-003](003-zone-arrosee-lisible.md) (menu de la zone arrosée), [ADR-006](006-vision-debit.md) |
| Références | `IsoObject.FindExternalWaterSource`, `IsoObject.getFluidAmount` (42.22) ; `ISUI/ISCollapsableWindow.lua` ; écran LCD de Live Wire (`LW_Lcd.lua`, modèle visuel seulement : LiveWater ne dépend pas de Live Wire) |
| Origine | essai en jeu de l'utilisateur, 2026-11-19 : sept remarques (raccord est-ouest, noms non traduits, compteur, menus non exclusifs, eau des appareils, appareils reliés dans la vue du réseau, écran de la pompe) |

## Contexte

L'utilisateur a joué avec le réseau et relève ce qu'il ne voit pas ou voit mal :

1. un raccord de baril posé au bout d'un tuyau est-ouest, baril au nord, dessine son embout vers le sud, où il n'y a
   rien : la tuile n'existe que droite (tuyau à l'opposé du baril) ;
2. cinq objets posables s'affichent en `Base.Mov_LiveWater_…` dans l'inventaire : `ItemName.json` n'a pas la vanne,
   l'arrivée d'eau, les deux arroseurs ni le raccord, dans aucune langue ;
3. le compteur ne montre que les litres des dix dernières minutes : l'arrivée d'eau remplit ses relais de 25 L au pas
   suivant, donc une consommation de la maison passe en un pas et disparaît au suivant ;
4. « Afficher le réseau d'eau » reste au menu quand le réseau est affiché, à côté de « Masquer » ;
5. l'eau disponible dans un évier, une douche ou des toilettes ne se lit nulle part ;
6. la vue du réseau ne dit pas quels appareils de la maison sont raccordés ;
7. la pompe n'a qu'une infobulle ; Live Wire montre ses appareils sur un écran LCD.

## Décisions

- **D01 — Raccord coudé.** Le raccord garde l'orientation choisie à la pose (le baril derrière lui) et son embout suit
  le tuyau voisin réel : droit quand le tuyau est devant (comme aujourd'hui), coudé à gauche ou à droite quand il
  arrive par un côté. Trois modes (Remplir haut, Remplir bas, Pomper) × deux coudes × quatre orientations = 24 tuiles
  nouvelles, aux index 184-207 (le tileset passe à 208 sprites ; aucun index publié n'est réattribué). Le choix est
  une donnée de la définition de la pièce (le coude par côté relatif à l'orientation), pas un `if` sur le type.
- **D01b — Le raccord est un embranchement (mise à jour du 2026-11-19).** Deuxième essai de l'utilisateur : un raccord
  posé entre deux tuyaux n'en dessine qu'un, et un raccord posé au croisement de trois tuyaux n'est pas prévu. D01 ne
  traitait qu'un seul tuyau voisin ; elle est complétée, sans être retirée :
  - l'eau traverse le raccord d'un tuyau à l'autre (il « porte » comme un tuyau), en plus de remplir ou de vider son
    récipient : un raccord sur une conduite ne coupe plus ce qui est derrière lui ;
  - son dessin suit toutes les combinaisons de tuyaux devant, à gauche et à droite (le baril reste derrière) : droit,
    coude gauche, coude droit (D01), et quatre nouvelles formes : traversant gauche-droite (té), devant + gauche,
    devant + droite, devant + gauche + droite (croix) ;
  - 4 formes × 3 modes × 4 orientations = 48 tuiles nouvelles, aux index 208-255 (le tileset passe à 256 sprites).
  La forme est choisie par le masque des côtés relatifs raccordés, donnée de la définition de la pièce.
- **D02 — Noms.** Chaque objet de `LWT_moveables.txt` a son nom dans `ItemName.json`, dans les onze langues. Un test
  hors jeu le vérifie pour tout objet de script du mod.
- **D03 — Compteur d'eau.** Le compteur cumule les litres passés depuis sa pose (`total`, gardé quand on le ramasse et
  le repose, comme un vrai compteur). « Information » ouvre une fenêtre de compteur d'eau : un totalisateur à
  rouleaux (litres) et, dessous, les litres des dix dernières minutes et la qualité de l'eau. Pas de remise à zéro.
- **D04 — Menus exclusifs.** Quand le réseau est affiché, le menu propose « Masquer le réseau d'eau » seul ; quand il
  ne l'est pas, « Afficher le réseau d'eau » seul. Même règle pour la zone arrosée.
- **D05 — Eau d'un appareil.** Le menu d'un évier, d'une douche, d'une baignoire, de toilettes ou d'un lave-linge
  alimenté par un relais de LiveWater montre une ligne grisée « Eau : 18 L / 25 L ». Un appareil à sec garde sa ligne
  qui dit pourquoi (L09).
- **D06 — Appareils dans la vue du réseau.** « Afficher le réseau d'eau » surligne aussi les appareils de la zone de
  chaque arrivée d'eau du réseau : vert raccordé et en eau, rouge raccordé à LiveWater mais à sec, ambre non raccordé
  (pas plombé à la clé à tuyau), gris alimenté par autre chose (Live Wire, baril). L'autorité donne la liste ; la
  légende de « Masquer » compte chaque groupe.
- **D07 — Écran de la pompe.** « Information » sur la pompe ouvre une fenêtre à écran LCD rétroéclairé, propre à
  LiveWater (inspirée de Live Wire, sans en dépendre) : état, débit possible (50 L × rendement), débit des dix
  dernières minutes, total pompé depuis la pose, rendement, source. La pompe cumule son total comme le compteur (D03).
  Les fenêtres se mettent à jour pendant qu'elles sont ouvertes.

- **D08 — Une pièce en ligne reste droite (ajout du 2026-11-19).** Essai de l'utilisateur : un tuyau posé à côté
  d'un compteur se raccorde par le flanc et le dessin du réseau fait un T autour du compteur. Le compteur, comme la
  vanne en ligne, n'a que deux côtés, sur un seul axe : celui qu'il montre (est-ouest ou nord-sud, choisi à la pose).
  Un tuyau posé sur l'un de ses deux autres côtés est posé, mais ne s'y raccorde pas (ni lien, ni bras dessiné), ce
  qui vaut aussi après rechargement. La pièce déclare cette règle par une donnée (côtés par orientation), le réseau la
  lit ; aucun `if` sur le type. Le raccord de baril n'est pas concerné (décision de l'utilisateur : on laisse un tuyau
  derrière lui tel quel).

- **D09 — Vanne d'arroseur lisible (ajout du 2026-11-19).** L'utilisateur distingue mal un arroseur ouvert d'un
  arroseur fermé. La manette quart de tour de l'arroseur manuel est agrandie et épaissie (environ deux fois), dans
  le long du tuyau quand l'arroseur est ouvert, en travers quand il est fermé ; le programmateur de l'arroseur
  automatique porte un voyant vert allumé pendant l'arrosage, éteint au repos. Seules les tuiles 48-63 changent (mêmes
  index).
- **D10 — Bruit de vanne (ajout du 2026-11-19).** Ouvrir ou fermer une vanne (vanne en ligne, vanne d'arroseur à la
  main) fait un bruit d'ouverture ou de fermeture, entendu par les joueurs proches. Le jeu n'a aucun son de vanne : le
  mod livre deux sons courts (`.ogg` mono), générés pour lui, déclarés par des scripts `sound`. Le bruit part de
  l'autorité quand la vanne change d'état ; chaque client proche le joue localement.

- **D11 — La pompe ronronne dès qu'elle a du courant (ajout du 2026-11-19).** Jusqu'ici la pompe ne faisait du bruit
  qu'en pompant, et son courant n'était relu qu'au pas de dix minutes. Désormais son bruit suit son courant : une pompe
  allumée, alimentée et en état ronronne, même sans demande d'eau ; elle se tait dès que le courant tombe ou qu'on
  l'éteint. L'autorité écoute l'événement vanilla `OnElectricityChanged` (générateur allumé ou éteint, coupure du
  réseau ; `IsoGenerator.java:487, 572`, `AmbientSoundManager.java:254`) : elle relit aussitôt le courant des pompes
  chargées et démarre ou arrête leur bruit, sans attendre le pas. Le débit, l'usure et le bruit qui attire les zombies
  restent calculés au pas, sur le pompage réel.

- **D12 — Recettes rangées (ajout du 2026-11-19).** Les recettes de démontage apparaissaient en double (menu
  contextuel de l'objet et panneau d'artisanat) et l'arroseur automatique, entre autres, montrait un point
  d'interrogation au lieu de son icône. Toutes les recettes de LiveWater (fabrication et démontage) sont dans le seul
  panneau d'artisanat (étiquette `AnySurfaceCraft`, jamais `InHandCraft`), dans une catégorie propre **LiveWater**
  (`IGUI_CraftingCategories_LiveWater`). Chaque objet posable a son icône d'inventaire (`Item_LWT_<Pièce>.png`,
  64 × 64), découpée dans sa tuile par la recette des tuiles.

Options retenues par défaut (consigne « pas de questionnaire de conception ») : rouleaux en litres plutôt qu'en m³,
couleurs de la vue du réseau dans la palette existante, aucune remise à zéro des totaux.

## Conséquences

- Nouvelles tuiles : la recette, l'empaquetage, la carte de profondeur et le contrat des tuiles changent.
- L'état sauvegardé du compteur et de la pompe gagne un champ `total` ; aucune reprise d'ancien format (mod non publié).
- Deux fenêtres client nouvelles ; l'infobulle « Information » reste pour les autres pièces.

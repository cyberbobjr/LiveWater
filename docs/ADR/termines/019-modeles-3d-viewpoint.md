# ADR-019 — Modèles 3D de LiveWater pour Viewpoint (sous-mod)

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-019-MODELES-3D-VIEWPOINT` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Accepté (2026-11-20) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 019](../../ADR-plans/termines/plan-019-modeles-3d-viewpoint.md) |
| Décideur | l'utilisateur (« génère les mods du projet ViewPoint en 3D, fais ça dans un sous-mod de LiveWater », 2026-11-20) ; options recommandées appliquées par défaut |
| Portée | nouveau mod `batman_LiveWaterViewpoint` dans `Contents/mods` (même objet Workshop), générateur `source/tiles/build_viewpoint_models.py`, tests `tests/test_viewpoint_pack.py`, CHANGELOG, wiki |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (tuiles, D23), [contrat des tuiles](../../annexes/conception/tuiles-contrat.md) |
| Références | Viewpoint 0.1.7 (2026-11-15, Workshop 3809306528), lu dans son `Viewpoint.jar` décompilé : `viewpoint.addons.Kind`, `ModScan`, `Descriptor`, `DescriptorCheck`, `Ids`, `PackContent` ; `viewpoint.packs.ModelPacks`, `PackManifest`, `ObjReader`, `PackLoads`, `PackBind` ; `viewpoint.world.PackGather`, `WorldMesher` ; `viewpoint.models.RigidCapture` |

## Contexte

Viewpoint (vue à la première personne, mod Java chargé par ZombieBuddy) remplace les sprites par des modèles 3D quand
un paquet de modèles les lie. Sans paquet, un équipement de LiveWater reste une image plate dans la vue 3D.

Depuis sa version 0.1.7, Viewpoint **découvre lui-même** les paquets : il parcourt, dans chaque mod chargé,
`media/viewpoint/resourcepacks/<id>/pack.properties` (dossiers `42.x` puis `common`) ; le joueur les active dans son
menu. L'ancienne inscription Lua `Viewpoint.ModelPacks.register(mod, manifeste)` devient un paquet « hérité »
(`legacy.<mod>`), retrouvé en lisant les fichiers Lua du mod.

Contrat lu dans le code de Viewpoint 0.1.7 :

- `pack.properties` (format 1) : clés obligatoires `format`, `id`, `name`, `version` (`MMM.NNN.PPP`), `game.min`
  (deux nombres, `42.22`) ; facultatives `author`, `description` (128 caractères au plus), `icon` (PNG), `license`,
  `viewpoint.min`, `models` (chemin du manifeste dans le dossier du paquet, séparateur `/`, sans `..`). L'`id` :
  2 à 64 caractères `a-z 0-9 - .`, commence et finit par une lettre ou un chiffre, égal au nom du dossier, ne commence
  pas par `legacy`.
- Manifeste de modèles : `model.<nom>=<fichier.obj>` (chemin relatif au manifeste) et
  `bind.<sprite>=<modèle>,<degrés>,<x>,<y>,<z>,<échelle>` (échelle > 0).
- OBJ : `mtllib` et au moins un `map_Kd` (PNG) obligatoires, sinon le modèle n'est pas chargé ; unité une case, Z en
  haut, X vers l'est, Y vers le sud ; origine au centre de la case (`WorldMesher` passe `x + 0,5`, `y + 0,5`) ;
  un étage mesure 2,4494896 unités ; faces dans le sens direct (volume signé positif, comme les paquets publiés) ;
  une matière à `Ke` non nul ou à `map_Ke` brille.
- Les sprites attachés à un objet (calques, `AttachedAnimSprite`) ne sont dessinés en 3D que s'ils sont liés eux aussi.

## Décisions

- **D01 — Un sous-mod de données.** Nouveau mod `batman_LiveWaterViewpoint` dans le même projet et le même objet
  Workshop que LiveWater : `require=\batman_LiveWater`, aucun fichier Lua, aucune dépendance déclarée à Viewpoint ni à
  ZombieBuddy (sans Viewpoint, le sous-mod n'a aucun effet). En multijoueur, il doit figurer dans la liste des mods du
  serveur pour être découvert.
- **D02 — Nouveau format de Viewpoint.** Paquet de ressources découvert par Viewpoint 0.1.7 :
  `common/media/viewpoint/resourcepacks/batman-livewater/pack.properties` (`viewpoint.min=0.1.7`), manifeste
  `models.properties` et modèles dans ce dossier. Pas d'inscription Lua (chemin hérité).
- **D03 — Une seule source de géométrie** (export modifié le 2026-11-20, voir la mise à jour). Les modèles sortent des mêmes constructeurs Blender que les tuiles
  (`build_livewater_tiles.py`, `tile_groups()`), exportés par un générateur sans rendu : un OBJ par sprite et par
  orientation (déjà tourné comme la tuile, degrés 0, échelle 1), coordonnées Blender `(x, y, z)` écrites `(x, -y, z)`
  et faces retournées. Une seule texture palette (une case de couleur par peinture) et un seul MTL partagés ; les
  voyants allumés (pompe en marche, arrivée d'eau verte ou ambre, arroseur automatique en marche) brillent.
- **D04 — Sprites liés.** Toutes les tuiles dessinées de la planche : tuyaux 0-15 et 104-123, vannes et compteur
  16-21, pompes 24-39, arrivées d'eau 40-47 et 176-183, arroseurs 48-63, raccords de baril 64-75 et 184-255,
  goutte-à-goutte 160-175. Non liés : le relais invisible 76 (il doit rester invisible) et le jet animé 128-159 (eau
  semi-transparente, que les modèles de Viewpoint ne rendent pas : il reste l'image du sprite).
- **D05 — Vérification hors jeu.** Un test relit le paquet produit et applique les règles de Viewpoint ci-dessus
  (descripteur, identifiant, manifeste, chaque liaison vers un modèle existant, OBJ lisible avec `mtllib` et `map_Kd`,
  volume positif, modèle contenu dans sa case), et couvre exactement les sprites de D04.

## Mise à jour du 2026-11-20

D03, export par orientation remplacé : un OBJ par sprite et par orientation pesait 15 Mo (4 Mo compressés, plus que
LiveWater). Désormais **un OBJ par groupe de tuiles** (son orientation S), que les liaisons E, N et W tournent de 270,
180 et 90 degrés : Viewpoint tourne un modèle lié de `a` degrés en `(X, Y) -> (X cos a - Y sin a, X sin a + Y cos a)`
(`PackBind`, axes `x = -X`, `z = -Y`), soit +90 de l'est vers le sud, quand l'outil de rendu des tuiles tourne
l'orientation S de 90 degrés dans l'autre sens à chaque orientation. Paquet : 91 modèles, 4,4 Mo. Le MTL et la texture
palette sont rangés avec les OBJ (`models/`), pour que `mtllib` et `map_Kd` n'aient jamais de `..`.

## Mise à jour du 2026-11-27

D01 et D02, « aucun fichier Lua » et « pas d'inscription Lua », remplacés après les retours des joueurs (modèles
invisibles). Constat en jeu : Viewpoint 0.1.7 ne cherche les `pack.properties` qu'une fois, au lancement du jeu, dans
les mods actifs au menu principal (`AddonHooks.modsLoading`, `Discovery.begin`) ; un mod activé par une sauvegarde ou
un serveur n'est jamais trouvé (« 0 resource packs »), et un paquet trouvé reste éteint tant que le joueur ne l'allume
pas (`Choices.isOn`). `common/media/lua/client/LiveWaterViewpoint.lua` inscrit donc le manifeste du paquet
(`Viewpoint.ModelPacks.register`, deux arguments littéraux, à `OnGameBoot`, `OnGameStart` et au chargement du
fichier) : les modèles se chargent et s'affichent sans geste du joueur. Le paquet au nouveau format reste en place.
Conséquence acceptée : quand le mod est actif au menu principal, Viewpoint liste deux entrées (le paquet
`batman-livewater`, éteint, et `legacy.batman_LiveWaterViewpoint`, allumé). Test :
`tests/test_viewpoint_pack.py` (`LuaRegistration`). Passage en jeu : `autotest/scenarios/viewpoint.json`.

## Limites

Le rendu réel dans Viewpoint (GPU, éclairage, orientation vue en jeu) n'est vérifiable qu'en jeu, par l'utilisateur.

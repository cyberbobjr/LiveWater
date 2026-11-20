# Plan 019 — Modèles 3D de LiveWater pour Viewpoint (sous-mod)

ADR : [ADR-019](../../ADR/termines/019-modeles-3d-viewpoint.md) (Accepté le 2026-11-20).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Test du paquet, générateur Blender, sous-mod `batman_LiveWaterViewpoint` produit | Terminée (2026-11-20) | ADR accepté | D01-D05 | M | — |
| E02 | CHANGELOG, wiki (Viewpoint EN/FR), pages Steam, architecture, README des ADR | Terminée (2026-11-20) | E01 | D01, D02 | S | — |
| E03 | Passage en jeu par l'utilisateur : Viewpoint actif, paquet activé dans son menu, chaque équipement vu en 3D, bien orienté | Terminée (2026-11-20) | E01 | D03, D04 | S | — |

## Fiches

### E01 — Paquet et générateur

Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.

- `Contents/mods/batman_LiveWaterViewpoint/42.21/mod.info` (`require=\batman_LiveWater`, aucun Lua) et `icon.png`.
- `source/tiles/build_viewpoint_models.py` : Blender sans interface ni rendu, réutilise `tile_groups()` et `Kit` de
  `build_livewater_tiles.py` ; un OBJ par groupe (orientation S, version allumée pour les groupes à voyant), axes
  `(x, -y, z)` et coins des faces retournés, normales dédoublonnées, 4 décimales ; `models/livewater.mtl` et
  `models/palette.png` (une case 8 × 8 px par peinture, voyants `Ke`) ; `models.properties` (91 modèles, 190 liaisons,
  angles 0/270/180/90) ; `pack.properties` (format 1, `batman-livewater`, 1.0.0, `game.min=42.22`,
  `viewpoint.min=0.1.7`) ; `icon.png` tiré de `preview.png`.
  Commande : `blender -b --factory-startup -P source/tiles/build_viewpoint_models.py -- <projet>` →
  `viewpoint pack: 190 sprites into ...\batman-livewater`.
- `tests/test_viewpoint_pack.py` (10 tests) : mod.info sans Lua ; descripteur et identifiant selon les règles de
  Viewpoint ; sprites liés exactement ceux de D04 ; angles par orientation, même modèle pour les quatre ; OBJ avec
  `mtllib` sans `..`, `map_Kd` PNG ; volume signé positif ; modèle dans sa case (débord 0,75 au plus) et sous un
  étage ; arrivée d'eau tournée contre le bon mur (S, E, N, W) ; voyants qui brillent.
- Contrôle visuel : rendu Blender des OBJ importés (pompe en marche, arrivée d'eau à filtre, vanne, compteur,
  arroseur automatique, raccord en té, croix de tuyaux, goutte-à-goutte) : faces pleines, couleurs de la palette,
  voyants verts.
- Taille : 4,4 Mo (91 OBJ) ; l'export par orientation pesait 15 Mo (mise à jour de l'ADR).
- Preuves (2026-11-20) : `python -B -m unittest discover -s tests` → `Ran 576 tests` / `OK` ;
  `python -B tools/check_mod.py` → `OK: 112 Lua file(s) checked`.

### E02 — Documentation

Statut : Terminée (2026-11-20).

- `CHANGELOG.md` (Unreleased) : une ligne joueur.
- `docs/wiki/en/09-viewpoint.md`, `docs/wiki/fr/09-viewpoint.md`, sommaires et accueils EN/FR.
- `docs/architecture.md` (Outillage), `docs/ADR/README.md` (ligne ADR-019).
- Pages Steam (`README.steam*`, 11 langues, et `workshop.txt`) : une ligne Viewpoint dans « Options & compatibility » ;
  pages JP, KO, RU, FR raccourcies (le suffixe d'envoi compte désormais une ligne `Mod ID` de plus). Preuve
  (2026-11-20) : `pz_workshop_project.validate` → `[]` ; tailles de 6 602 (CN) à 7 982 octets (RU).

### E03 — Passage en jeu

Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.
activés ; dans les réglages de Viewpoint, paquet LiveWater activé et portée des modèles au-dessus de 0. Poser une pompe
contre l'eau (ses quatre orientations), quelques tuyaux (droit, coude, té), une vanne, une arrivée d'eau, un arroseur :
chaque pièce apparaît en 3D, collée au mur ou au bord attendu, tournée comme sa tuile ; le voyant de la pompe en marche
brille.

# Plan 017 — Pompe à eau reliée par fil à un onduleur LiveWire

ADR : [ADR-017](../../ADR/termines/017-pompe-reliee-a-un-onduleur-livewire.md) (Accepté le 2026-11-20). Dépend du plan 004 de
LiveWire (API révision 9).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| E01 | Inscription partagée, champ `link`, règle de courant de la pompe (relié / case), tests | Terminée (2026-11-20) | plan 004 de LiveWire, L4 | D01, D02, D03 | M | — |
| E02 | Wiki EN/FR, descriptions Steam, CHANGELOG | Terminée (2026-11-20) | E01 | D04 | S | — |
| E03 | Passage en jeu par l'utilisateur : pompe à l'étang reliée par fil, pompe non reliée sur générateur, sans LiveWire | Terminée (2026-11-20) | E01 | D01, D02 | S | — |

## Fiches

### E01 — Code

Statut : Terminée (2026-11-20). Preuve : code présent, mod publié (1.0.0-beta6) et fonctionnel, validé par l'utilisateur le 2026-11-20.

- Champ de pièce `link = { level = 0..10 }` (révision 24 de l'API LiveWater, refus `invalid_link`,
  `Parts:linkOf`) : `shared/LiveWater/LWT_Parts.lua`, `LWT_API.lua` ; la pompe porte `link = { level = 2 }`
  (`Parts/LWT_PartPondPump.lua`), l'arroseur automatique n'en porte pas (D01 : donnée du catalogue, aucun `if` sur un
  type).
- Inscription partagée (D03) : `shared/LiveWater/LWT_LiveWireConsumers.lua` (définition de base : sprites, catégorie,
  circuit, `link` à partir de la révision 9 de LiveWire ; inscription de chaque type qui a le crochet `power`) ;
  `server/LiveWater/LWT_Power.lua` la complète (`powerConsumption`, `display`, `summary`) ;
  `client/LiveWater/LWT_PowerClient.lua` l'inscrit sur un client multijoueur seulement, à `OnInitWorld`
  (`powerConsumption` 0, sans `display` ni `summary`). Ordre vérifié dans `E:\pz-source-42.22` :
  `IsoWorld.java:1811` déclenche `OnInitWorld`, puis `IsoWorld.java:1921` appelle `GlobalModData.instance.init()` qui
  déclenche `OnInitGlobalModData` (`GlobalModData.java:55`), sans branche `GameClient.client` qui saute l'un des deux.
- Règle de courant (D02) : case chargée inchangée (`consumerPowered`) ; case non chargée : `consumerLinkPowered`
  quand le type est reliable et que la réponse est un booléen (avec la dernière lecture `live`), sinon `gridAt` puis
  les règles de l'absence (`LWT_Power:linkSupplied`, `readAway`).
- Tests : `tests/test_linked_pump.py` (12 tests) ; `test_api.py` (révision 24), `test_fuel_station.py` (révision 23
  au moins).
- Preuves : `python -B -m unittest discover -s tests` → `Ran 557 tests` / `OK` ; `python -B tools/check_mod.py` →
  `OK: 111 Lua file(s) checked`. Aucun passage en jeu (E03).

### E02 — Documentation

Statut : Terminée (2026-11-20). Faits : wiki `docs/wiki/en/04-livewire.md`, `docs/wiki/fr/04-livewire.md` (pompe
raccordée par fil, sinon courant de la case), `06-for-modders.md` / `06-pour-les-moddeurs.md` (champ `link`,
révision 24), `CHANGELOG.md` (« Unreleased »), `docs/architecture.md`, `docs/specifications-techniques.md`. Descriptions Steam (11 langues) et `workshop.txt` : ligne LiveWire (pompe raccordée par fil à un onduleur, même hors
de sa zone) ; page russe raccourcie ailleurs ; `pz_workshop_project.validate` → `[]` (russe 7 987 octets, japonais 7 967).

### E03 — Passage en jeu

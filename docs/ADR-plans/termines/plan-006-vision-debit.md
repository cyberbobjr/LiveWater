# Plan 006 — Vision débit

ADR : [ADR-006](../../ADR/termines/006-vision-debit.md) (Accepté le 2026-11-18).

| # | Étape | Statut | Dépend de | Décisions ADR | Taille | Parallélisable avec |
|---|---|---|---|---|---|---|
| V01 | Débit des sorties d'arrosage, options sandbox, minuterie de 30 minutes ; tests | Terminée (2026-11-18) | ADR accepté | D01-D03 | L | V02 |
| V02 | Bout de circuit à sec et ports pleins après un mur démoli : les deux cas mis de côté deviennent des tests verts | Terminée (2026-11-18) | ADR accepté | D04, D05 | S | V01 |
| V03 | Scénarios en jeu et documentation | Terminée (2026-11-19) | V01, V02 | D01-D05 | M | — |
| V04 | Réseaux hors chargement : horloge, barils décomptés puis rapprochés, plantes globales, courant (LiveWire `gridAt`, ville, générateur au dernier état) ; tests ; scénario en jeu (joueur qui s'éloigne puis revient) | Terminée (2026-11-19) | V01 | D06-D08 | L | — |

## Fiches

### V01 — Débit

- Statut : Terminée (2026-11-18).
- Fait : besoin d'une sortie d'arrosage = son débit (`LWT_Plants:need`, 4e résultat de la stratégie de zone) ; débit
  lu par les capacités `spray` (option `SprinklerFlow`, 10 L) et `drip` (option `DripFlow`, 0,5 L par case), réglage
  `flow` facultatif d'une pièce (API révision 16) ; `LWT_Settings.value` ; `loss` = part de l'eau prélevée (7,5 L sur
  10) ; minuterie : réglage `duration` du `controller` (3 pas), état `left` ; options sandbox et traductions (11
  langues). L'arrivée d'eau et le remplissage des barils gardent leur besoin.
- Tests rebasés : `test_sprinkler` (10 L prélevés au lieu de 0,75 ; plus d'état `idle` sans plante assoiffée ; dose
  courte 0,6 L → 2 doses), `test_timer` (3 pas de 10 L puis fermé), `test_drip` (baril 30 → 28,5 L : 3 cases × 0,5 L).
- Preuve du vert : `python -B -m unittest discover -s tests` → `Ran 406 tests`, `OK` (aucun saut) ;
  `python -B tools/check_mod.py` → `OK: 102 Lua file(s) checked`.

### V02 — Cas mis de côté

- Statut : Terminée (2026-11-18).
- Fait : D04 — ligne après une sortie à court de pression : `no_pressure` (comportement déjà en place, test vert) ;
  plante couverte deux fois : chaque sortie prélève son débit, la plante reçoit son besoin ; D05 — `Network:relink`
  reçoit les masques d'avant (`masksAround`), un lien apparu qui dépasse un port n'est pas fait, la pièce posée en
  dernier reçoit `apart` (gardé dans le registre, effacé quand la voisine part).
- Preuve du vert : `test_combo_outlets` et `test_combo_topology` sans `skip`, même suite que V01 : `Ran 406 tests`,
  `OK`.

### V04 — Hors chargement

- Statut : Terminée (2026-11-19).
- Fait : `LWT_Clock` avance tout réseau qui a un départ d'eau, chargé ou non (plus de port monde dans l'horloge) ;
  prise d'eau : sorte de source notée à la pose (inchangé, aucune lecture du monde) ; `LWT_Fittings` : hors
  chargement, décompte dans l'état relevé (`count` → crochet `sense`, `offline = { taken, added, quality }`), jamais
  sous 0 ni au-delà de la place relevée, écrit une fois dans le vrai conteneur (`chunkLoaded` sur `LoadChunk`, sinon
  premier pas chargé) ; plantes : objet global vanilla par `LWT_GameFarming` (déjà sans case) ; `LWT_Relays:need` = 0
  hors chargement ; `LWT_Publisher` : rien d'écrit hors chargement, pièce présentée au `LoadChunk` (`chunkLoaded`) ;
  `LWT_Power` : lecture chargée notée (`_power`), hors chargement Live Wire `gridAt` + dernier `consumerPowered`,
  sinon générateur au dernier pas chargé ou réseau de la ville (`getSandboxOptions():doesPowerGridExist()`) ; port
  monde `powerAt`, `gridRuns`. Scénario `autotest/lwt_hooks.lua` (solo) : vanne de l'arroseur rouverte, culture à 0,
  joueur à 300 cases, 2 pas, retour : culture arrosée, arroseur `served` et dessiné en marche.
- Preuve du vert : `tests/test_away.py` (17 tests) et `test_inlet` (arrivée d'eau hors chargement), `test_clock`
  rebasé (tout réseau avancé, chargé ou non) ; `python -B -m unittest discover -s tests` → `Ran 431 tests`, `OK` ;
  `python -B tools/check_mod.py` → `OK: 102 Lua file(s) checked` ; `python PZDevKit/pzdev.py check LiveWater` →
  `sp: hooks ok`, `server: hooks ok`, `mp: hooks ok`.
- Preuve en jeu (2026-11-19) :
  - solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code 0, `summary=47/47 PASS`, `runs/20261119-005256-sp-7ac436c52094` ;
  - visual : `python PZDevKit/pzdev.py sp LiveWater/autotest/scenarios/visual.json --wait-idle 3600` → code 0, `summary=58/58 PASS`, `runs/20261119-005417-sp-6496fd0c65f5` ;
  - multijoueur : `python PZDevKit/pzdev.py mp LiveWater --clients 1 --client-run --wait-idle 3600` → code 0, serveur `20/20 PASS`, client 1 `6/6 PASS`, `runs/20261119-005810-mp-202a8d9e9990`.
  Le scénario a été corrigé deux fois avant le vert (2026-11-19) : l'accélération du temps ne prenait pas (`setGameSpeed` remet le multiplicateur à 1, `SpeedControls.java:137` : multiplicateur 40 posé ensuite) ; l'arroseur automatique, posé après la vanne en ligne restée fermée, était à sec à raison (vanne rouverte avant), puis rouvert par une nouvelle tranche de 6 h (minuterie réglée à 24 h par la commande `setTimer`).

### V03 — Scénarios en jeu et documentation

- Statut : Terminée (2026-11-19).
- Fait : `autotest/lwt_hooks.lua` (arroseur « servi » à chaque pas, jamais `idle` ; ligne de goutte-à-goutte `served` ;
  arroseur automatique : 3 pas servis puis fermé) ; `python PZDevKit/pzdev.py check LiveWater` → `sp: hooks ok`,
  `server: hooks ok`, `mp: hooks ok`. Documentation : CHANGELOG, wiki EN/FR, spécifications, architecture,
  README.steam (11 langues), workshop.txt.
- Preuve en jeu (2026-11-19) :
  - solo : `python PZDevKit/pzdev.py sp LiveWater --wait-idle 3600` → code 0, `summary=47/47 PASS`, `runs/20261119-005256-sp-7ac436c52094` ;
  - visual : `python PZDevKit/pzdev.py sp LiveWater/autotest/scenarios/visual.json --wait-idle 3600` → code 0, `summary=58/58 PASS`, `runs/20261119-005417-sp-6496fd0c65f5` ;
  - multijoueur : `python PZDevKit/pzdev.py mp LiveWater --clients 1 --client-run --wait-idle 3600` → code 0, serveur `20/20 PASS`, client 1 `6/6 PASS`, `runs/20261119-005810-mp-202a8d9e9990`.
  Le scénario a été corrigé deux fois avant le vert (2026-11-19) : l'accélération du temps ne prenait pas (`setGameSpeed` remet le multiplicateur à 1, `SpeedControls.java:137` : multiplicateur 40 posé ensuite) ; l'arroseur automatique, posé après la vanne en ligne restée fermée, était à sec à raison (vanne rouverte avant), puis rouvert par une nouvelle tranche de 6 h (minuterie réglée à 24 h par la commande `setTimer`).

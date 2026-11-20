# ADR-021 — Le raccord de remplissage fait le plein d'un groupe électrogène

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-021-PLEIN-DES-GROUPES-ELECTROGENES` |
| Date de création et de mise à jour | 2026-11-20 |
| Statut | Proposé |
| Avancement | voir le [plan 021](../ADR-plans/plan-021-plein-des-groupes-electrogenes.md) |
| Décideur | l'utilisateur (« oui ok pour les 2 ADR », 2026-11-20) |
| Portée | `batman_LiveWater` : nouveau genre de récipient « groupe électrogène » (`LWT_GameContainers`, `LWT_Containers`), compte pendant l'absence (`LWT_Fittings`), reprise au chargement de la case, textes d'information, traductions, tests, wiki, CHANGELOG |
| Documents liés | [ADR-013](013-raccord-de-remplissage-et-abreuvoirs.md) (raccord de remplissage), [ADR-014](014-essence-dans-les-tuyaux.md) (D03 `takes`, D04 jamais de mélange), [ADR-006](termines/006-vision-debit.md) (D06 vie loin du joueur), [ADR-011](011-pompe-sur-baril.md) |
| Références | Java 42.22 `IsoGenerator` : `getFuel`, `setFuel` (borné à `getMaxFuel` = 10, `IsoGenerator.java:439-460`), `getTotalPowerUsing` (:660), rattrapage des heures manquées à la première mise à jour (:185-239, `lastHour`), `setActivated(true)` remet `lastHour` à l'heure courante (:470-473) ; option de partie `GeneratorFuelConsumption` ; LiveWire `LW_Backup.restore` (même arrêt-relance pour annuler le rattrapage, `LW_Backup.lua:250-262`) |
| Origine | suggestion d'un joueur sur la page Workshop (2026-11-20) : baril d'essence, pompe et tuyaux pour remplir le groupe électrogène tout seul, qui se vide très vite avec le profil « Realistic 1993 » de LiveWire |

## Contexte

La pompe à eau posée contre un baril d'essence l'envoie déjà dans les tuyaux (ADR-014), et le raccord de remplissage
remplit un autre baril d'essence. Rien ne verse l'essence dans un groupe électrogène.

Un groupe électrogène du jeu ne brûle son essence que si sa case est chargée. Au retour du joueur, sa première mise à
jour décompte d'un coup toutes les heures manquées : réservoir plein au départ (10), trois jours d'absence, il se vide
et s'arrête avant que le réseau ait pu le remplir. Pendant l'absence, le réseau ne voit pas cette consommation : la
place libre notée au départ (0 pour un plein) bloque tout apport.

## Décisions

- **D01 — Le raccord de remplissage, pas une nouvelle pièce.** Le raccord de remplissage existant, posé entre un tuyau
  et un groupe électrogène (le groupe derrière lui, comme un baril), fait son plein. Un seul objet à connaître pour le
  joueur ; côté code, un genre de récipient de plus dans le registre des genres (`KINDS`), sans `if` sur une liste.
- **D02 — De l'essence seulement.** Le groupe électrogène n'accepte que l'essence (`takes = "fuel"`). Sur un réseau
  d'eau, le raccord ne lui donne rien et son information dit « Mauvais liquide » (ADR-014 D03).
- **D03 — Plein près du joueur.** Case chargée, à chaque pas de 10 minutes, le raccord remet le réservoir à plein (place
  libre = `getMaxFuel() - getFuel()`, au plus le débit du raccord), sur l'autorité, par `setFuel`. Un groupe arrêté se
  remplit aussi ; le raccord ne le démarre jamais.
- **D04 — Loin du joueur, LiveWater compte la consommation.** Au départ, le raccord note l'essence du groupe, s'il
  tourne, sa consommation par heure (`getTotalPowerUsing()` × `GeneratorFuelConsumption`). À chaque pas d'absence, il
  retire du réservoir noté la consommation du pas (si le groupe tourne et n'est pas vide), puis demande au réseau la
  place ainsi libérée. Un réservoir noté vide arrête le groupe noté. Jamais d'essence créée : le raccord ne compte que
  ce que le réseau a vraiment donné.
- **D05 — Au retour, LiveWater remplace le rattrapage du jeu.** Au chargement de la case, si le raccord a compté
  quelque chose pendant l'absence, LiveWater arrête le groupe, écrit l'essence notée (`setFuel`), puis le redémarre s'il
  tournait encore dans le compte. Le redémarrage remet `lastHour` à l'heure courante : le jeu ne décompte pas une
  seconde fois les heures déjà comptées (même méthode que LiveWire `LW_Backup.restore`). L'usure de l'absence
  (`condition`) suit la loi du jeu : une chance sur `getConditionLowerChance()` par heure de perdre 1 ou 2 points.
  Si le raccord n'a rien compté (réseau sec, mauvais liquide), LiveWater ne touche à rien et le jeu fait son rattrapage
  habituel.
- **D06 — Groupes pilotés par LiveWire.** Un groupe électrogène relié à LiveWire comme secours (sa clé de ModData de
  secours) a déjà son propre compte d'absence dans LiveWire. LiveWater le remplit seulement quand sa case est chargée
  (D03) et ne fait ni D04 ni D05 pour lui, pour ne jamais compter deux fois. Un meilleur accord passerait par l'API de
  LiveWire : demande à transmettre par l'utilisateur, hors de ce chantier.
- **D07 — Ce que le joueur lit.** L'information du raccord montre « Groupe électrogène : 6,2 / 10 » et, s'il est
  arrêté, « Groupe électrogène arrêté ». Le menu du groupe électrogène du jeu ne change pas.

## Arbitrages ouverts

- **Q01 — Ordre au chargement.** D05 suppose que l'événement de chargement de la case passe avant la première mise à
  jour du groupe (hypothèse, celle de LiveWire). L'étape 1 du plan le vérifie dans le code Java ; sinon, D05 revient à
  l'utilisateur avant tout code.

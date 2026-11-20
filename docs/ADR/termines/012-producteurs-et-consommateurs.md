# ADR-012 — Producteurs et consommateurs : seule une pompe met l'eau dans le réseau ; API ouverte

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-012-PRODUCTEURS-ET-CONSOMMATEURS` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | Terminé le 2026-11-20 ; voir le [plan 012](../../ADR-plans/termines/plan-012-producteurs-et-consommateurs.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : raccord de baril (mode Pomper retiré), écoulement par gravité retiré, distribution (`LWT_Flow`, `LWT_Clock`, `LWT_Network`), API publique des consommateurs, traductions, tests, scénario en jeu, documentation |
| Documents liés | [ADR-001](001-reseau-eau-ouvert.md) (D13 sorties, D20 Live Wire, D26 raccord), [ADR-004](004-goutte-a-goutte.md) (D04 gravité, remplacée), [ADR-009](009-cartouche-rechargeable-et-barils.md) (D03 : partie « goutte-à-goutte sans pompe » remplacée), [ADR-011](011-pompe-sur-baril.md) (pompe contre un baril) |
| Références | `LWT_CapFitting`, `LWT_Flow:supply`, `LWT_Flow:gravity`, `LWT_Outlets`, `LWT_API`, `LWT_Power` (consommateurs Live Wire) |
| Origine | demandes de l'utilisateur du 2026-11-19 : « une pompe doit prendre l'eau quelle que soit sa source (baril, étang, piscine, point d'eau, rivière) à côté et injecte ensuite l'eau dans le circuit. Une fois l'eau dans le circuit, les consommateurs en font ce qu'ils en veulent. C'est comme LiveWire : il y a les producteurs et les consommateurs. Et il faut une API ouverte » ; « supprime complètement le mode pomper. Si l'eau du baril doit aller dans le réseau, il faut placer une pompe à eau à côté » ; « n'oublie pas d'enregistrer la pompe à eau comme consommateur dans LiveWire si le mod est présent » |

## Décisions

- **D01 — Seul un producteur met l'eau dans le réseau.** Un producteur (une pièce qui met sous pression : la pompe à
  eau, ou celle d'un autre mod) prend l'eau de la source qu'il touche (eau naturelle, puits, baril, ou sorte
  enregistrée par un autre mod) et l'injecte dans les tuyaux. Rien d'autre n'y met d'eau.
- **D02 — Le raccord de baril ne fait plus que Remplir.** Le mode **Pomper** du raccord est supprimé, avec sa
  commande de bascule, ses lignes, ses traductions et ses variantes de dessin. Le raccord est un consommateur : il
  remplit son baril. Pour envoyer l'eau d'un baril dans le réseau, on pose une pompe à eau contre lui (ADR-011).
- **D03 — Plus d'écoulement par gravité.** Un réseau sans pompe ne donne rien : le goutte-à-goutte, comme les autres
  consommateurs, a besoin d'une pompe. Remplace ADR-004 D04 et la phrase d'ADR-009 D03 « sans pompe, il ne donne de
  l'eau qu'au goutte-à-goutte ». Le champ `byGravity` des sorties et le crochet `gravity` disparaissent de l'API.
- **D04 — API ouverte des consommateurs.** `LiveWater.API.registerOutlet(type, handler)` permet à un autre mod de dire
  où va l'eau d'une sorte de consommateur : `need(part)` (litres voulus ce pas), `deliver(part, litres, quality)`,
  et en option `release(part)` (la pièce part) et `cut(part)` (une vanne la coupe, ADR-010 D04). Les consommateurs de
  LiveWater (maison, arroseurs, goutte-à-goutte, raccord de baril) passent par la même porte. Les producteurs ont déjà
  la leur : `registerPart` (capacité pompe), `registerSource` (sorte de point d'eau), `registerContainer` (récipient),
  `registerCapability`. Le wiki des moddeurs décrit producteurs et consommateurs, comme Live Wire.
- **D05 — Live Wire.** La pompe à eau reste un consommateur de Live Wire quand ce mod est chargé (ADR-001 D20 : toute
  pièce qui demande du courant, enregistrée à `OnInitWorld` si l'API de Live Wire est en révision 6 ou plus), qu'elle
  pompe un étang, un puits ou un baril. Aucun `require=` : sans Live Wire, la pompe prend le courant d'un générateur ou
  du réseau public.

## Conséquences

- API révision 22. Mod non publié : aucune reprise de sauvegarde (un raccord enregistré sur Pomper redevient Remplir).
- Code, tests et traductions du mode Pomper et de la gravité supprimés (règle : supprimer du code supprime ses tests).

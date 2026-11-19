# ADR-011 — La pompe à eau puise dans un baril

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-011-POMPE-SUR-BARIL` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | En cours ; voir le [plan 011](../ADR-plans/plan-011-pompe-sur-baril.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : pose de la pompe (capacité intake, site de pose), nouvelle capacité de puisage dans un récipient voisin (API), traductions, tests, scénario en jeu, documentation |
| Documents liés | [ADR-001](termines/001-reseau-eau-ouvert.md) (D16 sources, D26 raccord de baril), [ADR-009](009-cartouche-rechargeable-et-barils.md) (D03 : un baril n'alimente la maison que par une pompe), [ADR-010](010-pompe-a-eau-et-vanne-immediate.md) |
| Références | `LWT_CapIntake`, `LWT_GameSite`, `LWT_Fittings`, `LWT_CapFitting` (`draw`, `sense`), `LWT_Flow:supply` (les puisages remplacent la source propre des pompes), `LWT_Containers:admits` |
| Origine | demande de l'utilisateur du 2026-11-19 : « je veux que la pompe à eau puisse se connecter à un baril afin d'utiliser l'eau du baril pour alimenter le circuit d'eau dans les tuyaux » |

## Contexte

- La pompe ne se pose qu'au bord d'une eau naturelle ou contre un puits. Un baril ne rejoint le réseau que par un
  raccord de baril réglé sur Pomper, et la pompe doit quand même se trouver au bord de l'eau.
- `LWT_Flow:supply` sait déjà faire tirer aux pompes l'eau des parties qui puisent (`draw`), à la place de leur source.

## Décisions

- **D01 — La pompe se pose contre un baril.** La pompe à eau se pose au bord d'une eau naturelle, contre un puits **ou
  contre un baril** : un récipient que le raccord de baril accepte (`LWT_Containers:admits` : 20 L ou plus,
  récupérateur d'eau de pluie, récipient enregistré ou listé), sur l'un de ses quatre côtés. Le refus dit les trois
  possibilités.
- **D02 — Elle pompe l'eau du baril.** Contre un baril, la pompe tire l'eau du baril dans les tuyaux, jusqu'à son débit
  par pas, avec les mêmes règles que le raccord réglé sur Pomper (part partagée entre ceux qui puisent dans le même
  baril, compte tenu pendant l'absence du joueur, jamais d'eau créée). Elle ne prend que de l'eau (propre ou souillée),
  jamais de carburant ni autre chose. L'eau garde sa qualité : souillée, la maison demande le filtre ; propre, elle
  passe. Baril vide : la pompe ne donne rien.
- **D03 — Le baril passe avant l'étang.** Posée à la fois au bord de l'eau et contre un baril, la pompe tire d'abord
  le baril (règle existante des puisages), puis sa source naturelle quand le baril est vide.
- **D05 — Chaque pompe tire sa propre source (ajout du 2026-11-19, question de l'utilisateur sur deux pompes, l'une
  dans l'étang, l'autre contre un baril).** Le baril d'une pompe n'appartient qu'à elle : il n'entre pas dans le
  puisage commun des raccords réglés sur Pomper. Sur un même réseau, la pompe de l'étang donne l'eau de l'étang, la
  pompe du baril l'eau du baril ; leurs litres s'additionnent (deux pompes, deux débits, comme deux pompes d'étang
  aujourd'hui, chacune avec son courant et son usure), la qualité est mélangée (souillée si l'une l'est). La pompe de
  l'étang ne vide jamais le baril de l'autre. Une pompe qui remplit un baril par un raccord réglé sur Remplir pendant
  qu'une pompe le vide ne crée pas d'eau : elle ne fait que tourner en rond.
- **D04 — Information.** La fenêtre et le menu d'information de la pompe montrent le baril et son contenu
  (« Baril : N L ») ; sans baril contre elle, rien de plus (une pompe d'étang seule n'a pas de ligne de baril).

## Conséquences

- API révision 21 : capacité `vessel` (puisage dans un récipient voisin, hooks `sense`, `fittingMode`, `draw`, `lines`),
  champ `orVessel` de la capacité `intake`, `GameSite:hasVessel()`.
- Le raccord de baril garde ses deux réglages ; rien ne change pour lui.

# ADR-016 — « Retirer LiveWater de ce monde » : mode debug en solo, admin en multijoueur

| Champ | Valeur |
|---|---|
| Identifiant | `ADR-016-RETRAIT-DEBUG-OU-ADMIN` |
| Date de création et de mise à jour | 2026-11-19 |
| Statut | Accepté (2026-11-19) |
| Avancement | voir le [plan 016](../ADR-plans/plan-016-retrait-debug-ou-admin.md) |
| Décideur | l'utilisateur |
| Portée | `batman_LiveWater` : menu client `LWT_AdminMenu.lua`, adaptateur serveur `LWT_GamePlayers.lua` (`isAdmin`), nouveau module partagé du droit de retrait, tests, wiki |
| Documents liés | [ADR-001](termines/001-reseau-eau-ouvert.md) (P21, L14 : action de retrait), même règle que l'action « Retirer tous les relais d'eau » de LiveWire |
| Références | `Capability.UseDebugContextMenu` (rôle admin, vanilla `ClientCommands.lua`) ; `isDebugEnabled()` (option de lancement `-debug`) |
| Origine | demande de l'utilisateur du 2026-11-19 : « le sous-menu "Retirer livewater" apparait tout le temps alors que je ne veux qu'il apparaisse qu'en mode débug ou pour l'admin sur un serveur mp... je te l'ai déjà dit » |

## Contexte

L'ADR-001 offrait l'action « Retirer LiveWater de ce monde » à un admin sur un serveur **et au joueur en solo, toujours**.
En solo, l'option apparaît donc dans chaque menu au clic droit, alors qu'elle ne sert qu'avant de désinstaller le mod.
L'utilisateur avait déjà demandé qu'elle soit réservée au mode debug ou à l'admin.

## Décisions

- **D01 — Qui voit et peut lancer le retrait.** En multijoueur (client ou serveur) : un joueur dont le rôle a la
  capacité `UseDebugContextMenu` (admin). En solo : seulement quand le jeu est lancé en mode debug
  (`isDebugEnabled()`). Remplace, pour le solo, la règle « toujours » de l'ADR-001 (P21, L14).
- **D02 — Une seule règle, deux contrôles.** La règle vit dans un module partagé ; le menu du client l'utilise pour
  afficher l'option, l'autorité (serveur ou solo) l'utilise pour accepter la commande.
- **D03 — Textes.** Le wiki (retirer le mod) dit : admin en multijoueur, mode debug en solo
  (option de lancement `-debug`).

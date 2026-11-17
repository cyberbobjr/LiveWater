# LiveWater — contraintes de développement

Contraintes propres à ce projet. Les règles communes à tous les mods de l'utilisateur vivent dans le fichier
d'instructions unique du dossier de développement parent, hors de ce dépôt.

## Périmètre

- Mod `batman_LiveWater`, mod frère de Live Wire consacré à l'eau. Il **n'exige pas** Live Wire : avec Live Wire
  (API révision 6 ou plus), il s'y inscrit comme consommateur ; sans lui, il suit la règle vanilla du courant.
- **Aucune modification de Live Wire** pour ce projet. Un besoin d'API côté Live Wire se transmet à la session qui
  tient l'API de Live Wire, par l'utilisateur.
- Aucun code d'ADR non accepté. Test rouge d'abord. Clôture selon la skill `chantier-adr`.

## Règles d'architecture (ADR-001)

- **Ouvert avant tout** : tout élément est une pièce inscrite par l'API publique ; tout comportement est une capacité.
  Un fichier par pièce et par capacité. Aucun `if` sur une liste fermée de types.
- **Ne jamais casser l'existant** : identifiants publiés jamais renommés ni réattribués ; données versionnées, champs
  inconnus conservés ; pièces de type inconnu conservées ; API à révisions seulement additives.
- **Aucun abonnement par image** (`OnTick`, `OnTickEvenPaused`, `OnPlayerUpdate`, `OnRenderTick`, `OnPostRender`,
  `OnPreUIDraw`), même pour une vue ouverte. Une seule horloge serveur `EveryTenMinutes`.
- Domaine pur (graphe, pression, distribution, qualité) sans API du jeu ; adaptateurs PZ autour.

## Conventions

Table globale `LiveWater`, fichiers `LiveWater/LWT_*.lua`, objets posables `Base.Mov_LiveWater_<Nom>`, objets
d'inventaire `LiveWater.<Nom>`, recettes `module LiveWater` préfixe `LWT`, traductions `*_LWT_*`, ids de pièces
`"<Mod>:<Nom>"`. Tuiles provisoires en formes simples marquées `placeholder`.

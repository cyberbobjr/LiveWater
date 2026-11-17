# LiveWater — spécifications techniques

Contrats précis du mod (objets, commandes réseau, ModData, options sandbox, traductions, API publique). Ils sont
écrits ici à mesure que les étapes du [plan 001](ADR-plans/plan-001-reseau-eau-ouvert.md) les livrent.

## Identité

| Élément | Valeur |
|---|---|
| `id` | `batman_LiveWater` |
| Version minimale du jeu | 42.21 (cible 42.22) |
| `require=` | aucun |
| `incompatible=` | `\LGExtendedPlumbing,\LGMainsWater` |
| Table Lua globale | `LiveWater` |
| Préfixes | fichiers `LWT_*.lua`, recettes `LWT`, traductions `*_LWT_*`, ids de pièces `"<Mod>:<Nom>"` |

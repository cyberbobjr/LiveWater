# LiveWater — améliorations et idées

Ce document propose ; il n'autorise aucune implémentation sans validation de l'utilisateur.

## Améliorations de code

Aucune pour l'instant.

## Idées de fonctionnalités

| # | Idée | Intérêt pour le joueur | Faisabilité | Effort |
|---|---|---|---|---|
| I01 | Gel des tuyaux et de la pompe en hiver | Saisons qui comptent | point d'extension `available(context)` de `intake` (D16) | M |
| I02 | Surpresseur (`booster`) | Réseaux plus longs | capacité `pump` existante (D14) | S |
| I03 | Tuyaux en cuivre ou en PVC | Variété de matériaux | nouvelle définition de pièce, 16 sprites (D12) | S |
| I04 | Fuites et casse des tuyaux | Entretien du réseau | nouvelle capacité ; hors portée de l'ADR-001 | M |
| I05 | Pompe manuelle à levier sans courant | Début de partie | pièce `intake` + `pump` sans consommation | S |
| I06 | Piscine comme source | Sources en ville | `intake` sur case de piscine (D16) | S |
| I07 | Récupérateur d'eau de pluie sur toit raccordé (retirée : ADR-009 D03) | Eau propre gratuite | ~~D28, baril raccordé~~ | M |
| I08 | Abreuvoir pour animaux alimenté | Élevage B42 | sortie « Remplir » d'un conteneur inscrit (D26) | M |
| I09 | Douche extérieure posable | Hygiène en base | point d'eau posable + arrivée d'eau | S |
| I10 | Reprise de la pompe aux barils de Live Wire | Un seul mod de l'eau | ADR distinct (D21) | L |

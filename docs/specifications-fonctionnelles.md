# LiveWater — spécifications fonctionnelles

Ce que fait le mod pour le joueur et l'administrateur. Les fonctionnalités prévues sont décrites par
l'[ADR-001](ADR/001-reseau-eau-ouvert.md) et entrent ici, avec un identifiant `F01`, `F02`…, à mesure que les étapes
du [plan 001](ADR-plans/plan-001-reseau-eau-ouvert.md) sont terminées. Rien n'est encore vérifié en jeu.

| Id | Fonctionnalité | Étape |
|---|---|---|
| F01 | Tuyaux galvanisés : 4 sections par tuyau métallique scié ; posés au clic droit, une section par case ; ils prennent seuls leur forme (droit, coude, T, croix) ; démontés à la clé à tuyau, section rendue | E07 |
| F02 | Pompe d'étang : fabriquée (Électricité 2), posée au curseur de meuble à côté d'un lac, d'un étang ou d'une rivière (refus en rouge ailleurs) ; 50 L toutes les 10 minutes tant qu'une sortie a besoin d'eau, arrêt seule sinon ; sprite en marche ou à l'arrêt ; elle garde son état si on la déplace | E08 |
| F03 | Courant de la pompe : générateur ou réseau public ; avec Live Wire, consommateur de 250 W en marche, coupé par ses disjoncteurs, visible dans le logiciel de gestion (état, débit ; total des pompes du réseau) | E08 |
| F04 | Réglage sandbox du débit des pompes (multiplicateur, 1,0 par défaut) | E08 |
| F05 | Cartouche filtrante : fabriquée avec 2 charbons et 2 bandes de tissu ; montée dans la pompe au clic droit, elle rend l'eau propre (la maison la reçoit) sur 500 L ; son état montre ce qui reste ; retirée, elle revient avec son usure, ou est jetée si usée ; la pompe montre le filtre ; durée réglable en sandbox | E10 |

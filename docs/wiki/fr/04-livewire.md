# LiveWire (facultatif)

LiveWater fonctionne seul : une pompe tourne quand sa case a du courant d'un générateur ou du réseau public, comme
tout appareil du jeu.

Avec **LiveWire** activé (révision 6 ou plus de son API), LiveWater inscrit ses pièces électriques comme consommateurs
de LiveWire :

- la **pompe d'étang** tire **250 W** en marche, de l'onduleur LiveWire qui alimente sa case ; un disjoncteur de
  LiveWire peut la couper ;
- la **minuterie d'un arroseur automatique** tire **5 W** ;
- le logiciel de gestion de LiveWire montre chaque pompe (état, débit) et le total des pompes (*pompes à eau en
  marche*, *eau pompée par 10 minutes*).

Un évier alimenté par une pompe à eau de LiveWire est laissé tel quel par l'arrivée d'eau de LiveWater : les deux mods
ne remplissent pas deux fois le même point d'eau.

Aucun réglage : LiveWater détecte LiveWire au démarrage du monde.

Suite : [Options sandbox](05-options-sandbox.md)

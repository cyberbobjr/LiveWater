# LiveWire (facultatif)

LiveWater fonctionne seul : une pompe tourne quand sa case a du courant d'un générateur ou du réseau public, comme
tout appareil du jeu.

Avec **LiveWire** activé (révision 6 ou plus de son API), LiveWater inscrit ses pièces électriques comme consommateurs
de LiveWire :

- la **pompe à eau** tire **150 W** en marche, de l'onduleur LiveWire qui alimente sa case ; un disjoncteur de
  LiveWire peut la couper ;
- la **minuterie d'un arroseur automatique** tire **5 W** ;
- le logiciel de gestion de LiveWire montre chaque pompe (état, débit) et le total des pompes (*pompes à eau en
  marche*, *eau pompée par 10 minutes*).

### Relier la pompe à un onduleur (LiveWire 2.x)

Avec LiveWire 2.x (révision 9 ou plus de son API), la pompe à eau peut être **raccordée à un onduleur par du fil
électrique**, comme un appareil de LiveWire :

- clic droit sur la pompe, **LiveWire > Raccorder à un onduleur** ; ou, depuis l'onduleur, **Raccorder un
  équipement** ou la fenêtre **Raccordements** ;
- il faut **Électricité 2**, un **tournevis** et du **fil électrique** selon la distance, jusqu'à la portée du câble
  (**12 cases** par défaut), même hors de la zone alimentée par l'onduleur : une pompe à l'étang, l'onduleur dans la
  maison ;
- une fois raccordée, la pompe tourne sur cet onduleur et sa consommation lui est facturée, même quand personne n'est
  à proximité.

Une pompe non raccordée (ou avec un LiveWire plus ancien, ou sans LiveWire) prend le courant de sa case : générateur,
réseau public ou zone d'un onduleur. La minuterie de l'arroseur automatique ne se raccorde pas : elle prend toujours le
courant de sa case.

Un évier alimenté par une pompe à eau de LiveWire est laissé tel quel par l'arrivée d'eau de LiveWater : les deux mods
ne remplissent pas deux fois le même point d'eau.

Aucun réglage : LiveWater détecte LiveWire au démarrage du monde.

Suite : [Options sandbox](05-options-sandbox.md)

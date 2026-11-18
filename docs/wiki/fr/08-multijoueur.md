# Multijoueur

> LiveWater n'a pas encore été testé sur un serveur multijoueur. Signalez ce que vous constatez.

- Le **serveur décide de tout** : il fait avancer l'eau toutes les 10 minutes, sauvegarde les réseaux et vérifie
  chaque action (distance, objets, outils, droits d'administration). Les joueurs envoient seulement des demandes depuis
  leurs menus au clic droit.
- Tous les joueurs voient les mêmes tuiles : pompe en marche ou arrêtée, filtre, voyant de l'arrivée d'eau, jet des
  arroseurs.
- Ajoutez LiveWater à la ligne `Mods=` du serveur et à `WorkshopItems=`. Les tuiles (`batman_livewater_01`) viennent
  avec le mod.
- LiveWater est **incompatible** avec *LG Extended Plumbing* et *LG Connect To Water Supply* : tous deux changent la
  source d'eau des points d'eau, et deux mods de ce genre rempliraient deux fois le même évier. LiveWater couvre ce
  qu'ils font.
- L'option sandbox *Corriger les lave-linge raccordés* (activée par défaut) corrige un défaut du jeu sur serveur : les
  lave-linge alimentés par une arrivée d'eau apparaissent raccordés aux joueurs et s'arrêtent quand ils n'ont plus
  d'eau.
- Les bornes sandbox de la minuterie des arroseurs sont vérifiées par le serveur (*Cet intervalle n'est pas permis sur
  ce serveur.*).
- Retirer le mod est une action d'administrateur : voir [Retirer le mod](07-retirer-le-mod.md).

[Accueil](Home.md)

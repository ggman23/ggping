# Cahier des charges — Outil adversaires CVTT Vaires

Outil à lancer sur un PC Windows qui récupère sur Internet les informations sur les
adversaires des 7 équipes du **CVTT Vaires** (club FFTT n° **08770250**) et génère une
**page HTML statique** consultable dans le navigateur (et partageable par mail/WhatsApp).

## Contraintes

- Pas d'identifiants API FFTT (Smartping) : on passe par des sites publics qui exposent
  les données FFTT — **pingpocket.fr** en source principale, **pongiste.fr** / **fftt.com**
  en secours.
- Récupération polie : cache disque + temporisation entre les requêtes.
- Windows + Python, lancement par double-clic sur un `.bat` (même principe que le projet jarvis).
- Page **statique** : le `.bat` récupère les données, génère le HTML et l'ouvre. On relance
  après chaque journée pour mettre à jour.

## Équipes de Vaires (phase 1 2026-2027)

- Vaires 1 à Vaires 6 : championnat par équipes **masculin**, le **vendredi** soir
  (départemental 77 ; démarrage J1 le vendredi 25/09/2026).
- Vaires 1 féminine : championnat **féminin régional** (poules mélangeant 77 et 94),
  le **samedi**.
- Les équipes sont **détectées automatiquement** à partir du numéro de club (l'outil doit
  marcher en phase 2 et les saisons suivantes sans modification).
- Les filles jouent aussi en équipes masculines le vendredi.

## Pour chaque club adverse (clubs des poules des équipes de Vaires)

### Effectif
- Exclure les **licences loisir** (promotionnelles).
- Les joueurs **non renouvelés** sont affichés dans une **section repliée** séparée
  (en début de saison beaucoup renouvellent en octobre).
- Garder les féminines dans l'effectif (elles peuvent jouer en masculin).
- Colonnes : nom, **catégorie d'âge**, **classement officiel** (points de la phase),
  **classement mensuel**, **meilleur classement de l'historique + année** de ce meilleur
  classement (pas d'autre colonne, pour rester lisible).

### Qui a joué dans quelle équipe
- Pour **toutes** les équipes masculines du club (national, régional, départemental) :
  qui a joué dans quelle équipe, à quelle journée (ex. toto → Lognes 18, titi → Lognes 19).
  Le régional se joue le samedi, le départemental le vendredi.
- Le championnat **féminin** est traité à part (uniquement pour Vaires 1 F).
- On ignore coupes et Championnat de Paris.

### Règles de brûlage appliquées (validées)
1. **Brûlage** : un joueur qui a disputé 2 rencontres (dans la même phase) dans des équipes
   de numéro plus petit (plus fortes) ne peut plus jouer dans une équipe de numéro plus
   grand. Ex. : 1× en équipe 16 et 1× en équipe 18 → ne peut plus jouer en 19 et au-delà.
   Formule : le joueur peut jouer en équipe N tant qu'il a moins de 2 matchs dans des
   équipes de numéro < N.
2. **Un seul match par journée** (la J1 régionale du samedi et la J1 départementale du
   vendredi comptent comme la même journée).
3. **Règle de la J2** : à la 2e journée, une équipe ne peut aligner qu'**un seul** joueur
   ayant joué la J1 dans une équipe de numéro plus petit.

### Analyse de chaque rencontre contre Vaires
- Joueurs **qualifiés** pour l'équipe adverse.
- **Renforts possibles** : joueurs des équipes plus fortes non brûlés, triés par points.
- Joueurs **brûlés** (ne peuvent pas jouer contre Vaires).
- **Composition probable** (clairement indiquée comme une estimation).

## Calendrier
- Onglet **Récapitulatif** regroupé **par semaine** (hommes le vendredi, filles le samedi) :
  où joue chacune des 7 équipes de Vaires.
- Planning de la phase par équipe de Vaires.
- Pour chaque rencontre : domicile/extérieur, **adresse de la salle** (surtout pour les
  matchs à l'extérieur), horaire, date réelle si avancée/reportée, score.
- **Classement de la poule**.

## Interface
- Onglets : Récapitulatif, Vaires 1 … Vaires 6, Vaires 1 F.
- Dans chaque onglet équipe : liens vers chaque club de la poule → effectif + brûlage +
  analyse de la rencontre contre Vaires.

## Dépôt
- Code dans le dépôt GitHub `ggman23/ggping`.

## Précisions constatées lors de la réalisation

- Source : pages publiques de pingpocket.fr. Le site sature au-delà de 2-3 requêtes
  simultanées : l'outil reste à 2 requêtes, avec cache disque (premier lancement ~40 min,
  lancements suivants de quelques secondes à ~15 min selon ce qui a changé).
- La poule féminine est la « D1 Championnat Féminin 77/94 » (équipes de 3 joueuses).
- Les horaires des rencontres ne sont pas publiés : seules les dates sont affichées.
- L'historique n'est pas lu pour les joueurs restés à 500 points (le minimum) qui n'ont pas
  joué de la phase : leur meilleur classement est affiché « — ».
- Le meilleur classement est le maximum des points officiels de début de phase (janvier et
  juillet) sur tout l'historique ; il est mis en évidence quand il dépasse d'au moins
  2 classements le classement actuel.

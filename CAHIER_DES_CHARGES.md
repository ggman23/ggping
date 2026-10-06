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
- Les horaires des rencontres viennent de l'API publique de la FFTT.
- L'historique n'est pas lu pour les joueurs restés à 500 points (le minimum) qui n'ont pas
  joué de la phase : leur meilleur classement est affiché « — ».
- Le meilleur classement est le maximum des points officiels de début de phase (janvier et
  juillet) sur tout l'historique ; il est mis en évidence quand il dépasse d'au moins
  2 classements le classement actuel.

## Sources de données (mise à jour du 04/10/2026)

- pingpocket.fr a commencé à bloquer les requêtes automatiques (protection anti-robots
  Cloudflare, erreurs 502). La structure des deux pages vient désormais de l'**API publique de
  la FFTT** (apiv2.fftt.com, celle des pages de consultation de monclub.fftt.com, sans
  identifiant) : équipes, poules, calendrier avec horaires, scores, classements, feuilles de
  match et parties.
- Les données des licenciés (effectifs complets, catégories, historique des classements,
  adresses des salles) ne sont pas publiques dans cette API : elles restent lues sur pingpocket
  quand il répond ; sinon la page indique que l'effectif est limité aux joueurs déjà alignés.

## Page « Effectif de Vaires » (06/10/2026)

- Option 3 du menu. Vue club : tous les réinscrits, l'équipe jouée à chaque journée, et pour
  chaque équipe de Vaires « ✓ » (peut jouer) ou « brûlé ». Un onglet par équipe : joueurs
  possibles (avec alerte quand il ne reste qu'un match possible en équipe plus forte) et joueurs
  brûlés. Un onglet « Non réinscrits · loisirs ».
- La liste des licenciés est revérifiée à chaque lancement (pingpocket.fr) ; les réinscrits
  depuis le lancement précédent sont marqués « nouveau ». Si pingpocket ne répond pas, la
  dernière liste obtenue est reprise (avec sa date), sinon seuls les joueurs déjà alignés
  apparaissent.
- Championnats masculin et féminin indépendants : une joueuse alignée en masculin y est traitée
  comme les garçons (2 matchs en équipe 4 → brûlée pour 5 et 6, disponible de 1 à 4) ; ses
  matchs en Vaires 1 F ne comptent pas pour le masculin. Une seule équipe féminine : pas de
  brûlage en féminin.

## Liste complète des licenciés malgré le blocage de pingpocket (06/10/2026)

- Demande : obtenir la liste complète des joueurs de Vaires même quand pingpocket bloque
  l'outil (piste évoquée : Playwright).
- Choix retenu : **ne pas contourner la protection anti-robots** (pas de navigateur automatisé
  déguisé, pas de résolution de vérification). L'outil d'origine fait sous ChatGPT applique la
  même règle (arrêt sur 401/403/429 ou vérification).
- À la place :
  - requêtes plus espacées vers pingpocket : une page toutes les 4 secondes au plus, quel que
    soit le nombre de requêtes simultanées ; au plus 150 historiques téléchargés par lancement
    (joueurs alignés d'abord), les autres aux lancements suivants ;
  - **dossier `import\`** : l'utilisateur enregistre depuis son navigateur (Ctrl+S, « Page Web,
    complète » ou .mhtml) les listes de licenciés du club (par catégorie d'âge et par licences à
    jour, indispensables ; par classement officiel, facultatif). L'outil y reconnaît chaque
    écran de liste (titre de l'écran, numéro du club), même si une page en contient plusieurs ou
    concerne plusieurs clubs ;
  - pour chaque liste, la version la plus récente l'emporte : lue sur le site au lancement,
    page enregistrée (date du fichier) ou dernière copie en cache. La page Effectif indique la
    provenance et la date de la liste, avec les liens et le mode d'emploi pour l'actualiser ;
  - le même dossier complète les effectifs des clubs adverses sur la page adversaires.
- Les pages enregistrées contiennent des données personnelles : le dossier est exclu du dépôt.

## Page « Classement virtuel » (06/10/2026)

- Demande : un vrai classement virtuel des joueurs du club, qui tienne compte de toutes les
  compétitions et pas seulement du championnat par équipes (exemple : Emily CHOLLET a joué le
  Top Jeune départemental). Option 4 du menu.
- Source : l'API publique de la FFTT donne toutes les parties de la saison d'un joueur
  (`/api/games`, filtrées par licence), avec les points officiels de la phase des deux joueurs,
  et chaque compétition porte son coefficient (`/api/contests/{id}` : championnat par équipes 1,
  critérium fédéral 1,5, championnat jeunes par équipes 77 0,75, Top Jeune départemental 0,5).
- Calcul : points virtuels = points officiels de la phase + somme, sur les parties de simple
  jouées depuis le début de la phase, de barème FFTT × coefficient. Doubles, victoires par
  forfait et parties marquées « non comptées » écartées.
- Vérification : pour les 33 joueurs alignés en championnat au 06/10/2026, points officiels et
  points du championnat identiques à ceux de la page Résultats (calculés depuis les feuilles de
  match). Les coefficients n'ont pas pu être confrontés aux points mensuels publiés (aucun
  classement mensuel de la phase n'intégrait encore de partie) ; les historiques des saisons
  passées sont incomplets dans l'API et ne permettent pas ce contrôle.
- Joueurs : liste des licenciés (réinscrits hors licences loisir) lue sur pingpocket ou dans le
  dossier `import\`, plus les joueurs alignés en championnat. Sans liste, les joueurs qui ne font
  que des compétitions individuelles n'apparaissent pas (la page le signale).

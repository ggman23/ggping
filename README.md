# Adversaires CVTT Vaires

Outil qui récupère sur Internet les informations sur les adversaires des équipes du
**CVTT Vaires** (club FFTT 08770250) et génère une page HTML consultable dans le navigateur :

- **Récapitulatif par semaine** : où jouent les 7 équipes de Vaires (date, domicile/extérieur,
  adresse de la salle avec lien vers le plan, score) ;
- un **onglet par équipe** (Vaires 1 à 6, Vaires 1 F) : calendrier, classement de la poule,
  et pour chaque adversaire une fiche avec l'**effectif du club** (catégorie, classement
  officiel, mensuel, meilleur classement et son année), **qui a joué dans quelle équipe**,
  les **brûlés**, les **renforts possibles** et une **composition probable**.

Une seconde page, **Résultats des joueurs de Vaires** (`sortie\resultats_vaires.html` et
`sortie\resultats_vaires.xlsx`), donne pour chaque journée les joueurs alignés dans les
7 équipes : équipe, points officiels, points gagnés/perdus (barème FFTT), victoires, meilleure
victoire du jour, classement virtuel (points officiels + total depuis la J1) et total depuis la
J1. L'onglet Cumul donne, par joueur, les points de chaque journée, le total et le classement
virtuel. Le tableau se trie en cliquant sur les
titres de colonnes ; un clic sur un joueur affiche le détail de ses parties. Le classeur Excel
a un onglet par journée, un onglet Cumul et l'onglet Parties (une ligne par partie, à partir
de laquelle tout est calculé par formules). Les équipes masculines (vendredi) et l'équipe
féminine (samedi) sont prises en compte : une joueuse qui a joué les deux rencontres d'une même
journée apparaît dans les deux équipes, et ses points se cumulent.

Avec elle, la page **Feuilles de match** (`sortie\rencontres_vaires.html`) détaille chaque
rencontre des équipes de Vaires, journée par journée : le score, puis chaque partie dans l'ordre
de la feuille (lettres A, B, C, D / W, X, Y, Z), les joueurs et leurs points, le score de chaque
manche (11-7, 8-11…, Vaires toujours en premier, vert = manche gagnée), le score de la rencontre
après chaque partie et le bilan de chaque joueur. Sur un téléphone, les manches passent sous la
partie ; des boutons filtrent une équipe.

Sur la copie Netlify, des **statistiques de visite** (pages vues, visiteurs, documents ouverts,
téléchargés, partagés) peuvent être activées avec un compte gratuit GoatCounter : voir
PUBLICATION.md.

La page **Classements des poules** (`sortie\classements_vaires.html`, faite avec la page des
adversaires) montre la poule de chaque équipe de Vaires (points, joués, victoires, nuls, défaites,
parties gagnées – perdues), la ligne de Vaires en rouge, comme l'image du même nom.

Les résultats viennent de l'**API publique de la FFTT** (celle des pages de consultation de
monclub.fftt.com, lisible sans identifiant) : quelques secondes suffisent.

Une troisième page, **Effectif de Vaires** (`sortie\effectif_vaires.html`), donne la vue du
club pour les capitaines : tous les joueurs réinscrits, les équipes dans lesquelles ils ont joué à
chaque journée, et pour chaque équipe s'ils peuvent encore y jouer ou s'ils sont brûlés ; un
onglet par équipe liste les joueurs possibles et les joueurs brûlés ; un dernier onglet liste les
non réinscrits et les licences loisir. La liste des licenciés est revérifiée à chaque lancement
(les nouveaux réinscrits sont signalés). Championnats masculin et féminin sont indépendants :
une joueuse alignée en masculin y est traitée comme les garçons, ses matchs en équipe féminine
ne comptent pas pour le brûlage masculin.

Une quatrième page, **Classement virtuel** (`sortie\classement_virtuel.html`), donne le vrai
classement virtuel de chaque joueur du club : points officiels de la phase + points gagnés ou
perdus **dans toutes les compétitions** (championnat par équipes, critérium fédéral, tournois,
compétitions jeunes...), pas seulement en championnat. Les parties viennent de l'API publique de
la FFTT, qui donne pour chaque partie les points officiels des deux joueurs et le coefficient de
la compétition (1 pour le championnat, 1,5 pour le critérium, 0,5 pour le Top Jeune
départemental...) : points = barème FFTT × coefficient. Les doubles, les victoires par forfait et
les parties non comptées sont écartés. Un clic sur un joueur affiche le détail de ses parties.
Deux autres onglets classent les parties elles-mêmes : **Meilleures perfs** (les victoires qui ont
rapporté le plus de points, avec l'écart de classement) et **Pires contres** (les défaites qui ont
coûté le plus), toutes compétitions confondues, en entier ou une seule ligne par joueur.
Pour avoir tous les joueurs (y compris les jeunes qui ne jouent pas en championnat), la liste des
licenciés est lue sur pingpocket ou dans le dossier `import\` (voir plus bas) ; sinon seuls les
joueurs alignés en championnat apparaissent.

Le détail des besoins et des règles de brûlage appliquées est dans
[CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

La page adversaires combine deux sources :

- l'**API publique de la FFTT** pour tout ce qui concerne la compétition : équipes, poules,
  calendrier **avec les horaires**, scores, classements, nom des salles et compositions de toutes
  les équipes des clubs adverses (donc le brûlage) ;
- **pingpocket.fr** pour les compléments que l'API ne publie pas : effectifs complets (joueurs
  pas encore alignés, licences loisir écartées, renouvellements), catégories d'âge, classement
  mensuel, meilleur classement de l'historique et adresses des salles.

Si pingpocket ne répond pas (panne ou protection anti-robots), la page est quand même générée :
les effectifs se limitent alors aux joueurs déjà alignés, et une note l'indique. Les données
sont gardées dans le dossier `cache\` : le premier lancement complet peut être long, les suivants
ne retéléchargent que ce qui a pu changer :

| Donnée | Relue |
|---|---|
| Listes des rencontres (nouveaux résultats) | à chaque lancement (si plus de 1 à 3 h) |
| Feuille de match pas encore saisie | à chaque lancement, jusqu'à ce qu'elle soit saisie |
| Feuille de match saisie | relue pendant 10 jours (corrections), puis gardée |
| Parties de chaque joueur (classement virtuel) | à chaque lancement (si plus de 1 h) |
| Liste des licenciés de Vaires (pingpocket) | à chaque lancement (si plus de 1 h) |
| Listes des licenciés des clubs adverses (pingpocket) | une fois par jour |
| Adresses des salles (pingpocket) | une fois par mois |
| Historiques (meilleur classement, pingpocket) | une fois par phase (150 par lancement au plus) |

Un résultat nouveau n'est donc jamais manqué parce qu'un lancement a eu lieu la veille ; le bilan
des vérifications, à la fin, le confirme équipe par équipe. L'outil reste discret avec pingpocket : une page toutes
les 4 secondes au plus, 150 historiques au plus par lancement (les autres aux lancements
suivants ; un historique lu reste valable toute la phase, le meilleur classement ne changeant qu'en
janvier et juillet), arrêt immédiat en cas de vérification anti-robot. Il ne contourne aucune protection.

## Liste des licenciés quand pingpocket bloque l'outil : le dossier `import\`

Les listes de licenciés (non réinscrits, licences loisir, catégories) ne sont publiées que par
pingpocket. Quand le site refuse les requêtes de l'outil, on peut les lui fournir à la main :

1. ouvrir dans son navigateur, normalement, les listes du club :
   [par catégorie d'âge](https://www.pingpocket.fr/?page=app%2Ffftt%2Fclubs%2F08770250%2Flicencies%3FSORT%3DCATEGORY)
   et [par licences à jour](https://www.pingpocket.fr/?page=app%2Ffftt%2Fclubs%2F08770250%2Flicencies%3FSORT%3DLICENCE_STATE)
   (indispensables), [par classement officiel](https://www.pingpocket.fr/?page=app%2Ffftt%2Fclubs%2F08770250%2Flicencies%3FSORT%3DOFFICIAL_RANK)
   (facultatif) ;
2. les enregistrer (**Ctrl+S**, type **« Page Web, complète »** ou « fichier unique .mhtml ») dans
   le dossier `import\` de l'outil — un fichier par liste, ou un seul après avoir ouvert les
   listes à la suite ;
3. relancer `lancer.bat` (option 3 pour l'effectif, 4 pour le classement virtuel).

L'outil retient pour chaque liste la version la plus récente (site, pages enregistrées ou copie
en cache) et la page indique laquelle est utilisée et sa date. Cela marche aussi pour les clubs
adverses (remplacer 08770250 par le numéro du club). Le mode d'emploi est aussi dans
`import\LISEZ-MOI.txt`. Les pages enregistrées ne sont jamais envoyées sur GitHub.

## Images à partager (téléphone)

Chaque option du menu produit aussi des **images PNG** des tableaux, faites pour être lues sur un
téléphone et partagées dans les groupes du club (dossier `sortie\images\` sur le PC, section
« Images à partager » du site) :

- **adversaires** : la prochaine journée (équipes, dates, adversaires, lieux) et, pour chaque
  équipe de Vaires, le prochain adversaire avec sa composition probable, ses renforts possibles et
  les 8 mieux classés qui n'ont pas encore joué ;
- **résultats** : la dernière journée (triée par points gagnés sur la journée) et le cumul (trié
  par points gagnés au total) ;
- **feuilles de match** : une image par rencontre de la dernière journée (chaque partie, le score
  des manches, le bilan des joueurs) ;
- **récapitulatif de la journée** (`recap_J3.png`) : la copie de l'image du club faite avec
  Excalidraw (mêmes polices Lilita One et Excalifont, mêmes couleurs, même mise en page) : pour
  chaque équipe, le résultat et le score en points-parties (domicile – extérieur), les victoires et
  défaites de chaque joueur (astérisque orange = perf : victoire contre un joueur qui a plus de
  points) et des doubles ; le top 5 des perfs ; la place de la photo en haut. Déposer
  `import\photo_J3.jpg` (et une fois pour toutes `logo_gauche.png`, `logo_droite.png`) pour que
  l'outil la complète : voir `import\LISEZ-MOI.txt` (et `surnoms.txt` pour les noms affichés) ;
- **classements des poules** (`classements_poules.png`, avec la page adversaires) : la poule de
  chaque équipe de Vaires (# ÉQUIPE PTS J V N D, la ligne de Vaires en rouge), deux cartes par
  rangée sur fond sombre, « après la journée 03 » ; le logo du club est pris dans
  `import\logo_club.png` (sinon `logo_gauche.png`, sinon un écusson CVTT) ;
- **effectif** : tout le club (équipes jouées à chaque journée, coche verte = peut jouer,
  flamme = brûlé) et, pour chaque équipe masculine de la 2 à la 6, ses joueurs brûlés ;
- **classement virtuel** : le classement complet.

Largeur 1080 points, texte agrandi, colonnes de même largeur (le nom est abrégé « NOM P. » s'il est
trop long), 25 lignes au plus par image (un long tableau donne plusieurs images 1/2, 2/2) pour
qu'elles restent nettes une fois envoyées par une messagerie. Un tableau découpé est aussi donné en
plus en une seule image verticale (`..._complet.png`, « image unique » sur le site), avec les titres
des colonnes répétés aux mêmes endroits. Elle se lit très bien sur le site en faisant défiler ; une
messagerie peut la réduire : l'envoyer plutôt comme document (ou en HD). Mêmes images sur le PC et
en ligne (police fournie avec l'outil : Liberation Sans, licence SIL OFL).

## Vérifications : tous les résultats ont-ils été récupérés ?

Les résultats sont saisis par les clubs, souvent dans les 48 h après la rencontre : un lancement
le lundi peut tomber avant que tout soit saisi. Chaque option du menu vérifie donc, pour chaque
journée déjà jouée, que le résultat de **chaque équipe** a bien été récupéré : score et feuille de
match (compositions). Une rencontre peut être :

- complète (ou perdue par forfait : pas de feuille à attendre) ;
- « résultat non saisi » ;
- « score saisi, feuille de match pas encore saisie » (les brûlages ne peuvent pas en tenir compte) ;
- « non récupérée » (l'API de la FFTT n'a pas répondu) ;
- jouée le jour même : résultat pas encore attendu, non compté comme manquant.

Où le voir :

- **dans la fenêtre**, à la fin de chaque page, puis un **bilan des vérifications** juste avant
  « Appuyez sur une touche » ; pour les adversaires, une ligne par club, par exemple
  `OK E. P. DE LOGNES (21 équipes) : J1 21/21 | J2 21/21 | J3 21/21`, et le détail de chaque
  résultat manquant ;
- **dans la page adversaires** : un bandeau sur le récapitulatif, un onglet **Vérifications**
  (par journée, par club et liste des rencontres manquantes) et une alerte dans la fiche du club
  concerné (ses brûlages et sa composition probable peuvent être incomplets) ;
- **dans les pages résultats, effectif et classement virtuel** : un bandeau vert si les 7 équipes
  de Vaires ont tous leurs résultats, rouge avec la liste sinon. Le classement virtuel signale en
  plus les joueurs dont les parties n'ont pas pu être lues, et les parties de championnat pas
  encore propagées dans la liste des parties d'un joueur. Les compétitions individuelles
  (critérium, tournois) ne peuvent pas être vérifiées : l'outil ne sait pas à l'avance qui y a
  participé.

Les équipes exemptes ne sont pas attendues. En cas de manque, il suffit de relancer plus tard :
les rencontres incomplètes sont retéléchargées à chaque lancement.

## Sur téléphone

Les mises à jour peuvent aussi être lancées depuis un téléphone : GitHub génère les pages sur ses
serveurs et les publie, chiffrées par un mot de passe, sur **https://ggman23.github.io/ggping/**
(bouton « Lancer la mise à jour » sur la page d'accueil, Excel téléchargeable, mises à jour
automatiques les lendemains de journée). Pour que le site donne exactement les mêmes pages que le PC,
le PC y envoie, chiffrés, son dossier `import` et ses pages de pingpocket.fr après chaque lancement
(option 7 du menu pour le réglage). Copie de secours sur **https://ggping.netlify.app/** après
chaque mise à jour : la page des adversaires pour tout le club, l'**espace club** dans **/club/**
(menu des pages, de l'Excel et des images, à regarder et télécharger, avec un mot de passe) et dans
**/gg/** la copie du site avec un autre mot de passe (pour les capitaines). Les journées passées
restent consultables dans les **archives** (pages, Excel et images telles qu'à la veille de la
journée suivante). Mise en place :
[PUBLICATION.md](PUBLICATION.md).

## Installation (Windows)

1. Installer **Python 3.10 ou plus** depuis <https://www.python.org/downloads/> — cocher
   **« Add python.exe to PATH »**.
2. Télécharger ce projet (bouton *Code → Download ZIP* sur GitHub) et le décompresser.
3. Double-cliquer sur **`lancer.bat`** : le premier lancement installe tout, puis un menu
   propose :
   1. Adversaires (effectifs, brûlages, calendrier) ;
   2. Résultats des joueurs de Vaires (page + Excel) et feuilles de match — rapide, moins d'une minute ;
   3. Effectif de Vaires : brûlages par joueur et par équipe — rapide ;
   4. Classement virtuel du club, toutes compétitions — rapide ;
   5. tout : les quatre pages ;
   6. la page de démonstration ;
   7. le lien avec le téléphone (réglage, puis envoi automatique des données au site) ;
   8. les adversaires en lisant d'un coup tous les meilleurs classements manquants (long : une
      page toutes les 4 secondes, environ 1 h la première fois ; à faire une fois, ensuite les
      lancements normaux suffisent) ;
   9. refaire les quatre pages et les images **sans rien télécharger** (30 secondes) : avec les
      données du dernier lancement, par exemple après une nouvelle version de l'outil. Rien n'est
      envoyé au site. Un résultat paru depuis le dernier lancement n'y est pas : pour les
      nouveaux résultats, prendre les options 1 à 5 ;
   0. quitter.

   Les pages s'ouvrent dans le navigateur et sont enregistrées dans le dossier `sortie\`.

Relancer `lancer.bat` après chaque journée pour mettre à jour les données (les feuilles de
match sont en général saisies dans les 48 h après la rencontre).

La page `sortie\vaires.html` est un fichier autonome : on peut l'envoyer par mail ou WhatsApp
aux capitaines, elle s'ouvre sans Internet.

Options (dans une invite de commandes, dans le dossier du projet) :

- `lancer.bat --adversaires`, `--resultats`, `--effectif`, `--virtuel` : lance directement une page, sans menu ;
- `--hors-ligne` (à ajouter) : régénère sans rien télécharger (cache uniquement, rien n'est envoyé au site) ;
- `lancer.bat --demo` : page de démonstration avec des données fictives.

## Lancement manuel (Windows/Mac/Linux)

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate     Mac/Linux : source .venv/bin/activate
pip install -r requirements.txt
python -m ttvaires --demo
python -m pytest
```

## Structure

```
ttvaires/
  __main__.py    Point d'entrée (python -m ttvaires)
  adversaires.py Données de la page adversaires (API FFTT + compléments pingpocket)
  pingpocket.py  Compléments lus sur pingpocket.fr (licenciés, salles, historiques) et
                 pages enregistrées depuis un navigateur (dossier import)
  reseau.py      Téléchargements : cache disque, requêtes parallèles, nouvelles tentatives
  brulage.py     Règles de brûlage et analyse de chaque rencontre
  fftt.py        Accès à l'API publique de la FFTT (rencontres, feuilles de match)
  resultats.py   Résultats des joueurs de Vaires : points virtuels, page et classeur Excel
  effectif.py    Effectif de Vaires : équipes jouées, brûlage par joueur et par équipe
  virtuel.py     Classement virtuel : parties de toutes les compétitions, barème × coefficient
  verifications.py  Vérifications : résultats de chaque équipe récupérés pour chaque journée
  images.py      Images PNG des tableaux (lisibles sur téléphone)
  polices/       Polices des images (Liberation Sans, Lilita One, Excalifont : SIL OFL ; DejaVu Sans : licence libre)
  publier.py     Publication du site pour téléphone : pages chiffrées, page d'accueil
  synchro.py     Données du PC (import, pages pingpocket) envoyées chiffrées pour le site
  gabarit_accueil.html, gabarit_verrou.html  Accueil du site et page protégée par mot de passe
.github/workflows/mise-a-jour.yml  Mise à jour en ligne (GitHub Actions + GitHub Pages)
  rendu.py       Génération de la page HTML (un seul fichier)
  gabarit.html   Mise en page de la page adversaires (HTML/CSS/JavaScript)
  gabarit_resultats.html  Mise en page de la page résultats
  gabarit_rencontres.html Mise en page de la page feuilles de match
  gabarit_classements.html Mise en page de la page classements des poules
  classements.py Image des classements des poules
  gabarit_effectif.html   Mise en page de la page effectif
  gabarit_virtuel.html    Mise en page de la page classement virtuel
  demo.py        Données fictives pour tester sans Internet
tests/           Tests (brûlage, lecture des pages, points virtuels)
import/          Listes de licenciés enregistrées depuis le navigateur (voir LISEZ-MOI.txt)
```

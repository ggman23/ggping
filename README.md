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
ne retéléchargent que ce qui a pu changer. L'outil reste discret avec pingpocket : une page toutes
les 4 secondes au plus, 150 historiques au plus par lancement (les autres aux lancements
suivants), arrêt immédiat en cas de vérification anti-robot. Il ne contourne aucune protection.

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

## Installation (Windows)

1. Installer **Python 3.10 ou plus** depuis <https://www.python.org/downloads/> — cocher
   **« Add python.exe to PATH »**.
2. Télécharger ce projet (bouton *Code → Download ZIP* sur GitHub) et le décompresser.
3. Double-cliquer sur **`lancer.bat`** : le premier lancement installe tout, puis un menu
   propose :
   1. Adversaires (effectifs, brûlages, calendrier) ;
   2. Résultats des joueurs de Vaires (page + Excel) — rapide, moins d'une minute ;
   3. Effectif de Vaires : brûlages par joueur et par équipe — rapide ;
   4. Classement virtuel du club, toutes compétitions — rapide ;
   5. tout : les quatre pages ;
   6. la page de démonstration.

   Les pages s'ouvrent dans le navigateur et sont enregistrées dans le dossier `sortie\`.

Relancer `lancer.bat` après chaque journée pour mettre à jour les données (les feuilles de
match sont en général saisies dans les 48 h après la rencontre).

La page `sortie\vaires.html` est un fichier autonome : on peut l'envoyer par mail ou WhatsApp
aux capitaines, elle s'ouvre sans Internet.

Options (dans une invite de commandes, dans le dossier du projet) :

- `lancer.bat --adversaires`, `--resultats`, `--effectif`, `--virtuel` : lance directement une page, sans menu ;
- `--hors-ligne` (à ajouter) : régénère sans rien télécharger (cache uniquement) ;
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
  rendu.py       Génération de la page HTML (un seul fichier)
  gabarit.html   Mise en page de la page adversaires (HTML/CSS/JavaScript)
  gabarit_resultats.html  Mise en page de la page résultats
  gabarit_effectif.html   Mise en page de la page effectif
  gabarit_virtuel.html    Mise en page de la page classement virtuel
  demo.py        Données fictives pour tester sans Internet
tests/           Tests (brûlage, lecture des pages, points virtuels)
import/          Listes de licenciés enregistrées depuis le navigateur (voir LISEZ-MOI.txt)
```

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

Le détail des besoins et des règles de brûlage appliquées est dans
[CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

Les données de la page adversaires viennent des pages publiques de **pingpocket.fr** (aucun
identifiant FFTT nécessaire). Si pingpocket bloque les requêtes automatiques (protection
anti-robots), l'outil l'indique et génère quand même la page des résultats. Elles sont gardées dans le dossier `cache\` : le **premier lancement** télécharge
environ 2 000 pages (**40 minutes environ** : le site sature vite, l'outil reste discret).
Les lancements suivants ne retéléchargent que ce qui a pu changer : quelques secondes le même
jour, 10 à 20 minutes d'une semaine sur l'autre (poules, listes de licenciés, nouvelles
feuilles de match).

> Les horaires des rencontres ne sont pas publiés par pingpocket : seules les dates figurent.

## Installation (Windows)

1. Installer **Python 3.10 ou plus** depuis <https://www.python.org/downloads/> — cocher
   **« Add python.exe to PATH »**.
2. Télécharger ce projet (bouton *Code → Download ZIP* sur GitHub) et le décompresser.
3. Double-cliquer sur **`lancer.bat`** : le premier lancement installe tout, puis un menu
   propose :
   1. Adversaires (effectifs, brûlages, calendrier) ;
   2. Résultats des joueurs de Vaires (page + Excel) — rapide, moins d'une minute ;
   3. les deux ;
   4. la page de démonstration.

   Les pages s'ouvrent dans le navigateur et sont enregistrées dans le dossier `sortie\`.

Relancer `lancer.bat` après chaque journée pour mettre à jour les données (les feuilles de
match sont en général saisies dans les 48 h après la rencontre).

La page `sortie\vaires.html` est un fichier autonome : on peut l'envoyer par mail ou WhatsApp
aux capitaines, elle s'ouvre sans Internet.

Options (dans une invite de commandes, dans le dossier du projet) :

- `lancer.bat --adversaires`, `lancer.bat --resultats` : lance directement une page, sans menu ;
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
  pingpocket.py  Lecture des pages pingpocket.fr et assemblage des données
  reseau.py      Téléchargements : cache disque, requêtes parallèles, nouvelles tentatives
  brulage.py     Règles de brûlage et analyse de chaque rencontre
  fftt.py        Accès à l'API publique de la FFTT (rencontres, feuilles de match)
  resultats.py   Résultats des joueurs de Vaires : points virtuels, page et classeur Excel
  rendu.py       Génération de la page HTML (un seul fichier)
  gabarit.html   Mise en page de la page adversaires (HTML/CSS/JavaScript)
  gabarit_resultats.html  Mise en page de la page résultats
  demo.py        Données fictives pour tester sans Internet
tests/           Tests (brûlage, lecture des pages, points virtuels)
```

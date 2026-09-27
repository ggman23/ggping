# Adversaires CVTT Vaires

Outil qui récupère sur Internet les informations sur les adversaires des équipes du
**CVTT Vaires** (club FFTT 08770250) et génère une page HTML consultable dans le navigateur :

- **Récapitulatif par semaine** : où jouent les 7 équipes de Vaires (date, domicile/extérieur,
  adresse de la salle avec lien vers le plan, score) ;
- un **onglet par équipe** (Vaires 1 à 6, Vaires 1 F) : calendrier, classement de la poule,
  et pour chaque adversaire une fiche avec l'**effectif du club** (catégorie, classement
  officiel, mensuel, meilleur classement et son année), **qui a joué dans quelle équipe**,
  les **brûlés**, les **renforts possibles** et une **composition probable**.

Le détail des besoins et des règles de brûlage appliquées est dans
[CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

Les données viennent des pages publiques de **pingpocket.fr** (aucun identifiant FFTT
nécessaire). Elles sont gardées dans le dossier `cache\` : le **premier lancement** télécharge
environ 2 000 pages (**40 minutes environ** : le site sature vite, l'outil reste discret).
Les lancements suivants ne retéléchargent que ce qui a pu changer : quelques secondes le même
jour, 10 à 20 minutes d'une semaine sur l'autre (poules, listes de licenciés, nouvelles
feuilles de match).

> Les horaires des rencontres ne sont pas publiés par pingpocket : seules les dates figurent.

## Installation (Windows)

1. Installer **Python 3.10 ou plus** depuis <https://www.python.org/downloads/> — cocher
   **« Add python.exe to PATH »**.
2. Télécharger ce projet (bouton *Code → Download ZIP* sur GitHub) et le décompresser.
3. Double-cliquer sur **`lancer.bat`** : le premier lancement installe tout, puis la page
   s'ouvre dans le navigateur. Elle est enregistrée dans le dossier `sortie\`.

Relancer `lancer.bat` après chaque journée pour mettre à jour les données (les feuilles de
match sont en général saisies dans les 48 h après la rencontre).

La page `sortie\vaires.html` est un fichier autonome : on peut l'envoyer par mail ou WhatsApp
aux capitaines, elle s'ouvre sans Internet.

Options (dans une invite de commandes, dans le dossier du projet) :

- `lancer.bat --hors-ligne` : régénère la page sans rien télécharger (cache uniquement) ;
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
  rendu.py       Génération de la page HTML (un seul fichier)
  gabarit.html   Mise en page et affichage (HTML/CSS/JavaScript)
  demo.py        Données fictives pour tester sans Internet
tests/           Tests (brûlage, lecture des pages)
```

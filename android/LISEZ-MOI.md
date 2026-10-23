# Application Android CVTT Vaires

Tout sous la main dans une seule application, en quatre onglets (en bas de l'écran) :

| Onglet | Page |
|---|---|
| ⟳ **Mise à jour** | le site GitHub (https://ggman23.github.io/ggping/) : bouton « Lancer la mise à jour », pages, images |
| 🏓 **Club** | l'espace club (https://ggping.netlify.app/club/) |
| 📊 **GoatCounter** | les statistiques GoatCounter (https://ggman23.goatcounter.com/) |
| 📈 **Umami** | les statistiques Umami (https://cloud.umami.is/) |

Chaque onglet garde sa page quand on passe à un autre (une mise à jour en cours continue d'être
suivie). En haut : ⌂ revient à la page de départ de l'onglet, ↻ recharge, ↗ ouvre la page dans le
navigateur ; un appui long sur un onglet le ramène aussi à sa page de départ. Le bouton Retour
d'Android revient à la page précédente de l'onglet.

- **Télécharger** (pages, Excel, images) : enregistré dans *Téléchargements/CVTT Vaires*.
- **Partager** une image : ouvre le menu de partage d'Android (WhatsApp, SMS...).
- Les liens vers d'autres sites (GitHub, cartes des salles...) s'ouvrent dans le navigateur.
- Tes visites depuis l'application ne sont **pas comptées** dans les statistiques du club.

## Installation (une fois)

1. Sur le téléphone, ouvrir :
   **https://github.com/ggman23/ggping/releases/download/application-android/CVTT-Vaires.apk**
2. Ouvrir le fichier téléchargé. La première fois, Android demande d'autoriser l'installation
   d'applications depuis cette source (Chrome ou *Mes fichiers*) : *Paramètres* → autoriser, puis
   revenir et *Installer*. Google Play Protect peut prévenir que l'application est inconnue
   (elle ne vient pas du Play Store) : *Installer quand même*.
3. Dans l'application, une seule fois par onglet : le jeton GitHub (onglet Mise à jour, comme sur
   le téléphone), le mot de passe du club (onglet Club, cocher « Se souvenir »), la connexion à
   GoatCounter et à Umami. L'application garde tout (elle a sa propre mémoire, distincte de Chrome).

## Mises à jour de l'application

L'application est construite par GitHub (workflow *Application Android*) à chaque modification du
dossier `android/`. Pour installer la nouvelle version : retélécharger le même lien et installer par-
dessus : les réglages (jeton, mots de passe, connexions) sont gardés. Les pages, elles, sont toujours
à jour sans réinstaller : l'application affiche les sites en ligne.

La signature de l'application est toujours la même (clé créée à la première construction, gardée
chiffrée avec le mot de passe du site dans la version « application-android » : `cle-apk.chiffre`).
Si le mot de passe du site change, la construction s'arrête plutôt que de créer une autre clé :
supprimer alors `cle-apk.chiffre` de la version, relancer, et désinstaller l'ancienne application
avant d'installer la nouvelle.

## Construction (pour information)

Sans Gradle, avec les seuls outils du SDK Android (build-tools 35, plateforme android-35) :
`android/construire.sh` (voir l'en-tête du script). Code : `src/fr/cvtt/vaires/Principale.java`
(onglets, pages, téléchargements, partage), `Fichiers.java` (fichier partagé), `assets/appli.js`
(ajouté aux pages : téléchargements et partage passent par l'application). Icône :
`python android/icones.py` (à partir du logo du club).

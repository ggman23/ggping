# Application Android CVTT Vaires

Tout sous la main dans une seule application, en six onglets (en bas de l'écran) :

| Onglet | Page |
|---|---|
| ⟳ **Mise à jour** | le site GitHub (https://ggman23.github.io/ggping/) : boutons de mise à jour, pages, images |
| 🏓 **Club** | l'espace club, sur GitHub (https://ggman23.github.io/ggping/club/), sinon Cloudflare, sinon Netlify (voir plus bas) |
| 👑 **Lundi** | l'espace /lundi/ (« Le roi du lundi »), sur GitHub (https://ggman23.github.io/ggping/lundi/), sinon Cloudflare, sinon Netlify |
| 🎯 **Indivs** | les individuels /indivs/ (poules du critérium et forme des adversaires), sur GitHub (https://ggman23.github.io/ggping/indivs/), sinon Cloudflare, sinon Netlify |
| 📊 **Goat** | les statistiques GoatCounter (https://ggman23.goatcounter.com/) |
| 📈 **Umami** | les statistiques Umami (https://cloud.umami.is/, ou ton lien de partage : voir plus bas) |

Chaque onglet garde sa page quand on passe à un autre (une mise à jour en cours continue d'être
suivie). En haut : ⌂ revient à la page de départ de l'onglet, ↻ recharge, ↗ ouvre la page dans le
navigateur ; un appui long sur un onglet le ramène aussi à sa page de départ. Le bouton Retour
d'Android revient à la page précédente de l'onglet.

- **Télécharger** (pages, Excel, images) : enregistré dans *Téléchargements/CVTT Vaires*.
- **Partager** une image : ouvre le menu de partage d'Android (WhatsApp, SMS...).
- Les liens vers d'autres sites (GitHub, cartes des salles...) s'ouvrent dans le navigateur.
- Tes visites depuis l'application ne sont **pas comptées** dans les statistiques du club.

## Onglets Club, Lundi et Indivs : trois copies du même espace

Les espaces club, /lundi/ et /indivs/ sont publiés à trois adresses, avec le même contenu et le même
mot de passe (celui du club). À l'ouverture de l'onglet (et avec ⌂ ou un appui long sur l'onglet),
l'application vérifie l'une après l'autre que la page répond et ouvre la première qui marche :

1. **GitHub** : https://ggman23.github.io/ggping/club/ (ou …/lundi/), mis à jour à chaque mise à jour ;
2. sinon **Cloudflare** : https://ggping-pap.pages.dev/club/ (ou …/lundi/) ;
3. sinon **Netlify** : https://ggping.netlify.app/club/ (ou …/lundi/), mis à jour seulement à la main
   (bouton « Mettre à jour les 3 sites ») ;
4. sinon une page « site indisponible » avec un bouton **Réessayer** (↻ fait la même chose).

La barre du haut dit quelle copie est affichée (« Club · GitHub », « Club · Cloudflare »...) et un
message prévient quand l'application a dû passer à la suivante. Si une page cesse de répondre en
cours de route (site en panne), la même page est ouverte sur la copie suivante.

Chaque copie a sa propre mémoire : le mot de passe du club est demandé **une fois par copie** (une
fois sur GitHub, puis une fois sur Cloudflare le jour où elle sert), cocher « Se souvenir ». Sur une
même copie, Club, Lundi et Indivs partagent le mot de passe retenu : saisi dans l'un, les autres
s'ouvrent seuls. Un lien d'une de ces pages vers une autre (« Espace club » ou « Image de la poule » depuis
/indivs/, « Autres espaces » du club) ouvre le bon onglet.

## Umami sans avoir à se connecter

La connexion « avec Google » ne peut pas être gardée dans l'application : Google refuse les
connexions faites dans une application qui affiche des pages web (comme celle-ci). Le lien s'ouvre
alors dans Chrome, et c'est Chrome qui reste connecté, pas l'application. Deux solutions :

- **Lien de partage Umami (conseillé)** : un tableau de bord en lecture seule, sans connexion.
  1. Dans Chrome (où tu es connecté), sur https://cloud.umami.is : ouvrir les réglages du site
     (*Settings* → *Websites* → *Edit*, ou l'engrenage du site selon la version), partie
     *Share URL* → activer *Enable share URL* → *Save*. Ouvrir le lien affiché (il commence par
     `https://cloud.umami.is/share/`).
  2. Dans Chrome, sur cette page : ⋮ → *Partager* → **CVTT Vaires**. L'application l'enregistre :
     l'onglet Umami s'ouvre désormais directement sur ces statistiques.
  Ce lien est secret (il n'est écrit nulle part dans le dépôt) : quiconque l'a voit les
  statistiques, sans pouvoir rien modifier. On peut le désactiver dans Umami à tout moment. Pour
  revenir à la page de connexion d'Umami : appui long sur ⌂ dans l'onglet Umami.
- **Umami dans Chrome** : ↗ ouvre l'onglet dans Chrome, qui garde la connexion Google.

Un lien vers l'un des sites de l'application (club, site GitHub, GoatCounter) partagé de la même
façon avec « CVTT Vaires » s'ouvre aussi dans son onglet.

## Installation (une fois)

1. Sur le téléphone, ouvrir :
   **https://github.com/ggman23/ggping/releases/download/application-android/CVTT-Vaires.apk**
2. Ouvrir le fichier téléchargé. La première fois, Android demande d'autoriser l'installation
   d'applications depuis cette source (Chrome ou *Mes fichiers*) : *Paramètres* → autoriser, puis
   revenir et *Installer*. Google Play Protect peut prévenir que l'application est inconnue
   (elle ne vient pas du Play Store) : *Installer quand même*.
3. Dans l'application, une seule fois par onglet : le jeton GitHub (onglet Mise à jour, comme sur
   le téléphone), le mot de passe du club (onglet Club, cocher « Se souvenir » ; une fois par copie,
   voir plus haut), la connexion à GoatCounter, et pour Umami le lien de partage (voir plus haut).
   L'application garde tout (elle a sa propre mémoire, distincte de Chrome).

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
(onglets, copies du club, page d'erreur, téléchargements, partage), `Fichiers.java` (fichier partagé), `assets/appli.js`
(ajouté aux pages : téléchargements et partage passent par l'application). Icône :
`python android/icones.py` (à partir du logo du club).

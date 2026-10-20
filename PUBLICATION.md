# Lancer les mises à jour depuis un téléphone

Les pages sont générées sur les serveurs de GitHub (GitHub Actions) et publiées sur un site
(GitHub Pages), consultable et actualisable depuis un téléphone :

**https://ggman23.github.io/ggping/**

- La page d'accueil liste les pages (adversaires, résultats, Excel, feuilles de match, effectif,
  classement virtuel)
  avec leur date et le bilan des vérifications, et propose un bouton **« Lancer la mise à jour »**.
- Chaque page s'**ouvre** dans le navigateur ou se **télécharge** ; « Tout télécharger » récupère
  les pages HTML, l'Excel et toutes les images dans « Téléchargements » : ce sont exactement
  les fichiers du dossier `sortie` du PC (mêmes noms), lisibles sans connexion et sans mot de passe.
- Section **« Images à partager »** : chaque image se voit en grand (« Voir »), se télécharge, et
  peut être envoyée directement depuis le téléphone (« Partager » : WhatsApp, SMS…).
- Les pages sont **chiffrées** : il faut le mot de passe du club pour les lire (cochez « Se
  souvenir sur cet appareil » pour ne le taper qu'une fois). Le site est public, mais sans le mot
  de passe on n'y voit aucun nom de joueur ; il n'est pas référencé par les moteurs de recherche.
- Mises à jour automatiques : samedi, dimanche, lundi et mardi vers 8 h (lendemains de journée),
  et après chaque lancement de `lancer.bat` sur le PC.
- Gratuit (dépôt public : GitHub Actions et GitHub Pages sans frais).

## Même résultat sur le PC et sur le téléphone

pingpocket.fr refuse les serveurs de GitHub, et le dossier `import` n'existe que sur le PC. Pour
que la mise à jour en ligne produise **exactement les mêmes pages** que `lancer.bat`, le PC envoie
ses données sur GitHub après chaque lancement :

- les fichiers du dossier `import` (listes des licenciés enregistrées depuis le navigateur ; pour le
  récapitulatif de la journée : photos `photo_J*.jpg`, logos `logo_*.png` et `surnoms.txt`, une photo
  lourde étant réduite) ;
- les pages de pingpocket.fr gardées en cache (effectifs complets des clubs, catégories, salles,
  historiques des classements) et l'état de la page effectif (joueurs « nouveaux ») ;

le tout **chiffré avec le mot de passe du site** (un seul fichier d'environ 2 Mo, plus les photos, remplacé à
chaque envoi, déposé dans la version « Données du PC » du dépôt). Puis il lance la mise à jour du
site : 5 à 10 minutes plus tard, le site affiche les mêmes pages que le PC.

En ligne, l'outil reprend ces fichiers avec leur date d'origine et n'interroge pas pingpocket.fr ;
les résultats des rencontres, eux, sont relus en direct sur l'API de la FFTT. Une mise à jour
lancée du téléphone (ou automatique) donne donc les mêmes pages que le PC, avec les derniers
résultats. Seuls les effectifs et historiques de pingpocket ont la fraîcheur du dernier lancement
sur le PC (la page Effectif indique « liste lue sur pingpocket.fr par le PC le … »).

Contrôle fait le 18/10/2026 : un lancement « PC » puis une mise à jour « en ligne » à partir des
données envoyées ont produit des données identiques pour les quatre pages et le même contenu
Excel.

## Mise en place (une seule fois)

Sur github.com, connecté avec le compte propriétaire du dépôt `ggman23/ggping` (dans le
navigateur du téléphone, choisir « Version pour ordinateur » si un menu n'apparaît pas) :

1. **Activer le site** : dépôt → *Settings* → *Pages* → *Build and deployment* → *Source* :
   **GitHub Actions**.
2. **Choisir le mot de passe du club** : dépôt → *Settings* → *Secrets and variables* →
   *Actions* → *New repository secret* :
   - *Name* : `MOT_DE_PASSE_SITE`
   - *Secret* : le mot de passe (au moins 12 caractères, par exemple trois mots et un chiffre).

   C'est ce mot de passe que vous donnerez aux capitaines.
3. **Créer un jeton GitHub** (sert au PC et au bouton du site) :
   https://github.com/settings/personal-access-tokens/new (*Fine-grained token*) :
   - *Token name* : « Vaires », *Expiration* : 1 an ;
   - *Repository access* : **Only select repositories** → `ggman23/ggping` ;
   - *Permissions* → *Repository permissions* : **Contents : Read and write** et
     **Actions : Read and write** (rien d'autre) ;
   - *Generate token*, puis copier le jeton (`github_pat_…`).
4. **Sur le PC** : `lancer.bat`, **option 7** (« Lien avec le téléphone ») : coller le jeton, taper
   le mot de passe du site (le même qu'à l'étape 2). Le PC envoie ses données et lance la
   première mise à jour du site. Ensuite, chaque lancement de `lancer.bat` (options 1 à 5) envoie
   les données et met le site à jour automatiquement.
5. **Sur le téléphone** : ouvrir le site, l'ajouter à l'écran d'accueil (menu du navigateur →
   « Ajouter à l'écran d'accueil »), et coller le même jeton dans « Réglage du bouton ».

## Le bouton « Lancer la mise à jour » du site

Il demande à GitHub de lancer la mise à jour, puis affiche son avancement (« en cours… »,
« terminé »). Il utilise le jeton de l'étape 3, enregistré uniquement sur le téléphone (stockage
du navigateur) ; « Effacer » le retire. Pour le bouton seul, le droit *Actions : Read and write*
suffit.

Sans jeton, on peut toujours lancer depuis l'appli ou le site GitHub : *Actions* → *Mise à jour
du site* → *Run workflow* (choix des pages : tout, résultats, effectif, virtuel, adversaires).

Une page non choisie lors d'une mise à jour reste celle de la mise à jour précédente (sa date
est affichée sur l'accueil).

## Si le PC n'a pas envoyé ses données

Sans données du PC (lien pas encore réglé), la mise à jour en ligne fonctionne quand même, mais
sans pingpocket ni dossier `import` : effectifs limités aux joueurs alignés en championnat, sans
meilleurs classements (les pages le signalent). D'où l'option 7.

## Copie de secours sur Netlify (ggping.netlify.app)

À chaque mise à jour du site GitHub (lancée du PC, du téléphone ou automatique), une copie part
aussi sur Netlify :

- **https://ggping.netlify.app/** : la page des adversaires (`vaires.html`), **sans mot de passe**,
  pour tout le club. Elle n'est pas référencée par les moteurs de recherche (robots.txt et en-tête
  `X-Robots-Tag: noindex`), mais toute personne qui a l'adresse peut la lire : elle contient les
  noms, classements et catégories d'âge des joueurs (dont des mineurs) de Vaires et des clubs adverses.
- **https://ggping.netlify.app/club/** : l'**espace club**, avec son propre mot de passe (secret
  `MOT_DE_PASSE_CLUB`) : un menu des pages, de l'Excel et des images (à gauche sur un ordinateur,
  en plein écran sur un téléphone) ; chaque document s'affiche dans la page, avec un bouton
  « Télécharger » (et « Partager » pour les images), puis « Menu » pour revenir ; « Tout
  télécharger » en bas du menu. On ne peut pas y lancer de mise à jour. Le mot de passe est
  demandé une fois par appareil (« Se souvenir sur cet appareil »).
- **https://ggping.netlify.app/gg/** : la copie du site GitHub (accueil, toutes les pages, l'Excel,
  les images, « Tout télécharger »), re-chiffrée avec **son propre mot de passe** (secret
  `MOT_DE_PASSE_GG`), à donner aux capitaines. Le mot de passe du site GitHub ne sert pas sur
  /gg/ et reste secret. Sans le secret `MOT_DE_PASSE_GG`, /gg/ n'est pas publié.

Mise en place, une seule fois :

1. Sur Netlify (compte qui possède le site ggping) : avatar → *User settings* → *Applications* →
   *Personal access tokens* → *New access token* (https://app.netlify.com/user/applications#personal-access-tokens).
   Nom : `ggping`, expiration la plus longue proposée. Copier le jeton.
2. Sur GitHub : dépôt → *Settings* → *Secrets and variables* → *Actions* → *New repository secret* :
   nom `NETLIFY_AUTH_TOKEN`, valeur : le jeton.
3. Même endroit, deux autres secrets : `MOT_DE_PASSE_CLUB` (le mot de passe de /club/) et
   `MOT_DE_PASSE_GG` (celui de /gg/). Ils ne sont écrits nulle part dans le dépôt, qui est public ;
   sans l'un d'eux, la partie correspondante n'est pas publiée.
4. Si le site Netlify ne s'appelle pas `ggping` : onglet *Variables* → *New repository variable*
   `NETLIFY_SITE` = `nom.netlify.app`.
5. Lancer une mise à jour : le journal de l'étape « Copie de secours sur Netlify » affiche l'adresse.

Sans le secret, l'étape ne fait rien. Si Netlify refuse l'envoi, un avertissement s'affiche dans le
journal de la mise à jour, mais le site GitHub est publié quand même. La copie part même si GitHub
Pages est en panne, dès que le site est prêt.

## Archives des journées passées

Après chaque mise à jour, les journées terminées sont archivées : la J3 passe en archive dès que la
J4 a commencé. Une archive contient les pages, l'Excel et les images **telles qu'elles étaient la
veille de la journée suivante** (résultats, feuilles de match, classement virtuel, brûlages et
prochaine journée de ce jour-là) : elle est refaite à cette date, puis publiée une fois pour toutes
(étape « Archives des journées passées » du workflow). Les archives qui manquent, par exemple J1 et
J2 à la mise en place, sont reconstruites de la même façon.

- Site GitHub et /gg/ : section « Archives des journées passées » en bas de l'accueil ; chaque
  archive est un petit site (même mot de passe), avec un lien « ← Journée en cours ».
- /club/ : rubrique « Archives » dans le menu (et en tuiles sur l'accueil) ; chaque journée
  s'ouvre comme la journée en cours (pages, Excel, images, « Tout télécharger ») ; les fichiers
  téléchargés portent la journée dans leur nom (J2_resultats_vaires.html).
- Netlify ne reçoit que les fichiers qui ont changé : une archive n'est envoyée qu'une fois.

## Sécurité

- Chaque page, l'Excel et les données envoyées par le PC sont chiffrés en AES-256-GCM avec une clé
  tirée du mot de passe (PBKDF2-SHA256, 310 000 itérations) ; le déchiffrement se fait dans le
  navigateur (pages) ou dans la mise à jour en ligne (données du PC). Rien n'est publié ni envoyé
  en clair, sauf la page des adversaires à l'accueil de la copie Netlify (choix du club, voir
  ci-dessus).
- Le mot de passe est stocké en secret GitHub (illisible, même par le propriétaire), dans le
  fichier `publication.local.json` du PC (avec le jeton ; jamais envoyé sur GitHub) et, si on le
  demande, sous forme de clé dans le navigateur de l'appareil.
- Changer le mot de passe : modifier le secret `MOT_DE_PASSE_SITE`, refaire l'option 7 sur le PC
  avec le nouveau, puis relancer. Chacun devra saisir le nouveau mot de passe sur le site.
- Le bilan des vérifications sur l'accueil ne contient que des nombres et des noms d'équipes.

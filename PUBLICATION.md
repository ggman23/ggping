# Lancer les mises à jour depuis un téléphone

Les pages sont générées sur les serveurs de GitHub (GitHub Actions) et publiées sur un site
(GitHub Pages), consultable et actualisable depuis un téléphone :

**https://ggman23.github.io/ggping/**

- La page d'accueil liste les pages (adversaires, résultats, Excel, feuilles de match, classements
  des poules, effectif, classement virtuel)
  avec leur date et le bilan des vérifications, et propose un bouton **« Lancer la mise à jour »**.
- Chaque page s'**ouvre** dans le navigateur ou se **télécharge** ; « Tout télécharger » récupère
  les pages HTML, l'Excel et toutes les images dans « Téléchargements » : ce sont exactement
  les fichiers du dossier `sortie` du PC (mêmes noms), lisibles sans connexion et sans mot de passe.
- Section **« Images à partager »** : chaque image se voit en grand (« Voir »), se télécharge, et
  peut être envoyée directement depuis le téléphone (« Partager » : WhatsApp, SMS…).
- Les pages sont **chiffrées** : il faut le mot de passe du club pour les lire (cochez « Se
  souvenir sur cet appareil » pour ne le taper qu'une fois). Le site est public, mais sans le mot
  de passe on n'y voit aucun nom de joueur ; il n'est pas référencé par les moteurs de recherche.
- Mise à jour automatique : tous les lundis vers 7 h et vers 22 h 30 (heure d'hiver ; une heure plus
  tard en été), sur GitHub et Cloudflare (Netlify seulement à la main) ; et après chaque lancement de
  `lancer.bat` sur le PC.
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

En haut de la page d'accueil du site (« Mettre à jour maintenant », avant la liste des pages). Avec
« Tout » ou « Clubs du 77 », un second choix dit **quels joueurs du 77 relire pour leurs points
virtuels** : tous (par défaut, environ 2 300), les jeunes (environ 820), les adultes (environ 1 500) ou
aucun (garder les dernières lectures). Chaque liste n'est de toute façon relue qu'une fois par semaine
(à la première mise à jour à partir du lundi). Dans GitHub (*Run workflow*) : « joueurs_77 ». Voir
« Clubs du 77 » plus bas.

Deux boutons :
- **« Mettre à jour GitHub et Cloudflare »** : gratuit, autant de fois qu'il faut (corrections,
  ajouts) ; la copie Netlify n'est pas touchée.
- **« Mettre à jour les 3 sites (avec Netlify) »** : envoie aussi la version sur Netlify, l'adresse
  donnée au club (15 crédits Netlify ; garde-fou à 18 envois par mois).

Les mises à jour automatiques du lundi (matin et soir) mettent à jour GitHub et
Cloudflare seulement : Netlify n'est envoyé qu'à la main (aucun crédit dépensé sans le demander). Sur le
PC, à la fin de chaque lancement, l'outil demande s'il faut publier aussi sur Netlify (Entrée = non).
Dans GitHub (*Actions* → *Run workflow*), c'est la case « Envoyer aussi sur Netlify ».

Le bouton demande à GitHub de lancer la mise à jour, puis affiche son avancement (« en cours… »,
« terminé »). Il utilise le jeton de l'étape 3, enregistré uniquement sur le téléphone (stockage
du navigateur) ; « Effacer » le retire. Pour le bouton seul, le droit *Actions : Read and write*
suffit.

Sans jeton, on peut toujours lancer depuis l'appli ou le site GitHub : *Actions* → *Mise à jour
du site* → *Run workflow* (choix des pages : tout, résultats, effectif, virtuel, adversaires,
individuels, clubs du 77, publication).

Une page non choisie lors d'une mise à jour reste celle de la mise à jour précédente (sa date
est affichée sur l'accueil).

**« Publication seule »** (dernier choix de la liste ; `publication` dans *Run workflow*) : rien n'est
relu, ni à la FFTT ni sur pingpocket.fr, et aucune archive n'est refaite. Les pages déjà en ligne sont
reprises telles quelles, avec leur date, et le site est republié : c'est ce qu'il faut après avoir
ajouté un document à l'espace club (affiche, PDF : voir « Rubriques de l'espace club ») ou changé
l'outil sans vouloir attendre une mise à jour complète. Environ 2 à 3 minutes. Avec le bouton « les 3
sites », Netlify reçoit aussi la nouvelle version (15 crédits).

## Si le PC n'a pas envoyé ses données

Sans données du PC (lien pas encore réglé), la mise à jour en ligne fonctionne quand même, mais
sans pingpocket ni dossier `import` : effectifs limités aux joueurs alignés en championnat, sans
meilleurs classements (les pages le signalent). D'où l'option 7.

## Surnoms du récapitulatif sans le PC (secret SURNOMS)

Le fichier `import\surnoms.txt` n'existe que sur le PC (il part en ligne avec les autres données
du PC, une fois envoyé il y reste). Pour une mise à jour lancée depuis le site, sans passer par le
PC, les mêmes lignes peuvent être mises dans un secret GitHub :

1. Sur github.com (le navigateur du téléphone convient) : dépôt → *Settings* → *Secrets and
   variables* → *Actions* → *New repository secret*.
2. *Name* : `SURNOMS` ; *Secret* : une ligne par joueur, `NOM Prénom = nom affiché`, par exemple

       GUITTON Marc = Marc G
       LE CERF Christian = Christian LC

   (sur une seule ligne, séparer par des `;` convient aussi). Majuscules et accents indifférents.
3. *Add secret*. Pour le modifier : *Update* sur le secret, et recopier **toute** la liste
   (GitHub ne la ré-affiche pas : la garder dans une note).

C'est un secret plutôt qu'une variable parce que les journaux des mises à jour sont publics : un
secret n'y apparaît jamais. Il l'emporte sur `surnoms.txt` pour un même joueur. Les archives des
journées passées sont refaites à la mise à jour suivante pour en tenir compte.

## Accès aux données de la FFTT : compte licencié (depuis le 31/10/2026)

Les résultats, feuilles de match et poules viennent de l'API de la FFTT (apiv2.fftt.com), celle de
l'espace licencié https://malicence.fftt.com. Jusqu'au 27/10/2026 elle répondait sans connexion ;
depuis le 31/10/2026 elle répond « 401 JWT Token not found » sans elle. L'outil se connecte donc
comme l'espace licencié, avec **le compte licencié du responsable de l'outil** (identifiant et mot
de passe de malicence.fftt.com), et reçoit un jeton d'accès qu'il renouvelle au besoin
(`ttvaires/compte_fftt.py`) :

- **en ligne (GitHub)** : deux secrets, *Settings* → *Secrets and variables* → *Actions* :
  `FFTT_IDENTIFIANT` et `FFTT_MOT_DE_PASSE` ;
- **sur le PC** : lancer.bat les demande au premier lancement et les garde dans
  `publication.local.json` (sur le PC seulement, jamais envoyé).

Une connexion refusée n'est pas retentée dans le même lancement (pas de rafale d'essais qui
bloquerait le compte) ; l'accueil du site affiche alors « connexion à la FFTT refusée pour le
compte… ». Si la FFTT demande un code de vérification à la connexion (double authentification),
l'outil ne peut pas le saisir et le dit. L'outil reste discret (pages gardées en cache, pauses
entre les requêtes). C'est un compte personnel : la FFTT pourrait ne pas apprécier son usage par
un programme.

L'autre voie, prévue par la FFTT pour les applications, est son API officielle (Smartping v2.0,
https://www.fftt.com/api/, formulaire à envoyer à interfaces.informatiques@fftt.email), sur
dossier et avec des conditions d'utilisation strictes (site ouvert à tous, pas de conservation
au-delà de 24 h sans accord, pas de mélange avec d'autres sources).

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

### Crédits Netlify (offre gratuite : 300 par mois)

Netlify décompte **15 crédits par mise en ligne**, quelle que soit sa taille : 300 crédits font
20 envois par mois. La taille du site compte peu (le trafic : 20 crédits par Go servi aux visiteurs,
soit environ 1 crédit pour 50 Mo ; les requêtes : 2 crédits pour 10 000). Les crédits repartent à zéro à chaque cycle (le 6 du mois pour ce
compte). **Crédits épuisés (offre gratuite) : Netlify met le site en pause** jusqu'au cycle suivant,
les visiteurs voient « Site not available » (documentation Netlify, « How credits work ») : garder
de la marge. Le site GitHub, lui, n'est pas concerné.

Pour économiser : **une copie identique à celle en ligne n'est pas renvoyée**. L'outil calcule une
empreinte de ce que montre la copie (pages sans leur date de génération, bilans, archives, surnoms et
photos, code de l'outil, réglages) et la compare à celle de la copie en ligne (`signature.txt`,
chiffrée). Sans résultat nouveau, le journal affiche « rien de nouveau depuis la copie en ligne : pas
d'envoi » et rien n'est décompté.

Mises à jour automatiques : **tous les lundis**, vers 7 h et vers 22 h 30 (heure d'hiver ; une heure
plus tard en été, l'horaire de GitHub étant en heure universelle), même sans championnat le week-end :
les critériums et tournois changent aussi la forme des adversaires, et certains résultats ne sont
saisis que le lundi (celle du soir les prend). Elles ne publient que sur GitHub et Cloudflare
(depuis le 11/11/2026) : **les envois sur Netlify sont tous manuels** (bouton « Mettre à jour les 3
sites », case « Envoyer aussi sur Netlify », ou réponse « o » sur le PC). Requêtes vers l'API de la
FFTT : environ 1 100 le lundi matin (dont les parties des joueurs adverses, relues une fois par
jour), quelques centaines le soir ; de 6 000 à 8 000 par mois avec quelques mises à jour à la main.
Le site GitHub, lui, est toujours mis à jour (gratuit). Pour forcer l'envoi : *Actions* → *Mise à
jour du site* → *Run workflow* → cocher « Envoyer la copie Netlify même si rien n'a changé ».

**Garde-fou** : avant chaque envoi, l'outil compte les mises en ligne Netlify du cycle en cours
(depuis le 6 du mois). À partir de **18** (270 crédits ; la marge couvre le trafic), il n'envoie plus
rien sur Netlify jusqu'au cycle suivant : le journal l'indique (« Plus d'envoi jusqu'au 6 du mois
prochain »), la copie Netlify reste en ligne telle quelle, et l'espace club reste à jour sur le site
GitHub et sur Cloudflare Pages. Un envoi forcé passe encore une fois (19, soit 285 crédits), jamais
au-delà. Réglages dans `ttvaires/netlify.py` (JOUR_CYCLE, LIMITE_ENVOIS, PLAFOND_ENVOIS).

## Publication sur GitHub Pages : un commit par mise à jour

GitHub Pages identifie une publication par le commit du code sur lequel tourne la mise à jour : deux
mises à jour sur le même commit (par exemple la mise à jour automatique du lundi après une mise à jour
à la main, sans nouvelle version de l'outil entre les deux) se disaient réussies, mais la seconde
n'était pas mise en ligne (constaté le 09/11/2026). Publier avec un autre commit ne marche pas non
plus (essai du 10/11/2026 : publication jamais traitée). Donc, à la fin de chaque mise à jour, un
commit vide « Mise à jour du site n° … » est ajouté à la branche (`ttvaires/pages.py`) : la suivante
tourne sur un commit nouveau. Ces commits ne changent aucun fichier.

GitHub répond parfois qu'il ne trouve pas le site qu'on vient de lui envoyer (15/11/2026 : « No
artifacts named github-pages were found », une seconde après « successfully uploaded » ; Netlify et
Cloudflare, eux, publiés). L'étape « Publication » réessaie donc une fois, une minute plus tard ; la
mise à jour n'est en échec que si le second essai rate aussi (alors : la relancer plus tard).

## Espace club sur le site GitHub (gratuit, sans limite de mises à jour)

À chaque mise à jour, l'espace club est aussi publié sur le site GitHub, à l'adresse
**https://ggman23.github.io/ggping/club/**, avec le même mot de passe (secret `MOT_DE_PASSE_CLUB`) et
le même contenu que sur Netlify (pages, Excel, images, archives, Matériel, Prépa mentale). GitHub
Pages ne compte pas les mises en ligne : cette adresse est toujours à jour, même quand le garde-fou
Netlify a arrêté les envois. Les statistiques de visite y fonctionnent aussi.

## Copie sur Cloudflare Pages (gratuit : 500 mises en ligne par mois)

La même copie que Netlify (accueil public, /club/, /gg/) part aussi sur Cloudflare Pages, à une
adresse du type **https://ggping.pages.dev/** (club : https://ggping.pages.dev/club/, mêmes mots de
passe). Mise en place, une fois :

1. Sur https://dash.cloudflare.com : icône du profil (en haut à droite) → **Profil** → **Jetons d'API**
   (*API Tokens*) → **Créer un jeton** → **Créer un jeton personnalisé** (*Create Custom Token*).
   Nom : `ggping` ; Autorisations : **Compte** → **Cloudflare Pages** → **Modifier** (*Edit*) ;
   Ressources du compte : **Inclure** → ton compte. Continuer → Créer le jeton → copier le jeton
   (il n'est affiché qu'une fois).
2. L'identifiant du compte (*Account ID*) : sur la page d'accueil du tableau de bord, menu « ⋯ » du
   compte → *Copy account ID* (ou colonne de droite de **Workers & Pages**).
3. Sur GitHub : *Settings* → *Secrets and variables* → *Actions* → **New repository secret** :
   `CLOUDFLARE_API_TOKEN` (le jeton) et `CLOUDFLARE_ACCOUNT_ID` (l'identifiant). Facultatif : une
   *variable* `CLOUDFLARE_PROJET` pour un autre nom de projet que `ggping`.
4. Lancer une mise à jour : le projet est créé au premier passage, l'adresse exacte est dans le
   journal (étape « Copie sur Cloudflare Pages ») ; si `ggping.pages.dev` est déjà pris par
   quelqu'un d'autre, Cloudflare ajoute un suffixe.

Comme pour Netlify, une copie identique à celle en ligne n'est pas renvoyée. Sans ces secrets, les
étapes Cloudflare ne font rien ; une erreur Cloudflare est signalée sans empêcher les autres copies.

## Statistiques de visite (GoatCounter, facultatif)

Pour savoir ce que font les membres du club sur la copie Netlify : nombre de pages vues et de
visiteurs, documents ouverts, téléchargés et partagés. Seule la copie Netlify est comptée
(accueil public, /club/, /gg/), jamais le site GitHub.

1. Créer un compte gratuit (usage non commercial) sur https://www.goatcounter.com/signup : choisir
   un **code**, par exemple `cvtt-vaires` (le tableau de bord sera https://cvtt-vaires.goatcounter.com),
   une adresse e-mail et un mot de passe.
2. Sur github.com : dépôt → *Settings* → *Secrets and variables* → *Actions* → onglet
   **Variables** → *New repository variable* : *Name* `GOATCOUNTER`, *Value* le code
   (`cvtt-vaires`). Un secret du même nom (onglet *Secrets*) convient aussi. Pas dans
   *Codespaces* ni *Dependabot* : ceux-là ne sont pas lus par la mise à jour.
3. À la mise à jour suivante, le journal affiche « Statistiques de visite : https://cvtt-vaires.goatcounter.com ».

Ce que l'on voit sur le tableau de bord :

- **pages vues** : `/` (accueil public, adversaires), `/club/connexion` (écran du mot de passe),
  `/club/` (accueil de l'espace club), `/club/<fichier>` pour chaque document ouvert
  (`/club/resultats_vaires.html`, `/club/recap_J3.png`...), `/club/archives/<journée>`, `/gg/` ;
- **événements** (onglet *Events*) : `club/connexion`, `club/connexion-refusee`,
  `club/telechargement/<fichier>`, `club/partage/<fichier>`, `club/tout-telecharger` ; sur /gg/ :
  `gg/ouverture/<page>`, `gg/telechargement/<fichier>`, `gg/image/<fichier>`, `gg/partage/<fichier>`,
  `gg/tout-telecharger`, `gg/mise-a-jour` ; dans les pages à part (une page vue par ouverture, puis
  ce qu'on y fait) :
  - `/77/` : `77/onglet/<clubs, classements, comparer, poules, joueurs>`, `77/fiche/<club>` (fiche
    d'un club ouverte), `77/classement/<mesure choisie>`, `77/filtre/<…>` (femmes ou hommes, licences
    loisir, catégories, division ; dans Joueurs : catégorie, club, femmes ou hommes), `77/tri/<onglet>-<colonne>`,
    `77/bouton/<…>` (jeunes par progression, tous les jeunes ou joueurs d'un club, afficher plus,
    comparer les clubs d'une poule), `77/comparer/<…>`, `77/poule/<poule choisie>`, `77/lien/<page>` ;
  - `/cal/` : `cal/mois/<AAAA-MM>`, `cal/jour/<date>`, `cal/categorie/<compétition>-<affichee ou masquee>`,
    `cal/lien/<lien>` (agenda partagé, PDF, autres espaces) ;
  - `/indivs/` : `indivs/vue/ensemble`, `indivs/vue/joueur` (fiche d'un joueur, sans dire lequel),
    `indivs/lien/<lien>` ; `/tournois/` : `tournois/liste/<liste>`, `tournois/lien/<lien>` (un tournoi
    ouvert dans les cadres de PingRadar ne peut pas être compté) ;
  jamais un nom de joueur ni un texte tapé (recherche) ;
- les **appareils différents** (taper `appareils` dans *Filter paths*) : chaque téléphone ou
  navigateur de PC se signale une seule fois par jour, par semaine et par mois, d'où :
  `appareils/jour` (vu par jour : combien d'appareils différents chaque jour), `appareils/semaine`,
  `appareils/mois` (sur le mois choisi en haut : combien d'appareils différents dans le mois),
  `appareils/nouveaux` (venus pour la première fois), et les mêmes par espace :
  `appareils/club/mois`, `appareils/gg/semaine`, `appareils/accueil/jour`... C'est le nombre de
  personnes différentes, à peu près : une personne qui vient avec son téléphone et son PC compte
  pour deux, et un navigateur vidé ou en navigation privée revient comme un nouvel appareil ;
- les navigateurs, téléphone ou PC, tailles d'écran, pays, et d'où viennent les visites.

Les « visits » de GoatCounter (ligne *Totals* et colonne de chaque page) comptent chaque page vue
et chaque action, pas les personnes : une personne qui ouvre 6 documents compte 6. Les adresses IP
ne sont ni gardées ni affichées (par choix de GoatCounter, et ce sont des données personnelles) ;
elles ne donneraient d'ailleurs pas le nombre de personnes : un téléphone en 4G change d'adresse
sans arrêt, et tout un foyer partage la même en wifi.

Pour ne pas compter ses propres visites : ouvrir une fois **https://ggping.netlify.app/#toggle-goatcounter**
sur chacun de ses appareils (un message confirme ; le refaire pour réactiver). Cela coupe aussi Umami.

### Umami (en plus de GoatCounter)

Umami Cloud (gratuit, sans cookie) reçoit les mêmes pages vues et les mêmes actions, et donne en
plus : les **visiteurs différents** (calculés par Umami), le **temps passé** et le **taux de rebond**,
les **parcours** (*Journeys* : accueil → connexion → téléchargement...), le **retour** des visiteurs
semaine après semaine (*Retention*), les **entonnoirs** (*Funnels*) et la vitesse de chargement de
l'accueil public. Les actions y sont des événements nommés `connexion`, `connexion-refusee`,
`telechargement`, `partage`, `tout-telecharger`, `ouverture`, `image`, `mise-a-jour`, avec en détail
l'espace (club, gg...) et le fichier ; ceux des pages à part sont nommés par l'action (`onglet`,
`fiche`, `classement`, `filtre`, `tri`, `bouton`, `comparer`, `poule`, `lien`, `mois`, `jour`,
`categorie`, `vue`, `liste`), avec en détail l'espace (77, cal...) et la valeur sous le nom de
l'action (onglet = joueurs, mois = 2026-12...).

Tableau de bord : https://cloud.umami.is, site « CVTT Vaires ». L'identifiant du site
(`data-website-id`) est déjà dans le workflow ; une variable ou un secret `UMAMI` le remplace. Le
script d'Umami est une copie figée servie par le site lui-même (`stats/umami.js`), qui envoie les
mesures à Umami Cloud.

Vie privée : GoatCounter ne pose pas de cookie et ne garde pas les adresses IP ; il ne reçoit que
des noms de fichiers, jamais un nom de joueur ni un mot de passe. Pour les appareils différents,
le navigateur garde seulement les dates de ses derniers signalements (aucun identifiant n'est
créé ni envoyé). Le script est figé (version et
empreinte vérifiées par le navigateur). Sans la variable, rien n'est ajouté aux pages.
Autre possibilité, payante : Netlify Analytics (compté par le serveur de Netlify, sans script,
mais sans les téléchargements ni les partages).

## Archives des journées passées

Après chaque mise à jour, les journées terminées sont archivées : la J3 passe en archive dès que la
J4 a commencé. Une archive contient les pages, l'Excel et les images **telles qu'elles étaient la
veille de la journée suivante** (résultats, feuilles de match, classement virtuel, brûlages et
prochaine journée de ce jour-là) : elle est refaite à cette date, puis publiée une fois pour toutes
(étape « Archives des journées passées » du workflow). Les archives qui manquent, par exemple J1 et
J2 à la mise en place, sont reconstruites de la même façon. Une archive est aussi refaite quand son
récapitulatif changerait : surnoms modifiés, photo de la journée ou logos ajoutés après coup.

- Site GitHub et /gg/ : section « Archives des journées passées » en bas de l'accueil ; chaque
  archive est un petit site (même mot de passe), avec un lien « ← Journée en cours ».
- /club/ : rubrique « Archives » dans le menu (et en tuiles sur l'accueil) ; chaque journée
  s'ouvre comme la journée en cours (pages, Excel, images, « Tout télécharger ») ; les fichiers
  téléchargés portent la journée dans leur nom (J2_resultats_vaires.html).
- Netlify ne reçoit que les fichiers qui ont changé : une archive n'est envoyée qu'une fois.

## Rubriques de l'espace club : Championnat de Paris, Matériel, Prépa mentale

Après les archives, le menu de /club/ (et l'accueil, en tuiles) a des rubriques permanentes faites
de documents fournis, publiés tels quels : une page HTML (Matériel : forums et communautés sur le
matériel) et des PDF (Prépa mentale). Sur ordinateur, un PDF s'affiche dans la page ; sur téléphone
(et dans l'application), « Ouvrir le PDF » le donne au lecteur PDF de l'appareil. Une page HTML
fournie s'affiche isolée de l'espace club (elle n'a accès ni au mot de passe ni aux autres documents).

Les documents sont dans le dossier `ressources/` du dépôt, **chiffrés avec le mot de passe du club**
(le dépôt est public, eux ne le sont pas) ; `ressources/ressources.json` donne l'ordre des rubriques,
les titres et les descriptions. Pour ajouter ou remplacer un document, sur le PC :

    python -m ttvaires.ressources ajouter "Prépa mentale" "C:\chemin\guide.pdf" --titre "Guide du joueur" --description "26 pages"

(le mot de passe du club est demandé), puis envoyer le dossier `ressources/` sur GitHub et lancer une
mise à jour « Publication seule » (2 à 3 minutes, rien n'est relu) ou attendre la suivante. Une
nouvelle rubrique est créée à la fin si son nom n'existe pas. Si le mot de passe du club change,
ces documents ne s'ouvrent plus avec la nouvelle clé : la mise à jour le signale dans son journal et
ne les publie pas ; il faut alors les ajouter de nouveau.


Une image (png, jpg) peut aussi être un document de rubrique : elle s'affiche comme les images du
site, avec « Télécharger » et « Partager » sur téléphone (partagée avec son vrai type, PNG ou JPEG) :
ex. le mémo sac de sport, version image du PDF, ou l'affiche du championnat de Paris 2026-2027
(rubrique « Championnat de Paris », placée en premier dans `ressources.json`).

Une grande image (plus de 2 400 pixels de côté, comme cette affiche en 5461 × 8192, 15 Mo) reçoit en
plus, à l'ajout, un **aperçu allégé** (2 000 pixels de haut au plus, JPEG, chiffré lui aussi :
`<nom>.apercu.jpg.chiffre`). L'espace club affiche l'aperçu, rapide à ouvrir sur un téléphone, avec la
mention « Aperçu allégé » ; « Télécharger » et « Partager » donnent l'original en pleine résolution.
Pour garder la pleine résolution dans WhatsApp, l'envoyer en « Document » (en « Photo », WhatsApp la
réduit). Cloudflare Pages refuse les fichiers de plus de 25 Mo : une image plus lourde est à réduire.

## Vue par équipe (espace club et v2)

L'espace club garde tout ce qu'il avait (pages, Excel, images, archives, rubriques) ; en plus, en tête de son
menu et de son accueil, **Par équipe** : un bouton par équipe (Vaires 1 à 6, Vaires 1 F, les trois équipes de
Paris, les deux équipes jeunes). La page d'une équipe (`/club/#equipe/v2`, `#equipe/v1f`, `#equipe/p2`,
`#equipe/j1`) ne montre que ce qui la concerne :
- **ses pages**, ouvertes sur cette équipe seulement : adversaires, feuilles de match, classement de sa poule,
  effectif et brûlages pour elle, progression de ses joueurs, résultats de ses joueurs ; pour Paris et les
  jeunes, sa page de /paris/ ou /jeunes/ (et les disponibilités pour Paris) ;
- **ses images à partager** : prochain adversaire, feuille de match, joueurs disponibles (en plusieurs images et
  en image unique), joueurs brûlés, progression ; pour Paris, l'infographie et l'affiche ; et le programme des
  équipes.

La dernière équipe choisie est retenue sur l'appareil (« Ton équipe : Vaires 2 » en haut de l'accueil). En bas
du téléphone, « Équipe » ramène de la page ouverte à la page de l'équipe.

Chaque page du site sait s'afficher pour une seule équipe : adresse `#seule/<code>` (`v1` à `v6`, `v1f` ; à
/paris/ et /jeunes/ : `v1`, `v2`...), un bandeau « Vue de Vaires 2 seulement · Voir toutes les équipes », les
onglets réduits à cette équipe ; « Voir toutes les équipes » rend la page entière. Cela marche aussi pour les
pages ouvertes à part (ex. https://ggman23.github.io/ggping/paris/#seule/v2).

Dans la **v2**, la fiche de chaque équipe (onglet Équipes, ou « Par équipe » en tête de la page Club) a des
**onglets en haut de la page**, qui restent collés sous la barre du haut quand on fait défiler :
**Résumé** (sa place, sa prochaine rencontre, le classement de sa poule, son calendrier, ses joueurs habituels) ·
**Adversaire** · **Feuilles de match** · **Poule** · **Effectif** · **Progression** · **Résultats** (les pages du
site actuel, ouvertes dans la fiche sur cette équipe seulement) · **Images** (ses images en vignettes, puis le
programme du club ; une vignette touchée s'agrandit, avec Télécharger et Partager). Pour Paris : Résumé ·
Poule et adversaires · Disponibilités · Images ; pour les jeunes : Résumé · Poule et adversaires. Chaque
onglet a son adresse : `/v2/equipes/#france-2`, `#france-2/effectif`, `#france-2/images`, `#femmes-1/feuilles`,
`#paris-2/dispos`...

Le bouton « ☆ C'est mon équipe » de la fiche la retient sur l'appareil : l'**accueil** de la v2 montre alors, juste
sous le bandeau, « **Tout sur Vaires 2** » (sa place, sa prochaine rencontre) et un raccourci vers chaque
onglet. Sans équipe choisie, l'accueil propose « Choisis ton équipe » avec un bouton par équipe (celle touchée
est retenue) ; sinon, c'est l'équipe du joueur choisi dans « Mon espace ».

## Version 2 à l'essai : /v2/ (copie Cloudflare)

Une nouvelle version du site, à tester sans rien changer au site actuel : **https://ggping-pap.pages.dev/v2/**
(l'adresse du projet Cloudflare suivie de /v2/ ; aussi sur Netlify quand la copie y est envoyée ; pas sur le
site GitHub). Même mot de passe que l'espace club ; un appareil qui a déjà mémorisé celui de /club/ (même
adresse) entre directement. Un bandeau jaune en haut ramène au site actuel.

Organisation, par question plutôt que par source de données, avec 5 onglets en bas de l'écran (en haut sur
ordinateur) :
- **Accueil** (`/v2/`) : la prochaine journée en une phrase, les rencontres de la semaine (une carte par
  rencontre : couleur et pictogramme de la compétition, domicile en vert, extérieur en orange), « Mon espace »,
  les derniers résultats, les images à partager, ce qui est nouveau depuis la dernière visite ;
- **Équipes** (`/v2/equipes/`) : sous-rubriques « Équipes de Vaires » et **Clubs du 77** (`/v2/77/` : les 55
  clubs classés par force (moyenne des 4 meilleurs), nombre de joueurs ou nom ; la fiche d'un club : ses
  chiffres, ses équipes et tous ses joueurs avec leurs points virtuels) ; les 12 équipes (France hommes et
  femmes, Paris, jeunes) ; pour chacune
  (`#france-4`, `#paris-2`...) : prochaine rencontre, classement de la poule, calendrier et résultats, joueurs
  habituels, « Ajouter à mon agenda » ;
- **Rencontre** (`/v2/rencontre/#france-4/6`) : face-à-face, salle avec « Itinéraire » (lien Google Maps) et
  Waze, place de l'adversaire dans la poule, compo probable adverse et joueurs habituels de Vaires, pronostic,
  feuille de match une fois jouée, disponibilités (Paris) ;
- **Joueurs** (`/v2/joueurs/`) : sous-rubriques « Joueurs de Vaires » et **Tous les joueurs du 77**
  (`/v2/77/#joueurs` : recherche par nom ou par club, filtres hommes, femmes, jeunes, par 100) ; recherche, tri par points virtuels, progression ou nom, filtres femmes et
  jeunes, petite courbe ; fiche (`#<licence>`) : points officiels et virtuels, objectif (« encore 87,5 points
  pour passer 10 »), courbe de la saison, perfs et contres, séries, meilleur classement, bilan selon le niveau
  de l'adversaire, dernières parties, brûlage ;
- **Agenda** (`/v2/agenda/`) : tous les matchs de Vaires par mois et par jour, les tours des individuels, et
  au choix les dates du comité ; « Ajouter les matchs de Vaires à mon agenda » (fichier .ics fabriqué dans le
  navigateur : rien n'est envoyé). Sous-rubriques en haut : **Calendrier** (`#calendrier` : la grille du mois,
  une pastille de couleur par rencontre ou date, avec son libellé sur ordinateur ; mois précédent ou suivant ;
  touche un jour pour voir son programme), **Individuels** (`/v2/indivs/` : les poules à venir et les tours
  joués ; pour chaque poule, le lieu avec l'itinéraire, les **résultats du tour** et le classement de la poule,
  les parties de chacun, puis la poule de la plus forte à la plus faible avec la forme et le niveau de chaque
  adversaire) et **Tournois** (`/v2/tournois/` : les blocs PingRadar de la page Tournois, autour de Vaires, ce
  week-end, le week-end prochain, Île-de-France, Seine-et-Marne) ;
- **Club** (`/v2/club/`) : dans l'ordre, « Par équipe », les documents du club (affiche du championnat de Paris,
  Matériel : forums et communautés du monde entier, Prépa mentale : mémo du sac de sport et guides en PDF, affichés
  dans la page sur ordinateur), les pages détaillées du site actuel (avec l'état de leurs vérifications, ouvertes
  dans le cadre de la v2), les images à partager, les archives, les autres espaces, « Tout télécharger » et les
  réglages. L'accueil de la v2 a aussi un bloc « Documents du club ».

En haut de chaque page : la **recherche** (joueur, club adverse, équipe, page) et les **réglages** : « C'est moi »
(Mon espace : prochaine rencontre de son équipe, ses points, son objectif ; gardé sur l'appareil seulement),
taille du texte (normale, grande, très grande), apparence (claire, sombre ou comme le téléphone), mode
administrateur (lien vers la mise à jour du site, /lundi/), déconnexion.

**Application installable** : sur Android (Chrome : menu → « Installer l'application » ou « Ajouter à l'écran
d'accueil ») et sur iPhone (Safari : Partager → « Sur l'écran d'accueil »), avec l'icône du club ; la dernière
version consultée reste lisible sans réseau (service worker ; les données restent chiffrées).

Le **pronostic** est une estimation pour le plaisir : probabilité de gagner une partie selon l'écart de points
(1 / (1 + e^(−écart/150))), sur 12 simples et 2 doubles, entre les 4 joueurs habituels de Vaires les mieux
classés (points virtuels) et la compo probable adverse ; seulement pour le championnat de France masculin.

Fabrication (ttvaires/v2.py, appelé à la fin de la copie Cloudflare/Netlify) : les pages du site actuel ne
sont pas modifiées ; la v2 reprend les données (le JSON intégré à chaque page publiée), les rechiffre avec la
clé du club dans `v2/donnees/*.json.chiffre` et copie les pages de `ttvaires/v2/`, qui ne contiennent aucune
donnée. Une mise à jour « Publication seule » suffit donc à la refaire. Si la fabrication de la v2 échoue, le
journal le signale (« Version 2 (/v2/) non publiée ») et le reste de la copie part comme avant. Pour voir les
pages à une autre date (essais) : `?date=AAAA-MM-JJ` dans l'adresse.

La recherche du haut trouve aussi les clubs et les joueurs du 77 ; l'accueil montre les résultats du dernier
tour des individuels (trois semaines) et le prochain tour.

Pas encore dans la v2 (pages du site actuel en attendant) : disponibilités de Paris, adversaires détaillés de Paris
et des jeunes, comparaison des clubs et poules du 77 ; simulateur « que faut-il pour monter ? », records du club ;
disponibilités cochées par les joueurs eux-mêmes et covoiturage (il faudrait un stockage partagé en ligne : à
décider).

## Espaces à leur propre adresse : /lundi/ (le roi du lundi)

Une page HTML fournie peut avoir sa propre adresse, à côté de /club/ : **/lundi/** sur chaque site
(https://ggping.netlify.app/lundi/, https://ggman23.github.io/ggping/lundi/,
https://ggping-pap.pages.dev/lundi/). Depuis le 17/11/2026 (page personnelle, avec des notes sur des
joueurs), elle a **son propre mot de passe, pas celui du club** : le secret GitHub
**`MOT_DE_PASSE_LUNDI`** (*Settings* → *Secrets and variables* → *Actions* → *New repository secret*),
choisi par l'administrateur et écrit nulle part ailleurs. **Sans ce secret, /lundi/ n'est pas publié du
tout.** Le navigateur le retient à part (« se souvenir ») : entrer dans l'espace club n'ouvre pas
/lundi/. Elle n'est pas listée dans l'espace club (ni dans /indivs/ ou /tournois/) : elle est pour
l'administrateur et l'application (onglet Lundi, qui la reconnaît toujours).

Dans le dépôt (public), la page est **scellée** (`ressources/espace-lundi.html.scelle`) avec la clé
publique de l'espace : on peut y déposer une nouvelle version sans connaître le mot de passe, et seule
la mise à jour en ligne, qui a le secret, sait l'ouvrir ; le mot de passe du club ne l'ouvre pas. La
mise à jour publie cette clé publique à …/lundi/cle-publique.txt. Une nouvelle version, sur le PC :

    python -m ttvaires.ressources espace lundi "C:\chemin\roi.html"

puis envoyer le dossier `ressources/` sur GitHub (ou m'envoyer la page). Si le mot de passe à part
change, la page déposée ne s'ouvre plus : la mise à jour le signale ; enregistrer la nouvelle clé
publique (`python -m ttvaires.ressources cle lundi <clé>`) et déposer de nouveau la page. Les versions
d'avant le 17/11 restent dans l'historique du dépôt, chiffrées avec le mot de passe du club.

## Individuels : /indivs/ (poules du critérium et forme des adversaires)

**/indivs/** sur chaque site (https://ggping-pap.pages.dev/indivs/, https://ggman23.github.io/ggping/indivs/,
https://ggping.netlify.app/indivs/), avec le **mot de passe du club** (déjà entré dans l'espace club :
ouverture directe ; lien dans « Autres espaces » de /club/). Menu à gauche (sur téléphone : la liste
d'abord) : la vue d'ensemble, puis chaque joueur de Vaires, rangés en Adultes, Jeunes et Féminines.
Pour chacun : sa poule (compétition, date, horaires, lieu avec le plan), son rang probable, et ses
adversaires du plus fort au plus faible, avec pour chacun les points virtuels, les parties gagnées sur
parties jouées depuis le début de la phase, les points gagnés ou perdus, les compétitions jouées
(championnat, critérium, tournois) et un niveau : **plus fort** (au moins 50 points virtuels de plus),
**à surveiller** (à moins de 50 points, ou plus faible mais à +30 points sur la phase), **à ta portée**.

- **Images à partager** : une image par poule (lisible sur téléphone, comme les autres), dans l'espace
  club, section « Individuels (poules du critérium) », et sur le site GitHub. Joueurs du plus fort au
  plus faible, ceux de Vaires sur fond bleu, critérium et tournois sous le nom ; colonne « Pour
  <prénom> » quand un seul joueur de Vaires est dans la poule. Leurs titres ne donnent que la poule et
  sa date (la liste des images est visible sans mot de passe ; les images, elles, sont chiffrées).
  Sur /indivs/, le bouton « Image de la poule à partager » ouvre celle de la poule dans l'espace club.
- **Résultats du tour** : une fois la date de la poule passée, la fiche de chaque joueur de Vaires a une
  carte « Résultats du tour » : sa journée (classement dans la poule, victoires, défaites, points gagnés ou
  perdus), le **classement de la poule** (victoires–défaites et points du jour de chacun, ceux de Vaires sur
  fond bleu) et **les parties de chacun** (adversaire et ses points, V ou D, manches, points gagnés ou
  perdus ; la sienne ouverte). La vue d'ensemble a une colonne « Tour » (classement, V–D, points). Ce sont
  les parties de critérium du jour du tour, tirées des parties déjà lues pour la forme : aucune requête de
  plus. Classement indicatif : victoires, puis, entre deux joueurs à égalité qui se sont rencontrés, le
  vainqueur de leur partie (≡), puis les points gagnés ; la place officielle du groupe (montées,
  descentes) vient du tableau final du tour, publié par le comité. Les résultats arrivent à la mise à jour
  qui suit leur saisie par le juge-arbitre (« Tout » ou « Individuels »).
  Une poule recopiée **sans date** (par exemple la liste des 24 qualifiées du tour régional dames) : le jour
  du tour est retrouvé dans les parties de critérium de ses joueurs (le jour où le plus de joueurs de la
  liste ont joué, après la recopie des poules et jusqu'à aujourd'hui ; il en faut au moins deux), avec la
  mention « date d'après les parties jouées ». Le journal de la mise à jour l'indique (« date du tour
  retrouvée dans les parties pour 1 poule(s) »).
- Liens : « Club » et « Tournois » en haut de /indivs/ (et dans son menu) ; « Individuels » en haut du
  menu de /club/ (« Aller à », avec « Tournois ») et dans ses « Autres espaces » (menu et accueil).

- Les poules viennent des convocations (PDF, captures WhatsApp) : je les recopie à chaque tour
  (licence, nom, points, club, catégorie) dans `ressources/indivs.json.chiffre`, chiffré avec le mot
  de passe du club (joueurs mineurs, dépôt public). Il suffit de m'envoyer les convocations du tour.
- À chaque mise à jour (« Tout », ou « Individuels » dans la liste des pages), les parties de la phase
  de chaque joueur des poules sont lues dans l'API de la FFTT (une requête par joueur, environ 200 par
  tour, gardées un jour). Le nom donné par l'API pour chaque licence est comparé à celui de la
  convocation : une licence mal recopiée est signalée (« licence ? » sur la page, et dans le journal).
- Sans le secret MOT_DE_PASSE_CLUB (ou si le mot de passe du club a changé depuis l'enregistrement des
  poules), la page n'est pas faite ; le bilan l'indique.
- Pour les relire ou les corriger soi-même : `python -m ttvaires.indivs exporter poules.json` (en clair :
  ne pas l'envoyer sur GitHub), puis `python -m ttvaires.indivs importer poules.json`.

## Tournois : /tournois/ (tournois à venir, par PingRadar)

**/tournois/** sur chaque site (https://ggping-pap.pages.dev/tournois/, https://ggman23.github.io/ggping/tournois/,
https://ggping.netlify.app/tournois/), avec le **mot de passe du club** (déjà entré dans l'espace club :
ouverture directe). Menu à gauche (sur téléphone : la liste « Autour de Vaires » d'abord, « ‹ Menu »
pour les autres) :

- **Autour de Vaires** : les 10 prochains tournois à moins de 100 km (à vol d'oiseau) ;
- **Ce week-end** et **Le week-end prochain** : à moins de 100 km ;
- **Île-de-France** et **Seine-et-Marne** : les 10 prochains ;
- **Chercher plus** : la recherche de PingRadar (filtre par points, distance, dates) et la liste
  officielle des tournois de la FFTT ;
- **Autres espaces** : l'espace club et les individuels (aussi en haut de la page : « Club », « Indivs »).

Chaque liste est le bloc « prochains tournois » que PingRadar (pingradar.fr, site indépendant, d'après
la liste des tournois de la FFTT) propose d'intégrer au site d'un club (page « Intégrer PingRadar ») :
un cadre sans script, sans cookie ni traceur, qui se met à jour tout seul. Rien n'est copié ni calculé
par l'outil, qui ne fait aucune requête pour les tournois ; la page ne change pas d'une mise à jour à
l'autre (elle est publiée à chaque mise à jour, comme /club/). Touche un tournoi pour ouvrir sa fiche
sur PingRadar (tableaux, tarifs, lien d'inscription).

- PingRadar le dit lui-même : sa liste n'est pas forcément complète ; vérifier sur la fiche du tournoi
  et, au besoin, dans la liste officielle de la FFTT. L'inscription se fait auprès de l'organisateur.
- Autres sources regardées et écartées : l'API de la FFTT (aucune liste de tournois pour le compte de
  l'outil), le flux de tournois-tt.fr (arrêté au 18/10/2026), PingMap (extraction automatique
  interdite par le site), MyPing Tournois (application, sans intégration prévue) : à utiliser à la main.

## Calendrier : /cal/ (dates de la saison)

**/cal/** sur chaque site (https://ggping-pap.pages.dev/cal/, https://ggman23.github.io/ggping/cal/,
https://ggping.netlify.app/cal/), avec le **mot de passe du club** (ouverture directe depuis /club/).

- Un mois à la fois, comme Google Agenda : ‹ ›, « Aujourd'hui », le jour du jour entouré ; sur
  ordinateur, chaque date porte son nom dans la case (« Équipes J5 », « Paris J1 », « Crit. T2
  jeunes ») ; sur téléphone, des points de couleur. Dessous, toutes les dates du mois en clair ;
  toucher un jour le met en avant dans cette liste. À gauche (en bas sur téléphone) : les prochaines
  dates, les autres espaces (club, individuels, tournois) et les liens du comité (agenda partagé du
  CD77 pour s'y abonner dans Google Agenda, PDF du calendrier, page sportive).
- Compétitions (boutons au-dessus du mois, retenus sur l'appareil) : championnat par équipes (le
  vendredi), championnat féminin (le samedi), championnat de Paris, championnat des jeunes,
  critérium fédéral (jeunes le samedi, seniors le dimanche, D4 le dimanche suivant) ; et, à cocher,
  les autres épreuves du comité et les dates limites d'inscription.
- Les dates viennent du calendrier 2026-2027 du comité (PDF de https://www.cdtt77.fr/sportive),
  recopiées dans `ttvaires/calendrier.py` ; les tests vérifient que chacune tombe le bon jour de la
  semaine. Le calendrier est prévisionnel : quand le comité en publie une nouvelle version, il suffit
  de m'envoyer le PDF. L'agenda partagé du CD77 n'est pas lu par l'outil (Google l'interdit aux
  robots) ; la page n'a besoin d'aucune mise à jour pour être à jour.
- Liens : « Club », « Indivs », « Tournois » en haut de /cal/ (et dans son menu) ; « Calendrier » en
  haut de /indivs/ et de /tournois/ (et dans leur menu) et dans « Aller à » de /club/. Pas de lien
  vers /lundi/.

## Classement des poules : égalités départagées comme le règlement le dit

Les classements des poules (page adversaires, page et image des classements) sont calculés par l'outil à partir
des feuilles de match : points-rencontres (victoire 3, nul 2, défaite 1, forfait 0), puis les égalités
(`ttvaires/departage.py`).

**Poules du comité 77** (PR, D1, D2..., pas le féminin 77/94) : règlement du championnat par équipes du comité
2026-2027, article 5.2 (toutes les parties sont jouées, article 6.1) :

- égalité de points : quotient général des points-parties (PG / PP de toute la poule), puis, pour les équipes
  encore à égalité, goal-average particulier sur leurs seules rencontres : points-rencontres, quotient des
  parties, des manches, des points-jeu, puis tirage au sort (non simulé : ex aequo) ; on recommence au premier
  critère chaque fois qu'une partie des équipes est départagée ;
- équipe battue par forfait ou pénalité : 28 à 0, chaque partie (14) perdue 3 manches à 0 (11-0 par manche) ;
- poule incomplète : l'équipe exempte d'une journée jouée marque les 3 points de la victoire.

**Autres poules** (régionales...) : article I.202 des règlements sportifs de la FFTT 2026-2027 :

- rencontres arrêtées au score acquis (I.202.1) : goal-average particulier, c'est-à-dire un classement sur
  les seules rencontres entre les équipes à égalité : points-rencontres, puis quotient des parties, des
  manches, des points-jeu, puis tirage au sort (non simulé : ex aequo) ;
- toutes les parties jouées (I.202.2) : d'abord le quotient général des parties (toute la poule), puis le
  même goal-average particulier pour celles encore à égalité ;
- dès qu'une partie des équipes est départagée, on recommence au premier critère avec celles qui restent à
  égalité, sur leurs seules rencontres ; une équipe battue par forfait l'est par toutes les parties prévues
  à 0 (I.202.2) ou la moitié plus une (I.202.1), 3 manches à 0 et 11-0 par manche.

Le cas se lit sur les scores d'une poule (le même total de points-parties partout : toutes jouées). Le journal
écrit la règle de chaque poule de Vaires, le total de points-parties par rencontre et les points d'exemptes
(« classement … : règlement du comité 77, article 5.2 … »). ≡ à côté du rang : équipe placée par le
goal-average particulier (détail au survol). Le règlement du comité (cdtt77.fr, que l'outil ne lit pas : le
site interdit toute lecture automatique) a été envoyé le 21/11/2026 ; une nouvelle version : me l'envoyer.

## Espace club rangé par rubriques (28/11)

« Il faut une navigation simple et intuitive avec les choses bien rangées » : l'accueil de **/club/** n'a plus que
de **gros boutons de rubriques**, chacun avec une ligne d'explication :

- **Championnat de France** : ses pages (Adversaires, Feuilles de match, Classements des poules, Résultats des joueurs
  et l'Excel, Effectif et brûlages), un bouton par équipe (Vaires 1 à 6, Vaires 1 F), et ses images rangées par type
  dans des sections qui se déplient (Récapitulatif, Classements, Feuilles de match, Résultats, Adversaires, Effectif,
  Programme) ;
- **Championnat de Paris** : /paris/ (poules et adversaires), Disponibilités, puis Feuilles de match, Classement de la
  poule et Résultats des joueurs ouverts directement sur Paris (`#paris`), Vaires 1 à 3, et les images de Paris
  (récapitulatif, classements, feuilles, résultats, infographie, affiche) ;
- **Championnat des jeunes** : de même (/jeunes/, pages ouvertes sur les jeunes) ;
- **Par équipe** (toutes les équipes, par championnat), **Joueurs du club** (Classement virtuel, Progression,
  Fiches, et leurs images), **Individuels** (/indivs/ et les images des poules), **Documents du club** (affiche,
  matériel, préparation mentale), **Archives** ;
- **Tout** : l'ancienne page complète (toutes les pages, toutes les images, archives, documents, « Tout
  télécharger »).

Dans chaque rubrique, une rangée de boutons en haut (France · Paris · Jeunes · Par équipe · Joueurs · Individuels ·
Documents · Archives · Tout) passe directement à une autre. Sur ordinateur, le menu de gauche n'a plus que ces
rubriques (et les autres espaces) ; sur téléphone, il n'y a plus de menu à gauche : l'accueil sert de menu et
« Retour » remonte d'un cran (document → sa rubrique → accueil). Adresses : `/club/#rubrique/paris`,
`/club/#rubrique/paris/rencontres_vaires.html` (page ouverte sur Paris). Les anciennes adresses (`#equipe/v2`,
`#archives/...`, un document) marchent toujours.

La page Club de la **v2** est rangée de la même façon : cartes de rubriques (France, Paris, jeunes, joueurs,
individuels, documents, Tout), rangée de boutons en haut de chaque rubrique (`/v2/club/#r/paris`), images en sections
qui se déplient ; une page s'ouvre sur un championnat avec `#doc/<page>/paris`.

## Championnat de Paris et des jeunes dans les pages du club (depuis le 28/11)

Les rencontres du championnat de Paris IDF (« L08_Championnat de Paris IDF », 21 rencontres de Vaires) et du
championnat des jeunes (« Chpt Jeunes par Equipes 77 », 14 rencontres) sont maintenant dans l'API de la FFTT
(mise à jour du 28/11). Elles sont lues comme celles du championnat de France (`fftt.CHAMPIONNATS`, toute la
saison : `fftt.bornes`), et les pages les montrent avec un **sélecteur en haut de la page** :
« Championnat de France · Championnat de Paris · Championnat des jeunes » (un championnat n'apparaît que s'il a
des données).

- **Pages concernées** : Résultats des joueurs, Feuilles de match, Classements des poules. Adresse :
  `#paris` ou `#jeunes` (ex. `rencontres.html#paris`), et pour une seule équipe `#paris/seule/v2` (Vaires 2
  de Paris). La page garde toutes les données ; le choix met celles du championnat demandé à la place de
  `<script id="donnees">` avant que la page ne les lise (`rendu.generer_html(..., autres=...)`).
- **Feuilles de match de Paris** : équipes de 9 (Honneur : 3 groupes de 3), 6 (Promotion d'Honneur : 2 groupes)
  ou 3 joueurs (Division 2) ; 9 parties par groupe. Chaque partie a son groupe (`resultats.groupes_des_parties` :
  les joueurs qui se rencontrent forment un groupe ; groupe 1 = celui des meilleurs joueurs de Vaires, règlement
  article 8), chaque groupe son score et ses points (6, 5 ou 4 par partie gagnée en groupe 1, 2 ou 3, article 7).
  Le résultat de la rencontre se lit en points-parties (ex. victoire 90-45).
- **Résultats des joueurs** : points gagnés ou perdus avec le coefficient du championnat lu dans l'API (Paris :
  0,75 ; jeunes : celui de l'API, 0,5 sinon), journées J1 à J7 sur la saison. La colonne **Virt.** (page et images,
  tous les championnats) est le classement virtuel du club, toutes compétitions (le même que la page Classement
  virtuel, faite maintenant en premier) ; « Total » = points gagnés dans ce championnat depuis la J1. Avant le
  28/11, « Points J5 » valait points officiels + total du seul championnat : pas le vrai classement virtuel.
- **/paris/ et /jeunes/** : scores de chaque rencontre et classement de la poule lus dans l'API
  (`paris.avec_resultats` : équipe reconnue par son numéro, rencontre par sa journée ; noms de la page gardés).
- **Classements des poules** : les poules de Paris et des jeunes, comme celles du championnat de France
  (points-rencontres de l'API, départage de l'article I.202).
- **Images** (à part, préfixe `paris_` ou `jeunes_`, groupe « Championnat de Paris » / « Championnat des jeunes »
  de l'espace club) : récapitulatif de la journée (`paris_recap_J1.png` : « CHAMPIONNAT DE PARIS », les 9, 6 et
  3 joueurs de chaque équipe rangés par groupe, top 5 des perfs ; photo : `import/photo_paris_J1.jpg`), une
  feuille de match par équipe (`paris_rencontres_J1_V2.png`, avec les groupes), résultats de la journée et cumul
  (`paris_resultats_J1.png`, `paris_resultats_cumul.png`), classements des poules (`paris_classements_poules.png`).
- **Par équipe** (espace club et v2) : pour les équipes de Paris et des jeunes, en plus de /paris/ (ou /jeunes/) :
  Feuilles de match, Classement de la poule et Résultats des joueurs, ouverts sur l'équipe (`#paris/seule/v2`),
  et leurs images (celles de leur championnat, sans celles des autres équipes).
- Le journal de la mise à jour écrit, pour chaque feuille de Paris, ce que l'API donne (aucun nom) : nombre de
  parties, points-parties, lettres des joueurs, groupes trouvés (« groupes {1: 9, 2: 9, 3: 9} »).
- **Effectif et brûlages de Paris** (sélecteur de la page Effectif, images `paris_effectif_...`) : règlement de la
  ligue, article 12 : est brûlé pour l'équipe 2 ou 3 un joueur qui a joué **3 fois ou plus** dans une équipe de
  numéro inférieur (`brulage.SEUILS` : France 2, Paris 3) ; il peut encore y jouer, mais **un seul brûlé par groupe
  de 3** (deux brûlés dans un même groupe : tous deux non qualifiés) ; un joueur ne joue qu'une équipe par journée.
  Toute la saison compte. Images : effectif du club, joueurs disponibles et joueurs brûlés de Vaires 2 et 3.
- **Classement virtuel** : colonne **Paris** (points gagnés ou perdus en championnat de Paris, coefficient 0,75) ;
  « Autre » ne compte plus Paris (Champ. + Paris + Autre = Total). Les colonnes Paris n'apparaissent qu'une fois le
  championnat commencé. Colonne Équipe (page et image) sur une seule ligne : **« V1 / P1 »** = Vaires 1 au
  championnat de France et P1 à Paris (l'équipe la plus jouée de chacun, `equipe_paris`) ; « V1 » seul pour un
  joueur qui n'a pas joué Paris, « P1 » seul pour un joueur qui n'a joué que Paris ; au survol, le détail de Paris
  (« P1 ×2, P2 »). Avant le 28/11 au soir, l'équipe de Paris était écrite sous l'équipe et sous les points :
  deux lignes par joueur.
- **Licences loisir** (28/11) : un joueur à licence loisir (« L » sur pingpocket.fr, sans points) peut avoir des
  parties que la FFTT compte (critérium). Les parties des licences loisir du club sont donc lues aussi : celles qui
  ont joué sont dans le classement virtuel (marquées « loisir », « (L) » sur l'image), la progression, les fiches et
  /77/ ; les autres restent écartées, et elles ne sont jamais proposées pour Paris (tableau des disponibilités). Le
  journal donne seulement des chiffres et des dates : « licences loisir : N au club, M avec des parties dans l'API
  cette phase ; parties par date : 14/11 ×7 » (pour voir si un tournoi est remonté à la FFTT).
- **Une seule mise à jour suffit** (28/11) : le classement virtuel est fait au début, avec les valeurs du mois
  enregistrées par la page des clubs du 77 de la mise à jour précédente. Quand cette page (faite à la fin) les
  change, le classement virtuel et les résultats sont refaits avec elles (`refaire_avec_les_valeurs_du_mois`, les
  parties sont déjà en cache) ; une page qui échoue garde sa première version.
- **Récapitulatif de Paris avec les jeunes** (28/11) : `paris_recap_J<n>.png` montre aussi les équipes jeunes de la
  dernière journée jouée du championnat des jeunes : titre « CHAMPIONNAT DE PARIS + CHAMPIONNAT JEUNES » (la
  seconde partie en bleu), bandeaux bleus « Vaires 1 (−15 ans) » et « Vaires 2 (−13 ans) » (catégorie lue dans la
  division de l'API, « MOINS 15 »). Disposition demandée par le club : Vaires 1, 2 et 3 de Paris l'une sous
  l'autre à gauche, les équipes jeunes l'une sous l'autre sous la photo, à droite le cadre des perfs des deux
  championnats, en top 15 (top 10 ou 5 seulement si la place manque ; `recap._emplacements_paris_jeunes`). Une équipe jeune
  sans feuille garde sa place (« Pas encore saisi »). Si Paris et les jeunes ne sont pas à la même journée : « Paris J2 · Jeunes J1 ». Le récapitulatif
  des jeunes seul (`jeunes_recap_J<n>.png`) n'est plus fait quand l'image de Paris existe.
- **Arrondi des images** (28/11) : 911,25 s'écrit 911,3, comme la FFTT et les pages (arrondi au-dessus à la moitié ;
  le format de Python arrondissait au pair : 911,2 sur l'image du classement virtuel, 911,3 sur la page).
- **Surnoms** (secret SURNOMS, import/surnoms.txt) : un surnom qui peut se confondre avec le nom d'un autre joueur de
  l'image (« Marc G » à côté de « Marc Go. ») n'est pas pris : le nom distinctif reste (« Marc Gu. »).
- **Récapitulatif** : deux joueurs du même prénom avec la même initiale (« Marc G » deux fois) : le début du nom
  les distingue (« Marc Gu. », « Marc Go. » ; `recap._distinction`).
- **Progression** : une image par équipe de Paris (`paris_progression_V1.png`...) avec ses joueurs (9, 6 ou 3 :
  ceux qui ont joué dans cette équipe de Paris, l'équipe la plus jouée pour chacun ; `progression.equipe_paris`).
- **Prochains adversaires** (`paris_adversaires_prochaine_journee.png`, `paris_adversaires_V1.png`...) : la prochaine
  journée de Paris, puis pour chaque équipe son prochain adversaire : les joueurs que cette équipe adverse a déjà
  alignés au championnat de Paris (feuilles de la poule, nombre de rencontres), puis les autres joueurs de son club
  les mieux classés (points, meilleur classement, forme de la phase).
- **v2** : les fiches des équipes de Paris ont leurs scores et leur classement (repris de /paris/), les onglets
  Feuilles de match, Poule, Effectif et Résultats ouverts sur Paris, et les feuilles de Paris (et des jeunes) sont
  lues dans les pages à sélecteur (`v2.SOURCES_CHAMP` : données `rencontres_paris`, `rencontres_jeunes`,
  `resultats_paris`).

## Championnat de Paris : /paris/ (les trois équipes de Vaires)

**/paris/** sur chaque site (https://ggping-pap.pages.dev/paris/, https://ggman23.github.io/ggping/paris/,
https://ggping.netlify.app/paris/), avec le **mot de passe du club** (ouverture directe depuis /club/).

- Championnat de Paris IDF 2026-2027 : Vaires 1 en Honneur (poule 1), Vaires 2 en Promotion
  d'Honneur (poule 2), Vaires 3 en Division 2 (poule 3) ; sept journées, le vendredi, du 27/11/2026
  au 04/06/2027.
- Même présentation que la page adversaires du championnat de France (`gabarit_championnat.html`, calqué
  sur `gabarit.html`, commun avec /jeunes/) : onglets **Récapitulatif** (les rencontres semaine par semaine : équipe, date,
  adversaire, lieu, score ; la semaine en cours ou prochaine encadrée ; filtre par équipe) et
  **Vaires 1 / 2 / 3** (calendrier de la saison avec le lieu, DOM ou EXT avec l'adresse de la salle
  adverse et un lien « plan » ; classement de la poule, vide pour l'instant ; « Adversaires — clique
  sur une équipe »). La fiche d'un adversaire : la rencontre, le lieu, les équipes du club en
  championnat de France, et son effectif : catégorie, classement officiel, phase (victoires/parties
  et points gagnés ou perdus, points virtuels), mensuel, meilleur classement (année), compétitions hors
  championnat, équipe du championnat de France où il joue (×nombre de rencontres) ; tris par points,
  meilleur classement, forme, parties jouées ; « qui a joué dans quelle équipe » du championnat de
  France. Pas de brûlage ni de composition probable : on ne sait pas qui joue en Paris.
- Bandeau tant qu'il manque des effectifs, des adresses de salle ou des meilleurs classements (lus sur
  pingpocket.fr par le PC) : lancer la mise à jour depuis le PC (option 8 : tout d'un coup).
- Données : poules et calendrier des documents de la ligue (PDF « Poules HO / PH / D2 »), recopiés
  dans `ttvaires/paris.py` (le premier nommé de la grille reçoit) ; les tests vérifient que chaque
  équipe rencontre les sept autres une fois, une seule rencontre par équipe et par journée, le
  vendredi. Nouveaux documents de la ligue : me les envoyer.
- **Clubs adverses** (17 : 6 du 77, 8 du 93, 3 du 94), sans numéro de licence dans la page (repères j1, j2…).
  Comme la page adversaires du championnat de France (`adversaires.recuperer_paris`, mêmes caches) :
  équipes et joueurs alignés par l'API de la FFTT, effectif complet et meilleur classement par
  pingpocket.fr (pages lues par **le PC**, options 1 et 8, envoyées au site), forme par l'API. Faite
  par l'étape adversaires de la mise à jour (`paris_vaires.html`, publiée à /paris/ comme /77/).
- **Disponibilités** (onglet de /paris/) : les joueurs du club (ceux du dernier classement virtuel : licences
  compétition, pas les loisirs), du mieux au moins bien classé aux points virtuels, une liste par journée (J1 à
  J7) : toucher le bouton d'un joueur (sans réponse → disponible → pas disponible), ou « Coller les réponses »
  (les noms reçus, un par ligne : accents, ordre prénom / nom et petites fautes reconnus ; les noms pas trouvés
  sont listés). « Image à partager » : disponibles à gauche (vert), pas disponibles puis sans réponse à droite
  (rouge, gris), noms seulement, à télécharger ou partager. Les réponses restent dans le navigateur (le
  téléphone) qui les a saisies ; la liste des joueurs vient de la mise à jour (`cache/joueurs_vaires.json`,
  écrit par l'étape du classement virtuel, jamais dans le dépôt).
- (Jusqu'au 28/11) Pas de résultats ni de compositions du championnat de Paris : ses rencontres n'étaient pas dans l'API
  de la FFTT (contrôle du 18/11/2026, mise à jour n° 89 : seulement le championnat de France, 42
  rencontres masculines et 7 féminines ; le journal le redit à chaque mise à jour, « Championnat de
  Paris dans l'API FFTT ? »). Les poules sont sorties le 17/11 : la ligue les saisira. Le jour où elles
  y sont, le bilan de l'étape adversaires l'écrit (« championnat de Paris maintenant dans l'API FFTT
  (N rencontres de Vaires) ») : on branchera alors scores, classement, compositions, « qui a joué
  où » et brûlages comme pour le championnat de France (la page a déjà le même format), avec les
  règles du championnat de Paris (règlement de la ligue).
- Liens : « Paris » en haut de /cal/, /indivs/, /tournois/ et /77/ (et dans le menu des trois
  premiers), dans « Aller à » et « Autres espaces » de /club/ ; /paris/ renvoie vers chacun. Pas de lien
  vers /lundi/.

## Championnat des jeunes : /jeunes/ (les équipes −15 et −13 ans)

**/jeunes/** sur chaque site, avec le **mot de passe du club** (ouverture directe depuis /club/), même
présentation que /paris/ (`gabarit_championnat.html`, commun aux deux pages).

- Championnat des jeunes par équipes 77, 2026-2027 : **Vaires 1 en moins de 15 ans** (poule 3, « A (C) »
  dans l'application de la FFTT, 8 équipes) et **Vaires 2 en moins de 13 ans** (poule 1, « A (A) »,
  7 équipes : une exempte à chaque journée). Pas d'équipe en moins de 11 ans. Poules recopiées des
  captures de l'application de la FFTT du 18/11/2026 dans `ttvaires/jeunes.py` ; dates : les vendredis
  du calendrier du comité (les mêmes que Paris) ; en moins de 13 ans, l'application n'a pas encore de
  dates ni de numéros de tour : « (à confirmer) », journées dans l'ordre de l'application.
- **Qui peut jouer** : la catégorie de l'équipe et les plus jeunes. Catégories de la FFTT, de deux ans en
  deux ans (âge atteint dans l'année où commence la saison) : poussins moins de 9 ans, benjamins 9-10,
  minimes 11-12, cadets 13-14. Moins de 15 ans : cadets, minimes, benjamins, poussins ; moins de 13 ans :
  minimes, benjamins, poussins (un minime 1 joue dans les deux équipes). Chaque fiche d'adversaire ne montre que les jeunes
  qui ont l'âge, **licences loisir comprises** (badge « loisir » : le club les changera pour les faire
  jouer ; pas de forme pour elles). Forme de **tous** les jeunes réinscrits (beaucoup sont à 500 points),
  depuis le début de la phase (la saison jusqu'en décembre).
- **Numéros des clubs adverses** : Monthyon et Dammartin connus ; les autres (Coulommiers, Roissy,
  Meaux, Fertois, Serris, Villeparisis, Saint-Thibault, Apozoir) retrouvés par leur nom dans les
  rencontres du comité 77 (API FFTT, celles de /77/, en cache) : `jeunes.trouver_clubs`, le journal
  écrit chaque association (« jeunes : SERRIS ATT -> 0877…… »). Un club pas retrouvé est signalé en
  haut de la page (« club pas encore lu ») : me le dire, j'ajoute son numéro dans `jeunes.CLUBS`.
- Effectifs et adresses : listes des licenciés de pingpocket.fr (déjà lues pour /77/), adresses des
  salles lues par le PC (lancer.bat) : bandeau tant qu'il en manque.
- Faite par l'étape adversaires de la mise à jour (`jeunes_vaires.html`, publiée à /jeunes/ comme /paris/).
  Ni score ni composition : les rencontres des jeunes ne sont pas encore dans l'API de la FFTT. Le
  contrôle de chaque mise à jour liste maintenant toute compétition par équipes du club autre que le
  championnat de France (Paris, jeunes) et le bilan l'écrit (« nouveau dans l'API FFTT : … ») : on
  branchera alors scores, classement, compositions et brûlages.
- Liens : « Jeunes » dans l'en-tête et le menu de /cal/, /indivs/, /tournois/, /77/, /paris/, et dans
  « Aller à » et « Autres espaces » de /club/. Sur téléphone, les liens des en-têtes passent sur deux
  lignes de trois.

## Clubs du 77 : /77/ (niveau de Vaires parmi les clubs du département)

**/77/** sur chaque site, avec le **mot de passe du club** (ouverture directe depuis /club/). Faite à
chaque mise à jour « Tout » (ou « Clubs du 77 » dans la liste des pages), et par l'option 5 du PC.

- **Clubs** : un tableau, une ligne par club (Vaires en jaune) : joueurs, femmes, hommes, poussins
  (P), benjamins (B), minimes (M), cadets (C), juniors (J), seniors (S), vétérans (V), meilleur
  joueur, moyenne des 4 et des 10 meilleurs (points mensuels), joueurs à 1000 points ou plus,
  équipes, et les équipes par division (« D2 ×3 », « F D1 » pour une équipe féminine). Toucher un
  en-tête trie, toucher un club ouvre sa fiche (équipes avec leur force estimée, 10 meilleurs joueurs).
  Recherche par nom et filtre par division.
- **Joueurs comptés** (en haut, pour toutes les vues ; chaque visite repart de « tout » ; tant qu'il n'est
  pas sur « tout », un bandeau le rappelle dans chaque vue, avec « Tout compter ») : femmes et hommes,
  femmes seulement ou hommes seulement ;
  toutes les catégories, les jeunes (P à J), les adultes (S et V) ou des catégories au choix ; toutes
  les licences (par défaut : le nombre de licenciés affiché par la FFTT et pingpocket, avec une colonne
  « dont loisir ») ou seulement les licences compétition. Seules les licences de la saison comptent.
  Les points (meilleur, moyennes, joueurs à 1000 points) ne concernent que les licences compétition.
- **Classements** : tous les clubs selon une mesure (joueurs, moyenne des 4 ou des 10 meilleurs,
  meilleur joueur, joueurs à 1000 points, joueuses, équipes, division de la meilleure équipe), Vaires
  en jaune, et sa place (« 34e sur 54 »).
- **Comparer** : 8 clubs au plus, choisis un à un ou d'un coup ceux d'une poule ; le tableau et une
  barre par mesure.
- **Poules** : les équipes d'une poule classées par **force estimée**, les favoris d'abord. Force
  estimée : la moyenne des points des 4 joueurs que le numéro de l'équipe lui donne dans son club
  (équipe 1 : les 4 meilleurs, équipe 2 : les 4 suivants...), parmi les joueuses pour une équipe
  féminine ; ni les brûlages ni les absences ne comptent : c'est un ordre de grandeur. En phase 2, les
  nouvelles poules apparaissent dès que la FFTT les publie (une mise à jour suffit).
- **Joueurs** : tous les licenciés compétition des clubs du 77, classés par **points mensuels** (le
  classement officiel du mois, pas les points virtuels : il faudrait une requête FFTT par joueur, des
  milliers). Filtres : femmes et hommes, femmes ou hommes ; catégorie, toute la catégorie (« Minimes »)
  ou précise (« Minimes 1 », « Minimes 2 », « Vétérans 45 »...) ; club ; recherche par nom (accents
  ignorés). Toucher un en-tête trie (nom, club, catégorie, points) ; les ex aequo ont la même place ;
  200 lignes, puis « afficher plus ». Joueurs de Vaires en jaune, avec leur nombre et la place du
  mieux classé. La fiche d'un club mène à ses joueurs (« Tous les joueurs du club »). Les noms ne sont que
  dans la page chiffrée (mot de passe du club).
- **Points virtuels et progression** : quand au moins 3 joueurs de la liste sur 4 ont leurs points
  virtuels (les jeunes par défaut ; tout le monde après une mise à jour « tous » ; lien « Voir les jeunes
  classés par progression »), quatre colonnes de plus :
  **Virtuels**, **+/−** (points gagnés ou perdus depuis le début de la phase, toutes compétitions :
  championnat, critérium, tournois...), **Parties** (victoires, défaites) et **Lu le** (date à laquelle ses
  parties ont été lues à la FFTT ; en orange si c'est il y a plus de 7 jours). Toucher « +/− » classe les
  joueurs qui progressent le plus. Sur téléphone, les points mensuels s'effacent pour laisser la place (un
  joueur pas encore lu montre ses points mensuels en gris) et la date est sous le nom.
  La fiche d'un club montre ses jeunes les plus en progression ; **Classements** et **Comparer** ont deux
  mesures de plus : moyenne des 4 meilleurs jeunes (virtuels) et points gagnés par tous les jeunes du club.

D'où viennent les données :

- **Équipes et divisions** : API de la FFTT. Les clubs sont ceux des rencontres des journées 1 et 2
  des divisions du comité (un club sans aucune équipe départementale n'apparaît donc pas) ; puis, pour
  chacun, ses rencontres de la phase (toutes ses équipes, toutes divisions). Environ 70 requêtes,
  gardées une semaine.
- **Joueurs** : listes de licenciés de pingpocket.fr (par catégorie et par état de licence), comme
  pour les clubs adverses : **lues par le PC** (option 5 de `lancer.bat`), une page toutes les 4
  secondes, au plus 60 nouvelles par lancement (environ 4 minutes), gardées un mois, puis envoyées au
  site avec les autres données du PC. La première fois, il faut deux ou trois lancements du PC pour
  avoir tous les clubs ; d'ici là, leurs colonnes affichent « — ». Une liste enregistrée depuis un
  navigateur dans le dossier `import\` sert aussi.
- **Points virtuels** (des **estimations** : seule la situation mensuelle publiée par la FFTT est
  officielle ; l'API ne donne ni points mensuels ni points virtuels, même avec un compte Premium,
  vérifié le 15/11/2026) : API de la FFTT (avec le compte licencié), une requête par joueur. Seulement par
  la mise à jour en ligne (le PC n'en a pas besoin : la page publiée est faite en ligne). **Une lecture
  par semaine** : la liste d'un joueur est relue si elle date d'avant le lundi de la semaine (les
  parties se jouent le vendredi soir et le week-end) ; la mise à jour automatique du lundi matin relit
  donc tout, les suivantes rien. Au lancement, on peut se limiter aux jeunes, aux adultes ou à aucun
  (par défaut : tous). Environ 220 listes par minute. Les autres gardent leur dernière lecture, avec sa
  date (« Lu le ») : rien ne disparaît.
- **Adversaires d'autres départements** (2 349 au 15/11/2026, rencontrés par 405 joueurs du 77 dans
  5 695 parties) : leurs listes sont lues de même (une fois par semaine), pour calculer leur valeur
  mois par mois. Leur liste est refaite à chaque lecture des joueurs du 77 : un nouvel adversaire (jamais
  lu) est lu en premier, sans rien faire. MAX_EXTERIEURS (3 000) borne seulement le nombre lu en une
  mise à jour : au-delà, le reste l'est à la suivante.
- **Troisième cercle** (28/11/2026, pour le championnat de Paris, le critérium et les tournois) : les
  adversaires de Vaires d'autres départements ont une valeur du mois calculée, mais avec les points de
  début de phase de leurs propres adversaires hors du 77 ; une défaite contre un joueur estimé à 851,2
  au lieu de moins de 850 donnait par exemple 912 au lieu de 911,3. Les adversaires de ces adversaires
  (hors du 77, et pas déjà lus) sont donc lus aussi, une fois par semaine, seulement pour eux : leur
  valeur devient presque exacte. Seule la première mise à jour de la semaine (celle du lundi matin)
  les lit : les suivantes reprennent les listes déjà lues. MAX_CERCLE3 (3 000, environ 14 minutes) ne
  sert que de borne de sécurité ; le reste serait lu à la mise à jour suivante (jamais lus d'abord).
  Durée permise d'une mise à jour : 120 minutes (timeout-minutes du workflow, un filet de sécurité
  contre une mise à jour bloquée ; le lundi dure 35 à 50 minutes). Le journal
  donne les nombres (« troisième cercle : N adversaires de Vaires d'autres départements, M de leurs
  adversaires hors du 77 », et combien restent à valeur estimée).
- **Forfaits des adversaires de Vaires d'autres départements (28/11)** : écart de 911,3 / 912 signalé. Les deux
  joueurs avaient joué le même adversaire de Paris (autre département), compté 852,2 par l'outil quand la FFTT le
  comptait à moins de 850 (défaite à −7 × 0,75 depuis 900, victoire à 5 × 0,75 depuis 902). Cause : une victoire
  par forfait en tournoi (+6), que la FFTT ne compte pas ; seul le détail d'une partie dit qu'elle est un forfait.
  Le détail des parties hors championnat des adversaires de Vaires d'autres départements est donc lu (une fois,
  gardé ; MAX_DETAILS_VAIRES_EXT = 1 500 par mise à jour ; 470 parties, 5 forfaits au 28/11). Mise à jour n° 122 :
  l'adversaire à 846,2, les deux joueurs à 911,25 et 914,75, comme la FFTT (911,3 et 914,8). Un autre joueur de la
  même équipe adverse, vérifié dans l'application FFTT (situation de fin octobre : 889,0), est à 889,0 dans l'outil.
  Piste écartée : la date de prise en compte des parties (effectiveDate) ; 0 partie sur 92 251 dans un autre mois
  que celui de sa date (décompte gardé au journal, par surveillance).
- **Affichage** : points virtuels à une décimale, comme l'appli FFTT (909,5). Règle de la FFTT
  (règlements administratifs, juillet 2025) : une situation mensuelle garde ses décimales ; les
  points publiés sur la licence sont arrondis à l'entier le plus proche (1525,50 donne 1526), et en
  fin de phase, après retrait de la dérive (−5,16 en phase 1 de 2025-2026, −5,95 en phase 2).
  Calendrier 2026-2027 (circulaire administrative) : période 1 = juillet, août et septembre, puis un
  mois par période ; une période est publiée le 9 du mois suivant en Premium et le 16 pour tous.
- **Classements officiels** : liens dans l'onglet Joueurs vers ceux de la FFTT (département, région,
  France ; situation du mois précédent). Nouvel onglet : le site de la FFTT refuse d'être affiché
  dans un cadre (X-Frame-Options SAMEORIGIN) et demande un code à recopier (captcha) : l'outil ne
  lit jamais ces pages.
- **Fiabilité d'une estimation** (pastille de couleur à côté des points virtuels, page des clubs du 77
  et classement virtuel de Vaires, avec une info-bulle) : le nombre de parties du joueur contre un
  adversaire dont la valeur du mois est elle-même estimée. Les parties du premier mois de la phase
  (septembre, avec juillet et août ; janvier en phase 2) sont calculées avec les points du début de
  phase de tous les joueurs : jamais estimées. La valeur d'un joueur lu reste exacte tant qu'il n'a joué
  que des joueurs lus ; dès qu'il a joué, après le premier mois, un joueur que l'outil ne lit pas (le
  plus souvent pour un joueur d'un autre département), elle est estimée pour les mois suivants.
  Gris : aucune partie de ce genre, mais des joueurs d'autres départements rencontrés, tous avec une
  valeur calculée d'après leurs parties, presque sûre (un forfait non vérifié chez eux peut laisser un
  petit écart) ; vert : 1 à 5 parties, très proche ; orange : 6 à 20, quelques points d'écart
  possibles ; rouge : plus de 20, moins sûre ; sans pastille : que des joueurs du 77, valeurs connues.
  Au 15/11/2026 : 2 332 joueurs, 2 145 sans pastille verte, orange ou rouge (dont 218 gris), 151
  verts, 32 orange, 4 rouges. Une partie ne change
  que si l'erreur sur la valeur de l'adversaire fait passer l'écart dans une autre tranche du barème.
  Seuils (mensuel.SEUILS) à revoir en comparant quelques joueurs de chaque couleur à la FFTT ; le
  journal donne le nombre de joueurs de chaque couleur.
- **Forfaits** : la liste des parties d'un joueur ne dit pas qu'une partie a été gagnée par forfait
  (la FFTT ne la compte pas) ; seul le détail de la partie le dit. Le détail des parties hors
  championnat (critérium, tournois...) est donc lu une fois puis gardé : au plus 2 500 nouvelles par
  mise à jour (environ 11 minutes), celles des joueurs choisis, les plus récentes d'abord (6 600
  environ au 15/11 : trois mises à jour « tous » pour tout vérifier, ensuite seulement les nouvelles).
  La note de la page dit combien sont vérifiées.
- **Calcul mois par mois** : pour chaque partie, la FFTT prend la valeur des deux joueurs à la fin du
  mois précédent, pas leurs points du début de saison (que l'API donne dans chaque partie). L'outil
  refait donc le calcul mois après mois pour les joueurs du 77 (référence : points du début de phase
  + gains des mois précédents ; un adversaire hors du 77 garde ses points). Juillet et août comptent
  avec septembre (les périodes de la FFTT commencent en septembre). Vérifié sur la liste des parties
  d'un joueur dans l'application FFTT : ses parties d'octobre ne s'expliquent qu'avec ses points de fin
  septembre, et ses tournois de fin août sont dans la même situation mensuelle que septembre. Au
  survol de « +/− » : les points gagnés mois par mois (« sept. +12 · oct. +8 · nov. −2 »).
- **Pages de Vaires** (classement virtuel, fiches des joueurs, progression, résultats, forme des
  adversaires et des individuels) : même calcul mois par mois. La page des clubs du 77 enregistre la
  valeur de chaque joueur du 77 au début de chaque mois (fichier `references_77.json` du cache de la
  mise à jour en ligne) ; les pages de Vaires la relisent à la mise à jour suivante (elles passent
  avant la page des clubs du 77). La page Résultats garde son cumul à partir des points officiels de
  la phase. Sans ce fichier (PC, ou avant la première mise à jour des clubs du 77), le calcul reste sur
  les points de la phase ; la note de chaque page dit lequel est utilisé. Les clubs du 77 passent après les adversaires : si
  la FFTT refusait des requêtes pendant la lecture des jeunes, la page des adversaires serait déjà faite.

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

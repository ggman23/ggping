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
du site* → *Run workflow* (choix des pages : tout, résultats, effectif, virtuel, adversaires).

Une page non choisie lors d'une mise à jour reste celle de la mise à jour précédente (sa date
est affichée sur l'accueil).

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

## Rubriques de l'espace club : Matériel, Prépa mentale

Après les archives, le menu de /club/ (et l'accueil, en tuiles) a des rubriques permanentes faites
de documents fournis, publiés tels quels : une page HTML (Matériel : forums et communautés sur le
matériel) et des PDF (Prépa mentale). Sur ordinateur, un PDF s'affiche dans la page ; sur téléphone
(et dans l'application), « Ouvrir le PDF » le donne au lecteur PDF de l'appareil. Une page HTML
fournie s'affiche isolée de l'espace club (elle n'a accès ni au mot de passe ni aux autres documents).

Les documents sont dans le dossier `ressources/` du dépôt, **chiffrés avec le mot de passe du club**
(le dépôt est public, eux ne le sont pas) ; `ressources/ressources.json` donne l'ordre des rubriques,
les titres et les descriptions. Pour ajouter ou remplacer un document, sur le PC :

    python -m ttvaires.ressources ajouter "Prépa mentale" "C:\chemin\guide.pdf" --titre "Guide du joueur" --description "26 pages"

(le mot de passe du club est demandé), puis envoyer le dossier `ressources/` sur GitHub. Une
nouvelle rubrique est créée à la fin si son nom n'existe pas. Si le mot de passe du club change,
ces documents ne s'ouvrent plus avec la nouvelle clé : la mise à jour le signale dans son journal et
ne les publie pas ; il faut alors les ajouter de nouveau.


Une image (png, jpg) peut aussi être un document de rubrique : elle s'affiche comme les images du
site, avec « Partager » sur téléphone (ex. le mémo sac de sport, version image du PDF).

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

## Championnat de Paris : /paris/ (les trois équipes de Vaires)

**/paris/** sur chaque site (https://ggping-pap.pages.dev/paris/, https://ggman23.github.io/ggping/paris/,
https://ggping.netlify.app/paris/), avec le **mot de passe du club** (ouverture directe depuis /club/).

- Championnat de Paris IDF 2026-2027 : Vaires 1 en Honneur (poule 1), Vaires 2 en Promotion
  d'Honneur (poule 2), Vaires 3 en Division 2 (poule 3) ; sept journées, le vendredi, du 27/11/2026
  au 04/06/2027.
- Menu : la prochaine journée (les trois rencontres de Vaires, domicile ou extérieur, l'adversaire et
  son département), chaque équipe (son calendrier, la journée suivante encadrée, les journées passées
  grisées ; sa poule ; toutes les rencontres de la poule, journée par journée), toutes les dates ;
  et les autres espaces.
- Données : poules et calendrier des documents de la ligue (PDF « Poules HO / PH / D2 »), recopiés
  dans `ttvaires/paris.py` (le premier nommé de la grille reçoit) ; les tests vérifient que chaque
  équipe rencontre les sept autres une fois, une seule rencontre par équipe et par journée, le
  vendredi. Aucune requête : la page ne change qu'avec ces documents (m'envoyer les nouveaux PDF).
- Résultats, compositions, forme des adversaires, comme dans /club/ pour le championnat de France :
  seulement si l'API de la FFTT a les rencontres du championnat de Paris. La mise à jour le vérifie
  (journal : « Championnat de Paris dans l'API FFTT ? », compétitions par équipes du club sur la
  saison, poules de Paris trouvées ; aucun nom de joueur).
- Liens : « Paris » en haut de /cal/, /indivs/, /tournois/ et /77/ (et dans le menu des trois
  premiers), dans « Aller à » et « Autres espaces » de /club/ ; /paris/ renvoie vers chacun. Pas de lien
  vers /lundi/.

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

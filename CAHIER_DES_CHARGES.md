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
- Onglets « Meilleures perfs » et « Pires contres » (demande du 06/10/2026) : classement des
  parties de simple de la phase, toutes compétitions, par points gagnés (victoires) ou perdus
  (défaites) sur une partie. À points égaux, la plus grande différence de classement passe
  devant ; ex aequo si même écart. Colonnes : joueur (ses points), adversaire (ses points),
  écart (points de l'adversaire − points du joueur), points, compétition, date. Choix « toutes
  les parties » ou « une ligne par joueur » ; les 30 premières affichées, le reste sur demande.

## Vérifications de complétude (18/10/2026)

- Demande : savoir, à la fin de chaque option du menu, si les résultats de toutes les équipes ont
  bien été récupérés pour chaque journée (exemple : les 21 équipes de Lognes ; un lancement le
  lundi peut précéder la saisie de certains résultats).
- État de chaque rencontre jouée, d'après son détail dans l'API FFTT : complète (score et
  compositions), forfait, résultat non saisi, score sans feuille de match, non récupérée (API
  muette), du jour (pas encore attendue). Les rencontres incomplètes ne sont pas gardées en cache
  et sont relues au lancement suivant. Une feuille complète est relue pendant 10 jours après la
  rencontre (au plus toutes les 6 h), pour prendre en compte une correction ; ensuite gardée.
- Menu : option 9 pour refaire les pages et les images sans rien télécharger (données du dernier
  lancement, rien envoyé au site) ; 0 pour quitter.
- Bilan équipe par équipe et journée par journée (équipes complètes / équipes qui ont joué ; les
  exemptes ne sont pas attendues ; une équipe masculine et une féminine de même nom comptent pour
  deux). Option 1 : toutes les rencontres des poules de Vaires et de toutes les équipes des clubs
  adverses (dans le championnat où ils rencontrent Vaires), bilan par journée et par club.
  Options 2 à 4 : les équipes de Vaires. Le classement virtuel contrôle en plus les parties non
  lues et la cohérence entre feuilles de match et liste des parties de chaque joueur.
- Affichage : console (détail puis bilan final avant la pause), bandeaux dans les pages, onglet
  « Vérifications » et alerte dans la fiche du club concerné sur la page adversaires.
- Contrôle du 18/10/2026 : 31 clubs (dont Lognes, 21 équipes) et 409 rencontres, tous complets
  pour les J1 à J3.

## Lancement depuis un téléphone (18/10/2026)

- Demande : lancer les mises à jour depuis un téléphone et y consulter ou télécharger les
  résultats.
- Réalisation : workflow GitHub Actions « Mise à jour du site » (lancement manuel avec le choix
  des pages, et automatique samedi, dimanche, lundi et mardi vers 8 h) qui exécute l'outil sur les
  serveurs de GitHub et publie le résultat sur GitHub Pages (https://ggman23.github.io/ggping/).
- Données personnelles (dont mineurs) : le site est public mais chaque page est chiffrée
  (AES-256-GCM, clé PBKDF2-SHA256 tirée du mot de passe du club, secret GitHub
  `MOT_DE_PASSE_SITE`) et déchiffrée dans le navigateur ; noindex et robots.txt. Rien n'est
  publié sans mot de passe. L'Excel est chiffré aussi et déchiffré au téléchargement.
- Page d'accueil (non chiffrée, sans nom de joueur) : pages et dates, bilan des vérifications,
  bouton « Lancer la mise à jour » (API GitHub, jeton à droits limités enregistré seulement sur
  le téléphone) avec suivi de l'avancement.
- Une page non régénérée reste celle de la mise à jour précédente (reprise du site en ligne).
- Limites en ligne : pingpocket.fr inaccessible depuis GitHub, dossier `import` resté sur le PC
  (listes des licenciés non publiées) : effectifs limités aux joueurs alignés.
- Mise en place par le propriétaire du dépôt : activer Pages (source GitHub Actions), créer le
  secret, premier lancement. Voir PUBLICATION.md.

## Même résultat sur le PC et sur le téléphone (18/10/2026)

- Exigence : les pages produites en ligne doivent être exactement celles du PC (sinon la mise à
  jour par téléphone ne sert pas).
- Écarts à combler : pingpocket.fr inaccessible depuis GitHub, dossier `import` seulement sur le PC.
- Solution : après chaque lancement sur le PC (si le lien est réglé, option 7), l'outil envoie sur
  GitHub une archive chiffrée (mot de passe du site) du dossier `import`, des pages de pingpocket
  en cache et de l'état de la page effectif, pièce jointe de la version « donnees-pc » (remplacée
  à chaque envoi), puis lance la mise à jour du site. En ligne, l'archive est déchiffrée et
  extraite avec les dates d'origine, et pingpocket n'est pas interrogé (mode « cache seul ») ;
  l'API FFTT est relue en direct.
- Ajustements pour l'égalité stricte : la page adversaires reprend les dernières pages de
  pingpocket téléchargées quand le site ne répond pas (sur le PC comme en ligne) ; l'ordre des
  rencontres de l'API (variable à date égale) est fixé ; les joueurs « nouveaux » restent signalés
  tant que la liste des licenciés ne change pas (relancer ne les efface plus).
- Contrôle : lancement PC puis lancement en ligne à partir de l'archive : données identiques pour
  les quatre pages (hors heure de génération) et même contenu Excel.

## Images à partager (19/10/2026)

- Demande : une version image des tableaux, la plus lisible possible sur un téléphone, sur le PC
  comme en ligne, incluse dans « Tout télécharger ».
- Images produites à chaque lancement (PNG, Pillow, police Liberation Sans fournie : mêmes images
  sur le PC et en ligne) :
  - classement virtuel (colonnes Éq., Pts off., Champ., Autre, Total, Virt., Clt, V/D de même
    largeur, colonne du nom réduite) ;
  - adversaires : la prochaine journée ; pour chaque équipe de Vaires, le prochain adversaire avec
    composition probable, renforts possibles et les 8 mieux classés n'ayant pas encore joué ;
  - résultats : la dernière journée triée par points gagnés sur la journée (« Meilleure victoire »
    sur deux lignes) ; le cumul trié par points gagnés au total ;
  - effectif : vue du club (équipes jouées, coche = peut jouer, flamme = brûlé) ; pour chaque
    équipe masculine 2 à 6, ses joueurs brûlés.
  - feuilles de match : une image par rencontre de la dernière journée (parties, score des
    manches, bilan des joueurs).
  - adversaires : la fiche de chaque équipe prend la largeur de son contenu (720 points au moins,
    sans colonne vide) ; un sous-titre trop long (adresse) passe sur 2 lignes.
- Copie de secours sur Netlify (https://ggping.netlify.app/) après chaque mise à jour du site
  GitHub : accueil = page des adversaires en clair (demande du club : visible par tous ; non
  référencée : robots.txt, X-Robots-Tag noindex) ; /gg/ = copie du site GitHub re-chiffrée avec un
  mot de passe propre (secret MOT_DE_PASSE_GG, pour les capitaines ; celui du site GitHub reste
  secret ; sans ce secret, /gg/ n'est pas publié). /club/ = espace club (secret MOT_DE_PASSE_CLUB) :
  menu des pages, de l'Excel et des images (barre latérale sur ordinateur, plein écran sur
  téléphone), affichage dans la page (cadre pour les pages, image, fiche de téléchargement pour
  l'Excel), Télécharger / Partager / Menu / Tout télécharger, sans lancement de mise à jour ;
  fichiers re-chiffrés avec la clé du club sous leur nom d'origine, clé mémorisée à part de /gg/. Envoi par l'API Netlify (archive zip) depuis le
  workflow, secret NETLIFY_AUTH_TOKEN ; sans jeton, rien n'est fait ; un échec n'empêche pas la
  publication GitHub.
- Archives des journées passées : la journée N est archivée dès que la N+1 a commencé, refaite à
  la date de la veille de la N+1 (option date de référence du programme : résultats, feuilles de
  match, classement virtuel s'arrêtent à cette date ; la page adversaires se place à cette date),
  publiée une fois pour toutes dans le site (archives/<saison>-P<phase>-J<n>/, petit site chiffré
  complet, repris à chaque mise à jour) ; archives manquantes reconstruites (J1, J2 à la mise en
  place). Accueil GitHub et /gg/ : section Archives ; /club/ : rubrique Archives (vue par journée,
  Retour vers l'archive, fichiers téléchargés préfixés J<n>_). Netlify : chiffrement stable (même
  contenu, même fichier) et envoi par empreintes (seuls les fichiers modifiés partent).
- Récapitulatif de la journée (`recap_J3.png`, avec les feuilles de match) : copie exacte de l'image
  du club (faite avec Excalidraw) : polices Lilita One et Excalifont (SIL OFL, fournies), palette
  Excalidraw (rouge #e03131, vert #2f9e44, orange #f08c00, jaune #ffec99, texte #1e1e1e), mise en
  page mesurée sur le modèle (1280 x 987 pour 7 équipes ; rangées de 3 blocs en plus au-delà).
  Résultat en points-parties domicile – extérieur ; Victoire en vert, Défaite en rouge, Égalité en
  orange ; astérisque orange pour une perf ; top 5 des perfs (plus grand écart de points, points
  des joueurs battus). Photo `import/photo_J<n>.jpg` et logos `import/logo_gauche|droite.png`
  collés s'ils existent (envoyés au site avec les données du PC, photo réduite si lourde) ; noms
  affichés : prénom (+ initiales du nom si prénom partagé dans l'image) ou `import/surnoms.txt`.
- Statistiques de visite de la copie Netlify (facultatif, variable GitHub GOATCOUNTER = code d'un
  compte gratuit goatcounter.com) : accueil public (une page vue par chargement), /club/ (accueil,
  écran de connexion, chaque document et archive ouverts ; événements connexion, connexion refusée,
  téléchargement, partage, tout télécharger) et accueils de /gg/ (ouverture, téléchargement, image
  vue, partage, tout télécharger, mise à jour lancée). Appareils différents : chaque appareil se
  signale une fois par jour, semaine et mois (et à sa première visite), au total et par espace
  (événements appareils/<période>, appareils/<espace>/<période>, appareils/nouveaux), grâce à un
  mémo local de dates, sans identifiant. Pas d'adresse IP. Sans cookie ; noms de fichiers seulement ;
  script count.v5.js figé et vérifié (integrity SRI). Site GitHub jamais compté.
- Crédits Netlify (gratuit : 300/mois, 15 par mise en ligne) : la copie n'est envoyée que si son
  contenu a changé. Empreinte (HMAC avec la clé du site, publiée dans signature.txt) des pages
  déchiffrées sans genere_le, des bilans, des noms de fichiers, des archives, des surnoms et images
  du dossier import, du code de l'outil et des réglages ; identique à celle en ligne : pas d'envoi.
  Option du workflow « forcer_netlify » pour envoyer quand même.
- Umami Cloud en plus (identifiant du site dans le workflow, variable UMAMI pour le changer) : mêmes
  pages vues et actions (événements nommés par l'action, détail espace et fichier), visiteurs,
  temps passé, parcours, retour des visiteurs, vitesse de l'accueil. Script servi par le site (copie
  figée ttvaires/umami.js, licence MIT). #toggle-goatcounter coupe aussi Umami (umami.disabled).
- Classements des poules (avec la page adversaires, mêmes données : classements calculés à partir
  des feuilles de match) : page `classements_vaires.html` (publiée sous classements.html) et image
  `classements_poules.png` sur le modèle proposé par le club : fond sombre, bandeau (logo du club,
  raquette et balle dessinées, fumée rouge), « CLASSEMENTS DES POULES » / « APRÈS LA JOURNÉE 03 •
  PHASE 1 • 2026–2027 », une carte par équipe (bandeau rouge « VAIRES 1 », « CLASSEMENT DE LA
  POULE », division et poule ; colonnes # ÉQUIPE PTS J V N D ; ligne de Vaires en rouge), deux par
  rangée, la dernière seule si leur nombre est impair, légende en bas. Police DejaVu Sans
  (fournie). Logo : celui du club, fourni (ttvaires/logo_club.png, découpé dans l'image du club) ;
  `import/logo_club.png` (sinon `logo_gauche.png`) le remplace.
  Section d'images « Classements des poules » à part (après le récapitulatif) sur le site, /gg/ et
  /club/ (en tuile sur l'accueil de /club/). Aucun nom de joueur dans la page.
- Page « Feuilles de match » (avec l'option 2 du menu, sans téléchargement en plus : mêmes feuilles
  que les résultats) : chaque rencontre de Vaires, journée par journée, avec chaque partie, les
  joueurs (lettres de la feuille, points), le score de chaque manche vu de Vaires, le score de la
  rencontre après chaque partie et le bilan des joueurs. Publiée sur le site (rencontres.html).
- Lisibilité : largeur 1080 points, texte 26 points, nom abrégé « NOM P. » si besoin, 25 lignes au
  plus par image (au-delà, plusieurs images numérotées : une image très haute serait réduite par
  les messageries). En plus, et sans rien changer aux images numérotées, chaque tableau découpé est
  aussi donné en une seule image verticale (titres des colonnes répétés aux mêmes coupures).
- Pages HTML : en-têtes « Autre » et « Virt. » et colonnes de même largeur dans le classement
  virtuel ; « Meilleure victoire » sur deux lignes dans les résultats.
- Site : images chiffrées comme les pages ; section « Images à partager » (voir, télécharger,
  partager) ; « Tout télécharger » inclut les images. Les images d'une page sont remplacées à
  chaque mise à jour de cette page.

## Forme des joueurs adverses (11/11/2026)

Demande : pour les adversaires des équipes de Vaires, voir qui joue et qui est en forme (un 750 qui a
gagné 12 parties sur 12 et déjà +46 points virtuels n'est pas un 790 qui en a gagné 2 sur 12 avec
−67), et qui joue aussi le critérium, les individuels ou des tournois.

- Joueurs suivis : ceux des clubs que Vaires doit encore rencontrer (rencontre à venir ou pas encore
  saisie), déjà alignés cette phase, ou réinscrits à plus de 500 points (ils peuvent jouer critérium
  ou tournois sans avoir encore joué en championnat).
- Pour chacun : parties de simple depuis le début de la phase dans toutes les compétitions (API
  FFTT, une requête par joueur, relue une fois par jour), victoires, défaites, points gagnés ou
  perdus avec le barème et le coefficient de chaque compétition (même calcul que le classement
  virtuel de Vaires), points virtuels, et le détail par famille : championnat, critérium fédéral,
  tournois, autres (finales par classement, jeunes, vétérans...).
- Pour ménager l'API, le détail de chaque partie hors championnat n'est pas demandé : seules les
  feuilles de match déjà lues disent si une partie est non comptée ou perdue par forfait. Une
  partie sans adversaire est écartée ; un forfait déclaré en cours de compétition individuelle
  alors que les deux joueurs sont inscrits compterait (rare).
- Page adversaires : « 12/12 +46 » (parties gagnées sur parties jouées, points) après chaque joueur
  des listes (composition probable, renforts, montées...) ; dans l'effectif, colonnes « Phase » (avec
  les points virtuels) et « Hors championnat » (« Critérium 3/3 +18 », « Tournois 2/5 −4 »), tri par
  points, par forme ou par nombre de parties.
- Image du prochain adversaire : colonne « Phase » et compétitions individuelles dans la dernière
  colonne (« critérium 3/3 · tournois 1/2 »).

## Individuels : poules du critérium (11/11/2026)

Demande : récupérer les poules d'individuels des joueurs de Vaires (adultes, jeunes, féminines) et
regarder, comme pour les adversaires en championnat, les performances de leurs adversaires de poule,
pour voir qui est dangereux ; le tout dans une page comme /club/, à l'adresse /indivs/, avec un menu à
gauche.

- Source : les convocations du tour (PDF du CD77 et du critérium jeunes filles 77/94, captures des
  poules adultes, liste des qualifiées R2 dames de la Ligue). Recopiées une fois (licence, nom,
  prénom, points, club, catégorie) dans ressources/indivs.json.chiffre (clé du club). Tour 2 :
  13 poules, 18 joueurs de Vaires (10 adultes, 6 jeunes, 2 féminines).
- Forme de chaque joueur des poules : même calcul que la forme des adversaires en championnat
  (virtuel.forme_joueurs) ; nom de l'API comparé à celui de la convocation (licence mal recopiée).
- Niveau de chaque adversaire pour le joueur de Vaires, d'après les points virtuels : plus fort
  (≥ +50), à surveiller (à moins de 50 points, ou plus faible mais à +30 points sur la phase), à ta
  portée ; rang probable dans la poule.
- Page indivs_vaires.html (gabarit_indivs.html), publiée chiffrée sur le site GitHub (« Individuels »)
  et à son adresse /indivs/ avec le mot de passe du club (clé retenue avec celle de /club/), pas parmi
  les documents de /club/ (lien « Autres espaces »). Faite avec « Tout » et le choix « Individuels ».
- Images à partager (12/11) : une par poule (images_indivs), section « Individuels » de /club/ ; titres
  sans nom de joueur. Liens croisés /indivs/ ↔ /club/ (bouton « Espace club », « Autres espaces »).

## Progression des joueurs (12/11/2026)

Demande : des graphes, dans une autre rubrique, qui montrent au fil des semaines si un joueur de
Vaires progresse ou régresse ; choisir son joueur dans une liste déroulante, pouvoir en sélectionner
plusieurs pour les comparer (en restant lisible) ; des images si c'est lisible.

- Données : les parties du classement virtuel (toutes compétitions), cumulées par semaine (lundi au
  dimanche) à partir des points officiels de la phase (progression.py) ; aucune requête de plus.
- Page progression_vaires.html (gabarit_progression.html, publiée « Progression des joueurs » après
  le classement virtuel, dans /club/ aussi) : liste déroulante par équipe, jusqu'à 5 joueurs
  comparés (couleurs vérifiées pour le daltonisme en clair et en sombre ; chaque joueur garde sa
  couleur), points virtuels ou évolution (±, choisie seule dès deux joueurs), bulle au survol ou au
  toucher (sous le graphe sur téléphone), noms au bout des courbes s'ils ne se chevauchent pas,
  tableau des joueurs affichés ; tous les joueurs avec mini-courbe, progression sur la phase et sur
  les 4 dernières semaines (tendance : ±5 points), tri et filtre par équipe ; choix gardés sur
  l'appareil.
- Images : une par équipe (petits multiples : une courbe par joueur qui a joué, échelle propre d'au
  moins 40 points, niveau de départ en trait fin), groupe « Progression des joueurs ».
- Ajout (12/11) : sur le même graphe, matchs, perfs et contres (points officiels de la phase : perf =
  victoire contre plus de points, contre = défaite contre moins de points), par joueur au-dessus de
  la courbe, ▲ / ▼ sur les semaines concernées, dans la bulle, les tableaux et les images ; lecture :
  « baisse sans contre : perdu contre plus fort », « baisse avec n contres », « progression avec n
  perfs », « progression sans perf », « stable ».
- Changement (12/11) : progression et tendance depuis le début de la saison (1er septembre) et non plus
  sur les 4 dernières semaines ; tendance : ±10 points. En phase 2, la courbe reprend la phase 1 (ses
  parties, cumulées à partir de ses points officiels) puis passe aux points officiels de janvier :
  recuperer_virtuel garde pour cela les parties de la phase 1 (déjà dans la liste de la saison ; leur
  détail n'est pas redemandé). Départ des courbes : les points au 1er septembre (tournois d'été compris).

## Tournois à venir (11/11/2026)

Demande : la liste des tournois de tennis de table d'Île-de-France ou à 100 km de Vaires, dans une page
/tournois/ comme /club/, avec des liens pour aller de /tournois/ à /club/ et /indivs/ et réciproquement.
Pas d'onglet dans l'application pour l'instant.

- Sources regardées : l'API de la FFTT (vérifiée pendant les mises à jour n° 56 et 57 avec le compte de
  l'outil : point d'entrée vide, documentation JSON-LD limitée aux classes techniques, pas d'OpenAPI ;
  vérification retirée ensuite) ; le flux RSS de tournois-tt.fr (autorisé mais arrêté au 18/10/2026) ;
  PingMap (robots.txt : extraction automatique de sa base interdite) ; MyPing Tournois (application
  web) ; PingRadar (pingradar.fr, d'après la liste des tournois de la FFTT, collecte du jour), qui
  propose un bloc à intégrer au site d'un club (gratuit, sans compte, sans script ni cookie,
  frame-ancestors *) ; ses adresses /api/ sont interdites aux robots : rien n'est extrait.
- Page fixe gabarit_tournois.html (aucune donnée de mise à jour), publiée par netlify.PAGES_FIXES à
  /tournois/ sur les trois sites, chiffrée avec le mot de passe du club (clé retenue avec celle de
  /club/) : cinq blocs (100 km autour de Vaires, code INSEE 77479 : 10 prochains, ce week-end, le
  week-end prochain ; Île-de-France ; Seine-et-Marne), format compact sur téléphone, liens vers la
  recherche de PingRadar et la liste de la FFTT.
- Liens : /tournois/ → « Club », « Indivs » (en haut et dans le menu) ; /indivs/ → « Club »,
  « Tournois » ; /club/ → « Aller à » en haut du menu (individuels, tournois) et « Autres espaces ».
- Changement (11/11) : /lundi/ (le roi du lundi) n'est plus listé dans /club/ (ni « Aller à » ni
  « Autres espaces ») : il est pour l'administrateur et l'application seulement.

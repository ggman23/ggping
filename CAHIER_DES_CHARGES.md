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
- On ignore coupes et Championnat de Paris (Paris : page /paris/ ajoutée le 18/11/2026, voir plus bas).

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

## Fiches des joueurs (12/11/2026)

Demande : une page qui récapitule tout pour chaque joueur, avec une liste déroulante plutôt que 90
liens (format laissé à l'appréciation), et en plus des statistiques de manches (% de victoires en 3,
4 ou 5 manches), les remontées, et le bilan selon le niveau de l'adversaire (plus faible, même
niveau, plus fort).

- Données : celles du classement virtuel et de la progression, aucune requête de plus. Chaque partie
  garde ses manches, vues du joueur (virtuel._manches) : lues dans la liste des parties si l'API les y
  donne, sinon dans le détail déjà lu (feuille de match pour le championnat, détail de la partie pour
  les autres compétitions de la phase) ; les abandons sont repérés. Le journal de la mise à jour dit
  combien de parties ont leurs manches (championnat / autres compétitions).
- Calculs (fiches.py, testés) : parties en 3, 4, 5 manches (vainqueur à 3 manches ; autres formats à
  part), belles (manche décisive), manches et points des manches, manches serrées (2 points d'écart) ;
  remontées (victoire après avoir été mené, dont de deux manches), avances perdues, résultat selon la
  première manche ; niveaux à ±50 points (points officiels de la phase au moment de la partie) ; bilan
  par famille de compétitions ; séries ; 3 meilleures perfs et contres ; équipes jouées par journée.
  Une partie sans manches, arrêtée sur abandon ou dont les manches contredisent le résultat : dans le
  bilan, pas dans les statistiques de manches.
- Page fiches_vaires.html (gabarit_fiches.html), publiée « Fiches des joueurs » après la progression
  (site et /club/) : liste déroulante par équipe puis par nom, boutons ‹ ›, adresse #licence, dernier
  joueur retenu sur l'appareil ; tuiles, courbe (une série, bulle au survol, tableau des valeurs),
  jauges (part de victoires), liste des parties avec le score des manches ; tableau de tout le club
  triable et filtrable par équipe. Lisible sur téléphone, thème sombre.
- Au passage : sur l'accueil du site, les pages hors de la liste d'ordre (progression, individuels) se
  plaçaient en tête ; elles suivent maintenant le classement virtuel.
- Mise à jour n° 60 (données réelles) : 61 fiches ; manches connues pour 315 parties de championnat sur
  315, pour aucune des 78 parties de critérium et de tournois (le journal liste depuis les champs que
  l'API donne pour ces parties).
- Ajout (12/11) : historique du classement. Demande : le meilleur classement du joueur, ou une courbe
  de tous ses anciens classements. Les deux : virtuel.historiques_classement lit la page « historique
  classement » de pingpocket.fr de chaque joueur du club (même page et même règle de cache que pour les
  adversaires : gardée toute la phase, au plus 120 nouvelles pages par lancement, pas pour un joueur à
  500 points sans partie) ; lue par le PC, servie en ligne par les pages que le PC envoie. Fiche : tuile
  « Meilleur classement », carte « Historique de son classement » (points officiels de chaque phase,
  janvier et juillet, repère sur le meilleur, bulle par phase, tableau), colonne et tri « Meilleur »
  dans le tableau du club. Une archive ne montre rien d'après sa date.

## Clubs du 77 : /77/ (15/11/2026)

Demande : une page 77 avec les statistiques des clubs du département pour voir le niveau de Vaires :
les joueurs de chaque club, leur nombre, par sexe et par catégorie (poussins à vétérans), triable et
filtrable, la ligne de Vaires surlignée en jaune dans les classements ; le nombre d'équipes engagées et
leurs divisions (nationale, régionale, D1, D2...) ; comparer jusqu'à 8 clubs ; s'en servir en phase 2
pour voir les favoris d'une poule.

- Données (departement.py, testé) : clubs du comité (rencontres J1 et J2 des divisions D77, numéros
  0877…) ; équipes de chaque club par fftt.rencontres_club (division, niveau court, poule ; une équipe
  féminine peut porter le même nom qu'une masculine : clé nom + féminine) ; poules et leurs équipes ;
  listes pingpocket (catégories, état ; licences de la saison), au plus MAX_LISTES = 60 pages nouvelles
  par lancement sur le PC, 30 jours de cache, en ligne seulement le cache envoyé par le PC. Joueurs
  envoyés à la page : [points, sexe, catégorie précise, loisir, « NOM Prénom »] (voir l'onglet Joueurs
  ci-dessous). Force estimée d'une équipe : moyenne des 4 joueurs de son rang.
- Page departement_77.html (gabarit_77.html), publiée « Clubs du 77 » et à /77/ (PAGES_A_PART, mot de
  passe du club) : onglets Clubs, Classements, Comparer, Poules ; filtres de joueurs communs ; tri par
  colonne, recherche, filtre de division ; classement par mesure avec la place de Vaires ;
  comparaison de 8 clubs (ou ceux d'une poule) ; favoris d'une poule ; fiche de club. Vaires : ligne
  et barre en jaune, les autres en gris.
- Correction (15/11) : Vaires affichait 62 joueurs pour 89 licenciés sur la FFTT et pingpocket : les 27
  licences loisir n'étaient pas comptées par défaut. Par défaut maintenant : toutes les licences, avec
  une colonne « dont loisir » ; bouton « Compétition » pour les retirer (réglage retenu sous un
  nouveau nom pour que tout le monde reparte de ce défaut).
- Correction (15/11) : la comparaison montrait 49 joueurs pour Vaires : « Hommes » et « Adultes »
  étaient restés choisis (réglage retenu d'une visite à l'autre, en haut de la page, hors de vue).
  Maintenant : chaque visite repart de « tout », un bandeau « Comptés : … · Tout compter » rappelle le
  réglage dans chaque vue, et les boutons disent « Femmes et hommes / Femmes seulement / Hommes
  seulement ». La force estimée des équipes masculines compte toujours aussi les joueuses (championnat mixte).
- Mise à jour : option --departement, dans « Tout » (workflow, PC option 5 et option 9) et seule
  (« Clubs du 77 »). Navigation : « 77 » en haut et dans le menu de /indivs/, /tournois/, /cal/ ;
  « Aller à » de /club/.
- Onglet Joueurs (15/11) : demande : les noms et classements de chaque joueur du 77, un classement
  triable et filtrable par catégorie et par sexe (par exemple tous les minimes du 77), aussi précis que
  possible (minimes 1, minimes 2...). Les listes pingpocket donnent nom, sexe, catégorie précise (« M1 »,
  « V45 ») et points mensuels : departement.joueurs_du_club garde la catégorie précise, la page reçoit le nom.
  Points virtuels non repris : une requête FFTT par joueur (des milliers), à envisager seulement pour un
  sous-ensemble si on le demande. Onglet « Joueurs » : licences compétition, place par points (ex aequo
  à la même place), filtres sexe / catégorie (groupe « M* » ou précise « M1 ») / club / nom sans
  accents, tri par colonne, 200 lignes puis « afficher plus », Vaires en jaune avec sa meilleure place ;
  lien depuis la fiche d'un club. Les statistiques par club utilisent la lettre de la catégorie.
  Rien à relancer sur le PC : les pages déjà envoyées contiennent ces informations.
- Points virtuels des jeunes (15/11) : demande : estimer combien de jeunes (catégories sous senior)
  cela concernerait et, si c'est acceptable, les calculer, pour voir les jeunes en pleine progression et
  les clubs qui investissent dans leurs jeunes. Données réelles du 15/11 : 824 jeunes en licence
  compétition dans les 55 clubs (P 63, B 137, M 208, C 212, J 204 ; 1974 avec les licences loisir). Une
  mise à jour « Tout » lisait déjà les parties de 789 à 985 adversaires (1191 pages téléchargées) :
  même ordre de grandeur, donc retenu, étalé. departement.virtuels_des_jeunes : virtuel.forme_joueurs
  (même calcul que les adversaires ; même adresse, donc le cache des adversaires sert), au plus
  MAX_VIRTUELS = 300 jeunes lus par lancement (jamais lus d'abord, puis les réponses les plus anciennes),
  TTL_VIRTUELS = 3 jours, les autres déjà lus gardent leur dernière réponse ; sans partie dans la phase,
  virtuels = points mensuels. Seulement dans la mise à jour en ligne (pingpocket lu dans le cache du PC) :
  le PC n'envoie pas les réponses de l'API, le faire aussi sur le PC doublerait les requêtes. Page :
  [virtuels, gagnés depuis le début de la phase, V, D] en 6e élément d'un jeune (pas de numéro de
  licence) ; onglet Joueurs : catégorie « Jeunes », colonnes Virtuels, +/−, Parties (catégorie de jeunes
  choisie ; sur téléphone sans les points mensuels), rang selon la colonne triée ; fiche du club : jeunes
  les plus en progression ; Classements et Comparer : moyenne des 4 meilleurs jeunes (virtuels), points
  gagnés par tous les jeunes du club. Tests : plafond, ordre de lecture, en ligne seulement.
- Précision demandée (15/11) : « gardée 3 jours » voulait dire qu'un jeune lu il y a moins de 3 jours
  n'est pas redemandé ; rien ne disparaît après. Demandes : afficher la date de récupération de chaque
  joueur ; pourquoi trois mises à jour plutôt qu'une ? Réponse : le plafond de 300 par lancement n'était
  qu'une précaution ; les 789 adversaires sont lus en 3 min 30 dans une mise à jour, donc les 824 jeunes
  le sont en une seule (environ 4 minutes de plus ; MAX_VIRTUELS = 1500, simple borne de sécurité). Date
  de lecture (date de la réponse enregistrée) en 5e valeur du jeune : colonne « Lu le » (téléphone : sous
  le nom), en orange au-delà de 7 jours, dans la fiche du club et dans la note (« lus entre le … et le
  … »). Ordre des pages : les clubs du 77 après les adversaires (un refus de l'API pendant la lecture
  des jeunes ne touche plus la page des adversaires).
- Choix des joueurs à relire et bouton en haut (15/11) : demande : 2 332 joueurs en tout, soit 3 fois
  les jeunes : est-ce acceptable pour la FFTT ? pouvoir lancer tous les joueurs du 77, tous les jeunes,
  ou tous sauf les jeunes ; et le bouton de mise à jour en tout premier sur la page. Réponse : la
  première fois, environ 1 300 à 1 500 requêtes de plus pour tout le département (une partie est déjà
  lue comme adversaires), 6 à 7 minutes, deux fois la charge d'une mise à jour « Tout » ; ensuite,
  seulement ceux lus il y a plus de 3 jours : acceptable, au choix de l'utilisateur. Option
  --virtuels-77 {jeunes, adultes, tous, aucun} (departement.PERIMETRES, défaut : jeunes), entrée
  « joueurs_77 » du workflow (lundi : jeunes), second choix sous « Pages à mettre à jour » de l'accueil
  (seulement pour « Tout » et « Clubs du 77 », non retenu). Hors du choix : la dernière lecture
  enregistrée sert, sans requête (adultes adversaires compris). MAX_VIRTUELS = 2500. Page : colonnes des
  virtuels quand au moins 3 joueurs affichés sur 4 en ont ; sur téléphone, un joueur sans virtuels
  montre ses points mensuels en gris ; note : connus pour x jeunes sur y et z adultes sur w. Accueil :
  « Mettre à jour maintenant » avant « Pages » ; l'explication des deux boutons repliée (« Quel bouton
  choisir ? »).
- Écart signalé (15/11) : un V40 d'un autre club : l'outil 99 parties (59 V, 40 D) et +203,2, la FFTT 98
  parties (58 V, 40 D) et +123,1 (début de saison 1499, virtuels 1622,1). Le barème est celui de la
  FFTT. Pistes : (1) parties « non comptées » (tableaux handicap...) : le drapeau n'est que dans le
  détail d'une partie (une requête par partie), que forme_joueurs ne lit pas (adversaires et joueurs du
  77) ; la liste ne donne que id, date, effectiveDate, contest, joueurs, winner, sportMatch,
  doubleOpposition ; (2) coefficients des compétitions (jamais confrontés à la FFTT hors championnat) ;
  (3) parties en double ; (4) date de prise en compte. Pas d'accès direct à l'API (compte du club) :
  controle_parties.controler mesure tout cela à chaque mise à jour en ligne et l'écrit dans le journal en
  chiffres seulement (filtres acceptés par l'API, doublons, effectiveDate, nombre de parties hors
  championnat, coefficients par famille, part de « non comptées » sur un échantillon d'une partie sur
  40 lue en détail et gardée). Les joueurs de Vaires (classement virtuel) lisent déjà ce détail. Note
  « vérification en cours » sur la page en attendant la correction.
- Résultats du contrôle (mises à jour n° 71 et 72) : 0 partie « non comptée » sur 160, ni doublon, ni
  décalage d'effectiveDate ; pas de filtre « notCounted » dans l'API (seulement order[notCounted]) ;
  6 623 parties hors championnat distinctes ; coefficients donnés par la FFTT : tournois 0,75 / 1 /
  0,5, critérium fédéral 1,5, Top Jeune 0,5, vétérans 1 ; homePoints / awayPoints du détail = points de
  rencontre (2 victoire, 1 défaite, 0 forfait), pas des points de classement ; **2 forfaits sur 160**
  (forfeit, présent seulement dans le détail), comptés jusque-là comme des victoires avec leurs points.
  Correction : departement.virtuels_des_joueurs lit le détail des parties hors championnat (virtuel.
  lire_etats_parties, gardé pour toujours), au plus MAX_DETAILS = 2500 nouveaux par lancement, ceux des
  joueurs choisis, les plus récents d'abord ; les détails déjà lus servent à tous ; calcul par virtuel.
  formes_depuis_parties (forme_joueurs le réutilise). Les coefficients restent ceux de la FFTT, faute de
  barème officiel trouvé : à confirmer en comparant ensuite le joueur signalé.
- Après la lecture des forfaits (mise à jour n° 73, « tous », 2 657 parties vérifiées sur 6 623) : le
  joueur signalé passe à 58 V / 40 D (comme la FFTT) et +186,2 (FFTT +123,1) : reste 63 points. Le
  nombre de parties étant juste, le calcul de chaque partie est en cause. Coefficients de l'API
  conformes à ceux cités par un guide récent (championnat et tournois nationaux A 1, autres nationaux
  0,75, régionaux et départementaux 0,5, critérium 1,5). En revanche, la FFTT calcule chaque partie avec
  « la valeur du joueur à la fin de la période précédant la partie » (situation mensuelle), et non ses
  points officiels de la phase, que l'API donne dans les parties : pour un joueur qui progresse, tous les
  cas jouent contre lui (victoire contre plus fort ou plus faible, défaite...), environ 1 point par
  partie. Correction : mensuel.py, calcul mois par mois (référence = début de phase + gains des mois
  précédents, adversaires hors du 77 : points de la partie), comparé aux points mensuels publiés
  (listes pingpocket : situation de fin du mois -1 ou -2 selon la date de la liste) ; retenu s'il est
  nettement plus juste (erreur moyenne ≤ 80 % de l'autre, 50 joueurs au moins). Journal : erreur des
  deux calculs, variabilité des points lus dans les parties.
- Mise à jour n° 74 : points lus dans les parties constants pour les 1 889 joueurs qui ont joué (ce sont
  bien les points de la phase) ; comparaison aux « points mensuels » des listes sans valeur : pour le
  joueur signalé, la liste donne 1499 (la FFTT 1532,5) ; les deux calculs à 9 points d'erreur moyenne,
  le constant gardé. Captures de la liste des parties de l'application FFTT (99 parties : 75 validées,
  24 non validées ; forfait 11-0 ×3 à 0 point) : au critérium du 11/10 (coef 1,5), +8,25 contre un 15xx,
  +12 contre un 16xx, +19,5 contre un 17xx ne sont possibles qu'avec 1532,5 (situation de fin
  septembre), pas avec 1499. Le calcul mois par mois est donc appliqué sans condition ; la comparaison
  automatique est retirée. Restent hors du calcul : les adversaires d'autres départements (points de
  début de phase, faute de leur situation mensuelle), le classement virtuel de Vaires, la page
  Résultats et la forme des adversaires (encore sur les points de début de phase).
- Mise à jour n° 75 (calcul mensuel, toutes les parties hors championnat vérifiées : 6 538 lues) : le
  joueur signalé passe à +108,4 (FFTT +123,1 ; 1607 contre 1622,1). D'après les captures : octobre
  (critérium +42,75, Troyes +46,5, Vittel -2, championnat -3) = +84,3 = « Premium » de la FFTT ; fin
  août et septembre = +33,5 = « Mensuels » : la FFTT met les tournois des 29-30 août dans la même
  période que septembre (périodes : 1 = septembre ... 4 = décembre, 10 = juin), et calcule septembre
  avec 1499. L'outil faisait une période d'août (septembre à 1499 + gains d'août, environ 1534 : environ
  -1 point sur chacune des 14 parties de septembre). Correction : mensuel.periode, juillet et août
  comptés avec septembre.
- Mise à jour n° 76 : +107,6 seulement (au lieu de +108,4) : l'explication d'août n'était pas la
  bonne (ou pas la seule). Pour mesurer au lieu de supposer : gains de chaque joueur par période
  (6e valeur de ses points virtuels, périodes dans virtuels.periodes), à comparer aux +33,5 (fin août
  et septembre), +84,3 (octobre) et +5,3 (novembre) de la FFTT ; affichés au survol de « +/− »
  (« sept. +12 · oct. +8 »).
- Mise à jour n° 77 : outil +33,5 / +80,8 / -6,6 ; FFTT +33,5 / +84,3 / +5,3. Fin août + septembre
  exacts : parties, forfaits, barème, coefficients et périodes justes. Octobre (-3,5) et novembre
  (-11,9, parties non validées) : adversaires d'autres départements (Troyes, Vittel, Compiègne...)
  comptés avec leurs points de début de phase, la FFTT avec leur valeur du mois (jeunes en progression).
  Non corrigé (des milliers de listes de plus).
- Calcul mois par mois sur les pages de Vaires (demande du 15/11) : la page des clubs du 77 enregistre
  les valeurs de début de période de ses joueurs (mensuel.enregistrer, references_77.json dans le
  cache) ; mensuel.References et mensuel.recalculer (valeur du joueur et de l'adversaire si connues,
  sinon début de phase + gains des périodes précédentes / points de la partie) servent au classement
  virtuel (et donc aux fiches, à la progression et à leurs images), à la forme des adversaires et des
  individuels (formes_depuis_parties) et aux résultats (points de chaque partie ; le cumul part des
  points officiels de la phase : champ « officiels »). Indicateur « mensuel » dans les données, notes
  des pages adaptées. Les pages de Vaires passent avant celle des clubs du 77 : elles utilisent les
  valeurs du lancement précédent (deux mises à jour la première fois).
- Adversaires d'autres départements et compte Premium (15/11) : contrôle de la mise à jour n° 80 :
  2 349 adversaires hors du 77, 5 695 parties, 405 joueurs du 77 concernés (sur 1 889 qui ont joué).
  L'API ne donne pas de points mensuels ni virtuels au compte utilisé (Premium) : un joueur dans une
  partie = {grade, id, identifier, person, points de la phase} ; fiche de licence refusée ; rubriques
  de l'API vides. Pas d'exploration de l'application FFTT (accès non documenté), et les données Premium
  sont celles d'un abonnement personnel. Décision de l'utilisateur : lire les 2 349 adversaires, une
  fois par semaine (pas de tournoi en semaine hors vacances) ; mentions « estimation » et repère « * ».
  Réalisation : departement.debut_de_semaine (lundi 0 h ; liste lue avant : relue) pour tous les
  joueurs, MAX_EXTERIEURS = 3000, adversaires extérieurs des joueurs choisis, dans le calcul mensuel
  (leurs valeurs aussi dans references_77.json, avec la liste des joueurs du 77 : clé « _77 ») ;
  nombre de parties contre d'autres départements (7e valeur d'un joueur, « exterieurs » au classement
  virtuel) ; choix par défaut « tous ». Pages : « estimation » / « estim. » (77, classement virtuel,
  fiches, progression, résultats, images), repère « * » avec info-bulle.
- Nouveaux adversaires et fiabilité (15/11) : « dans un mois on aura peut-être 2 600 joueurs hors
  département, l'outil ira interroger leur fiche ? » Oui : la liste des adversaires extérieurs est
  refaite à chaque lecture des listes du 77 (chaque lundi) ; un nouveau, jamais lu, passe en premier ;
  MAX_EXTERIEURS borne une mise à jour, pas le total. « Différencier par une couleur une estimation
  proche du résultat officiel ou très loin (1 adversaire hors 77 : très proche ; 80 : plus éloignée). »
  Réalisation : mensuel.incertitudes / valeur_estimee / niveau ; parties du premier mois de la phase
  jamais estimées (points du début de phase de tous) ; valeur d'un joueur lu estimée après le premier
  mois où il a joué un joueur non lu ; 8e valeur d'un joueur du 77 (parties contre un adversaire à
  valeur estimée), « estimees » au classement virtuel (fichier des valeurs : clés _premiere et _estime) ;
  pastille verte (1 à 5), orange (6 à 20), rouge (plus de 20), seuils à revoir d'après des
  comparaisons avec la FFTT ; journal : nombre de joueurs de chaque couleur.
- Statistiques (15/11) : vérifié en ligne, toutes les pages de la copie Cloudflare ont GoatCounter et
  Umami (accueil, /club/, /gg/ et ses archives, /77/, /indivs/, /tournois/, /cal/, /lundi/). Demande :
  compter aussi ce qu'on fait dans les pages (« plus il y a d'informations, plus c'est intéressant »).
  Réalisation : compterAction dans gabarit_77, gabarit_cal, gabarit_indivs, gabarit_tournois →
  window.compteur(« espace/action/détail », titre, événement) ; netlify.ACTIONS_PAGES pour Umami.
  Onglet compté à son changement (pas à chaque filtre), jamais un nom de joueur ni une recherche.
- Pastille grise (15/11) : 405 joueurs ont joué hors du 77, 187 ont une pastille ; les 218 autres
  (adversaires extérieurs tous à valeur calculée) ont maintenant une pastille grise (« presque sûre »),
  journal : fiabilite_gris. France entière (125 000 licenciés) : écartée avec l'utilisateur
  (extraction de toute la base avec un compte personnel ; accès officiel peu probable).
- Classements officiels publics et arrondi (15-16/11) : pages de la FFTT (www2.fftt.com,
  classement national, régional, départemental) derrière un captcha, et interdites en cadre ;
  tennis2table.com interdit les agents de Claude (robots.txt) : rien n'est lu automatiquement.
  Vérification sur captures de l'utilisateur : gains de septembre identiques pour 21 joueurs (minimes
  garçons du 77) ; deux joueurs de Vaires identiques sur trois mois (−1,0 / +14,0 / +7,5 et
  0 / +4,5 / 0). Règle d'arrondi trouvée (entier le plus proche, 0,5 vers le haut, après dérive en fin
  de phase) : virtuels affichés à une décimale ; liens vers les classements officiels (nouvel onglet).
- /lundi/ (17/11) : nouvelle version de la page (au 16/11), puis, à la demande de l'utilisateur (notes
  personnelles sur des joueurs), mot de passe à part : secret MOT_DE_PASSE_LUNDI (ressources.json :
  « acces »), sans lui pas de publication. Page déposée scellée (X25519 + AES-GCM) avec la clé publique
  tirée du mot de passe, publiée à …/lundi/cle-publique.txt : dépôt d'une nouvelle version sans le mot
  de passe, le mot de passe du club n'ouvre plus rien. Clé retenue sous cvtt-vaires-cle-club-lundi
  (repère de l'application Android inchangé). Consigne de la page de mot de passe adaptée.

## Calendrier de la saison : /cal/ (13/11/2026)

Demande : une page /cal/ sur le même principe que /club/ (et /tournois/), qui permet d'aller dans toutes
les pages sauf /lundi/, et qui affiche un calendrier de type Google Agenda avec toutes les journées du
championnat de France par équipes 77, du championnat de Paris, du championnat des jeunes 77 et les
dates des individuels (critérium) ; sources : https://www.cdtt77.fr/sportive et le PDF du calendrier.

- Données (calendrier.py) : le PDF 2026-2027 du CD77 (version du 04/09/2025 V3), recopié : 14 journées
  du championnat par équipes (vendredi), 14 du championnat féminin 77/94 (samedi), 7 du championnat de
  Paris et 7 + « T » du championnat des jeunes (les mêmes vendredis), 4 tours du critérium (jeunes
  samedi, seniors dimanche, D4 dimanche suivant), 27 autres épreuves et 8 dates limites
  d'inscription. Test : chaque date tombe le jour de la semaine du PDF. Les formations d'arbitrage
  (dates « ? ») ne sont pas reprises. L'agenda Google partagé du comité n'est pas lu (robots.txt de
  calendar.google.com : tout interdit) : lien pour s'y abonner.
- Page fixe gabarit_cal.html (netlify.PAGES_FIXES, comme /tournois/, données intégrées à la
  publication) : grille du mois (lundi en premier), pastilles nommées sur ordinateur, points sur
  téléphone, liste des dates du mois, prochaines dates, boutons de catégories (légende et filtre,
  retenus sur l'appareil ; autres épreuves et dates limites décochées au départ), adresse #2026-11.
  Couleurs : trois teintes validées entre elles (bleu, orange, vert) plus une neutre et des variantes
  de remplissage ; chaque pastille porte son nom.
- Navigation : en-têtes de /indivs/, /tournois/ et /cal/ avec les autres espaces (sur une deuxième
  ligne sur téléphone), menus « Autres espaces », « Aller à » de /club/. Jamais /lundi/.

## Meilleur classement sur l'image des adversaires (12/11/2026)

Demande : le meilleur classement et son année sur l'image du prochain adversaire (la page l'avait,
pas l'image), idéalement en points exacts (1452 plutôt que 14), en restant lisible.

- Colonne « Meilleur » après « Pts » (images._cel_meilleur) : « 1 452 (2006) », en orange et en gras
  quand il dépasse les points actuels d'au moins 200 points (même règle que la page). Retirée si aucun
  joueur n'a d'historique lu ; note en pied d'image.
- Place : si l'image (1080 points) n'a pas la place de l'année à côté des points, l'année passe dessous
  (colonne plus étroite). Au passage : une fiche aux colonnes trop larges (positions « Placé »
  nombreuses) sortait de l'image ; elle s'élargit maintenant au lieu d'être coupée, et la colonne des
  remarques ne grandit plus quand elle doit rétrécir.
- Remarques coupées par « … » (« a joué en 3 … », « nouvel ins… ») : sur deux lignes maintenant.
  Renfort : « a joué en 3 » et dessous « déjà 1× en 9 » (fois où il a déjà joué dans l'équipe que
  Vaires rencontre) ; nouvel inscrit : « nouvel inscrit » en vert (« nouveau » si la colonne est
  étroite), ou dessous s'il y a déjà une remarque. Expliqué en pied d'image.

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
- Championnat de Paris (18/11) : « une page /paris/ avec l'identique de /club/ pour le championnat de
  France, et la navigation d'une page à l'autre ». Documents de la ligue (PDF des poules HO, PH, D2) :
  Vaires 1 Honneur poule 1, Vaires 2 Promotion d'Honneur poule 2, Vaires 3 Division 2 poule 3 ; 7
  journées (27/11/2026 → 04/06/2027), grille commune. Réalisation : paris.py (données recopiées, tests
  de la grille), gabarit_paris.html (prochaine journée, chaque équipe : calendrier, poule, rencontres ;
  toutes les dates), publiée comme /cal/ (PAGES_FIXES, mot de passe du club), liens « Paris » dans
  /club/, /cal/, /indivs/, /tournois/, /77/. Les pages de /club/ (adversaires, compositions, brûlages,
  résultats, classements) viennent de l'API de la FFTT, filtrée sur le championnat de France :
  paris.diagnostic_api écrit dans le journal si l'API a les rencontres de Paris (étape suivante selon
  le résultat).
- Contrôle (mise à jour n° 89, 18/11) : l'API n'a pour Vaires que le championnat de France (42 + 7
  rencontres), pas le championnat de Paris. Demande : « au moins l'effectif des clubs, le meilleur
  classement, les victoires, défaites et points gagnés ». Réalisation : adversaires.recuperer_paris
  (clubs des poules de paris.py ; équipes du championnat de France par l'API, pingpocket, forme),
  paris.donnees(adversaires) (sans licence), vue par club dans gabarit_paris.html ; /paris/ devient une
  page de la mise à jour (paris_vaires.html → paris.html, PAGES_A_PART) ; PC : options 1 et 8 pour les
  effectifs et meilleurs classements des 11 clubs hors du 77.
- Changement (18/11) : « la liste des clubs est moins lisible que le travail fait pour le championnat de
  France : refais cela pour les 3 équipes, qui ils vont rencontrer et quand, avec les adresses des clubs ;
  sur Vaires 1 un classement même s'il est vide ; cliquer sur un adversaire pour la liste de ses joueurs
  (classement, meilleur classement, matchs gagnés/perdus, points gagnés/perdus) ». Réalisation :
  paris.donnees au format de adversaires.recuperer (rencontres domicile/extérieur, classement des 8
  équipes, salles de pingpocket, joueurs avec repères au lieu des licences), gabarit_paris.html calqué
  sur gabarit.html (récapitulatif, onglets, fiche du club), sans brûlage ni vérifications.
- Championnat des jeunes (19/11) : « crée une page /jeunes/ comme France et Paris : calendrier des 2
  équipes (−15 ans, −13 ans), liste des adversaires, effectifs des clubs adverses avec matchs,
  victoires, défaites ; une catégorie plus jeune peut jouer (un benjamin en −15 et en −13) ; garder les
  licences loisir qui ont l'âge ». Réalisation : jeunes.py (poules des captures de l'application FFTT,
  exempt en −13, dates du calendrier du comité, catégories P/B/M, numéros des clubs retrouvés par leur
  nom : trouver_clubs), adversaires.clubs_des_poules (commun avec Paris ; garder : jeunes et loisirs ;
  forme de tous les jeunes), gabarit_championnat.html (ex gabarit_paris.html, paramétré par D.espace,
  D.titre, e.categories), PAGES_A_PART jeunes.html, liens « Jeunes » partout (en-têtes sur deux lignes
  sur téléphone). Contrôle de l'API élargi à toute compétition hors championnat de France.
- Correction (19/11) : « mon fils, minime 1, pourra jouer en Vaires 1 ou Vaires 2 » : moins de 13 ans =
  minimes (11-12 ans) et plus jeunes, moins de 15 ans = cadets (13-14 ans) aussi (jeunes.AGES).
- Classement des poules (21/11) : « le classement doit se faire au goal-average particulier ; vérifie dans le
  règlement du comité 77 (cdtt77.fr/documents) ». cdtt77.fr interdit toute lecture automatique (robots.txt :
  Disallow: /) : non lu. Règlements sportifs fédéraux 2026-2027 (fftt.com/reglements, lecture autorisée),
  article I.202 : I.202.1 (score acquis) goal-average particulier ; I.202.2 (toutes les parties jouées)
  quotient général des parties puis goal-average particulier ; procédure recommencée pour les équipes encore
  à égalité ; forfaits comptés à 0. Réalisation : departage.py, adversaires.classement_poule (règle lue sur
  les scores, critère de chaque équipe), notes et ≡ sur la page adversaires et la page des classements.
- Règlement du comité 77 envoyé (21/11) : article 5.2 : quotient général des parties puis goal-average
  particulier (a à e), forfait 28 à 0 et 3 manches à 0 par partie, exempte d'une poule incomplète : 3 points ;
  article 6.1 : toutes les parties sont jouées. Réalisation : departage.CD77 (poules PR, D1, D2..., pas le
  féminin 77/94), points de l'exempte dans adversaires.classement_poule, notes des pages, journal.
- Image du programme (22/11) : « une image au format téléphone, lisible, qui récapitule les rencontres des
  équipes de Vaires : les 2 journées restantes du championnat de France (6 équipes + l'équipe femmes), les
  matchs des 3 équipes de Paris et des 2 équipes jeunes ; un code couleur domicile / extérieur ; pas
  d'adresse ». Réalisation : programme.py (rencontres : 2 prochaines par équipe de France, Paris et jeunes sur
  la même période ou leur prochaine ; dessin 1080 de large, une carte par rencontre, vert / orange et
  pastille DOM / EXT), faite par l'étape adversaires, groupe d'images « programme » à la une de /club/.
- Programme (22/11) : pictogramme de chaque compétition (carte de France, tour Eiffel, femme en rose, enfant) ;
  plus de « date à confirmer » ni de texte de pied ; « une autre image avec tous les matchs jusqu'à la fin de
  saison » : programme_saison.png (une ligne par rencontre ; phase 2 du championnat de France d'après le
  calendrier du comité tant que ses poules ne sont pas faites).
- Infographie de Paris (22/11) : « une belle infographie juste pour le championnat de Paris, au format
  téléphone, qui ne fasse pas Excel ». Réalisation : infographie_paris.py (paris_infographie.png), groupe
  « paris » à la une de /club/.
- Disponibilités du championnat de Paris (22/11) : « un tableau de disponibilité de mon club, tous les joueurs
  sans les loisirs, juste le nom, classés par le dernier classement virtuel, vert si disponible, rouge si non ;
  au format téléphone : 1re colonne les disponibles, 2e les pas disponibles et en dessous les sans réponse ; à
  faire pour chaque journée ». Réalisation : onglet « Disponibilités » de /paris/ (une liste par journée,
  gardée dans le navigateur, collage des réponses avec reconnaissance des noms, image dessinée dans la page),
  joueurs : paris.memoriser_joueurs (cache, depuis le classement virtuel).

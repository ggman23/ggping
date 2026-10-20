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

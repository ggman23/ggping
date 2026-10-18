# Lancer les mises à jour depuis un téléphone

Les pages sont générées sur les serveurs de GitHub (GitHub Actions) et publiées sur un site
(GitHub Pages), consultable et actualisable depuis un téléphone :

**https://ggman23.github.io/ggping/**

- La page d'accueil liste les pages (adversaires, résultats, Excel, effectif, classement virtuel)
  avec leur date et le bilan des vérifications, et propose un bouton **« Lancer la mise à jour »**.
- Les pages sont **chiffrées** : il faut le mot de passe du club pour les lire (cochez « Se
  souvenir sur cet appareil » pour ne le taper qu'une fois). Le site est public, mais sans le mot
  de passe on n'y voit aucun nom de joueur ; il n'est pas référencé par les moteurs de recherche.
- Mises à jour automatiques : samedi, dimanche, lundi et mardi vers 8 h (lendemains de journée).
- Gratuit (dépôt public : GitHub Actions et GitHub Pages sans frais).

## Mise en place (une seule fois, faisable depuis le téléphone)

Sur github.com, connecté avec le compte propriétaire du dépôt `ggman23/ggping` (dans le
navigateur du téléphone, choisir « Version pour ordinateur » si un menu n'apparaît pas) :

1. **Activer le site** : dépôt → *Settings* → *Pages* → *Build and deployment* → *Source* :
   **GitHub Actions**.
2. **Choisir le mot de passe du club** : dépôt → *Settings* → *Secrets and variables* →
   *Actions* → *New repository secret* :
   - *Name* : `MOT_DE_PASSE_SITE`
   - *Secret* : le mot de passe (au moins 12 caractères, par exemple trois mots et un chiffre).

   C'est ce mot de passe que vous donnerez aux capitaines.
3. **Premier lancement** : dépôt → *Actions* → *Mise à jour du site* → *Run workflow* → *Run
   workflow*. Environ 5 minutes. Le site est ensuite à l'adresse ci-dessus : l'ajouter à l'écran
   d'accueil du téléphone (menu du navigateur → « Ajouter à l'écran d'accueil »).

## Le bouton « Lancer la mise à jour » du site

Il demande à GitHub de lancer la mise à jour, puis affiche son avancement (« en cours… »,
« terminé »). Il lui faut un **jeton** GitHub, créé une fois et enregistré uniquement sur le
téléphone (le site explique la marche à suivre dans « Réglage du bouton ») :

1. https://github.com/settings/personal-access-tokens/new (*Fine-grained token*) ;
2. *Token name* : « Vaires téléphone », *Expiration* : 1 an ;
3. *Repository access* : **Only select repositories** → `ggman23/ggping` ;
4. *Permissions* → *Repository permissions* → **Actions : Read and write** (rien d'autre) ;
5. *Generate token*, copier le jeton (`github_pat_…`) et le coller dans le site.

Ce jeton permet seulement de lancer et de suivre les mises à jour de ce dépôt. Il ne quitte pas
le téléphone (stockage du navigateur). À renouveler à son expiration ; « Effacer » le retire.

Sans jeton, on peut toujours lancer depuis l'appli ou le site GitHub : *Actions* → *Mise à jour
du site* → *Run workflow* (choix des pages : tout, résultats, effectif, virtuel, adversaires).

## Ce qui diffère du lancement sur le PC

- Les données viennent de l'API publique de la FFTT, comme sur le PC.
- **pingpocket.fr** refuse en pratique les serveurs de GitHub : pas d'effectifs complets des
  adversaires ni de meilleurs classements en ligne (les pages le signalent).
- **Le dossier `import`** (listes des licenciés enregistrées depuis le navigateur) reste sur le
  PC : il n'est jamais envoyé sur GitHub (données personnelles). En ligne, les pages Effectif et
  Classement virtuel ne montrent donc que les joueurs alignés en championnat. Pour la version
  complète, utiliser `lancer.bat` sur le PC.
- Une page non choisie lors d'une mise à jour reste celle de la mise à jour précédente (sa date
  est affichée sur l'accueil).

## Sécurité

- Chaque page est chiffrée en AES-256-GCM avec une clé tirée du mot de passe (PBKDF2-SHA256,
  310 000 itérations) ; le déchiffrement se fait dans le navigateur. Le mot de passe n'est stocké
  qu'en secret GitHub (illisible, même par le propriétaire) et, si on le demande, sous forme de
  clé dans le navigateur de l'appareil.
- Changer le mot de passe : modifier le secret `MOT_DE_PASSE_SITE`, puis relancer une mise à jour
  « Tout ». Chacun devra saisir le nouveau mot de passe.
- Le bilan des vérifications sur l'accueil ne contient que des nombres et des noms d'équipes.

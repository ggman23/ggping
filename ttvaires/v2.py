"""Version 2 du site, à l'essai : /v2/ sur la copie Cloudflare (et Netlify), à côté du site actuel.

Demandée le 26/11/2026 : « une /v2/, copie du site actuel avec toutes les modifications proposées, pour
tester sans toucher au site actuel ». Rien du site actuel n'est modifié : la v2 est fabriquée à la fin
de la copie (netlify.construire), à partir des pages déjà publiées. Leurs données (le JSON intégré à
chaque page) sont reprises telles quelles et rechiffrées avec la clé du club. Une mise à jour
« Publication seule » suffit donc à la refaire.

Organisation (par question plutôt que par source de données) :
- /v2/            accueil : prochaines rencontres, derniers résultats, « Mon espace », images à partager ;
- /v2/equipes/    toutes les équipes (France hommes et femmes, Paris, jeunes) : poule, calendrier, joueurs ;
- /v2/rencontre/  fiche d'une rencontre : salle et itinéraire, compo probable adverse, pronostic, feuille ;
- /v2/joueurs/    joueurs de Vaires : recherche, fiche, objectif de points ;
- /v2/agenda/     tout le calendrier (Vaires et comité), en liste ou en grille du mois (#calendrier), export vers
                  l'agenda du téléphone ; /v2/indivs/ (poules, résultats du tour, classement de la poule) et
                  /v2/tournois/ (PingRadar) dans le même onglet ;
- /v2/77/         clubs du 77 et tous leurs joueurs (onglets Équipes et Joueurs) ;
- /v2/club/       documents, images, archives, rubriques, autres espaces, réglages ; les pages détaillées
                  du site actuel s'y ouvrent dans le cadre de la v2.

Fichiers : les pages, le style et le code communs sont dans ttvaires/v2/ (copiés tels quels, sans
aucune donnée) ; les données dans v2/donnees/<nom>.json.chiffre (clé du club, même mot de passe et même
clé mémorisée que /club/). Application installable : manifest, service worker (dernière version gardée
pour la salle sans réseau) et icônes dessinées ici.
"""

import base64
import hashlib
import json
import re
import shutil
from pathlib import Path

from . import calendrier, publier

STATIQUE = Path(__file__).with_name("v2")
# Données de la v2 -> page publiée du site (chiffrée avec la clé du site) qui les contient
SOURCES = {"france": "adversaires.html", "effectif": "effectif.html", "virtuel": "classement_virtuel.html",
           "fiches": "fiches.html", "progression": "progression.html", "resultats": "resultats.html",
           "rencontres": "rencontres.html", "classements": "classements.html", "paris": "paris.html",
           "jeunes": "jeunes.html", "indivs": "indivs.html", "departement": "77.html"}
# Données des autres championnats dans les pages à sélecteur (<script id="donnees-paris">...) : nom -> (page, championnat)
SOURCES_CHAMP = {"rencontres_paris": ("rencontres.html", "paris"), "rencontres_jeunes": ("rencontres.html", "jeunes"),
                 "resultats_paris": ("resultats.html", "paris")}
CHIFFRE = re.compile(r'<script id="chiffre" type="text/plain">([^<]+)</script>')
DONNEES_SCRIPT = re.compile(r'<script id="donnees" type="application/json">(.*?)</script>', re.S)
VERIF = b"cvtt-vaires-club"  # le même témoin que /club/ (netlify.VERIF_CLUB)
NUIT, ROUGE = (15, 39, 64), (198, 40, 40)


def donnees_de_la_page(html, championnat=None):
    """Le JSON intégré à une page du site : <script id="donnees"> ou « const D = {...}; » ; `championnat` (paris,
    jeunes) : celui du championnat dans une page à sélecteur (<script id="donnees-paris">), None s'il n'y est pas."""
    if championnat:
        m = re.search(rf'<script id="donnees-{championnat}" type="application/json">(.*?)</script>', html, re.S)
        return json.loads(m[1]) if m else None
    m = DONNEES_SCRIPT.search(html)
    if m:
        return json.loads(m[1])
    i = html.find("const D = ")
    if i >= 0:
        return json.JSONDecoder().raw_decode(html[i + len("const D = "):])[0]
    return None


def lire_page(site, nom, cle_site, championnat=None):
    """Données d'une page publiée du site (None si elle n'existe pas ou ne s'ouvre pas) ; `championnat` : celles
    d'un autre championnat dans une page à sélecteur."""
    fichier = Path(site) / nom
    if not fichier.exists():
        return None
    m = CHIFFRE.search(fichier.read_text(encoding="utf-8"))
    if not m:
        return None
    try:
        return donnees_de_la_page(publier.dechiffrer(base64.b64decode(m[1]), cle_site).decode("utf-8"), championnat)
    except Exception:  # autre clé, page abîmée : la v2 fait sans
        return None


def _chiffre(objet, cle_club):
    from .netlify import chiffrer_stable  # (netlify importe ce module)

    brut = objet if isinstance(objet, bytes) else json.dumps(objet, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return chiffrer_stable(brut, cle_club)


def icone(taille):
    """Icône de l'application : raquette rouge et balle sur fond bleu nuit, « CVTT » en dessous."""
    from PIL import Image, ImageDraw

    from .images import police

    s = taille / 512
    img = Image.new("RGB", (taille, taille), NUIT)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([int(206 * s), int(250 * s), int(246 * s), int(372 * s)], radius=int(16 * s), fill=(214, 160, 90))
    d.ellipse([int(120 * s), int(70 * s), int(332 * s), int(282 * s)], fill=ROUGE)
    d.ellipse([int(330 * s), int(96 * s), int(392 * s), int(158 * s)], fill=(255, 255, 255))
    texte, p = "CVTT", police(max(8, 74 * s / 2), True)  # police() travaille à l'échelle 2 des images
    largeur = d.textlength(texte, font=p)
    d.text(((taille - largeur) / 2, 392 * s), texte, font=p, fill=(255, 255, 255))
    from io import BytesIO
    sortie = BytesIO()
    img.save(sortie, "PNG", optimize=True)
    return sortie.getvalue()


def _version(fichiers, maj):
    h = hashlib.sha256(maj.encode("utf-8"))
    for f in fichiers:
        h.update(f.name.encode("utf-8") + f.read_bytes())
    return h.hexdigest()[:12]


def construire(site, dossier, cle_site, cle_club, club_index=None):
    """Écrit la v2 dans `dossier` (ex. site-netlify/v2). `club_index` : la page /club/ déjà construite
    (liste des documents, images, archives et rubriques, sans donnée de joueur). Renvoie les données
    publiées."""
    site, dossier = Path(site), Path(dossier)
    if dossier.exists():
        shutil.rmtree(dossier)
    statiques = sorted(f for f in STATIQUE.rglob("*") if f.is_file())
    etat = json.loads((site / "etat.json").read_text(encoding="utf-8")) if (site / "etat.json").exists() else {}
    maj = (etat.get("derniere_maj") or {}).get("fin") or ""
    version = _version(statiques, maj)
    for f in statiques:
        cible = dossier / f.relative_to(STATIQUE)
        cible.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix in (".js", ".html", ".webmanifest"):
            texte = f.read_text(encoding="utf-8")
            texte = (texte.replace("__SEL__", publier.SEL).replace("__ITERATIONS__", str(publier.ITERATIONS))
                     .replace("__MAJ__", maj).replace("__VERSION__", version))
            cible.write_text(texte, encoding="utf-8")
        else:
            shutil.copyfile(f, cible)
    (dossier / "icones").mkdir(parents=True, exist_ok=True)
    for taille in (180, 192, 512):
        (dossier / "icones" / f"icone-{taille}.png").write_bytes(icone(taille))
    sortie = dossier / "donnees"
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "verif.chiffre").write_bytes(_chiffre(VERIF, cle_club))
    publiees = []
    for nom, page in SOURCES.items():
        donnees = lire_page(site, page, cle_site)
        if donnees is not None:
            (sortie / f"{nom}.json.chiffre").write_bytes(_chiffre(donnees, cle_club))
            publiees.append(nom)
    for nom, (page, championnat) in SOURCES_CHAMP.items():  # Paris, jeunes (28/11)
        donnees = lire_page(site, page, cle_site, championnat)
        if donnees is not None:
            (sortie / f"{nom}.json.chiffre").write_bytes(_chiffre(donnees, cle_club))
            publiees.append(nom)
    (sortie / "agenda.json.chiffre").write_bytes(_chiffre(calendrier.donnees(), cle_club))
    publiees.append("agenda")
    if club_index is not None and Path(club_index).exists():
        club = donnees_de_la_page(Path(club_index).read_text(encoding="utf-8"))
        if club:
            (sortie / "club.json.chiffre").write_bytes(_chiffre(club, cle_club))
            publiees.append("club")
    index = {"maj": maj, "version": version, "donnees": publiees,
             "pages": {nom: {"titre": p.get("titre"), "date": p.get("date")} for nom, p in etat.get("pages", {}).items()}}
    (sortie / "index.json.chiffre").write_bytes(_chiffre(index, cle_club))
    return publiees

"""Copie de secours du site sur Netlify (https://ggping.netlify.app/).

- https://ggping.netlify.app/ : la page des adversaires (vaires.html), lisible par tout le club
  sans mot de passe (non référencée par les moteurs de recherche : robots.txt et en-tête noindex) ;
- https://ggping.netlify.app/club/ : l'espace club, avec son propre mot de passe (secret
  MOT_DE_PASSE_CLUB) : un menu des pages, de l'Excel et des images, que l'on peut regarder dans
  la page puis télécharger (sans bouton de mise à jour). Sans ce secret, /club/ n'est pas publié ;
- https://ggping.netlify.app/gg/ : la copie du site GitHub (page d'accueil, toutes les pages,
  l'Excel et les images), re-chiffrée avec son propre mot de passe (secret MOT_DE_PASSE_GG, à donner
  aux capitaines) : le mot de passe du site GitHub reste secret. Sans MOT_DE_PASSE_GG, /gg/ n'est
  pas publié.

Lancé par le workflow GitHub après la publication du site (dossier site/ prêt), donc après chaque
mise à jour, qu'elle vienne du PC (option 7) ou du téléphone :
  python -m ttvaires.netlify
Variables d'environnement : NETLIFY_AUTH_TOKEN (jeton Netlify ; sans lui, rien n'est fait),
NETLIFY_SITE (par défaut ggping.netlify.app), MOT_DE_PASSE_SITE (pour lire le site GitHub),
MOT_DE_PASSE_GG (celui de /gg/), MOT_DE_PASSE_CLUB (celui de /club/).
"""

import argparse
import base64
import io
import json
import os
import re
import shutil
import sys
import time
import zipfile
from pathlib import Path

import requests

from . import publier

RACINE = Path(__file__).resolve().parent.parent
API = "https://api.netlify.com/api/v1"
SITE_PAR_DEFAUT = "ggping.netlify.app"
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
CHIFFRE = re.compile(r'<script id="chiffre" type="text/plain">([^<]+)</script>')
GABARIT_CLUB = Path(__file__).with_name("gabarit_club.html")
VERIF_CLUB = b"cvtt-vaires-club"  # fichier témoin : sert à vérifier le mot de passe de /club/
ORDRE_CLUB = ["vaires.html", "resultats_vaires.html", "resultats_vaires.xlsx", "rencontres_vaires.html",
              "effectif_vaires.html", "classement_virtuel.html"]


class ErreurNetlify(Exception):
    pass


def page_publique(site, mot_de_passe):
    """La page des adversaires du site GitHub, déchiffrée : l'accueil public de Netlify."""
    fichier = site / "adversaires.html"
    if not fichier.exists():
        return ("<!doctype html><meta charset=\"utf-8\"><title>CVTT Vaires</title>"
                "<p>La page des adversaires n'a pas encore été générée.</p>")
    chiffre = CHIFFRE.search(fichier.read_text(encoding="utf-8"))
    html = publier.dechiffrer(base64.b64decode(chiffre[1]), publier.cle(mot_de_passe)).decode("utf-8")
    if 'name="robots"' not in html:
        html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX, 1)
    return html


def copie_rechiffree(site, gg, cle_site, cle_gg):
    """Copie du site GitHub dont chaque page, l'Excel et chaque image sont re-chiffrés avec la clé de /gg/.
    L'accueil, etat.json, robots.txt... ne contiennent aucune donnée de joueur : copiés tels quels."""
    for f in sorted(site.rglob("*")):
        if not f.is_file():
            continue
        cible = gg / f.relative_to(site)
        cible.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix == ".chiffre":
            cible.write_bytes(publier.chiffrer(publier.dechiffrer(f.read_bytes(), cle_site), cle_gg))
            continue
        texte = f.read_text(encoding="utf-8") if f.suffix == ".html" else None
        m = CHIFFRE.search(texte) if texte else None
        if m:  # page verrouillée : seul le contenu chiffré change
            donnees = publier.dechiffrer(base64.b64decode(m[1]), cle_site)
            nouveau = base64.b64encode(publier.chiffrer(donnees, cle_gg)).decode("ascii")
            cible.write_text(texte[:m.start(1)] + nouveau + texte[m.end(1):], encoding="utf-8")
        else:
            shutil.copy2(f, cible)


def _clair(fichier, cle):
    """Contenu d'un fichier du site GitHub : page verrouillée (HTML) ou fichier .chiffre (Excel, image)."""
    if fichier.suffix == ".chiffre":
        return publier.dechiffrer(fichier.read_bytes(), cle)
    return publier.dechiffrer(base64.b64decode(CHIFFRE.search(fichier.read_text(encoding="utf-8"))[1]), cle)


def espace_club(site, club, cle_site, cle_club):
    """/club/ : chaque page, l'Excel et chaque image, re-chiffrés avec la clé du club sous leur nom
    d'origine (fichiers/vaires.html.chiffre...), et la page de navigation (gabarit_club.html) qui
    les déchiffre dans le navigateur. La liste des documents (titres, dates) ne contient aucun nom de joueur."""
    fichier_etat = site / "etat.json"
    etat = json.loads(fichier_etat.read_text(encoding="utf-8")) if fichier_etat.exists() else {}
    fichiers = club / "fichiers"
    fichiers.mkdir(parents=True)
    documents = []
    for publie, info in etat.get("pages", {}).items():
        if not (site / publie).exists():
            continue
        nom = info.get("nom_telecharge") or publie.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(publier.chiffrer(_clair(site / publie, cle_site), cle_club))
        excel = nom.endswith(".xlsx")
        documents.append({"fichier": nom, "type": "excel" if excel else "page", "titre": info.get("titre", nom),
                          "description": info.get("description", ""), "date": info.get("date"),
                          "verification": "" if excel else info.get("verification", ""),
                          "ordre": ORDRE_CLUB.index(nom) if nom in ORDRE_CLUB else len(ORDRE_CLUB)})
    for publie, info in etat.get("images", {}).items():
        if not (site / publie).exists():
            continue
        nom = info.get("nom_telecharge") or Path(publie).name.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(publier.chiffrer(_clair(site / publie, cle_site), cle_club))
        documents.append({"fichier": nom, "type": "image", "titre": info.get("titre", nom), "groupe": info.get("groupe"),
                          "ordre": info.get("ordre", 0), "date": info.get("date")})
    (fichiers / "verif.chiffre").write_bytes(publier.chiffrer(VERIF_CLUB, cle_club))
    donnees = {"maj": (etat.get("derniere_maj") or {}).get("fin"), "sel": publier.SEL, "iterations": publier.ITERATIONS,
               "documents": documents}
    js = json.dumps(donnees, ensure_ascii=False).replace("<", "\\u003c")
    (club / "index.html").write_text(GABARIT_CLUB.read_text(encoding="utf-8").replace("__DONNEES_JSON__", js), encoding="utf-8")


def construire(site, dossier, mot_de_passe, mot_de_passe_gg, mot_de_passe_club=""):
    """Prépare dans `dossier` le site Netlify : accueil public, club/ (espace club) et gg/ (copie
    re-chiffrée du site GitHub). Sans leur propre mot de passe, club/ et gg/ ne sont pas publiés
    (jamais avec celui du site GitHub)."""
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)
    cle_site = publier.cle(mot_de_passe)
    if mot_de_passe_gg:
        copie_rechiffree(site, dossier / "gg", cle_site, publier.cle(mot_de_passe_gg))
    if mot_de_passe_club:
        espace_club(site, dossier / "club", cle_site, publier.cle(mot_de_passe_club))
    (dossier / "index.html").write_text(page_publique(site, mot_de_passe), encoding="utf-8")
    (dossier / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    # En-têtes Netlify : pas de référencement, et des pages toujours à jour (pas de vieille copie en cache)
    (dossier / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n", encoding="utf-8")
    return dossier


def archive(dossier):
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(dossier.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(dossier).as_posix())
    return tampon.getvalue()


def deployer(dossier, jeton, site=SITE_PAR_DEFAUT, attente=120):
    """Envoie le site (archive zip) sur Netlify et attend qu'il soit en ligne. Renvoie l'adresse."""
    entetes = {"Authorization": f"Bearer {jeton}"}
    r = requests.post(f"{API}/sites/{site}/deploys", data=archive(dossier), timeout=300,
                      headers={**entetes, "Content-Type": "application/zip"})
    if r.status_code == 401:
        raise ErreurNetlify("jeton Netlify refusé (expiré ou mal copié) : refaire le secret NETLIFY_AUTH_TOKEN")
    if r.status_code in (403, 404):
        raise ErreurNetlify(f"site Netlify « {site} » introuvable pour ce jeton : vérifier son nom "
                            "(variable NETLIFY_SITE) et que le jeton est celui du compte qui possède le site")
    if not r.ok:
        raise ErreurNetlify(f"Netlify a répondu {r.status_code} : {r.text[:300]}")
    deploiement = r.json()
    fin = time.time() + attente
    while deploiement.get("state") not in ("ready", "error") and time.time() < fin:
        time.sleep(3)
        deploiement = requests.get(f"{API}/deploys/{deploiement['id']}", headers=entetes, timeout=60).json()
    if deploiement.get("state") == "error":
        raise ErreurNetlify(f"Netlify n'a pas pu publier le site : {deploiement.get('error_message')}")
    return deploiement.get("ssl_url") or deploiement.get("url") or f"https://{site}"


def main():
    parser = argparse.ArgumentParser(description="Copie de secours du site sur Netlify")
    parser.add_argument("--site", default=str(RACINE / "site"), help="site GitHub déjà construit")
    parser.add_argument("--dossier", default=str(RACINE / "site-netlify"), help="dossier préparé pour Netlify")
    args = parser.parse_args()
    jeton = os.environ.get("NETLIFY_AUTH_TOKEN", "")
    if not jeton:
        print("Netlify : pas de jeton (secret NETLIFY_AUTH_TOKEN), copie non envoyée. Voir PUBLICATION.md.")
        return
    nom = os.environ.get("NETLIFY_SITE") or SITE_PAR_DEFAUT
    mot_de_passe_gg = os.environ.get("MOT_DE_PASSE_GG", "")
    mot_de_passe_club = os.environ.get("MOT_DE_PASSE_CLUB", "")
    for secret, valeur, partie in (("MOT_DE_PASSE_CLUB", mot_de_passe_club, "/club/"), ("MOT_DE_PASSE_GG", mot_de_passe_gg, "/gg/")):
        if not valeur:
            print(f"::warning::Pas de secret {secret} : {partie} n'est pas publié sur Netlify.")
    try:
        dossier = construire(Path(args.site), Path(args.dossier), os.environ.get("MOT_DE_PASSE_SITE", ""),
                             mot_de_passe_gg, mot_de_passe_club)
        adresse = deployer(dossier, jeton, nom)
    except (ErreurNetlify, requests.RequestException, ValueError) as e:
        # Le site GitHub est déjà publié : la copie Netlify en échec est signalée sans tout faire échouer.
        print(f"::warning::Copie Netlify non publiée : {e}")
        sys.exit(0)
    base = adresse.rstrip("/")
    print(f"Copie Netlify publiée : {base}/ (accueil public)"
          + (f", {base}/club/ (mot de passe du club)" if mot_de_passe_club else "")
          + (f", {base}/gg/ (mot de passe de /gg/)" if mot_de_passe_gg else ""))


if __name__ == "__main__":
    main()

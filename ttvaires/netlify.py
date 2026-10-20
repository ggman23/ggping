"""Copie de secours du site sur Netlify (https://ggping.netlify.app/).

- https://ggping.netlify.app/ : la page des adversaires (vaires.html), lisible par tout le club
  sans mot de passe (non référencée par les moteurs de recherche : robots.txt et en-tête noindex) ;
- https://ggping.netlify.app/gg/ : la copie du site GitHub (page d'accueil, toutes les pages,
  l'Excel et les images), re-chiffrée avec son propre mot de passe (secret MOT_DE_PASSE_GG, à donner
  aux capitaines) : le mot de passe du site GitHub reste secret. Sans MOT_DE_PASSE_GG, /gg/ n'est
  pas publié.

Lancé par le workflow GitHub après la publication du site (dossier site/ prêt), donc après chaque
mise à jour, qu'elle vienne du PC (option 7) ou du téléphone :
  python -m ttvaires.netlify
Variables d'environnement : NETLIFY_AUTH_TOKEN (jeton Netlify ; sans lui, rien n'est fait),
NETLIFY_SITE (par défaut ggping.netlify.app), MOT_DE_PASSE_SITE (pour lire le site GitHub),
MOT_DE_PASSE_GG (celui de /gg/).
"""

import argparse
import base64
import io
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


def construire(site, dossier, mot_de_passe, mot_de_passe_gg):
    """Prépare dans `dossier` le site Netlify : accueil public + gg/ (copie re-chiffrée du site GitHub).
    Sans mot de passe propre à /gg/, /gg/ n'est pas publié (jamais avec celui du site GitHub)."""
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)
    if mot_de_passe_gg:
        copie_rechiffree(site, dossier / "gg", publier.cle(mot_de_passe), publier.cle(mot_de_passe_gg))
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
    if not mot_de_passe_gg:
        print("::warning::Pas de secret MOT_DE_PASSE_GG : /gg/ n'est pas publié sur Netlify (seulement l'accueil).")
    try:
        dossier = construire(Path(args.site), Path(args.dossier), os.environ.get("MOT_DE_PASSE_SITE", ""), mot_de_passe_gg)
        adresse = deployer(dossier, jeton, nom)
    except (ErreurNetlify, requests.RequestException, ValueError) as e:
        # Le site GitHub est déjà publié : la copie Netlify en échec est signalée sans tout faire échouer.
        print(f"::warning::Copie Netlify non publiée : {e}")
        sys.exit(0)
    print(f"Copie Netlify publiée : {adresse} (accueil public)"
          + (f" et {adresse.rstrip('/')}/gg/ (mot de passe de /gg/)" if mot_de_passe_gg else ""))


if __name__ == "__main__":
    main()

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
import gzip
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from urllib.parse import quote

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


def chiffrer_stable(donnees, cle):
    """Comme publier.chiffrer, mais un même contenu donne toujours le même fichier (vecteur
    d'initialisation tiré du contenu) : une archive, qui ne change plus, n'est pas renvoyée à
    Netlify à chaque mise à jour. Seule l'égalité de deux contenus identiques se voit."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = hmac.new(cle, donnees, hashlib.sha256).digest()[:12]
    return iv + AESGCM(cle).encrypt(iv, gzip.compress(donnees, mtime=0), None)


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
            cible.write_bytes(chiffrer_stable(publier.dechiffrer(f.read_bytes(), cle_site), cle_gg))
            continue
        texte = f.read_text(encoding="utf-8") if f.suffix == ".html" else None
        m = CHIFFRE.search(texte) if texte else None
        if m:  # page verrouillée : seul le contenu chiffré change
            donnees = publier.dechiffrer(base64.b64decode(m[1]), cle_site)
            nouveau = base64.b64encode(chiffrer_stable(donnees, cle_gg)).decode("ascii")
            cible.write_text(texte[:m.start(1)] + nouveau + texte[m.end(1):], encoding="utf-8")
        else:
            shutil.copy2(f, cible)


def _clair(fichier, cle):
    """Contenu d'un fichier du site GitHub : page verrouillée (HTML) ou fichier .chiffre (Excel, image)."""
    if fichier.suffix == ".chiffre":
        return publier.dechiffrer(fichier.read_bytes(), cle)
    return publier.dechiffrer(base64.b64decode(CHIFFRE.search(fichier.read_text(encoding="utf-8"))[1]), cle)


def _documents_club(site, etat, fichiers, prefixe, cle_site, cle_club):
    """Re-chiffre pour /club/ les pages, l'Excel et les images d'un site (celui du jour ou une archive)
    dans `fichiers`, sous leur nom d'origine ; renvoie leur liste (chemin : prefixe + nom.chiffre)."""
    fichiers.mkdir(parents=True, exist_ok=True)
    documents = []
    for publie, info in etat.get("pages", {}).items():
        if not (site / publie).exists():
            continue
        nom = info.get("nom_telecharge") or publie.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(chiffrer_stable(_clair(site / publie, cle_site), cle_club))
        excel = nom.endswith(".xlsx")
        documents.append({"fichier": nom, "chemin": f"{prefixe}{nom}.chiffre", "type": "excel" if excel else "page",
                          "titre": info.get("titre", nom), "description": info.get("description", ""), "date": info.get("date"),
                          "verification": "" if excel else info.get("verification", ""),
                          "ordre": ORDRE_CLUB.index(nom) if nom in ORDRE_CLUB else len(ORDRE_CLUB)})
    for publie, info in etat.get("images", {}).items():
        if not (site / publie).exists():
            continue
        nom = info.get("nom_telecharge") or Path(publie).name.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(chiffrer_stable(_clair(site / publie, cle_site), cle_club))
        documents.append({"fichier": nom, "chemin": f"{prefixe}{nom}.chiffre", "type": "image", "titre": info.get("titre", nom),
                          "groupe": info.get("groupe"), "ordre": info.get("ordre", 0), "date": info.get("date")})
    return documents


def espace_club(site, club, cle_site, cle_club):
    """/club/ : chaque page, l'Excel et chaque image (du jour, et de chaque journée archivée),
    re-chiffrés avec la clé du club sous leur nom d'origine, et la page de navigation
    (gabarit_club.html) qui les déchiffre dans le navigateur. La liste des documents (titres,
    dates) ne contient aucun nom de joueur."""
    fichier_etat = site / "etat.json"
    etat = json.loads(fichier_etat.read_text(encoding="utf-8")) if fichier_etat.exists() else {}
    documents = _documents_club(site, etat, club / "fichiers", "fichiers/", cle_site, cle_club)
    archives = []
    for cle_archive, a in sorted(etat.get("archives", {}).items(),
                                 key=lambda x: (x[1].get("saison", ""), x[1].get("phase", 0), x[1].get("journee", 0)), reverse=True):
        dossier = site / a["dossier"]
        if not (dossier / "etat.json").exists():
            continue
        etat_archive = json.loads((dossier / "etat.json").read_text(encoding="utf-8"))
        archives.append({"cle": cle_archive, "titre": a["titre"], "journee": a.get("journee"), "phase": a.get("phase"),
                         "saison": a.get("saison"), "date_reference": a.get("date_reference"),
                         "documents": _documents_club(dossier, etat_archive, club / "archives" / cle_archive / "fichiers",
                                                      f"archives/{cle_archive}/fichiers/", cle_site, cle_club)})
    (club / "fichiers" / "verif.chiffre").write_bytes(chiffrer_stable(VERIF_CLUB, cle_club))
    donnees = {"maj": (etat.get("derniere_maj") or {}).get("fin"), "sel": publier.SEL, "iterations": publier.ITERATIONS,
               "documents": documents, "archives": archives}
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


def deployer(dossier, jeton, site=SITE_PAR_DEFAUT, attente=180):
    """Envoie le site sur Netlify par empreintes : Netlify ne demande que les fichiers qu'il n'a pas
    déjà (les archives, qui ne changent plus, ne repartent pas à chaque fois). Attend qu'il soit en
    ligne et renvoie son adresse."""
    entetes = {"Authorization": f"Bearer {jeton}"}
    fichiers = {"/" + f.relative_to(dossier).as_posix(): f for f in sorted(dossier.rglob("*")) if f.is_file()}
    empreintes = {chemin: hashlib.sha1(f.read_bytes()).hexdigest() for chemin, f in fichiers.items()}
    r = requests.post(f"{API}/sites/{site}/deploys", json={"files": empreintes}, headers=entetes, timeout=120)
    if r.status_code == 401:
        raise ErreurNetlify("jeton Netlify refusé (expiré ou mal copié) : refaire le secret NETLIFY_AUTH_TOKEN")
    if r.status_code in (403, 404):
        raise ErreurNetlify(f"site Netlify « {site} » introuvable pour ce jeton : vérifier son nom "
                            "(variable NETLIFY_SITE) et que le jeton est celui du compte qui possède le site")
    if not r.ok:
        raise ErreurNetlify(f"Netlify a répondu {r.status_code} : {r.text[:300]}")
    deploiement = r.json()
    demandes, envoyes = set(deploiement.get("required") or []), 0
    for chemin, f in fichiers.items():
        if empreintes[chemin] not in demandes:
            continue
        demandes.discard(empreintes[chemin])  # deux fichiers identiques : un seul envoi
        rf = requests.put(f"{API}/deploys/{deploiement['id']}/files{quote(chemin)}", data=f.read_bytes(), timeout=300,
                          headers={**entetes, "Content-Type": "application/octet-stream"})
        if not rf.ok:
            raise ErreurNetlify(f"envoi de {chemin} refusé par Netlify ({rf.status_code})")
        envoyes += 1
    print(f"Netlify : {envoyes} fichier(s) envoyé(s) sur {len(fichiers)} (les autres n'ont pas changé)", flush=True)
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

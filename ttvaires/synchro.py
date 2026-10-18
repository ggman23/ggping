"""Données du PC envoyées sur GitHub, pour que la mise à jour en ligne donne le même résultat.

pingpocket.fr refuse les serveurs de GitHub et le dossier import (listes des licenciés
enregistrées depuis le navigateur) n'existe que sur le PC. Après chaque lancement sur le PC,
l'outil envoie donc sur GitHub, **chiffrés avec le mot de passe du site** :
- les fichiers du dossier import ;
- les pages de pingpocket.fr gardées en cache (effectifs, salles, historiques des classements)
  et l'état de la page effectif (joueurs déjà vus, pour signaler les nouveaux) ;
puis il lance la mise à jour du site. La mise à jour en ligne reprend ces fichiers (avec leur
date d'origine) et n'interroge pas pingpocket.fr : elle produit les mêmes pages que le PC.

Le fichier chiffré est déposé comme pièce jointe d'une version (« release ») du dépôt, remplacé
à chaque envoi : il n'alourdit pas l'historique. Réglages du PC (jeton GitHub, mot de passe) :
fichier publication.local.json, jamais envoyé sur GitHub.

  python -m ttvaires.synchro --configurer   # réglage (lancer.bat, option 7)
  python -m ttvaires.synchro --envoyer      # envoi seul (fait aussi après chaque lancement)
  python -m ttvaires.synchro --recevoir     # dans le workflow GitHub
"""

import argparse
import getpass
import io
import json
import os
import sys
import tarfile
from pathlib import Path

import requests

from . import publier

RACINE = Path(__file__).resolve().parent.parent
CONFIG = RACINE / "publication.local.json"
DEPOT_PAR_DEFAUT = "ggman23/ggping"
ETIQUETTE = "donnees-pc"
FICHIER = "donnees-pc.chiffre"
API = "https://api.github.com"
EXTENSIONS_IMPORT = (".html", ".htm", ".mhtml", ".mht")


class ErreurSynchro(Exception):
    pass


# ---------------------------------------------------------------------------
# Paquet de données (archive tar.gz chiffrée)
# ---------------------------------------------------------------------------

def _page_pingpocket(fichier):
    """Pages de pingpocket (fragments HTML) et état de l'effectif ; les réponses JSON de l'API
    FFTT, elles, sont relues en ligne."""
    if fichier.name.startswith("effectif_") and fichier.suffix == ".json":
        return True
    with open(fichier, "rb") as f:
        return f.read(1) != b"{"


def paquet(racine=RACINE):
    """Archive des fichiers du PC utiles à la mise à jour en ligne (dates de modification gardées)."""
    tampon = io.BytesIO()
    nb = 0
    with tarfile.open(fileobj=tampon, mode="w:gz", compresslevel=9) as tar:
        for dossier, garder in (("import", lambda f: f.suffix.lower() in EXTENSIONS_IMPORT), ("cache", _page_pingpocket)):
            base = racine / dossier
            if not base.is_dir():
                continue
            for f in sorted(base.iterdir()):
                if f.is_file() and garder(f):
                    tar.add(f, arcname=f"{dossier}/{f.name}", recursive=False)
                    nb += 1
    return tampon.getvalue(), nb


def deballer(archive, racine=RACINE):
    """Extrait l'archive ; un fichier déjà présent et plus récent est gardé. Renvoie le nombre extrait."""
    nb = 0
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for m in tar.getmembers():
            dossier, _, nom = m.name.partition("/")
            if not (m.isfile() and dossier in ("import", "cache") and nom and "/" not in nom and nom not in (".", "..")):
                continue  # rien d'autre que des fichiers de import/ et cache/
            cible = racine / dossier / nom
            if cible.exists() and cible.stat().st_mtime >= m.mtime and not nom.startswith("effectif_"):
                continue  # (l'état de la page effectif du PC fait toujours foi)
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(tar.extractfile(m).read())
            os.utime(cible, (m.mtime, m.mtime))
            nb += 1
    return nb


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def lire_config():
    if not CONFIG.exists():
        return None
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
    except ValueError:
        return None
    return config if config.get("jeton") and config.get("mot_de_passe") else None


def _github(config, methode, chemin, droit="Contents", **options):
    """Appel à l'API GitHub. `droit` : la permission du jeton nécessaire à cet appel (pour le message d'erreur)."""
    entetes = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {config['jeton']}",
               "X-GitHub-Api-Version": "2022-11-28", **options.pop("headers", {})}
    url = chemin if chemin.startswith("http") else API + chemin
    r = requests.request(methode, url, headers=entetes, timeout=120, **options)
    if r.status_code == 401:
        raise ErreurSynchro("jeton GitHub refusé (expiré ou mal copié) : refaire le réglage, option 7 du menu")
    if r.status_code == 403:
        raise ErreurSynchro(
            f"le jeton GitHub n'a pas le droit « {droit} : Read and write » sur {config['depot']}.\n"
            f"    Pour l'ajouter (le jeton ne change pas) : github.com > photo de profil > Settings > Developer settings\n"
            f"    > Personal access tokens > Fine-grained tokens > ton jeton > Edit > Repository permissions >\n"
            f"    {droit} : Read and write (et aussi {'Actions' if droit == 'Contents' else 'Contents'} : Read and write) > Update.\n"
            f"    Puis relance l'option 7 et appuie sur Entrée à chaque question pour garder le réglage.")
    return r


def _version(config):
    """La version (release) qui porte le fichier chiffré, créée au premier envoi."""
    depot = config["depot"]
    r = _github(config, "GET", f"/repos/{depot}/releases/tags/{ETIQUETTE}")
    if r.status_code == 200:
        return r.json()
    branche = _github(config, "GET", f"/repos/{depot}").json().get("default_branch")
    r = _github(config, "POST", f"/repos/{depot}/releases", json={
        "tag_name": ETIQUETTE, "target_commitish": branche, "name": "Données du PC (chiffrées)", "prerelease": True,
        "body": "Données envoyées par le PC (dossier import, pages de pingpocket.fr), chiffrées avec le mot de passe "
                "du site, pour que la mise à jour en ligne donne le même résultat que le PC. Ne pas supprimer."})
    if r.status_code != 201:
        raise ErreurSynchro(f"création de la version « {ETIQUETTE} » impossible : HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def envoyer(config, declencher=True):
    """Chiffre et envoie les données du PC, puis lance la mise à jour du site."""
    archive, nb = paquet()
    chiffre = publier.chiffrer(archive, publier.cle(config["mot_de_passe"]))
    version = _version(config)
    for piece in version.get("assets", []):
        if piece["name"] == FICHIER:
            _github(config, "DELETE", f"/repos/{config['depot']}/releases/assets/{piece['id']}")
    url = version["upload_url"].split("{")[0]
    r = _github(config, "POST", url, params={"name": FICHIER}, data=chiffre,
                headers={"Content-Type": "application/octet-stream"})
    if r.status_code != 201:
        raise ErreurSynchro(f"envoi refusé par GitHub : HTTP {r.status_code} {r.text[:200]}")
    print(f"Données du PC envoyées sur GitHub (chiffrées) : {nb} fichiers, {len(chiffre) / 1e6:.1f} Mo")
    if declencher:
        depot = config["depot"]
        branche = _github(config, "GET", f"/repos/{depot}").json().get("default_branch")
        r = _github(config, "POST", f"/repos/{depot}/actions/workflows/{publier.WORKFLOW}/dispatches", droit="Actions",
                    json={"ref": branche, "inputs": {"pages": "tout"}})
        if r.status_code != 204:
            raise ErreurSynchro(f"lancement de la mise à jour du site impossible : HTTP {r.status_code} {r.text[:200]}")
        print(f"Mise à jour du site lancée : pages identiques en ligne dans 5 à 10 minutes "
              f"(https://{depot.split('/')[0].lower()}.github.io/{depot.split('/')[1]}/).")


def recevoir(depot, mot_de_passe):
    """Dans le workflow : récupère et extrait les données envoyées par le PC (dépôt public)."""
    url = f"https://github.com/{depot}/releases/download/{ETIQUETTE}/{FICHIER}"
    r = requests.get(url, timeout=300)
    if r.status_code == 404:
        print("Aucune donnée envoyée par le PC pour le moment : effectifs limités aux joueurs alignés.")
        return 0
    r.raise_for_status()
    try:
        archive = publier.dechiffrer(r.content, publier.cle(mot_de_passe))
    except Exception:
        raise ErreurSynchro("données du PC illisibles : le mot de passe du PC (option 7 du menu) et le secret "
                            "MOT_DE_PASSE_SITE doivent être identiques")
    date = r.headers.get("last-modified", "")
    nb = deballer(archive)
    print(f"Données du PC reçues ({date}) : {nb} fichiers mis à jour")
    return nb


# ---------------------------------------------------------------------------
# Réglage sur le PC
# ---------------------------------------------------------------------------

def configurer():
    print("Lien avec le téléphone : après chaque lancement, le PC envoie ses données (chiffrées) sur GitHub")
    print("et met le site à jour, pour que le téléphone affiche exactement les mêmes pages.\n")
    print("Il faut un jeton GitHub (fine-grained) limité au dépôt de l'outil, avec les droits")
    print("  Contents : Read and write   et   Actions : Read and write")
    print("à créer sur https://github.com/settings/personal-access-tokens/new (voir PUBLICATION.md).")
    print("Le même jeton peut servir pour le bouton du site sur le téléphone.\n")
    ancien = lire_config() or {}
    depot = input(f"Dépôt GitHub [{ancien.get('depot', DEPOT_PAR_DEFAUT)}] : ").strip() or ancien.get("depot", DEPOT_PAR_DEFAUT)
    jeton = getpass.getpass("Jeton GitHub (github_pat_..., invisible à la saisie ; Entrée = garder l'ancien) : ").strip() \
        or ancien.get("jeton", "")
    mdp = getpass.getpass("Mot de passe du site (le même que le secret MOT_DE_PASSE_SITE ; Entrée = garder) : ") \
        or ancien.get("mot_de_passe", "")
    if mdp and mdp != ancien.get("mot_de_passe") and getpass.getpass("Mot de passe, encore une fois : ") != mdp:
        print("Les deux saisies diffèrent : rien n'est enregistré.")
        return False
    if not (jeton and mdp):
        print("Jeton et mot de passe sont nécessaires : rien n'est enregistré.")
        return False
    config = {"depot": depot, "jeton": jeton, "mot_de_passe": mdp}
    r = _github(config, "GET", f"/repos/{depot}")
    if r.status_code != 200:
        print(f"Dépôt {depot} inaccessible avec ce jeton (HTTP {r.status_code}) : rien n'est enregistré.")
        return False
    CONFIG.write_text(json.dumps(config, indent=1), encoding="utf-8")
    print(f"Réglage enregistré dans {CONFIG.name} (reste sur ce PC).")
    envoyer(config)
    return True


def apres_lancement():
    """Appelé à la fin d'un lancement sur le PC : envoi automatique si le lien est réglé."""
    config = lire_config()
    if not config:
        return None
    print("\n=== Envoi des données au site (téléphone) ===")
    try:
        envoyer(config)
        return "données envoyées, site en cours de mise à jour"
    except Exception as e:  # les pages du PC sont faites : un échec d'envoi ne doit rien bloquer
        print(f"  ! envoi impossible : {e}")
        return f"ENVOI IMPOSSIBLE ({e})"


def main():
    parser = argparse.ArgumentParser(description="Données du PC pour la mise à jour en ligne")
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--configurer", action="store_true", help="régler le lien avec le site (jeton, mot de passe)")
    groupe.add_argument("--envoyer", action="store_true", help="envoyer les données du PC et mettre le site à jour")
    groupe.add_argument("--recevoir", action="store_true", help="(workflow GitHub) reprendre les données du PC")
    args = parser.parse_args()
    try:
        if args.configurer:
            configurer()
        elif args.envoyer:
            config = lire_config()
            if not config:
                print("Lien avec le téléphone pas encore réglé : option 7 du menu de lancer.bat.")
                sys.exit(1)
            envoyer(config)
        else:
            recevoir(os.environ.get("GITHUB_REPOSITORY", DEPOT_PAR_DEFAUT), os.environ.get("MOT_DE_PASSE_SITE", ""))
    except ErreurSynchro as e:
        print(f"!!! {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"!!! GitHub injoignable : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

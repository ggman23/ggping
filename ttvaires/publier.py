"""Publication des pages sur un site (GitHub Pages), consultables depuis un téléphone.

Les pages contiennent des données personnelles (dont celles de mineurs) : elles sont publiées
**chiffrées** (AES-256-GCM, clé tirée du mot de passe par PBKDF2-SHA256). Le site est public,
mais une page n'est lisible qu'avec le mot de passe, saisi dans le navigateur ; rien n'est
déchiffré sur le serveur. La page d'accueil, elle, ne contient que les dates de mise à jour et
le bilan des vérifications (aucun nom de joueur).

Utilisé par le workflow GitHub Actions (.github/workflows/mise-a-jour.yml) :
  python -m ttvaires.publier --recuperer URL_DU_SITE   # reprend les pages déjà en ligne
  python -m ttvaires.publier                           # chiffre les pages de sortie/ dans site/
Le mot de passe est lu dans la variable d'environnement MOT_DE_PASSE_SITE.
"""

import argparse
import base64
import gzip
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
GABARIT_VERROU = Path(__file__).with_name("gabarit_verrou.html")
GABARIT_ACCUEIL = Path(__file__).with_name("gabarit_accueil.html")

SEL = "cvtt-vaires-ggping-v1"  # public : sert seulement à ce que la clé soit propre à ce site
ITERATIONS = 310_000
WORKFLOW = "mise-a-jour.yml"

# Fichier produit dans sortie/ -> (fichier publié, titre, description)
PUBLIES = {
    "vaires.html": ("adversaires.html", "Adversaires", "Effectifs, brûlages et compositions probables des adversaires, calendrier, vérifications"),
    "resultats_vaires.html": ("resultats.html", "Résultats des joueurs", "Points gagnés ou perdus à chaque journée de championnat"),
    "resultats_vaires.xlsx": ("resultats_vaires.xlsx.chiffre", "Résultats (Excel)", "Classeur à télécharger"),
    "rencontres_vaires.html": ("rencontres.html", "Feuilles de match", "Chaque rencontre de Vaires : parties, joueurs et scores des manches"),
    "effectif_vaires.html": ("effectif.html", "Effectif et brûlages", "Joueurs de Vaires : équipes jouées, brûlés et possibles par équipe"),
    "classement_virtuel.html": ("classement_virtuel.html", "Classement virtuel", "Toutes compétitions, meilleures perfs et pires contres"),
}


class ErreurPublication(Exception):
    pass


# ---------------------------------------------------------------------------
# Chiffrement
# ---------------------------------------------------------------------------

def cle(mot_de_passe):
    return hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"), SEL.encode("utf-8"), ITERATIONS, 32)


def chiffrer(donnees, cle_):
    """Données compressées puis chiffrées : vecteur d'initialisation (12 octets) + chiffré + étiquette."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = os.urandom(12)
    return iv + AESGCM(cle_).encrypt(iv, gzip.compress(donnees, mtime=0), None)


def dechiffrer(brut, cle_):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return gzip.decompress(AESGCM(cle_).decrypt(brut[:12], brut[12:], None))


def page_verrouillee(html, titre, cle_):
    """Page HTML qui demande le mot de passe puis affiche la page d'origine (déchiffrée dans le navigateur)."""
    chiffre = base64.b64encode(chiffrer(html.encode("utf-8"), cle_)).decode("ascii")
    return (GABARIT_VERROU.read_text(encoding="utf-8")
            .replace("__TITRE__", titre).replace("__SEL__", SEL)
            .replace("__ITERATIONS__", str(ITERATIONS)).replace("__CHIFFRE__", chiffre))


# ---------------------------------------------------------------------------
# Construction du site
# ---------------------------------------------------------------------------

def recuperer(url, site):
    """Reprend les fichiers déjà en ligne : une page qui n'est pas régénérée reste publiée."""
    import requests

    site.mkdir(parents=True, exist_ok=True)
    url = url.rstrip("/") + "/"
    try:
        r = requests.get(url + "etat.json", timeout=60)
        r.raise_for_status()
        etat = r.json()
    except (requests.RequestException, ValueError) as e:
        print(f"Aucun site précédent récupéré ({e}) : premier déploiement ?")
        return
    (site / "etat.json").write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    for nom in etat.get("fichiers", []):
        try:
            r = requests.get(url + nom, timeout=120)
            r.raise_for_status()
            (site / nom).parent.mkdir(parents=True, exist_ok=True)
            (site / nom).write_bytes(r.content)
            print(f"Repris du site : {nom}")
        except requests.RequestException as e:
            print(f"  ! {nom} non repris : {e}")


def publier(sortie, site, mot_de_passe, depot="", branche=""):
    """Chiffre les fichiers produits par le dernier lancement et écrit l'accueil et etat.json."""
    if not mot_de_passe:
        raise ErreurPublication(
            "Mot de passe absent : ajoutez le secret MOT_DE_PASSE_SITE dans les réglages du dépôt GitHub "
            "(Settings > Secrets and variables > Actions). Rien n'est publié sans mot de passe.")
    bilan = json.loads((sortie / "bilan.json").read_text(encoding="utf-8"))
    site.mkdir(parents=True, exist_ok=True)
    fichier_etat = site / "etat.json"
    etat = json.loads(fichier_etat.read_text(encoding="utf-8")) if fichier_etat.exists() else {}
    etat.setdefault("pages", {})
    etat.setdefault("images", {})
    cle_ = cle(mot_de_passe)

    for page in bilan["pages"]:
        for nom in page["fichiers"]:
            if nom not in PUBLIES:
                continue
            publie, titre, description = PUBLIES[nom]
            donnees = (sortie / nom).read_bytes()
            if publie.endswith(".html"):
                (site / publie).write_text(page_verrouillee(donnees.decode("utf-8"), titre, cle_), encoding="utf-8")
            else:
                (site / publie).write_bytes(chiffrer(donnees, cle_))
            etat["pages"][publie] = {"titre": titre, "description": description, "date": bilan["fin"],
                                     "verification": page["resume"], "telechargement": not publie.endswith(".html"),
                                     "nom_telecharge": nom}
            print(f"Publié (chiffré) : {publie}")
        publier_images(page, bilan["fin"], sortie, site, etat, cle_)

    etat.update({
        "depot": depot, "branche": branche, "workflow": WORKFLOW, "sel": SEL, "iterations": ITERATIONS,
        "derniere_maj": {"debut": bilan["debut"], "fin": bilan["fin"],
                         "bilans": [{"nom": p["nom"], "resume": p["resume"]} for p in bilan["pages"]]},
        "fichiers": sorted(n for n in [*etat["pages"], *etat["images"]] if (site / n).exists()),
    })
    fichier_etat.write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
    js = json.dumps(etat, ensure_ascii=False).replace("<", "\\u003c")
    (site / "index.html").write_text(GABARIT_ACCUEIL.read_text(encoding="utf-8").replace("__ETAT_JSON__", js),
                                     encoding="utf-8")
    (site / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (site / ".nojekyll").write_text("", encoding="utf-8")
    return etat


def publier_images(page, date, sortie, site, etat, cle_):
    """Images PNG d'une page : celles du lancement précédent pour cette page sont remplacées
    (leur nombre et leurs noms peuvent changer d'une fois à l'autre : J3 puis J4...)."""
    if page["resume"].startswith("PAGE NON GÉNÉRÉE"):
        return  # on garde les images de la fois précédente
    for publie in [n for n, i in etat["images"].items() if i.get("groupe") == page["nom"]]:
        (site / publie).unlink(missing_ok=True)
        del etat["images"][publie]
    for ordre, image in enumerate(page.get("images", [])):
        nom = image["fichier"]
        publie = f"images/{Path(nom).name}.chiffre"
        (site / publie).parent.mkdir(parents=True, exist_ok=True)
        (site / publie).write_bytes(chiffrer((sortie / nom).read_bytes(), cle_))
        etat["images"][publie] = {"titre": image["titre"], "groupe": page["nom"], "ordre": ordre, "date": date,
                                  "nom_telecharge": Path(nom).name}
    if page.get("images"):
        print(f"Publié (chiffré) : {len(page['images'])} image(s) « {page['nom']} »")


def main():
    parser = argparse.ArgumentParser(description="Publication du site (pages chiffrées)")
    parser.add_argument("--sortie", default=str(RACINE / "sortie"), help="dossier des pages générées")
    parser.add_argument("--site", default=str(RACINE / "site"), help="dossier du site à publier")
    parser.add_argument("--recuperer", metavar="URL", help="reprendre d'abord les fichiers du site en ligne")
    args = parser.parse_args()
    site = Path(args.site)
    if args.recuperer:
        recuperer(args.recuperer, site)
        return
    try:
        publier(Path(args.sortie), site, os.environ.get("MOT_DE_PASSE_SITE", ""),
                os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_REF_NAME", ""))
    except ErreurPublication as e:
        print(f"!!! {e}")
        sys.exit(1)
    print(f"Site prêt dans {site} ({datetime.now():%d/%m/%Y %H:%M})")


if __name__ == "__main__":
    main()

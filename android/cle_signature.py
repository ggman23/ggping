"""Clé de signature de l'application Android, toujours la même d'une construction à l'autre (sans
elle, Android refuse d'installer une nouvelle version par-dessus l'ancienne).

Elle est créée à la première construction puis gardée dans la version « application-android » du
dépôt, chiffrée avec le mot de passe du site (comme les données du PC) : cle-apk.chiffre. Le
workflow application-android.yml la récupère ici :

  python android/cle_signature.py DOSSIER

Écrit DOSSIER/cle.p12 et donne au workflow CLE et CLE_MDP (masqué dans le journal). Si la clé est
nouvelle, DOSSIER/cle-apk.chiffre est à publier avec l'APK. Si elle existe mais ne se déchiffre pas
(mot de passe du site changé), rien n'est créé à sa place : l'erreur est signalée.
"""

import base64
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ttvaires import publier  # noqa: E402

VERSION = "application-android"
FICHIER = "cle-apk.chiffre"


def cle_publiee(depot):
    """Contenu chiffré de la clé publiée, ou None si elle n'existe pas encore."""
    r = requests.get(f"https://api.github.com/repos/{depot}/releases/tags/{VERSION}", timeout=60,
                     headers={"Authorization": f"Bearer {os.environ['GH_TOKEN']}"} if os.environ.get("GH_TOKEN") else {})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    for piece in r.json().get("assets", []):
        if piece["name"] == FICHIER:
            fichier = requests.get(piece["browser_download_url"], timeout=60)
            fichier.raise_for_status()
            return fichier.content
    return None


def main():
    dossier = Path(sys.argv[1])
    dossier.mkdir(parents=True, exist_ok=True)
    mot_de_passe = os.environ.get("MOT_DE_PASSE_SITE", "")
    if not mot_de_passe:
        sys.exit("!!! Secret MOT_DE_PASSE_SITE absent : pas de clé de signature.")
    cle_site = publier.cle(mot_de_passe)
    chiffre = cle_publiee(os.environ.get("GITHUB_REPOSITORY", "ggman23/ggping"))
    if chiffre is not None:
        try:
            contenu = json.loads(publier.dechiffrer(chiffre, cle_site))
        except Exception:  # noqa: BLE001
            sys.exit(f"!!! {FICHIER} ne se déchiffre pas (mot de passe du site changé ?). Rien n'est remplacé : "
                     "supprimer ce fichier de la version « application-android » pour créer une nouvelle clé "
                     "(il faudra alors désinstaller l'ancienne appli avant d'installer la nouvelle).")
        (dossier / "cle.p12").write_bytes(base64.b64decode(contenu["p12"]))
        mdp = contenu["mdp"]
        print("Clé de signature : la même que pour les versions précédentes.")
    else:
        mdp = secrets.token_urlsafe(24)
        subprocess.run(["keytool", "-genkeypair", "-keystore", str(dossier / "cle.p12"), "-storetype", "PKCS12",
                        "-alias", "cvtt", "-keyalg", "RSA", "-keysize", "3072", "-validity", "36500",
                        "-storepass", mdp, "-keypass", mdp, "-dname", "CN=CVTT Vaires"], check=True)
        contenu = {"mdp": mdp, "p12": base64.b64encode((dossier / "cle.p12").read_bytes()).decode("ascii")}
        (dossier / FICHIER).write_bytes(publier.chiffrer(json.dumps(contenu).encode("utf-8"), cle_site))
        print(f"Clé de signature : nouvelle, gardée chiffrée dans {FICHIER}.")
    print(f"::add-mask::{mdp}")
    if os.environ.get("GITHUB_ENV"):
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as env:
            env.write(f"CLE={dossier / 'cle.p12'}\nCLE_MDP={mdp}\n")


if __name__ == "__main__":
    main()

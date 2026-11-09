"""Copie du site sur Cloudflare Pages, en plus de Netlify (gratuit : 500 mises en ligne par mois).

La copie envoyée est celle préparée pour Netlify (dossier site-netlify : accueil public, /club/,
/gg/, et le fichier _headers, que Cloudflare Pages comprend aussi). Cette étape crée le projet au
premier passage, compare l'empreinte de la copie à celle déjà en ligne et dit au workflow s'il faut
l'envoyer ; l'envoi est fait ensuite par wrangler, l'outil officiel de Cloudflare.

Réglages (GitHub : Settings > Secrets and variables > Actions) :
- secret CLOUDFLARE_API_TOKEN : jeton Cloudflare avec la permission « Compte > Cloudflare Pages >
  Modifier » (voir PUBLICATION.md) ;
- secret CLOUDFLARE_ACCOUNT_ID : identifiant du compte Cloudflare ;
- variable CLOUDFLARE_PROJET (facultative) : nom du projet, « ggping » par défaut. L'adresse est
  https://<projet>.pages.dev (Cloudflare ajoute un suffixe si le nom est déjà pris ailleurs).
Sans ces secrets, rien n'est fait.
"""

import argparse
import os
import re
import sys
from pathlib import Path

import requests

from .netlify import SIGNATURE, signature_en_ligne

API = "https://api.cloudflare.com/client/v4"
RACINE = Path(__file__).resolve().parent.parent
PROJET_PAR_DEFAUT = "ggping"


class ErreurCloudflare(Exception):
    pass


def _erreur(r):
    try:
        erreurs = r.json().get("errors") or []
        return "; ".join(f"{e.get('code')} {e.get('message')}" for e in erreurs) or r.text[:300]
    except ValueError:
        return r.text[:300]


def projet(jeton, compte, nom):
    """Adresse (sous-domaine *.pages.dev) du projet, créé s'il n'existe pas encore."""
    entetes = {"Authorization": f"Bearer {jeton}"}
    url = f"{API}/accounts/{compte}/pages/projects"
    r = requests.get(f"{url}/{nom}", headers=entetes, timeout=60)
    if r.status_code in (401, 403):
        raise ErreurCloudflare("jeton Cloudflare refusé : il faut la permission « Cloudflare Pages : Modifier » sur ce "
                               f"compte, et le bon identifiant de compte (secret CLOUDFLARE_ACCOUNT_ID) ({_erreur(r)})")
    if r.status_code == 404:
        print(f"Cloudflare Pages : création du projet « {nom} »", flush=True)
        r = requests.post(url, json={"name": nom, "production_branch": "main"}, headers=entetes, timeout=60)
    if not r.ok:
        raise ErreurCloudflare(f"Cloudflare a répondu {r.status_code} : {_erreur(r)}")
    return r.json()["result"].get("subdomain") or f"{nom}.pages.dev"


def main(arguments=None):
    p = argparse.ArgumentParser(description="Copie du site sur Cloudflare Pages : projet et besoin d'envoi")
    p.add_argument("--dossier", default=str(RACINE / "site-netlify"), help="copie préparée (celle de Netlify)")
    args = p.parse_args(arguments)
    jeton, compte = os.environ.get("CLOUDFLARE_API_TOKEN", ""), os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    nom = (os.environ.get("CLOUDFLARE_PROJET") or PROJET_PAR_DEFAUT).strip().lower()
    sortie = {"envoyer": "false", "projet": nom, "adresse": ""}
    try:
        if not (jeton and compte):
            print("Cloudflare Pages : pas de secrets CLOUDFLARE_API_TOKEN et CLOUDFLARE_ACCOUNT_ID, copie non envoyée. "
                  "Voir PUBLICATION.md.")
            return 0
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,57}", nom):
            raise ErreurCloudflare(f"nom de projet invalide : « {nom} » (lettres minuscules, chiffres et tirets)")
        dossier = Path(args.dossier)
        if not (dossier / "index.html").exists():
            raise ErreurCloudflare("copie du site absente (l'étape Netlify ne l'a pas préparée)")
        hote = projet(jeton, compte, nom)
        sortie["adresse"] = f"https://{hote}/"
        signature = (dossier / SIGNATURE).read_text(encoding="utf-8").strip() if (dossier / SIGNATURE).exists() else ""
        forcer = os.environ.get("FORCER", "").lower() in ("1", "true", "oui")
        if not forcer and signature and signature_en_ligne(hote) == signature:
            print(f"Cloudflare Pages : rien de nouveau depuis la copie en ligne ({sortie['adresse']}), pas d'envoi.")
        else:
            sortie["envoyer"] = "true"
            print(f"Cloudflare Pages : copie à envoyer sur {sortie['adresse']} (club : {sortie['adresse']}club/)")
    except (ErreurCloudflare, requests.RequestException, ValueError, KeyError) as e:
        # Les autres copies sont déjà publiées : on signale sans tout faire échouer
        print(f"::warning::Copie Cloudflare Pages non publiée : {e}")
    finally:
        fichier = os.environ.get("GITHUB_OUTPUT")
        if fichier:
            with open(fichier, "a", encoding="utf-8") as f:
                f.writelines(f"{k}={v}\n" for k, v in sortie.items())
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Publication du site sur GitHub Pages, avec une version différente à chaque mise à jour.

GitHub Pages identifie une publication par le commit du code (« pages_build_version » de l'action
officielle actions/deploy-pages, toujours GITHUB_SHA). Deux mises à jour lancées sur le même commit
(par exemple la mise à jour du lundi après une mise à jour à la main, sans changement de l'outil
entre les deux) donnent le même identifiant : GitHub répond « succès » mais garde l'ancienne
version en ligne. Constaté le 09/11/2026 (le site GitHub est resté à la version de 01:28).

Ici, chaque mise à jour crée donc un commit de publication à part : même contenu que le code
(même arbre), le commit du code pour parent, rangé sur la branche « publication-pages » (remplacée
à chaque fois : l'historique de la branche principale n'est pas touché). Le site est publié avec ce
commit comme version, par les mêmes appels que actions/deploy-pages. Les changements faits avec le
jeton du workflow ne déclenchent aucun autre workflow.

Si cette publication échoue, l'étape suivante du workflow (actions/deploy-pages) prend le relais.
"""

import os
import sys
import time

import requests

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
BRANCHE = "publication-pages"
ERREURS = {"deployment_failed", "deployment_perms_error", "deployment_content_failed", "deployment_cancelled",
           "deployment_lost"}


class ErreurPages(Exception):
    pass


def _appel(methode, chemin, jeton, **options):
    r = requests.request(methode, f"{API}{chemin}", timeout=60, **options, headers={
        "Authorization": f"Bearer {jeton}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    if not r.ok:
        raise ErreurPages(f"{methode} {chemin} : HTTP {r.status_code} {r.text[:200]}")
    return r.json() if r.content else {}


def commit_de_publication(depot, sha, jeton, message):
    """Nouveau commit, même arbre que `sha` (le code), rangé sur la branche de publication."""
    arbre = _appel("GET", f"/repos/{depot}/git/commits/{sha}", jeton)["tree"]["sha"]
    nouveau = _appel("POST", f"/repos/{depot}/git/commits", jeton, json={"message": message, "tree": arbre, "parents": [sha]})["sha"]
    try:
        _appel("PATCH", f"/repos/{depot}/git/refs/heads/{BRANCHE}", jeton, json={"sha": nouveau, "force": True})
    except ErreurPages:  # première fois : la branche n'existe pas encore
        _appel("POST", f"/repos/{depot}/git/refs", jeton, json={"ref": f"refs/heads/{BRANCHE}", "sha": nouveau})
    return nouveau


def jeton_oidc():
    """Jeton OIDC du workflow (permission id-token: write), comme core.getIDToken()."""
    url, jeton = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL"), os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not (url and jeton):
        raise ErreurPages("jeton OIDC indisponible (permission id-token: write ?)")
    r = requests.get(url, headers={"Authorization": f"bearer {jeton}"}, timeout=60)
    if not r.ok:
        raise ErreurPages(f"jeton OIDC refusé : HTTP {r.status_code}")
    return r.json()["value"]


def publier(depot, sha, jeton, artefact, message, attente=600, pause=5):
    """Publie l'artefact « github-pages » déjà envoyé, avec une version de publication unique."""
    version = commit_de_publication(depot, sha, jeton, message)
    print(f"Version de publication : {version} (commit du code {sha[:7]})", flush=True)
    deploiement = _appel("POST", f"/repos/{depot}/pages/deployments", jeton,
                         json={"artifact_id": int(artefact), "pages_build_version": version, "oidc_token": jeton_oidc()})
    ident = deploiement.get("id") or (deploiement.get("status_url") or "").rstrip("/").split("/")[-1] or version
    fin = time.time() + attente
    while time.time() < fin:
        time.sleep(pause)
        etat = _appel("GET", f"/repos/{depot}/pages/deployments/{ident}", jeton).get("status")
        if etat == "succeed":
            return deploiement.get("page_url") or ""
        if etat in ERREURS:
            raise ErreurPages(f"GitHub Pages : {etat}")
    raise ErreurPages("GitHub Pages : publication toujours en cours après 10 minutes")


def main():
    depot, sha = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_SHA", "")
    jeton, artefact = os.environ.get("GITHUB_TOKEN", ""), os.environ.get("ARTIFACT_ID", "")
    if not (depot and sha and jeton and artefact):
        print("::warning::Publication GitHub Pages : contexte incomplet, l'action officielle prend le relais.")
        return 1
    message = f"Publication du site (mise à jour {os.environ.get('GITHUB_RUN_ID', '?')})"
    try:
        adresse = publier(depot, sha, jeton, artefact, message)
    except (ErreurPages, requests.RequestException, ValueError, KeyError) as e:
        print(f"::warning::Publication GitHub Pages avec une version unique impossible ({e}) : "
              "l'action officielle prend le relais.")
        return 1
    print(f"Site GitHub publié : {adresse}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""GitHub Pages : une mise à jour = un commit du code différent.

GitHub Pages identifie une publication par le commit du code sur lequel tourne la mise à jour
(GITHUB_SHA, utilisé par l'action officielle actions/deploy-pages). Deux mises à jour sur le même
commit (par exemple la mise à jour automatique du lundi après une mise à jour à la main, sans
nouvelle version de l'outil entre les deux) : la seconde se dit réussie mais l'ancienne version
reste en ligne (constaté le 09/11/2026). Publier avec un autre commit que celui de la mise à jour
ne marche pas non plus : GitHub l'accepte puis ne la traite jamais (essai du 10/11/2026).

Donc, à la fin de chaque mise à jour (réussie ou non), un commit vide (« Mise à jour du site … »)
est ajouté à la branche : la mise à jour suivante, qu'elle soit lancée par le bouton, le PC ou le
calendrier, tourne sur un commit nouveau et sa publication est bien mise en ligne. Un commit fait
avec le jeton du workflow ne déclenche aucun autre workflow.

  python -m ttvaires.pages commit-suivant   # fin de la mise à jour
  python -m ttvaires.pages nettoyer         # annule la publication bloquée de l'essai du 10/11
"""

import os
import sys
import time

import requests

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
ANCIENNE_BRANCHE = "publication-pages"  # essai du 10/11/2026, abandonné


class ErreurPages(Exception):
    pass


def _appel(methode, chemin, jeton, **options):
    r = requests.request(methode, f"{API}{chemin}", timeout=60, **options, headers={
        "Authorization": f"Bearer {jeton}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    if not r.ok:
        raise ErreurPages(f"{methode} {chemin} : HTTP {r.status_code} {r.text[:200]}")
    return r.json() if r.content else {}


def commit_suivant(depot, branche, jeton, message, essais=3):
    """Ajoute un commit vide (même arbre) au bout de la branche ; renvoie son identifiant."""
    for essai in range(essais):
        tete = _appel("GET", f"/repos/{depot}/git/ref/heads/{branche}", jeton)["object"]["sha"]
        arbre = _appel("GET", f"/repos/{depot}/git/commits/{tete}", jeton)["tree"]["sha"]
        nouveau = _appel("POST", f"/repos/{depot}/git/commits", jeton,
                         json={"message": message, "tree": arbre, "parents": [tete]})["sha"]
        try:  # sans forcer : si quelqu'un a poussé entre-temps, on recommence par-dessus
            _appel("PATCH", f"/repos/{depot}/git/refs/heads/{branche}", jeton, json={"sha": nouveau, "force": False})
            return nouveau
        except ErreurPages:
            if essai == essais - 1:
                raise
            time.sleep(2)


def nettoyer(depot, jeton):
    """Annule la publication restée « en cours » de l'essai du 10/11 (elle bloque les suivantes) et
    supprime sa branche. Ne fait rien si elle n'existe plus."""
    try:
        sha = _appel("GET", f"/repos/{depot}/git/ref/heads/{ANCIENNE_BRANCHE}", jeton)["object"]["sha"]
    except ErreurPages:
        return False
    try:
        _appel("POST", f"/repos/{depot}/pages/deployments/{sha}/cancel", jeton)
        print(f"Publication bloquée {sha[:7]} annulée.")
    except ErreurPages as e:
        print(f"Publication {sha[:7]} : annulation impossible ou inutile ({e}).")
    _appel("DELETE", f"/repos/{depot}/git/refs/heads/{ANCIENNE_BRANCHE}", jeton)
    print(f"Branche {ANCIENNE_BRANCHE} supprimée.")
    return True


def main(arguments=None):
    action = (arguments or sys.argv[1:] or [""])[0]
    depot, jeton = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    branche = os.environ.get("GITHUB_REF_NAME", "")
    if not (depot and jeton):
        print("::warning::GitHub Pages : contexte incomplet (GITHUB_REPOSITORY, GITHUB_TOKEN).")
        return 0
    try:
        if action == "nettoyer":
            nettoyer(depot, jeton)
        elif action == "commit-suivant":
            numero = os.environ.get("GITHUB_RUN_NUMBER", "?")
            sha = commit_suivant(depot, branche, jeton, f"Mise à jour du site n° {numero} (publiée)\n\n"
                                 "Commit vide : la prochaine mise à jour tourne sur un commit nouveau, "
                                 "sinon GitHub Pages ne la mettrait pas en ligne (voir ttvaires/pages.py).")
            print(f"Commit pour la prochaine mise à jour : {sha[:7]} sur {branche}")
        else:
            print("usage : python -m ttvaires.pages commit-suivant | nettoyer")
            return 2
    except (ErreurPages, requests.RequestException, KeyError) as e:
        print(f"::warning::GitHub Pages ({action}) : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

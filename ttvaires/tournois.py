"""Tournois de tennis de table autour de Vaires (à venir) : étape 1, ce que l'API de la FFTT en donne.

La liste officielle des tournois est celle de la FFTT (monclub.fftt.com, « Liste des tournois »), une
application web qui la charge depuis un service de la FFTT. L'API de la FFTT n'a pas d'adresse
publique « tournaments » et sa documentation demande une connexion : cette vérification, faite pendant
une mise à jour avec le compte licencié de l'outil, lit la liste des ressources de l'API et sa
documentation OpenAPI, signale celles qui parlent de tournois (et leurs filtres), puis en lit un petit
échantillon. Quelques requêtes en tout, en lecture seule ; aucune protection n'est contournée.

    python -m ttvaires.tournois --verification
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from . import compte_fftt
from .fftt import API, ENTETES
from .reseau import JOUR, Client, ErreurReseau

RACINE = Path(__file__).resolve().parent.parent
CACHE = RACINE / "cache"
# Seine-et-Marne et les départements qui la touchent (Paris, Hauts-de-Seine, Yvelines : non limitrophes)
DEPARTEMENTS = ["77", "02", "10", "45", "51", "60", "89", "91", "93", "94", "95"]
MOTS = ("tourn",)  # tournament, tournoi...
MAX_ESSAIS = 3  # collections lues pour l'échantillon


def _json(texte):
    return texte.lstrip().startswith("{")


def _lire(client, chemin):
    return json.loads(client.get(chemin, ttl=JOUR, entetes=ENTETES, valide=_json))


def ressources(entree):
    """Collections de l'API d'après son point d'entrée : {nom: adresse}."""
    return {k: v for k, v in entree.items() if not k.startswith("@") and isinstance(v, str) and v.startswith("/api/")}


def chemins_tournois(openapi):
    """Chemins de la documentation OpenAPI qui parlent de tournois : {chemin: [filtres de la lecture]}."""
    sortie = {}
    for chemin, operations in (openapi.get("paths") or {}).items():
        lecture = (operations or {}).get("get") or {}
        texte = (chemin + " " + json.dumps(lecture.get("tags") or []) + " " + (lecture.get("summary") or "")).lower()
        if any(m in texte for m in MOTS):
            sortie[chemin] = [p.get("name") for p in lecture.get("parameters") or [] if p.get("in") == "query"]
    return sortie


def _resume_element(e):
    """Clés d'un élément et quelques valeurs courtes (nom, dates, lieu) pour juger de son intérêt."""
    valeurs = {k: v for k, v in e.items() if isinstance(v, (str, int, float)) and not k.startswith("@")
               and len(str(v)) <= 80}
    return {"cles": sorted(k for k in e if not k.startswith("@")), "exemple": dict(list(valeurs.items())[:12])}


def verification(client):
    print("Tournois : ce que l'API de la FFTT en donne (vérification, quelques requêtes)", flush=True)
    collections = {}
    try:
        collections = ressources(_lire(client, API))
        print(f"  {len(collections)} collections dans le point d'entrée de l'API")
    except (ErreurReseau, ValueError) as e:
        print(f"  ! point d'entrée illisible : {e}")
    retenues = {k: v for k, v in collections.items() if any(m in k.lower() for m in MOTS)}
    print("  Collections « tournois » : " + (", ".join(f"{k} -> {v}" for k, v in retenues.items()) or "aucune"))
    filtres = {}
    for doc in ("/docs.json", "/docs.jsonopenapi"):
        try:
            filtres = chemins_tournois(_lire(client, API + doc))
            print(f"  Documentation OpenAPI ({doc}) : {len(filtres)} chemin(s) « tournois »")
            for chemin, params in filtres.items():
                print(f"    {chemin} : filtres {', '.join(params) or 'aucun'}")
            break
        except (ErreurReseau, ValueError) as e:
            print(f"  ! documentation {doc} illisible : {e}")
    # Échantillon : les collections « tournois » (point d'entrée, puis documentation), sans paramètre de chemin
    a_lire = [c if c.startswith("/api") else "/api" + c for c in [*retenues.values(), *(c for c in filtres if "{" not in c)]]
    for chemin in list(dict.fromkeys(a_lire))[:MAX_ESSAIS]:
        url = f"{API.removesuffix('/api')}{chemin}?itemsPerPage=2"
        try:
            d = _lire(client, url)
        except (ErreurReseau, ValueError) as e:
            print(f"  ! {chemin} : {e}")
            continue
        elements = d.get("hydra:member") or d.get("member") or []
        print(f"  {chemin} : {d.get('hydra:totalItems', d.get('totalItems', '?'))} élément(s)")
        if elements:
            print("    " + json.dumps(_resume_element(elements[0]), ensure_ascii=False)[:1500])
    print(f"  Départements retenus pour la suite : {', '.join(DEPARTEMENTS)} (au {date.today():%d/%m/%Y})")


def main(arguments=None):
    p = argparse.ArgumentParser(prog="python -m ttvaires.tournois", description="Tournois autour de Vaires")
    p.add_argument("--verification", action="store_true", help="ce que l'API de la FFTT donne sur les tournois")
    args = p.parse_args(arguments)
    if not args.verification:
        p.print_help()
        return 0
    client = Client(CACHE)
    compte_fftt.connecter(client, demander=False)
    try:
        verification(client)
    except Exception as e:  # noqa: BLE001 - une vérification ne doit jamais faire échouer la mise à jour
        print(f"::warning::Tournois (vérification) : {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

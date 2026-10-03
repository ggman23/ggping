"""Accès en lecture à l'API publique de la FFTT (apiv2.fftt.com).

C'est l'API qu'utilisent les pages publiques de consultation des championnats sur
monclub.fftt.com : rencontres, feuilles de match et parties sont lisibles sans identifiant.
"""

import json
import re
from urllib.parse import quote

from .reseau import JOUR

API = "https://apiv2.fftt.com/api"
ENTETES = {"Accept": "application/ld+json", "X-Requested-With": None, "Referer": None}
# Identifiant interne de l'API pour les clubs connus (numéro FFTT -> identifiant).
IDS_CLUBS = {"08770250": 12770250}
CHAMPIONNAT_PAR_EQUIPES = "Championnat de France par Equipes"


def json_valide(texte):
    return texte.lstrip().startswith("{") and '"@context"' in texte[:300]


def lire(client, chemin, ttl=JOUR):
    return json.loads(client.get(API + chemin, ttl=ttl, entetes=ENTETES, valide=json_valide))


def lire_tout(client, chemin, ttl=JOUR):
    """Tous les éléments d'une liste paginée."""
    elements, page = [], chemin
    while page:
        d = lire(client, page, ttl)
        elements += d.get("hydra:member", [])
        suivante = d.get("hydra:view", {}).get("hydra:next")
        page = suivante[len("/api"):] if suivante else None
    return elements


def _q(cle):
    return quote(cle, safe="")


def id_interne_club(client, numero, debut_saison):
    """Identifiant interne d'un club. Le répertoire des clubs n'est pas public : on cherche le
    club parmi les rencontres de la 1re journée de son comité départemental."""
    if numero in IDS_CLUBS:
        return IDS_CLUBS[numero]
    comite = f"D{numero[2:4]}"
    rencontres = lire_tout(client, f"/sport_matches?{_q('division.organization.identifier')}={comite}"
                                   f"&{_q('day.position')}=1&{_q('date[after]')}={debut_saison}&itemsPerPage=200", 30 * JOUR)
    for r in rencontres:
        for cote in ("homeOpponent", "awayOpponent"):
            for club in ((r.get(cote) or {}).get("team") or {}).get("clubs", []):
                if club.get("identifier") == numero:
                    return club["id"]
    raise ValueError(f"club {numero} introuvable dans l'API FFTT")


def rencontres_club(client, id_club, debut, fin, ttl):
    """Rencontres de championnat par équipes d'un club entre deux dates (sans le détail)."""
    filtre = (f"{_q('or[homeOpponent.team.clubs.id]')}={id_club}&{_q('or[awayOpponent.team.clubs.id]')}={id_club}"
              f"&{_q('date[after]')}={debut}&{_q('date[before]')}={fin}&{_q('order[date]')}=asc&itemsPerPage=100")
    return [r for r in lire_tout(client, f"/sport_matches?{filtre}", ttl)
            if CHAMPIONNAT_PAR_EQUIPES in r["division"].get("contest", {}).get("name", "")]


def feminin(rencontre):
    nom = rencontre["division"].get("contest", {}).get("name", "")
    return bool(re.search(r"F[ée]minin", nom))


def numero_equipe(nom):
    m = re.search(r"(\d+)\s*$", nom or "")
    return int(m[1]) if m else None


def joueur(licence):
    personne = licence.get("person") or {}
    return {
        "licence": licence.get("identifier"),
        "nom": f"{personne.get('familyName', '')} {personne.get('givenName', '')}".strip(),
        "points": licence.get("points"),
    }

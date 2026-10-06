"""Accès en lecture à l'API publique de la FFTT (apiv2.fftt.com).

C'est l'API qu'utilisent les pages publiques de consultation des championnats sur
monclub.fftt.com : poules, rencontres, feuilles de match, compétitions et parties de chaque
joueur (toutes compétitions) sont lisibles sans identifiant. Les listes de licenciés d'un club,
elles, ne le sont pas.
"""

import json
import re
from datetime import date
from urllib.parse import quote

from .reseau import JOUR

API = "https://apiv2.fftt.com/api"
ENTETES = {"Accept": "application/ld+json", "X-Requested-With": None, "Referer": None}
# Identifiant interne de l'API pour les clubs connus (numéro FFTT -> identifiant).
IDS_CLUBS = {"08770250": 12770250}
CHAMPIONNAT_PAR_EQUIPES = "Championnat de France par Equipes"
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# ---------------------------------------------------------------------------
# Saison, phase, libellés
# ---------------------------------------------------------------------------

def phase_et_saison(jour):
    debut = jour.year if jour.month >= 7 else jour.year - 1
    return (1 if jour.month >= 7 else 2), f"{debut}-{debut + 1}"


def bornes_phase(jour):
    """Dates de début et de fin de la phase en cours."""
    phase, saison = phase_et_saison(jour)
    annee = int(saison[:4])
    return ("%d-07-01" % annee, "%d-12-31" % annee) if phase == 1 else ("%d-01-01" % (annee + 1), "%d-06-30" % (annee + 1))


def libelle_division(txt):
    """Rend lisibles les codes de division FFTT ('L08_R2' -> 'Régionale 2', 'DEP 3 Ph1' -> 'Départementale 3')."""
    txt = " ".join((txt or "").replace("FED_", "").split())
    txt = re.sub(r"\s+Ph\s*\d$", "", txt)
    txt = re.sub(r"^L\d+_R(\d+)", r"Régionale \1", txt)
    txt = re.sub(r"^PRE-REG\b", "Pré-régionale", txt)
    txt = re.sub(r"^DEP (\d+)", r"Départementale \1", txt)
    return txt


def jour_habituel(dates):
    jours = [date.fromisoformat(d).weekday() for d in dates if d]
    return JOURS[max(set(jours), key=jours.count)] if jours else None


def numero_equipe(nom):
    m = re.search(r"(\d+)\s*$", nom or "")
    return int(m[1]) if m else None


# ---------------------------------------------------------------------------
# Lecture de l'API
# ---------------------------------------------------------------------------

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
            for club in equipe(r, cote).get("clubs", []):
                if club.get("identifier") == numero:
                    return club["id"]
    raise ValueError(f"club {numero} introuvable dans l'API FFTT")


def rencontres_club(client, id_club, debut, fin, ttl):
    """Rencontres de championnat par équipes d'un club entre deux dates (sans le détail)."""
    filtre = (f"{_q('or[homeOpponent.team.clubs.id]')}={id_club}&{_q('or[awayOpponent.team.clubs.id]')}={id_club}"
              f"&{_q('date[after]')}={debut}&{_q('date[before]')}={fin}&{_q('order[date]')}=asc&itemsPerPage=100")
    return [r for r in lire_tout(client, f"/sport_matches?{filtre}", ttl) if championnat_par_equipes(r)]


def rencontres_poule(client, id_poule, ttl):
    return lire_tout(client, f"/sport_matches?{_q('pool.id')}={id_poule}&itemsPerPage=100", ttl)


def details(client, rencontres, aujourdhui):
    """Détail (score, joueurs, parties) des rencontres déjà jouées : {id: détail}.

    Les détails complets sont gardés en cache indéfiniment ; une rencontre dont le résultat
    n'est pas encore saisi est retentée au lancement suivant.
    """
    jouees = {r["id"] for r in rencontres if r["date"][:10] <= aujourdhui
              and r.get("homeOpponent") and r.get("awayOpponent")}
    chemins = {i: f"{API}/sport_matches/{i}" for i in sorted(jouees)}
    pages = client.get_plusieurs(list(chemins.values()), ttl=None, message="feuilles de match",
                                 entetes=ENTETES, valide=json_valide)
    resultat = {}
    for i, chemin in chemins.items():
        d = json.loads(pages[chemin]) if pages.get(chemin) else {}
        if d.get("homeGamePoints") is None or not d.get("homeSheetMatches"):
            client.oublier(chemin)
            continue
        resultat[i] = d
    return resultat


# ---------------------------------------------------------------------------
# Lecture des objets de l'API
# ---------------------------------------------------------------------------

def championnat_par_equipes(rencontre):
    return CHAMPIONNAT_PAR_EQUIPES in rencontre["division"].get("contest", {}).get("name", "")


def feminin(rencontre):
    nom = rencontre["division"].get("contest", {}).get("name", "")
    return bool(re.search(r"F[ée]minin", nom))


def equipe(rencontre, cote):
    return (rencontre.get(cote) or {}).get("team") or {}


def club_de(equipe_api):
    """(numéro FFTT, identifiant interne, nom) du club d'une équipe."""
    clubs = equipe_api.get("clubs") or [{}]
    return clubs[0].get("identifier"), clubs[0].get("id"), clubs[0].get("name")


def joueur(licence):
    personne = licence.get("person") or {}
    return {
        "licence": licence.get("identifier"),
        "nom": f"{personne.get('familyName', '')} {personne.get('givenName', '')}".strip(),
        "nom_famille": personne.get("familyName", ""), "prenom": personne.get("givenName", ""),
        "points": licence.get("points"),
    }


def heure(rencontre):
    h = (rencontre.get("time") or "")[11:16]
    return h or None

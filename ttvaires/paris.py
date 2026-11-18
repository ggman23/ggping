"""Championnat de Paris IDF 2026-2027 : les trois équipes de Vaires, leurs poules et leur calendrier.

Recopiés des documents de la ligue (« 2026-2027 - Ch. de Paris - Poules HO / PH / D2 », PDF fournis
le 18/11/2026) : Vaires 1 en Honneur poule 1, Vaires 2 en Promotion d'Honneur poule 2, Vaires 3 en
Division 2 poule 3. Sept journées, le vendredi, sur toute la saison (la journée 1 en phase 1, les
autres en phase 2). La grille des rencontres est la même pour toutes les poules : « 1/8 » veut dire
que l'équipe placée en 1 reçoit celle placée en 8 (le premier nommé reçoit).

Page /paris/ (mot de passe du club) : faite par la mise à jour (étape adversaires, paris_vaires.html,
publiée comme /77/), avec la présentation de la page adversaires du championnat de France
(gabarit_paris.html, calqué sur gabarit.html) : récapitulatif par semaine, un onglet par équipe
(calendrier, lieu et adresse de la salle, classement de la poule, adversaires) et la fiche de chaque club
adverse. L'API de la FFTT n'a pas les rencontres du championnat de Paris (contrôle du 18/11/2026,
diagnostic_api) : ni résultats ni compositions de Paris, donc pas de score, un classement vide et pas de
brûlage. Pour chaque club adverse, comme pour le championnat de France (adversaires.recuperer_paris) :
ses joueurs, leurs points, leur meilleur classement, leur forme (victoires, défaites, points gagnés depuis
le début de la phase) et l'équipe où chacun joue en championnat de France.
"""

import json
from collections import Counter
from pathlib import Path

GABARIT = Path(__file__).with_name("gabarit_paris.html")
SAISON = "2026-2027"
SOURCE = "Poules et calendrier du championnat de Paris IDF 2026-2027 (documents de la ligue Paris Île-de-France)"

JOURNEES = ["2026-11-27", "2027-01-08", "2027-02-05", "2027-03-19", "2027-04-02", "2027-05-14", "2027-06-04"]
GRILLE = ["1/8 2/7 3/6 4/5", "7/1 6/2 5/3 8/4", "1/6 2/5 3/4 8/7", "5/1 4/2 3/8 6/7",
          "1/4 2/3 7/5 8/6", "3/1 2/8 4/7 5/6", "1/2 7/3 6/4 8/5"]
CLUB_VAIRES = "08770250"

# Équipes de chaque poule, dans l'ordre des documents (position 1 à 8) : (numéro du club, nom, équipe, département)
EQUIPES = [
    {"cle": "v1", "nom": "Vaires 1", "division": "Honneur", "code": "HO", "poule": 1, "equipes": [
        ("08770250", "VAIRES CTT", 1, "77"), ("08930928", "NEUILLY S/MARNE TT", 2, "93"),
        ("08940096", "VINCENNOIS TT", 2, "94"), ("08931057", "DRANCY JA", 1, "93"),
        ("08771394", "LA COMPANAISE", 1, "77"), ("08930610", "NOISY LE GRAND", 1, "93"),
        ("08940524", "NOGENT TT", 1, "94"), ("08930113", "VILLEMOMBLE SP", 2, "93")]},
    {"cle": "v2", "nom": "Vaires 2", "division": "Promotion d'Honneur", "code": "PH", "poule": 2, "equipes": [
        ("08771394", "LA COMPANAISE", 2, "77"), ("08930430", "LIVRY-GARGAN EP", 4, "93"),
        ("08930452", "PAVILLONNAIS SE", 1, "93"), ("08930113", "VILLEMOMBLE SP", 3, "93"),
        ("08770250", "VAIRES CTT", 2, "77"), ("08771521", "CRECY AP", 1, "77"),
        ("08930059", "AULNAYSIENS AP", 1, "93"), ("08770937", "DAMMARTIN CTT", 2, "77")]},
    {"cle": "v3", "nom": "Vaires 3", "division": "Division 2", "code": "D2", "poule": 3, "equipes": [
        ("08771398", "BUSSY ST-GEORGES CTT", 4, "77"), ("08930430", "LIVRY-GARGAN EP", 6, "93"),
        ("08931320", "LES LILAS TT", 3, "93"), ("08771201", "MONTHYON CTT", 1, "77"),
        ("08770250", "VAIRES CVTT", 3, "77"), ("08771085", "ST-JEAN TT", 2, "77"),
        ("08940073", "FONTENAYSIENNE US TT", 1, "94"), ("08770937", "DAMMARTIN CTT", 4, "77")]},
]


def rencontres_de_la_poule():
    """[(journée, date, position qui reçoit, position reçue)] : la grille, la même pour toutes les poules."""
    return [(j, JOURNEES[j - 1], int(a), int(b))
            for j, ligne in enumerate(GRILLE, 1) for a, b in (paire.split("/") for paire in ligne.split())]


def _equipe(position, club, nom, numero, dep):
    return {"position": position, "club": club, "nom": f"{nom} {numero}", "numero": numero, "dep": dep,
            "vaires": club == CLUB_VAIRES}


# Champs gardés pour chaque joueur adverse (la page n'a aucun numéro de licence : voir clubs_adverses)
CHAMPS_JOUEUR = ("nom", "prenom", "sexe", "categorie", "categorie_long", "classement", "points", "points_mensuels",
                 "meilleur", "renouvele", "nouveau")


def clubs_adverses(adversaires):
    """Clubs adverses pour la page (adversaires.recuperer_paris), au format de la page adversaires du
    championnat de France : salle, joueurs (points, meilleur classement, forme) et équipes du championnat
    de France avec qui y a joué. Les numéros de licence sont remplacés par des repères (j1, j2...)."""
    res = {}
    for num, c in (adversaires or {}).get("clubs", {}).items():
        reperes = {}
        repere = lambda lic: reperes.setdefault(lic, f"j{len(reperes) + 1}")
        joueurs = []
        for j in c.get("joueurs", []):
            x = {"id": repere(j["id"]), **{k: j.get(k) for k in CHAMPS_JOUEUR}}
            if "forme" in j:  # absent : joueur non suivi ; None : parties non lues
                x["forme"] = j["forme"]
            joueurs.append(x)
        equipes = [{"libelle": e.get("libelle"), "numero": e.get("numero"), "championnat": e.get("championnat"),
                    "division": e.get("division"),
                    "compositions": [{"journee": co.get("journee"), "date": co.get("date"),
                                      "joueurs": [repere(i) for i in co.get("joueurs", [])]} for co in e.get("compositions", [])]}
                   for e in c.get("equipes", [])]
        res[num] = {"numero": num, "nom": c.get("nom"), "salle": c.get("salle"), "joueurs": joueurs, "equipes": equipes,
                    "effectif_complet": bool(c.get("effectif_complet")), "date_effectif": c.get("date_effectif"),
                    "reference_nouveaux": c.get("reference_nouveaux"), "erreur": c.get("erreur")}
    return res


def _rencontres(poule, nous):
    """Les sept rencontres d'une équipe de Vaires, au format de la page adversaires."""
    par_position = {p["position"]: p for p in poule}
    res = []
    for j, jour, a, b in rencontres_de_la_poule():
        if nous["position"] not in (a, b):
            continue
        dom, ext = par_position[a], par_position[b]
        adv = ext if dom is nous else dom
        res.append({"journee": j, "date": jour, "date_reelle": None, "heure": None,
                    "domicile": {"libelle": dom["nom"], "club": dom["club"]},
                    "exterieur": {"libelle": ext["nom"], "club": ext["club"]},
                    "vaires_domicile": dom is nous, "score": None,
                    "adversaire": {"club": adv["club"], "libelle": adv["nom"], "numero": adv["numero"]}})
    return res


def donnees(adversaires=None):
    """Données de la page /paris/, au format de la page adversaires du championnat de France : les trois
    équipes de Vaires (calendrier, lieu, classement de la poule) et, avec `adversaires`
    (adversaires.recuperer_paris), les clubs adverses et leurs joueurs. Les résultats du championnat de
    Paris ne sont pas dans l'API de la FFTT : pas de score, classement vide."""
    adv = adversaires or {}
    equipes = []
    for e in EQUIPES:
        poule = [_equipe(i, *t) for i, t in enumerate(e["equipes"], 1)]
        nous = next(p for p in poule if p["vaires"])
        equipes.append({
            "id": e["cle"], "libelle": nous["nom"], "nom_court": e["nom"], "numero": nous["numero"], "championnat": "M",
            "division": e["division"], "code": e["code"], "poule": f"Poule {e['poule']}", "position": nous["position"],
            "jour": "vendredi", "rencontres": _rencontres(poule, nous),
            "classement": [{"rang": None, "libelle": p["nom"], "club": p["club"], "dep": p["dep"], "position": p["position"],
                            "points": None, "joues": None, "v": None, "n": None, "d": None} for p in poule]})
    club = adv.get("club") or {}
    sources = adv.get("sources", {})
    return {"saison": SAISON, "source": SOURCE, "phase": adv.get("phase"),
            "journees": [{"numero": i, "date": d} for i, d in enumerate(JOURNEES, 1)],
            "club": {"numero": CLUB_VAIRES, "nom": "CVTT Vaires", "salle": club.get("salle")},
            "equipes": equipes, "clubs": clubs_adverses(adv), "genere_le": adv.get("genere_le"),
            "debut_forme": (sources.get("forme") or {}).get("debut"), "historiques_restants": sources.get("historiques_restants", 0)}


def page(adversaires=None):
    """Page /paris/ (HTML) : le gabarit avec les données."""
    js = json.dumps(donnees(adversaires), ensure_ascii=False).replace("<", "\\u003c")
    return GABARIT.read_text(encoding="utf-8").replace("__DONNEES_JSON__", js).encode("utf-8")


def diagnostic_api(client, numero_club, aujourdhui):
    """Le championnat de Paris est-il dans l'API de la FFTT ? Écrit dans le journal, en chiffres et noms de
    compétitions, divisions, poules et équipes seulement (aucun nom de joueur) : les compétitions par
    équipes du club sur toute la saison. Renvoie {nom de compétition: nombre de rencontres}."""
    from . import fftt
    from .reseau import HEURE

    annee = aujourdhui.year if aujourdhui.month >= 7 else aujourdhui.year - 1
    debut, fin = f"{annee}-07-01", f"{annee + 1}-06-30"
    id_club = fftt.id_interne_club(client, numero_club, debut)
    q = fftt._q
    filtre = (f"{q('or[homeOpponent.team.clubs.id]')}={id_club}&{q('or[awayOpponent.team.clubs.id]')}={id_club}"
              f"&{q('date[after]')}={debut}&{q('date[before]')}={fin}&{q('order[date]')}=asc&itemsPerPage=100")
    rencontres = fftt.lire_tout(client, f"/sport_matches?{filtre}", 6 * HEURE)
    par_competition = Counter((r.get("division") or {}).get("contest", {}).get("name") or "?" for r in rencontres)
    print(f"--- Championnat de Paris dans l'API FFTT ? Compétitions par équipes du club ({debut} au {fin}) ---", flush=True)
    for nom, n in par_competition.most_common():
        print(f"  {nom} : {n} rencontres", flush=True)
    paris = [r for r in rencontres if "paris" in ((r.get("division") or {}).get("contest", {}).get("name") or "").lower()]
    if not paris:
        print("  championnat de Paris : aucune rencontre dans l'API pour ce club (pas encore saisies, ou pas dans l'API)", flush=True)
    vues = Counter()
    for r in paris:
        nos = [fftt.equipe(r, c).get("name") for c in ("homeOpponent", "awayOpponent")
               if fftt.club_de(fftt.equipe(r, c))[0] == numero_club]
        vues[(r["division"].get("name"), (r.get("pool") or {}).get("id"), tuple(nos))] += 1
    for (division, poule, nos), n in sorted(vues.items(), key=lambda x: str(x[0])):
        print(f"  Paris : division « {division} », poule {poule}, équipe(s) {', '.join(filter(None, nos))} : {n} rencontres", flush=True)
    if paris:
        jours = sorted({(r.get("day") or {}).get("position") for r in paris} - {None})
        dates = sorted({(r.get("date") or "")[:10] for r in paris})
        print(f"  Paris : journées {jours}, dates {dates[:8]}", flush=True)
    return dict(par_competition)

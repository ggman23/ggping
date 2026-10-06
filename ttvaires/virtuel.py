"""Classement virtuel des joueurs du club, toutes compétitions confondues (page « Classement virtuel »).

Points virtuels = points officiels de la phase + points gagnés ou perdus depuis le début de la
phase dans toutes les compétitions : championnat par équipes, critérium fédéral, tournois,
compétitions jeunes...

- Joueurs : liste des licenciés du club (pingpocket.fr ou dossier import), complétée par les
  joueurs alignés en championnat (feuilles de match).
- Parties : API publique de la FFTT. Chaque partie de simple donne les deux joueurs avec leurs
  points officiels de la phase, et sa compétition, qui porte son coefficient (1 pour le
  championnat par équipes, 1,5 pour le critérium fédéral, 0,5 pour un tournoi départemental...).
- Points d'une partie : barème FFTT × coefficient de la compétition. Les doubles, les parties
  gagnées par forfait et les parties marquées « non comptées » ne rapportent rien.
"""

import json
import re
from collections import Counter
from datetime import date, datetime

from . import fftt
from .effectif import feuilles_du_club, liste_licencies
from .fftt import API, ENTETES, _q, json_valide
from .reseau import HEURE, JOUR
from .resultats import points_partie


def url_parties(licence):
    """Parties de la saison en cours d'un joueur (simples et doubles, toutes compétitions)."""
    return (f"{API}/games?{_q('players.licence.identifier')}={licence}&{_q('contest.season.current')}=true"
            f"&{_q('order[date]')}=asc&itemsPerPage=200")


def classement(points):
    return max(5, int(points // 100)) if points is not None else None


def libelle_competition(nom):
    """'FED_Championnat de France par Equipes Masculin' -> 'Championnat par équipes M'."""
    nom = " ".join((nom or "").replace("FED_", "").split()) or "Compétition"
    m = re.fullmatch(r"Championnat de France par Equipes (M|F)\w*", nom)
    return f"Championnat par équipes {m[1]}" if m else nom


def est_championnat(nom):
    return fftt.CHAMPIONNAT_PAR_EQUIPES in (nom or "")


def _simple(partie):
    return not (partie.get("doubleOpposition") or partie.get("homeTeammatePlayer") or partie.get("awayTeammatePlayer"))


def _lire_parties(client, licences):
    """{licence: [parties de la saison]} (None si l'API n'a pas répondu pour ce joueur)."""
    urls = {lic: url_parties(lic) for lic in licences}
    pages = client.get_plusieurs(list(urls.values()), ttl=HEURE, message="parties des joueurs",
                                 entetes=ENTETES, valide=json_valide)
    res = {}
    for lic, url in urls.items():
        if not pages.get(url):
            res[lic] = None
            continue
        d = json.loads(pages[url])
        parties = d.get("hydra:member", [])
        suivante = d.get("hydra:view", {}).get("hydra:next")
        if suivante:
            parties += fftt.lire_tout(client, suivante[len("/api"):], ttl=HEURE)
        res[lic] = parties
    return res


def _competitions(client, ids):
    """{id de compétition: {nom, coef}} : le coefficient est donné par la FFTT pour chaque compétition."""
    urls = {i: f"{API}/contests/{i}" for i in sorted(ids)}
    pages = client.get_plusieurs(list(urls.values()), ttl=30 * JOUR, message="compétitions", entetes=ENTETES, valide=json_valide)
    res = {}
    for i, url in urls.items():
        d = json.loads(pages[url]) if pages.get(url) else {}
        res[i] = {"nom": d.get("name"), "coef": d.get("coefficient")}
    return res


def _etats(client, parties, detail_rencontres):
    """{id de partie: {non_comptee, forfait, division}}.

    Les parties du championnat par équipes du club sont dans les feuilles de match déjà lues ;
    pour les autres (compétitions individuelles...), le détail de chaque partie est lu une fois
    puis gardé en cache.
    """
    etats = {}
    for d in detail_rencontres.values():
        division = fftt.libelle_division((d.get("division") or {}).get("name"))
        for g in d.get("games") or []:
            etats[g.get("id")] = {"non_comptee": bool(g.get("notCounted")), "forfait": bool(g.get("forfeit")),
                                  "division": division}
    manquantes = sorted({p["id"] for p in parties if p["id"] not in etats})
    urls = {i: f"{API}/games/{i}" for i in manquantes}
    pages = client.get_plusieurs(list(urls.values()), ttl=None, message="détail des parties", entetes=ENTETES, valide=json_valide)
    for i, url in urls.items():
        if not pages.get(url):
            continue
        g = json.loads(pages[url])
        sm = g.get("sportMatch") or {}
        division = ((sm.get("tour") or {}).get("division") or sm.get("division") or {}).get("name")
        etats[i] = {"non_comptee": bool(g.get("notCounted")), "forfait": bool(g.get("forfeit")),
                    "division": fftt.libelle_division(division) if division else None}
    return etats


def analyser(licence, parties, competitions, etats, debut, fin):
    """Parties de simple d'un joueur pendant la phase et points gagnés ou perdus sur chacune.

    Renvoie (parties retenues, points officiels lus sur les parties, parties écartées par motif).
    """
    lignes, ecartees, officiels = [], Counter(), Counter()
    for g in parties:
        jour = (g.get("date") or "")[:10]
        h, a = g.get("homePlayer") or {}, g.get("awayPlayer") or {}
        if h.get("identifier") == licence:
            moi, adv, cote = h, a, "home"
        elif a.get("identifier") == licence:
            moi, adv, cote = a, h, "away"
        else:
            continue  # double où il est partenaire
        if not (debut <= jour <= fin) or not _simple(g):
            continue
        if moi.get("points"):
            officiels[moi["points"]] += 1
        etat = etats.get(g["id"], {})
        comp = competitions.get((g.get("contest") or {}).get("id"), {})
        nom = comp.get("nom") or (g.get("contest") or {}).get("name")
        if not g.get("winner") or not adv.get("identifier") or etat.get("forfait"):
            ecartees["forfait"] += 1
        elif etat.get("non_comptee"):
            ecartees["non comptée"] += 1
        elif moi.get("points") is None or adv.get("points") is None:
            ecartees["points inconnus"] += 1
        elif comp.get("coef") is None:
            ecartees["coefficient inconnu"] += 1
        else:
            victoire = g["winner"] == cote
            adversaire = fftt.joueur(adv)
            lignes.append({
                "id": g["id"], "date": jour, "competition": libelle_competition(nom), "division": etat.get("division"),
                "championnat": est_championnat(nom), "coef": comp["coef"],
                "adversaire": adversaire["nom"], "adv_points": adv["points"], "victoire": victoire,
                "points": round(points_partie(moi["points"], adv["points"], victoire, comp["coef"]), 3),
            })
    lignes.sort(key=lambda l: (l["date"], l["id"]))
    return lignes, officiels, ecartees


def recuperer_virtuel(client, numero_club="08770250", aujourdhui=None, dossier_import=None):
    aujourdhui = aujourdhui or date.today()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)

    print(f"1/3 Équipes et feuilles de match du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
    feuilles = feuilles_du_club(client, numero_club, aujourdhui)
    print("2/3 Licenciés du club (pingpocket.fr ou dossier import)", flush=True)
    liste, source = liste_licencies(client, numero_club, dossier_import)

    joueurs = {j["id"]: j for j in liste if j["renouvele"] and not j["loisir"]}
    for lic, vu in feuilles["vus"].items():  # un joueur aligné est forcément réinscrit
        j = joueurs.setdefault(lic, dict(vu))
        j["points"] = vu["points"] or j.get("points")
        j["sexe"] = j.get("sexe") or vu["sexe"]
    for lic, j in joueurs.items():
        equipes = Counter((p["championnat"], p["numero"]) for p in feuilles["parts"].get(lic, []))
        if equipes:
            (ch, n), _ = max(equipes.items(), key=lambda e: (e[1], e[0][0] == "M", -e[0][1]))
            j["equipe"] = f"V{n}" + (" F" if ch == "F" else "")

    print(f"3/3 Parties de toutes les compétitions : {len(joueurs)} joueurs (API FFTT)", flush=True)
    toutes = _lire_parties(client, sorted(joueurs))
    du_club = [p for ps in toutes.values() if ps for p in ps
               if debut <= (p.get("date") or "")[:10] <= fin and _simple(p)]
    competitions = _competitions(client, {(p.get("contest") or {}).get("id") for p in du_club} - {None})
    etats = _etats(client, du_club, feuilles["detail"])

    resultat, sans_reponse = [], 0
    for lic, j in joueurs.items():
        parties = toutes.get(lic)
        sans_reponse += parties is None
        lignes, officiels, ecartees = analyser(lic, parties or [], competitions, etats, debut, fin)
        off = officiels.most_common(1)[0][0] if officiels else (j.get("points") or j.get("points_mensuels"))
        championnat = round(sum(l["points"] for l in lignes if l["championnat"]), 3)
        autres = round(sum(l["points"] for l in lignes if not l["championnat"]), 3)
        total = round(championnat + autres, 3)
        virtuels = round(off + total, 3) if off else None
        resultat.append({
            "id": lic, "nom": j.get("nom"), "prenom": j.get("prenom"), "sexe": j.get("sexe"),
            "categorie": j.get("categorie"), "equipe": j.get("equipe"), "nouveau": j.get("nouveau", False),
            "officiels": off, "classement": classement(off), "championnat": championnat, "autres": autres,
            "total": total, "virtuels": virtuels, "classement_virtuel": classement(virtuels),
            "v": sum(l["victoire"] for l in lignes), "d": sum(not l["victoire"] for l in lignes),
            "parties": lignes, "ecartees": dict(ecartees), "inconnu": parties is None,
        })
    if sans_reponse:
        print(f"  ! parties non lues pour {sans_reponse} joueur(s) : l'API FFTT n'a pas répondu, relancer plus tard.")
    resultat.sort(key=lambda j: (j["virtuels"] is None, -(j["virtuels"] or 0), j["nom"] or ""))

    comps = Counter()
    for j in resultat:
        for l in j["parties"]:
            comps[(l["competition"], l["coef"], l["championnat"])] += 1
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "debut": debut, "club": {"numero": numero_club, "nom": feuilles["nom_club"]}, "source": source,
        "competitions": [{"nom": n, "coef": c, "championnat": ch, "parties": nb}
                         for (n, c, ch), nb in sorted(comps.items(), key=lambda x: (not x[0][2], -x[1]))],
        "joueurs": resultat,
    }

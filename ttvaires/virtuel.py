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
import time
import unicodedata
from collections import Counter
from datetime import date, datetime

from . import fftt, pingpocket
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


def _lire_parties(client, licences, ttl=HEURE, message="parties des joueurs"):
    """{licence: [parties de la saison]} (None si l'API n'a pas répondu pour ce joueur)."""
    urls = {lic: url_parties(lic) for lic in licences}
    pages = client.get_plusieurs(list(urls.values()), ttl=ttl, message=message,
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
            parties += fftt.lire_tout(client, suivante[len("/api"):], ttl=ttl)
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


def _manches(partie):
    """Manches d'une partie telles que l'API les donne : [[points « home », points « away »], ...] dans
    l'ordre joué ; None si elles n'ont pas été saisies (ou si la réponse ne les contient pas)."""
    manches = [[m.get("homeScore"), m.get("awayScore")] for m in partie.get("sets") or [] if isinstance(m, dict)]
    manches = [m for m in manches if isinstance(m[0], int) and isinstance(m[1], int) and m[0] != m[1]]
    return manches or None


def etats_des_feuilles(detail_rencontres):
    """{id de partie: {non_comptee, forfait, abandon, division, manches}} d'après les feuilles de match déjà lues."""
    etats = {}
    for d in detail_rencontres.values():
        division = fftt.libelle_division((d.get("division") or {}).get("name"))
        for g in d.get("games") or []:
            etats[g.get("id")] = {"non_comptee": bool(g.get("notCounted")), "forfait": bool(g.get("forfeit")),
                                  "abandon": bool(g.get("abandonment")), "division": division, "manches": _manches(g)}
    return etats


def _etats(client, parties, detail_rencontres):
    """{id de partie: {non_comptee, forfait, abandon, division, manches}}.

    Les parties du championnat par équipes du club sont dans les feuilles de match déjà lues ;
    pour les autres (compétitions individuelles...), le détail de chaque partie est lu une fois
    puis gardé en cache.
    """
    etats = etats_des_feuilles(detail_rencontres)
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
                    "abandon": bool(g.get("abandonment")), "manches": _manches(g),
                    "division": fftt.libelle_division(division) if division else None}
    _signaler_manches_absentes(parties, [json.loads(pages[u]) for u in list(urls.values())[:1] if pages.get(u)],
                               [etats[i] for i in urls if i in etats])
    return etats


def _champs(objet):
    """Noms des champs d'une réponse de l'API (jamais leurs valeurs), avec la forme du champ « sets »."""
    sets = objet.get("sets", "absent")
    forme = (f"liste de {len(sets)} ({type(sets[0]).__name__})" if isinstance(sets, list) and sets
             else "liste vide" if isinstance(sets, list) else sets if sets == "absent" else type(sets).__name__)
    return f"{', '.join(sorted(objet))} ; sets : {forme}"


def _signaler_manches_absentes(parties, details, etats_lus):
    """Journal : si aucune partie hors championnat n'a ses manches, les champs que l'API donne pour une
    de ces parties (dans la liste et dans le détail), pour savoir si les manches existent sous un autre nom."""
    if not etats_lus or any(e.get("manches") for e in etats_lus):
        return
    hors = [p for p in parties if not est_championnat((p.get("contest") or {}).get("name"))]
    print(f"  ! manches absentes pour les {len(etats_lus)} parties lues hors feuilles de match (critérium, tournois...)")
    if hors:
        print(f"    champs d'une partie dans la liste : {_champs(hors[0])}"[:700])
    if details:
        print(f"    champs du détail d'une partie : {_champs(details[0])}"[:700])


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
            # Manches : dans la liste des parties si l'API les y donne, sinon dans le détail déjà lu
            # (feuille de match, ou détail de la partie) ; vues du joueur : ses points d'abord
            manches = _manches(g) or etat.get("manches")
            if manches and cote == "away":
                manches = [[b, a] for a, b in manches]
            lignes.append({
                "id": g["id"], "date": jour, "competition": libelle_competition(nom), "division": etat.get("division"),
                "championnat": est_championnat(nom), "coef": comp["coef"],
                "pts_joueur": moi["points"], "adversaire": adversaire["nom"], "adv_points": adv["points"],
                "ecart": adv["points"] - moi["points"], "victoire": victoire,
                "points": round(points_partie(moi["points"], adv["points"], victoire, comp["coef"]), 3),
                "manches": manches, "abandon": bool(g.get("abandonment") or etat.get("abandon")),
            })
    lignes.sort(key=lambda l: (l["date"], l["id"]))
    return lignes, officiels, ecartees


def famille_competition(competition, championnat=False):
    """Regroupement des compétitions pour la forme des adversaires : « Championnat », « Critérium
    fédéral », « Tournois » (chaque tournoi est une compétition à part), sinon le libellé (finales
    par classement, compétitions jeunes, vétérans...)."""
    if championnat:
        return "Championnat"
    simple = unicodedata.normalize("NFKD", competition or "").encode("ascii", "ignore").decode("ascii").lower()
    if "criterium" in simple:
        return "Critérium fédéral"
    if "tournoi" in simple:
        return "Tournois"
    return competition or "Autre compétition"


def resume_forme(lignes, officiels):
    """Résumé des parties retenues d'un joueur (voir analyser) : victoires, défaites, points gagnés
    ou perdus depuis le début de la phase, points virtuels, et le détail par famille de compétitions
    (championnat d'abord, puis par nombre de parties)."""
    familles = {}
    for l in lignes:
        f = familles.setdefault(famille_competition(l["competition"], l["championnat"]),
                                {"v": 0, "d": 0, "points": 0.0})
        f["v" if l["victoire"] else "d"] += 1
        f["points"] += l["points"]
    off = officiels.most_common(1)[0][0] if officiels else None
    total = round(sum(l["points"] for l in lignes), 1)
    return {
        "v": sum(l["victoire"] for l in lignes), "d": sum(not l["victoire"] for l in lignes), "points": total,
        "officiels": off, "virtuels": round(off + total, 1) if off else None,
        "derniere": lignes[-1]["date"] if lignes else None,
        "competitions": [{"nom": n, "v": f["v"], "d": f["d"], "points": round(f["points"], 1)}
                         for n, f in sorted(familles.items(), key=lambda x: (x[0] != "Championnat", -(x[1]["v"] + x[1]["d"]), x[0]))],
    }


def forme_joueurs(client, licences, detail_rencontres, debut, fin, ttl=JOUR):
    """Forme de joueurs d'autres clubs (page adversaires) : {licence: resume_forme(...), ou None si
    l'API n'a pas répondu pour ce joueur}. Même calcul que le classement virtuel, avec une économie :
    seules les feuilles de match déjà lues disent si une partie est non comptée ou perdue par forfait.
    Le détail des parties hors championnat n'est pas demandé (une requête par partie) : une partie de
    compétition individuelle abandonnée par forfait alors que les deux joueurs sont inscrits compterait
    (cas rare ; une partie sans adversaire, elle, est bien écartée)."""
    toutes = _lire_parties(client, sorted(licences), ttl=ttl, message="parties des joueurs adverses")
    simples = [p for ps in toutes.values() if ps for p in ps if debut <= (p.get("date") or "")[:10] <= fin and _simple(p)]
    competitions = _competitions(client, {(p.get("contest") or {}).get("id") for p in simples} - {None})
    etats = etats_des_feuilles(detail_rencontres)
    res = {}
    for lic, parties in toutes.items():
        if parties is None:
            res[lic] = None
            continue
        lignes, officiels, _ = analyser(lic, parties, competitions, etats, debut, fin)
        res[lic] = resume_forme(lignes, officiels)
        res[lic]["nom"] = _nom_du_joueur(lic, parties)
    return res


def _nom_du_joueur(licence, parties):
    """Nom de famille du joueur d'après ses parties (pour vérifier qu'une licence recopiée est la bonne)."""
    for g in parties:
        for cote in ("homePlayer", "awayPlayer"):
            j = g.get(cote) or {}
            if j.get("identifier") == licence:
                return ((j.get("person") or {}).get("familyName") or "").strip() or None
    return None


SITE_PINGPOCKET = "www.pingpocket.fr"
MAX_HISTORIQUES = 120  # historiques téléchargés au plus par lancement (une page toutes les 4 secondes : 8 minutes)


def historiques_classement(client, joueurs, aujourdhui=None):
    """Historique des classements des joueurs du club (fiches des joueurs) : {licence: [[année, mois,
    points], ...]}, du plus ancien au plus récent, d'après le graphique de leur fiche pingpocket.fr.

    Comme pour les adversaires : une page par joueur, gardée toute la phase (les points officiels ne
    changent qu'en janvier et en juillet), lue par le PC ; la mise à jour en ligne (pingpocket.fr refuse
    les serveurs de GitHub) se sert des pages que le PC a envoyées. Les joueurs restés à 500 points sans
    aucune partie n'ont pas d'historique à montrer : leur page n'est pas demandée.
    """
    aujourdhui = aujourdhui or date.today()
    a_lire = [j["id"] for j in joueurs if (j.get("officiels") or 0) > 500 or j.get("parties")]
    chemins = {lic: pingpocket.CHEMIN_HISTORIQUE.format(lic) for lic in a_lire}
    debut_phase = datetime.fromisoformat(fftt.bornes_phase(date.today())[0]).timestamp()
    ttl = max(JOUR, time.time() - debut_phase)
    disponible = getattr(client, "disponible", lambda site: True)
    muet = (not disponible(SITE_PINGPOCKET) or SITE_PINGPOCKET in getattr(client, "sites_cache_seul", ())
            or getattr(client, "hors_ligne", False))
    if muet:  # seules les pages déjà en cache servent (même anciennes) : on ne demande pas les autres
        demandes = [lic for lic in a_lire if client.date(chemins[lic]) is not None]
    else:
        en_cache = getattr(client, "en_cache", lambda chemin, ttl: False)
        nouvelles = [lic for lic in a_lire if not en_cache(chemins[lic], ttl)]
        reportees = set(nouvelles[MAX_HISTORIQUES:])
        demandes = [lic for lic in a_lire if lic not in reportees]
        a_telecharger = len(nouvelles) - len(reportees)
        if a_telecharger > 30:
            print(f"  {a_telecharger} historiques à télécharger : environ {a_telecharger * 4 // 60 + 1} minutes "
                  "(une page toutes les 4 secondes), une seule fois par phase.", flush=True)
    pages = client.get_plusieurs([chemins[lic] for lic in demandes], ttl=ttl, message="historiques des joueurs",
                                 perime_si_erreur=True) if demandes else {}
    limite = (aujourdhui.year, aujourdhui.month)  # une archive ne montre rien d'après sa date
    res = {}
    for lic in demandes:
        html = pages.get(chemins[lic])
        points = [list(p) for p in sorted(set(pingpocket.lire_historique(html)))] if html else []
        points = [p for p in points if (p[0], p[1]) <= limite]
        if points:
            res[lic] = points
    print(f"  historiques lus : {len(res)} joueurs sur {len(a_lire)}"
          + (" (les autres : au prochain lancement sur le PC, lancer.bat)" if len(res) < len(a_lire) and muet else ""), flush=True)
    return res


def controle_parties(joueurs, detail_rencontres, numero_club, source):
    """Contrôles du classement virtuel :
    - joueurs dont les parties n'ont pas pu être lues (API muette) ;
    - parties de championnat présentes sur les feuilles de match de Vaires mais absentes de la
      liste des parties du joueur (saisie pas encore propagée) : son total serait faux.
    """
    retenues = {j["id"]: {p["id"] for p in j["parties"]} for j in joueurs}
    noms = {j["id"]: f"{j['nom'] or ''} {j['prenom'] or ''}".strip() for j in joueurs}
    inconnus = {j["id"] for j in joueurs if j["inconnu"]}
    absentes = Counter()
    for d in detail_rencontres.values():
        for cote in ("home", "away"):
            if fftt.club_de((d.get(f"{cote}Opponent") or {}).get("team") or {})[0] != numero_club:
                continue
            for g in d.get("games") or []:
                lic = (g.get(f"{cote}Player") or {}).get("identifier")
                autre = "away" if cote == "home" else "home"
                if (not lic or lic not in retenues or not _simple(g) or g.get("notCounted") or g.get("forfeit")
                        or g.get("winner") not in ("home", "away") or not g.get(f"{autre}Player")):
                    continue
                if g.get("id") not in retenues[lic] and lic not in inconnus:
                    absentes[lic] += 1
    return {"liste": source["liste"],
            "sans_reponse": sorted(noms[j["id"]] for j in joueurs if j["inconnu"]),
            "parties_absentes": [{"joueur": noms[lic], "nb": nb} for lic, nb in sorted(absentes.items(), key=lambda x: noms[x[0]])]}


def recuperer_virtuel(client, numero_club="08770250", aujourdhui=None, dossier_import=None):
    aujourdhui = aujourdhui or date.today()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)
    fin = min(fin, aujourdhui.isoformat())  # rien après ce jour (archives : la veille de la journée suivante)

    print(f"1/4 Équipes et feuilles de match du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
    feuilles = feuilles_du_club(client, numero_club, aujourdhui)
    print("2/4 Licenciés du club (pingpocket.fr ou dossier import)", flush=True)
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
        j["alignements"] = sorted(({"journee": p["journee"], "date": p["date"], "equipe": f"V{p['numero']}" + (" F" if p["championnat"] == "F" else "")}
                                   for p in feuilles["parts"].get(lic, [])), key=lambda a: (a["date"], a["journee"], a["equipe"]))

    print(f"3/4 Parties de toutes les compétitions : {len(joueurs)} joueurs (API FFTT)", flush=True)
    toutes = _lire_parties(client, sorted(joueurs))
    # En phase 2, les parties de la phase 1 (déjà dans la liste de la saison) servent aussi : la page
    # « Progression des joueurs » suit toute la saison, depuis le 1er septembre
    debut1, fin1 = fftt.bornes_phase(date(int(saison[:4]), 9, 1)) if phase == 2 else (None, None)
    retenue = lambda jour: debut <= jour <= fin or (debut1 is not None and debut1 <= jour <= fin1)
    du_club = [p for ps in toutes.values() if ps for p in ps if retenue((p.get("date") or "")[:10]) and _simple(p)]
    competitions = _competitions(client, {(p.get("contest") or {}).get("id") for p in du_club} - {None})
    # Détail des parties (non comptée, forfait) : seulement pour la phase en cours ; celles de la phase 1,
    # pour la progression, s'en passent (sinon des centaines de requêtes de plus en janvier)
    etats = _etats(client, [p for p in du_club if debut <= p["date"][:10] <= fin], feuilles["detail"])

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
            "alignements": j.get("alignements") or [],
        })
        if debut1:  # phase 1 de la saison : ses points officiels et ses parties (progression depuis septembre)
            lignes1, officiels1, _ = analyser(lic, parties or [], competitions, etats, debut1, fin1)
            resultat[-1]["phase1"] = {"officiels": officiels1.most_common(1)[0][0] if officiels1 else None,
                                      "parties": lignes1}
    resultat.sort(key=lambda j: (j["virtuels"] is None, -(j["virtuels"] or 0), j["nom"] or ""))

    print("4/4 Historique des classements des joueurs (pingpocket.fr, pages gardées toute la phase)", flush=True)
    historiques = historiques_classement(client, resultat, aujourdhui)
    for j in resultat:
        j["historique"] = historiques.get(j["id"])

    comps = Counter()
    for j in resultat:
        for l in j["parties"]:
            comps[(l["competition"], l["coef"], l["championnat"])] += 1
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "debut": debut, "club": {"numero": numero_club, "nom": feuilles["nom_club"]}, "source": source,
        "verification": feuilles["verification"],
        "controle": controle_parties(resultat, feuilles["detail"], numero_club, source),
        "competitions": [{"nom": n, "coef": c, "championnat": ch, "parties": nb}
                         for (n, c, ch), nb in sorted(comps.items(), key=lambda x: (not x[0][2], -x[1]))],
        "joueurs": resultat,
    }

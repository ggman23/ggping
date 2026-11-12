"""Page « Fiches des joueurs » : tout ce que l'outil sait d'un joueur de Vaires sur une page, choisie dans
une liste déroulante.

Aucune donnée de plus : ce sont les parties du classement virtuel (toutes compétitions, depuis le début
de la saison) et la courbe de la page « Progression des joueurs ». En plus du bilan, des perfs et des
contres :

- manches : parties gagnées en 3, 4 ou 5 manches, belles, manches serrées (2 points d'écart) ;
- remontées : victoires après avoir été mené au score des manches, avances perdues, et ce que donne
  la première manche ;
- niveau de l'adversaire : bilan contre plus faible, de même niveau (à SEUIL_NIVEAU points près), plus fort.

Le détail des manches vient des feuilles de match (championnat par équipes) et, pour les autres
compétitions, de ce que l'API en donne ; une partie saisie sans ses manches compte dans le bilan mais
pas dans les statistiques de manches (« sans le détail »).

Et l'historique de son classement : les points officiels de chaque phase depuis ses débuts et son
meilleur classement, d'après l'historique de pingpocket.fr (lu par le PC, voir virtuel.historiques_classement).
"""

from . import pingpocket, progression
from .virtuel import classement, famille_competition

SEUIL_NIVEAU = 50  # points d'écart (points officiels de la phase) en dessous desquels l'adversaire est « de même niveau »
NIVEAUX = [("plus_faible", "Contre plus faible"), ("meme", "Contre même niveau"), ("plus_fort", "Contre plus fort")]


def score(manches):
    """(manches gagnées, manches perdues) ; les manches sont vues du joueur : ses points d'abord."""
    return sum(a > b for a, b in manches), sum(b > a for a, b in manches)


def detail_fiable(p):
    """Vrai si les manches de la partie sont connues et racontent bien son résultat (pas d'abandon, le
    vainqueur a plus de manches que le perdant, et au moins deux)."""
    if not p.get("manches") or p.get("abandon"):
        return False
    g, d = score(p["manches"])
    return max(g, d) >= 2 and (g > d) == bool(p["victoire"])


def stats_manches(parties):
    """Parties en 3, 4 ou 5 manches (au meilleur des cinq manches : le vainqueur en a 3), belles (manche
    décisive, quel que soit le format), manches et points des manches, manches serrées."""
    avec = [p for p in parties if detail_fiable(p)]
    formats = {n: {"jouees": 0, "gagnees": 0} for n in (3, 4, 5)}
    belles, manches, points, serrees, autres = [0, 0], [0, 0], [0, 0], [0, 0], 0
    for p in avec:
        g, d = score(p["manches"])
        if max(g, d) == 3:
            formats[g + d]["jouees"] += 1
            formats[g + d]["gagnees"] += bool(p["victoire"])
        else:
            autres += 1  # autre format (deux ou quatre manches gagnantes)
        if g + d == 2 * max(g, d) - 1:  # manche décisive : 3-2, 2-1, 4-3
            belles[0] += 1
            belles[1] += bool(p["victoire"])
        manches[0] += g
        manches[1] += d
        for a, b in p["manches"]:
            points[0] += a
            points[1] += b
            if abs(a - b) == 2:  # 11-9, 12-10, 15-13...
                serrees[0 if a > b else 1] += 1
    return {"avec_detail": len(avec), "sans_detail": len(parties) - len(avec),
            "formats": [{"manches": n, **formats[n]} for n in (3, 4, 5)], "autres_formats": autres,
            "belles": {"jouees": belles[0], "gagnees": belles[1]},
            "manches": manches, "points": points, "serrees": serrees}


def stats_remontees(parties):
    """Remontées : victoires après avoir été mené au score des manches (dont celles après deux manches
    de retard : 0-2, 1-3) ; avances perdues : défaites après avoir mené (dont celles après deux manches
    d'avance) ; et le résultat selon la première manche."""
    r = {"remontees": 0, "remontees_de_2": 0, "avances_perdues": 0, "avances_perdues_de_2": 0,
         "premiere_gagnee": {"jouees": 0, "gagnees": 0}, "premiere_perdue": {"jouees": 0, "gagnees": 0}}
    for p in parties:
        if not detail_fiable(p):
            continue
        moi = adv = retard = avance = 0
        for a, b in p["manches"]:
            moi += a > b
            adv += b > a
            retard, avance = max(retard, adv - moi), max(avance, moi - adv)
        if p["victoire"] and retard:
            r["remontees"] += 1
            r["remontees_de_2"] += retard >= 2
        if not p["victoire"] and avance:
            r["avances_perdues"] += 1
            r["avances_perdues_de_2"] += avance >= 2
        premiere = r["premiere_gagnee" if p["manches"][0][0] > p["manches"][0][1] else "premiere_perdue"]
        premiere["jouees"] += 1
        premiere["gagnees"] += bool(p["victoire"])
    return r


def niveau(ecart, seuil=SEUIL_NIVEAU):
    """Niveau de l'adversaire d'après l'écart de points (les siens moins ceux du joueur)."""
    return "plus_fort" if ecart > seuil else "plus_faible" if ecart < -seuil else "meme"


def stats_niveaux(parties, seuil=SEUIL_NIVEAU):
    res = {cle: {"cle": cle, "titre": titre, "v": 0, "d": 0, "points": 0.0} for cle, titre in NIVEAUX}
    for p in parties:
        n = res[niveau(p.get("ecart") or 0, seuil)]
        n["v" if p["victoire"] else "d"] += 1
        n["points"] += p["points"]
    return [{**n, "points": round(n["points"], 1)} for n in res.values()]


def stats_competitions(parties):
    """Bilan par famille de compétitions (championnat d'abord, puis par nombre de parties)."""
    familles = {}
    for p in parties:
        f = familles.setdefault(famille_competition(p["competition"], p["championnat"]), {"v": 0, "d": 0, "points": 0.0})
        f["v" if p["victoire"] else "d"] += 1
        f["points"] += p["points"]
    return [{"nom": n, "v": f["v"], "d": f["d"], "points": round(f["points"], 1)}
            for n, f in sorted(familles.items(), key=lambda x: (x[0] != "Championnat", -(x[1]["v"] + x[1]["d"]), x[0]))]


def stats_series(parties):
    """Plus longue série de victoires de la saison, et série en cours (victoires ou défaites)."""
    meilleure = courante = 0
    for p in parties:
        courante = courante + 1 if p["victoire"] else 0
        meilleure = max(meilleure, courante)
    en_cours = 0
    for p in reversed(parties):
        if p["victoire"] != parties[-1]["victoire"]:
            break
        en_cours += 1
    return {"meilleure": meilleure, "en_cours": en_cours, "en_cours_victoires": bool(parties and parties[-1]["victoire"])}


def _extremes(parties, nb=3):
    """Meilleures perfs (victoires contre plus de points, du plus gros écart au plus petit) et pires
    contres (défaites contre moins de points)."""
    cle = lambda p: {k: p.get(k) for k in ("date", "competition", "adversaire", "adv_points", "pts_joueur", "ecart", "points")}
    perfs = sorted((p for p in parties if p["victoire"] and (p.get("ecart") or 0) > 0), key=lambda p: -p["ecart"])
    contres = sorted((p for p in parties if not p["victoire"] and (p.get("ecart") or 0) < 0), key=lambda p: p["ecart"])
    return len(perfs), [cle(p) for p in perfs[:nb]], len(contres), [cle(p) for p in contres[:nb]]


def stats_historique(historique):
    """Historique du classement : les points officiels de chaque phase ([année, mois, points], janvier :
    phase 2, juillet : phase 1 de la saison qui commence), du plus ancien au plus récent, et le meilleur
    classement (à égalité, le plus récent ; « actuel » : c'est celui de la dernière phase). None sans historique."""
    if not historique:
        return None
    phases = [list(p) for p in pingpocket.officiels_historique([tuple(p) for p in historique])]
    meilleur = max(phases, key=lambda p: (p[2], p[0], p[1]))
    return {"phases": phases,
            "meilleur": {"points": meilleur[2], "annee": meilleur[0], "mois": meilleur[1],
                         "classement": classement(meilleur[2]), "actuel": meilleur == phases[-1]}}


def parties_de_la_saison(j):
    """Parties du joueur depuis le début de la saison, dans l'ordre : la phase 1 (en phase 2), puis la phase en cours."""
    return [*((j.get("phase1") or {}).get("parties") or []), *j["parties"]]


def fiche(j, courbe=None):
    """Fiche d'un joueur du classement virtuel ; `courbe` : sa ligne de la page Progression (None sans points officiels)."""
    parties = parties_de_la_saison(j)
    v = sum(bool(p["victoire"]) for p in parties)
    nb_perfs, perfs, nb_contres, contres = _extremes(parties)
    return {
        "id": j["id"], "nom": j.get("nom"), "prenom": j.get("prenom"), "sexe": j.get("sexe"), "categorie": j.get("categorie"),
        "equipe": j.get("equipe"), "officiels": j.get("officiels"), "virtuels": j.get("virtuels"), "total_phase": j.get("total"),
        "classement": j.get("classement"), "classement_virtuel": j.get("classement_virtuel"), "inconnu": bool(j.get("inconnu")),
        "bilan": {"v": v, "d": len(parties) - v, "points": round(sum(p["points"] for p in parties), 1)},
        "nb_perfs": nb_perfs, "perfs": perfs, "nb_contres": nb_contres, "contres": contres,
        "manches": stats_manches(parties), "remontees": stats_remontees(parties), "niveaux": stats_niveaux(parties),
        "competitions": stats_competitions(parties), "series": stats_series(parties),
        "alignements": j.get("alignements") or [], "historique": stats_historique(j.get("historique")),
        "courbe": ({k: courbe[k] for k in ("serie", "parties", "victoires", "perfs", "contres", "total", "tendance", "lecture")}
                   if courbe else None),
        "parties": [{k: p.get(k) for k in ("date", "competition", "division", "championnat", "coef", "adversaire", "adv_points",
                                           "pts_joueur", "ecart", "victoire", "points", "manches", "abandon")} for p in parties],
    }


def donnees_fiches(virtuel, donnees_progression=None, aujourdhui=None):
    """Données de la page à partir de celles du classement virtuel (recuperer_virtuel) et de la page
    Progression (calculée ici si elle n'est pas fournie)."""
    prog = donnees_progression or progression.donnees_progression(virtuel, aujourdhui)
    courbes = {x["id"]: x for x in prog["joueurs"]}
    joueurs = [fiche(j, courbes.get(j["id"])) for j in virtuel["joueurs"]]
    joueurs.sort(key=lambda x: ((x["nom"] or "").lower(), (x["prenom"] or "").lower()))
    return {**{k: prog.get(k) for k in ("genere_le", "saison", "phase", "debut", "debut_saison", "club", "date_reference")},
            "semaines": prog["semaines"], "seuil_niveau": SEUIL_NIVEAU, "seuil_tendance": progression.SEUIL_TENDANCE,
            "joueurs": joueurs}


def resume(donnees):
    """Une ligne pour le journal : combien de parties ont le détail de leurs manches, championnat et autres
    compétitions à part (dit si l'API donne les manches hors championnat)."""
    compte = {True: [0, 0], False: [0, 0]}  # championnat ? -> [avec le détail, total]
    for j in donnees["joueurs"]:
        for p in j["parties"]:
            c = compte[bool(p["championnat"])]
            c[0] += detail_fiable(p)
            c[1] += 1
    return (f"{len(donnees['joueurs'])} fiches ; manches connues : championnat {compte[True][0]}/{compte[True][1]}, "
            f"autres compétitions {compte[False][0]}/{compte[False][1]} ; historiques des classements : "
            f"{sum(1 for j in donnees['joueurs'] if j['historique'])}/{len(donnees['joueurs'])}")

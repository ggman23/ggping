"""Points virtuels calculés mois par mois, comme la FFTT (joueurs du 77).

Pour chaque partie, la FFTT compare « la valeur du joueur à la fin de la période précédant la partie »
(sa situation mensuelle), et non ses points officiels du début de la phase. L'API donne, dans chaque
partie, les points officiels de la phase des deux joueurs : calculer toutes les parties avec ces
points-là surestime les gains d'un joueur qui progresse (signalé le 15/11/2026 : +186 dans l'outil,
+123 à la FFTT, à nombre de parties égal).

Calcul mensuel : mois après mois, la référence de chaque joueur du 77 est ses points du début de la
phase plus ce qu'il a gagné les mois précédents ; un adversaire hors du 77 garde les points donnés par
la partie. Les parties d'un mois sont calculées avec les références de la fin du mois précédent.

Les points mensuels publiés par la FFTT (listes de licenciés) servent de juge : pour chaque joueur, ce
qu'il a gagné jusqu'à la fin du dernier mois publié, selon chaque calcul, est comparé à « points
mensuels − points du début de la phase ». Le journal donne l'erreur des deux calculs (chiffres
seulement) et la page prend le plus juste.
"""

from collections import defaultdict
from datetime import datetime, timedelta

from .resultats import points_partie
from .virtuel import analyser

ECART_SIGNIFICATIF = 0.8  # le calcul mensuel n'est retenu que si son erreur moyenne est au plus 80 % de l'autre
MINIMUM_COMPARES = 50      # joueurs comparés au moins pour décider


def lignes_des_joueurs(toutes, competitions, etats, debut, fin):
    """Parties retenues de chaque joueur (mêmes règles que le classement virtuel) avec la licence de
    l'adversaire : ({licence: [ligne]}, {licence: points du début de la phase})."""
    lignes, depart = {}, {}
    for lic, parties in toutes.items():
        if not parties:
            continue
        adverses = {}
        for p in parties:
            h, a = (p.get("homePlayer") or {}).get("identifier"), (p.get("awayPlayer") or {}).get("identifier")
            adverses[p.get("id")] = a if h == lic else h
        ls, officiels, _ = analyser(lic, parties, competitions, etats, debut, fin)
        for l in ls:
            l["adv_licence"] = adverses.get(l["id"])
        lignes[lic] = ls
        if officiels:
            depart[lic] = officiels.most_common(1)[0][0]
    return lignes, depart


def calcul_mensuel(lignes, depart):
    """{licence: [points de chaque partie, dans l'ordre de ses lignes]} : parties d'un mois calculées avec
    les références de fin du mois précédent (début de phase + gains des mois précédents)."""
    mois = sorted({l["date"][:7] for ls in lignes.values() for l in ls})
    cumul = defaultdict(float)
    points = {lic: [None] * len(ls) for lic, ls in lignes.items()}
    for m in mois:
        reference = {lic: depart[lic] + cumul[lic] for lic in depart}
        gains = defaultdict(float)
        for lic, ls in lignes.items():
            for k, l in enumerate(ls):
                if l["date"][:7] != m:
                    continue
                moi = reference.get(lic, l["pts_joueur"])
                adv = reference.get(l["adv_licence"], l["adv_points"])
                points[lic][k] = round(points_partie(moi, adv, l["victoire"], l["coef"]), 3)
                gains[lic] += points[lic][k]
        for lic, g in gains.items():
            cumul[lic] += g
    return points


def _fin_du_mois_avant(jour, mois_en_arriere):
    """Dernier jour du mois situé `mois_en_arriere` mois avant celui de `jour` (1 : le mois précédent)."""
    d = jour.replace(day=1)
    for _ in range(mois_en_arriere - 1):
        d = (d - timedelta(days=1)).replace(day=1)
    return (d - timedelta(days=1)).isoformat()


def comparer_aux_mensuels(lignes, depart, mensuels, dates_listes, points_mensuel):
    """Erreur de chaque calcul face aux points mensuels publiés : {(calcul, décalage): (joueurs, erreur
    moyenne, part à 2 points près)} ; décalage : la liste lue donne la situation de la fin du mois
    précédent (1) ou du mois d'avant (2), selon la date de publication."""
    res = {}
    for decalage in (1, 2):
        erreurs = {"constant": [], "mensuel": []}
        for lic, ls in lignes.items():
            if lic not in depart or mensuels.get(lic) is None or not dates_listes.get(lic):
                continue
            borne = _fin_du_mois_avant(datetime.fromtimestamp(dates_listes[lic]).date(), decalage)
            avant = [k for k, l in enumerate(ls) if l["date"] <= borne]
            if not avant:
                continue
            fftt = mensuels[lic] - depart[lic]
            erreurs["constant"].append(sum(ls[k]["points"] for k in avant) - fftt)
            erreurs["mensuel"].append(sum(points_mensuel[lic][k] for k in avant) - fftt)
        for calcul, e in erreurs.items():
            if e:
                res[(calcul, decalage)] = (len(e), round(sum(abs(x) for x in e) / len(e), 2),
                                           round(sum(1 for x in e if abs(x) <= 2) / len(e), 3))
    return res


def choisir(comparaison):
    """'mensuel' si le calcul mensuel est nettement plus proche des points publiés par la FFTT (au
    meilleur décalage de chacun), sinon 'constant' ; et le résumé de la comparaison."""
    meilleur = {}
    for (calcul, decalage), (n, erreur, part) in comparaison.items():
        if n >= MINIMUM_COMPARES and (calcul not in meilleur or erreur < meilleur[calcul][1]):
            meilleur[calcul] = (n, erreur, part, decalage)
    if "constant" in meilleur and "mensuel" in meilleur and meilleur["mensuel"][1] <= ECART_SIGNIFICATIF * meilleur["constant"][1]:
        return "mensuel", meilleur
    return "constant", meilleur


def points_variables(lignes):
    """Joueurs dont les points lus dans leurs parties changent d'une partie à l'autre (contrôle : l'API
    donne-t-elle les points de la phase, constants, ou ceux du mois ?)."""
    return sum(1 for ls in lignes.values() if len({l["pts_joueur"] for l in ls}) > 1), sum(1 for ls in lignes.values() if ls)

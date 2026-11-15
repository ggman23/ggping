"""Points virtuels calculés mois par mois, comme la FFTT (joueurs du 77).

Pour chaque partie, la FFTT compare « la valeur du joueur à la fin de la période précédant la partie »
(sa situation mensuelle), et non ses points officiels du début de la phase. L'API donne, dans chaque
partie, les points officiels de la phase des deux joueurs : calculer toutes les parties avec ces
points-là surestime les gains d'un joueur qui progresse (signalé le 15/11/2026 : +186 dans l'outil,
+123 à la FFTT, à nombre de parties égal).

Calcul mensuel : période après période (un mois ; juillet et août comptent avec septembre), la
référence de chaque joueur du 77 est ses points du début de la phase plus ce qu'il a gagné les périodes
précédentes ; un adversaire hors du 77 garde les points donnés par la partie. Les parties d'une période
sont calculées avec les références de la fin de la période précédente.

Vérifié le 15/11/2026 sur la liste des parties de l'application FFTT du joueur signalé (1499 en début
de saison, 1532,5 à la situation de fin septembre) : au critérium du 11/10 (coefficient 1,5), +8,25
contre un 15xx (victoire normale, écart 25 à 49), +12 contre un 16xx et +19,5 contre un 17xx
(victoires anormales, écarts 50 à 99 et 150 à 199) ne sont possibles qu'avec 1532,5, pas avec 1499.
(Les « points mensuels » des listes de licenciés de pingpocket ne donnent pas cette situation : 1499
pour ce joueur ; ils ne peuvent pas servir à vérifier le calcul.)
"""

from collections import defaultdict

from .resultats import points_partie
from .virtuel import analyser


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


def periode(jour):
    """Période FFTT d'une partie (« AAAA-MM ») : son mois, sauf juillet et août, comptés avec septembre.
    Les périodes de la saison commencent en septembre (période 4 : décembre, période 10 : juin) : le joueur
    signalé a ses tournois des 29-30 août et ses parties de septembre dans la même situation mensuelle
    (+33,5), et ses parties de septembre sont calculées avec ses points du début de saison."""
    annee, mois = jour[:4], jour[5:7]
    return f"{annee}-09" if mois in ("07", "08") else jour[:7]


def calcul_mensuel(lignes, depart):
    """{licence: [points de chaque partie, dans l'ordre de ses lignes]} : parties d'une période (un mois,
    juillet et août avec septembre) calculées avec les références de la fin de la période précédente
    (début de phase + gains des périodes précédentes)."""
    mois = sorted({periode(l["date"]) for ls in lignes.values() for l in ls})
    cumul = defaultdict(float)
    points = {lic: [None] * len(ls) for lic, ls in lignes.items()}
    for m in mois:
        reference = {lic: depart[lic] + cumul[lic] for lic in depart}
        gains = defaultdict(float)
        for lic, ls in lignes.items():
            for k, l in enumerate(ls):
                if periode(l["date"]) != m:
                    continue
                moi = reference.get(lic, l["pts_joueur"])
                adv = reference.get(l["adv_licence"], l["adv_points"])
                points[lic][k] = round(points_partie(moi, adv, l["victoire"], l["coef"]), 3)
                gains[lic] += points[lic][k]
        for lic, g in gains.items():
            cumul[lic] += g
    return points


def points_variables(lignes):
    """Joueurs dont les points lus dans leurs parties changent d'une partie à l'autre (contrôle : l'API
    donne-t-elle les points de la phase, constants, ou ceux du mois ?)."""
    return sum(1 for ls in lignes.values() if len({l["pts_joueur"] for l in ls}) > 1), sum(1 for ls in lignes.values() if ls)

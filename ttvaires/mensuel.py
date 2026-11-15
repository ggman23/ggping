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

Fiabilité d'une estimation (incertitudes, valeur_estimee, niveau) : les parties de la première période
de la phase sont calculées avec les points du début de phase de tous les joueurs, connus exactement. La
valeur d'un joueur lu reste exacte tant qu'il n'a joué que des joueurs lus ; dès qu'il a joué, après la
première période, un adversaire non lu (dont les gains sont inconnus : points de la phase), sa valeur
des périodes suivantes est estimée. Pour chaque joueur, l'outil compte ses parties contre un adversaire
dont la valeur du mois est estimée : de 1 à SEUILS[0], estimation très proche ; jusqu'à SEUILS[1],
quelques points d'écart possibles ; au-delà, moins sûre (une partie ne change que si l'erreur sur la
valeur de l'adversaire fait passer l'écart dans une autre tranche du barème). Seuils à revoir d'après
des comparaisons avec la FFTT.

Les pages de Vaires (classement virtuel, fiches, progression, résultats, forme des adversaires) se
servent des valeurs mensuelles ainsi calculées pour les joueurs du 77 : la page des clubs du 77 les
enregistre (FICHIER, dans le cache de la mise à jour en ligne) et les pages les relisent au lancement
suivant (References). Sans ce fichier (PC, première fois), le calcul reste sur les points de la phase.
"""

import json
from collections import defaultdict

from .resultats import points_partie
from .virtuel import analyser

FICHIER = "references_77.json"  # {licence: {période « AAAA-MM »: valeur du joueur au début de la période}}
CLE_77 = "_77"                  # dans le même fichier : les licences des joueurs du 77 (les autres sont d'autres départements)
CLE_PREMIERE = "_premiere"      # première période de la phase (« AAAA-MM »)
CLE_ESTIME = "_estime"          # {licence: période} : sa valeur est estimée pour les périodes qui suivent celle-ci
SEUILS = (5, 20)                # parties contre un adversaire à valeur estimée : très proche, quelques points, moins sûre


def lignes_des_joueurs(toutes, competitions, etats, debut, fin):
    """Parties retenues de chaque joueur (mêmes règles que le classement virtuel) avec la licence de
    l'adversaire : ({licence: [ligne]}, {licence: points du début de la phase})."""
    lignes, depart = {}, {}
    for lic, parties in toutes.items():
        if not parties:
            continue
        ls, officiels, _ = analyser(lic, parties, competitions, etats, debut, fin)
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


def calcul_mensuel(lignes, depart, references=None):
    """{licence: [points de chaque partie, dans l'ordre de ses lignes]} : parties d'une période (un mois,
    juillet et août avec septembre) calculées avec les références de la fin de la période précédente
    (début de phase + gains des périodes précédentes). references (dict) : rempli avec la valeur de
    chaque joueur au début de chaque période, {licence: {période: valeur}}."""
    mois = sorted({periode(l["date"]) for ls in lignes.values() for l in ls})
    cumul = defaultdict(float)
    points = {lic: [None] * len(ls) for lic, ls in lignes.items()}
    for m in mois:
        reference = {lic: depart[lic] + cumul[lic] for lic in depart}
        if references is not None:
            for lic, valeur in reference.items():
                references.setdefault(lic, {})[m] = round(valeur, 2)
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


def incertitudes(lignes, connus, premiere):
    """{licence: période} : pour chaque joueur lu, la première période après `premiere` où il a joué un
    adversaire absent de `connus` (gains inconnus : points de la phase) ; sa valeur est estimée ensuite."""
    res = {}
    for lic, ls in lignes.items():
        for l in ls:
            p = periode(l["date"])
            if p > premiere and l.get("adv_licence") not in connus and (lic not in res or p < res[lic]):
                res[lic] = p
    return res


def valeur_estimee(adv, jour, connus, estime, premiere):
    """La valeur du mois de l'adversaire est-elle estimée pour une partie de ce jour ?"""
    p = periode(jour)
    if p <= premiere:
        return False  # première période : points du début de phase, connus pour tous
    return adv not in connus or (adv in estime and p > estime[adv])


def niveau(estimees):
    """0 : aucune partie contre un adversaire à valeur estimée ; 1 : très proche ; 2 : quelques points
    d'écart possibles ; 3 : moins sûre."""
    return 0 if not estimees else 1 if estimees <= SEUILS[0] else 2 if estimees <= SEUILS[1] else 3


def points_variables(lignes):
    """Joueurs dont les points lus dans leurs parties changent d'une partie à l'autre (contrôle : l'API
    donne-t-elle les points de la phase, constants, ou ceux du mois ?)."""
    return sum(1 for ls in lignes.values() if len({l["pts_joueur"] for l in ls}) > 1), sum(1 for ls in lignes.values() if ls)


def enregistrer(client, references):
    """Valeurs mensuelles des joueurs du 77, pour les pages du lancement suivant (dossier du cache)."""
    dossier = getattr(client, "dossier", None)
    if dossier is not None and references:
        (dossier / FICHIER).write_text(json.dumps(references, separators=(",", ":")), encoding="utf-8")


class References:
    """Valeur mensuelle connue des joueurs du 77 (enregistrée par la page des clubs du 77)."""

    def __init__(self, table=None):
        self.table = table or {}

    @classmethod
    def lire(cls, client):
        dossier = getattr(client, "dossier", None)
        try:
            return cls(json.loads((dossier / FICHIER).read_text(encoding="utf-8"))) if dossier is not None else cls()
        except (OSError, ValueError):
            return cls()

    def __bool__(self):
        return bool(self.table)

    def du_77(self):
        """Licences des joueurs du 77 (vide si le fichier ne les donne pas)."""
        return set(self.table.get(CLE_77) or [])

    def valeur(self, licence, jour):
        return self.table.get(licence, {}).get(periode(jour))

    def estimee(self, adv, jour):
        """La valeur du mois de l'adversaire est-elle estimée pour cette partie ? None si le fichier ne le
        dit pas (enregistré avant le 15/11/2026)."""
        premiere = self.table.get(CLE_PREMIERE)
        if not premiere:
            return None
        return valeur_estimee(adv, jour, self.table, self.table.get(CLE_ESTIME) or {}, premiere)


def recalculer(lignes, licence, depart, references):
    """Points de chaque partie d'un joueur (lignes de virtuel.analyser, dans l'ordre des dates) avec les
    valeurs mensuelles : la sienne et celle de l'adversaire si elles sont connues ; à défaut, la sienne
    vaut son début de phase + ses gains des périodes précédentes, celle de l'adversaire ses points de la
    partie. Met à jour pts_joueur, adv_points, ecart et points de chaque ligne."""
    cumul, avant, courante = 0.0, 0.0, None
    base = depart if depart is not None else (lignes[0]["pts_joueur"] if lignes else None)
    for l in lignes:
        p = periode(l["date"])
        if p != courante:
            avant, courante = cumul, p
        moi = references.valeur(licence, l["date"])
        moi = moi if moi is not None else base + avant
        adv = references.valeur(l.get("adv_licence"), l["date"])
        adv = adv if adv is not None else l["adv_points"]
        l["pts_joueur"], l["adv_points"], l["ecart"] = round(moi, 1), round(adv, 1), round(adv - moi, 1)
        l["points"] = round(points_partie(moi, adv, l["victoire"], l["coef"]), 3)
        cumul += l["points"]
    return lignes

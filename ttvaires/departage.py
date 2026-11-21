"""Classement d'une poule et départage des égalités, selon l'article I.202 des règlements sportifs de la
FFTT (juillet 2026, https://www.fftt.com/reglements/), auquel renvoient les championnats par équipes.

Classement par points-rencontres (victoire 3, nul 2, défaite 1, défaite par forfait ou pénalité 0). Pour
les équipes à égalité, deux cas :

- I.202.1, rencontres arrêtées au score acquis : classement particulier des équipes à égalité, sur les
  seules rencontres disputées entre elles (« goal-average particulier ») : a) points-rencontres, b) quotient
  des points-parties gagnés / perdus, c) quotient des manches, d) quotient des points-jeu, e) tirage au sort ;
- I.202.2, toutes les parties jouées : d'abord le quotient général des points-parties (toutes les rencontres
  de la poule), puis, pour celles encore à égalité, le même classement particulier (a à e).

Dans les deux cas, « chaque fois qu'une ou plusieurs équipes ne peuvent pas être classées, il convient de
recommencer la procédure du départage pour celles restant encore à égalité » : on repart du critère a) avec
les seules rencontres entre les équipes encore à égalité. Une équipe battue par forfait est considérée comme
battue par toutes les parties prévues à 0 (I.202.2) ou par la moitié des parties plus une à 0 (I.202.1),
chaque partie 3 manches à 0 et chaque manche 11-0. Le tirage au sort n'est pas simulé : les équipes restent
ex aequo.

Le cas se lit sur les scores : quand toutes les parties sont jouées, toutes les rencontres d'une poule ont le
même total de parties (14 à quatre joueurs, 10 à trois) ; arrêtées au score acquis, les totaux varient.
"""

from fractions import Fraction

TOUTES, SCORE_ACQUIS = "toutes", "score_acquis"
REGLES = {TOUTES: "article I.202.2 (toutes les parties jouées) : quotient général des parties, puis goal-average particulier",
          SCORE_ACQUIS: "article I.202.1 (arrêt au score acquis) : goal-average particulier"}
GENERAL = "quotient général des parties"
CRITERES = [("pts", "points-rencontres entre elles"), ("parties", "quotient des parties entre elles"),
            ("manches", "quotient des manches entre elles"), ("jeu", "quotient des points-jeu entre elles")]
TIRAGE = "tirage au sort (non simulé : ex aequo)"


def quotient(gagnes, perdus):
    """Quotient comparable : g / p, et g / 0 au-dessus de tout quotient fini (0 / 0 vaut 0)."""
    if perdus == 0:
        return (1, Fraction(gagnes)) if gagnes else (0, Fraction(0))
    return (0, Fraction(gagnes, perdus))


def regle_de_la_poule(rencontres):
    """TOUTES si toutes les rencontres sans forfait ont le même total de parties, SCORE_ACQUIS sinon (TOUTES
    tant qu'il n'y a pas deux rencontres pour en juger)."""
    totaux = {sum(r["parties"]) for r in rencontres if not r.get("forfait")}
    return SCORE_ACQUIS if len(totaux) > 1 else TOUTES


def ajuster_forfaits(rencontres, regle):
    """Rencontres perdues par forfait comptées comme le règlement le dit (voir le module)."""
    prevues = max((sum(r["parties"]) for r in rencontres if not r.get("forfait")), default=0)
    res = []
    for r in rencontres:
        a, b = r["pts"]
        if r.get("forfait") and a != b and prevues:
            n = prevues if regle == TOUTES else prevues // 2 + 1
            gagne = (n, 0) if a > b else (0, n)
            r = {**r, "parties": gagne, "manches": tuple(3 * x for x in gagne), "jeu": tuple(33 * x for x in gagne)}
        res.append(r)
    return res


def _cumul(equipes, rencontres, cle, entre_elles=True):
    s = {n: [0, 0] for n in equipes}
    for r in rencontres:
        dom, ext = r["dom"], r["ext"]
        if entre_elles and not (dom in s and ext in s):
            continue
        a, b = r[cle]
        if dom in s:
            s[dom][0] += a
            s[dom][1] += b
        if ext in s:
            s[ext][0] += b
            s[ext][1] += a
    return s


def _groupes(equipes, valeur):
    """Équipes regroupées par valeur, de la meilleure à la moins bonne (ordre d'origine gardé dans un groupe)."""
    return [[n for n in equipes if valeur[n] == v] for v in sorted({valeur[n] for n in equipes}, reverse=True)]


def departager(equipes, rencontres, critere=None):
    """Classement particulier d'équipes à égalité : [(groupe, critère qui l'a placé)] ; un groupe de plusieurs
    équipes est resté à égalité (tirage au sort)."""
    if len(equipes) == 1:
        return [(equipes, critere)]
    for cle, libelle in CRITERES:
        s = _cumul(equipes, rencontres, cle)
        valeur = {n: (0, Fraction(s[n][0])) if cle == "pts" else quotient(*s[n]) for n in equipes}
        groupes = _groupes(equipes, valeur)
        if len(groupes) > 1:  # on recommence la procédure pour chaque groupe encore à égalité
            return [x for g in groupes for x in departager(g, rencontres, libelle)]
    return [(equipes, TIRAGE)]


def classer(points, rencontres, regle=None):
    """Classement d'une poule. `points` : {équipe: points-rencontres} (ordre d'origine gardé entre ex aequo) ;
    `rencontres` : [{dom, ext, pts, parties, manches, jeu : (domicile, extérieur), forfait}].
    Renvoie (règle, [(équipe, rang, critère qui a départagé l'équipe ou None)])."""
    regle = regle or regle_de_la_poule(rencontres)
    rencontres = ajuster_forfaits(rencontres, regle)
    places = []
    for groupe in _groupes(list(points), {n: points[n] for n in points}):
        if len(groupe) == 1:
            places.append((groupe, None))
        elif regle == TOUTES:
            s = _cumul(groupe, rencontres, "parties", entre_elles=False)
            sous = _groupes(groupe, {n: quotient(*s[n]) for n in groupe})
            places += [x for g in sous for x in departager(g, rencontres, GENERAL if len(sous) > 1 else None)]
        else:
            places += departager(groupe, rencontres)
    res, rang = [], 1
    for groupe, critere in places:
        res += [(n, rang, critere) for n in groupe]
        rang += len(groupe)
    return regle, res

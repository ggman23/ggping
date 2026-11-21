"""Départage des égalités dans une poule : article I.202 des règlements sportifs de la FFTT."""

from ttvaires import departage
from ttvaires.departage import GENERAL, SCORE_ACQUIS, TIRAGE, TOUTES


def renc(dom, ext, parties, manches=None, jeu=None, forfait=False):
    a, b = parties
    pts = (3, 1) if a > b else (1, 3) if b > a else (2, 2)
    if forfait:
        pts = (3, 0) if a > b else (0, 3)
    return {"dom": dom, "ext": ext, "pts": pts, "parties": parties, "forfait": forfait,
            "manches": manches or (3 * a, 3 * b), "jeu": jeu or (33 * a, 33 * b)}


def test_face_a_face_ou_quotient_general_selon_le_cas():
    """A et B à égalité de points : A a gagné leur rencontre, B a le meilleur quotient général de parties.
    Arrêt au score acquis (I.202.1) : A devant (goal-average particulier) ; toutes les parties jouées
    (I.202.2) : B devant (quotient général d'abord)."""
    rencontres = [renc("A", "B", (8, 6)), renc("B", "C", (14, 0)), renc("A", "C", (8, 6)),
                  renc("B", "D", (14, 0)), renc("A", "D", (6, 8)), renc("C", "D", (7, 7))]
    points = {"B": 7, "A": 7, "D": 6, "C": 4}
    assert departage.classer(points, rencontres, SCORE_ACQUIS)[1] == [
        ("A", 1, "points-rencontres entre elles"), ("B", 2, "points-rencontres entre elles"), ("D", 3, None), ("C", 4, None)]
    assert departage.classer(points, rencontres, TOUTES)[1] == [
        ("B", 1, GENERAL), ("A", 2, GENERAL), ("D", 3, None), ("C", 4, None)]


def test_deux_equipes_departagees_par_leur_rencontre():
    rencontres = [renc("A", "B", (6, 8)), renc("A", "C", (14, 0)), renc("C", "B", (8, 6)), renc("D", "A", (7, 7))]
    points = {"A": 6, "B": 4, "C": 4, "D": 2}
    regle, places = departage.classer(points, rencontres, SCORE_ACQUIS)
    assert [(n, r) for n, r, _ in places] == [("A", 1), ("C", 2), ("B", 3), ("D", 4)]
    assert dict((n, c) for n, _, c in places)["C"] == "points-rencontres entre elles"


def test_egalite_a_trois_puis_on_recommence_pour_les_deux_restantes():
    """A, B, C à égalité : entre elles, A a 6 points, B et C 3 (nul entre eux). On recommence pour B et C sur
    leur seule rencontre : nul, parties égales, manches 22-20 pour B. Avec les manches des trois rencontres,
    C serait devant (B a pris une raclée contre A) : la procédure recommencée donne B."""
    rencontres = [renc("A", "B", (8, 6), manches=(30, 5)), renc("A", "C", (8, 6), manches=(25, 20)),
                  renc("B", "C", (7, 7), manches=(22, 20))]
    regle, places = departage.classer({"C": 6, "B": 6, "A": 6, "Z": 0}, rencontres, SCORE_ACQUIS)
    assert [(n, r, c) for n, r, c in places] == [
        ("A", 1, "points-rencontres entre elles"), ("B", 2, "quotient des manches entre elles"),
        ("C", 3, "quotient des manches entre elles"), ("Z", 4, None)]


def test_cycle_de_trois_departage_aux_parties():
    rencontres = [renc("A", "B", (8, 6)), renc("B", "C", (9, 5)), renc("C", "A", (10, 4))]
    regle, places = departage.classer({"A": 4, "B": 4, "C": 4}, rencontres, SCORE_ACQUIS)
    # entre elles : 4 points chacune ; parties A 12-16, B 15-13, C 15-13 ; B et C : leur rencontre, B gagne
    assert [(n, r) for n, r, _ in places] == [("B", 1), ("C", 2), ("A", 3)]
    assert places[2][2] == "quotient des parties entre elles"


def test_forfait_compte_comme_le_reglement_le_dit():
    """Forfait : toutes les parties prévues à 0 (I.202.2), la moitié plus une à 0 (I.202.1), chaque partie
    3 manches à 0 et chaque manche 11-0 (et non le score saisi)."""
    rencontres = [renc("A", "B", (8, 6)), renc("C", "D", (0, 0), forfait=True)]
    rencontres[1]["pts"] = (3, 0)
    ajuste = departage.ajuster_forfaits(rencontres, TOUTES)[1]
    assert (ajuste["parties"], ajuste["manches"], ajuste["jeu"]) == ((14, 0), (42, 0), (462, 0))
    assert departage.ajuster_forfaits(rencontres, SCORE_ACQUIS)[1]["parties"] == (8, 0)


def test_egalite_parfaite_ex_aequo_et_cas_lu_sur_les_scores():
    rencontres = [renc("A", "C", (7, 7)), renc("B", "D", (7, 7)), renc("A", "B", (7, 7))]
    regle, places = departage.classer({"A": 4, "B": 4, "C": 2, "D": 2}, rencontres)
    assert regle == TOUTES and [(n, r, c) for n, r, c in places] == [
        ("A", 1, TIRAGE), ("B", 1, TIRAGE), ("C", 3, TIRAGE), ("D", 3, TIRAGE)]
    # Rencontres arrêtées au score acquis : des totaux de parties différents
    assert departage.regle_de_la_poule([renc("A", "B", (8, 2)), renc("C", "D", (8, 6))]) == SCORE_ACQUIS
    assert departage.regle_de_la_poule([renc("A", "B", (10, 4)), renc("C", "D", (8, 6))]) == TOUTES

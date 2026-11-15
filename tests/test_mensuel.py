"""Points virtuels mois par mois, comme la FFTT : chaque partie avec les points de fin du mois précédent."""

from datetime import datetime

from ttvaires import mensuel
from ttvaires.resultats import points_partie


def _ligne(jour, adv, adv_points, victoire, pts=1000, coef=1):
    return {"date": jour, "adv_licence": adv, "adv_points": adv_points, "victoire": victoire, "coef": coef,
            "pts_joueur": pts, "points": round(points_partie(pts, adv_points, victoire, coef), 3)}


def test_les_parties_d_un_mois_avec_les_references_de_fin_du_mois_precedent():
    # a (1000) bat deux fois x (hors du 77, 1115) en septembre, puis le rejoue en octobre
    lignes = {"a": [_ligne("2026-09-10", "x", 1115, True), _ligne("2026-09-20", "x", 1115, True),
                    _ligne("2026-10-05", "x", 1115, True)],
              "b": [_ligne("2026-10-06", "a", 1000, False, pts=1200)]}  # b (77) perd contre a en octobre
    points = mensuel.calcul_mensuel(lignes, {"a": 1000, "b": 1200})
    septembre = 2 * points_partie(1000, 1115, True, 1)                                  # 2 × 10 (écart 115)
    assert points["a"][:2] == [10, 10]
    assert points["a"][2] == points_partie(1000 + septembre, 1115, True, 1) == 8        # écart 95 en octobre
    assert points["b"][0] == points_partie(1200, 1000 + septembre, False, 1) == -10     # a vaut 1020 fin septembre
    # Le calcul « constant » (points du début de phase) aurait donné 10 et -12,5
    assert [l["points"] for l in lignes["a"]][2] == 10 and lignes["b"][0]["points"] == -12.5


def test_le_calcul_le_plus_proche_des_points_mensuels_publies_est_retenu():
    # 60 joueurs qui progressent : la FFTT publie (fin octobre) ce que donne le calcul mensuel
    lignes, depart, mensuels, dates = {}, {}, {}, {}
    liste_lue = datetime(2026, 11, 14).timestamp()  # liste lue mi-novembre : situation de fin octobre
    for i in range(60):
        lic = f"j{i}"
        lignes[lic] = [_ligne("2026-09-10", "x", 1115, True), _ligne("2026-09-20", "x", 1115, True),
                       _ligne("2026-10-05", "x", 1115, True), _ligne("2026-11-08", "x", 1115, True)]
        depart[lic], dates[lic] = 1000, liste_lue
    points = mensuel.calcul_mensuel(lignes, depart)
    for lic in lignes:
        mensuels[lic] = depart[lic] + sum(points[lic][:3])  # jusqu'à fin octobre : 10 + 10 + 8
    comparaison = mensuel.comparer_aux_mensuels(lignes, depart, mensuels, dates, points)
    assert comparaison[("mensuel", 1)] == (60, 0.0, 1.0) and comparaison[("constant", 1)] == (60, 2.0, 1.0)
    methode, meilleur = mensuel.choisir(comparaison)
    assert methode == "mensuel" and meilleur["mensuel"][3] == 1
    # Trop peu de joueurs comparés, ou pas d'écart net : on garde le calcul constant
    assert mensuel.choisir({("constant", 1): (10, 5.0, 0.5), ("mensuel", 1): (10, 0.0, 1.0)})[0] == "constant"
    assert mensuel.choisir({("constant", 1): (80, 1.0, 0.9), ("mensuel", 1): (80, 0.9, 0.9)})[0] == "constant"
    assert mensuel.points_variables(lignes) == (0, 60)

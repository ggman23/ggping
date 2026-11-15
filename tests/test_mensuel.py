"""Points virtuels mois par mois, comme la FFTT : chaque partie avec les points de fin du mois précédent."""

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


def test_points_lus_dans_les_parties_constants():
    lignes = {"a": [_ligne("2026-09-10", "x", 1115, True), _ligne("2026-10-05", "x", 1115, True)], "b": []}
    assert mensuel.points_variables(lignes) == (0, 1)


def test_juillet_et_aout_comptent_avec_septembre():
    """Tournois de fin août et parties de septembre : une seule période FFTT (la première de la saison),
    calculée avec les points du début de saison ; octobre avec les gains d'août et de septembre."""
    assert [mensuel.periode(j) for j in ("2026-07-04", "2026-08-30", "2026-09-19", "2026-10-11", "2027-01-09")] == \
        ["2026-09", "2026-09", "2026-09", "2026-10", "2027-01"]
    lignes = {"a": [_ligne("2026-08-30", "x", 1115, True), _ligne("2026-09-05", "x", 1115, True),
                    _ligne("2026-10-05", "x", 1115, True)]}
    points = mensuel.calcul_mensuel(lignes, {"a": 1000})
    assert points["a"] == [10, 10, 8]  # septembre encore à 1000 (écart 115) ; octobre à 1020 (écart 95)

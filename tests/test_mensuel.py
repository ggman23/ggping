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


def test_valeurs_mensuelles_enregistrees_puis_utilisees_par_les_pages_de_vaires(tmp_path):
    """La page des clubs du 77 enregistre la valeur de chaque joueur au début de chaque période ; les pages
    de Vaires la relisent pour calculer chaque partie (le joueur et son adversaire)."""
    class Client:
        dossier = tmp_path
    lignes = {"a": [_ligne("2026-08-30", "b", 1200, True), _ligne("2026-10-05", "b", 1200, True)],
              "b": [_ligne("2026-08-30", "a", 1000, False, pts=1200), _ligne("2026-10-05", "a", 1000, False, pts=1200)]}
    references = {}
    mensuel.calcul_mensuel(lignes, {"a": 1000, "b": 1200}, references)
    g = points_partie(1000, 1200, True, 1)  # août (période de septembre), avec les points du début de saison
    assert references["a"] == {"2026-09": 1000, "2026-10": 1000 + g}
    assert references["b"] == {"2026-09": 1200, "2026-10": 1200 + points_partie(1200, 1000, False, 1)}
    mensuel.enregistrer(Client, references)
    lues = mensuel.References.lire(Client)
    assert lues.valeur("a", "2026-10-20") == 1000 + g and lues.valeur("a", "2026-07-02") == 1000
    assert lues.valeur("inconnu", "2026-10-01") is None
    # Recalcul d'un joueur : sa valeur et celle de l'adversaire du 77 (b) ; un adversaire inconnu (x) garde ses points
    ls = [_ligne("2026-09-10", "b", 1200, True), _ligne("2026-10-06", "b", 1200, False), _ligne("2026-10-07", "x", 1100, False)]
    mensuel.recalculer(ls, "a", 1000, lues)
    assert (ls[0]["pts_joueur"], ls[0]["adv_points"], ls[0]["points"]) == (1000, 1200, g)
    b_oct = references["b"]["2026-10"]
    assert (ls[1]["pts_joueur"], ls[1]["adv_points"]) == (round(1000 + g, 1), round(b_oct, 1))
    assert ls[1]["points"] == round(points_partie(1000 + g, b_oct, False, 1), 3) and ls[1]["ecart"] == round(b_oct - 1000 - g, 1)
    assert (ls[2]["adv_points"], ls[2]["points"]) == (1100, round(points_partie(1000 + g, 1100, False, 1), 3))
    # Sans fichier (PC, première fois) : aucune valeur, les pages gardent les points de la phase
    class Vide:
        dossier = tmp_path / "absent"
    assert not mensuel.References.lire(Vide) and not mensuel.References.lire(object())


def test_liste_des_joueurs_du_77_avec_les_valeurs(tmp_path):
    """Le fichier des valeurs dit aussi qui est du 77 : un adversaire absent de la liste est d'un autre
    département (repère « * » : estimation moins sûre)."""
    class Client:
        dossier = tmp_path
    mensuel.enregistrer(Client, {"a": {"2026-09": 1000}, "x": {"2026-09": 900}, mensuel.CLE_77: ["a", "b"]})
    lues = mensuel.References.lire(Client)
    assert lues.du_77() == {"a", "b"} and lues.valeur("x", "2026-09-10") == 900
    assert mensuel.References().du_77() == set()

"""Classement virtuel : parties de toutes les compétitions (objets JSON de même forme que l'API FFTT)."""

import json
from datetime import date

from test_effectif import VAIRES, FauxClient, _ecrans_vaires, _page_enregistree, _site
from ttvaires.fftt import API
from ttvaires.virtuel import analyser, classement, libelle_competition, recuperer_virtuel, url_parties

CHAMPIONNAT = {"id": 1, "name": "FED_Championnat de France par Equipes Masculin"}
TOP_JEUNE = {"id": 2, "name": "Top Jeune Departemental"}
COMPETITIONS = {1: {"nom": CHAMPIONNAT["name"], "coef": 1}, 2: {"nom": TOP_JEUNE["name"], "coef": 0.5}}


def _licence(lic, points=None, nom="NOM"):
    return {"identifier": lic, "points": points, "person": {"familyName": nom, "givenName": "Prénom"}} if lic else None


def _partie(id_, jour, dom, ext, gagnant="home", contest=CHAMPIONNAT, **autres):
    g = {"id": id_, "date": jour + "T00:00:00", "homePlayer": _licence(*dom), "awayPlayer": _licence(*ext),
         "winner": gagnant, "contest": contest, "doubleOpposition": False}
    g.update(autres)
    return g


def test_points_de_chaque_partie_avec_le_coefficient_de_la_competition():
    parties = [
        _partie(1, "2026-09-25", ("100", 800), ("9", 900)),                                    # victoire contre +100 : +10
        _partie(2, "2026-09-27", ("100", 800), ("8", 700), "away", TOP_JEUNE),                # défaite contre -100 : -8 x 0,5
        _partie(3, "2026-09-25", ("100", 800), ("9", 900), homeTeammatePlayer={"identifier": "7"}),  # double
        _partie(4, "2026-09-25", ("7", 600), ("9", 900)),                                     # partie d'un autre joueur
        _partie(5, "2026-09-26", ("100", 800), (None,)),                                      # adversaire absent : forfait
        _partie(6, "2026-09-26", ("100", 800), ("6", 750)),                                   # marquée non comptée
        _partie(7, "2026-06-15", ("100", 800), ("6", 750)),                                   # phase précédente
        _partie(8, "2026-09-28", ("100", 800), ("5", None)),                                  # adversaire sans points
    ]
    lignes, officiels, ecartees = analyser("100", parties, COMPETITIONS, {6: {"non_comptee": True}},
                                           "2026-07-01", "2026-12-31")
    assert [(l["id"], l["points"], l["coef"], l["championnat"]) for l in lignes] == [(1, 10, 1, True), (2, -4, 0.5, False)]
    assert lignes[1]["competition"] == "Top Jeune Departemental" and not lignes[1]["victoire"]
    assert ecartees == {"forfait": 1, "non comptée": 1, "points inconnus": 1}
    assert officiels.most_common(1)[0][0] == 800


def test_utilitaires():
    assert classement(899.5) == 8 and classement(480) == 5 and classement(None) is None
    assert libelle_competition("FED_Championnat de France par Equipes Féminin") == "Championnat par équipes F"
    assert libelle_competition("FED_Critérium Fédéral") == "Critérium Fédéral"


def test_classement_virtuel_de_bout_en_bout(tmp_path):
    """Liste des joueurs du dossier import ; Tom n'a joué qu'une compétition jeunes."""
    pages = _site(avec_listes=False)  # Léa (800) et Paul (900) alignés en Vaires 4
    dossier = tmp_path / "import"
    dossier.mkdir()
    _page_enregistree(dossier / "vaires.html", _ecrans_vaires("CATEGORY", "LICENCE_STATE"))
    parties = {
        "100": [_partie(11, "2026-09-25", ("100", 800), ("9", 900)),
                _partie(12, "2026-09-25", ("100", 800), ("9", 900), homeTeammatePlayer={"identifier": "200"})],
        "200": [_partie(12, "2026-09-25", ("100", 800), ("9", 900), homeTeammatePlayer={"identifier": "200"})],
        "300": [_partie(13, "2026-09-27", ("300", 700), ("8", 600), contest=TOP_JEUNE),
                _partie(14, "2026-06-13", ("300", 700), ("8", 600), "away", TOP_JEUNE)],
    }
    for lic, ps in parties.items():
        pages[url_parties(lic)] = json.dumps({"@context": "/api/contexts/Game", "hydra:member": ps})
    pages[f"{API}/contests/1"] = json.dumps({"@context": "/api/contexts/Contest", "name": CHAMPIONNAT["name"], "coefficient": 1})
    pages[f"{API}/contests/2"] = json.dumps({"@context": "/api/contexts/Contest", "name": TOP_JEUNE["name"], "coefficient": 0.5})
    pages[f"{API}/games/13"] = json.dumps({"@context": "/api/contexts/Game", "notCounted": False,
                                           "sportMatch": {"tour": {"division": {"name": "M15G - Cadets"}}}})

    d = recuperer_virtuel(FauxClient(pages), VAIRES, aujourdhui=date(2026, 10, 6), dossier_import=dossier)
    j = {x["id"]: x for x in d["joueurs"]}
    assert set(j) == {"100", "200", "300"}  # licence loisir et non réinscrit écartés
    assert (j["100"]["championnat"], j["100"]["virtuels"], j["100"]["equipe"]) == (10, 810, "V4")
    assert (j["200"]["officiels"], j["200"]["total"], j["200"]["virtuels"], j["200"]["parties"]) == (900, 0, 900, [])
    assert (j["300"]["autres"], j["300"]["virtuels"], j["300"]["categorie"]) == (2, 702, "S")
    assert j["300"]["parties"][0]["division"] == "M15G - Cadets"
    assert [x["id"] for x in d["joueurs"]] == ["200", "100", "300"]  # par points virtuels
    assert [(c["nom"], c["coef"]) for c in d["competitions"]] == [("Championnat par équipes M", 1), ("Top Jeune Departemental", 0.5)]
    assert d["source"]["origine"] == "import"

"""Classements des poules de toutes les équipes de Vaires : données, page et image."""

import json

import pytest

from ttvaires.adversaires import derniere_journee, donnees_classements
from ttvaires.rendu import GABARIT_CLASSEMENTS, generer_html


def _ligne(rang, libelle, club, points, v, n, d):
    return {"rang": rang, "libelle": libelle, "club": club, "numero": 1, "points": points, "joues": v + n + d,
            "v": v, "n": n, "d": d, "pg": 10 * v, "pp": 10 * d}


def _donnees(nb_equipes=3):
    equipes = []
    for i in range(1, nb_equipes + 1):
        equipes.append({
            "id": f"v{i}", "libelle": f"VAIRES CVTT {i}", "nom_court": f"Vaires {i}", "numero": i, "championnat": "M",
            "division": "Départementale 2", "poule": f"Poule {i}", "jour": "vendredi",
            "rencontres": [{"journee": 1, "score": [26, 16]}, {"journee": 2, "score": [20, 22]}, {"journee": 3, "score": None}],
            "classement": [_ligne(1, "COMBS SENART TT 7", "08770426", 6, 2, 0, 0),
                           _ligne(2, f"VAIRES CVTT {i}", "08770250", 4, 1, 0, 1),
                           _ligne(3, "TT ST PATHUS 3", "08771000", 2, 0, 0, 2)],
            "composition_probable": [{"nom": "DELOBELLE", "prenom": "Jérôme"}],
        })
    return {"genere_le": "2026-10-20T15:44", "saison": "2026-2027", "phase": 1,
            "club": {"numero": "08770250", "nom": "CVTT VAIRES"}, "equipes": equipes}


def test_donnees_sans_aucun_nom_de_joueur():
    c = donnees_classements(_donnees())
    assert derniere_journee(_donnees()) == 2 and c["journee"] == 2
    assert [p["equipe"] for p in c["poules"]] == ["Vaires 1", "Vaires 2", "Vaires 3"]
    assert [l["nous"] for l in c["poules"][0]["lignes"]] == [False, True, False]
    assert "DELOBELLE" not in json.dumps(c)
    archive = _donnees()
    archive["date_reference"] = "2026-10-15"
    assert donnees_classements(archive)["date_reference"] == "2026-10-15"


def test_page(tmp_path):
    page = generer_html(donnees_classements(_donnees()), tmp_path / "classements_vaires.html", GABARIT_CLASSEMENTS)
    html = page.read_text(encoding="utf-8")
    assert "__DONNEES_JSON__" not in html and "COMBS SENART TT 7" in html and "DELOBELLE" not in html


def test_image_deux_par_rangee_la_ligne_de_vaires_en_rouge(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image
    from ttvaires import classements
    assert classements.sous_titre(donnees_classements(_donnees())) == "APRÈS LA JOURNÉE 02   •   PHASE 1   •   2026–2027"
    [(chemin, titre)] = classements.image_classements(_donnees(3), None, tmp_path)
    assert chemin.name == "classements_poules.png" and titre == "Classements des poules après la J2"
    with Image.open(chemin) as img:
        largeur, hauteur = img.size
        assert largeur == classements.LARGEUR
        # Ligne de Vaires (2e) de la première carte : rouge
        y = 338 + classements.HAUT_TETE + classements.HAUT_COLONNES + classements.HAUT_LIGNE + 4
        r, g, b = img.getpixel((300, y))[:3]
        assert r > 150 and g < 60 and b < 70
    # Une équipe de plus : une rangée de plus
    [(chemin, _)] = classements.image_classements(_donnees(5), None, tmp_path)
    with Image.open(chemin) as img:
        assert img.size[1] > hauteur
    # Logo fourni avec l'outil (rouge), remplacé par celui du dossier import s'il existe
    with Image.open(chemin) as img:
        r, g, b = img.getpixel((165, 60))[:3]
        assert r > 180 and g < 80
    # Logo du club pris dans le dossier import
    imports = tmp_path / "import"
    imports.mkdir()
    Image.new("RGBA", (300, 300), (10, 200, 10, 255)).save(imports / "logo_club.png")
    [(chemin, _)] = classements.image_classements(_donnees(3), imports, tmp_path)
    with Image.open(chemin) as img:
        r, g, b = img.getpixel((165, 116))[:3]
        assert g > 150 and r < 80
    assert classements.image_classements({**_donnees(0)}, None, tmp_path) == []
    assert not list(tmp_path.glob("classements_*.png"))  # l'ancienne image est retirée


def test_sets_et_points_des_sets_cumules_dans_le_classement():
    """PG / PP : cumul des scores des rencontres (comme la FFTT) ; SG / SP et PM / PE : sets et points
    des sets additionnés partie par partie, doubles compris."""
    from ttvaires.adversaires import classement_poule

    def equipe(nom, club):
        return {"opponent": {"team": {"name": nom, "position": 4, "clubs": [{"code": club, "id": 1, "name": nom}]}}}

    poule = {"poolOpponents": [equipe("VAIRES CVTT 4", "08770250"), equipe("DAMMARTIN CTT 4", "08770937")]}
    detail = {1: {"homeOpponent": {"team": {"name": "VAIRES CVTT 4"}}, "awayOpponent": {"team": {"name": "DAMMARTIN CTT 4"}},
                  "homeGamePoints": 21, "awayGamePoints": 21, "homePoints": 2, "awayPoints": 2,
                  "games": [{"winner": "home", "sets": [{"homeScore": 12, "awayScore": 10}, {"homeScore": 11, "awayScore": 6},
                                                         {"homeScore": 11, "awayScore": 9}]},
                            {"winner": "away", "doubleOpposition": True,
                             "sets": [{"homeScore": 1, "awayScore": 11}, {"homeScore": 9, "awayScore": 11},
                                      {"homeScore": 12, "awayScore": 14}]},
                            {"winner": "away", "sets": []}]}}
    vaires, dammartin = sorted(classement_poule(poule, [{"id": 1}], detail), key=lambda e: e["libelle"], reverse=True)
    assert (vaires["pg"], vaires["pp"], vaires["n"]) == (21, 21, 1)
    assert (vaires["sg"], vaires["sp"], vaires["pm"], vaires["pe"]) == (3, 3, 56, 61)
    assert (dammartin["sg"], dammartin["sp"], dammartin["pm"], dammartin["pe"]) == (3, 3, 61, 56)
    assert vaires["sans_detail"] == dammartin["sans_detail"] == 1      # partie jouée sans le détail des sets


def test_totaux_d_une_feuille_de_match():
    from ttvaires.resultats import totaux_manches
    parties = [{"sets": [[12, 10], [11, 6], [11, 9]], "gagne": True, "forfait": False, "double": False},
               {"sets": [[1, 11], [9, 11], [12, 14]], "gagne": False, "forfait": False, "double": True},
               {"sets": [], "gagne": False, "forfait": True, "double": False}]
    assert totaux_manches(parties) == {"manches": [3, 3], "points": [56, 61], "sans_detail": 0}

"""Progression des joueurs : points virtuels cumulés semaine après semaine, page et images."""

import pytest

from ttvaires.progression import donnees_progression, tendance


def _virtuel():
    p = lambda jour, pts, v=True: {"date": jour, "points": pts, "victoire": v}
    return {"genere_le": "2026-11-11T10:00", "saison": "2026-2027", "phase": 1, "club": {"nom": "CVTT VAIRES"}, "joueurs": [
        {"id": "1", "nom": "DUPOND", "prenom": "Paul", "equipe": "V1", "officiels": 800, "v": 3, "d": 1, "parties": [
            p("2026-09-25", 10), p("2026-09-26", 2.5), p("2026-10-17", -3, False), p("2026-11-07", 6.5)]},
        {"id": "2", "nom": "DURAND", "prenom": "Léa", "equipe": "V1 F", "officiels": 900, "v": 0, "d": 0, "parties": []},
        {"id": "3", "nom": "SANS", "prenom": "Points", "equipe": None, "officiels": None, "v": 0, "d": 0, "parties": []},
    ]}


def test_points_virtuels_semaine_apres_semaine():
    d = donnees_progression(_virtuel())
    # Une semaine avant la première partie (départ), jusqu'à la semaine de la mise à jour (lundi 09/11)
    assert d["semaines"][0] == "2026-09-14" and d["semaines"][1] == "2026-09-21" and d["semaines"][-1] == "2026-11-09"
    j = {x["id"]: x for x in d["joueurs"]}
    assert "3" not in j  # sans points officiels : pas de courbe
    a = j["1"]
    assert a["serie"][0] == 800 and a["serie"][1] == 812.5  # deux parties la même semaine
    assert a["serie"][-1] == 816 and a["total"] == 16
    assert a["parties"][1] == 2 and a["victoires"][1] == 2
    assert a["recent"] == 6.5 and a["tendance"] == "progresse"  # 4 dernières semaines : 809,5 (sem. du 12/10) -> 816
    assert j["2"]["serie"] == [900] * len(d["semaines"]) and j["2"]["tendance"] is None
    assert [x["id"] for x in d["joueurs"]] == ["2", "1"]  # par points virtuels
    assert tendance(5) == "progresse" and tendance(-5) == "régresse" and tendance(4.9) == "stable"


def test_archive_et_phase_sans_partie():
    v = _virtuel()
    v["date_reference"] = "2026-10-20"  # archive : courbe arrêtée à cette date (les parties sont déjà filtrées)
    assert donnees_progression(v)["semaines"][-1] == "2026-11-02"  # la dernière partie fixe la fin si elle est après
    vide = {"genere_le": "2026-07-02T10:00", "joueurs": [{"id": "1", "officiels": 500, "parties": []}]}
    assert donnees_progression(vide)["semaines"] == [] and donnees_progression(vide)["joueurs"] == []


def test_une_image_par_equipe(tmp_path):
    pytest.importorskip("PIL.ImageDraw")
    from ttvaires.images import images_progression

    sorties = images_progression(donnees_progression(_virtuel()), tmp_path)
    # Vaires 1 F : une seule joueuse, sans partie -> pas d'image ; titres sans nom de joueur
    assert [(c.name, t) for c, t in sorties] == [("progression_V1.png", "Progression · Vaires 1")]
    assert images_progression({"semaines": [], "joueurs": []}, tmp_path) == []

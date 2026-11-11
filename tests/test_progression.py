"""Progression des joueurs : points virtuels cumulés semaine après semaine depuis le 1er septembre."""

import pytest

from ttvaires.progression import donnees_progression, lecture, tendance

p = lambda jour, pts, v=True, ecart=0: {"date": jour, "points": pts, "victoire": v, "ecart": ecart}


def _virtuel():
    return {"genere_le": "2026-11-11T10:00", "saison": "2026-2027", "phase": 1, "debut": "2026-07-01",
            "club": {"nom": "CVTT VAIRES"}, "joueurs": [
        {"id": "1", "nom": "DUPOND", "prenom": "Paul", "equipe": "V1", "officiels": 800, "v": 4, "d": 1, "parties": [
            p("2026-08-15", 4),  # tournoi d'été : avant la saison, compté dans le départ
            p("2026-09-25", 10, ecart=120), p("2026-09-26", 2.5), p("2026-10-17", -3, False, ecart=-40), p("2026-11-07", 6.5, ecart=30)]},
        {"id": "2", "nom": "DURAND", "prenom": "Léa", "equipe": "V1 F", "officiels": 900, "v": 0, "d": 0, "parties": []},
        {"id": "3", "nom": "SANS", "prenom": "Points", "equipe": None, "officiels": None, "v": 0, "d": 0, "parties": []},
    ]}


def test_progression_depuis_le_1er_septembre():
    d = donnees_progression(_virtuel())
    assert d["debut_saison"] == "2026-09-01"
    # Départ : la semaine avant celle du 1er septembre (lundi 31/08) ; fin : semaine de la mise à jour
    assert d["semaines"][:2] == ["2026-08-24", "2026-08-31"] and d["semaines"][-1] == "2026-11-09"
    j = {x["id"]: x for x in d["joueurs"]}
    assert "3" not in j  # sans points officiels : pas de courbe
    a = j["1"]
    assert a["serie"][0] == 804  # points au 1er septembre : officiels + tournoi d'été
    assert a["serie"][-1] == 820 and a["total"] == 16  # progression depuis le 1er septembre
    i = d["semaines"].index("2026-09-21")
    assert a["parties"][i] == 2 and a["victoires"][i] == 2 and a["perfs"][i] == 1
    assert (a["v"], a["d"], a["nb_perfs"], a["nb_contres"]) == (3, 1, 2, 1)  # sans le tournoi d'été
    assert a["tendance"] == "progresse" and a["lecture"] == "progression avec 2 perfs"
    assert j["2"]["serie"] == [900] * len(d["semaines"]) and j["2"]["tendance"] is None and j["2"]["lecture"] is None
    assert tendance(10) == "progresse" and tendance(-10) == "régresse" and tendance(9.9) == "stable"
    b = lambda total, pf, ct: {"v": 1, "d": 1, "total": total, "nb_perfs": pf, "nb_contres": ct}
    assert lecture(b(-20, 0, 0)) == "baisse sans contre : perdu contre plus fort" and lecture(b(-20, 1, 2)) == "baisse avec 2 contres"


def test_en_phase_2_la_courbe_reprend_la_phase_1():
    v = {"genere_le": "2027-01-20T10:00", "saison": "2026-2027", "phase": 2, "debut": "2027-01-01", "joueurs": [
        {"id": "1", "nom": "DUPOND", "prenom": "Paul", "equipe": "V1", "officiels": 840, "parties": [p("2027-01-15", 5)],
         "phase1": {"officiels": 800, "parties": [p("2026-09-25", 10), p("2026-12-12", 20)]}}]}
    d = donnees_progression(v)
    a = d["joueurs"][0]
    assert a["serie"][0] == 800  # départ : points de la phase 1 au 1er septembre
    assert a["serie"][d["semaines"].index("2026-12-07")] == 830  # fin de la phase 1 (virtuels)
    assert a["serie"][d["semaines"].index("2026-12-28")] == 840  # semaine du 1er janvier : nouveaux points officiels
    assert a["serie"][-1] == 845 and a["total"] == 45 and (a["v"], a["d"]) == (3, 0)


def test_archive_et_saison_sans_partie():
    v = _virtuel()
    v["date_reference"] = "2026-10-20"
    assert donnees_progression(v)["semaines"][-1] == "2026-11-02"  # la dernière partie fixe la fin si elle est après
    vide = {"genere_le": "2026-07-02T10:00", "saison": "2026-2027", "joueurs": [{"id": "1", "officiels": 500, "parties": []}]}
    assert donnees_progression(vide)["semaines"] == [] and donnees_progression(vide)["joueurs"] == []


def test_une_image_par_equipe(tmp_path):
    pytest.importorskip("PIL.ImageDraw")
    from ttvaires.images import images_progression

    sorties = images_progression(donnees_progression(_virtuel()), tmp_path)
    # Vaires 1 F : une seule joueuse, sans partie -> pas d'image ; titres sans nom de joueur
    assert [(c.name, t) for c, t in sorties] == [("progression_V1.png", "Progression · Vaires 1")]
    assert images_progression({"semaines": [], "joueurs": []}, tmp_path) == []

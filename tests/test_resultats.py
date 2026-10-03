"""Calcul des points virtuels et synthèse par journée (cas réel de la J1 de Vaires 3, noms fictifs)."""

from ttvaires.resultats import points_partie, synthese


def test_bareme_fftt():
    assert points_partie(780, 752, True) == 5.5     # victoire normale, écart 28
    assert points_partie(780, 1014, True) == 17     # victoire anormale, écart 234
    assert points_partie(961, 1014, False) == -4    # défaite normale, écart 53
    assert points_partie(768, 706, False) == -7     # défaite anormale, écart 62
    assert points_partie(500, 916, False) == 0      # défaite normale, écart 416
    assert points_partie(1410, 800, True) == 0      # victoire normale, écart 610
    assert points_partie(800, 1410, True) == 40     # victoire anormale, écart 610
    assert points_partie(900, 900, False) == -5     # même nombre de points


def _partie(joueur, points, adversaire, points_adv, victoire, journee=1, equipe="VAIRES 3", ordre=2):
    return {"journee": journee, "date": "2026-09-25", "equipe": equipe, "ordre": ordre, "adversaires": "CLUB X 2",
            "licence": joueur, "joueur": joueur, "points": points, "adversaire": adversaire,
            "points_adv": points_adv, "ecart": points_adv - points, "victoire": victoire,
            "gain": points_partie(points, points_adv, victoire)}


def test_synthese_journee_et_total():
    # Delobelle : 3 victoires (écarts -28, -74, +234) = +27,5 (valeurs de la feuille de match réelle).
    parties = [_partie("DELOBELLE", 780, "A", 752, True), _partie("DELOBELLE", 780, "B", 706, True),
               _partie("DELOBELLE", 780, "C", 1014, True),
               _partie("RIGUET", 500, "E", 916, False), _partie("RIGUET", 500, "B", 706, True),
               _partie("RIGUET", 500, "C", 1014, False),
               _partie("DELOBELLE", 807, "D", 900, False, journee=2)]
    lignes, cumuls = synthese(parties)
    j1 = {l["joueur"]: l for l in lignes if l["journee"] == 1}
    assert (j1["DELOBELLE"]["delta"], j1["DELOBELLE"]["v"], j1["DELOBELLE"]["matchs"]) == (27.5, 3, 3)
    assert j1["DELOBELLE"]["meilleure"] == 234 and j1["DELOBELLE"]["apres"] == 807.5
    assert (j1["RIGUET"]["delta"], j1["RIGUET"]["meilleure"]) == (17, 206)
    j2 = next(l for l in lignes if l["journee"] == 2)
    assert j2["delta"] == -4 and j2["meilleure"] is None and j2["total"] == 23.5
    # Classement virtuel cumulé : 780 + 27,5 - 4 (et non 807 - 4 ni 780 - 4).
    assert j2["points"] == 780 and j2["apres"] == 803.5
    c = next(c for c in cumuls if c["joueur"] == "DELOBELLE")
    assert c["journees"] == {1: 27.5, 2: -4} and c["total"] == 23.5 and (c["v"], c["matchs"]) == (3, 4)
    assert c["points"] == 780 and c["virtuels"] == 803.5


def test_joueuse_deux_rencontres_dans_la_journee():
    # Vendredi en VAIRES 3 (masculin), samedi en VAIRES 1 F : les deux rencontres comptent.
    vendredi = _partie("LEA", 768, "A", 706, True, journee=2, equipe="VAIRES 3", ordre=2)
    vendredi["date"] = "2026-10-02"
    samedi = _partie("LEA", 768, "B", 900, True, journee=2, equipe="VAIRES 1 F", ordre=6)
    samedi["date"] = "2026-10-03"
    lignes, cumuls = synthese([samedi, vendredi])
    v3 = next(l for l in lignes if l["equipe"] == "VAIRES 3")
    f1 = next(l for l in lignes if l["equipe"] == "VAIRES 1 F")
    assert (v3["delta"], f1["delta"]) == (5, 10)          # +5 (normale, écart 62) et +10 (anormale, écart 132)
    assert v3["apres"] == 773 and f1["apres"] == 783      # le samedi part des points virtuels du vendredi
    assert (v3["total"], f1["total"]) == (5, 15)
    assert f1["autres"] == [{"equipe": "VAIRES 3", "date": "2026-10-02", "delta": 5}]
    assert cumuls[0]["equipes"] == ["VAIRES 3", "VAIRES 1 F"] and cumuls[0]["journees"] == {2: 15}

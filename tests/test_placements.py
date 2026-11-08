from ttvaires.placements import EVITE, LIBELLES, placements, position, resume_joueur

ORDRE_4 = "AW BX CY DZ AX BW DY CZ AY CW DX BZ".split()


def test_positions_et_adversaires_jamais_rencontres():
    assert [position(l) for l in "ABCDWXYZ"] == [1, 2, 3, 4, 1, 2, 3, 4]
    assert [position(l, 3) for l in "ABCXYZ"] == [1, 2, 3, 1, 2, 3]
    assert position("?") is None
    # Ordre des parties relevé sur les feuilles : chaque position évite une position adverse.
    for lettre in "ABCD":
        adversaires = {position(p[1]) for p in ORDRE_4 if p[0] == lettre}
        assert {1, 2, 3, 4} - adversaires == {EVITE[position(lettre)]}


def _compo(journee, date_, lettres, points, domicile=True, contre="X 1", format_=4):
    return {"journee": journee, "date": date_, "joueurs": list(lettres), "lettres": lettres, "points": points,
            "domicile": domicile, "contre": contre, "format": format_}


def test_placements_des_rencontres_jouees_avant():
    equipe = {"compositions": [
        _compo(1, "2026-09-25", {"a": "A", "b": "B", "c": "C", "d": "D"}, {"a": 900, "b": 800, "c": 700, "d": 600}),
        _compo(2, "2026-10-02", {"a": "Y", "b": "W", "c": "X", "e": "Z"}, {"a": 900, "b": 800, "c": 700, "e": 650},
               domicile=False, contre="Y 2"),
        _compo(3, "2026-10-16", {"a": "A"}, {"a": 900}),  # après la rencontre analysée : ignorée
        {"journee": 1, "date": "2026-09-20", "joueurs": ["z"]},  # feuille sans lettres (données anciennes)
    ]}
    p = placements(equipe, 3, "2026-10-16")
    assert p["format"] == 4 and p["libelles"] == LIBELLES[4]
    assert [r["places"] for r in p["rencontres"]] == [["a", "b", "c", "d"], ["b", "c", "a", "e"]]
    assert [(r["journee"], r["domicile"], r["contre"], r["par_points"]) for r in p["rencontres"]] == [
        (1, True, "X 1", True), (2, False, "Y 2", False)]
    assert p["joueurs"]["a"] == [1, 0, 1, 0] and (p["par_points"], p["avec_points"]) == (1, 2)
    assert resume_joueur(p["joueurs"]["a"], p["libelles"]) == "A/W · C/Y"
    assert resume_joueur([0, 2, 1, 0], p["libelles"]) == "B/X ×2 · C/Y"
    assert placements(equipe, 1, "2026-09-25") is None and placements(None, 2) is None


def test_placements_a_trois_joueurs():
    equipe = {"compositions": [_compo(1, "2026-09-26", {"a": "X", "b": "Y", "c": "Z"}, {"a": 600, "b": 500, "c": 500},
                                      domicile=False, format_=3)]}
    p = placements(equipe, 2)
    assert p["libelles"] == ["A/X", "B/Y", "C/Z"] and p["rencontres"][0]["places"] == ["a", "b", "c"]
    assert p["rencontres"][0]["par_points"] is True

from ttvaires.brulage import analyse_rencontre, enrichir, equipe_max


def _joueur(jid, points, **extra):
    return {"id": jid, "nom": jid, "prenom": "", "points": points, **extra}


def _club(joueurs, equipes):
    """equipes : {numero: [(journee, date, [ids]), ...]} (championnat masculin)."""
    return {
        "numero": "08770000",
        "nom": "CLUB TEST",
        "joueurs": joueurs,
        "equipes": [
            {
                "libelle": f"CLUB {n}",
                "numero": n,
                "championnat": "M",
                "compositions": [{"journee": j, "date": d, "joueurs": ids} for j, d, ids in compos],
            }
            for n, compos in equipes.items()
        ],
    }


def _parts(*numeros):
    return [{"numero": n} for n in numeros]


def test_equipe_max_est_le_deuxieme_plus_petit_numero():
    assert equipe_max(_parts()) is None
    assert equipe_max(_parts(16)) is None
    assert equipe_max(_parts(16, 18)) == 18
    assert equipe_max(_parts(18, 16)) == 18
    assert equipe_max(_parts(1, 1)) == 1
    assert equipe_max(_parts(5, 1, 3)) == 3


def test_brule_apres_deux_matchs_en_equipes_plus_fortes():
    club = _club(
        [_joueur("A", 1500)],
        {16: [(1, "2026-09-25", ["A"])], 17: [(2, "2026-10-02", ["A"])], 18: []},
    )
    a18 = analyse_rencontre(club, "M", 18, 3, "2026-10-09")
    assert [b["id"] for b in a18["brules"]] == ["A"]
    # En équipe 17, un seul match en équipe plus forte (16) : il peut encore jouer.
    a17 = analyse_rencontre(club, "M", 17, 3, "2026-10-09")
    assert a17["brules"] == []
    assert [h["id"] for h in a17["habitues"]] == ["A"]


def test_seuls_les_matchs_avant_la_rencontre_comptent():
    club = _club(
        [_joueur("A", 1500)],
        {16: [(1, "2026-09-25", ["A"]), (3, "2026-10-09", ["A"])], 18: []},
    )
    # À la J2, A n'a joué qu'une fois en équipe 16 : c'est un renfort possible.
    a = analyse_rencontre(club, "M", 18, 2, "2026-10-02")
    assert a["brules"] == []
    assert [r["id"] for r in a["renforts"]] == ["A"]


def test_regle_j2():
    club = _club(
        [_joueur("A", 1500), _joueur("B", 1400), _joueur("C", 900)],
        {16: [(1, "2026-09-25", ["A", "B"])], 18: [(1, "2026-09-25", ["C"])]},
    )
    a = analyse_rencontre(club, "M", 18, 2, "2026-10-02")
    assert a["regle_j2"] is True
    assert all(r["j1_plus_forte"] for r in a["renforts"])
    # À la J3, la règle ne s'applique plus.
    assert analyse_rencontre(club, "M", 18, 3, "2026-10-09")["regle_j2"] is False


def test_un_seul_match_par_journee():
    club = _club(
        [_joueur("A", 1500)],
        {20: [(3, "2026-10-09", ["A"])], 18: []},
    )
    a = analyse_rencontre(club, "M", 18, 3, "2026-10-10")
    assert a["brules"] == [{"id": "A", "equipes": [20], "raison": "a déjà joué la J3 en équipe 20"}]


def test_non_renouveles_exclus_et_feminin_reserve_aux_filles():
    club = _club(
        [_joueur("A", 1500, renouvele=False), _joueur("B", 800, sexe="F"), _joueur("C", 900, sexe="M")],
        {},
    )
    assert analyse_rencontre(club, "M", 1, 1)["non_alignes"] == ["C", "B"]
    assert analyse_rencontre(club, "F", 1, 1)["non_alignes"] == ["B"]


def test_composition_probable_habitues_puis_equipe_du_dessous():
    joueurs = [_joueur(x, p) for x, p in [("A", 1400), ("B", 1300), ("C", 1200), ("D", 1100), ("E", 1000)]]
    club = _club(
        joueurs,
        {
            17: [(1, "2026-09-25", ["A", "B", "C"])],
            18: [(1, "2026-09-25", ["D", "E"])],
        },
    )
    a = analyse_rencontre(club, "M", 17, 2, "2026-10-02")
    assert a["taille"] == 3
    assert a["probable"] == ["A", "B", "C"]
    # Il manque un joueur en équipe 17 : on complète avec l'équipe du dessous.
    club["equipes"][0]["compositions"][0]["joueurs"] = ["A", "B", "C", "X"]
    a = analyse_rencontre(club, "M", 17, 2, "2026-10-02")
    assert a["probable"] == ["A", "B", "C", "D"]


def test_enrichir_ajoute_analyse_et_composition_alignee():
    club = _club([_joueur("A", 1500)], {18: [(1, "2026-09-25", ["A"])]})
    donnees = {
        "clubs": {club["numero"]: club},
        "equipes": [{
            "libelle": "VAIRES 3",
            "championnat": "M",
            "rencontres": [
                {"journee": 1, "date": "2026-09-25",
                 "adversaire": {"club": club["numero"], "libelle": "CLUB 18"}},
                {"journee": 2, "date": "2026-10-02", "adversaire": None},
            ],
        }],
    }
    enrichir(donnees)
    r1, r2 = donnees["equipes"][0]["rencontres"]
    assert r1["adversaire"]["numero"] == 18
    assert r1["composition_adverse"] == ["A"]
    assert "analyse" not in r2
    assert club["parcours"]["A"]["M"]["matchs"] == [{"j": 1, "n": 18, "d": "2026-09-25"}]

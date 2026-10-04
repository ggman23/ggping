"""Structure de la page adversaires construite depuis l'API FFTT (objets JSON fictifs de même forme)."""

from datetime import date

from ttvaires.adversaires import classement_poule, equipes_et_compositions
from ttvaires.fftt import bornes_phase, libelle_division, phase_et_saison


def _equipe(nom, club, position=None):
    return {"name": nom, "position": position, "clubs": [{"identifier": club, "id": 1, "name": f"CLUB {club}"}]}


def _rencontre(id_, dom, ext, journee=1, date_="2026-09-25", feminin=False, **detail):
    contest = "FED_Championnat de France par Equipes " + ("Féminin" if feminin else "Masculin")
    r = {"id": id_, "homeOpponent": {"team": dom}, "awayOpponent": {"team": ext} if ext else None,
         "day": {"position": journee}, "date": date_ + "T00:00:00", "division": {"name": "DEP 2 Ph1", "contest": {"name": contest}}}
    r.update(detail)
    return r


def _licence(lic, nom, prenom, points):
    return {"player": {"identifier": lic, "points": points, "person": {"familyName": nom, "givenName": prenom}}}


def test_saison_phase_et_libelles():
    assert phase_et_saison(date(2026, 10, 3)) == (1, "2026-2027")
    assert phase_et_saison(date(2027, 2, 1)) == (2, "2026-2027")
    assert bornes_phase(date(2026, 10, 3)) == ("2026-07-01", "2026-12-31")
    assert bornes_phase(date(2027, 2, 1)) == ("2027-01-01", "2027-06-30")
    assert libelle_division("DEP 2 Ph1") == "Départementale 2"
    assert libelle_division("L08_R2") == "Régionale 2"
    assert libelle_division("FED_Nationale 2") == "Nationale 2"


def test_classement_poule():
    a, b, c = _equipe("ALPHA 1", "1", 1), _equipe("BETA 2", "2", 2), _equipe("VAIRES CVTT 3", "08770250", 3)
    poule = {"poolOpponents": [{"opponent": {"team": t}} for t in (a, b, c)]}
    rencontres = [_rencontre(1, a, c), _rencontre(2, b, None), _rencontre(3, c, b, journee=2, date_="2026-10-02")]
    detail = {
        1: {"homeOpponent": {"team": a}, "awayOpponent": {"team": c}, "homePoints": 3, "awayPoints": 1,
            "homeGamePoints": 27, "awayGamePoints": 15},
        3: {"homeOpponent": {"team": c}, "awayOpponent": {"team": b}, "homePoints": 2, "awayPoints": 2,
            "homeGamePoints": 21, "awayGamePoints": 21},
    }
    cl = {e["libelle"]: e for e in classement_poule(poule, rencontres, detail)}
    assert (cl["ALPHA 1"]["rang"], cl["ALPHA 1"]["points"], cl["ALPHA 1"]["v"]) == (1, 3, 1)
    assert (cl["VAIRES CVTT 3"]["points"], cl["VAIRES CVTT 3"]["joues"], cl["VAIRES CVTT 3"]["n"], cl["VAIRES CVTT 3"]["d"]) == (3, 2, 1, 1)
    assert (cl["VAIRES CVTT 3"]["pg"], cl["VAIRES CVTT 3"]["pp"]) == (36, 48)
    assert cl["BETA 2"]["rang"] == 3 and cl["VAIRES CVTT 3"]["rang"] == 2


def test_equipes_et_compositions():
    l12, l13 = _equipe("LOGNES EP 12", "08771184"), _equipe("LOGNES EP 13", "08771184")
    x, f1 = _equipe("AUTRE 4", "9"), _equipe("LOGNES EP 1", "08771184")
    rencontres = [
        _rencontre(10, l12, x), _rencontre(11, x, l13), _rencontre(12, l12, x, journee=2, date_="2026-10-02"),
        _rencontre(20, f1, x, date_="2026-09-26", feminin=True),
    ]
    detail = {
        10: {"day": {"position": 1}, "date": "2026-09-25T00:00:00",
             "homeSheetMatches": [_licence("1", "DUPONT", "Jean", 900), _licence("2", "MARTIN", "Léa", 800)]},
        11: {"day": {"position": 1}, "date": "2026-09-25T00:00:00", "awaySheetMatches": [_licence("3", "PETIT", "Luc", 700)]},
        20: {"day": {"position": 1}, "date": "2026-09-26T00:00:00", "homeSheetMatches": [_licence("2", "MARTIN", "Léa", 800)]},
    }
    equipes, joueurs = equipes_et_compositions("08771184", rencontres, detail, {"M"})
    assert [(e["libelle"], e["numero"], e["compositions"]) for e in equipes] == [
        ("LOGNES EP 12", 12, [{"journee": 1, "date": "2026-09-25", "joueurs": ["1", "2"]}]),  # J2 pas encore saisie
        ("LOGNES EP 13", 13, [{"journee": 1, "date": "2026-09-25", "joueurs": ["3"]}]),
    ]
    assert joueurs["1"]["classement"] == 9 and joueurs["1"]["sexe"] is None
    # Championnat féminin demandé aussi : l'équipe féminine apparaît et la joueuse est marquée F.
    equipes, joueurs = equipes_et_compositions("08771184", rencontres, detail, {"M", "F"})
    assert [e["libelle"] for e in equipes if e["championnat"] == "F"] == ["LOGNES EP 1"]
    assert joueurs["2"]["sexe"] == "F"

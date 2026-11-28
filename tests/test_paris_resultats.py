"""Championnat de Paris (28/11) : rencontres, feuilles de match (groupes de 3 joueurs), résultats des joueurs et
classement de la poule lus dans l'API comme ceux du championnat de France ; pages avec le sélecteur de championnat
et images à part (paris_...). Objets JSON fictifs de même forme que l'API, noms fictifs."""

import json
from datetime import date

import pytest

from test_effectif import FauxClient
from ttvaires import fftt, rendu
from ttvaires.adversaires import donnees_classements, equipes_du_championnat
from ttvaires.resultats import donnees_page, groupes_des_parties, points_partie, recuperer_parties, recuperer_rencontres

VAIRES = "08770250"


def _equipe(nom, club, position):
    return {"name": nom, "position": position, "clubs": [{"identifier": club, "id": 12770250 if club == VAIRES else 5, "name": f"CLUB {club}"}]}


NOUS, EUX = _equipe("VAIRES CVTT (1)", VAIRES, 1), _equipe("NOGENT TT (1)", "08940524", 7)
FRANCE = _equipe("VAIRES CVTT 2", VAIRES, 2)


def _joueur(lic, nom, points):
    return {"identifier": lic, "points": points, "person": {"familyName": nom, "givenName": "Fictif"}}


# Vaires : 9 joueurs (1400 à 600 points), Nogent : 9 joueurs ; groupe k : nos joueurs 3k-2..3k contre les leurs
NOS = [_joueur(str(i), f"VAIRIEN{i}", 1500 - 100 * i) for i in range(1, 10)]
LEURS = [_joueur(str(10 + i), f"NOGENTAIS{i}", 1480 - 100 * i) for i in range(1, 10)]


def _parties(melanger=False):
    jeux = []
    for k in range(3):
        for a in NOS[3 * k:3 * k + 3]:
            for b in LEURS[3 * k:3 * k + 3]:
                gagne = int(a["identifier"]) % 3 != 0  # deux victoires sur trois par joueur
                jeux.append({"homePlayer": a, "awayPlayer": b, "winner": "home" if gagne else "away", "doubleOpposition": False,
                             "sets": [{"homeScore": 11, "awayScore": 7}] * 3 if gagne else [{"homeScore": 6, "awayScore": 11}] * 3})
    return jeux[18:] + jeux[:18] if melanger else jeux


def _rencontre(id_, dom, ext, journee, date_, contest, poule, division):
    return {"id": id_, "homeOpponent": {"team": dom}, "awayOpponent": {"team": ext}, "day": {"position": journee},
            "date": date_ + "T00:00:00", "time": "1970-01-01T20:30:00", "pool": {"id": poule},
            "division": {"name": division, "contest": {"name": contest}}}


PARIS = _rencontre(101, NOUS, EUX, 1, "2026-11-27", "L08_Championnat de Paris IDF", 55, "L08_Honneur")
PARIS_J2 = _rencontre(102, EUX, NOUS, 2, "2027-01-08", "L08_Championnat de Paris IDF", 55, "L08_Honneur")
CHAMP_FR = _rencontre(201, FRANCE, EUX, 5, "2026-11-20", "FED_Championnat de France par Equipes Masculin", 66, "DEP 2 Ph1")


def _site(melanger=False):
    jeux = _parties(melanger)
    gagnees = [sum(1 for g in jeux[i * 9:(i + 1) * 9] if g["winner"] == "home") for i in range(3)] if not melanger else None
    feuille = {**PARIS, "games": jeux, "homeGamePoints": 6 * 6 + 6 * 5 + 6 * 4, "awayGamePoints": 3 * 6 + 3 * 5 + 3 * 4,
               "homePoints": 3, "awayPoints": 1, "@context": "x",
               "homeSheetMatches": [{"identifier": "ABCDEFGHI"[i], "player": j} for i, j in enumerate(NOS)],
               "awaySheetMatches": [{"identifier": "UVWXYZRST"[i], "player": j} for i, j in enumerate(LEURS)]}
    assert gagnees in (None, [6, 6, 6])
    liste = {"@context": "/api/contexts/SportMatch", "hydra:member": [CHAMP_FR, PARIS, PARIS_J2]}
    poule = {"@context": "/api/contexts/SportMatch", "hydra:member": [PARIS, PARIS_J2]}
    return {
        f"{fftt.API}/sport_matches?{fftt._q('pool.id')}=55": json.dumps(poule),  # avant la liste du club (préfixes)
        f"{fftt.API}/sport_matches/101": json.dumps(feuille),
        f"{fftt.API}/sport_matches/201": json.dumps({**CHAMP_FR, "@context": "x", "homeGamePoints": 22, "awayGamePoints": 20,
                                                     "games": [], "homeSheetMatches": [{}]}),
        f"{fftt.API}/sport_matches?": json.dumps(liste),
        f"{fftt.API}/pools/55": json.dumps({"@context": "x", "name": "1", "poolOpponents": [
            {"opponent": {"team": NOUS}}, {"opponent": {"team": EUX}}]}),
    }


AUJ = date(2026, 11, 28)


def test_noms_des_divisions_et_des_equipes_de_paris():
    assert fftt.numero_equipe("VAIRES CVTT (3)") == 3 and fftt.numero_equipe("VAIRES CVTT 2") == 2
    assert [fftt.libelle_division(d) for d in ("L08_Honneur", "L08_Promo Honneur", "L08_2eme Division")] == [
        "Honneur", "Promotion d'Honneur", "Division 2"]
    assert [fftt.division_courte(d) for d in ("L08_Honneur", "L08_Promo Honneur", "L08_2eme Division")] == ["HO", "PH", "D2"]
    assert fftt.du_championnat(PARIS, "paris") and not fftt.du_championnat(PARIS, "france")
    assert fftt.du_championnat(CHAMP_FR, "france") and not fftt.du_championnat(CHAMP_FR, "paris")
    assert fftt.du_championnat({"division": {"contest": {"name": "Chpt Jeunes par Equipes 77 2526"}}}, "jeunes")
    assert fftt.bornes(AUJ, "paris") == ("2026-07-01", "2027-06-30") and fftt.bornes(AUJ, "france") == ("2026-07-01", "2026-12-31")


@pytest.mark.parametrize("melanger", [False, True])
def test_groupes_de_trois_joueurs(melanger):
    """Le groupe 1 est celui des meilleurs joueurs de Vaires, quel que soit l'ordre des parties dans l'API."""
    d = {"games": _parties(melanger)}
    groupes = groupes_des_parties(d, "home", "away")
    par_joueur = {}
    for g, n in zip(d["games"], groupes):
        par_joueur.setdefault(g["homePlayer"]["identifier"], set()).add(n)
    assert par_joueur == {str(i): {(i - 1) // 3 + 1} for i in range(1, 10)}


def test_feuilles_de_match_de_paris():
    d = recuperer_rencontres(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    assert d["championnat"] == "paris" and d["journees"] == [1]
    (r,) = d["rencontres"]
    assert (r["equipe"], r["numero"], r["division"], r["division_courte"]) == ("VAIRES 1", 1, "Honneur", "HO")
    assert r["points_partie"] == [90, 45] and r["score"] == [18, 9]
    assert [(g["numero"], g["score"], g["points"], g["bareme"]) for g in r["groupes"]] == [
        (1, [6, 3], [36, 18], 6), (2, [6, 3], [30, 15], 5), (3, [6, 3], [24, 12], 4)]
    assert [p["groupe"] for p in r["parties"]] == [1] * 9 + [2] * 9 + [3] * 9
    assert r["groupes"][0]["nous"] == ["1", "2", "3"]
    # Le championnat de France reste à part
    fr = recuperer_rencontres(FauxClient(_site()), VAIRES, AUJ)
    assert [x["equipe"] for x in fr["rencontres"]] == ["VAIRES 2"] and "groupe" not in str(fr["rencontres"][0].get("groupes"))


def test_resultats_des_joueurs_coefficient_de_paris():
    r = recuperer_parties(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    assert r["championnat"] == "paris" and r["coefficient"] == 0.75 and len(r["parties"]) == 27
    p = next(x for x in r["parties"] if x["licence"] == "1")
    assert p["gain"] == points_partie(p["points"], p["points_adv"], p["victoire"], 0.75)
    page = donnees_page(r)
    assert page["championnat"] == "paris" and page["coefficient"] == 0.75 and [j["numero"] for j in page["journees"]] == [1]


def test_classement_de_la_poule_de_paris():
    res = equipes_du_championnat(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    (e,) = res["equipes"]
    assert (e["id"], e["championnat"], e["division"], e["nom_court"]) == ("v1", "P", "Honneur", "Vaires 1")
    assert [r["journee"] for r in e["rencontres"]] == [1, 2] and e["rencontres"][0]["score"] == [90, 45]
    assert [(c["libelle"], c["points"], c["v"], c["joues"]) for c in e["classement"]] == [("VAIRES CVTT (1)", 3, 1, 1), ("NOGENT TT (1)", 1, 0, 1)]
    c = donnees_classements({"club": {"numero": VAIRES, "nom": "CVTT VAIRES"}, "saison": "2026-2027", "phase": 1,
                             "championnat": "paris", "equipes": res["equipes"]})
    assert c["championnat"] == "paris" and c["journee"] == 1 and c["poules"][0]["lignes"][0]["nous"]


def test_page_avec_selecteur_de_championnat(tmp_path):
    rendu.generer_html({"x": 1}, tmp_path / "p.html", rendu.GABARIT_RENCONTRES, autres={"paris": {"x": 2}, "jeunes": None})
    html = (tmp_path / "p.html").read_text(encoding="utf-8")
    assert '<script id="donnees-paris" type="application/json">{"x": 2}</script>' in html and "donnees-jeunes" not in html
    assert html.index('id="donnees"') < html.index('id="donnees-paris"') < html.index("CVTT_CHAMPIONNAT") < html.index("const D = JSON.parse")
    assert '["france", "paris"]' in html
    rendu.generer_html({"x": 1}, tmp_path / "q.html", rendu.GABARIT_RENCONTRES)
    assert "cvtt-champ" not in (tmp_path / "q.html").read_text(encoding="utf-8")


def test_images_de_paris(tmp_path):
    pytest.importorskip("PIL")
    from ttvaires import images
    from ttvaires.recap import image_recap

    d = recuperer_rencontres(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    feuilles = images.images_rencontres(d, tmp_path, prefixe="paris_")
    assert [(c.name, t) for c, t in feuilles] == [("paris_rencontres_J1_V1.png", "Paris · Vaires 1 : feuille de match J1")]
    (recap, titre), = image_recap(d, None, tmp_path, "paris_")
    assert recap.name == "paris_recap_J1.png" and titre.startswith("Paris · Récapitulatif J1")
    r = donnees_page(recuperer_parties(FauxClient(_site()), VAIRES, AUJ, championnat="paris"))
    noms = [c.name for c, _ in images.images_resultats(r, tmp_path, prefixe="paris_")]
    assert noms and all(n.startswith("paris_resultats_") for n in noms)
    eq = equipes_du_championnat(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    (cl, t), = images.image_classements({"club": {"numero": VAIRES, "nom": "CVTT VAIRES"}, "saison": "2026-2027", "phase": 1,
                                          "championnat": "paris", "equipes": eq["equipes"]}, None, tmp_path, prefixe="paris_")
    assert cl.name == "paris_classements_poules.png" and t == "Paris · Classements des poules après la J1"
    # Les images du championnat de France ne sont pas effacées par celles de Paris (et inversement)
    (tmp_path / "rencontres_J5_V2.png").write_bytes(b"x")
    images.images_rencontres(d, tmp_path, prefixe="paris_")
    assert (tmp_path / "rencontres_J5_V2.png").exists()


def test_scores_et_classement_dans_la_page_de_paris():
    """28/11 : /paris/ (poules recopiées des documents) reçoit les scores et le classement lus dans l'API, dans le
    sens de la page (équipe qui reçoit d'abord) ; les noms de la page sont gardés."""
    from ttvaires import paris

    eq = equipes_du_championnat(FauxClient(_site()), VAIRES, AUJ, championnat="paris")["equipes"]
    page = {"equipes": [{"numero": 1, "rencontres": [
        {"journee": 1, "date": "2026-11-27", "vaires_domicile": True, "score": None},
        {"journee": 2, "date": "2027-01-08", "vaires_domicile": False, "score": None}],
        "classement": [{"rang": None, "libelle": "VAIRES CTT 1", "club": VAIRES, "dep": "77", "points": None},
                       {"rang": None, "libelle": "NOGENT TT 1", "club": "08940524", "dep": "94", "points": None}]}]}
    d = paris.avec_resultats(page, eq)
    e = d["equipes"][0]
    assert e["rencontres"][0]["score"] == [90, 45] and e["rencontres"][1]["score"] is None
    assert [(c["rang"], c["libelle"], c["dep"], c["points"], c["joues"]) for c in e["classement"]] == [
        (1, "VAIRES CTT 1", "77", 3, 1), (2, "NOGENT TT 1", "94", 1, 1)]
    # Vaires à l'extérieur : le score suit le sens de la page
    eq[0]["rencontres"][0]["vaires_domicile"] = False
    eq[0]["rencontres"][0]["score"] = [45, 90]
    page["equipes"][0]["rencontres"][0].update(vaires_domicile=False, score=None)
    assert paris.avec_resultats(page, eq)["equipes"][0]["rencontres"][0]["score"] == [45, 90]
    assert paris.avec_resultats({"equipes": []}, None) == {"equipes": []}


def test_colonne_virtuel_du_club_dans_les_resultats():
    """28/11 : « Virt. » = classement virtuel du club (toutes compétitions), pas les points + le total du championnat."""
    r = recuperer_parties(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    d = donnees_page(r, {"1": 1415.5, "999": 800})
    assert d["virtuels_club"] == {"1": 1415.5}
    assert donnees_page(r)["virtuels_club"] is None


def test_brulage_de_paris_trois_matchs():
    """Règlement de la ligue, article 12 : brûlé pour l'équipe N après 3 matchs (et non 2) dans des équipes plus fortes."""
    from ttvaires.brulage import SEUILS, brulage_par_equipe, equipe_max

    deux, trois = [{"numero": 1}, {"numero": 1}], [{"numero": 1}, {"numero": 2}, {"numero": 1}]
    assert SEUILS == {"france": 2, "paris": 3}
    assert not brulage_par_equipe(deux, [1, 2, 3], 3)[2]["brule"] and brulage_par_equipe(deux, [1, 2, 3])[2]["brule"]
    b = brulage_par_equipe(trois, [1, 2, 3], 3)
    assert (b[2]["brule"], b[3]["brule"]) == (False, True) and equipe_max(trois, 3) == 2 and equipe_max(deux, 3) is None


def test_effectif_de_paris_page_et_images(tmp_path):
    from ttvaires import images
    from ttvaires.effectif import recuperer_effectif

    d = recuperer_effectif(FauxClient(_site()), VAIRES, AUJ, championnat="paris")
    assert d["championnat"] == "paris" and d["seuil_brulage"] == 3
    assert [(e["id"], e["championnat"], e["division"]) for e in d["equipes"]] == [("v1", "M", "Honneur")]
    alignes = [j for j in d["joueurs"] if j["matchs"]]
    assert len(alignes) == 9 and all(m["n"] == 1 for j in alignes for m in j["matchs"])
    pytest.importorskip("PIL")
    noms = [c.name for c, _ in images.images_effectif(d, tmp_path, prefixe="paris_")]
    assert noms and all(n.startswith("paris_effectif_") for n in noms)


def test_classement_virtuel_colonne_paris(tmp_path):
    """28/11 : colonne Paris (points du championnat de Paris, à part des « autres » compétitions) et l'équipe de Paris."""
    pytest.importorskip("PIL")
    from ttvaires import images

    partie = lambda champ, paris, pts: {"championnat": champ, "paris": paris, "points": pts}
    j = {"nom": "FICTIF", "prenom": "Un", "categorie": "V50", "equipe": "V1", "officiels": 889, "classement": 8,
         "championnat": 23.5, "paris": 2.2, "autres": 0.05, "total": 25.75, "virtuels": 914.75, "classement_virtuel": 9,
         "v": 10, "d": 8, "equipes_paris": "P1", "parties": [partie(True, False, 23.5), partie(False, True, 2.2), partie(False, False, 0.05)]}
    d = {"club": {"nom": "CVTT VAIRES"}, "phase": 1, "saison": "2026-2027", "genere_le": "2026-11-28T10:42", "joueurs": [j]}
    ((chemin, titre),) = images.images_virtuel(d, tmp_path)
    assert chemin.name == "classement_virtuel.png"
    gabarit = (rendu.GABARIT_VIRTUEL).read_text(encoding="utf-8")
    assert "AVEC_PARIS" in gabarit and "parisComp" in gabarit

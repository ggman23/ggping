"""Individuels : poules du critérium chiffrées dans le dépôt, forme des adversaires, page /indivs/."""

import base64
import json
import re

import pytest

from test_effectif import FauxClient
from ttvaires import indivs, netlify, publier
from ttvaires.virtuel import url_parties


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:
        pytest.skip("bibliothèque cryptography indisponible")


def _poules():
    j = lambda lic, nom, pts, club: {"licence": lic, "nom": nom, "prenom": "P", "points": pts, "club": club, "cat": "S"}
    return {"maj": "2026-11-11", "poules": [
        {"id": "p1", "public": "adultes", "competition": "Critérium · Tour 2", "titre": "D3 · groupe 1", "date": "2026-11-15",
         "horaire": None, "lieu": "COSEC", "joueurs": [j("1", "VAIRIEN", 1000, "CVTT VAIRES"), j("2", "FORT", 1200, "CS MEAUX TT"),
                                                      j("3", "ERREUR", 800, "ATT QUINCY")]},
        {"id": "p2", "public": "jeunes", "competition": "Critérium · Tour 2", "titre": "M11", "date": "2026-11-14",
         "horaire": None, "lieu": None, "joueurs": [j("9", "AUTRE", 500, "CHELLES TENNIS DE TABLE")]},  # sans Vaires
    ]}


def test_poules_chiffrees_dans_le_depot(tmp_path):
    _crypto()
    fichier = indivs.ecrire(_poules(), "club", tmp_path / "indivs.json.chiffre")
    assert b"VAIRIEN" not in fichier.read_bytes()  # dépôt public : rien en clair
    assert indivs.lire("club", fichier)["poules"][0]["joueurs"][0]["nom"] == "VAIRIEN"
    with pytest.raises(Exception):
        indivs.lire("autre", fichier)
    assert indivs.lire("club", tmp_path / "absent") is None


def test_noms_et_club():
    assert indivs.nom_coherent("DOS REIS", "Dos Reis") and indivs.nom_coherent("PELEGRIN BRESSAND", "PELEGRIN-BRESSAND")
    assert indivs.nom_coherent("DUPOND", "MARTIN") is False and indivs.nom_coherent("X", None) is None
    assert indivs.de_vaires({"club": "CVTT VAIRES"}) and indivs.de_vaires({"club": "x", "numero_club": "08770250"})
    assert not indivs.de_vaires({"club": "CHELLES TENNIS DE TABLE"})


def test_forme_des_joueurs_des_poules_de_vaires():
    def partie(id_, lic, nom, pts, adv_pts, gagne=True):
        return {"id": id_, "date": "2026-10-10T00:00:00", "winner": "home" if gagne else "away", "doubleOpposition": False,
                "contest": {"id": 7, "name": "FED_Critérium Fédéral"},
                "homePlayer": {"identifier": lic, "points": pts, "person": {"familyName": nom}},
                "awayPlayer": {"identifier": "88", "points": adv_pts, "person": {"familyName": "X"}}}

    pages = {url_parties("1"): json.dumps({"hydra:member": [partie(1, "1", "Vairien", 1000, 1050)]}),
             url_parties("2"): json.dumps({"hydra:member": [partie(2, "2", "FORT", 1200, 1100), partie(3, "2", "FORT", 1200, 1150)]}),
             url_parties("3"): json.dumps({"hydra:member": [partie(4, "3", "QUELQU'UN", 800, 790)]}),  # licence mal recopiée
             "https://apiv2.fftt.com/api/contests/7": json.dumps({"name": "FED_Critérium Fédéral", "coefficient": 1.5})}
    client = FauxClient(pages)
    d = indivs.recuperer(client, _poules())
    assert [p["id"] for p in d["poules"]] == ["p1"]  # seulement les poules où joue un joueur de Vaires
    js = {j["licence"]: j for j in d["poules"][0]["joueurs"]}
    assert js["1"]["vaires"] and not js["2"]["vaires"]
    assert (js["2"]["forme"]["v"], js["2"]["forme"]["d"]) == (2, 0) and js["2"]["forme"]["competitions"][0]["nom"] == "Critérium fédéral"
    assert js["3"]["licence_douteuse"] and not js["2"]["licence_douteuse"]
    assert d["controle"]["joueurs"] == 3 and len(d["controle"]["licences_douteuses"]) == 1
    assert "1 licence(s) à vérifier" in indivs.resume(d)


def test_page_publiee_a_son_adresse_avec_le_mot_de_passe_du_club(tmp_path):
    _crypto()
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    (sortie / "vaires.html").write_text("<p>adversaires</p>", encoding="utf-8")
    (sortie / "indivs_vaires.html").write_text("<p>POULE DUPOND</p>", encoding="utf-8")
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-11T08:00", "fin": "2026-11-11T08:05", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["vaires.html"]},
        {"nom": "individuels", "resume": "ok", "fichiers": ["indivs_vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "g/p", "b")
    assert "DUPOND" not in (site / "indivs.html").read_text(encoding="utf-8")  # chiffrée (mot de passe du site)
    for dossier in (netlify.construire(site, tmp_path / "netlify", "secret", "", "club"),
                    netlify.site_github(site, tmp_path / "github", "secret", "club")):
        page = (dossier / "indivs" / "index.html").read_text(encoding="utf-8")
        assert "DUPOND" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page  # même mot de passe retenu que /club/
        chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', page, re.S)[1].strip()
        assert b"POULE DUPOND" in publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club"))
        club = (dossier / "club" / "index.html").read_text(encoding="utf-8")
        donnees = json.loads(re.search(r"const D = (\{.*?\});\n", club, re.S)[1]) if "const D = {" in club else None
        assert '"chemin": "indivs"' in club or (donnees and any(e["chemin"] == "indivs" for e in donnees["espaces"]))
        assert not (dossier / "club" / "fichiers" / "indivs_vaires.html.chiffre").exists()  # pas parmi les documents


def test_une_image_par_poule_sans_nom_dans_les_titres(tmp_path):
    pytest.importorskip("PIL.ImageDraw")
    from ttvaires.images import images_indivs

    f = lambda pts: {"v": 3, "d": 1, "points": pts, "officiels": 1000, "virtuels": 1000 + pts, "competitions": [
        {"nom": "Critérium fédéral", "v": 3, "d": 1, "points": pts}], "nom": "X"}
    j = lambda nom, club, vaires, forme: {"licence": nom, "nom": nom, "prenom": "Paul", "points": 1000, "club": club,
                                          "cat": "S", "vaires": vaires, "forme": forme, "licence_douteuse": False}
    donnees = {"genere_le": "2026-11-11T18:00", "publics": indivs.PUBLICS, "poules": [
        {"id": "p1", "public": "adultes", "competition": "Critérium · Tour 2", "titre": "D3 · groupe 1", "date": "2026-11-15",
         "horaire": None, "lieu": "COSEC", "joueurs": [j("DUPOND", "CVTT VAIRES", True, f(-4)), j("FORT", "CS MEAUX TT", False, f(60)),
                                                      {**j("FAIBLE", "ATT QUINCY", False, None), "points": 900}]}]}
    sorties = images_indivs(donnees, tmp_path)
    assert [(c.name, t) for c, t in sorties] == [("indivs_p1.png", "Adultes · D3 · groupe 1 · dim. 15/11")]
    assert "DUPOND" not in sorties[0][1]  # liste des images visible sans mot de passe : pas de nom
    moi, fort = donnees["poules"][0]["joueurs"][:2]
    assert indivs.niveau(fort, moi) == "plus fort" and indivs.niveau(moi, fort) == "à sa portée"
    assert [x["nom"] for x in indivs.par_virtuels(donnees["poules"][0]["joueurs"])] == ["FORT", "DUPOND", "FAIBLE"]


def test_resultats_du_tour_et_classement_de_la_poule():
    """Tour joué : les parties de critérium du jour de chaque joueur de la poule (déjà lues pour la forme, aucune
    requête de plus), V/D et points gagnés ; classement : victoires, puis la partie entre deux joueurs à égalité,
    puis les points. Une partie de championnat le même jour ne compte pas ; un adversaire hors liste, si."""
    from datetime import date

    crit = {"id": 7, "name": "FED_Critérium Fédéral"}
    champ = {"id": 1, "name": "Championnat par équipes M"}

    def partie(id_, dom, ext, gagnant="home", jour="2026-11-15", contest=crit):
        return {"id": id_, "date": jour + "T00:00:00", "winner": gagnant, "doubleOpposition": False, "contest": contest,
                "homePlayer": {"identifier": dom[0], "points": dom[1], "person": {"familyName": dom[2]}},
                "awayPlayer": {"identifier": ext[0], "points": ext[1], "person": {"familyName": ext[2]}}}

    v, f, e, x = ("1", 1000, "VAIRIEN"), ("2", 1200, "FORT"), ("3", 800, "ERREUR"), ("88", 900, "INVITE")
    g11, g12, g13 = partie(11, v, e), partie(12, f, e), partie(13, v, f)          # 1 bat 3 ; 2 bat 3 ; 1 bat 2
    g14 = partie(14, f, x)                                                         # 2 bat un joueur hors liste
    g15 = partie(15, v, x, "away", contest=champ)                                  # championnat : hors tour
    g16 = partie(16, v, f, "away", jour="2026-10-10")                              # autre jour : hors tour
    pages = {url_parties("1"): json.dumps({"hydra:member": [g11, g13, g15, g16]}),
             url_parties("2"): json.dumps({"hydra:member": [g12, g13, g14, g16]}),
             url_parties("3"): json.dumps({"hydra:member": [g11, g12]}),
             "https://apiv2.fftt.com/api/contests/7": json.dumps({"name": crit["name"], "coefficient": 1.5}),
             "https://apiv2.fftt.com/api/contests/1": json.dumps({"name": champ["name"], "coefficient": 1})}
    d = indivs.recuperer(FauxClient(pages), _poules(), aujourdhui=date(2026, 11, 20))
    r = d["poules"][0]["resultats"]
    assert r["jour"] == "2026-11-15" and r["sans_resultat"] == []
    assert {k: (x["v"], x["d"]) for k, x in r["joueurs"].items()} == {"1": (2, 0), "2": (2, 1), "3": (0, 2)}
    assert [(c["licence"], c["rang"], c["departage"]) for c in r["classement"]] == [
        ("1", 1, "partie entre eux"), ("2", 2, "partie entre eux"), ("3", 3, None)]
    hors = [p for p in r["joueurs"]["2"]["parties"] if not p["dans_la_poule"]]
    assert [p["adv_licence"] for p in hors] == ["88"] and r["joueurs"]["1"]["points"] > 0 > r["joueurs"]["3"]["points"]
    assert "résultats du tour : 1 poule(s)" in indivs.resume(d)
    # Avant le tour : pas de résultats
    assert "resultats" not in indivs.recuperer(FauxClient(pages), _poules(), aujourdhui=date(2026, 11, 14))["poules"][0]
    # Égalité à trois (cycle) : départagés par les points gagnés
    cycle = {"a": {"v": 1, "d": 1, "points": 2.0, "parties": [{"adv_licence": "b", "victoire": True}]},
             "b": {"v": 1, "d": 1, "points": 5.0, "parties": [{"adv_licence": "c", "victoire": True}]},
             "c": {"v": 1, "d": 1, "points": -1.0, "parties": [{"adv_licence": "a", "victoire": True}]}}
    assert [(c["licence"], c["rang"]) for c in indivs.classement_du_tour(cycle)] == [("b", 1), ("a", 2), ("c", 3)]


def test_tour_sans_date_retrouve_dans_les_parties(capsys):
    """Liste recopiée sans date (qualifiées d'un tour régional, 26/11) : le jour du tour vient des parties de
    critérium des joueurs, après la recopie des poules (le tour précédent ne compte pas) ; sinon, pas de résultats."""
    from datetime import date

    crit = {"id": 7, "name": "FED_Critérium Fédéral"}

    def partie(id_, dom, ext, jour, gagnant="home"):
        return {"id": id_, "date": jour + "T00:00:00", "winner": gagnant, "doubleOpposition": False, "contest": crit,
                "homePlayer": {"identifier": dom[0], "points": dom[1], "person": {"familyName": dom[2]}},
                "awayPlayer": {"identifier": ext[0], "points": ext[1], "person": {"familyName": ext[2]}}}

    v, a, b = ("1", 800, "VAIRIENNE"), ("2", 900, "AUTRE"), ("3", 700, "TROISIEME")
    tour1 = [partie(1, a, v, "2026-10-11"), partie(2, a, b, "2026-10-11"), partie(3, v, b, "2026-10-11")]  # avant la recopie
    tour2 = [partie(4, v, a, "2026-11-15"), partie(5, b, a, "2026-11-15", "away")]
    seule = partie(6, b, ("77", 600, "X"), "2026-11-22")  # une seule joueuse ce jour-là : pas un tour de la liste
    pages = {url_parties("1"): json.dumps({"hydra:member": [tour1[0], tour1[2], tour2[0]]}),
             url_parties("2"): json.dumps({"hydra:member": [tour1[0], tour1[1], tour2[0], tour2[1]]}),
             url_parties("3"): json.dumps({"hydra:member": [tour1[1], tour1[2], tour2[1], seule]}),
             "https://apiv2.fftt.com/api/contests/7": json.dumps({"name": crit["name"], "coefficient": 1.5})}
    j = lambda x, club: {"licence": x[0], "nom": x[2], "prenom": "P", "points": x[1], "club": club, "cat": "S"}
    poules = {"maj": "2026-11-11", "poules": [
        {"id": "p1", "public": "feminines", "competition": "Critérium régional · Tour 2", "titre": "R2 dames (3 qualifiées)",
         "date": None, "horaire": None, "lieu": None, "joueurs": [j(v, "CVTT VAIRES"), j(a, "CS MEAUX TT"), j(b, "ATT QUINCY")]}]}
    d = indivs.recuperer(FauxClient(pages), poules, aujourdhui=date(2026, 11, 26))
    p = d["poules"][0]
    assert p["date"] == "2026-11-15" and p["date_deduite"] is True
    assert p["resultats"]["jour"] == "2026-11-15" and {k: (x["v"], x["d"]) for k, x in p["resultats"]["joueurs"].items()} == {
        "1": (1, 0), "2": (1, 1), "3": (0, 1)}
    assert "date du tour retrouvée dans les parties pour 1 poule(s)" in capsys.readouterr().out
    # Avant le tour : ni date ni résultats (les parties du tour précédent ne comptent pas)
    avant = indivs.recuperer(FauxClient(pages), poules, aujourdhui=date(2026, 11, 14))["poules"][0]
    assert avant["date"] is None and "resultats" not in avant and "date_deduite" not in avant
    # Le jour où une seule joueuse de la liste a joué ne suffit pas
    assert indivs.date_du_tour(poules["poules"][0], {"3": [{"date": "2026-11-22", "competition": "FED_Critérium Fédéral",
                                                             "championnat": False}]}, "2026-11-11", date(2026, 11, 26)) is None

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

"""Récapitulatif de la journée en une image (modèle du club), sur des données fictives."""

import pytest

PIL = pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from ttvaires import recap  # noqa: E402


def _joueur(licence, nom, prenom, points, lettre):
    return {"licence": licence, "nom": nom, "prenom": prenom, "points": points, "lettre": lettre}


DELOBELLE = _joueur("1", "DELOBELLE", "Jérôme", 780, "Z")
LARDE = _joueur("2", "LARDE", "Jerome", 889, "X")
GUITTON = _joueur("3", "GUITTON", "Marc", 1410, "Y")
ADV = {p: _joueur(f"a{p}", "ADV", "X", p, "A") for p in (500, 932, 939, 975, 1200)}


def _partie(nous, eux, gagne, double=False):
    return {"double": double, "nous": nous, "eux": eux, "gagne": gagne, "sets": [], "forfait": False}


def _rencontre(parties, domicile=False, points_partie=(22, 20), numero=1, feminine=False, journee=3):
    return {"journee": journee, "date": "2026-10-16", "equipe": f"VAIRES {numero}", "numero": numero, "feminine": feminine,
            "division_courte": "D1", "domicile": domicile, "adversaire": "BRIE ASTT 2", "parties": parties,
            "score": [8, 6], "points_partie": list(points_partie), "forfait": False}


RENCONTRE = _rencontre([
    _partie([DELOBELLE], [ADV[939]], True), _partie([DELOBELLE], [ADV[932]], True), _partie([DELOBELLE], [ADV[500]], False),
    _partie([LARDE], [ADV[975]], True), _partie([LARDE], [ADV[500]], True),   # perf contre 975, pas contre 500
    _partie([GUITTON], [ADV[1200]], True),                                    # mieux classé : pas une perf
    _partie([LARDE, DELOBELLE], [ADV[500], ADV[932]], False, double=True),
    _partie([GUITTON, LARDE], [ADV[500], ADV[939]], True, double=True),
])


def test_equipe_resultat_joueurs_et_doubles():
    [e] = recap.equipes_de_la_journee([RENCONTRE])
    assert e["titre"] == "Vaires 1 (D1)"
    assert e["resultat"] == "Victoire 20 – 22"  # points-parties, domicile – extérieur (Vaires à l'extérieur)
    assert [(j["nom"], j["v"], j["d"], j["perfs"]) for j in e["joueurs"]] == [
        ("LARDE", 2, 0, [975]), ("GUITTON", 1, 0, []), ("DELOBELLE", 2, 1, [939, 932])]  # ordre de la feuille
    assert e["doubles"] == [1, 1] and e["nb_doubles"] == 2
    feminine = recap.equipes_de_la_journee([_rencontre([], feminine=True)])[0]
    assert feminine["titre"] == "Féminine (D1)" and feminine["resultat"] == "Pas encore saisi"
    nul = recap.equipes_de_la_journee([_rencontre([_partie([GUITTON], [ADV[500]], True)], domicile=True, points_partie=(21, 21))])[0]
    assert nul["resultat"] == "Égalité 21 – 21"


def test_noms_affiches_et_top_des_perfs(tmp_path, monkeypatch):
    monkeypatch.delenv("SURNOMS", raising=False)
    equipes = recap.equipes_de_la_journee([RENCONTRE])
    joueurs = [DELOBELLE, LARDE, GUITTON]
    noms = recap.noms_affiches(joueurs)
    # Même prénom (avec ou sans accents) : initiales du nom, et l'orthographe accentuée pour les deux
    assert noms == {"1": "Jérôme D", "2": "Jérôme L", "3": "Marc"}
    (tmp_path / "surnoms.txt").write_text("# noms affichés\nGUITTON Marc = Marc G\n", encoding="utf-8")
    assert recap.noms_affiches(joueurs, recap.lire_surnoms(tmp_path))["3"] == "Marc G"
    # Mise à jour lancée depuis le site : le secret SURNOMS complète le fichier et l'emporte sur lui
    monkeypatch.setenv("SURNOMS", "guitton marc = Marco ; LARDÉ Jérôme = Jérôme L.\r\n")
    assert recap.lire_surnoms(tmp_path) == {"GUITTON MARC": "Marco", "LARDE JEROME": "Jérôme L."}
    assert recap.lire_surnoms(None) == {"GUITTON MARC": "Marco", "LARDE JEROME": "Jérôme L."}
    assert recap.top_perfs(equipes, noms) == [("Jérôme D", [939, 932], 159), ("Jérôme L", [975], 86)]
    assert recap._liste([945, 932, 900]) == "945, 932 et 900"


def test_image_avec_la_place_de_la_photo_puis_avec_la_photo(tmp_path):
    donnees = {"phase": 1, "saison": "2026-2027", "journees": [2, 3],
               "rencontres": [_rencontre([], journee=2)] + [_rencontre(RENCONTRE["parties"], numero=n) for n in range(1, 8)]}
    sortie, imports = tmp_path / "sortie", tmp_path / "import"
    imports.mkdir()
    [(chemin, titre)] = recap.image_recap(donnees, imports, sortie)
    assert chemin.name == "recap_J3.png" and titre == "Récapitulatif J3 (photo à ajouter)"
    with Image.open(chemin) as img:
        assert img.size == (1280, 987)  # 7 équipes : comme le modèle
        assert img.getpixel((600, 120))[:3] == (241, 243, 245)  # place libre pour la photo
    Image.new("RGB", (1600, 1200), (200, 0, 0)).save(imports / "photo_J30.jpg")  # pas celle de la J3
    assert recap.image_recap(donnees, imports, sortie)[0][1] == "Récapitulatif J3 (photo à ajouter)"
    Image.new("RGB", (1600, 1200), (10, 120, 200)).save(imports / "photo_J3.jpg")
    assert [f.name for f in recap.images_du_recap(imports, 3)] == ["photo_J3.jpg"]
    [(chemin, titre)] = recap.image_recap(donnees, imports, sortie)
    assert titre == "Récapitulatif J3"
    with Image.open(chemin) as img:
        r, g, b = img.getpixel((600, 300))[:3]
        assert abs(r - 10) < 8 and abs(g - 120) < 8 and abs(b - 200) < 8  # photo collée dans le cadre

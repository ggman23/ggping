"""Images PNG des tableaux (lisibles sur téléphone), sur des données fictives."""

from datetime import date

import pytest

PIL = pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from ttvaires import images  # noqa: E402

CLUB = {"club": {"numero": "08770250", "nom": "CVTT VAIRES"}, "phase": 1, "saison": "2026-2027",
        "genere_le": "2026-10-19T08:00"}


def _ouvrir(chemin):
    with Image.open(chemin) as img:
        return img.size


def test_classement_virtuel_decoupe_en_images_lisibles(tmp_path):
    joueurs = [{"id": str(i), "nom": f"JOUEUR{i}", "prenom": "Prénom", "categorie": "S", "equipe": "V1",
                "officiels": 1000 - i, "classement": 9, "championnat": 2.5, "autres": -1.25, "total": 1.25,
                "virtuels": 1001.25 - i, "classement_virtuel": 10 if i == 1 else 9, "v": 2, "d": 1,
                "parties": [{"championnat": True}, {"championnat": False}]} for i in range(1, 31)]
    (tmp_path / "classement_virtuel_9.png").write_bytes(b"ancienne image")  # d'un lancement précédent
    sorties = images.images_virtuel({**CLUB, "joueurs": joueurs}, tmp_path)
    assert [c.name for c, _ in sorties] == ["classement_virtuel_1.png", "classement_virtuel_2.png",  # 15 + 15 lignes
                                            "classement_virtuel_complet.png"]                     # en plus : les 30
    assert [t for _, t in sorties] == ["Classement virtuel (1/2)", "Classement virtuel (2/2)",
                                       "Classement virtuel (image unique)"]
    assert not (tmp_path / "classement_virtuel_9.png").exists()
    largeur, hauteur = _ouvrir(sorties[0][0])
    assert largeur == 1080 and hauteur < 1600  # pas réduite par les messageries
    largeur_u, hauteur_u = _ouvrir(sorties[2][0])
    assert largeur_u == 1080 and hauteur_u > hauteur + 15 * 50  # toutes les lignes, l'une sous l'autre


def test_pas_d_image_unique_en_double_si_le_tableau_tient_en_une_image(tmp_path):
    joueurs = [{"id": "1", "nom": "SEUL", "prenom": "Paul", "categorie": "S", "equipe": "V1", "officiels": 900,
                "classement": 9, "championnat": 0, "autres": 0, "total": 0, "virtuels": 900, "classement_virtuel": 9,
                "v": 0, "d": 0, "parties": []}]
    sorties = images.images_virtuel({**CLUB, "joueurs": joueurs}, tmp_path)
    assert [c.name for c, _ in sorties] == ["classement_virtuel.png"]


def test_resultats_derniere_journee_et_cumul(tmp_path):
    lignes = [{"journee": 2, "date": "2026-10-02", "equipe": "VAIRES 1", "ordre": 0, "joueur": f"NOM{i} Prénom",
               "licence": str(i), "points": 800, "delta": d, "v": 2, "matchs": 3, "meilleure": 50, "meilleure_adv": 850,
               "apres": 800 + d, "total": d} for i, d in enumerate([3.0, -5.0, 12.5])]
    cumuls = [{"equipes": ["VAIRES 1"], "joueur": f"NOM{i} Prénom", "licence": str(i), "points": 800,
               "journees": {1: 1.0, 2: d}, "total": d + 1, "virtuels": 801 + d, "v": 3, "matchs": 6, "ordre": 0}
              for i, d in enumerate([3.0, -5.0, 12.5])]
    donnees = {**CLUB, "journees": [{"numero": 1, "dates": ["2026-09-25"]}, {"numero": 2, "dates": ["2026-10-02"]}],
               "lignes": lignes, "cumuls": cumuls}
    sorties = images.images_resultats(donnees, tmp_path)
    assert [c.name for c, _ in sorties] == ["resultats_J2.png", "resultats_cumul.png"]
    assert images.equipe_courte("VAIRES 1 F") == "V1F" and images.equipe_courte("Vaires 3") == "V3"


def test_effectif_club_et_brules_par_equipe(tmp_path):
    equipes = [{"id": f"v{n}", "numero": n, "championnat": "M", "nom_court": f"Vaires {n}"} for n in (1, 2, 3)]
    equipes.append({"id": "v1f", "numero": 1, "championnat": "F", "nom_court": "Vaires 1 F"})
    joueurs = [
        {"nom": "FORT", "prenom": "Paul", "points": 1200, "renouvele": True, "loisir": False, "sexe": "M",
         "matchs": [{"j": 1, "n": 1, "ch": "M"}, {"j": 2, "n": 1, "ch": "M"}],
         "brulage": {1: {"brule": False}, 2: {"brule": True, "plus_fortes": [1, 1]}, 3: {"brule": True, "plus_fortes": [1, 1]}}},
        {"nom": "JEUNE", "prenom": "Léa", "points": 600, "renouvele": True, "loisir": False, "sexe": "F",
         "matchs": [{"j": 1, "n": 3, "ch": "M"}, {"j": 1, "n": 1, "ch": "F"}],
         "brulage": {1: {"brule": False}, 2: {"brule": False}, 3: {"brule": False}}},
        {"nom": "LOISIR", "prenom": "Jean", "points": 500, "renouvele": True, "loisir": True, "matchs": [], "brulage": {}},
    ]
    sorties = images.images_effectif({**CLUB, "equipes": equipes, "joueurs": joueurs}, tmp_path)
    assert [c.name for c, _ in sorties] == ["effectif_club.png", "effectif_brules_V2.png", "effectif_brules_V3.png"]
    assert [t for _, t in sorties][1] == "Vaires 2 : joueurs brûlés"


def test_adversaires_prochaine_journee_et_prochain_adversaire(tmp_path):
    analyse = {"probable": ["1", "2"], "renforts": [{"id": "3", "equipes": [2]}], "non_alignes": ["4", "2"], "brules": []}
    rencontre = {"journee": 4, "date": "2026-11-06", "date_reelle": None, "heure": "20:45", "vaires_domicile": False,
                 "adversaire": {"club": "08779999", "libelle": "AUTRE 3", "numero": 3}, "analyse": analyse}
    passee = {**rencontre, "journee": 3, "date": "2026-10-16"}
    donnees = {**CLUB, "club": {**CLUB["club"], "salle": {"nom": "C.O.S.E.C"}},
               "equipes": [{"id": "v1", "nom_court": "Vaires 1", "numero": 1, "championnat": "M",
                            "rencontres": [passee, rencontre]}],
               "clubs": {"08779999": {"nom": "AUTRE", "salle": {"nom": "Gymnase", "adresse": "1 rue X", "cp": "77000",
                                                                "ville": "MELUN"},
                                      "joueurs": [{"id": str(i), "nom": f"ADV{i}", "prenom": "Max", "points": 900 - i,
                                                   "categorie": "S", "sexe": "M"} for i in range(1, 5)]}}}
    sorties = images.images_adversaires(donnees, tmp_path, date(2026, 10, 19))
    assert [c.name for c, _ in sorties] == ["adversaires_prochaine_journee.png", "adversaires_V1.png"]
    assert images._salle(donnees, rencontre) == "Gymnase, 1 rue X, 77000 MELUN"


def test_ajustement_du_texte():
    texte, taille = images.ajuster("MARTIMORT Christophe", 120, 23, alternatives=["MARTIMORT C.", "MARTIMORT"])
    assert texte in ("MARTIMORT C.", "MARTIMORT") or texte.endswith("…")
    assert images.largeur_texte(texte, taille) <= 120
    assert images.paginer(list(range(40))) == [list(range(20)), list(range(20, 40))]

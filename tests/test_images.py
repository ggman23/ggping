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


def test_deux_rencontres_la_meme_journee_chaque_ligne_rappelle_l_autre(tmp_path, monkeypatch):
    """Une joueuse alignée avec les garçons le vendredi et avec l'équipe féminine le samedi : ses deux
    lignes de la journée ne se suivent pas (tri par points), chacune rappelle donc l'autre."""
    base = {"journee": 4, "ordre": 0, "joueur": "CHOLLET Emily", "licence": "7", "points": 621, "matchs": 3,
            "meilleure": None, "meilleure_adv": None}
    lignes = [{**base, "date": "2026-11-06", "equipe": "VAIRES 5", "delta": -24.0, "v": 0, "apres": 591.5, "total": -29.5,
               "autres": [{"equipe": "VAIRES 1 F", "date": "2026-11-07", "delta": 1.0}]},
              {**base, "date": "2026-11-07", "equipe": "VAIRES 1 F", "delta": 1.0, "v": 2, "apres": 592.5, "total": -28.5,
               "autres": [{"equipe": "VAIRES 5", "date": "2026-11-06", "delta": -24.0}]}]
    cumuls = [{"equipes": ["VAIRES 5", "VAIRES 1 F"], "joueur": "CHOLLET Emily", "licence": "7", "points": 621,
               "journees": {4: -23.0}, "total": -23.0, "virtuels": 598, "v": 2, "matchs": 6, "ordre": 4}]
    vus = []
    monkeypatch.setattr(images, "_tableau_pagine", lambda dossier, prefixe, titre, st, colonnes, lignes, pied, tc:
                        vus.append((lignes, pied)) or [])
    images.images_resultats({**CLUB, "journees": [{"numero": 4, "dates": ["2026-11-06", "2026-11-07"]}],
                             "lignes": lignes, "cumuls": cumuls}, tmp_path)
    (journee, pied), _ = vus
    assert [l[1].apres for l in journee] == ["+ V5 -24,0", "+ V1F +1,0"]
    assert "autre ligne" in pied


def test_effectif_club_disponibles_et_brules_par_equipe(tmp_path, monkeypatch):
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
    vus, original = [], images._tableau_pagine

    def espion(dossier, prefixe, titre, sous_titre, colonnes, lignes, pied, titre_court):
        vus.append((prefixe, [l[0].texte for l in lignes]))
        return original(dossier, prefixe, titre, sous_titre, colonnes, lignes, pied, titre_court)

    monkeypatch.setattr(images, "_tableau_pagine", espion)
    sorties = images.images_effectif({**CLUB, "equipes": equipes, "joueurs": joueurs}, tmp_path)
    # Pour chaque équipe (sauf la 1) : les joueurs disponibles, triés par points, puis les brûlés ;
    # l'équipe féminine : toutes les joueuses.
    assert [c.name for c, _ in sorties] == ["effectif_club.png", "effectif_disponibles_V2.png", "effectif_brules_V2.png",
                                           "effectif_disponibles_V3.png", "effectif_brules_V3.png",
                                           "effectif_disponibles_V1F.png"]
    assert [t for _, t in sorties][1:3] == ["Vaires 2 : joueurs disponibles", "Vaires 2 : joueurs brûlés"]
    disponibles = {prefixe: noms for prefixe, noms in vus if "disponibles" in prefixe}
    assert disponibles == {"effectif_disponibles_V2": ["JEUNE Léa"], "effectif_disponibles_V3": ["JEUNE Léa"],
                           "effectif_disponibles_V1F": ["JEUNE Léa"]}


def test_adversaires_prochaine_journee_et_prochain_adversaire(tmp_path, monkeypatch):
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
    assert _ouvrir(sorties[0][0])[0] == 1080
    assert _ouvrir(sorties[1][0])[0] == images.FICHE_MIN  # fiche à la largeur de son contenu : pas de place perdue

    # Placement des joueurs adverses aux rencontres déjà jouées : colonne « Placé » et tableau par position
    rencontre["placements"] = {"format": 4, "libelles": ["A/W", "B/X", "C/Y", "D/Z"], "par_points": 0, "avec_points": 1,
                               "joueurs": {"1": [0, 0, 1, 0], "2": [1, 0, 0, 0]},
                               "rencontres": [{"journee": 3, "date": "2026-10-16", "domicile": True, "contre": "X 1",
                                               "places": ["2", "4", "1", None], "points": [898, 896, 899, None],
                                               "par_points": False}]}
    sorties = images.images_adversaires(donnees, tmp_path, date(2026, 10, 19))
    assert images.FICHE_MIN <= _ouvrir(sorties[1][0])[0] <= images.LARGEUR
    sans_meilleur = _ouvrir(sorties[1][0])[0]

    # Meilleur classement (historique pingpocket) : une colonne de plus, l'image s'élargit un peu
    joueurs = donnees["clubs"]["08779999"]["joueurs"]
    joueurs[0]["meilleur"] = {"points": 1452, "annee": "2006"}
    joueurs[1]["meilleur"] = {"points": 898, "annee": "2026"}
    sorties = images.images_adversaires(donnees, tmp_path, date(2026, 10, 19))
    assert sans_meilleur < _ouvrir(sorties[1][0])[0] <= images.LARGEUR

    # Beaucoup de colonnes chargées : l'année passe sous les points, et rien ne sort de l'image
    rencontre["placements"]["joueurs"] = {str(i): [3, 2, 2, 1] for i in range(1, 5)}
    for j in joueurs:
        j["nom"], j["prenom"] = "LE BOURHIS-KERGUELEN", "Jean-Baptiste"
    vues = []
    vrai_tableau = images.Rendu.tableau
    monkeypatch.setattr(images.Rendu, "tableau", lambda self, colonnes, lignes, *a, **k: (
        vues.append((self.largeur, colonnes, lignes)), vrai_tableau(self, colonnes, lignes, *a, **k))[1])
    sorties = images.images_adversaires(donnees, tmp_path, date(2026, 10, 19))
    largeur, colonnes, lignes = next(v for v in vues if v[1][3].titre == "Meilleur")
    assert sum(c.largeur for c in colonnes) + 2 * images.MARGE <= largeur == _ouvrir(sorties[1][0])[0]
    meilleur = next(l[3] for l in lignes if l[3].texte)
    assert (meilleur.texte, meilleur.sous, meilleur.apres) == ("1 452", "2006", None)


def test_remarques_des_renforts_sur_deux_lignes(tmp_path, monkeypatch):
    """« a joué en 3 » puis, dessous, « déjà 1× en 9 » (au lieu de « a joué en 3 … » coupé) ; un nouvel
    inscrit : « nouvel inscrit » en vert, ou dessous s'il y a déjà une remarque."""
    analyse = {"probable": ["1"], "renforts": [{"id": "2", "equipes": [3], "dans_equipe": 1}, {"id": "3", "equipes": [4, 5]}],
               "non_alignes": ["4"], "brules": []}
    rencontre = {"journee": 5, "date": "2026-11-20", "date_reelle": None, "heure": "20:45", "vaires_domicile": False,
                 "adversaire": {"club": "08779999", "libelle": "AUTRE 9", "numero": 9}, "analyse": analyse}
    joueurs = [{"id": str(i), "nom": f"ADV{i}", "prenom": "Max", "points": 900 - i, "categorie": "S", "sexe": "M",
                "nouveau": i in (2, 4)} for i in range(1, 5)]
    donnees = {**CLUB, "equipes": [{"id": "v4", "nom_court": "Vaires 4", "numero": 4, "championnat": "M", "rencontres": [rencontre]}],
               "clubs": {"08779999": {"nom": "AUTRE", "salle": {"nom": "Gymnase"}, "joueurs": joueurs}}}
    vues = []
    vrai_tableau = images.Rendu.tableau
    monkeypatch.setattr(images.Rendu, "tableau", lambda self, colonnes, lignes, *a, **k: (
        vues.append(lignes), vrai_tableau(self, colonnes, lignes, *a, **k))[1])
    images.images_adversaires(donnees, tmp_path, date(2026, 11, 16))
    remarques = {l[0].texte: (l[-1].texte, l[-1].sous) for lignes in vues for l in lignes if l[0].texte.startswith("ADV")}
    assert remarques["ADV2 Max"] == ("a joué en 3", "nouvel inscrit · déjà 1× en 9")
    assert remarques["ADV3 Max"] == ("a joué en 4, 5", None)
    assert remarques["ADV4 Max"] == ("nouvel inscrit", None)
    nouveau = next(l[-1] for lignes in vues for l in lignes if l[0].texte == "ADV4 Max")
    assert nouveau.alternatives == ("nouveau",) and nouveau.couleur == images.OK_TEXTE


def test_meilleur_classement_d_un_adversaire():
    c = images._cel_meilleur({"points": 961, "meilleur": {"points": 1452, "annee": "2006"}})
    assert (c.texte, c.apres, c.gras, c.couleur) == ("1 452", "(2006)", True, images.ATT_TEXTE)  # 491 points de plus : en orange
    c = images._cel_meilleur({"points": 973, "meilleur": {"points": 1020, "annee": "2024"}})
    assert (c.texte, c.gras, c.couleur) == ("1 020", False, images.DOUX)
    assert images._cel_meilleur({"points": 973}).texte == "" and images._cel_meilleur({"meilleur": None}).texte == ""


def test_sous_titre_long_sur_deux_lignes():
    court = "reçoit CHARENTON TT 1 · C.O.S.E.C"
    assert images.lignes_sous_titre(court, 684) == [court]
    long_ = ("se déplace à LAGNY SUR MARNE TENNIS DE TABLE 11 · Gymnase des Hauts de Lagny, "
             "12 avenue du Général de Gaulle, 77400 LAGNY-SUR-MARNE")
    lignes = images.lignes_sous_titre(long_, 684)
    assert lignes[0] == "se déplace à LAGNY SUR MARNE TENNIS DE TABLE 11"  # coupé au « · »
    assert 2 <= len(lignes) <= 3 and all(images.largeur_texte(l, 19) <= 684 for l in lignes)


def test_ajustement_du_texte():
    texte, taille = images.ajuster("MARTIMORT Christophe", 120, 23, alternatives=["MARTIMORT C.", "MARTIMORT"])
    assert texte in ("MARTIMORT C.", "MARTIMORT") or texte.endswith("…")
    assert images.largeur_texte(texte, taille) <= 120
    assert images.paginer(list(range(40))) == [list(range(20)), list(range(20, 40))]


def test_feuilles_de_match_de_la_derniere_journee(tmp_path):
    def partie(gagne, sets, double=False):
        nous = [{"nom": "GUITTON", "prenom": "Marc", "points": 1410}] + ([{"nom": "LARDE", "prenom": "J", "points": 889}] if double else [])
        eux = [{"nom": "PRIEM", "prenom": "Mickaël", "points": 932}] + ([{"nom": "ALLIAUME", "prenom": "J", "points": 1000}] if double else [])
        return {"double": double, "nous": nous, "eux": eux, "sets": sets, "gagne": gagne, "forfait": False, "abandon": False,
                "non_compte": False, "score": [0, 0]}
    rencontre = {"journee": 3, "date": "2026-10-16", "equipe": "VAIRES 1", "adversaire": "BRIE ASTT 2", "domicile": False,
                 "division": "Départementale 1", "score": [8, 6], "bilan": [{"nom": "GUITTON", "prenom": "Marc", "v": 3, "n": 3}],
                 "parties": [partie(True, [[11, 8], [9, 11], [11, 7], [13, 11]]), partie(False, [[4, 11]] * 3, double=True)]}
    sans_feuille = {**rencontre, "equipe": "VAIRES 2", "parties": [], "score": None, "bilan": []}
    ancienne = {**rencontre, "journee": 2}
    sorties = images.images_rencontres({**CLUB, "journees": [2, 3], "rencontres": [ancienne, rencontre, sans_feuille]}, tmp_path)
    assert [(c.name, t) for c, t in sorties] == [("rencontres_J3_V1.png", "Vaires 1 : feuille de match J3")]


def test_forme_des_adversaires_dans_l_image():
    from ttvaires.images import _cel_forme, _hors_championnat

    f = {"v": 12, "d": 0, "points": 46.4, "competitions": [
        {"nom": "Championnat", "v": 8, "d": 0, "points": 30}, {"nom": "Critérium fédéral", "v": 3, "d": 0, "points": 12},
        {"nom": "Tournois", "v": 1, "d": 0, "points": 4.4}]}
    assert _cel_forme(f).texte == "12/12 +46" and _cel_forme({**f, "points": -0.3}).texte == "12/12 ±0"
    assert _cel_forme({"v": 2, "d": 10, "points": -67}).texte == "2/12 -67"
    assert _cel_forme({"v": 0, "d": 0, "points": 0}).texte == "0 partie" and _cel_forme(None).texte == ""
    assert _hors_championnat(f) == "critérium 3/3 · tournois 1/1" and _hors_championnat(None) == ""
    assert _hors_championnat({"competitions": [{"nom": "Top Jeune Departemental", "v": 2, "d": 1}]}) == "Top Jeune 2/3"

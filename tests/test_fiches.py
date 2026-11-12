"""Fiches des joueurs : statistiques de manches, remontées, bilan par niveau d'adversaire (noms fictifs)."""

from ttvaires import fiches
from ttvaires.virtuel import analyser, etats_des_feuilles

CHAMPIONNAT = "Championnat par équipes M"


def _p(jour, victoire, manches=None, ecart=0, points=None, competition=CHAMPIONNAT, **autres):
    return {"date": jour, "competition": competition, "division": None, "championnat": competition == CHAMPIONNAT, "coef": 1,
            "adversaire": "DUPOND Jean", "adv_points": 800 + ecart, "pts_joueur": 800, "ecart": ecart, "victoire": victoire,
            "points": points if points is not None else (6 if victoire else -5), "manches": manches, "abandon": False, **autres}


PARTIES = [
    _p("2026-09-25", True, [[11, 5], [11, 7], [11, 9]], ecart=-120),                       # 3-0 contre plus faible
    _p("2026-09-25", True, [[9, 11], [8, 11], [11, 6], [12, 10], [11, 8]], ecart=30),      # mené 0-2, gagné à la belle (perf)
    _p("2026-10-02", False, [[11, 9], [11, 8], [9, 11], [7, 11], [10, 12]], ecart=-10),    # menait 2-0, perdu à la belle (contre)
    _p("2026-10-02", True, [[5, 11], [11, 9], [11, 4], [13, 11]], ecart=90),               # 3-1 après la 1re manche perdue (perf)
    _p("2026-10-16", False, [[4, 11], [6, 11], [9, 11]], ecart=200),                       # 0-3 contre plus fort
    _p("2026-10-17", False, None, ecart=60, competition="Tournoi de Lagny"),               # saisie sans les manches
    _p("2026-10-17", True, [[11, 3]], ecart=-300, competition="Tournoi de Lagny", abandon=True),  # abandon de l'adversaire
]


def test_parties_en_3_4_et_5_manches_et_belles():
    m = fiches.stats_manches(PARTIES)
    assert (m["avec_detail"], m["sans_detail"]) == (5, 2)  # la partie sans manches et l'abandon : hors statistiques
    assert m["formats"] == [{"manches": 3, "jouees": 2, "gagnees": 1}, {"manches": 4, "jouees": 1, "gagnees": 1},
                            {"manches": 5, "jouees": 2, "gagnees": 1}]
    assert m["belles"] == {"jouees": 2, "gagnees": 1} and m["autres_formats"] == 0
    assert m["manches"] == [11, 9]  # 3 + 3 + 2 + 3 + 0 gagnées, 0 + 2 + 3 + 1 + 3 perdues
    assert m["serrees"] == [5, 4]   # manches à deux points d'écart : gagnées, perdues
    assert m["points"] == [sum(a for p in PARTIES[:5] for a, _ in p["manches"]), sum(b for p in PARTIES[:5] for _, b in p["manches"])]


def test_autre_format_et_resultat_incoherent():
    deux_gagnantes = _p("2026-11-01", True, [[11, 9], [8, 11], [11, 6]])   # au meilleur des trois manches : une belle
    incoherent = _p("2026-11-01", True, [[5, 11], [6, 11], [7, 11]])        # manches du perdant : saisie douteuse
    m = fiches.stats_manches([deux_gagnantes, incoherent])
    assert (m["avec_detail"], m["sans_detail"], m["autres_formats"]) == (1, 1, 1)
    assert m["belles"] == {"jouees": 1, "gagnees": 1} and all(f["jouees"] == 0 for f in m["formats"])


def test_remontees_avances_perdues_et_premiere_manche():
    r = fiches.stats_remontees(PARTIES)
    assert (r["remontees"], r["remontees_de_2"]) == (2, 1)                    # 0-2 -> 3-2, et 0-1 -> 3-1
    assert (r["avances_perdues"], r["avances_perdues_de_2"]) == (1, 1)        # 2-0 -> 2-3
    assert r["premiere_gagnee"] == {"jouees": 2, "gagnees": 1} and r["premiere_perdue"] == {"jouees": 3, "gagnees": 2}


def test_bilan_par_niveau_d_adversaire():
    n = {x["cle"]: x for x in fiches.stats_niveaux(PARTIES)}
    assert (n["plus_faible"]["v"], n["plus_faible"]["d"]) == (2, 0)  # -120 et -300
    assert (n["meme"]["v"], n["meme"]["d"]) == (1, 1)                # +30 et -10 : à moins de 50 points
    assert (n["plus_fort"]["v"], n["plus_fort"]["d"]) == (1, 2)      # +90, +200, +60
    assert n["plus_fort"]["points"] == 6 - 5 - 5 and [x["titre"] for x in fiches.stats_niveaux([])][0] == "Contre plus faible"
    assert fiches.niveau(50) == "meme" and fiches.niveau(51) == "plus_fort" and fiches.niveau(-51) == "plus_faible"


def test_series_competitions_perfs_et_contres():
    assert fiches.stats_series(PARTIES) == {"meilleure": 2, "en_cours": 1, "en_cours_victoires": True}
    assert fiches.stats_series([]) == {"meilleure": 0, "en_cours": 0, "en_cours_victoires": False}
    assert [(c["nom"], c["v"], c["d"]) for c in fiches.stats_competitions(PARTIES)] == [("Championnat", 3, 2), ("Tournois", 1, 1)]
    nb_perfs, perfs, nb_contres, contres = fiches._extremes(PARTIES)
    assert (nb_perfs, [p["ecart"] for p in perfs]) == (2, [90, 30]) and (nb_contres, [p["ecart"] for p in contres]) == (1, [-10])


def _virtuel():
    return {"genere_le": "2026-10-20T08:00", "saison": "2026-2027", "phase": 1, "debut": "2026-07-01",
            "club": {"numero": "08770250", "nom": "CVTT VAIRES"},
            "joueurs": [
                {"id": "100", "nom": "MARTIN", "prenom": "Léa", "sexe": "F", "categorie": "S", "equipe": "V2", "officiels": 800,
                 "virtuels": 812, "total": 12, "classement": 8, "classement_virtuel": 8, "parties": PARTIES, "inconnu": False,
                 "alignements": [{"journee": 1, "date": "2026-09-25", "equipe": "V2"}]},
                {"id": "200", "nom": "bernard", "prenom": "Tom", "sexe": "M", "categorie": "C", "equipe": None, "officiels": None,
                 "virtuels": None, "total": 0, "classement": None, "classement_virtuel": None, "parties": [], "inconnu": False},
            ]}


def test_fiche_de_chaque_joueur_avec_sa_courbe():
    d = fiches.donnees_fiches(_virtuel())
    assert [j["nom"] for j in d["joueurs"]] == ["bernard", "MARTIN"]  # ordre alphabétique, sans tenir compte de la casse
    tom, lea = d["joueurs"]
    assert tom["courbe"] is None and tom["bilan"] == {"v": 0, "d": 0, "points": 0} and tom["parties"] == []
    assert lea["bilan"] == {"v": 4, "d": 3, "points": 4 * 6 - 3 * 5} and (lea["nb_perfs"], lea["nb_contres"]) == (2, 1)
    assert len(lea["courbe"]["serie"]) == len(d["semaines"]) and lea["courbe"]["serie"][0] == 800
    assert lea["alignements"] == [{"journee": 1, "date": "2026-09-25", "equipe": "V2"}]
    assert lea["parties"][1]["manches"][0] == [9, 11] and d["seuil_niveau"] == 50
    assert "manches connues : championnat 5/5, autres compétitions 0/2" in fiches.resume(d)
    assert lea["historique"] is None and "historiques des classements : 0/2" in fiches.resume(d)


def test_historique_du_classement_et_meilleur_classement():
    # juillet et janvier : points officiels des phases ; les autres mois (situation mensuelle) ne comptent pas
    historique = [[2019, 7, 650], [2020, 1, 702], [2020, 7, 702], [2021, 1, 688], [2026, 7, 640], [2026, 9, 655], [2026, 10, 661]]
    h = fiches.stats_historique(historique)
    assert h["phases"] == [[2019, 7, 650], [2020, 1, 702], [2020, 7, 702], [2021, 1, 688], [2026, 7, 640]]
    assert h["meilleur"] == {"points": 702, "annee": 2020, "mois": 7, "classement": 7, "actuel": False}  # à égalité : le plus récent
    assert fiches.stats_historique([[2026, 7, 512]])["meilleur"]["actuel"] is True                      # un débutant : son record, maintenant
    assert fiches.stats_historique([[2026, 9, 530], [2026, 10, 541]])["phases"] == [[2026, 9, 530], [2026, 10, 541]]  # sans point de phase
    assert fiches.stats_historique(None) is None and fiches.stats_historique([]) is None
    j = {**_virtuel()["joueurs"][0], "historique": historique}
    assert fiches.fiche(j)["historique"]["meilleur"]["points"] == 702


def test_phase_2_les_parties_de_la_phase_1_comptent_aussi():
    j = {**_virtuel()["joueurs"][0], "parties": PARTIES[4:5], "phase1": {"officiels": 780, "parties": PARTIES[:4]}}
    assert [p["date"] for p in fiches.parties_de_la_saison(j)] == [p["date"] for p in PARTIES[:5]]
    assert fiches.fiche(j)["bilan"]["v"] == 3


def test_manches_vues_du_joueur_dans_le_classement_virtuel():
    """Manches lues dans la feuille de match (ou la liste des parties), remises du côté du joueur."""
    lic = lambda n, pts: {"identifier": n, "points": pts, "person": {"familyName": "NOM", "givenName": "Prénom"}}
    manches = [{"homeScore": 11, "awayScore": 8}, {"homeScore": 9, "awayScore": 11}, {"homeScore": 11, "awayScore": 6},
               {"homeScore": 11, "awayScore": 9}]
    contest = {"id": 1, "name": "FED_Championnat de France par Equipes Masculin"}
    partie = {"id": 7, "date": "2026-09-25T00:00:00", "homePlayer": lic("9", 900), "awayPlayer": lic("100", 800),
              "winner": "home", "contest": contest, "doubleOpposition": False}
    feuilles = {1: {"division": {"name": "D2"}, "games": [{"id": 7, "sets": manches}, {"id": 8, "sets": [], "abandonment": True}]}}
    etats = etats_des_feuilles(feuilles)
    assert etats[7]["manches"] == [[11, 8], [9, 11], [11, 6], [11, 9]] and etats[8]["manches"] is None and etats[8]["abandon"]
    competitions = {1: {"nom": contest["name"], "coef": 1}}
    lignes, _, _ = analyser("100", [partie], competitions, etats, "2026-07-01", "2026-12-31")
    assert lignes[0]["manches"] == [[8, 11], [11, 9], [6, 11], [9, 11]] and not lignes[0]["victoire"]  # joueur « away »
    assert fiches.detail_fiable(lignes[0]) and fiches.score(lignes[0]["manches"]) == (1, 3)
    # Manches données dans la liste des parties elle-même (sans feuille de match) : même résultat
    lignes, _, _ = analyser("100", [{**partie, "sets": manches}], competitions, {}, "2026-07-01", "2026-12-31")
    assert lignes[0]["manches"][0] == [8, 11] and lignes[0]["abandon"] is False


def test_page_publiee_avec_les_autres_pages_du_club():
    from ttvaires import netlify, publier
    publie, titre, description = publier.PUBLIES["fiches_vaires.html"]
    assert (publie, titre) == ("fiches.html", "Fiches des joueurs") and "manches" in description
    assert netlify.ORDRE_CLUB.index("fiches_vaires.html") == netlify.ORDRE_CLUB.index("progression_vaires.html") + 1

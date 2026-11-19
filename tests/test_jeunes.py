from collections import Counter
from datetime import date

from ttvaires import jeunes


def test_poules_des_jeunes_recopiees_des_captures():
    """Chaque équipe joue une fois par journée (une exempte en moins de 13 ans, 7 équipes) et rencontre
    chacune des autres une seule fois ; les vendredis du calendrier du comité."""
    assert all(date.fromisoformat(d).weekday() == 4 for d in jeunes.JOURNEES) and len(jeunes.JOURNEES) == 7
    for e, taille in zip(jeunes.EQUIPES, (8, 7)):
        noms = jeunes.equipes_de_la_poule(e)
        assert len(noms) == taille and e["libelle"] in noms and len(e["journees"]) == 7
        for journee in e["journees"]:
            presentes = [n for paire in journee for n in paire if n]
            assert sorted(presentes) == sorted(noms)
            assert sum(None in paire for paire in journee) == (taille % 2)
        paires = Counter(frozenset(p) for j in e["journees"] for p in j if None not in p)
        assert len(paires) == taille * (taille - 1) // 2 and set(paires.values()) == {1}
        assert all(jeunes.club_et_numero(n)[0] in jeunes.CLUBS for n in noms)


def test_calendrier_des_deux_equipes_de_vaires():
    d = jeunes.donnees()
    v1, v2 = d["equipes"]
    assert (v1["libelle"], v1["division"], v1["poule"], v1["categories"]) == ("VAIRES CVTT 1", "Moins de 15 ans", "Poule 3", ["P", "B", "M"])
    assert (v2["libelle"], v2["division"], v2["poule"], v2["categories"]) == ("VAIRES CVTT 2", "Moins de 13 ans", "Poule 1", ["P", "B"])
    assert [(r["journee"], r["vaires_domicile"], r["adversaire"]["libelle"]) for r in v1["rencontres"][:2]] == [
        (1, True, "CTT MONTHYON 1"), (2, False, "ROISSY TT US 3")]
    assert v1["rencontres"][0]["adversaire"]["club"] == "08771201" and not v1["rencontres"][0]["date_a_confirmer"]
    # Moins de 13 ans : Vaires exempte à la J2, dates du calendrier du comité à confirmer
    assert [r["adversaire"]["libelle"] if r["adversaire"] else None for r in v2["rencontres"]] == [
        "CTT MONTHYON 2", None, "ST THIBAULT 2", "APOZOIR 2", "ROISSY TT US 4", "VILLEPARISIS TT 2", "SERRIS ATT 3"]
    assert all(r["date_a_confirmer"] for r in v2["rencontres"]) and v2["rencontres"][3]["vaires_domicile"] is False
    # Club pas encore retrouvé : son nom tient lieu de numéro (la page dit « pas encore lu »)
    assert v2["rencontres"][2]["adversaire"]["club"] == "ST THIBAULT"
    d = jeunes.donnees(numeros={"ST THIBAULT": "08770999"})
    assert d["equipes"][1]["rencontres"][2]["adversaire"]["club"] == "08770999"
    assert [c["libelle"] for c in d["equipes"][1]["classement"]][:2] == ["VAIRES CVTT 2", "CTT MONTHYON 2"]
    assert d["espace"] == "jeunes" and "__DONNEES_JSON__" not in jeunes.page().decode("utf-8")


def test_qui_peut_jouer_dans_chaque_equipe():
    """La catégorie de l'équipe et les plus jeunes : un benjamin joue en moins de 13 et en moins de 15 ans."""
    assert jeunes.peut_jouer("B1", "moins de 13 ans") and jeunes.peut_jouer("B2", "moins de 15 ans")
    assert jeunes.peut_jouer("P", "moins de 13 ans") and jeunes.peut_jouer("M2", "moins de 15 ans")
    assert not jeunes.peut_jouer("M1", "moins de 13 ans") and not jeunes.peut_jouer("C1", "moins de 15 ans")
    assert not jeunes.peut_jouer(None, "moins de 15 ans") and not jeunes.peut_jouer("V40", "moins de 15 ans")
    assert jeunes.jeune({"categorie": "M2"}) and not jeunes.jeune({"categorie": "S"}) and not jeunes.jeune({})


def test_numeros_des_clubs_retrouves_par_leur_nom():
    clubs = {"08770001": {"nom": "A.T.T. SERRIS", "equipes": {"SERRIS ATT"}},
             "08770002": {"nom": "AP OZOIR", "equipes": {"AP OZOIR"}},
             "08770003": {"nom": "CS MEAUX TT", "equipes": {"MEAUX TT CS"}},
             "08770004": {"nom": "ASL MEAUX", "equipes": {"MEAUX ASL"}},
             "08770005": {"nom": "TT ST THIBAULT DES VIGNES", "equipes": {"ST THIBAULT DES VIGNES"}}}
    assert jeunes.associer("SERRIS ATT", clubs) == "08770001"          # nom d'équipe identique
    assert jeunes.associer("MEAUX TT CS", clubs) == "08770003"
    assert jeunes.associer("APOZOIR", clubs) == "08770002"             # lettres collées
    assert jeunes.associer("ST THIBAULT", clubs) == "08770005"         # mot distinctif
    assert jeunes.associer("MEAUX", clubs) is None                     # deux clubs : on ne devine pas
    assert jeunes.associer("COULOMMIERS TT", clubs) is None


def test_jeunes_des_clubs_adverses_loisir_compris(tmp_path):
    """Avec `garder` (page /jeunes/) : seuls les jeunes qui ont l'âge restent, licences loisir comprises ;
    sans liste du club, personne (on ne connaît pas leur âge)."""
    from test_adversaires import MEAUX, FauxPingpocket, _donnees, _ecran
    from ttvaires.adversaires import completer_avec_pingpocket, joueurs_a_suivre

    base = f"/app/fftt/clubs/{MEAUX}/licencies?SORT="
    pages = {base + "CATEGORY": _ecran("par catégorie d'âge", [("Sénior", [("1", "ALIGNE Paul", "1210")]),
                                                              ("Minime 2", [("5", "MINIME Leo", "640")]),
                                                              ("Benjamin 1", [("6", "BENJ Lou", "L")]),
                                                              ("Cadet 1", [("7", "CADET Max", "700")])]),
             base + "LICENCE_STATE": _ecran("par licences à jour", [("Licences à jour", [(i, "", "") for i in "1567"])])}
    client = FauxPingpocket(en_ligne=True, pages=pages, en_cache=[f"/app/fftt/licencies/{i}/graphiques/historique-classement"
                                                                  for i in "1567"])
    donnees = _donnees()
    completer_avec_pingpocket(client, donnees, tmp_path, garder=jeunes.jeune)
    joueurs = {j["id"]: j for j in donnees["clubs"][MEAUX]["joueurs"]}
    assert set(joueurs) == {"5", "6"} and joueurs["6"]["loisir"] and not joueurs["5"]["loisir"]
    # Forme : tous les jeunes réinscrits (même à 500 points), pas les licences loisir
    donnees["equipes"] = [{"rencontres": [{"adversaire": {"club": MEAUX}, "score": None, "date": "2026-11-27"}]}]
    assert set(joueurs_a_suivre(donnees, "2026-11-19", tous=True)[1]) == {"5"}
    # Club sans liste : les joueurs des feuilles de match n'ont pas d'âge connu
    donnees = _donnees()
    completer_avec_pingpocket(FauxPingpocket(en_ligne=True), donnees, tmp_path, garder=jeunes.jeune)
    assert donnees["clubs"][MEAUX]["joueurs"] == []


def test_adversaires_des_jeunes_de_bout_en_bout(monkeypatch):
    from ttvaires import adversaires, fftt

    monkeypatch.setattr(jeunes, "trouver_clubs", lambda client, debut: {"SERRIS ATT": "08770001", "COULOMMIERS TT": None})
    monkeypatch.setattr(fftt, "id_interne_club", lambda client, numero, debut: numero)
    monkeypatch.setattr(fftt, "rencontres_club", lambda client, id_club, debut, fin, ttl: [])
    monkeypatch.setattr(fftt, "details", lambda client, rencontres, auj, etats=None: {})
    vus = {}

    def pingpocket(client, donnees, *args, garder=None, **kwargs):
        vus["garder"] = garder
        donnees["clubs"]["08770001"]["joueurs"] = [{"id": "7123456", "nom": "JEUNE", "prenom": "Lou", "categorie": "B1",
                                                   "renouvele": True, "loisir": True}]
    monkeypatch.setattr(adversaires, "completer_avec_pingpocket", pingpocket)
    monkeypatch.setattr(adversaires, "ajouter_forme", lambda *a, tous=False: vus.setdefault("tous", tous))
    donnees = adversaires.recuperer_jeunes(object(), aujourdhui=date(2026, 11, 19))
    assert vus == {"garder": jeunes.jeune, "tous": True}
    # Clubs connus (Vaires exclue) : Monthyon, Dammartin, et Serris retrouvé ; Coulommiers pas encore
    assert set(donnees["clubs"]) == {"08771201", "08770937", "08770001"} and donnees["numeros"] == {"SERRIS ATT": "08770001"}
    page = jeunes.donnees(donnees)
    assert page["clubs"]["08770001"]["joueurs"][0]["loisir"] and "7123456" not in str(page)
    serris = [r for r in page["equipes"][0]["rencontres"] if r["adversaire"]["libelle"] == "SERRIS ATT 2"]
    assert serris[0]["adversaire"]["club"] == "08770001"


def test_page_jeunes_publiee_et_reliee(tmp_path):
    """/jeunes/ : page de la mise à jour (jeunes_vaires.html) publiée avec le mot de passe du club, reliée
    aux autres espaces (et eux à elle)."""
    import json
    from test_tournois import _crypto
    from ttvaires import netlify, publier
    _crypto()
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    (sortie / "jeunes_vaires.html").write_bytes(jeunes.page())
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-19T08:00", "fin": "2026-11-19T08:05", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["jeunes_vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "g/p", "b")
    dossier = netlify.construire(site, tmp_path / "netlify", "secret", "", "club")
    page = (dossier / "jeunes" / "index.html").read_text(encoding="utf-8")
    assert "MONTHYON" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page
    assert '{"chemin": "jeunes", "titre": "Championnat des jeunes"}' in (dossier / "club" / "index.html").read_text(encoding="utf-8")
    for gabarit in ("gabarit_cal.html", "gabarit_indivs.html", "gabarit_tournois.html", "gabarit_77.html", "gabarit_championnat.html"):
        assert 'id="vers-jeunes"' in netlify.Path(netlify.__file__).with_name(gabarit).read_text(encoding="utf-8")

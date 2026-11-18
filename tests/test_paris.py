import json
from collections import Counter
from datetime import date

from ttvaires import paris


def test_calendrier_et_grille_du_championnat_de_paris():
    """Sept vendredis ; à chaque journée, chaque position joue une fois ; sur la saison, chaque équipe
    rencontre les sept autres une seule fois (recopié des documents de la ligue)."""
    assert all(date.fromisoformat(d).weekday() == 4 for d in paris.JOURNEES) and len(paris.JOURNEES) == 7
    grille = paris.rencontres_de_la_poule()
    for j in range(1, 8):
        positions = [p for jj, _, a, b in grille if jj == j for p in (a, b)]
        assert sorted(positions) == list(range(1, 9))
    paires = Counter(frozenset((a, b)) for _, _, a, b in grille)
    assert len(paires) == 28 and set(paires.values()) == {1}
    domicile = Counter(a for _, _, a, _ in grille)
    assert set(domicile.values()) <= {3, 4}


def test_les_trois_equipes_de_vaires_et_leur_calendrier():
    d = paris.donnees()
    assert [(e["nom"], e["code"], e["poule"], e["position"]) for e in d["equipes"]] == [
        ("Vaires 1", "HO", 1, 1), ("Vaires 2", "PH", 2, 5), ("Vaires 3", "D2", 3, 5)]
    for e in d["equipes"]:
        assert len(e["equipes"]) == 8 and sum(p["vaires"] for p in e["equipes"]) == 1
        assert len(e["calendrier"]) == 7 and len({c["adversaire"] for c in e["calendrier"]}) == 7
    v1 = d["equipes"][0]
    # J1 : 1/8, Vaires (1) reçoit Villemomble 2 ; J2 : 7/1, Vaires se déplace à Nogent
    noms = {p["position"]: p["nom"] for p in v1["equipes"]}
    assert (v1["calendrier"][0]["a_domicile"], noms[v1["calendrier"][0]["adversaire"]]) == (True, "VILLEMOMBLE SP 2")
    assert (v1["calendrier"][1]["a_domicile"], noms[v1["calendrier"][1]["adversaire"]]) == (False, "NOGENT TT 1")
    v2 = d["equipes"][1]
    noms = {p["position"]: p["nom"] for p in v2["equipes"]}
    assert (v2["calendrier"][0]["a_domicile"], noms[v2["calendrier"][0]["adversaire"]]) == (False, "VILLEMOMBLE SP 3")
    assert "licence" not in str(d)
    html = paris.page().decode("utf-8")
    assert "__DONNEES_JSON__" not in html and "VILLEMOMBLE SP 2" in html


def test_page_paris_avec_le_mot_de_passe_du_club_et_liens_entre_les_espaces(tmp_path):
    """/paris/ : page de la mise à jour (paris_vaires.html, comme /77/) publiée avec le mot de passe du club,
    listée dans « Autres espaces » de /club/, et reliée dans les deux sens à /cal/, /indivs/, /tournois/, /77/."""
    import base64
    import json
    import re
    from test_tournois import _crypto
    from ttvaires import netlify, publier
    _crypto()
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    (sortie / "vaires.html").write_text("<p>adversaires</p>", encoding="utf-8")
    (sortie / "paris_vaires.html").write_bytes(paris.page())
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-18T08:00", "fin": "2026-11-18T08:05", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["vaires.html", "paris_vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "g/p", "b")
    for dossier in (netlify.construire(site, tmp_path / "netlify", "secret", "", "club"),
                    netlify.site_github(site, tmp_path / "github", "secret", "club")):
        page = (dossier / "paris" / "index.html").read_text(encoding="utf-8")
        assert "VILLEMOMBLE" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page
        chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', page, re.S)[1].strip()
        assert publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club")) == paris.page()
        club = (dossier / "club" / "index.html").read_text(encoding="utf-8")
        assert '{"chemin": "paris", "titre": "Championnat de Paris"}' in club
    html = paris.page().decode("utf-8")
    assert all(f"`${{BASE}}/{e}/`" in html for e in ("club", "indivs", "tournois", "cal", "77")) and "/lundi/" not in html
    for gabarit in ("gabarit_cal.html", "gabarit_indivs.html", "gabarit_tournois.html", "gabarit_77.html"):
        autre = netlify.Path(netlify.__file__).with_name(gabarit).read_text(encoding="utf-8")
        assert 'id="vers-paris"' in autre and ("`${BASE}/paris/`" in autre or '["vers-paris", "paris"]' in autre)


def test_controle_du_championnat_de_paris_dans_l_api(capsys, monkeypatch):
    """Le journal dit quelles compétitions par équipes du club sont dans l'API, et les poules de Paris
    s'il y en a (noms de compétitions, divisions, équipes ; aucun nom de joueur)."""
    from ttvaires import fftt

    def rencontre(competition, jour, nous="VAIRES CTT 1"):
        club = lambda num, nom: {"name": nom, "clubs": [{"identifier": num, "id": 1, "name": nom}]}
        return {"division": {"name": "Division Honneur", "contest": {"name": competition}}, "pool": {"id": 77},
                "day": {"position": 1}, "date": jour + "T20:00:00",
                "homeOpponent": {"team": club("08770250", nous)}, "awayOpponent": {"team": club("08930113", "VILLEMOMBLE SP 2")}}
    rencontres = [rencontre("Championnat de France par Equipes Masculin", "2026-09-25"),
                  rencontre("Championnat de Paris IDF", "2026-11-27")]
    monkeypatch.setattr(fftt, "id_interne_club", lambda client, numero, debut: 1)
    monkeypatch.setattr(fftt, "lire_tout", lambda client, chemin, ttl: rencontres)
    assert paris.diagnostic_api(None, "08770250", date(2026, 11, 18)) == {
        "Championnat de France par Equipes Masculin": 1, "Championnat de Paris IDF": 1}
    journal = capsys.readouterr().out
    assert "Championnat de Paris IDF : 1 rencontres" in journal and "équipe(s) VAIRES CTT 1" in journal
    rencontres[:] = rencontres[:1]
    paris.diagnostic_api(None, "08770250", date(2026, 11, 18))
    assert "aucune rencontre dans l'API" in capsys.readouterr().out


def test_adversaires_de_paris_effectif_meilleur_classement_et_forme(monkeypatch):
    """Clubs adverses des trois poules : joueurs alignés en championnat de France (API), complétés par
    pingpocket (effectif, meilleur classement) et leur forme ; la page n'a aucun numéro de licence."""
    from ttvaires import adversaires, fftt

    villemomble = {"name": "VILLEMOMBLE SP 2", "clubs": [{"identifier": "08930113", "id": 93, "name": "VILLEMOMBLE SPORTS"}]}
    autre = {"name": "AUTRE 1", "clubs": [{"identifier": "08939999", "id": 9, "name": "AUTRE"}]}
    rencontre = {"id": 501, "homeOpponent": {"team": villemomble}, "awayOpponent": {"team": autre}, "day": {"position": 2},
                 "date": "2026-10-02T20:00:00", "division": {"name": "PR Ph1", "contest": {"name": "FED_Championnat de France par Equipes Masculin"}}}
    feuille = {**rencontre, "homeSheetMatches": [{"identifier": "A", "player": {"identifier": "7123456", "points": 1180,
               "person": {"familyName": "DUPONT", "givenName": "Marc"}}}], "awaySheetMatches": []}
    monkeypatch.setattr(fftt, "id_interne_club", lambda client, numero, debut: numero)
    monkeypatch.setattr(fftt, "rencontres_club", lambda client, id_club, debut, fin, ttl: [rencontre] if id_club == "08930113" else [])
    monkeypatch.setattr(fftt, "details", lambda client, rencontres, auj, etats=None: {501: feuille} if rencontres else {})

    def pingpocket(client, donnees, *args, **kwargs):  # effectif complet et meilleur classement (pages lues par le PC)
        club = donnees["clubs"]["08930113"]
        club["effectif_complet"], club["date_effectif"] = True, "2026-11-12T20:00"
        club["joueurs"][0].update(categorie="V40", points_mensuels=1205, meilleur={"points": 1450, "annee": "2015"}, renouvele=True)
    monkeypatch.setattr(adversaires, "completer_avec_pingpocket", pingpocket)
    monkeypatch.setattr(adversaires, "forme_joueurs", lambda client, licences, detail, debut, fin: {
        "7123456": {"v": 7, "d": 2, "points": 25.5, "virtuels": 1205.5}})
    donnees = adversaires.recuperer_paris(object(), aujourdhui=date(2026, 11, 18))
    assert len(donnees["clubs"]) == 17 and "08770250" not in donnees["clubs"]
    page = paris.donnees(donnees)
    v = page["clubs"]["08930113"]
    assert v["complet"] and v["france"] == [{"numero": 2, "ch": "M", "division": "PR"}]
    assert v["joueurs"] == [{"nom": "DUPONT Marc", "sexe": None, "cat": "V40", "pts": 1205, "meilleur": 1450, "annee": "2015",
                             "v": 7, "d": 2, "gain": 25.5, "virt": 1205.5, "eq": "2", "nb": 1, "nouveau": False}]
    assert page["clubs"]["08771394"]["joueurs"] == [] and "7123456" not in json.dumps(page)

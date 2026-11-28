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
    """Même format que la page adversaires du championnat de France : une équipe par onglet, sept
    rencontres (qui reçoit, adversaire), et le classement de la poule, vide pour l'instant."""
    d = paris.donnees()
    assert [(e["id"], e["nom_court"], e["libelle"], e["division"], e["poule"]) for e in d["equipes"]] == [
        ("v1", "Vaires 1", "VAIRES CTT 1", "Honneur", "Poule 1"), ("v2", "Vaires 2", "VAIRES CTT 2", "Promotion d'Honneur", "Poule 2"),
        ("v3", "Vaires 3", "VAIRES CVTT 3", "Division 2", "Poule 3")]
    for e in d["equipes"]:
        assert len(e["rencontres"]) == 7 and len({r["adversaire"]["libelle"] for r in e["rencontres"]}) == 7
        assert all(r["score"] is None and r["adversaire"]["club"] != paris.CLUB_VAIRES for r in e["rencontres"])
        assert [c["points"] for c in e["classement"]] == [None] * 8 and sum(c["club"] == paris.CLUB_VAIRES for c in e["classement"]) == 1
    v1 = d["equipes"][0]
    # J1 : 1/8, Vaires (1) reçoit Villemomble 2 ; J2 : 7/1, Vaires se déplace à Nogent
    j1, j2 = v1["rencontres"][:2]
    assert (j1["vaires_domicile"], j1["adversaire"]["libelle"], j1["domicile"]["libelle"]) == (True, "VILLEMOMBLE SP 2", "VAIRES CTT 1")
    assert (j2["vaires_domicile"], j2["adversaire"]["libelle"], j2["exterieur"]["libelle"]) == (False, "NOGENT TT 1", "VAIRES CTT 1")
    assert (j2["date"], j2["adversaire"]["club"], j2["adversaire"]["numero"]) == ("2027-01-08", "08940524", 1)
    v2 = d["equipes"][1]
    assert (v2["rencontres"][0]["vaires_domicile"], v2["rencontres"][0]["adversaire"]["libelle"]) == (False, "VILLEMOMBLE SP 3")
    assert d["club"] == {"numero": "08770250", "nom": "CVTT Vaires", "salle": None} and d["clubs"] == {}
    assert "licence" not in str(d)
    html = paris.page().decode("utf-8")
    assert "__DONNEES_JSON__" not in html and "VILLEMOMBLE SP 2" in html
    # La présentation de la page adversaires du championnat de France (gabarit.html), sans brûlage
    assert all(t in html for t in ("Récapitulatif", "Classement de la poule", "Adversaires — clique sur une équipe",
                                   "Meilleur (année)", "Mensuel", "Éq. France"))
    assert "Pour l'équipe" not in html and "Vérifications" not in html


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
    assert '["club", "paris", "jeunes", "indivs", "tournois", "cal", "77"]' in html and "/lundi/" not in html
    assert all(f'id="vers-{e}"' in html for e in ("club", "paris", "jeunes", "indivs", "tournois", "cal", "77"))
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
    assert v["effectif_complet"] and v["nom"] == "VILLEMOMBLE SP" and v["date_effectif"] == "2026-11-12T20:00"
    assert v["equipes"] == [{"libelle": "VILLEMOMBLE SP 2", "numero": 2, "championnat": "M", "division": "PR",
                             "compositions": [{"journee": 2, "date": "2026-10-02", "joueurs": ["j1"]}]}]
    assert v["joueurs"] == [{"id": "j1", "nom": "DUPONT", "prenom": "Marc", "sexe": None, "categorie": "V40", "categorie_long": None,
                             "classement": 11, "points": 1180, "points_mensuels": 1205, "meilleur": {"points": 1450, "annee": "2015"},
                             "renouvele": True, "nouveau": None, "loisir": None,
                             "forme": {"v": 7, "d": 2, "points": 25.5, "virtuels": 1205.5}}]
    assert page["clubs"]["08771394"]["joueurs"] == [] and "7123456" not in json.dumps(page)
    # Vaires 1 reçoit Villemomble 2 à la J1 : la fiche de la rencontre montre ce club
    assert page["equipes"][0]["rencontres"][0]["adversaire"]["club"] == "08930113"


def test_le_bilan_dit_quand_le_championnat_de_paris_arrive_dans_l_api(tmp_path, monkeypatch):
    """Le jour où la ligue saisit les rencontres de Paris, le bilan de l'étape adversaires le dit."""
    from types import SimpleNamespace
    import ttvaires.__main__ as m

    donnees = {"verification": {"journees": [], "clubs": []}, "sources": {}}
    monkeypatch.setattr(m, "recuperer", lambda *a, **k: donnees)
    monkeypatch.setattr(m, "enrichir", lambda d: d)
    monkeypatch.setattr(m.verifications, "afficher_adversaires", lambda *a: "tout est là")
    monkeypatch.setattr(m, "generer_html", lambda d, chemin, *a, **k: chemin)
    monkeypatch.setattr(m, "equipes_du_championnat", lambda *a, **k: {"equipes": []})
    monkeypatch.setattr(m, "donnees_classements", lambda d: d)
    monkeypatch.setattr(m, "faire_images", lambda *a, **k: [])
    monkeypatch.setattr(m, "page_paris", lambda *a, **k: [tmp_path / "paris_vaires.html"])
    monkeypatch.setattr(m, "page_jeunes", lambda *a, **k: tmp_path / "jeunes_vaires.html")
    ctx = SimpleNamespace(archive=False, aujourdhui=date(2026, 11, 25), sortie=tmp_path, images=tmp_path, donnees=lambda d: d)
    competitions = {"FED_Championnat de France par Equipes Masculin": 42}
    monkeypatch.setattr(paris, "diagnostic_api", lambda *a: competitions)
    assert m.page_adversaires(None, "08770250", ctx)[1] == "tout est là"
    # Paris et les jeunes sont lus depuis le 28/11 : seule une autre compétition par équipes est signalée
    competitions.update({"L08_Championnat de Paris IDF": 21, "Chpt Jeunes par Equipes 77 2526": 14})
    assert m.page_adversaires(None, "08770250", ctx)[1] == "tout est là"
    competitions["Coupe Vétérans par équipes"] = 2
    assert m.page_adversaires(None, "08770250", ctx)[1] == (
        "tout est là ; nouveau dans l'API FFTT : Coupe Vétérans par équipes (2 rencontres de Vaires)")


def test_disponibilites_joueurs_du_club_et_noms_colles(tmp_path):
    """Tableau des disponibilités de /paris/ : les joueurs du dernier classement virtuel (pas les loisirs, ils
    n'y sont pas), du mieux au moins bien classé, gardés dans le cache ; les noms collés sont reconnus malgré
    accents, ordre prénom / nom et une petite faute (noms fictifs)."""
    import shutil
    import subprocess

    virtuel = {"genere_le": "2026-11-21T09:25", "joueurs": [
        {"nom": "MARTIN", "prenom": "Paul", "virtuels": 1210.5, "officiels": 1200},
        {"nom": "DUPONT", "prenom": "Aymerik", "virtuels": 1420.0, "officiels": 1400},
        {"nom": "LE CERF", "prenom": "Léa", "virtuels": None, "officiels": 905},
        {"nom": "D'ALMEIDA", "prenom": "Jean-Luc", "virtuels": 640, "officiels": 650}]}
    chemin = tmp_path / "joueurs_vaires.json"
    joueurs = paris.memoriser_joueurs(virtuel, chemin)
    assert [j["nom"] for j in joueurs] == ["DUPONT", "MARTIN", "LE CERF", "D'ALMEIDA"] and joueurs[2]["virtuels"] == 905
    html = paris.page(None, paris.joueurs_memorises(chemin)).decode("utf-8")
    assert '"joueurs_vaires": [{"nom": "DUPONT"' in html and "Disponibilités" in html
    assert paris.joueurs_memorises(tmp_path / "absent.json") is None
    assert '"joueurs_vaires"' not in paris.page().decode("utf-8")  # pas de tableau sans classement virtuel
    if not shutil.which("node"):
        return
    debut, fin = html.index("const mots ="), html.index("function appliquerCollage")
    script = ("const JOUEURS_VAIRES = " + json.dumps(joueurs) + ";\nconst nomJ = (j) => `${j.prenom} ${j.nom}`.trim();\n"
              + html[debut:fin] + "\nconsole.log(JSON.stringify(['Aymerick Dupont', 'paul martin', 'LE CERF Lea', 'Jean Luc d almeida',"
              " 'Inconnu Total', 'Martin'].map((t) => (trouverJoueur(t) || {}).nom || null)));")
    sortie = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout
    assert json.loads(sortie) == ["DUPONT", "MARTIN", "LE CERF", "D'ALMEIDA", None, None]

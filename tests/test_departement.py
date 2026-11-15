"""Page « Clubs du 77 » : clubs du département, leurs équipes et divisions, leurs licenciés (noms fictifs)."""

import json
import time
from datetime import date, datetime

from test_effectif import _liste
from ttvaires import departement, fftt
from ttvaires.reseau import ErreurReseau

VAIRES, CHELLES, LAGNY, CRETEIL = "08770250", "08770001", "08770002", "08940001"


def _equipe(nom, club):
    return {"name": nom, "clubs": [{"identifier": club, "id": int(club[-4:]) + 1, "name": nom.rsplit(" ", 1)[0]}]}


def _match(id_, dom, ext, journee, division="DEP 1 Ph1", poule=10, feminin=False):
    contest = "FED_Championnat de France par Equipes " + ("Féminin" if feminin else "Masculin")
    return {"id": id_, "homeOpponent": {"team": dom}, "awayOpponent": {"team": ext}, "day": {"position": journee},
            "date": "2026-09-25T00:00:00", "pool": {"id": poule, "name": f"Poule {poule}"},
            "division": {"name": division, "contest": {"name": contest}}}


V1, V2, V1F = _equipe("CVTT VAIRES 1", VAIRES), _equipe("CVTT VAIRES 2", VAIRES), _equipe("CVTT VAIRES 1", VAIRES)
C1, C2, L1, L2 = _equipe("CHELLES TT 1", CHELLES), _equipe("CHELLES TT 2", CHELLES), _equipe("LAGNY TT 1", LAGNY), _equipe("LAGNY TT 2", LAGNY)
CR1F = _equipe("CRETEIL 1", CRETEIL)
MATCHS = {  # rencontres de la phase de chaque club (API) ; Vaires 1 et Chelles 1 en régionale, poule 20
    VAIRES: [_match(1, V1, C1, 1, "L08_R3", 20), _match(2, V2, L1, 1), _match(3, V1F, CR1F, 1, "D1 Championnat Feminin 77/94", 30, True)],
    CHELLES: [_match(1, V1, C1, 1, "L08_R3", 20), _match(4, C2, L2, 1, "DEP 2 Ph1", 11)],
    LAGNY: [_match(2, V2, L1, 1), _match(4, C2, L2, 1, "DEP 2 Ph1", 11)],
}
J1 = [MATCHS[VAIRES][1], MATCHS[CHELLES][1], MATCHS[VAIRES][2]]  # divisions du comité : pas la régionale

CATEGORIES_VAIRES = [("Senior", [("1", "MARTIN Paul", "1450", "M"), ("2", "DUPOND Luc", "1210", "M"), ("3", "PETIT Anne", "980", "F"),
                                 ("4", "LOISIR Jean", "L", "M"), ("5", "ANCIEN Marc", "700", "M")]),
                      ("Vétéran 45", [("6", "BERNARD Eric", "1105", "M"), ("7", "SIMON Lucie", "830", "F")]),
                      ("Benjamin 1", [("8", "PETIT Tom", "540", "M")])]
ETAT_VAIRES = [("Licences à jour", [(l, n, c, s) for l, n, c, s in CATEGORIES_VAIRES[0][1][:4] + CATEGORIES_VAIRES[1][1] + CATEGORIES_VAIRES[2][1]]),
               ("Licences non renouvelées", [("5", "ANCIEN Marc", "700", "M")])]


class Client:
    """Répond comme l'API de la FFTT et pingpocket ; note les pages demandées."""

    def __init__(self, listes, sites_cache_seul=()):
        self.listes, self.demandes, self.sites_cache_seul, self.hors_ligne = listes, [], set(sites_cache_seul), False

    def date(self, chemin):
        return time.time() if chemin in self.listes else None

    def disponible(self, site):
        return True

    def en_cache(self, chemin, ttl):
        return False

    def get(self, chemin, ttl=None, entetes=None, valide=None, perime_si_erreur=False):
        self.demandes.append(chemin)
        if chemin.startswith(fftt.API + "/sport_matches?"):
            if "organization.identifier" in chemin:
                membres = J1 if "position%5D=1" in chemin or "position=1" in chemin else []
            else:
                id_ = next(int(x.split("=")[1]) for x in chemin.split("&") if "clubs.id" in x)
                membres = next(m for num, m in MATCHS.items() if int(num[-4:]) + 1 == id_)
            return json.dumps({"@context": "/api/contexts/SportMatch", "hydra:member": membres})
        if chemin in self.listes:
            return self.listes[chemin]
        raise ErreurReseau(chemin)

    def get_plusieurs(self, chemins, ttl=None, message=None, **options):
        res = {}
        for c in chemins:
            try:
                res[c] = self.get(c)
            except ErreurReseau:
                res[c] = None
        return res


def _listes():
    return {f"/app/fftt/clubs/{VAIRES}/licencies?SORT=CATEGORY": _liste(CATEGORIES_VAIRES),
            f"/app/fftt/clubs/{VAIRES}/licencies?SORT=LICENCE_STATE": _liste(ETAT_VAIRES),
            f"/app/fftt/clubs/{CHELLES}/licencies?SORT=CATEGORY": _liste([("Senior", [("9", "FORT Max", "1800", "M")])]),
            f"/app/fftt/clubs/{CHELLES}/licencies?SORT=LICENCE_STATE": _liste([("Licences à jour", [("9", "FORT Max", "1800", "M")])])}


def test_clubs_du_77_equipes_divisions_et_licencies():
    client = Client(_listes())
    d = departement.recuperer_departement(client, VAIRES, aujourdhui=date(2026, 11, 15))
    clubs = {c["numero"]: c for c in d["clubs"]}
    assert set(clubs) == {VAIRES, CHELLES, LAGNY}  # Créteil (94) : hors du département
    v = clubs[VAIRES]
    assert v["vaires"] and [(e["nom"], e["niveau"], e["feminin"]) for e in v["equipes"]] == \
        [("CVTT VAIRES 1", "R3", False), ("CVTT VAIRES 2", "D1", False), ("CVTT VAIRES 1", "D1", True)]
    assert v["niveaux"] == {"R3": 1, "D1": 1, "F:D1": 1} and v["meilleur_niveau"] == "R3"
    # Licenciés de la saison : sans le non renouvelé ; loisir compté à part ; catégories P, B, M... V
    # Catégorie précise (« V45 », « B1 ») et nom de chaque joueur, pour le classement des joueurs du département
    cle = lambda x: (x[0] or 0, x[1], x[2], x[3])
    assert sorted(v["joueurs"], key=cle) == sorted([
        [1450, "M", "S", 0, "MARTIN Paul"], [1210, "M", "S", 0, "DUPOND Luc"], [980, "F", "S", 0, "PETIT Anne"],
        [None, "M", "S", 1, "LOISIR Jean"], [1105, "M", "V45", 0, "BERNARD Eric"], [830, "F", "V45", 0, "SIMON Lucie"],
        [540, "M", "B1", 0, "PETIT Tom"]], key=cle)
    assert v["date_liste"]
    # Force estimée : équipe 1 = les 4 meilleurs (1450, 1210, 1105, 980), équipe 2 = les suivants ; féminine : les joueuses
    forces = {(e["nom"], e["feminin"]): (e["force"], e["nb"]) for e in v["equipes"]}
    assert forces[("CVTT VAIRES 1", False)] == (round((1450 + 1210 + 1105 + 980) / 4), 4)
    assert forces[("CVTT VAIRES 2", False)] == (round((830 + 540) / 2), 2)
    assert forces[("CVTT VAIRES 1", True)] == (round((980 + 830) / 2), 2)
    assert clubs[LAGNY]["joueurs"] is None and d["controle"]["sans_liste"] == ["LAGNY TT"]
    # Poules : équipes triées par force estimée, celles d'autres départements sans données
    poule20 = next(p for p in d["poules"] if p["id"] == 20)
    assert (poule20["niveau"], [(e["nom"], e["force"]) for e in poule20["equipes"]]) == \
        ("R3", [("CHELLES TT 1", 1800), ("CVTT VAIRES 1", 1186)])
    poule30 = next(p for p in d["poules"] if p["id"] == 30)
    assert poule30["feminin"] and [e["dans_le_77"] for e in poule30["equipes"]] == [True, False]
    assert [p["niveau"] for p in d["poules"]][:2] == ["R3", "D1"]  # du plus haut niveau au plus bas
    assert "3 clubs" in departement.resume(d) and "licenciés connus pour 2 clubs" in departement.resume(d)


def test_listes_plafonnees_par_lancement_et_en_ligne_seulement_le_cache(monkeypatch):
    monkeypatch.setattr(departement, "MAX_LISTES", 2)
    client = Client(_listes())
    clubs = {VAIRES: {}, CHELLES: {}, LAGNY: {}}
    res, reportees = departement.listes_licencies(client, clubs)
    assert reportees == 4 and set(res) == {VAIRES} and len([d for d in client.demandes if "licencies" in d]) == 2
    en_ligne = Client(_listes(), sites_cache_seul={"www.pingpocket.fr"})
    res, reportees = departement.listes_licencies(en_ligne, clubs)
    assert reportees == 0 and set(res) == {VAIRES, CHELLES}  # pages envoyées par le PC ; Lagny n'en a pas
    assert not any(LAGNY in d for d in en_ligne.demandes)


def test_niveaux_et_rang():
    assert [fftt.division_courte(x) for x in ("L08_R3", "DEP 2 Ph1", "PRE-REG", "Nationale 3")] == ["R3", "D2", "PR", "N3"]
    assert departement.rang_niveau("N1") < departement.rang_niveau("R1") < departement.rang_niveau("PR") < departement.rang_niveau("D1")
    assert departement.rang_niveau("?") == len(departement.ORDRE_NIVEAUX)


def test_page_publiee_a_son_adresse_avec_le_mot_de_passe_du_club(tmp_path):
    """/77/ : page des données de la mise à jour (comme /indivs/), mot de passe du club, listée dans /club/."""
    import base64
    import re

    from ttvaires import netlify, publier
    from ttvaires.rendu import GABARIT_77, generer_html
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:
        import pytest
        pytest.skip("bibliothèque cryptography indisponible")
    d = departement.recuperer_departement(Client(_listes()), VAIRES, aujourdhui=date(2026, 11, 15))
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    html = generer_html(d, sortie / "departement_77.html", GABARIT_77).read_text(encoding="utf-8")
    assert "__DONNEES_JSON__" not in html and "CVTT VAIRES" in html
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-15T08:00", "fin": "2026-11-15T08:05", "pages": [
        {"nom": "clubs du 77", "resume": "ok", "fichiers": ["departement_77.html"]}]}))
    publier.publier(sortie, site, "secret", "g/p", "b")
    for dossier in (netlify.construire(site, tmp_path / "netlify", "secret", "", "club"),
                    netlify.site_github(site, tmp_path / "github", "secret", "club")):
        page = (dossier / "77" / "index.html").read_text(encoding="utf-8")
        assert "CVTT VAIRES" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page
        chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', page, re.S)[1].strip()
        assert b"CHELLES TT" in publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club"))
        assert '{"chemin": "77", "titre": "Clubs du 77"}' in (dossier / "club" / "index.html").read_text(encoding="utf-8")
    # Liens : /77/ mène aux autres espaces (pas à /lundi/), et ils mènent à /77/
    assert all(f'href="../{e}/"' in html for e in ("club", "indivs", "tournois", "cal")) and "/lundi/" not in html
    for gabarit in ("gabarit_indivs.html", "gabarit_tournois.html", "gabarit_cal.html"):
        assert 'id="vers-77"' in netlify.Path(netlify.__file__).with_name(gabarit).read_text(encoding="utf-8")


class ClientParties(Client):
    """Répond aussi aux parties des joueurs (API FFTT) ; dates des réponses déjà en cache réglables."""

    def __init__(self, listes, parties, dates_parties=None, **options):
        super().__init__(listes, **options)
        self.parties, self.dates_parties, self.ttls, self.details = parties, dates_parties or {}, {}, {}

    def date(self, chemin):
        if "/games?" in chemin:
            return self.dates_parties.get(chemin.split("identifier=")[1].split("&")[0])
        return super().date(chemin)

    def get(self, chemin, ttl=None, entetes=None, valide=None, perime_si_erreur=False):
        if "/games?" in chemin:
            self.demandes.append(chemin)
            lic = chemin.split("identifier=")[1].split("&")[0]
            if ttl is not None or lic not in self.ttls:  # une relecture du cache (contrôle) n'efface pas la lecture
                self.ttls[lic] = ttl
            if ttl is not None:  # nouvelle réponse enregistrée maintenant (ttl None : réponse déjà enregistrée)
                self.dates_parties[lic] = time.time()
            return json.dumps({"hydra:member": self.parties.get(lic, [])})
        if "/contests/" in chemin:
            return json.dumps({"name": "FED_Championnat de France par Equipes Masculin", "coefficient": 1} if chemin.endswith("/1")
                              else {"name": "Tournoi de Lagny", "coefficient": 0.5})
        if "/games/" in chemin:
            self.demandes.append(chemin)
            return json.dumps(self.details[int(chemin.rsplit("/", 1)[1])])
        return super().get(chemin, ttl, entetes, valide, perime_si_erreur)

    def get_plusieurs(self, chemins, ttl=None, message=None, **options):
        res = {}
        for c in chemins:
            try:
                res[c] = self.get(c, ttl)
            except ErreurReseau:
                res[c] = None
        return res


def _partie(id_, lic, points, adv_points, victoire, jour="2026-10-03"):
    joueur = lambda l, p: {"identifier": l, "points": p, "person": {"familyName": "NOM", "givenName": "Prénom"}}
    return {"id": id_, "date": jour + "T00:00:00", "homePlayer": joueur(lic, points), "awayPlayer": joueur("999", adv_points),
            "winner": "home" if victoire else "away", "doubleOpposition": False,
            "contest": {"id": 1, "name": "FED_Championnat de France par Equipes Masculin"}}


def test_points_virtuels_en_ligne_seulement_jeunes_par_defaut():
    from ttvaires.resultats import points_partie
    parties = {"8": [_partie(1, "8", 540, 700, True), _partie(2, "8", 540, 500, False),
                     _partie(3, "8", 540, 900, True, jour="2026-06-10")]}  # phase précédente : ne compte pas
    client = ClientParties(_listes(), parties)
    d = departement.recuperer_departement(client, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True)
    v = next(c for c in d["clubs"] if c["numero"] == VAIRES)
    gagne = points_partie(540, 700, True, 1) + points_partie(540, 500, False, 1)
    # Par défaut, seuls les jeunes sont relus : le benjamin (PETIT Tom, licence 8) ; sa ligne porte [virtuels,
    # gagnés, victoires, défaites, date de lecture de ses parties]
    lu = date.today().isoformat()
    assert [j for j in v["joueurs"] if len(j) == 6] == [[540, "M", "B1", 0, "PETIT Tom", [round(540 + gagne), round(gagne, 1), 1, 1, lu]]]
    assert set(client.ttls) == {"8"}
    assert d["virtuels"] == {"joueurs": 7, "a_relire": 1, "connus": 1, "lus": 1, "reportes": 0, "plus_ancienne": lu,
                             "plus_recente": lu, "perimetre": "jeunes"}  # 7 licences compétition (Vaires 6, Chelles 1)
    assert "points virtuels de 1 joueurs sur 7 (relus : jeunes)" in departement.resume(d)
    assert "licence" not in json.dumps(d)  # pas de numéro de licence dans la page
    # Par défaut : seulement en ligne (pingpocket.fr lu dans les pages du PC) ; sur le PC, aucune partie demandée
    pc = ClientParties(_listes(), parties)
    d = departement.recuperer_departement(pc, VAIRES, aujourdhui=date(2026, 11, 15))
    assert d["virtuels"] is None and not any("/games?" in x for x in pc.demandes)
    en_ligne = ClientParties(_listes(), parties, sites_cache_seul={"www.pingpocket.fr"})
    assert departement.recuperer_departement(en_ligne, VAIRES, aujourdhui=date(2026, 11, 15))["virtuels"]["connus"] == 1


def test_choix_des_joueurs_a_relire_les_autres_gardent_leur_derniere_lecture():
    client = ClientParties(_listes(), {})
    # « adultes » : les 6 adultes compétition relus (sans partie : virtuels = points mensuels), pas le benjamin
    d = departement.recuperer_departement(client, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True, perimetre="adultes")
    assert set(client.ttls) == {"1", "2", "3", "6", "7", "9"} and d["virtuels"]["connus"] == 6
    martin = next(j for c in d["clubs"] if c["numero"] == VAIRES for j in c["joueurs"] if j[4] == "MARTIN Paul")
    assert martin[5][:4] == [1450, 0, 0, 0]
    # « jeunes » ensuite : le benjamin lu ; les adultes, lus il y a moins de 3 jours, gardent leur lecture (sans requête)
    client.ttls.clear()
    d = departement.recuperer_departement(client, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True, perimetre="jeunes")
    assert client.ttls == {"8": departement.TTL_VIRTUELS, **{l: None for l in ("1", "2", "3", "6", "7", "9")}}
    assert d["virtuels"]["connus"] == 7
    # « aucun » : aucune requête, tout ce qui a déjà été lu reste affiché
    client.ttls.clear()
    d = departement.recuperer_departement(client, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True, perimetre="aucun")
    assert set(client.ttls.values()) == {None} and d["virtuels"]["connus"] == 7 and d["virtuels"]["lus"] == 0
    # « tous » sur un appareil neuf : tout le monde ; choix inconnu refusé
    neuf = ClientParties(_listes(), {})
    assert departement.recuperer_departement(neuf, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True, perimetre="tous")["virtuels"]["lus"] == 7
    import pytest
    with pytest.raises(ValueError):
        departement.recuperer_departement(neuf, VAIRES, aujourdhui=date(2026, 11, 15), virtuels=True, perimetre="minimes")


def test_virtuels_relus_apres_3_jours_avec_leur_date_et_plafond_de_securite(monkeypatch):
    monkeypatch.setattr(departement, "MAX_VIRTUELS", 3)
    maintenant = time.time()
    il_y_a = lambda jours: datetime.fromtimestamp(maintenant - jours * 86400).date().isoformat()
    # a, b : jamais lus ; c : lu il y a 4 jours (périmé) ; d : lu il y a une heure
    client = ClientParties({}, {"a": [_partie(1, "a", 600, 600, True)], "c": [_partie(2, "c", 800, 800, False)]},
                           dates_parties={"c": maintenant - 4 * 86400, "d": maintenant - 3600})
    res, controle = departement.virtuels_des_joueurs(client, ["a", "b", "c", "d"], {"a": 600, "b": 510, "c": 800, "d": 700},
                                                     date(2026, 11, 15))
    # a, b (jamais lus) et c (lu il y a plus de 3 jours) relus ; d (lu il y a une heure) : sa réponse enregistrée
    assert client.ttls == {"a": departement.TTL_VIRTUELS, "b": departement.TTL_VIRTUELS, "c": departement.TTL_VIRTUELS, "d": None}
    assert res["a"][1] > 0 and res["c"][1] < 0
    assert res["b"][:4] == [510, 0, 0, 0] and res["d"][:4] == [700, 0, 0, 0]  # sans partie : virtuels = points mensuels
    assert res["c"][4] == il_y_a(0) and res["d"][4] == il_y_a(1 / 24)  # date de lecture de chacun
    assert (controle["lus"], controle["reportes"], controle["connus"]) == (3, 0, 4)
    # Hors du choix : jamais lu (b) ignoré ; lu il y a 4 jours (c) gardé tel quel, avec sa date
    client = ClientParties({}, {}, dates_parties={"c": maintenant - 4 * 86400, "d": maintenant - 3600})
    res, controle = departement.virtuels_des_joueurs(client, ["a", "b", "c", "d"], {"a": 600, "b": 510, "c": 800, "d": 700},
                                                     date(2026, 11, 15), a_relire={"a", "d"})
    assert client.ttls == {"a": departement.TTL_VIRTUELS, "c": None, "d": None} and set(res) == {"a", "c", "d"}
    assert res["c"][4] == il_y_a(4) and controle["a_relire"] == 2
    # Borne de sécurité : au-delà, jamais lus d'abord ; un déjà lu garde sa réponse ancienne (et sa date)
    monkeypatch.setattr(departement, "MAX_VIRTUELS", 1)
    client = ClientParties({}, {}, dates_parties={"c": maintenant - 4 * 86400, "d": maintenant - 3600})
    res, controle = departement.virtuels_des_joueurs(client, ["a", "b", "c", "d"], {"a": 600, "b": 510, "c": 800, "d": 700}, date(2026, 11, 15))
    assert client.ttls == {"a": departement.TTL_VIRTUELS, "c": None, "d": None} and controle["reportes"] == 1
    assert set(res) == {"a", "c", "d"} and res["c"][4] == il_y_a(4) and controle["plus_ancienne"] == il_y_a(4)


def test_controle_des_parties_en_chiffres_seulement(capsys):
    """Écarts signalés avec la FFTT : le journal mesure doublons, coefficients et parties « non comptées »
    (échantillon lu en détail), sans nom ni numéro de licence."""
    from ttvaires import controle_parties
    tournoi = {"id": 2, "name": "Tournoi de Lagny"}
    p40 = {**_partie(40, "a", 600, 900, True), "contest": tournoi, "effectiveDate": "2026-10-01T00:00:00"}
    p41 = {**_partie(41, "a", 600, 500, False), "contest": tournoi}
    client = ClientParties({}, {"a": [p40, p41, p41, _partie(1, "a", 600, 650, True)], "b": [p40]},
                           dates_parties={"a": time.time(), "b": time.time()})
    client.details = {40: {"notCounted": True, "sportMatch": {"tour": {"division": {"name": "Tableau handicap"}}}}}
    res = controle_parties.controler(client, ["a", "b", "c"], "2026-07-01", "2026-11-15")
    sortie = capsys.readouterr().out
    assert res == {"joueurs": 2, "filtres": None, "doublons": 1, "hors_championnat": 2, "echantillon": 1, "non_comptees": 1}
    assert "Tableau handicap (1)" in sortie and "coefficients, Tournois : 0.5 (2 parties)" in sortie
    assert "NOM" not in sortie and "Prénom" not in sortie  # aucun nom dans le journal
    assert not any("identifier=c" in d for d in client.demandes)  # joueur jamais lu : pas de requête

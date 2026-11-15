"""Page « Clubs du 77 » : clubs du département, leurs équipes et divisions, leurs licenciés (noms fictifs)."""

import json
import time
from datetime import date

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

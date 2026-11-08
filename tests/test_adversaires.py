"""Structure de la page adversaires construite depuis l'API FFTT (objets JSON fictifs de même forme)."""

from datetime import date

from ttvaires import adversaires
from ttvaires.adversaires import classement_poule, completer_avec_pingpocket, equipes_et_compositions
from ttvaires.fftt import bornes_phase, libelle_division, phase_et_saison
from ttvaires.reseau import ErreurReseau


def _equipe(nom, club, position=None):
    return {"name": nom, "position": position, "clubs": [{"identifier": club, "id": 1, "name": f"CLUB {club}"}]}


def _rencontre(id_, dom, ext, journee=1, date_="2026-09-25", feminin=False, **detail):
    contest = "FED_Championnat de France par Equipes " + ("Féminin" if feminin else "Masculin")
    r = {"id": id_, "homeOpponent": {"team": dom}, "awayOpponent": {"team": ext} if ext else None,
         "day": {"position": journee}, "date": date_ + "T00:00:00", "division": {"name": "DEP 2 Ph1", "contest": {"name": contest}}}
    r.update(detail)
    return r


def _licence(lic, nom, prenom, points):
    return {"player": {"identifier": lic, "points": points, "person": {"familyName": nom, "givenName": prenom}}}


def test_saison_phase_et_libelles():
    assert phase_et_saison(date(2026, 10, 3)) == (1, "2026-2027")
    assert phase_et_saison(date(2027, 2, 1)) == (2, "2026-2027")
    assert bornes_phase(date(2026, 10, 3)) == ("2026-07-01", "2026-12-31")
    assert bornes_phase(date(2027, 2, 1)) == ("2027-01-01", "2027-06-30")
    assert libelle_division("DEP 2 Ph1") == "Départementale 2"
    assert libelle_division("L08_R2") == "Régionale 2"
    assert libelle_division("FED_Nationale 2") == "Nationale 2"


def test_classement_poule():
    a, b, c = _equipe("ALPHA 1", "1", 1), _equipe("BETA 2", "2", 2), _equipe("VAIRES CVTT 3", "08770250", 3)
    poule = {"poolOpponents": [{"opponent": {"team": t}} for t in (a, b, c)]}
    rencontres = [_rencontre(1, a, c), _rencontre(2, b, None), _rencontre(3, c, b, journee=2, date_="2026-10-02")]
    detail = {
        1: {"homeOpponent": {"team": a}, "awayOpponent": {"team": c}, "homePoints": 3, "awayPoints": 1,
            "homeGamePoints": 27, "awayGamePoints": 15},
        3: {"homeOpponent": {"team": c}, "awayOpponent": {"team": b}, "homePoints": 2, "awayPoints": 2,
            "homeGamePoints": 21, "awayGamePoints": 21},
    }
    cl = {e["libelle"]: e for e in classement_poule(poule, rencontres, detail)}
    assert (cl["ALPHA 1"]["rang"], cl["ALPHA 1"]["points"], cl["ALPHA 1"]["v"]) == (1, 3, 1)
    assert (cl["VAIRES CVTT 3"]["points"], cl["VAIRES CVTT 3"]["joues"], cl["VAIRES CVTT 3"]["n"], cl["VAIRES CVTT 3"]["d"]) == (3, 2, 1, 1)
    assert (cl["VAIRES CVTT 3"]["pg"], cl["VAIRES CVTT 3"]["pp"]) == (36, 48)
    assert cl["BETA 2"]["rang"] == 3 and cl["VAIRES CVTT 3"]["rang"] == 2


def test_equipes_et_compositions():
    l12, l13 = _equipe("LOGNES EP 12", "08771184"), _equipe("LOGNES EP 13", "08771184")
    x, f1 = _equipe("AUTRE 4", "9"), _equipe("LOGNES EP 1", "08771184")
    rencontres = [
        _rencontre(10, l12, x), _rencontre(11, x, l13), _rencontre(12, l12, x, journee=2, date_="2026-10-02"),
        _rencontre(20, f1, x, date_="2026-09-26", feminin=True),
    ]
    detail = {
        10: {"day": {"position": 1}, "date": "2026-09-25T00:00:00",
             "homeSheetMatches": [{**_licence("1", "DUPONT", "Jean", 900), "identifier": "B"},
                                  {**_licence("2", "MARTIN", "Léa", 800), "identifier": "A"}],
             "awaySheetMatches": [{"identifier": "W"}]},
        11: {"day": {"position": 1}, "date": "2026-09-25T00:00:00", "awaySheetMatches": [_licence("3", "PETIT", "Luc", 700)]},
        20: {"day": {"position": 1}, "date": "2026-09-26T00:00:00", "homeSheetMatches": [_licence("2", "MARTIN", "Léa", 800)]},
    }
    equipes, joueurs = equipes_et_compositions("08771184", rencontres, detail, {"M"})
    assert [(e["libelle"], e["numero"], [{k: c[k] for k in ("journee", "date", "joueurs")} for c in e["compositions"]])
            for e in equipes] == [
        ("LOGNES EP 12", 12, [{"journee": 1, "date": "2026-09-25", "joueurs": ["1", "2"]}]),  # J2 pas encore saisie
        ("LOGNES EP 13", 13, [{"journee": 1, "date": "2026-09-25", "joueurs": ["3"]}]),
    ]
    # Placement choisi par le capitaine : lettres de la feuille, points du jour, adversaire
    c = equipes[0]["compositions"][0]
    assert (c["lettres"], c["points"], c["domicile"], c["contre"], c["format"]) == (
        {"1": "B", "2": "A"}, {"1": 900, "2": 800}, True, "AUTRE 4", 4)
    assert equipes[1]["compositions"][0]["domicile"] is False
    assert joueurs["1"]["classement"] == 9 and joueurs["1"]["sexe"] is None
    # Championnat féminin demandé aussi : l'équipe féminine apparaît et la joueuse est marquée F.
    equipes, joueurs = equipes_et_compositions("08771184", rencontres, detail, {"M", "F"})
    assert [e["libelle"] for e in equipes if e["championnat"] == "F"] == ["LOGNES EP 1"]
    assert joueurs["2"]["sexe"] == "F"


MEAUX = "08770135"


def _ecran(titre, sections):
    lignes = "".join(f'<li class="sep"><p><span>{t}</span></p></li>' + "".join(
        f'<li class="arrow"><a href="/app/fftt/licencies/{lic}?CLUB_ID={MEAUX}"><div class="labels"><p>{nom}</p></div>'
        f'<small class="counter">{c}</small></a></li>' for lic, nom, c in joueurs) for t, joueurs in sections)
    return f'<div data-title="CS MEAUX TT, licenciés {titre}"><ul class="edgetoedge">{lignes}</ul></div>'


CATEGORIES = _ecran("par catégorie d'âge", [("Sénior", [("1", "ALIGNE Paul", "1210"), ("2", "AUTRE Luc", "900")]),
                                              ("Vétéran 60", [("3", "LOISIR Jean", "L")])])
ETAT = _ecran("par licences à jour", [("Licences à jour", [("1", "ALIGNE Paul", ""), ("2", "AUTRE Luc", ""), ("3", "LOISIR Jean", "")])])


class FauxPingpocket:
    sites_cache_seul = set()
    hors_ligne = False

    def __init__(self, en_ligne, pages=None, en_cache=()):
        self.en_ligne, self.pages, self.caches, self.demandes = en_ligne, pages or {}, set(en_cache), []

    def get(self, chemin, ttl=None, **options):
        if not self.en_ligne:
            raise ErreurReseau(chemin)
        return self.pages.get(chemin, "")

    def get_plusieurs(self, chemins, ttl=None, message=None, **options):
        self.demandes.append(list(chemins))
        return {c: self.pages.get(c) for c in chemins}

    def date(self, chemin):
        return None

    def en_cache(self, chemin, ttl):
        return chemin in self.caches

    def disponible(self, site):
        return self.en_ligne


def _donnees():
    aligne = {"id": "1", "licence": "1", "nom": "ALIGNE", "prenom": "Paul", "sexe": None, "points": 1180,
              "points_mensuels": None, "classement": 11, "renouvele": True, "meilleur": None}
    club = {"numero": MEAUX, "nom": "CS MEAUX TT", "salle": None, "joueurs": [aligne],
            "equipes": [{"compositions": [{"joueurs": ["1"]}]}], "effectif_complet": False}
    return {"club": {"numero": "08770250", "salle": None}, "clubs": {MEAUX: club}, "sources": {"pingpocket": False}}


def test_effectif_adverse_par_le_dossier_import(tmp_path):
    (tmp_path / "meaux.html").write_text(f"<html><body>{CATEGORIES}{ETAT}</body></html>", encoding="utf-8")
    donnees, client = _donnees(), FauxPingpocket(en_ligne=False)
    completer_avec_pingpocket(client, donnees, tmp_path)
    club = donnees["clubs"][MEAUX]
    assert club["effectif_complet"] and club["import"] == "meaux.html" and donnees["sources"]["pingpocket"]
    joueurs = {j["id"]: j for j in club["joueurs"]}
    assert set(joueurs) == {"1", "2"}  # licence loisir écartée
    assert joueurs["1"]["points"] == 1180 and joueurs["2"]["points_mensuels"] == 900
    assert client.demandes == []  # site muet : aucun historique demandé


def test_historiques_limites_par_lancement(tmp_path, monkeypatch):
    monkeypatch.setattr(adversaires, "MAX_HISTORIQUES", 1)
    base = f"/app/fftt/clubs/{MEAUX}/licencies?SORT="
    pages = {base + "CATEGORY": _ecran("par catégorie d'âge", [("Sénior", [("1", "ALIGNE Paul", "1210"), ("2", "AUTRE Luc", "900"),
                                                                          ("4", "TROIS Max", "800")])]),
             base + "LICENCE_STATE": _ecran("par licences à jour", [("Licences à jour", [("1", "", ""), ("2", "", ""), ("4", "", "")])])}
    historique = "/app/fftt/licencies/{}/graphiques/historique-classement"
    client = FauxPingpocket(en_ligne=True, pages=pages, en_cache=[historique.format("4")])
    donnees = _donnees()
    completer_avec_pingpocket(client, donnees, tmp_path)
    # Déjà en cache : 4 ; à télécharger : 1 (aligné, prioritaire) et 2 -> un seul par lancement.
    assert sorted(client.demandes[-1]) == sorted([historique.format("1"), historique.format("4")])
    assert donnees["sources"]["historiques_restants"] == 1
    # Option 8 du menu : tous les historiques manquants d'un coup.
    donnees = _donnees()
    completer_avec_pingpocket(client, donnees, tmp_path, tous_les_historiques=True)
    assert sorted(client.demandes[-1]) == sorted(historique.format(n) for n in ("1", "2", "4"))
    assert donnees["sources"]["historiques_restants"] == 0


def test_nouveaux_inscrits_des_clubs_adverses(tmp_path):
    """Un joueur qui apparaît dans la liste des licenciés d'un club adverse (inscription, mutation,
    réinscription) est marqué « nouveau » jusqu'au changement suivant de la liste."""
    base = f"/app/fftt/clubs/{MEAUX}/licencies?SORT="

    def lancement(joueurs, horodatage):
        pages = {base + "CATEGORY": _ecran("par catégorie d'âge", [("Sénior", [(i, f"NOM{i} P", p) for i, p in joueurs])]),
                 base + "LICENCE_STATE": _ecran("par licences à jour", [("Licences à jour", [(i, "", "") for i, _ in joueurs])])}
        client = FauxPingpocket(en_ligne=True, pages=pages, en_cache=[f"/app/fftt/licencies/{i}/graphiques/historique-classement"
                                                                      for i, _ in joueurs + [("1", 0)]])
        client.date = lambda chemin: horodatage
        donnees = _donnees()
        completer_avec_pingpocket(client, donnees, tmp_path / "import", fichier_etat=tmp_path / "cache" / "effectif_adversaires.json")
        club = donnees["clubs"][MEAUX]
        return club, sorted(j["id"] for j in club["joueurs"] if j.get("nouveau"))

    debut = 1_790_000_000  # 2026-09-21
    club, nouveaux = lancement([("1", "1210"), ("2", "900")], debut)
    club_debut_date = club["date_effectif"][:10]
    assert club_debut_date.startswith("2026-09-2") and nouveaux == [] and "reference_nouveaux" not in club
    # Un 1500 s'inscrit : il est nouveau, sur cette liste et tant qu'elle ne change pas
    club, nouveaux = lancement([("1", "1210"), ("2", "900"), ("7", "1500")], debut + 15 * 86400)
    assert nouveaux == ["7"] and club["reference_nouveaux"][:10] == club_debut_date
    club, nouveaux = lancement([("1", "1210"), ("2", "900"), ("7", "1500")], debut + 15 * 86400)
    assert nouveaux == ["7"]
    # Liste suivante sans changement d'inscrits après une autre arrivée : seul le dernier arrivé est nouveau
    club, nouveaux = lancement([("1", "1210"), ("2", "900"), ("7", "1500"), ("8", "500")], debut + 30 * 86400)
    assert nouveaux == ["8"]

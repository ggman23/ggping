"""Page « Effectif de Vaires » : de bout en bout avec un faux site (API FFTT + pingpocket)."""

import json
import os
import time
from datetime import date

from ttvaires import fftt
from ttvaires.brulage import brulage_par_equipe
from ttvaires.effectif import recuperer_effectif
from ttvaires.reseau import ErreurReseau

VAIRES = "08770250"


def _equipe(nom, club=VAIRES):
    return {"name": nom, "clubs": [{"identifier": club, "id": 7, "name": "CVTT VAIRES" if club == VAIRES else "AUTRE"}]}


def _rencontre(id_, vaires, autre, journee, date_, feminin=False):
    contest = "FED_Championnat de France par Equipes " + ("Féminin" if feminin else "Masculin")
    return {"id": id_, "homeOpponent": {"team": vaires}, "awayOpponent": {"team": autre}, "day": {"position": journee},
            "date": date_ + "T00:00:00", "time": "1970-01-01T20:45:00", "pool": {"id": 1},
            "division": {"name": "DEP 2 Ph1", "contest": {"name": contest}}}


def _feuille(rencontre, joueurs):
    d = dict(rencontre)
    d.update({"homeGamePoints": 21, "awayGamePoints": 21,
              "homeSheetMatches": [{"player": {"identifier": lic, "points": pts, "person": {"familyName": nom, "givenName": prenom}}}
                                   for lic, nom, prenom, pts in joueurs]})
    return d


def _liste(sections, titre_ecran="Club", club="1"):
    lignes = []
    for titre, joueurs in sections:
        lignes.append(f'<li class="sep"><p><span>{titre}</span></p>')
        for lic, nom, compteur, sexe in joueurs:
            lignes.append(f'<li class="arrow"><a href="/app/fftt/licencies/{lic}?CLUB_ID={club}"><div class="icon">'
                          f'<i class="fa fa-{"female" if sexe == "F" else "male"}"></i></div><div class="labels"><p>{nom}</p></div>'
                          f'<small class="counter">{compteur}</small></a></li>')
        lignes.append("</li>")
    return f'<div data-title="{titre_ecran}"><ul class="edgetoedge">' + "".join(lignes) + "</ul></div>"


class FauxClient:
    """Répond comme le site : listes et détails de l'API FFTT, listes de licenciés pingpocket."""

    def __init__(self, pages, perimes=None):
        self.pages, self.perimes = pages, perimes or {}

    def date(self, chemin):
        return self.perimes.get(chemin, time.time())

    def get(self, chemin, ttl=None, entetes=None, valide=None, perime_si_erreur=False):
        for prefixe, contenu in self.pages.items():
            if chemin.startswith(prefixe):
                return contenu
        raise ErreurReseau(chemin)

    def get_plusieurs(self, chemins, ttl=None, message=None, **options):
        res = {}
        for c in chemins:
            try:
                res[c] = self.get(c)
            except ErreurReseau:
                res[c] = None
        return res

    def oublier(self, chemin):
        pass


def test_brulage_par_equipe():
    parts = [{"numero": 4}, {"numero": 4}]
    b = brulage_par_equipe(parts, [1, 2, 3, 4, 5, 6])
    assert [n for n in b if b[n]["brule"]] == [5, 6]
    assert b[5]["plus_fortes"] == [4, 4]


CATEGORIES = [("Sénior", [("100", "MARTIN Léa", "800", "F"), ("200", "DURAND Paul", "900", "M"), ("300", "NOUVEAU Tom", "700", "M")]),
              ("Vétéran 50", [("400", "LOISIR Jean", "L", "M"), ("500", "ANCIEN Marc", "650", "M")])]
CLASSEMENTS = [("8", [("100", "MARTIN Léa", "800", "F")])]
ETAT = [("Licences à jour", [(x, "X", "", "M") for x in ("100", "200", "300", "400")]),
        ("Licences non renouvelées", [("500", "ANCIEN Marc", "", "M")])]
LISTES = {"CATEGORY": CATEGORIES, "OFFICIAL_RANK": CLASSEMENTS, "LICENCE_STATE": ETAT}


def _site(avec_listes=True):
    """Pages du faux site : rencontres et feuilles de Vaires, listes de licenciés si `avec_listes`."""
    v4, v1f, adv = _equipe("VAIRES CVTT 4"), _equipe("CVTT VAIRES 1"), _equipe("AUTRE 2", "08779999")
    rencontres = [
        _rencontre(1, v4, adv, 1, "2026-09-25"), _rencontre(2, v4, adv, 2, "2026-10-02"),
        _rencontre(3, v1f, adv, 2, "2026-10-03", feminin=True), _rencontre(4, v4, adv, 3, "2026-10-16"),
    ]
    lea, paul = ("100", "MARTIN", "Léa", 800), ("200", "DURAND", "Paul", 900)
    feuilles = {1: _feuille(rencontres[0], [lea, paul]), 2: _feuille(rencontres[1], [lea]), 3: _feuille(rencontres[2], [lea])}
    pages = {f"{fftt.API}/sport_matches/{i}": json.dumps(f) for i, f in feuilles.items()}
    pages[f"{fftt.API}/sport_matches?"] = json.dumps({"@context": "/api/contexts/SportMatch", "hydra:member": rencontres})
    if avec_listes:
        for tri, sections in LISTES.items():
            pages[f"/app/fftt/clubs/08770250/licencies?SORT={tri}"] = _liste(sections)
    return pages


def _page_enregistree(chemin, ecrans, date_=None):
    """Page pingpocket enregistrée depuis un navigateur : l'application et les écrans consultés."""
    chemin.write_text('<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><div id="jqt">'
                      '<div data-title="Accueil"><ul class="edgetoedge"><li>Clubs</li></ul></div>'
                      + "".join(ecrans) + "</div></body></html>", encoding="utf-8")
    if date_:
        os.utime(chemin, (date_, date_))


def _ecrans_vaires(*tris):
    titres = {"CATEGORY": "par catégorie d'âge", "OFFICIAL_RANK": "par classement officiel", "LICENCE_STATE": "par licences à jour"}
    return [_liste(LISTES[t], f"CVTT VAIRES, licenciés {titres[t]}", VAIRES) for t in tris]


def test_effectif_complet(tmp_path):
    pages = _site()
    etat = tmp_path / "etat.json"
    etat.write_text(json.dumps({"date": "2026-10-01T10:00", "renouveles": ["100", "200"]}))
    d = recuperer_effectif(FauxClient(pages), VAIRES, aujourdhui=date(2026, 10, 6), fichier_etat=etat)
    j = {x["id"]: x for x in d["joueurs"]}

    assert [e["nom_court"] for e in d["equipes"]] == ["Vaires 4", "Vaires 1 F"]
    assert d["prochaines"]["M"]["journee"] == 3 and d["source"]["liste"]
    # Léa : 2 matchs en V4 (masculin) + 1 en V1 F. Le match féminin ne compte pas pour le masculin.
    assert j["100"]["sexe"] == "F" and j["100"]["equipe_max"] == 4
    assert [m["ch"] for m in j["100"]["matchs"]] == ["M", "M", "F"]
    assert not j["100"]["brulage"][4]["brule"]
    # Paul : un seul match en V4, libre partout.
    assert j["200"]["equipe_max"] is None and j["200"]["habituelle"] == 4
    # Licence loisir, non renouvelé, nouveau réinscrit depuis la dernière mise à jour.
    assert j["400"]["loisir"] and not j["500"]["renouvele"]
    assert j["300"]["nouveau"] and not j["100"]["nouveau"]
    assert json.loads(etat.read_text())["renouveles"] == ["100", "200", "300"]


def test_brulee_pour_les_equipes_plus_faibles():
    # Exemple donné par le club : 2 matchs avec l'équipe 4 -> brûlée pour 5 et 6, disponible de 1 à 4.
    b = brulage_par_equipe([{"numero": 4}, {"numero": 4}], [1, 2, 3, 4, 5, 6])
    assert {n: v["brule"] for n, v in b.items()} == {1: False, 2: False, 3: False, 4: False, 5: True, 6: True}


def test_liste_importee_si_pingpocket_bloque(tmp_path):
    """Site bloqué : la liste vient des pages enregistrées dans le dossier import (un ou plusieurs fichiers)."""
    dossier = tmp_path / "import"
    dossier.mkdir()
    _page_enregistree(dossier / "categories.html", _ecrans_vaires("CATEGORY"))
    _page_enregistree(dossier / "etat et classements.html", _ecrans_vaires("LICENCE_STATE", "OFFICIAL_RANK"))
    (dossier / "autre chose.html").write_text("<html><body>rien</body></html>", encoding="utf-8")
    etat = tmp_path / "etat.json"
    etat.write_text(json.dumps({"date": "2026-10-01T10:00", "renouveles": ["100", "200"]}))

    d = recuperer_effectif(FauxClient(_site(avec_listes=False)), VAIRES, aujourdhui=date(2026, 10, 6),
                           fichier_etat=etat, dossier_import=dossier)
    j = {x["id"]: x for x in d["joueurs"]}
    src = d["source"]
    assert src["liste"] and src["origine"] == "import" and not src["a_jour"] and src["manquantes"] == []
    assert src["fichiers"] == ["categories.html", "etat et classements.html"]
    assert set(j) == {"100", "200", "300", "400", "500"}
    assert j["400"]["loisir"] and not j["500"]["renouvele"] and j["100"]["classement"] == 8
    assert j["300"]["nouveau"] and json.loads(etat.read_text())["renouveles"] == ["100", "200", "300"]
    assert "SORT%3DLICENCE_STATE" in src["liens"]["etat"]


def test_sans_liste_ni_import(tmp_path):
    d = recuperer_effectif(FauxClient(_site(avec_listes=False)), VAIRES, aujourdhui=date(2026, 10, 6),
                           dossier_import=tmp_path / "absent")
    assert not d["source"]["liste"] and d["source"]["origine"] is None
    assert {x["id"] for x in d["joueurs"]} == {"100", "200"}  # joueurs déjà alignés seulement


def test_la_liste_la_plus_recente_l_emporte(tmp_path):
    """Copie ancienne du cache (site muet) contre page enregistrée : la plus récente est retenue."""
    dossier = tmp_path / "import"
    dossier.mkdir()
    il_y_a_2_jours, il_y_a_5_jours = time.time() - 2 * 86400, time.time() - 5 * 86400
    _page_enregistree(dossier / "vaires.html", _ecrans_vaires("CATEGORY", "LICENCE_STATE", "OFFICIAL_RANK"), il_y_a_2_jours)
    for age, attendu in ((il_y_a_5_jours, "import"), (time.time() - 3600, "cache")):
        pages = _site()
        perimes = {u: age for u in pages if "/licencies?" in u}
        d = recuperer_effectif(FauxClient(pages, perimes), VAIRES, aujourdhui=date(2026, 10, 6), dossier_import=dossier)
        assert d["source"]["origine"] == attendu

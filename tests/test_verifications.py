"""Vérifications : chaque équipe a-t-elle son résultat pour chaque journée jouée ?"""

import json

from ttvaires import fftt
from ttvaires.verifications import bilan_club, bilan_rencontres, etat_detail, statut

LOGNES, AUTRE = "08771184", "08770999"
AUJ = "2026-10-18"


def _equipe(nom, club):
    return {"team": {"name": nom, "clubs": [{"identifier": club, "id": 1, "name": f"CLUB {club}"}]}}


def _rencontre(id_, dom, ext, journee, date_, feminin=False):
    return {"id": id_, "homeOpponent": _equipe(*dom) if dom else None, "awayOpponent": _equipe(*ext) if ext else None,
            "day": {"position": journee}, "date": date_ + "T00:00:00",
            "division": {"name": "DEP 1 Ph1", "contest": {"name": "FED_Championnat de France par Equipes "
                                                                  + ("Féminin" if feminin else "Masculin")}}}


def test_etat_d_une_rencontre():
    feuille = {"homeGamePoints": 22, "homeSheetMatches": [{}], "awaySheetMatches": [{}]}
    assert etat_detail(None) == "non_recupere"
    assert etat_detail({"homeGamePoints": None}) == "non_saisi"
    assert etat_detail({"homeGamePoints": 0, "forfeit": "home"}) == "forfait"
    assert etat_detail({"homeGamePoints": 22, "homeSheetMatches": [], "awaySheetMatches": []}) == "sans_feuille"
    assert etat_detail(feuille) == "complet"


def test_statut_selon_la_date():
    exempte = _rencontre(1, ("LOGNES 1", LOGNES), None, 1, "2026-09-25")
    a_venir = _rencontre(2, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 4, "2026-11-06")
    ce_soir = _rencontre(3, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, AUJ)
    assert statut(exempte, {}, AUJ) == "exempt"
    assert statut(a_venir, {}, AUJ) == "a_venir"
    assert statut(ce_soir, {3: "non_saisi"}, AUJ) == "du_jour"
    assert statut(ce_soir, {3: "complet"}, AUJ) == "complet"
    assert statut(_rencontre(4, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, "2026-10-16"), {}, AUJ) == "non_recupere"


def test_bilan_d_un_club_equipe_par_equipe():
    rencontres = [
        _rencontre(1, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, "2026-10-16"),     # complète
        _rencontre(2, ("AUTRE 2", AUTRE), ("LOGNES 2", LOGNES), 3, "2026-10-16"),     # résultat pas saisi
        _rencontre(3, ("LOGNES 3", LOGNES), ("LOGNES 4", LOGNES), 3, "2026-10-16"),   # entre deux équipes du club
        _rencontre(4, ("LOGNES 5", LOGNES), None, 3, "2026-10-16"),                   # exempte
        _rencontre(5, ("LOGNES 1", LOGNES), ("AUTRE 3", AUTRE), 3, "2026-10-17", feminin=True),  # même nom, en féminin
        _rencontre(6, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 4, "2026-11-06"),     # à venir
        _rencontre(1, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, "2026-10-16"),     # doublon (poule + club)
    ]
    etats = {1: "complet", 2: "non_saisi", 3: "complet", 5: "sans_feuille"}
    b = bilan_club(rencontres, etats, AUJ, LOGNES, "E. P. DE LOGNES")
    assert b["equipes"] == 6  # LOGNES 1 à 5 en masculin + LOGNES 1 en féminin
    [j3] = b["journees"]  # la J4 n'est pas encore jouée
    assert (j3["journee"], j3["attendues"], j3["completes"], j3["exemptes"]) == (3, 5, 3, 1)
    assert j3["dates"] == ["2026-10-16", "2026-10-17"]
    assert [(m["equipe"], m["etat"]) for m in j3["manquantes"]] == [("LOGNES 2", "non_saisi"), ("LOGNES 1", "sans_feuille")]
    assert b["manquantes"] == 2 and not b["complet"]

    [g3] = bilan_rencontres(rencontres, etats, AUJ)  # chaque rencontre comptée une fois
    assert (g3["attendues"], g3["completes"]) == (4, 2)


def test_details_note_l_etat_de_chaque_rencontre():
    class Faux:
        def __init__(self):
            self.oubliees = []

        def get_plusieurs(self, chemins, **options):
            pages = {f"{fftt.API}/sport_matches/1": {"@context": "x", "homeGamePoints": 20, "homeSheetMatches": [{}]},
                     f"{fftt.API}/sport_matches/2": {"@context": "x", "homeGamePoints": None}}
            return {c: json.dumps(pages[c]) if c in pages else None for c in chemins}

        def oublier(self, chemin):
            self.oubliees.append(chemin)

    rencontres = [_rencontre(i, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, "2026-10-16") for i in (1, 2, 3)]
    client, etats = Faux(), {}
    detail = fftt.details(client, rencontres, AUJ, etats)
    assert list(detail) == [1]
    assert etats == {1: "complet", 2: "non_saisi", 3: "non_recupere"}
    assert len(client.oubliees) == 2  # retentées au prochain lancement


def test_feuilles_recentes_relues_pour_les_corrections():
    """Une feuille saisie peut être corrigée ensuite : relue tant que la rencontre est récente."""
    class Faux:
        appels = []

        def get_plusieurs(self, chemins, ttl=None, **options):
            self.appels.append((sorted(c.rsplit("/", 1)[1] for c in chemins), ttl, options.get("perime_si_erreur", False)))
            return {c: json.dumps({"@context": "x", "homeGamePoints": 20, "homeSheetMatches": [{}]}) for c in chemins}

        def oublier(self, chemin):
            pass

    ancienne = _rencontre(1, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 1, "2026-09-25")
    recente = _rencontre(2, ("LOGNES 1", LOGNES), ("AUTRE 1", AUTRE), 3, "2026-10-16")
    client = Faux()
    assert list(fftt.details(client, [ancienne, recente], AUJ)) == [1, 2]
    assert client.appels == [(["1"], None, False),                       # ancienne : gardée en cache
                             (["2"], fftt.RELECTURE_TTL, True)]          # récente : relue (copie gardée si panne)

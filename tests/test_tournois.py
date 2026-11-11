"""Tournois : vérification de ce que l'API de la FFTT en donne (réponses de même forme que l'API)."""

import json

from ttvaires import tournois
from ttvaires.fftt import API
from ttvaires.reseau import ErreurReseau


class Client:
    def __init__(self, pages):
        self.pages, self.demandes = pages, []

    def get(self, chemin, ttl=None, entetes=None, valide=None, perime_si_erreur=False):
        self.demandes.append(chemin)
        if chemin not in self.pages:
            raise ErreurReseau(chemin)
        return json.dumps(self.pages[chemin])


def test_verification_des_tournois(capsys):
    pages = {
        API: {"@id": "/api", "contest": "/api/contests", "tournament": "/api/tournaments"},
        API + "/docs.json": {"paths": {
            "/api/tournaments": {"get": {"tags": ["Tournament"], "parameters": [
                {"name": "startDate[after]", "in": "query"}, {"name": "department", "in": "query"}]}},
            "/api/tournaments/{id}": {"get": {"tags": ["Tournament"], "parameters": [{"name": "id", "in": "path"}]}},
            "/api/contests": {"get": {"tags": ["Contest"], "parameters": []}}}},
        f"{API}/tournaments?itemsPerPage=2": {"hydra:totalItems": 412, "hydra:member": [
            {"@id": "/api/tournaments/1", "name": "Tournoi de Chelles", "startDate": "2026-12-05", "postalCode": "77500"}]},
    }
    client = Client(pages)
    tournois.verification(client)
    sortie = capsys.readouterr().out
    assert "Collections « tournois » : tournament -> /api/tournaments" in sortie
    assert "/api/tournaments : filtres startDate[after], department" in sortie
    assert "/api/tournaments : 412 élément(s)" in sortie and "Tournoi de Chelles" in sortie
    assert client.demandes.count(f"{API}/tournaments?itemsPerPage=2") == 1  # une seule lecture d'échantillon
    assert len(client.demandes) <= 2 + tournois.MAX_ESSAIS


def test_rien_sur_les_tournois(capsys):
    tournois.verification(Client({API: {"@id": "/api"}}))
    sortie = capsys.readouterr().out
    assert "Collections « tournois » : aucune" in sortie and "documentation /docs.json illisible" in sortie


def test_documentation_json_ld(capsys):
    pages = {
        API: {"@id": "/api"},
        API + "/docs.jsonld": {"hydra:supportedClass": [
            {"@id": "#Contest", "hydra:title": "Contest", "hydra:supportedProperty": [{"hydra:title": "name"}]},
            {"@id": "#TournamentRequest", "hydra:title": "TournamentRequest",
             "hydra:supportedProperty": [{"hydra:title": "name"}, {"hydra:title": "startDate"}, {"hydra:title": "address"}]},
            {"@id": "#Entrypoint", "hydra:title": "Entrypoint", "hydra:supportedProperty": [
                {"hydra:property": {"@id": "#Entrypoint/tournamentRequest"}}, {"hydra:property": {"@id": "#Entrypoint/contest"}}]}]},
        f"{API}/tournamentRequests?itemsPerPage=2": {"hydra:totalItems": 3, "hydra:member": [{"name": "Tournoi de Lagny"}]},
    }
    tournois.verification(Client(pages))
    sortie = capsys.readouterr().out
    assert "Classe « TournamentRequest » : name, startDate, address" in sortie
    assert "#Entrypoint/tournamentRequest" in sortie and "/api/tournamentRequests : 3 élément(s)" in sortie

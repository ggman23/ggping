"""Connexion à l'API de la FFTT avec un compte licencié (comme malicence.fftt.com)."""

import base64
import json
import time

import pytest

from ttvaires import compte_fftt
from ttvaires.reseau import Client, ErreurReseau


def _jeton(dans_secondes):
    charge = base64.urlsafe_b64encode(json.dumps({"exp": int(time.time()) + dans_secondes}).encode()).decode().rstrip("=")
    return f"entete.{charge}.signature"


class Reponse:
    def __init__(self, code, donnees=None, entetes=None):
        self.status_code, self._donnees = code, donnees or {}
        self.text, self.headers = json.dumps(self._donnees), entetes or {}

    def json(self):
        return self._donnees


class FFTT:
    """Faux serveur : connexion, renouvellement et API (qui exige le bon jeton)."""

    def __init__(self, identifiant="ggman23", mot_de_passe="secret", mfa=False):
        self.attendu, self.mfa = (identifiant, mot_de_passe), mfa
        self.connexions, self.renouvellements, self.appels, self.valide = 0, 0, [], set()

    def post(self, url, json=None, **options):
        if url.endswith("/login_check"):
            self.connexions += 1
            assert json["scope"] == "licence"
            if (json["username"], json["password"]) != self.attendu:
                return Reponse(401, {"code": 401, "message": "Identifiants invalides."}, {"www-authenticate": "Bearer"})
            if self.mfa:
                return Reponse(200, {"mfa_required": True, "hash": "h"})
            jeton = _jeton(3600) + str(self.connexions)
            self.valide = {jeton}
            return Reponse(200, {"token": jeton, "refresh_token": "r"})
        self.renouvellements += 1
        jeton = _jeton(3600) + "r"
        self.valide = {jeton}
        return Reponse(200, {"token": jeton, "refresh_token": "r2"})

    def get(self, url, headers=None, **options):
        self.appels.append(headers.get("Authorization"))
        if (headers.get("Authorization") or "")[7:] in self.valide:
            return Reponse(200, {"hydra:member": []})
        return Reponse(401, {"code": 401, "message": "JWT Token not found"}, {"www-authenticate": "Bearer"})


@pytest.fixture
def serveur(monkeypatch, tmp_path):
    for nom in ("FFTT_IDENTIFIANT", "FFTT_MOT_DE_PASSE"):
        monkeypatch.delenv(nom, raising=False)
    monkeypatch.setattr(compte_fftt, "CONFIG", tmp_path / "publication.local.json")
    faux = FFTT()
    monkeypatch.setattr(compte_fftt.requests, "post", faux.post)
    return faux


def _client(tmp_path, faux):
    client = Client(tmp_path / "cache", pause=0, tentatives=3)
    client._session = lambda: type("S", (), {"get": lambda self, url, **o: faux.get(url, **o)})()
    return client


def test_connexion_puis_jeton_dans_chaque_requete(serveur, tmp_path, monkeypatch):
    monkeypatch.setenv("FFTT_IDENTIFIANT", "ggman23")
    monkeypatch.setenv("FFTT_MOT_DE_PASSE", "secret")
    client = _client(tmp_path, serveur)
    compte_fftt.connecter(client, demander=False)
    for i in range(3):
        client.get(f"https://apiv2.fftt.com/api/sport_matches?p={i}", ttl=0, valide=lambda t: True)
    assert serveur.connexions == 1 and len(serveur.appels) == 3                  # une seule connexion
    assert all(a.startswith("Bearer entete.") for a in serveur.appels)
    # Jeton presque expiré : renouvelé (sans redemander le mot de passe)
    compte = client.connexions["apiv2.fftt.com"]
    compte._expire = time.time() + 10
    client.get("https://apiv2.fftt.com/api/teams", ttl=0, valide=lambda t: True)
    assert serveur.renouvellements == 1 and serveur.connexions == 1
    # Jeton refusé par l'API (révoqué) : une nouvelle connexion, puis la requête repart
    serveur.valide = set()
    client.get("https://apiv2.fftt.com/api/pools", ttl=0, valide=lambda t: True)
    assert serveur.connexions == 2


def test_mot_de_passe_refuse_un_seul_essai(serveur, tmp_path, monkeypatch):
    monkeypatch.setenv("FFTT_IDENTIFIANT", "ggman23")
    monkeypatch.setenv("FFTT_MOT_DE_PASSE", "faux")
    client = _client(tmp_path, serveur)
    compte_fftt.connecter(client, demander=False)
    with pytest.raises(ErreurReseau, match="connexion à la FFTT refusée pour le compte « ggman23 »"):
        client.get("https://apiv2.fftt.com/api/sport_matches", ttl=0, valide=lambda t: True)
    with pytest.raises(ErreurReseau):
        client.get("https://apiv2.fftt.com/api/teams", ttl=0, valide=lambda t: True)
    assert serveur.connexions == 1 and serveur.appels == []                       # pas de rafale d'essais


def test_code_de_verification_demande(serveur, tmp_path, monkeypatch):
    serveur.mfa = True
    monkeypatch.setenv("FFTT_IDENTIFIANT", "ggman23")
    monkeypatch.setenv("FFTT_MOT_DE_PASSE", "secret")
    client = _client(tmp_path, serveur)
    compte_fftt.connecter(client, demander=False)
    with pytest.raises(ErreurReseau, match="code de vérification"):
        client.get("https://apiv2.fftt.com/api/sport_matches", ttl=0, valide=lambda t: True)


def test_sans_compte_message_clair(serveur, tmp_path):
    client = _client(tmp_path, serveur)
    assert compte_fftt.connecter(client, demander=False) is None
    with pytest.raises(ErreurReseau, match="demande une connexion : régler le compte licencié FFTT"):
        client.get("https://apiv2.fftt.com/api/sport_matches", ttl=0, valide=lambda t: True)
    assert len(serveur.appels) == 1


def test_identifiants_du_pc_gardes_avec_les_autres_reglages(serveur, monkeypatch):
    compte_fftt.CONFIG.write_text(json.dumps({"jeton": "github_pat_x", "mot_de_passe": "site"}), encoding="utf-8")
    reponses = iter(["ggman23"])
    monkeypatch.setattr("builtins.input", lambda invite: next(reponses))
    monkeypatch.setattr(compte_fftt.getpass, "getpass", lambda invite: "secret")
    assert compte_fftt.identifiants(demander=True) == ("ggman23", "secret")
    config = json.loads(compte_fftt.CONFIG.read_text(encoding="utf-8"))
    assert config == {"jeton": "github_pat_x", "mot_de_passe": "site", "fftt_identifiant": "ggman23",
                      "fftt_mot_de_passe": "secret"}
    assert compte_fftt.identifiants(demander=False) == ("ggman23", "secret")    # plus redemandés
    monkeypatch.setenv("FFTT_IDENTIFIANT", "autre")
    monkeypatch.setenv("FFTT_MOT_DE_PASSE", "x")
    assert compte_fftt.identifiants(demander=False) == ("autre", "x")           # en ligne : les secrets

"""Connexion à l'API de la FFTT avec un compte licencié, comme l'espace licencié malicence.fftt.com.

Depuis le 31/10/2026, l'API (apiv2.fftt.com) ne répond plus sans connexion. L'espace licencié se
connecte avec l'identifiant et le mot de passe du licencié (POST /api/login_check, portée
« licence »), reçoit un jeton d'accès de courte durée et un jeton de renouvellement, puis envoie le
jeton dans chaque requête (Authorization: Bearer). L'outil fait de même, avec le compte du
responsable de l'outil :
- en ligne (GitHub) : secrets FFTT_IDENTIFIANT et FFTT_MOT_DE_PASSE ;
- sur le PC : demandés une fois par lancer.bat, gardés dans publication.local.json (jamais envoyé).

Une connexion refusée n'est jamais retentée dans le même lancement (pas de rafale d'essais qui
bloquerait le compte). Si la FFTT demande un code de vérification (double authentification),
l'outil ne peut pas répondre : il le dit.
"""

import base64
import getpass
import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

from .reseau import ENTETES, ErreurReseau

API = "https://apiv2.fftt.com/api"
SITE = "apiv2.fftt.com"
PORTEE = "licence"  # celle de l'espace licencié
MARGE = 60  # secondes : le jeton est renouvelé un peu avant d'expirer
CONFIG = Path(__file__).resolve().parent.parent / "publication.local.json"


def _expiration(jeton):
    """Date d'expiration (horodatage) lue dans le jeton JWT ; dans 10 minutes si illisible."""
    try:
        partie = jeton.split(".")[1]
        return float(json.loads(base64.urlsafe_b64decode(partie + "=" * (-len(partie) % 4)))["exp"])
    except (IndexError, ValueError, KeyError, TypeError):
        return time.time() + 600


class CompteFFTT:
    """Jeton d'accès à l'API de la FFTT pour un compte licencié, partagé entre les requêtes parallèles."""

    def __init__(self, identifiant, mot_de_passe):
        self.identifiant, self._mot_de_passe = identifiant, mot_de_passe
        self._jeton, self._renouvellement, self._expire = None, None, 0.0
        self._echec = None  # message de la connexion refusée : plus aucun essai ensuite
        self._verrou = threading.Lock()

    def entetes(self):
        """En-tête d'autorisation, avec un jeton valable (connexion ou renouvellement si besoin)."""
        with self._verrou:
            if not self._jeton or time.time() > self._expire - MARGE:
                self._obtenir(renouveler=True)
            return {"Authorization": f"Bearer {self._jeton}"}

    def reconnecter(self):
        """Après un refus de l'API avec un jeton : nouvelle connexion complète."""
        with self._verrou:
            self._jeton = None
            self._obtenir(renouveler=False)

    def _poster(self, chemin, donnees):
        try:
            return requests.post(f"{API}/{chemin}", json=donnees, timeout=60,
                                 headers={"User-Agent": ENTETES["User-Agent"], "Accept": "application/json"})
        except requests.RequestException as e:
            raise ErreurReseau(f"connexion à la FFTT impossible ({e})") from e

    def _obtenir(self, renouveler):
        if self._echec:
            raise ErreurReseau(self._echec)
        if renouveler and self._renouvellement:
            r = self._poster("token/refresh", {"refresh_token": self._renouvellement})
            if r.status_code == 200 and r.json().get("token"):
                self._garder(r.json())
                return
        r = self._poster("login_check", {"username": self.identifiant, "password": self._mot_de_passe, "scope": PORTEE})
        if r.status_code in (400, 401, 403):
            self._echec = ("connexion à la FFTT refusée pour le compte « %s » (identifiant ou mot de passe : secrets "
                           "FFTT_IDENTIFIANT et FFTT_MOT_DE_PASSE, ou réglage du PC)" % self.identifiant)
            raise ErreurReseau(self._echec)
        if r.status_code != 200:
            raise ErreurReseau(f"connexion à la FFTT : HTTP {r.status_code}")
        reponse = r.json()
        if reponse.get("mfa_required"):
            self._echec = ("la FFTT demande un code de vérification à la connexion (double authentification) : "
                           "l'outil ne peut pas le saisir")
            raise ErreurReseau(self._echec)
        self._garder(reponse)

    def _garder(self, reponse):
        if not reponse.get("token"):
            raise ErreurReseau("connexion à la FFTT : réponse inattendue (pas de jeton)")
        self._jeton, self._expire = reponse["token"], _expiration(reponse["token"])
        self._renouvellement = reponse.get("refresh_token") or self._renouvellement


def _config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8")) if CONFIG.exists() else {}
    except ValueError:
        return {}


def identifiants(demander=None):
    """(identifiant, mot de passe) du compte licencié : variables d'environnement (GitHub), sinon le
    réglage du PC, sinon demandés (console du PC) et gardés dans publication.local.json."""
    identifiant, mot_de_passe = os.environ.get("FFTT_IDENTIFIANT", ""), os.environ.get("FFTT_MOT_DE_PASSE", "")
    if identifiant and mot_de_passe:
        return identifiant, mot_de_passe
    config = _config()
    if config.get("fftt_identifiant") and config.get("fftt_mot_de_passe"):
        return config["fftt_identifiant"], config["fftt_mot_de_passe"]
    if demander is None:
        demander = sys.stdin is not None and sys.stdin.isatty()
    if not demander:
        return None
    print("\nDepuis le 31/10/2026, l'API de la FFTT demande une connexion. L'outil se connecte comme l'espace")
    print("licencié (https://malicence.fftt.com), avec ton compte : identifiant et mot de passe de cet espace.")
    print(f"Ils restent sur ce PC ({CONFIG.name}, jamais envoyé). Entrée sans rien : continuer sans connexion.")
    identifiant = input("Identifiant FFTT : ").strip()
    mot_de_passe = getpass.getpass("Mot de passe FFTT (invisible à la saisie) : ") if identifiant else ""
    if not (identifiant and mot_de_passe):
        return None
    CONFIG.write_text(json.dumps({**config, "fftt_identifiant": identifiant, "fftt_mot_de_passe": mot_de_passe},
                                 indent=1), encoding="utf-8")
    return identifiant, mot_de_passe


def connecter(client, demander=None):
    """Branche le compte licencié sur le client HTTP (requêtes vers apiv2.fftt.com). Rien en mode hors ligne."""
    if client.hors_ligne:
        return None
    ids = identifiants(demander)
    if not ids:
        print("  ! pas de compte FFTT réglé : l'API de la FFTT refusera les demandes")
        return None
    compte = CompteFFTT(*ids)
    client.connexions[SITE] = compte
    return compte

"""Accès à pingpocket.fr : cache disque, requêtes en parallèle limitées, nouvelles tentatives."""

import hashlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE = "https://www.pingpocket.fr"
HEURE = 3600
JOUR = 24 * HEURE

# Pingpocket ne renvoie le contenu d'une page (fragment HTML) qu'aux requêtes AJAX.
ENTETES = {
    "User-Agent": "Mozilla/5.0 (outil adversaires CVTT Vaires)",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE + "/",
}


class ErreurReseau(Exception):
    pass


class Client:
    """Client HTTP avec cache sur disque.

    ttl : durée de validité du cache en secondes (None = page conservée indéfiniment).
    """

    def __init__(self, dossier_cache, paralleles=2, hors_ligne=False, tentatives=5, pause=0.3):
        self.dossier = Path(dossier_cache)
        self.dossier.mkdir(parents=True, exist_ok=True)
        self.paralleles = paralleles
        self.hors_ligne = hors_ligne
        self.tentatives = tentatives
        self.pause = pause
        self._local = threading.local()
        self._verrou = threading.Lock()
        self.nb_telecharges = 0
        self.nb_cache = 0

    def _session(self):
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
            self._local.session.headers.update(ENTETES)
        return self._local.session

    def _fichier(self, chemin):
        return self.dossier / (hashlib.sha1(chemin.encode("utf-8")).hexdigest() + ".html")

    def oublier(self, chemin):
        """Supprime une page du cache (ex. feuille de match pas encore saisie)."""
        self._fichier(chemin).unlink(missing_ok=True)

    def get(self, chemin, ttl=JOUR):
        fichier = self._fichier(chemin)
        if fichier.exists() and (self.hors_ligne or ttl is None or time.time() - fichier.stat().st_mtime < ttl):
            with self._verrou:
                self.nb_cache += 1
            return fichier.read_text(encoding="utf-8")
        if self.hors_ligne:
            raise ErreurReseau(f"page absente du cache (mode hors ligne) : {chemin}")

        url = chemin if chemin.startswith("http") else BASE + chemin
        derniere_erreur = None
        for essai in range(self.tentatives):
            if essai:
                time.sleep(2 ** essai)
            try:
                r = self._session().get(url, timeout=45)
            except requests.RequestException as e:
                derniere_erreur = e
                continue
            if r.status_code == 200 and "data-title" in r.text[:3000]:
                fichier.write_text(r.text, encoding="utf-8")
                with self._verrou:
                    self.nb_telecharges += 1
                time.sleep(self.pause)  # le site sature vite : on reste discret
                return r.text
            derniere_erreur = f"HTTP {r.status_code}"
            if r.status_code == 404:
                break
        raise ErreurReseau(f"{url} : {derniere_erreur}")

    def get_plusieurs(self, chemins, ttl=JOUR, message=None):
        """Télécharge plusieurs pages en parallèle. Renvoie {chemin: html ou None si échec}."""
        chemins = list(dict.fromkeys(chemins))
        resultats = {}
        if not chemins:
            return resultats

        def une(chemin):
            try:
                return chemin, self.get(chemin, ttl)
            except ErreurReseau as e:
                print(f"  ! {e}")
                return chemin, None

        with ThreadPoolExecutor(self.paralleles) as ex:
            for i, (chemin, html) in enumerate(ex.map(une, chemins), 1):
                resultats[chemin] = html
                if message and (i % 25 == 0 or i == len(chemins)):
                    print(f"  {message} : {i}/{len(chemins)}", flush=True)
        return resultats

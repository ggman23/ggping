"""Données du PC envoyées sur GitHub : même résultat en ligne que sur le PC."""

import io
import json
import os
import tarfile
import time

import pytest

from ttvaires import synchro
from ttvaires.effectif import _nouveaux
from ttvaires.reseau import Client, ErreurReseau

IL_Y_A_3_JOURS = time.time() - 3 * 86400


def _ecrire(chemin, contenu, date=None):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")
    if date:
        os.utime(chemin, (date, date))


def test_paquet_puis_deballage_avec_les_dates(tmp_path):
    pc, en_ligne = tmp_path / "pc", tmp_path / "en_ligne"
    _ecrire(pc / "import" / "vaires.mhtml", "liste", IL_Y_A_3_JOURS)
    _ecrire(pc / "import" / "LISEZ-MOI.txt", "mode d'emploi")             # pas une page : non envoyé
    _ecrire(pc / "cache" / "a1.html", '<div data-title="X">pingpocket</div>', IL_Y_A_3_JOURS)
    _ecrire(pc / "cache" / "b2.html", '{"@context": "API FFTT"}')          # relu en ligne : non envoyé
    _ecrire(pc / "cache" / "effectif_08770250.json", '{"date": "pc"}')

    archive, nb = synchro.paquet(pc)
    assert nb == 3
    assert synchro.deballer(archive, en_ligne) == 3
    assert (en_ligne / "import" / "vaires.mhtml").read_text() == "liste"
    assert abs((en_ligne / "cache" / "a1.html").stat().st_mtime - IL_Y_A_3_JOURS) < 2  # date d'origine gardée
    assert not (en_ligne / "cache" / "b2.html").exists() and not (en_ligne / "import" / "LISEZ-MOI.txt").exists()

    # Un fichier plus récent déjà présent est gardé, sauf l'état de l'effectif (celui du PC fait foi).
    _ecrire(en_ligne / "cache" / "a1.html", "plus récent")
    _ecrire(en_ligne / "cache" / "effectif_08770250.json", '{"date": "en ligne"}')
    assert synchro.deballer(archive, en_ligne) == 1
    assert (en_ligne / "cache" / "a1.html").read_text() == "plus récent"
    assert json.loads((en_ligne / "cache" / "effectif_08770250.json").read_text()) == {"date": "pc"}


def test_deballage_refuse_les_chemins_hors_des_dossiers_prevus(tmp_path):
    tampon = io.BytesIO()
    with tarfile.open(fileobj=tampon, mode="w:gz") as tar:
        for nom in ("../evil.txt", "cache/../../evil.txt", "ttvaires/__init__.py", "cache/sous/dossier.html"):
            info = tarfile.TarInfo(nom)
            info.size = 4
            tar.addfile(info, io.BytesIO(b"mal!"))
    assert synchro.deballer(tampon.getvalue(), tmp_path / "en_ligne") == 0
    assert not (tmp_path / "evil.txt").exists() and not (tmp_path / "en_ligne").exists()


def test_mode_cache_seul_n_interroge_pas_le_site(tmp_path):
    client = Client(tmp_path, sites_cache_seul={"www.pingpocket.fr"})
    ancienne = client._fichier("/app/fftt/clubs/1/licencies?SORT=CATEGORY")
    _ecrire(ancienne, '<div data-title="Club">liste</div>', IL_Y_A_3_JOURS)
    client._session = lambda: pytest.fail("aucune requête ne doit partir vers pingpocket")

    page = client.get("/app/fftt/clubs/1/licencies?SORT=CATEGORY", ttl=3600, perime_si_erreur=True)
    assert "liste" in page and "/app/fftt/clubs/1/licencies?SORT=CATEGORY" in client.perimes
    assert client.en_cache("/app/fftt/clubs/1/licencies?SORT=CATEGORY", ttl=3600)
    with pytest.raises(ErreurReseau, match="données envoyées par le PC"):
        client.get("/app/fftt/clubs/2/coordonnees", perime_si_erreur=True)
    assert client.disponible("www.pingpocket.fr")


def test_les_nouveaux_restent_tant_que_la_liste_ne_change_pas(tmp_path):
    etat = tmp_path / "etat.json"
    etat.write_text(json.dumps({"date": "2026-10-01T10:00", "renouveles": ["1", "2"]}))

    def lancer(ids, date):
        joueurs = {i: {"id": i, "renouvele": True, "loisir": False} for i in ids}
        _nouveaux(joueurs, etat, {"liste": True, "date": date})
        return sorted(i for i, j in joueurs.items() if j.get("nouveau"))

    assert lancer(["1", "2", "3"], "2026-10-10T10:00") == ["3"]
    assert lancer(["1", "2", "3"], "2026-10-12T10:00") == ["3"]  # relancé : toujours signalé
    assert lancer(["1", "2", "3", "4"], "2026-10-15T10:00") == ["4"]


class _Reponse:
    def __init__(self, statut, contenu=None):
        self.status_code, self._contenu, self.text = statut, contenu, json.dumps(contenu)

    def json(self):
        return self._contenu


def test_envoi_sur_github(monkeypatch, tmp_path):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:  # absente, ou installation cassée
        pytest.skip("bibliothèque cryptography indisponible")
    monkeypatch.setattr(synchro, "RACINE", tmp_path)
    _ecrire(tmp_path / "import" / "vaires.html", "liste")
    appels = []

    def requete(methode, url, headers=None, **options):
        appels.append((methode, url.replace(synchro.API, "")))
        assert headers["Authorization"] == "Bearer jeton"
        if url.endswith("/releases/tags/donnees-pc"):
            return _Reponse(200, {"upload_url": "https://uploads.github.com/repos/d/r/releases/9/assets{?name,label}",
                                  "assets": [{"name": "donnees-pc.chiffre", "id": 5}]})
        if url.endswith("/repos/d/r"):
            return _Reponse(200, {"default_branch": "principale"})
        if methode == "POST" and "uploads.github.com" in url:
            assert options["params"] == {"name": "donnees-pc.chiffre"} and len(options["data"]) > 28
            return _Reponse(201, {})
        if url.endswith("/dispatches"):
            assert options["json"] == {"ref": "principale", "inputs": {"pages": "tout"}}
            return _Reponse(204)
        return _Reponse(204)

    monkeypatch.setattr(synchro.requests, "request", requete)
    synchro.envoyer({"depot": "d/r", "jeton": "jeton", "mot_de_passe": "secret"})
    assert [a for a in appels if a[0] != "GET"] == [
        ("DELETE", "/repos/d/r/releases/assets/5"),                                   # ancien fichier remplacé
        ("POST", "https://uploads.github.com/repos/d/r/releases/9/assets"),
        ("POST", "/repos/d/r/actions/workflows/mise-a-jour.yml/dispatches")]          # site mis à jour

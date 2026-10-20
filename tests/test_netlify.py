"""Copie du site sur Netlify : accueil public (adversaires), /gg/ chiffré, envoi par l'API Netlify."""

import io
import json
import zipfile

import pytest

from ttvaires import netlify, publier


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:  # absente, ou installation cassée
        pytest.skip("bibliothèque cryptography indisponible")


def _site(tmp_path):
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    (sortie / "vaires.html").write_text('<!doctype html><html><head><meta charset="utf-8"></head><body>LOGNES 21</body></html>',
                                        encoding="utf-8")
    (sortie / "resultats_vaires.html").write_text("<p>DELOBELLE 780</p>", encoding="utf-8")
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-10-20T08:00", "fin": "2026-10-20T08:05", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["vaires.html"]},
        {"nom": "résultats", "resume": "ok", "fichiers": ["resultats_vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "ggman23/ggping", "principale")
    return site


def _contenu(page, mot_de_passe):
    import base64
    chiffre = netlify.CHIFFRE.search(page.read_text(encoding="utf-8"))[1]
    return publier.dechiffrer(base64.b64decode(chiffre), publier.cle(mot_de_passe)).decode("utf-8")


def test_accueil_public_et_gg_avec_son_propre_mot_de_passe(tmp_path):
    _crypto()
    site = _site(tmp_path)
    (site / "images").mkdir()
    (site / "images" / "recap_J3.png.chiffre").write_bytes(publier.chiffrer(b"\x89PNG", publier.cle("secret")))
    dossier = netlify.construire(site, tmp_path / "netlify", "secret", "mdp-des-capitaines")
    accueil = (dossier / "index.html").read_text(encoding="utf-8")
    assert "LOGNES 21" in accueil and netlify.NOINDEX in accueil          # adversaires, en clair, non référencé
    page = dossier / "gg" / "resultats.html"
    assert "DELOBELLE" not in page.read_text(encoding="utf-8")            # /gg/ reste chiffré...
    assert _contenu(page, "mdp-des-capitaines") == "<p>DELOBELLE 780</p>"             # ... avec le mot de passe de /gg/
    with pytest.raises(Exception):
        _contenu(page, "secret")                                           # pas avec celui du site GitHub
    image = (dossier / "gg" / "images" / "recap_J3.png.chiffre").read_bytes()
    assert publier.dechiffrer(image, publier.cle("mdp-des-capitaines")) == b"\x89PNG"
    assert (dossier / "gg" / "index.html").read_bytes() == (site / "index.html").read_bytes()
    assert (dossier / "gg" / "etat.json").exists()
    assert (dossier / "robots.txt").read_text().endswith("Disallow: /\n")
    assert "X-Robots-Tag: noindex" in (dossier / "_headers").read_text()
    noms = zipfile.ZipFile(io.BytesIO(netlify.archive(dossier))).namelist()
    assert "index.html" in noms and "gg/resultats.html" in noms and "_headers" in noms


class _Reponse:
    def __init__(self, statut, contenu=None):
        self.status_code, self._contenu, self.text = statut, contenu or {}, json.dumps(contenu or {})
        self.ok = statut < 400

    def json(self):
        return self._contenu


def test_envoi_et_erreurs(monkeypatch, tmp_path):
    dossier = tmp_path / "netlify"
    dossier.mkdir()
    (dossier / "index.html").write_text("ok")
    appels = []

    def post(url, data=None, headers=None, timeout=None):
        appels.append(url)
        assert headers["Authorization"] == "Bearer jeton" and headers["Content-Type"] == "application/zip"
        assert zipfile.ZipFile(io.BytesIO(data)).namelist() == ["index.html"]
        return _Reponse(200, {"id": "d1", "state": "uploaded"})

    monkeypatch.setattr(netlify.requests, "post", post)
    monkeypatch.setattr(netlify.requests, "get", lambda url, **o: _Reponse(200, {"id": "d1", "state": "ready",
                                                                               "ssl_url": "https://ggping.netlify.app"}))
    monkeypatch.setattr(netlify.time, "sleep", lambda s: None)
    assert netlify.deployer(dossier, "jeton") == "https://ggping.netlify.app"
    assert appels == ["https://api.netlify.com/api/v1/sites/ggping.netlify.app/deploys"]

    monkeypatch.setattr(netlify.requests, "post", lambda *a, **o: _Reponse(401))
    with pytest.raises(netlify.ErreurNetlify, match="jeton Netlify refusé"):
        netlify.deployer(dossier, "jeton")
    monkeypatch.setattr(netlify.requests, "post", lambda *a, **o: _Reponse(404))
    with pytest.raises(netlify.ErreurNetlify, match="introuvable"):
        netlify.deployer(dossier, "jeton")


def test_sans_jeton_rien_n_est_envoye(monkeypatch, capsys):
    monkeypatch.delenv("NETLIFY_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(netlify.requests, "post", lambda *a, **o: pytest.fail("rien ne doit partir sans jeton"))
    monkeypatch.setattr("sys.argv", ["netlify"])
    netlify.main()
    assert "pas de jeton" in capsys.readouterr().out


def test_sans_mot_de_passe_gg_seul_l_accueil_est_publie(tmp_path):
    _crypto()
    dossier = netlify.construire(_site(tmp_path), tmp_path / "netlify", "secret", "")
    assert (dossier / "index.html").exists() and not (dossier / "gg").exists()

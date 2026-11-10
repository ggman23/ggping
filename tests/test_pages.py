import pytest

from ttvaires import pages


class Reponse:
    def __init__(self, code, donnees=None):
        self.status_code, self._d = code, donnees
        self.ok, self.text, self.content = code < 400, str(donnees), b"x" if donnees is not None else b""

    def json(self):
        return self._d


def test_publication_avec_une_version_unique(monkeypatch):
    appels, etats = [], iter(["deployment_queued", "succeed"])

    def requete(methode, url, **o):
        appels.append((methode, url.replace(pages.API, ""), o.get("json")))
        if url.endswith("/git/commits/abc123"):
            return Reponse(200, {"tree": {"sha": "arbre1"}})
        if url.endswith("/git/commits"):
            return Reponse(201, {"sha": "pub999"})
        if "/git/refs/heads/" in url:
            return Reponse(422, {"message": "Reference does not exist"})  # première fois
        if url.endswith("/git/refs"):
            return Reponse(201, {"ref": "refs/heads/publication-pages"})
        if url.endswith("/pages/deployments"):
            return Reponse(200, {"status_url": "https://api.github.com/repos/g/p/pages/deployments/pub999",
                                 "page_url": "https://g.github.io/p/"})
        if "/pages/deployments/pub999" in url:
            return Reponse(200, {"status": next(etats)})
        raise AssertionError(url)

    monkeypatch.setattr(pages.requests, "request", requete)
    monkeypatch.setattr(pages, "jeton_oidc", lambda: "oidc")
    assert pages.publier("g/p", "abc123", "jeton", "42", "Publication", pause=0) == "https://g.github.io/p/"
    commit = next(j for m, u, j in appels if m == "POST" and u.endswith("/git/commits"))
    assert commit == {"message": "Publication", "tree": "arbre1", "parents": ["abc123"]}  # même contenu, nouvel identifiant
    assert ("POST", "/repos/g/p/git/refs", {"ref": "refs/heads/publication-pages", "sha": "pub999"}) in appels
    deploiement = next(j for m, u, j in appels if u.endswith("/pages/deployments"))
    assert deploiement == {"artifact_id": 42, "pages_build_version": "pub999", "oidc_token": "oidc"}


def test_echec_signale_pour_que_l_action_officielle_prenne_le_relais(monkeypatch, capsys):
    for nom, valeur in (("GITHUB_REPOSITORY", "g/p"), ("GITHUB_SHA", "abc"), ("GITHUB_TOKEN", "t"), ("ARTIFACT_ID", "1")):
        monkeypatch.setenv(nom, valeur)
    monkeypatch.setattr(pages.requests, "request", lambda *a, **o: Reponse(403, {"message": "Resource not accessible"}))
    assert pages.main() == 1
    assert "l'action officielle prend le relais" in capsys.readouterr().out


def test_deploiement_en_erreur(monkeypatch):
    monkeypatch.setattr(pages, "commit_de_publication", lambda *a: "v1")
    monkeypatch.setattr(pages, "jeton_oidc", lambda: "oidc")
    reponses = iter([Reponse(200, {"id": "v1"}), Reponse(200, {"status": "deployment_failed"})])
    monkeypatch.setattr(pages.requests, "request", lambda *a, **o: next(reponses))
    with pytest.raises(pages.ErreurPages, match="deployment_failed"):
        pages.publier("g/p", "abc", "t", "1", "m", pause=0)

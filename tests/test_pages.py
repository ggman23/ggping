from ttvaires import pages


class Reponse:
    def __init__(self, code, donnees=None):
        self.status_code, self._d = code, donnees
        self.ok, self.text, self.content = code < 400, str(donnees), b"x" if donnees is not None else b""

    def json(self):
        return self._d


def test_commit_vide_au_bout_de_la_branche(monkeypatch):
    appels, tetes = [], iter(["tete1", "tete2"])

    def requete(methode, url, **o):
        appels.append((methode, url.replace(pages.API, ""), o.get("json")))
        if "/git/ref/heads/principale" in url:
            return Reponse(200, {"object": {"sha": next(tetes)}})
        if "/git/commits/tete" in url:
            return Reponse(200, {"tree": {"sha": "arbre"}})
        if url.endswith("/git/commits"):
            return Reponse(201, {"sha": "vide-" + o["json"]["parents"][0]})
        if "/git/refs/heads/principale" in url:
            # 1re fois : quelqu'un a poussé entre-temps (pas d'avance rapide) ; 2e fois : accepté
            return Reponse(422 if o["json"]["sha"] == "vide-tete1" else 200, {})
        raise AssertionError(url)

    monkeypatch.setattr(pages.requests, "request", requete)
    monkeypatch.setattr(pages.time, "sleep", lambda s: None)
    assert pages.commit_suivant("g/p", "principale", "jeton", "Mise à jour du site") == "vide-tete2"
    commits = [j for m, u, j in appels if m == "POST" and u.endswith("/git/commits")]
    assert commits[-1] == {"message": "Mise à jour du site", "tree": "arbre", "parents": ["tete2"]}  # même contenu
    assert all(j["force"] is False for m, u, j in appels if m == "PATCH")  # jamais d'écrasement


def test_nettoyage_de_la_publication_bloquee(monkeypatch, capsys):
    appels = []

    def requete(methode, url, **o):
        appels.append((methode, url.replace(pages.API, "")))
        if url.endswith("/git/ref/heads/publication-pages"):
            return Reponse(200, {"object": {"sha": "cac4c94"}})
        return Reponse(200, {})

    monkeypatch.setattr(pages.requests, "request", requete)
    assert pages.nettoyer("g/p", "jeton") is True
    assert ("POST", "/repos/g/p/pages/deployments/cac4c94/cancel") in appels
    assert ("DELETE", "/repos/g/p/git/refs/heads/publication-pages") in appels
    # Déjà nettoyé : rien
    monkeypatch.setattr(pages.requests, "request", lambda *a, **o: Reponse(404, {"message": "Not Found"}))
    assert pages.nettoyer("g/p", "jeton") is False


def test_erreur_signalee_sans_faire_echouer(monkeypatch, capsys):
    for nom, valeur in (("GITHUB_REPOSITORY", "g/p"), ("GITHUB_TOKEN", "t"), ("GITHUB_REF_NAME", "principale")):
        monkeypatch.setenv(nom, valeur)
    monkeypatch.setattr(pages.requests, "request", lambda *a, **o: Reponse(403, {"message": "Resource not accessible"}))
    assert pages.main(["commit-suivant"]) == 0
    assert "::warning::GitHub Pages (commit-suivant)" in capsys.readouterr().out

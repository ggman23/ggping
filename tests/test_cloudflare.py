from ttvaires import cloudflare, netlify


class Reponse:
    def __init__(self, code, donnees=None):
        self.status_code, self._donnees, self.text = code, donnees or {}, ""
        self.ok = code < 400

    def json(self):
        return self._donnees


def _sortie(tmp_path, monkeypatch):
    f = tmp_path / "sortie"
    monkeypatch.setenv("GITHUB_OUTPUT", str(f))
    return f


def test_sans_secrets_rien_n_est_envoye(tmp_path, monkeypatch, capsys):
    sortie = _sortie(tmp_path, monkeypatch)
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.setattr(cloudflare.requests, "get", lambda *a, **o: (_ for _ in ()).throw(AssertionError("aucune requête")))
    cloudflare.main(["--dossier", str(tmp_path)])
    assert "pas de secrets" in capsys.readouterr().out
    assert "envoyer=false" in sortie.read_text()


def test_projet_cree_puis_envoi_si_contenu_nouveau(tmp_path, monkeypatch):
    sortie = _sortie(tmp_path, monkeypatch)
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "jeton")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "compte")
    monkeypatch.delenv("CLOUDFLARE_PROJET", raising=False)
    copie = tmp_path / "copie"
    copie.mkdir()
    (copie / "index.html").write_text("<p>accueil</p>")
    (copie / netlify.SIGNATURE).write_text("abc\n")
    appels = []
    monkeypatch.setattr(cloudflare.requests, "get", lambda url, **o: appels.append(("GET", url)) or Reponse(404))
    monkeypatch.setattr(cloudflare.requests, "post", lambda url, **o: appels.append(("POST", url, o["json"]))
                        or Reponse(200, {"result": {"subdomain": "ggping-x1.pages.dev"}}))
    en_ligne = {"valeur": None}
    monkeypatch.setattr(cloudflare, "signature_en_ligne", lambda hote: en_ligne["valeur"])
    cloudflare.main(["--dossier", str(copie)])
    assert appels[-1] == ("POST", f"{cloudflare.API}/accounts/compte/pages/projects", {"name": "ggping", "production_branch": "main"})
    assert sortie.read_text() == "envoyer=true\nprojet=ggping\nadresse=https://ggping-x1.pages.dev/\n"
    # Même empreinte en ligne : pas d'envoi
    sortie.write_text("")
    en_ligne["valeur"] = "abc"
    cloudflare.main(["--dossier", str(copie)])
    assert sortie.read_text().startswith("envoyer=false")


def test_jeton_refuse_signale_sans_echec(tmp_path, monkeypatch, capsys):
    sortie = _sortie(tmp_path, monkeypatch)
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "jeton")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "compte")
    (tmp_path / "index.html").write_text("x")
    monkeypatch.setattr(cloudflare.requests, "get", lambda url, **o: Reponse(403, {"errors": [{"code": 10000, "message": "Authentication error"}]}))
    assert cloudflare.main(["--dossier", str(tmp_path)]) == 0
    assert "jeton Cloudflare refusé" in capsys.readouterr().out and "envoyer=false" in sortie.read_text()

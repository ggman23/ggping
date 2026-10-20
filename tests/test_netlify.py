"""Copie du site sur Netlify : accueil public (adversaires), /gg/ chiffré, envoi par l'API Netlify."""

import json

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
    noms = {f.relative_to(dossier).as_posix() for f in dossier.rglob("*") if f.is_file()}
    assert {"index.html", "gg/resultats.html", "_headers"} <= noms
    # Re-chiffrement stable : refaire la copie ne change pas les fichiers (Netlify ne les renvoie pas)
    avant = page.read_bytes()
    netlify.construire(site, tmp_path / "netlify", "secret", "mdp-des-capitaines")
    assert page.read_bytes() == avant


class _Reponse:
    def __init__(self, statut, contenu=None):
        self.status_code, self._contenu, self.text = statut, contenu or {}, json.dumps(contenu or {})
        self.ok = statut < 400

    def json(self):
        return self._contenu


def test_envoi_par_empreintes_seuls_les_fichiers_changes(monkeypatch, tmp_path):
    import hashlib
    dossier = tmp_path / "netlify"
    (dossier / "club" / "archives").mkdir(parents=True)
    (dossier / "index.html").write_text("nouvelle page")
    (dossier / "club" / "archives" / "J1.chiffre").write_bytes(b"archive")
    envois = []

    def post(url, json=None, headers=None, timeout=None):
        assert url == "https://api.netlify.com/api/v1/sites/ggping.netlify.app/deploys"
        assert headers["Authorization"] == "Bearer jeton"
        assert set(json["files"]) == {"/index.html", "/club/archives/J1.chiffre"}
        # Netlify a déjà l'archive : il ne demande que la nouvelle page
        return _Reponse(200, {"id": "d1", "state": "uploading", "required": [hashlib.sha1(b"nouvelle page").hexdigest()]})

    def put(url, data=None, headers=None, timeout=None):
        envois.append((url, data))
        return _Reponse(200, {})

    monkeypatch.setattr(netlify.requests, "post", post)
    monkeypatch.setattr(netlify.requests, "put", put)
    monkeypatch.setattr(netlify.requests, "get", lambda url, **o: _Reponse(200, {"id": "d1", "state": "ready",
                                                                               "ssl_url": "https://ggping.netlify.app"}))
    monkeypatch.setattr(netlify.time, "sleep", lambda s: None)
    assert netlify.deployer(dossier, "jeton") == "https://ggping.netlify.app"
    assert envois == [("https://api.netlify.com/api/v1/deploys/d1/files/index.html", b"nouvelle page")]

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


def test_espace_club_avec_son_propre_mot_de_passe(tmp_path):
    _crypto()
    site = _site(tmp_path)
    (site / "images").mkdir()
    (site / "images" / "recap_J3.png.chiffre").write_bytes(publier.chiffrer(b"\x89PNG", publier.cle("secret")))
    etat = json.loads((site / "etat.json").read_text(encoding="utf-8"))
    etat["images"]["images/recap_J3.png.chiffre"] = {"titre": "Récapitulatif J3", "groupe": "rencontres", "ordre": 0,
                                                     "date": "2026-10-20T08:05", "nom_telecharge": "recap_J3.png"}
    (site / "etat.json").write_text(json.dumps(etat), encoding="utf-8")
    dossier = netlify.construire(site, tmp_path / "netlify", "secret", "", "mdp-du-club")
    club = dossier / "club"
    cle = publier.cle("mdp-du-club")
    lire = lambda nom: publier.dechiffrer((club / "fichiers" / f"{nom}.chiffre").read_bytes(), cle)  # noqa: E731
    assert lire("resultats_vaires.html") == b"<p>DELOBELLE 780</p>"   # pages sous leur nom d'origine
    assert lire("vaires.html").startswith(b"<!doctype html>") and lire("recap_J3.png") == b"\x89PNG"
    assert lire("verif") == netlify.VERIF_CLUB
    with pytest.raises(Exception):
        publier.dechiffrer((club / "fichiers" / "vaires.html.chiffre").read_bytes(), publier.cle("secret"))
    page = (club / "index.html").read_text(encoding="utf-8")
    assert "DELOBELLE" not in page and "LOGNES" not in page            # la liste ne contient aucun nom de joueur
    donnees = json.loads(page.split('<script id="donnees" type="application/json">')[1].split("</script>")[0])
    assert [(d["fichier"], d["type"]) for d in donnees["documents"]] == [
        ("vaires.html", "page"), ("resultats_vaires.html", "page"), ("recap_J3.png", "image")]
    assert "dispatches" not in page and "jeton" not in page.lower()     # pas de lancement de mise à jour
    assert not (dossier / "gg").exists()                               # pas de secret pour /gg/ : non publié


def test_espace_club_avec_les_archives(tmp_path):
    _crypto()
    from ttvaires import archives
    site = _site(tmp_path)
    # une archive : un petit site complet sous archives/<clé>/
    sortie_j1 = tmp_path / "sortie_j1"
    sortie_j1.mkdir()
    (sortie_j1 / "resultats_vaires.html").write_text("<p>J1 : DELOBELLE 780</p>", encoding="utf-8")
    (sortie_j1 / "bilan.json").write_text(json.dumps({"debut": "2026-10-01T08:00", "fin": "2026-10-01T08:05", "pages": [
        {"nom": "résultats", "resume": "ok", "fichiers": ["resultats_vaires.html"]}]}))
    infos = {"titre": "Journée 1", "journee": 1, "phase": 1, "saison": "2026-2027", "date_reference": "2026-10-01"}
    publier.publier(sortie_j1, site / "archives" / "2026-2027-P1-J1", "secret", archive={**infos, "retour": "../../"})
    etat = json.loads((site / "etat.json").read_text(encoding="utf-8"))
    etat["archives"] = {"2026-2027-P1-J1": {**infos, "dossier": "archives/2026-2027-P1-J1/",
                        "fichiers": [f"archives/2026-2027-P1-J1/{f.relative_to(site / 'archives' / '2026-2027-P1-J1').as_posix()}"
                                     for f in (site / "archives" / "2026-2027-P1-J1").rglob("*") if f.is_file()]}}
    etat = publier.ecrire_etat(site, etat)
    assert "archives/2026-2027-P1-J1/resultats.html" in etat["fichiers"]   # repris à chaque mise à jour
    dossier = netlify.construire(site, tmp_path / "netlify", "secret", "", "mdp-du-club")
    page = (dossier / "club" / "index.html").read_text(encoding="utf-8")
    donnees = json.loads(page.split('<script id="donnees" type="application/json">')[1].split("</script>")[0])
    [archive] = donnees["archives"]
    assert archive["titre"] == "Journée 1" and archive["date_reference"] == "2026-10-01"
    [doc] = archive["documents"]
    assert doc["chemin"] == "archives/2026-2027-P1-J1/fichiers/resultats_vaires.html.chiffre"
    assert publier.dechiffrer((dossier / "club" / doc["chemin"]).read_bytes(), publier.cle("mdp-du-club")) == "<p>J1 : DELOBELLE 780</p>".encode()
    assert "DELOBELLE" not in page


def test_journees_a_archiver():
    from datetime import date
    from ttvaires.archives import a_archiver
    journees = [(1, "2026-09-25"), (2, "2026-10-02"), (3, "2026-10-16"), (4, "2026-11-06")]
    assert a_archiver(journees, date(2026, 10, 20)) == [(1, date(2026, 10, 1)), (2, date(2026, 10, 15))]
    # la J4 a commencé : la J3 passe en archive, datée de la veille de la J4
    assert a_archiver(journees, date(2026, 11, 6))[-1] == (3, date(2026, 11, 5))
    assert a_archiver(journees, date(2026, 9, 1)) == []


def test_archive_refaite_si_surnoms_photo_ou_logos_changent(tmp_path, monkeypatch):
    from ttvaires.archives import signature
    monkeypatch.delenv("SURNOMS", raising=False)
    imports = tmp_path / "import"
    imports.mkdir()
    avant = signature("secret", 2, imports)
    assert signature("secret", 2, imports) == avant
    (imports / "photo_J3.jpg").write_bytes(b"photo d'une autre journee")
    assert signature("secret", 2, imports) == avant
    monkeypatch.setenv("SURNOMS", "GUITTON Marc = Marc G")
    avec_surnom = signature("secret", 2, imports)
    assert avec_surnom != avant and "Marc" not in avec_surnom
    (imports / "photo_J2.jpg").write_bytes(b"photo de la J2")
    assert signature("secret", 2, imports) != avec_surnom
    assert signature("autre mot de passe", 2, imports) != signature("secret", 2, imports)


def test_compteur_de_visites_seulement_s_il_est_regle(tmp_path):
    _crypto()
    site = _site(tmp_path)
    sans = netlify.construire(site, tmp_path / "sans", "secret", "mdp-gg", "mdp-club")
    assert not [f for f in sans.rglob("*.html") if "goatcounter.com" in f.read_text(encoding="utf-8")]
    avec = netlify.construire(site, tmp_path / "avec", "secret", "mdp-gg", "mdp-club", "cvtt-vaires")
    accueil = (avec / "index.html").read_text(encoding="utf-8")
    assert 'data-goatcounter="https://cvtt-vaires.goatcounter.com/count"' in accueil
    assert f'integrity="{netlify.GOATCOUNTER_SRI}"' in accueil and "no_onload" not in accueil  # une vue par chargement
    assert "compteurVisiteurs()" in accueil and "appareils/" in accueil  # appareils différents, sans identifiant
    for page in (avec / "club" / "index.html", avec / "gg" / "index.html"):
        texte = page.read_text(encoding="utf-8")
        assert '"no_onload": true' in texte and "function compter(" in texte  # la page compte elle-même
    assert "goatcounter.com" not in (avec / "gg" / "resultats.html").read_text(encoding="utf-8")
    # Seul le code du compte est accepté (pas une autre adresse)
    assert netlify.code_goatcounter("https://CVTT-Vaires.goatcounter.com/count") == "cvtt-vaires"
    assert netlify.code_goatcounter("https://exemple.com/x") == "" and netlify.code_goatcounter("") == ""

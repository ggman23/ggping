"""Publication du site : pages chiffrées, pages non régénérées conservées, rien sans mot de passe."""

import base64
import json
import re

import pytest

from ttvaires import publier


def _crypto():
    """La publication a besoin de la bibliothèque cryptography (installée par le workflow GitHub)."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:  # absente, ou installation cassée
        pytest.skip("bibliothèque cryptography indisponible")


def _sortie(tmp_path, pages):
    sortie = tmp_path / "sortie"
    sortie.mkdir()
    for nom, contenu in pages.items():
        (sortie / nom).write_bytes(contenu)
    (sortie / "bilan.json").write_text(json.dumps({
        "debut": "2026-10-18T09:00", "fin": "2026-10-18T09:05",
        "pages": [{"nom": "résultats", "resume": "tous les résultats sont là", "fichiers": list(pages)}]}))
    return sortie


def test_page_chiffree_et_dechiffrable():
    _crypto()
    cle = publier.cle("mot de passe du club")
    page = publier.page_verrouillee("<h1>GUITTON Marc 1410</h1>", "Résultats", cle)
    assert "GUITTON" not in page and "noindex" in page and "Résultats" in page
    chiffre = re.search(r'<script id="chiffre" type="text/plain">([^<]+)</script>', page)[1]
    assert publier.dechiffrer(base64.b64decode(chiffre), cle) == "<h1>GUITTON Marc 1410</h1>".encode()
    with pytest.raises(Exception):
        publier.dechiffrer(base64.b64decode(chiffre), publier.cle("autre"))


def test_publication_garde_les_pages_non_regenerees(tmp_path):
    _crypto()
    site = tmp_path / "site"
    site.mkdir()
    (site / "adversaires.html").write_text("ancienne page chiffrée")
    (site / "etat.json").write_text(json.dumps({
        "pages": {"adversaires.html": {"titre": "Adversaires", "date": "2026-10-11T08:00", "verification": "ok"}},
        "fichiers": ["adversaires.html"]}))
    sortie = _sortie(tmp_path, {"resultats_vaires.html": "<p>DELOBELLE 823</p>".encode(), "resultats_vaires.xlsx": b"PK\x03\x04xlsx"})

    etat = publier.publier(sortie, site, "secret", "ggman23/ggping", "principale")

    assert etat["fichiers"] == ["adversaires.html", "resultats.html", "resultats_vaires.xlsx.chiffre"]
    assert etat["pages"]["adversaires.html"]["date"] == "2026-10-11T08:00"  # reprise telle quelle
    assert etat["pages"]["resultats.html"]["verification"] == "tous les résultats sont là"
    assert etat["pages"]["resultats_vaires.xlsx.chiffre"]["telechargement"]
    assert publier.dechiffrer((site / "resultats_vaires.xlsx.chiffre").read_bytes(), publier.cle("secret")) == b"PK\x03\x04xlsx"
    assert "DELOBELLE" not in (site / "resultats.html").read_text()
    accueil = (site / "index.html").read_text()
    assert '"depot": "ggman23/ggping"' in accueil and "DELOBELLE" not in accueil
    assert (site / "robots.txt").read_text().endswith("Disallow: /\n")


def test_rien_n_est_publie_sans_mot_de_passe(tmp_path):
    sortie = _sortie(tmp_path, {"resultats_vaires.html": b"<p>donnees</p>"})
    with pytest.raises(publier.ErreurPublication, match="MOT_DE_PASSE_SITE"):
        publier.publier(sortie, tmp_path / "site", "")
    assert not (tmp_path / "site").exists()


def test_images_publiees_et_remplacees_a_chaque_lancement(tmp_path):
    _crypto()
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    (sortie / "images").mkdir(parents=True)

    def lancer(noms, fin):
        for n in noms:
            (sortie / "images" / n).write_bytes(b"\x89PNG" + n.encode())
        (sortie / "bilan.json").write_text(json.dumps({"debut": fin, "fin": fin, "pages": [
            {"nom": "résultats", "resume": "ok", "fichiers": [],
             "images": [{"fichier": f"images/{n}", "titre": n} for n in noms]}]}))
        return publier.publier(sortie, site, "secret")

    lancer(["resultats_J3.png", "resultats_cumul.png"], "2026-10-18T09:00")
    etat = lancer(["resultats_J4.png", "resultats_cumul.png"], "2026-11-08T09:00")
    assert sorted(etat["images"]) == ["images/resultats_J4.png.chiffre", "images/resultats_cumul.png.chiffre"]
    assert not (site / "images" / "resultats_J3.png.chiffre").exists()
    assert "images/resultats_J4.png.chiffre" in etat["fichiers"]
    assert publier.dechiffrer((site / "images" / "resultats_J4.png.chiffre").read_bytes(), publier.cle("secret")) \
        == b"\x89PNGresultats_J4.png"
    assert etat["images"]["images/resultats_cumul.png.chiffre"]["nom_telecharge"] == "resultats_cumul.png"

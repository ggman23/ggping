"""Tournois : page /tournois/ (blocs de PingRadar intégrés), publiée avec le mot de passe du club et reliée
à /club/ et /indivs/."""

import base64
import json
import re

import pytest

from ttvaires import netlify, publier

GABARIT = netlify.PAGES_FIXES["tournois"][1]


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:
        pytest.skip("bibliothèque cryptography indisponible")


def _site(tmp_path):
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    (sortie / "vaires.html").write_text("<p>adversaires</p>", encoding="utf-8")
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-11T08:00", "fin": "2026-11-11T08:05", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "g/p", "b")
    return site


def test_page_publiee_avec_le_mot_de_passe_du_club_sans_donnee_de_mise_a_jour(tmp_path):
    _crypto()
    site = _site(tmp_path)
    for dossier in (netlify.construire(site, tmp_path / "netlify", "secret", "", "club"),
                    netlify.site_github(site, tmp_path / "github", "secret", "club")):
        page = (dossier / "tournois" / "index.html").read_text(encoding="utf-8")
        assert "pingradar" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page  # verrouillée, clé de /club/
        chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', page, re.S)[1].strip()
        assert publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club")) == GABARIT.read_bytes()
        club = (dossier / "club" / "index.html").read_text(encoding="utf-8")
        assert '{"chemin": "tournois", "titre": "Tournois"}' in club  # dans « Autres espaces » de /club/


def test_pas_d_espace_tournois_sans_mot_de_passe_du_club(tmp_path):
    site = _site(tmp_path)
    assert not (netlify.construire(site, tmp_path / "netlify", "secret", "") / "tournois").exists()
    assert not (netlify.site_github(site, tmp_path / "github", "secret", "") / "tournois").exists()


def test_blocs_pingradar_et_liens_entre_les_espaces():
    html = GABARIT.read_text(encoding="utf-8")
    assert "https://pingradar.fr" in html and "/integrer/prochains-tournois?" in html  # bloc prévu pour l'intégration
    assert 'VAIRES = "77479"' in html and "radius_km: 100" in html and "region: 11" in html and "department: 77" in html
    assert "/api/" not in html  # rien d'autre que les blocs et des liens
    assert "`${BASE}/club/`" in html and "`${BASE}/indivs/`" in html
    indivs = netlify.Path(netlify.__file__).with_name("gabarit_indivs.html").read_text(encoding="utf-8")
    assert "`${BASE}/tournois/`" in indivs and 'id="vers-tournois"' in indivs
    club = netlify.GABARIT_CLUB.read_text(encoding="utf-8")
    assert 'class="raccourcis"' in club  # accès direct aux autres espaces en haut du menu de /club/

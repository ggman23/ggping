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
        espaces = json.loads(re.search(r'"espaces": (\[.*?\])', club)[1])
        assert all(e["chemin"] in ("indivs", "tournois", "cal") for e in espaces)  # pas /lundi/ : administrateur et application


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


# ---------------------------------------------------------------------------
# Calendrier de la saison : page /cal/ (même principe que /tournois/)
# ---------------------------------------------------------------------------

def test_dates_du_calendrier_du_comite():
    from ttvaires import calendrier
    assert calendrier.jours_faux() == []  # chaque date tombe le jour de la semaine du calendrier du CD77
    d = calendrier.donnees()
    par_cat = {}
    for e in d["evenements"]:
        par_cat.setdefault(e["cat"], []).append(e)
    assert {c: len(v) for c, v in par_cat.items() if c in ("equipes", "feminin", "paris", "jeunes", "criterium")} == \
        {"equipes": 14, "feminin": 14, "paris": 7, "jeunes": 8, "criterium": 12}
    assert [e["debut"] for e in par_cat["paris"]] == [e["debut"] for e in par_cat["jeunes"]][:7]  # mêmes vendredis
    assert par_cat["equipes"][4] == {"debut": "2026-11-20", "fin": None, "cat": "equipes", "titre": "Équipes J5",
                                     "court": "Équipes J5", "detail": "Phase 1"}
    assert par_cat["criterium"][3]["court"] == "Crit. T2 jeunes" and par_cat["criterium"][3]["titre"] == "Critérium Tour 2 · jeunes"
    assert [e["debut"] for e in d["evenements"]] == sorted(e["debut"] for e in d["evenements"])
    assert {c["cle"] for c in d["categories"] if not c["affichee"]} == {"autres", "inscriptions"}


def test_page_cal_avec_le_mot_de_passe_du_club_et_liens_vers_les_espaces(tmp_path):
    _crypto()
    from ttvaires import calendrier
    site = _site(tmp_path)
    for dossier in (netlify.construire(site, tmp_path / "netlify", "secret", "", "club"),
                    netlify.site_github(site, tmp_path / "github", "secret", "club")):
        page = (dossier / "cal" / "index.html").read_text(encoding="utf-8")
        assert "Équipes J5" not in page and 'STOCKAGE = "cvtt-vaires-cle-club"' in page
        chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', page, re.S)[1].strip()
        html = publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club")).decode("utf-8")
        assert html == calendrier.page().decode("utf-8") and "Équipes J5" in html and "__DONNEES_JSON__" not in html
        club = (dossier / "club" / "index.html").read_text(encoding="utf-8")
        assert '{"chemin": "cal", "titre": "Calendrier"}' in club
    html = calendrier.page().decode("utf-8")
    assert all(f"`${{BASE}}/{e}/`" in html for e in ("club", "indivs", "tournois")) and "/lundi/" not in html
    for gabarit in ("gabarit_indivs.html", "gabarit_tournois.html"):  # et réciproquement
        autre = netlify.Path(netlify.__file__).with_name(gabarit).read_text(encoding="utf-8")
        assert 'id="vers-cal"' in autre and "`${BASE}/cal/`" in autre

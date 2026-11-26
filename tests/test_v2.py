"""Version 2 du site (/v2/, à l'essai) : fabriquée à côté du site actuel, à partir des pages publiées."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ttvaires import netlify, publier, v2

DONNEES_FRANCE = {"club": {"numero": "08770250", "nom": "CVTT Vaires"}, "equipes": [
    {"id": "v4", "nom_court": "Vaires 4", "numero": 4, "championnat": "M", "division": "Départementale 2", "poule": "Poule 6",
     "rencontres": [], "classement": []}],
    "clubs": {"08771201": {"nom": "CTT MONTHYON", "joueurs": [{"id": "1", "nom": "FICTIFNOM", "prenom": "Jean"}]}}}


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:
        pytest.skip("bibliothèque cryptography indisponible")


def _site(tmp_path):
    """Un site publié : la page des adversaires (données en <script id="donnees">) et celle des fiches
    (données en « const D = »), chiffrées avec la clé du site."""
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    js = json.dumps(DONNEES_FRANCE, ensure_ascii=False)
    (sortie / "vaires.html").write_text(f'<!doctype html><script id="donnees" type="application/json">{js}</script>', encoding="utf-8")
    (sortie / "fiches_vaires.html").write_text('<!doctype html><script>const D = {"joueurs": [{"id": "9", "nom": "LOGNES"}]};\nrendre();</script>',
                                               encoding="utf-8")
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-25T08:00", "fin": "2026-11-25T08:12", "pages": [
        {"nom": "adversaires", "resume": "ok", "fichiers": ["vaires.html"]}, {"nom": "fiches", "resume": "ok", "fichiers": ["fiches_vaires.html"]}]}))
    publier.publier(sortie, site, "secret", "ggman23/ggping", "principale")
    return site


def test_donnees_reprises_des_pages_publiees():
    assert v2.donnees_de_la_page('<script id="donnees" type="application/json">{"a": [1]}</script>') == {"a": [1]}
    assert v2.donnees_de_la_page('<script>\nconst D = {"b": "x;y"};\nconst E = 2;</script>') == {"b": "x;y"}
    assert v2.donnees_de_la_page("<p>rien</p>") is None


def test_v2_fabriquee_dans_la_copie_cloudflare(tmp_path):
    """La copie (Cloudflare, Netlify) a une /v2/ : pages sans aucune donnée, données rechiffrées avec la clé du
    club (le même mot de passe que /club/), aucun nom de joueur en clair ; le site actuel est inchangé."""
    _crypto()
    site = _site(tmp_path)
    dossier = netlify.construire(site, tmp_path / "copie", "secret", "", "mdp-du-club")
    racine = dossier / "v2"
    for page in ("index.html", "equipes/index.html", "rencontre/index.html", "joueurs/index.html", "agenda/index.html", "club/index.html",
                 "commun.css", "commun.js", "sw.js", "manifest.webmanifest", "icones/icone-192.png", "icones/icone-512.png"):
        assert (racine / page).exists(), page
    cle = publier.cle("mdp-du-club")
    lire = lambda nom: json.loads(publier.dechiffrer((racine / "donnees" / f"{nom}.json.chiffre").read_bytes(), cle))  # noqa: E731
    assert lire("france") == DONNEES_FRANCE and lire("fiches") == {"joueurs": [{"id": "9", "nom": "LOGNES"}]}
    assert lire("agenda")["evenements"] and [d["fichier"] for d in lire("club")["documents"]] == ["vaires.html", "fiches_vaires.html"]
    assert publier.dechiffrer((racine / "donnees" / "verif.chiffre").read_bytes(), cle) == netlify.VERIF_CLUB
    assert lire("index")["maj"] == "2026-11-25T08:12" and lire("index")["donnees"] == ["france", "fiches", "agenda", "club"]
    with pytest.raises(Exception):
        publier.dechiffrer((racine / "donnees" / "france.json.chiffre").read_bytes(), publier.cle("secret"))
    for f in racine.rglob("*"):
        if f.is_file() and f.suffix in (".html", ".js", ".css", ".webmanifest"):
            texte = f.read_text(encoding="utf-8")
            assert "FICTIFNOM" not in texte and "LOGNES" not in texte, f       # aucune donnée dans les pages
            assert not re.search(r"__[A-Z]+__", texte), f                       # réglages remplacés
            assert not re.search(r"""<(script|link|img|iframe)[^>]+(src|href)=["']https?://""", texte), f  # rien d'extérieur chargé
    commun = (racine / "commun.js").read_text(encoding="utf-8")
    assert f'const SEL = "{publier.SEL}", ITERATIONS = {publier.ITERATIONS}' in commun and '"cvtt-vaires-cle-club"' in commun
    from PIL import Image
    assert Image.open(racine / "icones" / "icone-512.png").size == (512, 512)
    assert (dossier / "club" / "index.html").exists() and (dossier / "index.html").exists()  # le reste de la copie, comme avant


def test_v2_en_echec_ne_bloque_pas_la_copie(tmp_path, monkeypatch, capsys):
    _crypto()
    site = _site(tmp_path)
    monkeypatch.setattr(v2, "construire", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("essai")))
    dossier = netlify.construire(site, tmp_path / "copie", "secret", "", "mdp-du-club")
    assert not (dossier / "v2").exists() and (dossier / "club" / "index.html").exists()
    assert "Version 2 (/v2/) non publiée" in capsys.readouterr().out
    assert not (netlify.construire(site, tmp_path / "copie2", "secret", "", "") / "v2").exists()  # sans mot de passe du club : pas de v2


def test_pages_de_la_v2_coherentes():
    """Chaque page charge le style et le code communs, se situe (racine, rubrique) et garde le repère de
    l'application Android ; les cinq onglets mènent à des pages qui existent."""
    pages = sorted(v2.STATIQUE.rglob("index.html"))
    assert {p.parent.name for p in pages} == {"v2", "equipes", "rencontre", "joueurs", "agenda", "club", "indivs", "77", "tournois"}
    for p in pages:
        html = p.read_text(encoding="utf-8")
        profondeur = len(p.relative_to(v2.STATIQUE).parts) - 1
        racine = "./" if profondeur == 0 else "../" * profondeur
        assert f'data-racine="{racine}"' in html and f'src="{racine.removeprefix("./")}commun.js?v=__VERSION__"' in html, p
        assert '<meta name="cvtt-cle" content="cvtt-vaires-cle-club">' in html and 'name="robots" content="noindex' in html, p
    commun = (v2.STATIQUE / "commun.js").read_text(encoding="utf-8")
    onglets = commun[commun.index("const ONGLETS"):commun.index("function cadre")]
    assert len(re.findall(r'\["\w+", "[^"]+", "([^"]*)"\]', onglets)) == 5
    for lien in re.findall(r'\["\w+", "[^"]+", "([^"]*)"\]', onglets):
        assert (v2.STATIQUE / lien / "index.html").exists(), lien


@pytest.mark.skipif(not shutil.which("node"), reason="node absent")
def test_javascript_de_la_v2_sans_erreur_de_syntaxe(tmp_path):
    fichiers = [v2.STATIQUE / "commun.js", v2.STATIQUE / "sw.js"]
    for p in v2.STATIQUE.rglob("index.html"):
        for i, script in enumerate(re.findall(r"<script>\n(.*?)</script>", p.read_text(encoding="utf-8"), re.S)):
            f = tmp_path / f"{p.parent.name}-{i}.js"
            f.write_text(script, encoding="utf-8")
            fichiers.append(f)
    for f in fichiers:
        texte = f.read_text(encoding="utf-8").replace("__ITERATIONS__", "1")
        g = tmp_path / f"verif-{f.name}"
        g.write_text(texte, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(g)], capture_output=True, text=True)
        assert r.returncode == 0, f"{f}: {r.stderr}"


def test_icone_dessinee():
    from io import BytesIO

    from PIL import Image
    img = Image.open(BytesIO(v2.icone(192)))
    assert img.size == (192, 192) and img.getpixel((4, 4)) == v2.NUIT and v2.ROUGE in {c for _, c in img.getcolors(1 << 16)}


def test_lecture_d_une_page_absente_ou_illisible(tmp_path):
    assert v2.lire_page(tmp_path, "absente.html", publier.cle("x")) is None
    (tmp_path / "abimee.html").write_text('<script id="chiffre" type="text/plain">AAAA</script>', encoding="utf-8")
    assert v2.lire_page(tmp_path, "abimee.html", publier.cle("x")) is None
    assert Path(v2.STATIQUE / "sw.js").read_text(encoding="utf-8").count("cvtt-v2-") >= 2

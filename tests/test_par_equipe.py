"""Vue par équipe (26/11) : chaque page du site s'ouvre sur une seule équipe (#seule/<code>) ; l'espace club et la
v2 ont une page par équipe (ses pages et ses images)."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ttvaires import netlify, paris, publier, rendu

GABARITS = [rendu.GABARIT, rendu.GABARIT_RENCONTRES, rendu.GABARIT_CLASSEMENTS, rendu.GABARIT_EFFECTIF,
            rendu.GABARIT_PROGRESSION, rendu.GABARIT_RESULTATS, paris.GABARIT]


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401
    except BaseException:
        pytest.skip("bibliothèque cryptography indisponible")


def test_chaque_page_a_sa_vue_une_seule_equipe():
    for g in GABARITS:
        html = g.read_text(encoding="utf-8")
        assert "#seule\\/(v\\d+f?)" in html and "bandeauSeule(" in html and "#toutes" in html, g.name


def test_code_d_equipe_de_chaque_libelle():
    """Le même code pour une équipe, quelle que soit la façon dont chaque page la nomme."""
    if not shutil.which("node"):
        pytest.skip("node absent")
    html = rendu.GABARIT_RESULTATS.read_text(encoding="utf-8")
    fonction = re.search(r"const codeEquipe = .*?;\n", html)[0]
    essai = fonction + 'console.log(JSON.stringify(["VAIRES 1 F", "V1 F", "Vaires 2", "VAIRES CVTT 2", "V6", "Vaires 1 · −15 ans", "x"].map(codeEquipe)));'
    r = subprocess.run(["node", "-e", essai], capture_output=True, text=True)
    assert json.loads(r.stdout) == ["v1f", "v1f", "v2", "v2", "v6", "v1", None]


@pytest.mark.skipif(not shutil.which("node"), reason="node absent")
def test_javascript_des_pages_sans_erreur_de_syntaxe(tmp_path):
    for g in GABARITS + [netlify.GABARIT_CLUB, rendu.GABARIT_INDIVS]:
        for i, script in enumerate(re.findall(r"<script>\n(.*?)</script>", g.read_text(encoding="utf-8"), re.S)):
            f = tmp_path / f"{g.stem}-{i}.js"
            f.write_text(script.replace("__DONNEES_JSON__", "{}"), encoding="utf-8")
            r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            assert r.returncode == 0, f"{g.name}: {r.stderr}"


def test_equipes_de_l_espace_club(tmp_path):
    """Les équipes de /club/ : France (v2, v1f), Paris (p1) et jeunes (j1), lues dans les pages publiées ; aucun nom de
    joueur ; la page de l'espace club a la rubrique « Par équipe »."""
    _crypto()
    sortie, site = tmp_path / "sortie", tmp_path / "site"
    sortie.mkdir()
    france = {"club": {"numero": "08770250"}, "equipes": [
        {"id": "v2", "numero": 2, "championnat": "M", "nom_court": "Vaires 2", "division": "Départementale 2", "poule": "Poule 4"},
        {"id": "v1f", "numero": 1, "championnat": "F", "nom_court": "Vaires 1 F", "division": "D1 féminine", "poule": "Poule 3"}],
        "clubs": {"1": {"joueurs": [{"nom": "FICTIFNOM"}]}}}
    paris_ = {"equipes": [{"id": "v1", "numero": 1, "nom_court": "Vaires 1", "division": "Honneur", "poule": "Poule 1"}]}
    jeunes = {"equipes": [{"id": "v1", "numero": 1, "nom_court": "Vaires 1 · −15 ans", "age": "moins de 15 ans", "poule": "Poule 3"}]}
    for nom, d in (("vaires.html", france), ("paris_vaires.html", paris_), ("jeunes_vaires.html", jeunes)):
        (sortie / nom).write_text(f'<script id="donnees" type="application/json">{json.dumps(d)}</script>', encoding="utf-8")
    (sortie / "bilan.json").write_text(json.dumps({"debut": "2026-11-25T08:00", "fin": "2026-11-25T08:12", "pages": [
        {"nom": n, "resume": "ok", "fichiers": [f]} for n, f in (("adversaires", "vaires.html"), ("paris", "paris_vaires.html"), ("jeunes", "jeunes_vaires.html"))]}))
    publier.publier(sortie, site, "secret")
    eq = netlify.equipes_du_club(site, publier.cle("secret"))
    assert [(e["code"], e["seule"], e["competition"], e["espace"]) for e in eq] == [
        ("v2", "v2", "france", None), ("v1f", "v1f", "femmes", None), ("p1", "v1", "paris", "paris"), ("j1", "v1", "jeunes", "jeunes")]
    assert eq[3]["division"] == "moins de 15 ans" and "FICTIFNOM" not in json.dumps(eq)
    netlify.espace_club(site, tmp_path / "club", publier.cle("secret"), publier.cle("club"))
    page = (tmp_path / "club" / "index.html").read_text(encoding="utf-8")
    donnees = json.loads(page.split('<script id="donnees" type="application/json">')[1].split("</script>")[0])
    assert [e["code"] for e in donnees["equipes"]] == ["v2", "v1f", "p1", "j1"] and "FICTIFNOM" not in page
    assert "Par équipe" in page and "#equipe/" in page and '"#" + seuleCourante' in page
    # Paris (28/11) : les pages avec le sélecteur s'ouvrent sur l'équipe de Paris (#paris/seule/v2)
    assert '`${equipe.espace ? equipe.espace + "/" : ""}seule/${equipe.seule}`' in page and "PAGES_CHAMP" in page


V2_DIR = Path(netlify.__file__).with_name("v2")


@pytest.mark.skipif(not shutil.which("node"), reason="node absent")
def test_onglets_en_haut_de_la_fiche_d_equipe_v2():
    """v2 (26/11) : la fiche d'une équipe a ses onglets en haut (Résumé, pages du site sur cette équipe, Images) ;
    les images de l'équipe d'abord (adversaire, feuille, disponibles « image unique » avant les morceaux, brûlés)."""
    js = (V2_DIR / "commun.js").read_text(encoding="utf-8")
    bloc = js[js.index("  const PAGES_EQUIPE"):js.index("  /* ---------- Cadre de page")]
    image = lambda f, g: {"fichier": f, "type": "image", "groupe": g}
    club = {"documents": [{"fichier": "vaires.html", "type": "page"}, {"fichier": "effectif_vaires.html", "type": "page"},
                          image("effectif_disponibles_V2_1.png", "effectif"), image("effectif_disponibles_V2_complet.png", "effectif"),
                          image("effectif_brules_V2.png", "effectif"), image("rencontres_J5_V2.png", "rencontres"),
                          image("adversaires_V2.png", "adversaires"), image("adversaires_V1F.png", "adversaires"),
                          image("progression_V2.png", "progression"), image("paris_infographie.png", "paris"),
                          image("programme_equipes.png", "programme")],
            "ressources": [{"nom": "Championnat de Paris", "documents": [image("affiche-championnat-de-paris.jpg", None)]}]}
    essai = ('const RACINE = "../";\n' + bloc + f"const club = {json.dumps(club)};\n"
             "const voir = (t) => ongletsEquipe(t, club).map((o) => [o.id, o.nom, o.externe || (o.doc && o.doc.fichier) || null,"
             " o.images ? o.images.siennes.map((d) => d.fichier) : null]);\n"
             'console.log(JSON.stringify({ v2: voir({ comp: "france", numero: 2 }), f1: voir({ comp: "femmes", numero: 1 }),'
             ' p2: voir({ comp: "paris", numero: 2 }), j1: voir({ comp: "jeunes", numero: 1 }) }));')
    r = subprocess.run(["node", "-e", essai], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    o = json.loads(r.stdout)
    assert o["v2"] == [["resume", "Résumé", None, None], ["adversaire", "Adversaire", "vaires.html", None],
                       ["effectif", "Effectif", "effectif_vaires.html", None],
                       ["images", "Images (6)", None, ["adversaires_V2.png", "rencontres_J5_V2.png", "effectif_disponibles_V2_complet.png",
                                                       "effectif_disponibles_V2_1.png", "effectif_brules_V2.png", "progression_V2.png"]]]
    assert o["f1"][-1] == ["images", "Images (1)", None, ["adversaires_V1F.png"]]
    assert o["p2"] == [["resume", "Résumé", None, None], ["poule", "Poule et adversaires", "../../paris/#seule/v2", None],
                       ["dispos", "Disponibilités", "../../paris/#dispo", None],
                       ["images", "Images (2)", None, ["paris_infographie.png", "affiche-championnat-de-paris.jpg"]]]
    assert o["j1"] == [["resume", "Résumé", None, None], ["poule", "Poule et adversaires", "../../jeunes/#seule/v1", None],
                       ["images", "Images", None, []]]


def test_fiche_d_equipe_et_mon_equipe_sur_l_accueil_v2():
    equipe = (V2_DIR / "equipes" / "index.html").read_text(encoding="utf-8")
    assert 'class="segments equipe-nav"' in equipe and "V2.ongletsEquipe(t, club)" in equipe and 'seule/${encodeURIComponent' in equipe
    assert 'o.championnat ? o.championnat + "/" : ""' in equipe  # Paris, jeunes : #paris/seule/v2 (sélecteur de la page)
    assert "C'est mon équipe" in equipe and "V2.R.equipe" in equipe and "vignette" in equipe
    accueil = (V2_DIR / "index.html").read_text(encoding="utf-8")
    assert "m.innerHTML = heros + monEquipe" in accueil and "Tout sur ${esc(mienne.nom)}" in accueil
    assert "data-mienne" in accueil and "V2.ongletsEquipe(mienne, club)" in accueil
    assert ".equipe-nav { position: sticky" in (V2_DIR / "commun.css").read_text(encoding="utf-8")

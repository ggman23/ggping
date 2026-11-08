import json
import re

from ttvaires import netlify, publier, ressources


def test_ajouter_puis_publier_dans_l_espace_club(tmp_path):
    depot, club = tmp_path / "ressources", tmp_path / "club"
    pdf = tmp_path / "Guide du joueur.pdf"
    pdf.write_bytes(b"%PDF-1.7 contenu")
    page = tmp_path / "forums.html"
    page.write_text("<!doctype html><title>Forums</title>", encoding="utf-8")
    assert ressources.ajouter("Matériel", page, "club", titre="Forums", dossier=depot) == "forums.html"
    assert ressources.ajouter("Prépa mentale", pdf, "club", description="26 pages", dossier=depot) == "guide-du-joueur.pdf"
    # Chiffrés dans le dépôt (public) : le contenu n'y apparaît pas
    assert b"contenu" not in (depot / "guide-du-joueur.pdf.chiffre").read_bytes()
    rubriques = ressources.publier_dans(club, publier.cle("club"), depot)
    assert [(r["nom"], [(d["fichier"], d["type"], d["titre"], d["chemin"]) for d in r["documents"]]) for r in rubriques] == [
        ("Matériel", [("forums.html", "page", "Forums", "ressources/forums.html.chiffre")]),
        ("Prépa mentale", [("guide-du-joueur.pdf", "pdf", "Guide du joueur", "ressources/guide-du-joueur.pdf.chiffre")]),
    ]
    assert publier.dechiffrer((club / "ressources" / "guide-du-joueur.pdf.chiffre").read_bytes(),
                              publier.cle("club")) == b"%PDF-1.7 contenu"
    # Remplacer un document : même nom, une seule entrée
    ressources.ajouter("Prépa mentale", pdf, "club", titre="Nouveau titre", dossier=depot)
    assert [d["titre"] for d in ressources.lire(depot)["rubriques"][1]["documents"]] == ["Nouveau titre"]


def test_mot_de_passe_du_club_change_document_laisse_de_cote(tmp_path, capsys):
    depot = tmp_path / "ressources"
    f = tmp_path / "a.pdf"
    f.write_bytes(b"%PDF")
    ressources.ajouter("Prépa mentale", f, "ancien", dossier=depot)
    assert ressources.publier_dans(tmp_path / "club", publier.cle("nouveau"), depot) == []
    assert "ne s'ouvre pas avec le mot de passe du club" in capsys.readouterr().out


def test_type_non_pris_en_charge(tmp_path):
    f = tmp_path / "a.docx"
    f.write_bytes(b"x")
    try:
        ressources.ajouter("X", f, "club", dossier=tmp_path)
    except ValueError as e:
        assert "pages .html et PDF" in str(e)
    else:
        raise AssertionError("type refusé attendu")


def test_rubriques_dans_la_page_de_l_espace_club(tmp_path, monkeypatch):
    depot = tmp_path / "ressources"
    f = tmp_path / "guide.pdf"
    f.write_bytes(b"%PDF")
    ressources.ajouter("Prépa mentale", f, "club", dossier=depot)
    monkeypatch.setattr(ressources, "DOSSIER", depot)
    site = tmp_path / "site"
    site.mkdir()
    (site / "etat.json").write_text(json.dumps({"pages": {}, "images": {}, "archives": {}}), encoding="utf-8")
    netlify.espace_club(site, tmp_path / "club", publier.cle("site"), publier.cle("club"))
    html = (tmp_path / "club" / "index.html").read_text(encoding="utf-8")
    donnees = json.loads(re.search(r'<script id="donnees" type="application/json">(.*?)</script>', html, re.S)[1])
    assert [r["nom"] for r in donnees["ressources"]] == ["Prépa mentale"]
    assert (tmp_path / "club" / "ressources" / "guide.pdf.chiffre").exists()


def test_ressources_du_depot_lisibles():
    """La liste du dépôt est valide et chaque document inscrit est présent (chiffré)."""
    for r in ressources.lire()["rubriques"]:
        for d in r["documents"]:
            assert (ressources.DOSSIER / f"{d['fichier']}.chiffre").exists(), d["fichier"]

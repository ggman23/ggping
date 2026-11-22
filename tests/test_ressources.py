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
        assert "pages .html, PDF et images" in str(e)
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


def test_espace_protege_a_son_adresse(tmp_path):
    depot = tmp_path / "ressources"
    page = tmp_path / "roi.html"
    page.write_text("<!doctype html><title>Roi du lundi</title><p>Classement</p>", encoding="utf-8")
    assert ressources.ajouter_espace("/Lundi/", page, "club", titre="Le roi du lundi", dossier=depot) == "espace-lundi.html"
    assert b"Classement" not in (depot / "espace-lundi.html.chiffre").read_bytes()  # chiffrée dans le dépôt public
    site = tmp_path / "site"
    assert ressources.publier_espaces(site, publier.cle("club"), depot) == ["lundi"]
    html = (site / "lundi" / "index.html").read_text(encoding="utf-8")
    # Page de mot de passe : clé gardée comme celle de l'espace club (entrée une seule fois pour les deux)
    assert "Le roi du lundi" in html and 'STOCKAGE = "cvtt-vaires-cle-club"' in html and "Classement" not in html
    # Repère de l'application Android au début de la page (la page fait 2 Mo, la clé est à la fin)
    assert html.index('<meta name="cvtt-cle" content="cvtt-vaires-cle-club">') < 1000
    import base64
    chiffre = re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', html, re.S)[1].strip()
    assert b"Classement" in publier.dechiffrer(base64.b64decode(chiffre), publier.cle("club"))
    # Mot de passe du club changé : signalé, pas publié
    assert ressources.publier_espaces(tmp_path / "autre", publier.cle("nouveau"), depot) == []
    for reserve in ("club", "gg", "a/b"):
        try:
            ressources.ajouter_espace(reserve, page, "club", dossier=depot)
        except ValueError:
            continue
        raise AssertionError(f"/{reserve}/ refusé attendu")


def test_image_dans_une_rubrique(tmp_path):
    depot = tmp_path / "ressources"
    image = tmp_path / "Mémo.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n...")
    ressources.ajouter("Prépa mentale", image, "club", dossier=depot)
    (r,) = ressources.publier_dans(tmp_path / "club", publier.cle("club"), depot)
    assert [(d["fichier"], d["type"]) for d in r["documents"]] == [("memo.png", "image")]
    assert "dimensions" not in r["documents"][0]  # illisible pour Pillow : publiée telle quelle, sans aperçu


def test_espace_a_mot_de_passe_a_part(tmp_path, monkeypatch):
    """/lundi/ (page personnelle, 17/11) : mot de passe à part, secret MOT_DE_PASSE_LUNDI. Sans lui, pas
    publié ; la page déposée est scellée avec la clé publique (le mot de passe du club ne l'ouvre pas)."""
    import base64
    depot, page = tmp_path / "ressources", tmp_path / "roi.html"
    page.write_text("<!doctype html><title>Roi</title><p>Notes personnelles</p>", encoding="utf-8")
    ressources.ajouter_espace("lundi", page, "club", titre="Le roi du lundi", dossier=depot)
    ressources.regler_acces("lundi", "MOT_DE_PASSE_LUNDI", dossier=depot)
    # Sans le secret : rien n'est publié (pas même au mot de passe du club)
    monkeypatch.delenv("MOT_DE_PASSE_LUNDI", raising=False)
    assert ressources.publier_espaces(tmp_path / "s1", publier.cle("club"), depot) == []
    assert not (tmp_path / "s1" / "lundi" / "index.html").exists()
    # Avec le secret : la version au mot de passe du club est publiée avec le mot de passe à part
    monkeypatch.setenv("MOT_DE_PASSE_LUNDI", "secret-lundi")
    assert ressources.publier_espaces(tmp_path / "s2", publier.cle("club"), depot) == ["lundi"]
    html = (tmp_path / "s2" / "lundi" / "index.html").read_text(encoding="utf-8")
    chiffre = base64.b64decode(re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', html, re.S)[1].strip())
    assert b"Notes personnelles" in publier.dechiffrer(chiffre, publier.cle("secret-lundi"))
    try:
        publier.dechiffrer(chiffre, publier.cle("club"))
        raise AssertionError("le mot de passe du club ne doit pas ouvrir /lundi/")
    except AssertionError:
        raise
    except Exception:
        pass
    # Clé gardée à part, mais repère de l'application Android conservé (il commence par celui du club)
    assert 'STOCKAGE = "cvtt-vaires-cle-club-lundi"' in html and "cvtt-vaires-cle-club" in html[:1000]
    assert "ce n'est pas celui du club" in html and "entre le mot de passe du club" not in html
    publique = (tmp_path / "s2" / "lundi" / "cle-publique.txt").read_text().strip()
    assert publique == ressources.cle_publique("secret-lundi", "lundi")
    # Clé publique enregistrée : la version au mot de passe du club est scellée puis supprimée
    ressources.regler_cle_publique("lundi", publique, "club", dossier=depot)
    assert not (depot / "espace-lundi.html.chiffre").exists() and (depot / "espace-lundi.html.scelle").exists()
    assert b"Notes" not in (depot / "espace-lundi.html.scelle").read_bytes()
    # Nouvelle version déposée sans aucun mot de passe : scellée, publiée
    page.write_text("<!doctype html><title>Roi</title><p>Version 2</p>", encoding="utf-8")
    ressources.ajouter_espace("lundi", page, "", dossier=depot)
    assert ressources.publier_espaces(tmp_path / "s3", publier.cle("club"), depot) == ["lundi"]
    html = (tmp_path / "s3" / "lundi" / "index.html").read_text(encoding="utf-8")
    chiffre = base64.b64decode(re.search(r'<script id="chiffre" type="text/plain">(.*?)</script>', html, re.S)[1].strip())
    assert b"Version 2" in publier.dechiffrer(chiffre, publier.cle("secret-lundi"))
    assert ressources.lire(depot)["espaces"][0]["titre"] == "Le roi du lundi"  # titre gardé
    # Mot de passe changé : la page scellée ne s'ouvre plus, pas publiée (nouvelle clé publique quand même)
    monkeypatch.setenv("MOT_DE_PASSE_LUNDI", "autre")
    assert ressources.publier_espaces(tmp_path / "s4", publier.cle("club"), depot) == []
    assert (tmp_path / "s4" / "lundi" / "cle-publique.txt").read_text().strip() == ressources.cle_publique("autre", "lundi")


def test_grande_image_avec_un_apercu_allege(tmp_path):
    """Une grande image (affiche 8K) : l'original est publié pour « Télécharger », un aperçu JPEG de
    2 000 pixels au plus pour l'affichage ; une petite image n'en a pas ; remplacer retire l'ancien aperçu."""
    from PIL import Image

    depot, club, cle = tmp_path / "ressources", tmp_path / "club", publier.cle("club")
    grande, petite = tmp_path / "Affiche Paris.png", tmp_path / "memo.jpg"
    Image.new("RGBA", (1600, 3000), (200, 20, 30, 0)).save(grande)  # transparente : posée sur du blanc
    Image.new("RGB", (800, 1200), "navy").save(petite)
    assert ressources.ajouter("Championnat de Paris", grande, "club", dossier=depot) == "affiche-paris.png"
    ressources.ajouter("Championnat de Paris", petite, "club", dossier=depot)
    docs = ressources.lire(depot)["rubriques"][0]["documents"]
    assert [(d["fichier"], d["dimensions"], d.get("apercu")) for d in docs] == [
        ("affiche-paris.png", [1600, 3000], "affiche-paris.apercu.jpg"), ("memo.jpg", [800, 1200], None)]
    import io
    leger = Image.open(io.BytesIO(publier.dechiffrer((depot / "affiche-paris.apercu.jpg.chiffre").read_bytes(), cle)))
    assert (leger.format, leger.size, leger.getpixel((10, 10))) == ("JPEG", (1067, 2000), (255, 255, 255))
    rubriques = ressources.publier_dans(club, cle, depot)
    affiche = rubriques[0]["documents"][0]
    assert (affiche["chemin"], affiche["apercu"], affiche["type"]) == (
        "ressources/affiche-paris.png.chiffre", "ressources/affiche-paris.apercu.jpg.chiffre", "image")
    assert (club / "ressources" / "affiche-paris.apercu.jpg.chiffre").exists()
    assert "apercu" not in rubriques[0]["documents"][1]
    # Remplacée par une version plus petite : plus d'aperçu, l'ancien fichier d'aperçu est retiré
    Image.new("RGB", (1000, 1500), "red").save(grande)
    ressources.ajouter("Championnat de Paris", grande, "club", dossier=depot)
    assert not (depot / "affiche-paris.apercu.jpg.chiffre").exists()
    assert all("apercu" not in d for d in ressources.lire(depot)["rubriques"][0]["documents"])


def test_apercus_du_depot_lisibles():
    """Chaque aperçu inscrit dans la liste du dépôt est présent (chiffré)."""
    for r in ressources.lire()["rubriques"]:
        for d in r["documents"]:
            if d.get("apercu"):
                assert (ressources.DOSSIER / f"{d['apercu']}.chiffre").exists(), d["apercu"]

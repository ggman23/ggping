"""Application Android : clé de signature créée une fois, puis toujours la même."""

import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "android"))


def test_cle_creee_puis_reprise(tmp_path, monkeypatch):
    if not shutil.which("keytool"):
        pytest.skip("keytool absent")
    pytest.importorskip("cryptography")
    import cle_signature

    env = tmp_path / "env"
    monkeypatch.setenv("MOT_DE_PASSE_SITE", "secret")
    monkeypatch.setenv("GITHUB_ENV", str(env))
    monkeypatch.setattr(cle_signature, "cle_publiee", lambda depot: None)       # première construction
    monkeypatch.setattr("sys.argv", ["cle_signature.py", str(tmp_path / "a")])
    cle_signature.main()
    chiffre = (tmp_path / "a" / cle_signature.FICHIER).read_bytes()
    premiere = (tmp_path / "a" / "cle.p12").read_bytes()
    mdp = env.read_text().split("CLE_MDP=")[1].strip()
    assert mdp and mdp.encode() not in chiffre                                    # mot de passe chiffré

    monkeypatch.setattr(cle_signature, "cle_publiee", lambda depot: chiffre)    # constructions suivantes
    monkeypatch.setattr("sys.argv", ["cle_signature.py", str(tmp_path / "b")])
    cle_signature.main()
    assert (tmp_path / "b" / "cle.p12").read_bytes() == premiere                 # la même clé
    assert not (tmp_path / "b" / cle_signature.FICHIER).exists()                 # rien à republier

    monkeypatch.setenv("MOT_DE_PASSE_SITE", "autre")                            # mot de passe du site changé
    monkeypatch.setattr("sys.argv", ["cle_signature.py", str(tmp_path / "c")])
    with pytest.raises(SystemExit, match="ne se déchiffre pas"):
        cle_signature.main()
    assert not (tmp_path / "c" / cle_signature.FICHIER).exists()                 # l'ancienne n'est pas remplacée


def test_onglets_paris_et_jeunes_entre_club_et_lundi():
    """Huit onglets ; Paris et Jeunes entre Club et Lundi, sur les trois copies, avec le témoin du club
    (/paris/ et /jeunes/ gardent le mot de passe du club sous la même clé)."""
    import re
    from ttvaires import netlify

    java = (Path(__file__).resolve().parent.parent / "android/src/fr/cvtt/vaires/Principale.java").read_text(encoding="utf-8")
    assert re.findall(r'new Onglet\("(\w+)"', java) == ["maj", "club", "paris", "jeunes", "lundi", "indivs", "goatcounter", "umami", "v2"]
    assert 'new Onglet("paris", "Paris", "🗼", COPIES, NOMS_COPIES, "paris/", TEMOIN_CLUB,' in java
    assert 'new Onglet("jeunes", "Jeunes", "🧒", COPIES, NOMS_COPIES, "jeunes/", TEMOIN_CLUB,' in java
    assert "PARIS = 2, JEUNES = 3, LUNDI = 4, INDIVS = 5, GOATCOUNTER = 6, UMAMI = 7" in java
    assert netlify.PAGES_A_PART["paris.html"][0] == "paris" and netlify.PAGES_A_PART["jeunes.html"][0] == "jeunes"


def test_bouton_v2_pour_comparer_avec_le_site_actuel():
    """Bouton V2 / V1 en haut : la version 2 (/v2/, Cloudflare puis Netlify, avec le témoin du club), sans bouton
    en bas (elle a ses onglets), et retour à l'onglet d'avant ; la v2 garde le repère du club dans ses pages."""
    import re
    from ttvaires import v2

    java = (Path(__file__).resolve().parent.parent / "android/src/fr/cvtt/vaires/Principale.java").read_text(encoding="utf-8")
    assert re.findall(r'new Onglet\("(\w+)"', java)[-1] == "v2"
    assert ('new Onglet("v2", "Version 2", "✨", new String[]{CLOUDFLARE, NETLIFY}, new String[]{"Cloudflare", "Netlify"}, "v2/",\n'
            '                TEMOIN_CLUB,') in java
    assert "UMAMI = 7, V2 = 8;" in java and "if (i == V2) continue;" in java
    assert "bas.setVisibility(n == V2 ? View.GONE : View.VISIBLE)" in java
    assert 'choisir(indiceDe(reglages.getString(AVANT_V2, "club")))' in java and 'bascule.setText(dansV2 ? "V1" : "V2")' in java
    assert all('<meta name="cvtt-cle" content="cvtt-vaires-cle-club">' in p.read_text(encoding="utf-8")
               for p in v2.STATIQUE.rglob("index.html"))  # témoin trouvé par l'application

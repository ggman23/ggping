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

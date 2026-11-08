from datetime import date

from ttvaires import calendrier, fftt


def test_week_end_precedent():
    lundi = date(2026, 11, 9)
    assert calendrier.week_end_precedent(lundi) == (date(2026, 11, 6), date(2026, 11, 8))
    # Un dimanche, le week-end n'est pas fini : c'est le précédent
    assert calendrier.week_end_precedent(date(2026, 11, 8)) == (date(2026, 10, 30), date(2026, 11, 1))
    assert calendrier.week_end_precedent(date(2026, 11, 13)) == (date(2026, 11, 6), date(2026, 11, 8))


def test_rencontres_du_week_end(monkeypatch):
    rencontres = [{"date": d + "T20:45:00"} for d in ("2026-11-06", "2026-11-07", "2026-11-20")]
    monkeypatch.setattr(fftt, "id_interne_club", lambda client, numero, debut: 12770250)
    monkeypatch.setattr(fftt, "rencontres_club", lambda client, id_club, debut, fin, ttl: rencontres)
    assert len(calendrier.rencontres_du_week_end(None, date(2026, 11, 9))) == 2  # vendredi et samedi
    assert calendrier.rencontres_du_week_end(None, date(2026, 11, 16)) == []  # week-end sans championnat


def test_sortie_pour_le_workflow(monkeypatch, tmp_path):
    sortie = tmp_path / "sortie"
    monkeypatch.setenv("GITHUB_OUTPUT", str(sortie))
    monkeypatch.setattr(calendrier.compte_fftt, "connecter", lambda client, demander=None: None)
    monkeypatch.setattr(calendrier, "rencontres_du_week_end", lambda client, jour: [])
    calendrier.main(["--date", "2026-11-16"])
    monkeypatch.setattr(calendrier, "rencontres_du_week_end", lambda client, jour: [{"date": "2026-11-20"}])
    calendrier.main(["--date", "2026-11-23"])
    assert sortie.read_text() == "continuer=false\ncontinuer=true\n"

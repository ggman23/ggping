"""Programme des équipes de Vaires en une image au format téléphone."""

from datetime import date

from ttvaires import jeunes, paris, programme


def _renc(journee, jour, adv, dom, heure="20:45", score=None):
    return {"journee": journee, "date": jour, "heure": heure, "vaires_domicile": dom, "score": score,
            "adversaire": {"libelle": adv} if adv else None}


FRANCE = {"genere_le": "2026-11-21T09:25", "equipes": [
    {"nom_court": "Vaires 4", "numero": 4, "championnat": "M", "division": "Départementale 2", "rencontres": [
        _renc(5, "2026-11-20", "CHELLES TT 9", False, score=[17, 25]),
        _renc(6, "2026-12-04", "CTT MONTHYON 2", True), _renc(7, "2026-12-11", "CHAMPS/M ASTT 1", False),
        _renc(1, "2027-01-15", "PLUS TARD 1", True)]},
    {"nom_court": "Vaires 1 F", "numero": 1, "championnat": "F", "division": "D1 Championnat Feminin 77/94", "rencontres": [
        _renc(6, "2026-12-05", None, False, heure="15:00"), _renc(7, "2026-12-12", "ST MAURICE TT 1", False, heure="15:00")]},
    {"nom_court": "Vaires 1", "numero": 1, "championnat": "M", "division": "Pré-régionale", "rencontres": [
        _renc(6, "2026-12-04", "COMBS SENART TT 7", True)]},
]}


def test_rencontres_du_programme():
    """Les 2 prochaines rencontres de chaque équipe de France (pas les jouées), puis Paris et jeunes sur la même
    période ; triées par date, puis France (hommes, femmes), Paris, jeunes."""
    lignes = programme.rencontres(FRANCE, paris.donnees(), jeunes.donnees(), date(2026, 11, 22))
    resume = [(l["date"], l["competition"], l["equipe"], l["adversaire"], l["domicile"]) for l in lignes]
    assert resume[:5] == [
        ("2026-11-27", "Paris", "Vaires 1", "VILLEMOMBLE SP 2", True), ("2026-11-27", "Paris", "Vaires 2", "VILLEMOMBLE SP 3", False),
        ("2026-11-27", "Paris", "Vaires 3", "MONTHYON CTT 1", False), ("2026-11-27", "Jeunes", "Vaires 1", "CTT MONTHYON 1", True),
        ("2026-11-27", "Jeunes", "Vaires 2", "CTT MONTHYON 2", True)]
    assert resume[5:] == [
        ("2026-12-04", "France", "Vaires 1", "COMBS SENART TT 7", True), ("2026-12-04", "France", "Vaires 4", "CTT MONTHYON 2", True),
        ("2026-12-05", "France", "Vaires 1 F", None, False), ("2026-12-11", "France", "Vaires 4", "CHAMPS/M ASTT 1", False),
        ("2026-12-12", "France", "Vaires 1 F", "ST MAURICE TT 1", False)]
    assert [l["detail"] for l in lignes if l["equipe"] in ("Vaires 4", "Vaires 1 F")][:2] == ["France · D2", "France féminin · D1"]
    assert lignes[1]["detail"] == "Paris · Promotion d'Honneur" and lignes[4]["detail"] == "Jeunes · −13 ans"
    assert lignes[4]["a_confirmer"] and not lignes[3]["a_confirmer"]
    # Hors période (après le 12/12), une équipe de Paris montre quand même sa prochaine rencontre
    tard = programme.rencontres(FRANCE, paris.donnees(), {"equipes": []}, date(2026, 11, 28))
    assert [l["journee"] for l in tard if l["competition"] == "Paris"] == [2, 2, 2]


def test_divisions_courtes():
    assert [programme.division_courte(d) for d in ("Départementale 2", "Régionale 3", "Pré-régionale",
                                                   "D1 Championnat Feminin 77/94")] == ["D2", "R3", "PR", "D1"]


def test_image_au_format_telephone(tmp_path):
    (sortie,) = programme.image_programme(FRANCE, tmp_path, aujourdhui=date(2026, 11, 22))
    from PIL import Image
    chemin, titre = sortie
    img = Image.open(chemin)
    assert titre == "Programme des équipes" and chemin.name == "programme_equipes.png"
    assert img.width == 1080 and img.height > img.width  # portrait : une colonne de cartes
    # Couleurs : vert pour le domicile, orange pour l'extérieur (le fond des cartes)
    couleurs = {c for _, c in img.convert("RGB").getcolors(1 << 20)}
    assert (227, 244, 234) in couleurs and (251, 238, 221) in couleurs
    # Pictogrammes : carte tricolore (bleu, rouge), tête de femme (rose), enfant (violet), tour Eiffel
    assert {programme.BLEU, programme.ROUGE_FR, programme.ROSE, programme.VIOLET, programme.TOUR} <= couleurs
    assert {l["icone"] for l in programme.rencontres(FRANCE, paris.donnees(), jeunes.donnees(), date(2026, 11, 22))} == {
        "france", "femmes", "paris", "jeunes"}
    assert programme.image_programme({"equipes": []}, tmp_path, aujourdhui=date(2027, 7, 1),
                                     paris_={"equipes": []}, jeunes_={"equipes": []}) == []

"""Tests des lecteurs de pages pingpocket, sur des extraits HTML fictifs de même structure."""

from ttvaires.pingpocket import (
    categorie_courte, date_courte, date_longue, libelle_division, lire_equipes_club, lire_feuille,
    lire_historique, lire_liste_licencies, lire_poule, lire_salle, resume_historique, separer_nom,
)

EQUIPES = """
<div class="current" data-title="Equipes">
<div class="info"><p><span>CLUB TEST</span> - n° <span>08779999</span></p></div>
<h2>Equipes féminines</h2><ul class="rounded">
<li class="arrow"><a href="/app/fftt/clubs/08779999/equipes/1/championnats/feminin?phase=1" class="item-container">
<div><div class="labels"><p>D1 Championnat Feminin 77/94 Poule 3</p></div></div><small class="counter">1</small></a></li></ul>
<h2>Equipes masculines</h2><ul class="rounded">
<li class="arrow"><a href="/app/fftt/clubs/08779999/equipes/4/championnats/masculin?phase=1" class="item-container">
<div><div class="labels"><p>L08_R1   Poule 1</p></div></div><small class="counter">4</small></a></li>
<li class="arrow"><a href="/app/fftt/clubs/08779999/equipes/12/championnats/masculin?phase=1" class="item-container">
<div><div class="labels"><p>DEP 2  Poule 5</p></div></div><small class="counter">12</small></a></li></ul>
</div>"""

POULE = """
<div data-title="Poule 5">
<ul class="rounded pool-ranking">
<li><span>Poule 5</span></li>
<li class="arrow"><a href="/x/equipes/A%201/vue-d-ensemble?COMPETITION_TEAM_NUMBER_1=1&amp;COMPETITION_CLUB_ID1=08770001">
<span>1.</span><span>ALPHA 1</span></a><span class="ppk-button" data-values=" 3;1;1 0 0;27 15">3</span></li>
<li class="arrow"><a href="/x/equipes/B%2012/vue-d-ensemble?COMPETITION_TEAM_NUMBER_1=12&amp;COMPETITION_CLUB_ID1=08779999">
<span style="visibility:hidden;">.</span><span>BETA TT 12</span></a><span class="ppk-button" data-values=" 3;1;1 0 0;24 18">3</span></li>
<li class="arrow"><a href="/x/equipes/V%203/vue-d-ensemble?COMPETITION_TEAM_NUMBER_1=3&amp;COMPETITION_CLUB_ID1=08770250">
<span>3.</span><span>VAIRES CVTT 3</span></a><span class="ppk-button" data-values=" 1;1;0 0 1;15 27">1</span></li>
</ul>
<div class="division-grid championshipDays">
<ul><li><span>Journée 1</span><span>Sep 25, 2026</span></li>
<li class="score arrow"><a href="/x/journee/1/rencontre/11?COMPETITION_CLUB_ID1=08770001&amp;COMPETITION_CLUB_ID2=08770250">
<div class="result"><span>ALPHA 1</span><div><span>27</span><span>-</span><span>15</span></div><span>VAIRES CVTT 3</span></div></a></li>
<li class="score"><div class="result"><span>BETA TT 12</span><div><span></span><span>-</span><span></span></div><span></span></div></li>
</ul><ul><li><span>Journée 2</span><span>Oct 2, 2026</span></li>
<li class="score arrow"><a href="/x/journee/2/rencontre/12?COMPETITION_CLUB_ID1=08770250&amp;COMPETITION_CLUB_ID2=08779999">
<div class="result"><span>VAIRES CVTT 3</span><span>03 Oct</span><span>BETA TT 12</span></div></a></li>
</ul></div></div>"""

FEUILLE = """
<div data-title="A vs B"><div class="division-grid">
<ul class="rounded">
<li class="arrow"><a href="/x"><div class="labels"><p>ALPHA 1</p></div><p class="rich-button">3388</p></a></li>
<li class="arrow"><a href="/app/fftt/licencies/7700001?CLUB_ID=08770001"><div class="icon"><i class="fa fa-male"></i></div>
<div class="labels"><p>DUPONT Jean Pierre</p></div><p class="rich-button">916</p></a></li>
<li class="arrow"><a href="/app/fftt/clubs/08770001"><div class="labels"><p>CLUB ALPHA</p></div></a></li>
</ul>
<ul class="rounded">
<li class="arrow"><a href="/x"><div class="labels"><p>VAIRES CVTT 3</p></div></a></li>
<li class="arrow"><a href="/app/fftt/licencies/7700002?CLUB_ID=08770250"><div class="icon"><i class="fa fa-female"></i></div>
<div class="labels"><p>DE LA TOUR Marie</p></div><p class="rich-button">768</p></a></li>
<li class="arrow"><a href="/app/fftt/clubs/08770250"><div class="labels"><p>CVTT VAIRES</p></div></a></li>
</ul></div></div>"""

LISTE = """
<div data-title="Club"><ul class="edgetoedge">
<li class="sep"><p><span>Vétéran 45</span><span></span></p>
<li class="arrow"><a href="/app/fftt/licencies/7700001?CLUB_ID=1"><div class="icon"><i class="fa fa-male"></i></div>
<div class="labels"><p>DUPONT Jean</p></div><small class="counter">1014</small></a></li>
</li><li class="sep"><p><span>Minime 1</span><span></span></p>
<li class="arrow"><a href="/app/fftt/licencies/7700003?CLUB_ID=1"><div class="icon"><i class="fa fa-female"></i></div>
<div class="labels"><p>MARTIN Léa</p></div><small class="counter">L</small></a></li>
</li></ul></div>"""

SALLE = """
<div data-title="Club"><h2>Salle</h2><ul class="rounded">
<li><p>Gymnase Test<br/>Avenue Anatole France <br/>77270 VILLEPARISIS </p></li>
<li class="forward"><a href="https://maps.google.fr/maps?hl=fr&amp;q=48.9%2C2.6">Carte</a></li></ul></div>"""

HISTORIQUE = """data: [
{ x: Date.UTC(2014, 6, 1) , y: 1530.0 , nationalRanking: null },
{ x: Date.UTC(2015, 0, 1) , y: 1480.0 , nationalRanking: null },
{ x: Date.UTC(2026, 6, 1) , y: 1014.0 , nationalRanking: null },
{ x: Date.UTC(2026, 8, 1) , y: 1030.0 , nationalRanking: null },
]"""


def test_utilitaires():
    assert date_longue("Sep 25, 2026") == "2026-09-25"
    assert date_courte("02 Oct", "2026-10-02") == "2026-10-02"
    assert date_courte("05 Jan", "2026-12-18") == "2027-01-05"
    assert separer_nom("SOARES GARCIA Ricardo Andre") == ("SOARES GARCIA", "Ricardo Andre")
    assert categorie_courte("Vétéran 45") == "V45"
    assert categorie_courte("Senior") == "S"
    assert libelle_division("L08_R2") == "Régionale 2"
    assert libelle_division("DEP 3") == "Départementale 3"
    assert libelle_division("FED_Nationale 2") == "Nationale 2"


def test_lire_equipes_club():
    nom, equipes = lire_equipes_club(EQUIPES)
    assert nom == "CLUB TEST"
    assert [(e["numero"], e["championnat"], e["division"], e["poule"]) for e in equipes] == [
        (1, "F", "D1 Championnat Feminin 77/94", "Poule 3"),
        (4, "M", "Régionale 1", "Poule 1"),
        (12, "M", "Départementale 2", "Poule 5"),
    ]


def test_lire_poule():
    poule = lire_poule(POULE)
    c = poule["classement"]
    assert [(x["rang"], x["libelle"], x["club"], x["numero"], x["points"]) for x in c] == [
        (1, "ALPHA 1", "08770001", 1, 3), (1, "BETA TT 12", "08779999", 12, 3), (3, "VAIRES CVTT 3", "08770250", 3, 1)]
    assert (c[0]["v"], c[0]["n"], c[0]["d"], c[0]["pg"], c[0]["pp"]) == (1, 0, 0, 27, 15)
    r1, exempt, r2 = poule["rencontres"]
    assert r1["score"] == [27, 15] and r1["club_ext"] == "08770250" and r1["date_journee"] == "2026-09-25"
    assert exempt["domicile"] == "BETA TT 12" and exempt["exterieur"] is None and exempt["lien"] is None
    assert r2["score"] is None and r2["date_prevue"] == "2026-10-03" and r2["journee"] == 2


def test_lire_feuille():
    dom, ext = lire_feuille(FEUILLE)
    assert dom["equipe"] == "ALPHA 1" and dom["club"] == "08770001"
    assert dom["joueurs"] == [{"licence": "7700001", "nom": "DUPONT", "prenom": "Jean Pierre", "points": 916, "sexe": "M"}]
    assert ext["joueurs"][0]["nom"] == "DE LA TOUR" and ext["joueurs"][0]["sexe"] == "F"


def test_lire_liste_licencies():
    sections = lire_liste_licencies(LISTE)
    assert [s[0] for s in sections] == ["Vétéran 45", "Minime 1"]
    assert sections[0][1][0]["compteur"] == "1014"
    assert sections[1][1][0]["compteur"] == "L" and sections[1][1][0]["sexe"] == "F"


def test_lire_salle():
    assert lire_salle(SALLE) == {"nom": "Gymnase Test", "adresse": "Avenue Anatole France", "cp": "77270",
                                 "ville": "VILLEPARISIS", "carte": "https://maps.google.fr/maps?hl=fr&q=48.9%2C2.6"}


def test_historique_meilleur_classement():
    points = lire_historique(HISTORIQUE)
    assert points[0] == (2014, 7, 1530)
    officiels, meilleur = resume_historique(points)
    assert officiels == 1014  # début de la phase en cours (juillet 2026)
    assert meilleur == {"points": 1530, "annee": "2014"}

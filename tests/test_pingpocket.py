"""Tests des compléments pingpocket (effectifs, salles, historiques), sur des extraits HTML fictifs."""

from ttvaires.pingpocket import (
    categorie_courte, effectif, lire_historique, lire_liste_licencies, lire_salle, resume_historique, separer_nom,
)

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
    assert separer_nom("SOARES GARCIA Ricardo Andre") == ("SOARES GARCIA", "Ricardo Andre")
    assert categorie_courte("Vétéran 45") == "V45"
    assert categorie_courte("Senior") == "S"
    assert categorie_courte("Sénior") == "S"


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


def test_effectif_ecarte_les_loisirs_et_repere_les_non_renouveles():
    etat = """<div data-title="Club"><ul class="edgetoedge">
<li class="sep"><p><span>Licences à jour</span></p>
<li class="arrow"><a href="/app/fftt/licencies/7700001?CLUB_ID=1"><div class="labels"><p>DUPONT Jean</p></div></a></li>
</li><li class="sep"><p><span>Licences non renouvelées</span></p>
<li class="arrow"><a href="/app/fftt/licencies/7700009?CLUB_ID=1"><div class="labels"><p>ANCIEN Paul</p></div></a></li>
</li></ul></div>"""
    liste = LISTE.replace("</ul>", '<li class="arrow"><a href="/app/fftt/licencies/7700009?CLUB_ID=1"><div class="labels">'
                                   '<p>ANCIEN Paul</p></div><small class="counter">640</small></a></li></ul>')
    pages = {"c": liste, "r": liste, "e": etat}
    joueurs = {j["id"]: j for j in effectif(pages, {"categories": "c", "classements": "r", "etat": "e"})}
    assert set(joueurs) == {"7700001", "7700009"}        # 7700003 (licence loisir « L ») écarté
    assert joueurs["7700001"]["renouvele"] and not joueurs["7700009"]["renouvele"]
    assert joueurs["7700001"]["categorie"] == "V45" and joueurs["7700001"]["points_mensuels"] == 1014

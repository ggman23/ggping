"""Calcul des points virtuels et synthèse par journée (cas réel de la J1 de Vaires 3, noms fictifs)."""

from ttvaires.pingpocket import lire_parties
from ttvaires.resultats import points_partie, synthese


def test_bareme_fftt():
    assert points_partie(780, 752, True) == 5.5     # victoire normale, écart 28
    assert points_partie(780, 1014, True) == 17     # victoire anormale, écart 234
    assert points_partie(961, 1014, False) == -4    # défaite normale, écart 53
    assert points_partie(768, 706, False) == -7     # défaite anormale, écart 62
    assert points_partie(500, 916, False) == 0      # défaite normale, écart 416
    assert points_partie(1410, 800, True) == 0      # victoire normale, écart 610
    assert points_partie(800, 1410, True) == 40     # victoire anormale, écart 610
    assert points_partie(900, 900, False) == -5     # même nombre de points


def _partie(joueur, points, adversaire, points_adv, victoire, journee=1, equipe="VAIRES 3", ordre=2):
    return {"journee": journee, "date": "2026-09-25", "equipe": equipe, "ordre": ordre, "adversaires": "CLUB X 2",
            "licence": joueur, "joueur": joueur, "points": points, "adversaire": adversaire,
            "points_adv": points_adv, "ecart": points_adv - points, "victoire": victoire,
            "gain": points_partie(points, points_adv, victoire)}


def test_synthese_journee_et_total():
    # Delobelle : 3 victoires (écarts -28, -74, +234) = +27,5 (valeurs de la feuille de match réelle).
    parties = [_partie("DELOBELLE", 780, "A", 752, True), _partie("DELOBELLE", 780, "B", 706, True),
               _partie("DELOBELLE", 780, "C", 1014, True),
               _partie("RIGUET", 500, "E", 916, False), _partie("RIGUET", 500, "B", 706, True),
               _partie("RIGUET", 500, "C", 1014, False),
               _partie("DELOBELLE", 807, "D", 900, False, journee=2)]
    lignes, cumuls = synthese(parties)
    j1 = {l["joueur"]: l for l in lignes if l["journee"] == 1}
    assert (j1["DELOBELLE"]["delta"], j1["DELOBELLE"]["v"], j1["DELOBELLE"]["matchs"]) == (27.5, 3, 3)
    assert j1["DELOBELLE"]["meilleure"] == 234 and j1["DELOBELLE"]["apres"] == 807.5
    assert (j1["RIGUET"]["delta"], j1["RIGUET"]["meilleure"]) == (17, 206)
    j2 = next(l for l in lignes if l["journee"] == 2)
    assert j2["delta"] == -4 and j2["meilleure"] is None and j2["total"] == 23.5
    c = next(c for c in cumuls if c["joueur"] == "DELOBELLE")
    assert c["journees"] == {1: 27.5, 2: -4} and c["total"] == 23.5 and (c["v"], c["matchs"]) == (3, 4)


PARTIES = """
<div data-title="A vs B">
<ul class="rounded divisionIndividualRoundMatchesPanel"><li><a href="/x/equipes/A"><span>ALPHA 1</span></a></li></ul>
<div class="division-grid"></div>
<ul class="rounded divisionIndividualRoundMatchesPanel">
<li><a href="/app/fftt/licencies/1"><span class="pos">A Un</span></a><p>2</p><p>1</p>
<a href="/app/fftt/licencies/2"><span class="neg">B Deux</span></a></li>
<li><a href="/app/fftt/licencies/3"><span class="neg">C Trois</span></a><p>1</p><p>2</p>
<a href="/app/fftt/licencies/4"><span class="pos">D Quatre</span></a></li>
<li><p class="labels-fragment"><span class="pos">A Un et C Trois</span></p><p>2</p><p>1</p>
<p class="labels-fragment"><span class="neg">B Deux et D Quatre</span></p></li>
</ul></div>"""


def test_lire_parties_ignore_les_doubles():
    assert lire_parties(PARTIES) == [{"a": "1", "b": "2", "gagnant": "1"}, {"a": "3", "b": "4", "gagnant": "4"}]

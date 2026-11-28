"""Championnat des jeunes par équipes 77, 2026-2027 : les deux équipes de Vaires, leurs poules et leur calendrier.

Recopiés des captures de l'application de la FFTT envoyées le 18/11/2026 : Vaires 1 en moins de 15 ans
(poule « A (C) », poule 3, avec les dates), Vaires 2 en moins de 13 ans (poule « A (A) », poule 1, 7 équipes :
une exempte à chaque journée ; pas encore de dates dans l'application : celles du calendrier du comité,
les mêmes vendredis que le championnat de Paris, voir calendrier.py). Pas d'équipe de Vaires en moins de 11 ans.

Qui peut jouer : les joueurs de la catégorie d'âge de l'équipe et des catégories plus jeunes. Les catégories
de la FFTT vont de deux ans en deux ans (âge atteint dans l'année où commence la saison) : poussins moins de
9 ans, benjamins 9-10 ans, minimes 11-12 ans, cadets 13-14 ans. Moins de 13 ans : minimes, benjamins,
poussins ; moins de 15 ans : cadets aussi (un minime 1 peut jouer en moins de 13 et en moins de 15 ans). Les licences loisir sont gardées : les clubs les
changeront pour faire jouer ces jeunes.

Page /jeunes/ (mot de passe du club), faite par l'étape adversaires de la mise à jour (jeunes_vaires.html,
publiée comme /paris/), avec le gabarit de /paris/ (gabarit_championnat.html). Les numéros FFTT des clubs
adverses qui ne sont pas écrits ici sont retrouvés par leur nom dans les rencontres du comité (API FFTT,
trouver_clubs) ; le journal les écrit.
"""

import json
import re
import unicodedata

from . import paris

SAISON = "2026-2027"
SOURCE = ("Poules du championnat des jeunes par équipes 2026-2027 (application de la FFTT, 18/11/2026) ; dates du "
          "calendrier du comité 77")
JOURNEES = ["2026-11-27", "2027-01-08", "2027-02-05", "2027-03-19", "2027-04-02", "2027-05-14", "2027-06-04"]
CLUB_VAIRES = paris.CLUB_VAIRES

# Catégories d'âge (code court de pingpocket : P, B1, B2, M1, M2, C1, C2...) : chaque équipe accueille sa
# catégorie et les plus jeunes. « Moins de 13 ans » = minimes (11-12 ans) et plus jeunes.
CATEGORIES = {"P": "poussins", "B": "benjamins", "M": "minimes", "C": "cadets"}
AGES = {"moins de 11 ans": ["P", "B"], "moins de 13 ans": ["P", "B", "M"], "moins de 15 ans": ["P", "B", "M", "C"]}

# Clubs des deux poules : nom des équipes (sans leur numéro) -> numéro FFTT (None : retrouvé par son nom)
CLUBS = {
    "VAIRES CVTT": CLUB_VAIRES, "CTT MONTHYON": "08771201", "DAMMARTIN CTT": "08770937",
    "COULOMMIERS TT": None, "ROISSY TT US": None, "MEAUX TT CS": None, "FERTOIS TT": None, "SERRIS ATT": None,
    "VILLEPARISIS TT": None, "ST THIBAULT": None, "APOZOIR": None,
}

# Rencontres journée par journée (le premier nommé reçoit ; None : l'équipe est exempte)
EQUIPES = [
    {"cle": "v1", "nom": "Vaires 1", "libelle": "VAIRES CVTT 1", "age": "moins de 15 ans", "poule": "Poule 3",
     "dates_application": True, "journees": [
        [("VAIRES CVTT 1", "CTT MONTHYON 1"), ("COULOMMIERS TT 1", "ROISSY TT US 3"), ("MEAUX TT CS 1", "FERTOIS TT 1"),
         ("SERRIS ATT 2", "DAMMARTIN CTT 1")],
        [("ROISSY TT US 3", "VAIRES CVTT 1"), ("FERTOIS TT 1", "COULOMMIERS TT 1"), ("DAMMARTIN CTT 1", "MEAUX TT CS 1"),
         ("CTT MONTHYON 1", "SERRIS ATT 2")],
        [("VAIRES CVTT 1", "FERTOIS TT 1"), ("COULOMMIERS TT 1", "DAMMARTIN CTT 1"), ("MEAUX TT CS 1", "SERRIS ATT 2"),
         ("CTT MONTHYON 1", "ROISSY TT US 3")],
        [("DAMMARTIN CTT 1", "VAIRES CVTT 1"), ("SERRIS ATT 2", "COULOMMIERS TT 1"), ("MEAUX TT CS 1", "CTT MONTHYON 1"),
         ("FERTOIS TT 1", "ROISSY TT US 3")],
        [("VAIRES CVTT 1", "SERRIS ATT 2"), ("COULOMMIERS TT 1", "MEAUX TT CS 1"), ("ROISSY TT US 3", "DAMMARTIN CTT 1"),
         ("CTT MONTHYON 1", "FERTOIS TT 1")],
        [("MEAUX TT CS 1", "VAIRES CVTT 1"), ("COULOMMIERS TT 1", "CTT MONTHYON 1"), ("SERRIS ATT 2", "ROISSY TT US 3"),
         ("DAMMARTIN CTT 1", "FERTOIS TT 1")],
        [("VAIRES CVTT 1", "COULOMMIERS TT 1"), ("ROISSY TT US 3", "MEAUX TT CS 1"), ("FERTOIS TT 1", "SERRIS ATT 2"),
         ("CTT MONTHYON 1", "DAMMARTIN CTT 1")],
    ]},
    {"cle": "v2", "nom": "Vaires 2", "libelle": "VAIRES CVTT 2", "age": "moins de 13 ans", "poule": "Poule 1",
     "dates_application": False, "journees": [
        [("VAIRES CVTT 2", "CTT MONTHYON 2"), ("SERRIS ATT 3", None), ("VILLEPARISIS TT 2", "ST THIBAULT 2"),
         ("ROISSY TT US 4", "APOZOIR 2")],
        [(None, "VAIRES CVTT 2"), ("ST THIBAULT 2", "SERRIS ATT 3"), ("APOZOIR 2", "VILLEPARISIS TT 2"),
         ("CTT MONTHYON 2", "ROISSY TT US 4")],
        [("VAIRES CVTT 2", "ST THIBAULT 2"), ("SERRIS ATT 3", "APOZOIR 2"), ("VILLEPARISIS TT 2", "ROISSY TT US 4"),
         ("CTT MONTHYON 2", None)],
        [("APOZOIR 2", "VAIRES CVTT 2"), ("ROISSY TT US 4", "SERRIS ATT 3"), ("VILLEPARISIS TT 2", "CTT MONTHYON 2"),
         ("ST THIBAULT 2", None)],
        [("VAIRES CVTT 2", "ROISSY TT US 4"), ("SERRIS ATT 3", "VILLEPARISIS TT 2"), (None, "APOZOIR 2"),
         ("CTT MONTHYON 2", "ST THIBAULT 2")],
        [("VILLEPARISIS TT 2", "VAIRES CVTT 2"), ("SERRIS ATT 3", "CTT MONTHYON 2"), ("ROISSY TT US 4", None),
         ("APOZOIR 2", "ST THIBAULT 2")],
        [("VAIRES CVTT 2", "SERRIS ATT 3"), (None, "VILLEPARISIS TT 2"), ("ST THIBAULT 2", "ROISSY TT US 4"),
         ("CTT MONTHYON 2", "APOZOIR 2")],
    ]},
]


def club_et_numero(equipe):
    """« SERRIS ATT 3 » -> (« SERRIS ATT », 3)."""
    m = re.match(r"(.*?)\s+(\d+)$", equipe)
    return (m[1], int(m[2])) if m else (equipe, None)


def equipes_de_la_poule(e):
    """Noms des équipes d'une poule, dans l'ordre où elles apparaissent."""
    vues = []
    for journee in e["journees"]:
        for paire in journee:
            for nom in paire:
                if nom and nom not in vues:
                    vues.append(nom)
    return vues


def peut_jouer(categorie, age):
    """Le joueur (code de catégorie : P, B1, M2...) a-t-il l'âge pour une équipe « moins de N ans » ?"""
    m = re.fullmatch(r"([A-Z])\d*", (categorie or "").replace(" ", ""))
    return bool(m) and m[1] in AGES[age]


def jeune(joueur):
    """Joueur gardé pour la page : un jeune d'au moins une des catégories des équipes (licences loisir comprises)."""
    return peut_jouer(joueur.get("categorie"), "moins de 15 ans")


def _rencontres(e, numeros):
    res = []
    for j, journee in enumerate(e["journees"], 1):
        for dom, ext in journee:
            if e["libelle"] not in (dom, ext):
                continue
            adv = ext if dom == e["libelle"] else dom
            r = {"journee": j, "date": JOURNEES[j - 1], "date_reelle": None, "heure": None,
                 "date_a_confirmer": not e["dates_application"],
                 "domicile": {"libelle": dom, "club": numeros.get(club_et_numero(dom)[0]) if dom else None},
                 "exterieur": {"libelle": ext, "club": numeros.get(club_et_numero(ext)[0]) if ext else None},
                 "vaires_domicile": dom == e["libelle"], "score": None, "adversaire": None}
            if adv:
                club, numero = club_et_numero(adv)
                r["adversaire"] = {"club": numeros.get(club) or club, "libelle": adv, "numero": numero}
            res.append(r)
    return res


def donnees(adversaires=None, numeros=None):
    """Données de la page /jeunes/, au format de /paris/ (gabarit_championnat.html). `numeros` : numéros FFTT des
    clubs (CLUBS complété par trouver_clubs) ; `adversaires` : adversaires.recuperer_jeunes."""
    adv = adversaires or {}
    numeros = {**CLUBS, **(numeros or adv.get("numeros") or {})}
    equipes = []
    for e in EQUIPES:
        noms = equipes_de_la_poule(e)
        equipes.append({
            "id": e["cle"], "libelle": e["libelle"], "nom_court": f"{e['nom']} · −{e['age'].split()[2]} ans",
            "numero": club_et_numero(e["libelle"])[1], "championnat": "M", "division": e["age"].capitalize(),
            "code": f"−{e['age'].split()[2]}", "poule": e["poule"], "jour": None, "categories": AGES[e["age"]],
            "age": e["age"], "rencontres": _rencontres(e, numeros),
            "classement": [{"rang": None, "libelle": n, "club": numeros.get(club_et_numero(n)[0]), "dep": None,
                            "points": None, "joues": None, "v": None, "n": None, "d": None} for n in noms]})
    club = adv.get("club") or {}
    sources = adv.get("sources", {})
    return {"espace": "jeunes", "titre": "championnat des jeunes", "competition": "championnat des jeunes par équipes 77",
            "saison": SAISON, "source": SOURCE, "phase": adv.get("phase"),
            "categories": CATEGORIES, "avec_loisir": True,
            "journees": [{"numero": i, "date": d} for i, d in enumerate(JOURNEES, 1)],
            "club": {"numero": CLUB_VAIRES, "nom": "CVTT Vaires", "salle": club.get("salle")},
            "equipes": equipes, "clubs": paris.clubs_adverses(adv), "genere_le": adv.get("genere_le"),
            "debut_forme": (sources.get("forme") or {}).get("debut"), "historiques_restants": sources.get("historiques_restants", 0)}


def page(adversaires=None, resultats=None):
    """Page /jeunes/ (HTML) : le gabarit du championnat de Paris avec les données des jeunes ; `resultats` (équipes
    de l'API) : scores et classement des poules (paris.avec_resultats)."""
    js = json.dumps(paris.avec_resultats(donnees(adversaires), resultats), ensure_ascii=False).replace("<", "\\u003c")
    return paris.GABARIT.read_text(encoding="utf-8").replace("__DONNEES_JSON__", js).encode("utf-8")


# ---------------------------------------------------------------------------
# Numéros FFTT des clubs, retrouvés par leur nom
# ---------------------------------------------------------------------------

GENERIQUES = {"TT", "CTT", "CVTT", "ATT", "US", "CS", "AP", "TENNIS", "TABLE", "DE", "DU", "DES", "LA", "LE", "LES", "CLUB",
              "ST", "STE", "SAINT", "SAINTE", "AS", "ASL", "ES", "SP", "PING", "T", "C", "ET"}


def _simple(texte):
    texte = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode("ascii").upper()
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", texte).split())


def mots_cles(nom):
    """Mots qui distinguent un club (« SERRIS ATT » -> SERRIS ; « ST THIBAULT » -> THIBAULT)."""
    return [m for m in _simple(nom).split() if m not in GENERIQUES and not m.isdigit() and len(m) >= 3]


def associer(nom, clubs):
    """Numéro du club « nom » parmi `clubs` ({numéro: {"nom", "equipes": {noms d'équipes sans numéro}}}) :
    d'abord un nom d'équipe identique, sinon un seul club dont le nom ou une équipe contient tous les mots
    qui le distinguent (lettres collées : « APOZOIR » dans « AP OZOIR »). None si aucun ou plusieurs."""
    cible = _simple(nom)
    exacts = {num for num, c in clubs.items() if cible in {_simple(x) for x in [c.get("nom"), *c.get("equipes", ())]}}
    if len(exacts) == 1:
        return exacts.pop()
    mots = mots_cles(nom)
    if not mots:
        return None
    proches = {num for num, c in clubs.items()
               if any(all(m in _simple(x).replace(" ", "") for m in mots) for x in [c.get("nom"), *c.get("equipes", ())])}
    return proches.pop() if len(proches) == 1 else None


def trouver_clubs(client, debut_saison):
    """Numéros FFTT des clubs de CLUBS sans numéro, par leur nom dans les rencontres des journées 1 et 2 du
    comité 77 (les mêmes que la page /77/, en cache) : {nom: numéro}. Le journal écrit chaque association."""
    from . import departement, fftt

    clubs = {}
    for journee in (1, 2):
        for r in fftt.lire_tout(client, departement._url_journee(debut_saison, journee), 30 * 24 * 3600):
            for cote in ("homeOpponent", "awayOpponent"):
                t = fftt.equipe(r, cote)
                num, _, nom = fftt.club_de(t)
                if num:
                    c = clubs.setdefault(num, {"nom": nom, "equipes": set()})
                    if t.get("name"):
                        c["equipes"].add(club_et_numero(t["name"])[0])
    trouves = {}
    for nom, num in CLUBS.items():
        if num:
            continue
        trouves[nom] = associer(nom, clubs)
        print(f"  jeunes : {nom} -> " + (f"{trouves[nom]} ({clubs[trouves[nom]]['nom']})" if trouves[nom]
                                       else "club non trouvé dans les rencontres du comité"), flush=True)
    return trouves

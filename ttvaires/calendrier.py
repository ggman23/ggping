"""Calendrier de la saison (page /cal/) : les dates des compétitions du comité de Seine-et-Marne (CD77).

Source : le calendrier 2026-2027 du CD77 (PDF « Calendrier V2 » de https://www.cdtt77.fr/sportive,
version du 04/09/2025 V3), recopié ici ; il est prévisionnel et peut changer : à mettre à jour quand le
comité publie une nouvelle version. Le calendrier partagé du comité (Google Agenda) n'est pas lu par
l'outil (Google l'interdit aux robots) : la page y renvoie pour s'y abonner.

Chaque date est contrôlée (tests) : elle tombe bien le jour de la semaine du calendrier du comité
(vendredi pour le championnat par équipes, samedi pour le championnat féminin...).
"""

import json
from datetime import date
from pathlib import Path

GABARIT = Path(__file__).with_name("gabarit_cal.html")
SAISON = "2026-2027"
SOURCE = "Calendrier 2026-2027 du CD77 (version du 04/09/2025 V3), prévisionnel"
PDF_CD77 = "https://drive.google.com/file/d/1nA04OHLJtxrdtXi-xKONsWwZfsuqv-wz/view?usp=sharing"
PAGE_CD77 = "https://www.cdtt77.fr/sportive"
AGENDA_CD77 = ("https://calendar.google.com/calendar/u/0?cid="
               "NGU2MzgyYzhkNzdmMGNiNjViY2E1MTc0ZWVjYTNmZGZlMTE5NzAzNDQ1MzQzMjRjYWZhNDNjZDdlYzM3Y2IxNEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t")

# Catégories : clé, nom, nom court (sur les pastilles), style de la pastille, affichée au départ
CATEGORIES = [
    {"cle": "equipes", "nom": "Championnat par équipes", "court": "Équipes", "style": "bleu", "affichee": True,
     "detail": "Championnat de France par équipes, Seine-et-Marne · vendredi"},
    {"cle": "feminin", "nom": "Championnat féminin", "court": "Féminin", "style": "bleu-clair", "affichee": True,
     "detail": "Championnat féminin par équipes 77/94 · samedi"},
    {"cle": "paris", "nom": "Championnat de Paris", "court": "Paris", "style": "orange", "affichee": True,
     "detail": "Championnat de Paris · vendredi"},
    {"cle": "jeunes", "nom": "Championnat des jeunes", "court": "Jeunes", "style": "vert", "affichee": True,
     "detail": "Championnat des jeunes par équipes 77 · vendredi"},
    {"cle": "criterium", "nom": "Critérium fédéral", "court": "Critérium", "style": "neutre", "affichee": True,
     "detail": "Individuels : jeunes le samedi, seniors le dimanche, D4 le dimanche suivant"},
    {"cle": "autres", "nom": "Autres épreuves", "court": "", "style": "contour", "affichee": False,
     "detail": "Coupes, tournois et épreuves du comité"},
    {"cle": "inscriptions", "nom": "Dates limites d'inscription", "court": "Inscription", "style": "pointille", "affichee": False,
     "detail": "Dernier jour pour s'inscrire"},
]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def _journees(categorie, jour, dates, premier=1, detail_phase=True):
    """Journées numérotées d'un championnat : [(date, catégorie, titre, détail, jour attendu)]."""
    sortie = []
    for k, d in enumerate(dates):
        n = premier + k
        detail = (f"Phase {1 if d < '2027-01-01' else 2}" if detail_phase else "")
        sortie.append((d, None, categorie, f"J{n}", detail, jour))
    return sortie


# (début, fin ou None, catégorie, titre, détail, jour de la semaine attendu)
EVENEMENTS = [
    # Championnat par équipes : 7 journées par phase, le vendredi
    *_journees("equipes", "vendredi", ["2026-09-25", "2026-10-02", "2026-10-16", "2026-11-06", "2026-11-20", "2026-12-04", "2026-12-11"]),
    *_journees("equipes", "vendredi", ["2027-01-15", "2027-01-22", "2027-02-26", "2027-03-12", "2027-04-23", "2027-05-21", "2027-05-28"]),
    # Championnat féminin : J1 à J14 sur la saison, le samedi
    *_journees("feminin", "samedi", ["2026-09-26", "2026-10-03", "2026-10-17", "2026-11-07", "2026-11-21", "2026-12-05", "2026-12-12",
                                     "2027-01-16", "2027-01-23", "2027-02-27", "2027-03-13", "2027-04-24", "2027-05-22", "2027-05-29"]),
    # Championnat de Paris et championnat des jeunes : les mêmes vendredis
    *_journees("paris", "vendredi", ["2026-11-27", "2027-01-08", "2027-02-05", "2027-03-19", "2027-04-02", "2027-05-14", "2027-06-04"],
               detail_phase=False),
    *_journees("jeunes", "vendredi", ["2026-11-27", "2027-01-08", "2027-02-05", "2027-03-19", "2027-04-02", "2027-05-14", "2027-06-04"],
               detail_phase=False),
    ("2027-06-19", None, "jeunes", "T", "Journée « T » du calendrier du comité", "samedi"),
    # Critérium fédéral : 4 tours ; jeunes le samedi, seniors le dimanche, D4 le dimanche suivant
    ("2026-10-10", None, "criterium", "Tour 1 · jeunes", "", "samedi"),
    ("2026-10-11", None, "criterium", "Tour 1 · seniors", "", "dimanche"),
    ("2026-10-18", None, "criterium", "Tour 1 · D4", "", "dimanche"),
    ("2026-11-14", None, "criterium", "Tour 2 · jeunes", "", "samedi"),
    ("2026-11-15", None, "criterium", "Tour 2 · seniors", "", "dimanche"),
    ("2026-11-22", None, "criterium", "Tour 2 · D4", "", "dimanche"),
    ("2027-01-30", None, "criterium", "Tour 3 · jeunes", "", "samedi"),
    ("2027-01-31", None, "criterium", "Tour 3 · seniors", "", "dimanche"),
    ("2027-02-07", None, "criterium", "Tour 3 · D4", "", "dimanche"),
    ("2027-03-06", None, "criterium", "Tour 4 · jeunes", "", "samedi"),
    ("2027-03-07", None, "criterium", "Tour 4 · seniors", "", "dimanche"),
    ("2027-03-14", None, "criterium", "Tour 4 · D4", "", "dimanche"),
    # Autres épreuves du comité
    ("2026-08-29", "2026-08-30", "autres", "Internationaux de Charleville-Mézières", "Euro Minichamp's", "samedi"),
    ("2026-09-04", None, "autres", "Assemblée générale du CD77", "", "vendredi"),
    ("2026-09-26", None, "autres", "Top détection", "", "samedi"),
    ("2026-09-26", None, "autres", "Assemblée générale de la Ligue IDF", "", "samedi"),
    ("2026-09-27", None, "autres", "Top départemental", "", "dimanche"),
    ("2026-11-08", None, "autres", "CPS n° 1", "", "dimanche"),
    ("2026-11-08", None, "autres", "Grand Prix M-9 n° 1", "", "dimanche"),
    ("2026-11-11", None, "autres", "Championnat individuel vétérans", "", "mercredi"),
    ("2026-11-22", None, "autres", "1re balle jeunes", "", "dimanche"),
    ("2026-12-06", None, "autres", "1re balle adultes", "", "dimanche"),
    ("2026-12-13", None, "autres", "Tournoi Jeunes Pousses", "", "dimanche"),
    ("2026-12-19", "2026-12-20", "autres", "Internationaux du Grand Est", "", "samedi"),
    ("2027-01-10", None, "autres", "Challenge Bernard Jeu", "", "dimanche"),
    ("2027-01-24", None, "autres", "Coupe nationale vétérans", "Poules", "dimanche"),
    ("2027-01-24", None, "autres", "CPS n° 2", "", "dimanche"),
    ("2027-01-24", None, "autres", "Grand Prix M-9 n° 2", "", "dimanche"),
    ("2027-02-07", "2027-02-12", "autres", "Stage Mesnil-Saint-Père 77/91", "", "dimanche"),
    ("2027-02-28", None, "autres", "Finales par classements", "", "dimanche"),
    ("2027-03-14", None, "autres", "1re balle jeunes", "", "dimanche"),
    ("2027-03-21", None, "autres", "Coupe mixte", "Poules", "dimanche"),
    ("2027-03-21", None, "autres", "Grand Prix M-9 n° 3", "", "dimanche"),
    ("2027-04-25", None, "autres", "1re balle adultes", "", "dimanche"),
    ("2027-05-23", None, "autres", "Coupe Davis jeunes", "", "dimanche"),
    ("2027-05-30", None, "autres", "Interclubs", "", "dimanche"),
    ("2027-05-30", None, "autres", "Tournoi féminin 77/91", "", "dimanche"),
    ("2027-06-06", None, "autres", "Coupe mixte", "Finale", "dimanche"),
    ("2027-06-06", None, "autres", "Tournoi Jeunes Pousses", "", "dimanche"),
    # Dates limites d'inscription
    ("2026-09-11", None, "inscriptions", "Critérium fédéral régional", "", "vendredi"),
    ("2026-09-13", None, "inscriptions", "Championnat féminin", "", "dimanche"),
    ("2026-09-13", None, "inscriptions", "Championnat par équipes", "", "dimanche"),
    ("2026-09-28", None, "inscriptions", "Critérium fédéral 77", "", "lundi"),
    ("2026-11-04", None, "inscriptions", "Championnat individuel vétérans", "", "mercredi"),
    ("2026-12-18", None, "inscriptions", "Coupe nationale vétérans", "", "vendredi"),
    ("2027-01-01", None, "inscriptions", "D5 et F supplémentaires, phase 2", "", "vendredi"),
    ("2027-03-07", None, "inscriptions", "Coupe mixte", "", "dimanche"),
]


def jours_faux():
    """Dates qui ne tombent pas le jour de la semaine du calendrier du comité (erreur de recopie)."""
    return [(debut, titre, attendu, JOURS[date.fromisoformat(debut).weekday()])
            for debut, _, _, titre, _, attendu in EVENEMENTS if JOURS[date.fromisoformat(debut).weekday()] != attendu]


def donnees():
    """Données de la page : catégories, évènements triés par date, sources."""
    noms = {c["cle"]: c for c in CATEGORIES}

    def court(cat, titre):
        """Libellé des cases de la grille : « Crit. T2 jeunes » plutôt que « Critérium Tour 2 · jeunes »."""
        if cat == "criterium":
            tour, _, quoi = titre.partition(" · ")
            return f"Crit. T{tour.split()[-1]} {quoi}"
        return f"{noms[cat]['court']} {titre}".strip() if cat != "autres" else titre

    evenements = sorted(({"debut": debut, "fin": fin, "cat": cat,
                          "titre": f"{noms[cat]['court']} {titre}".strip() if cat not in ("autres",) else titre,
                          "court": court(cat, titre), "detail": detail} for debut, fin, cat, titre, detail, _ in EVENEMENTS),
                        key=lambda e: (e["debut"], [c["cle"] for c in CATEGORIES].index(e["cat"]), e["titre"]))
    return {"saison": SAISON, "source": SOURCE, "pdf": PDF_CD77, "page_cd77": PAGE_CD77, "agenda_cd77": AGENDA_CD77,
            "categories": CATEGORIES, "evenements": evenements}


def page():
    """Page /cal/ (HTML) : le gabarit avec les données du calendrier."""
    js = json.dumps(donnees(), ensure_ascii=False).replace("<", "\\u003c")
    return GABARIT.read_text(encoding="utf-8").replace("__DONNEES_JSON__", js).encode("utf-8")

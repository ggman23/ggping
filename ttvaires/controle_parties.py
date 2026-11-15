"""Contrôle des parties lues pour les points virtuels des joueurs du 77 (journal de la mise à jour).

Signalé le 15/11/2026 : pour un joueur du 77, l'outil comptait 99 parties et +203 points depuis le
début de la saison, la FFTT 98 parties et +123. Causes possibles : parties « non comptées »
(l'information n'est que dans le détail d'une partie, une requête par partie, que l'outil ne lit pas
pour les joueurs du 77), coefficients des compétitions, parties en double, date de prise en compte
(« effectiveDate ») différente de la date de la partie.

Ce contrôle mesure tout cela et l'écrit dans le journal, en chiffres seulement : aucun nom, aucun
numéro de licence (le journal d'un dépôt public est public). Il ne coûte presque rien : les listes de
parties sont déjà en cache ; seul le détail d'une partie hors championnat sur ECHANTILLON (choisie par
son numéro, donc toujours la même) est lu, une fois, puis gardé.
"""

import json
from collections import Counter, defaultdict

from . import fftt
from .fftt import API, ENTETES, json_valide
from .resultats import points_partie
from .virtuel import _competitions, _lire_parties, _simple, est_championnat, famille_competition, url_parties

ECHANTILLON = 40  # une partie hors championnat sur 40 : son détail dit si elle est « non comptée »


def _forme(valeur, profondeur=2):
    """Forme d'une valeur JSON sans son contenu : type, et noms des champs d'un objet."""
    if isinstance(valeur, dict):
        if profondeur <= 0:
            return "{…}"
        return "{" + ", ".join(f"{k}: {_forme(v, profondeur - 1)}" for k, v in sorted(valeur.items()) if not k.startswith("@")) + "}"
    if isinstance(valeur, list):
        return f"[{_forme(valeur[0], profondeur - 1)}…]" if valeur else "[]"
    return type(valeur).__name__


def controler(client, licences, debut, fin):
    """Écrit dans le journal le contrôle des parties des joueurs déjà lus ; renvoie le résumé (pour les tests)."""
    lues = [lic for lic in licences if client.date(url_parties(lic)) is not None]
    if not lues:
        return None
    toutes = _lire_parties(client, lues, ttl=None, message=None)  # réponses déjà enregistrées : aucune requête
    res = {"joueurs": len(lues)}
    print(f"--- Contrôle des parties des joueurs du 77 ({len(lues)} joueurs déjà lus) ---", flush=True)

    # Filtres que l'API accepte sur la liste des parties (un filtre « non comptée » éviterait le détail)
    page = client.get(url_parties(lues[0]), ttl=None, entetes=ENTETES, valide=json_valide)
    recherche = json.loads(page).get("hydra:search") or {}
    res["filtres"] = recherche.get("hydra:template")
    print(f"  filtres de la liste des parties : {res['filtres'] or 'non indiqués'}", flush=True)

    # Parties de simple dans la phase : doublons, date de prise en compte, hors championnat
    doublons, effet_avant, effet_apres, hors_phase_effet_dedans = 0, 0, 0, 0
    hors, paires = {}, 0
    for parties in toutes.values():
        vus = Counter(p.get("id") for p in parties or [])
        doublons += sum(n - 1 for n in vus.values() if n > 1)
        for p in parties or []:
            jour, effet = (p.get("date") or "")[:10], (p.get("effectiveDate") or "")[:10]
            if not _simple(p):
                continue
            dans = debut <= jour <= fin
            if effet and dans and effet < debut:
                effet_avant += 1
            if effet and dans and effet > fin:
                effet_apres += 1
            if effet and not dans and debut <= effet <= fin:
                hors_phase_effet_dedans += 1
            if dans and not est_championnat((p.get("contest") or {}).get("name")):
                hors[p["id"]] = p
                paires += 1
    res.update(doublons=doublons, hors_championnat=len(hors))
    print(f"  parties en double dans une même liste : {doublons}", flush=True)
    print(f"  date de prise en compte (effectiveDate) : avant la phase pour {effet_avant} parties de la phase, après "
          f"aujourd'hui pour {effet_apres} ; dans la phase pour {hors_phase_effet_dedans} parties jouées hors de la phase", flush=True)
    print(f"  parties de simple hors championnat dans la phase : {len(hors)} distinctes ({paires} pour l'ensemble des "
          "joueurs) : nombre de requêtes pour lire le détail de toutes", flush=True)
    exemple = next((p for p in hors.values() if p.get("sportMatch")), None)
    if exemple:
        print(f"  forme du champ sportMatch dans la liste : {_forme(exemple['sportMatch'])}"[:600], flush=True)

    # Adversaires hors du 77 (leur valeur du mois est inconnue) : combien, et combien de parties contre eux
    du_77, exterieurs, contre, touches = set(licences), set(), 0, set()
    for lic, parties in toutes.items():
        for p in parties or []:
            if not (_simple(p) and debut <= (p.get("date") or "")[:10] <= fin):
                continue
            h, a = (p.get("homePlayer") or {}).get("identifier"), (p.get("awayPlayer") or {}).get("identifier")
            adv = a if h == lic else h
            if adv and adv not in du_77:
                exterieurs.add(adv)
                contre += 1
                touches.add(lic)
    res["exterieurs"] = len(exterieurs)
    print(f"  adversaires hors du 77 : {len(exterieurs)} joueurs différents, {contre} parties contre eux, "
          f"{len(touches)} joueurs du 77 concernés", flush=True)

    # Ce que l'API donne d'un joueur (noms des champs seulement) : points mensuels ou virtuels ?
    joueur = next((p.get("homePlayer") for ps in toutes.values() if ps for p in ps if p.get("homePlayer")), None)
    if joueur:
        print(f"  forme d'un joueur dans une partie : {_forme(joueur)}"[:700], flush=True)
    try:
        entree = json.loads(client.get(API, ttl=None, entetes=ENTETES, valide=json_valide))
        print("  rubriques de l'API : " + ", ".join(sorted(k for k in entree if not k.startswith("@")))[:1500], flush=True)
        iri = (joueur or {}).get("@id")
        if iri:
            licence = json.loads(client.get(API + iri[len("/api"):], ttl=None, entetes=ENTETES, valide=json_valide))
            print(f"  forme d'une licence ({iri.rsplit('/', 2)[-2]}) : {_forme(licence, 3)}"[:1500], flush=True)
    except Exception as e:  # noqa: BLE001 (un contrôle ne bloque jamais la mise à jour)
        print(f"  rubriques de l'API : non lues ({type(e).__name__})", flush=True)

    # Coefficients donnés par la FFTT, par famille de compétitions (nombre de parties)
    competitions = _competitions(client, {(p.get("contest") or {}).get("id") for p in hors.values()} - {None})
    coefs = defaultdict(Counter)
    for p in hors.values():
        c = competitions.get((p.get("contest") or {}).get("id"), {})
        coefs[famille_competition(c.get("nom") or (p.get("contest") or {}).get("name"))][c.get("coef")] += 1
    for famille, compte in sorted(coefs.items(), key=lambda x: -sum(x[1].values()))[:12]:
        print(f"  coefficients, {famille} : " + ", ".join(f"{k} ({n} parties)" for k, n in compte.most_common()), flush=True)

    # Échantillon : détail d'une partie sur ECHANTILLON, pour la part de parties « non comptées »
    echantillon = sorted(i for i in hors if isinstance(i, int) and i % ECHANTILLON == 0)
    urls = {i: f"{API}/games/{i}" for i in echantillon}
    pages = client.get_plusieurs(list(urls.values()), ttl=None, message="détail des parties (échantillon du contrôle)",
                                 entetes=ENTETES, valide=json_valide) if urls else {}
    lus, non_comptees, tableaux = Counter(), Counter(), Counter()
    details = {}
    for i, url in urls.items():
        if not pages.get(url):
            continue
        g = details[i] = json.loads(pages[url])
        c = competitions.get((hors[i].get("contest") or {}).get("id"), {})
        famille = famille_competition(c.get("nom") or (hors[i].get("contest") or {}).get("name"))
        lus[famille] += 1
        if g.get("notCounted"):
            non_comptees[famille] += 1
            sm = g.get("sportMatch") or {}
            division = ((sm.get("tour") or {}).get("division") or sm.get("division") or {}).get("name") if isinstance(sm, dict) else None
            tableaux[fftt.libelle_division(division) if division else "?"] += 1
    res.update(echantillon=sum(lus.values()), non_comptees=sum(non_comptees.values()))
    print(f"  échantillon (1 partie sur {ECHANTILLON}) : {sum(lus.values())} parties lues en détail, "
          f"{sum(non_comptees.values())} « non comptées » ; par famille : "
          + (", ".join(f"{f} {non_comptees[f]}/{n}" for f, n in lus.most_common()) or "—"), flush=True)
    if tableaux:
        print("  tableaux des parties non comptées : " + ", ".join(f"{t} ({n})" for t, n in tableaux.most_common(10))[:500], flush=True)
    res.update(comparer_au_detail(hors, details, competitions))
    return res


def _nombre(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def comparer_au_detail(hors, details, competitions):
    """Le détail d'une partie (échantillon) comparé au calcul de l'outil, en chiffres : champs présents,
    valeurs de homePoints / awayPoints, et, par famille de compétitions, leur rapport au barème (si ce
    sont les points gagnés ou perdus calculés par la FFTT, ce rapport est le coefficient qu'elle applique)."""
    if not details:
        return {}
    n = len(details)
    champs = Counter(k for g in details.values() for k, v in g.items() if not k.startswith("@") and v not in (None, False, "", []))
    print(f"  champs remplis du détail (sur {n} parties) : " + ", ".join(f"{k} {c}" for k, c in champs.most_common()), flush=True)
    valeurs = [g.get(c) for g in details.values() for c in ("homePoints", "awayPoints") if _nombre(g.get(c))]
    entieres = sum(1 for v in valeurs if float(v).is_integer())
    print(f"  homePoints / awayPoints : {len(valeurs)} valeurs, dont {entieres} entières ; les plus fréquentes : "
          + ", ".join(f"{v} ({c})" for v, c in Counter(valeurs).most_common(12)), flush=True)
    egales, comparees, rapports, exemples = Counter(), Counter(), defaultdict(Counter), []
    speciales = Counter()
    for i, g in details.items():
        p = hors[i]
        h, a = p.get("homePlayer") or {}, p.get("awayPlayer") or {}
        c = competitions.get((p.get("contest") or {}).get("id"), {})
        famille = famille_competition(c.get("nom") or (p.get("contest") or {}).get("name"))
        for drapeau in ("forfeit", "abandonment", "penalty", "draw", "notCounted"):
            if g.get(drapeau):
                speciales[f"{drapeau} (homePoints {g.get('homePoints')}, awayPoints {g.get('awayPoints')})"] += 1
        if not (_nombre(h.get("points")) and _nombre(a.get("points")) and p.get("winner") in ("home", "away")
                and _nombre(g.get("homePoints"))):
            continue
        bareme = points_partie(h["points"], a["points"], p["winner"] == "home", 1)
        comparees[famille] += 1
        if c.get("coef") is not None and abs(bareme * c["coef"] - g["homePoints"]) < 0.01:
            egales[famille] += 1
        if bareme:
            rapports[famille][round(g["homePoints"] / bareme, 3)] += 1
        if len(exemples) < 8:
            exemples.append(f"écart {round(a['points'] - h['points'])}, {'victoire' if p['winner'] == 'home' else 'défaite'}, "
                            f"barème {bareme}, coef {c.get('coef')} -> homePoints {g['homePoints']}, awayPoints {g.get('awayPoints')}")
    for famille, k in comparees.most_common():
        print(f"  {famille} : {k} parties comparées, homePoints = barème × coefficient de la FFTT pour {egales[famille]} ; "
              f"homePoints / barème : " + ", ".join(f"{r} ({c})" for r, c in rapports[famille].most_common(5)), flush=True)
    for e in exemples:
        print(f"    exemple (joueur à domicile) : {e}", flush=True)
    print("  parties particulières de l'échantillon : " + (", ".join(f"{s} : {c}" for s, c in speciales.most_common(10)) or "aucune"), flush=True)
    return {"comparees": sum(comparees.values()), "egales": sum(egales.values())}

"""Récupération des données sur pingpocket.fr.

Les fonctions `lire_*` analysent une page (fragment HTML) ; `recuperer` enchaîne les
téléchargements et construit le dictionnaire de données utilisé par brulage.py et rendu.py.
"""

import re
from collections import defaultdict
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .reseau import HEURE, JOUR

MOIS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
CATEGORIES = {"Poussin": "P", "Benjamin": "B", "Minime": "M", "Cadet": "C", "Junior": "J",
              "Senior": "S", "Sénior": "S", "Vétéran": "V"}
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# ---------------------------------------------------------------------------
# Petits utilitaires
# ---------------------------------------------------------------------------

def _soupe(html):
    return BeautifulSoup(html, "html.parser")


def _texte(el):
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def _params(href):
    return {k: v[0] for k, v in parse_qs(urlparse(href).query).items()}


def _entier(txt):
    txt = (txt or "").strip()
    return int(txt) if re.fullmatch(r"-?\d+", txt) else None


def date_longue(txt):
    """'Sep 25, 2026' -> '2026-09-25'."""
    m = re.search(r"([A-Z][a-z]{2})\s+(\d{1,2}),\s*(\d{4})", txt or "")
    return date(int(m[3]), MOIS[m[1]], int(m[2])).isoformat() if m and m[1] in MOIS else None


def date_courte(txt, reference):
    """'02 Oct' -> date ISO, l'année étant celle qui rapproche le plus de `reference`."""
    m = re.fullmatch(r"(\d{1,2})\s+([A-Z][a-z]{2})", (txt or "").strip())
    if not m or m[2] not in MOIS:
        return None
    ref = date.fromisoformat(reference) if reference else date.today()
    candidats = []
    for annee in (ref.year - 1, ref.year, ref.year + 1):
        try:
            candidats.append(date(annee, MOIS[m[2]], int(m[1])))
        except ValueError:
            pass
    return min(candidats, key=lambda d: abs((d - ref).days)).isoformat() if candidats else None


def separer_nom(complet):
    """'SOARES GARCIA Ricardo Andre' -> ('SOARES GARCIA', 'Ricardo Andre')."""
    mots = complet.split()
    i = 0
    while i < len(mots) - 1 and mots[i] == mots[i].upper():
        i += 1
    return " ".join(mots[:i]) or complet, " ".join(mots[i:])


def categorie_courte(txt):
    """'Vétéran 45' -> 'V45', 'Minime 1' -> 'M1', 'Senior' -> 'S'."""
    m = re.match(r"(\w+)\s*(\d*)", txt or "")
    if m and m[1] in CATEGORIES:
        return CATEGORIES[m[1]] + m[2]
    return txt


def libelle_division(txt):
    """Rend lisibles les codes de division FFTT ('L08_R2' -> 'Régionale 2', 'DEP 3' -> 'Départementale 3')."""
    txt = " ".join((txt or "").replace("FED_", "").split())
    txt = re.sub(r"^L\d+_R(\d+)", r"Régionale \1", txt)
    txt = re.sub(r"^PRE-REG\b", "Pré-régionale", txt)
    txt = re.sub(r"^DEP (\d+)", r"Départementale \1", txt)
    return txt


# ---------------------------------------------------------------------------
# Lecture des pages
# ---------------------------------------------------------------------------

def lire_equipes_club(html):
    """Page /clubs/{n}/equipes?phase=p -> (nom du club, [équipe, ...])."""
    soup = _soupe(html)
    info = soup.select_one("div.info span")
    equipes = []
    for a in soup.select('a[href*="/championnats/"]'):
        m = re.search(r"/clubs/(\d+)/equipes/(\d+)/championnats/(masculin|feminin)", a["href"])
        if not m:
            continue
        label = _texte(a.select_one(".labels p"))
        division, _, poule = label.partition("Poule")
        equipes.append({
            "club": m[1], "numero": int(m[2]), "championnat": "M" if m[3] == "masculin" else "F",
            "division": libelle_division(division), "poule": f"Poule {poule.strip()}" if poule else "",
            "lien": a["href"],
        })
    return _texte(info), equipes


def lire_poule(html):
    """Page d'une poule -> classement et rencontres de toutes les journées."""
    soup = _soupe(html)
    classement, rang = [], 0
    for li in soup.select("ul.pool-ranking > li.arrow"):
        a = li.find("a", href=True)
        spans = a.find_all("span") if a else []
        if not spans:
            continue
        p = _params(a["href"])
        rang = _entier(_texte(spans[0]).rstrip(".")) or rang
        bouton = li.select_one("span.ppk-button")
        valeurs = (bouton.get("data-values", "") if bouton else "").split(";")
        gnp = valeurs[2].split() if len(valeurs) > 2 else []
        pgpp = valeurs[3].split() if len(valeurs) > 3 else []
        classement.append({
            "rang": rang, "libelle": _texte(spans[-1]), "club": p.get("COMPETITION_CLUB_ID1"),
            "numero": _entier(p.get("COMPETITION_TEAM_NUMBER_1")),
            "points": _entier(valeurs[0]) if valeurs else None,
            "joues": _entier(valeurs[1]) if len(valeurs) > 1 else None,
            "v": _entier(gnp[0]) if len(gnp) == 3 else None,
            "n": _entier(gnp[1]) if len(gnp) == 3 else None,
            "d": _entier(gnp[2]) if len(gnp) == 3 else None,
            "pg": _entier(pgpp[0]) if len(pgpp) == 2 else None,
            "pp": _entier(pgpp[1]) if len(pgpp) == 2 else None,
        })

    rencontres = []
    for ul in soup.select("div.championshipDays > ul"):
        entete = ul.find("li")
        spans = entete.find_all("span") if entete else []
        if len(spans) < 2:
            continue
        journee = _entier(re.sub(r"\D", "", spans[0].get_text()))
        date_journee = date_longue(spans[1].get_text())
        for li in ul.select("li.score"):
            resultat = li.select_one("div.result")
            if not resultat:
                continue
            enfants = [c for c in resultat.children if getattr(c, "name", None)]
            if len(enfants) < 2:
                continue
            dom, ext = _texte(enfants[0]) or None, _texte(enfants[-1]) or None
            milieu = enfants[1] if len(enfants) == 3 else None
            score, date_prevue = None, None
            if milieu is not None and milieu.name == "div":
                nombres = [s.get_text(strip=True) for s in milieu.find_all("span")]
                if len(nombres) == 3 and nombres[0] and nombres[2]:
                    score = [_entier(nombres[0]) if _entier(nombres[0]) is not None else nombres[0],
                             _entier(nombres[2]) if _entier(nombres[2]) is not None else nombres[2]]
            elif milieu is not None:
                date_prevue = date_courte(_texte(milieu), date_journee)
            a = li.find("a", href=True)
            p = _params(a["href"]) if a else {}
            rencontres.append({
                "journee": journee, "date_journee": date_journee, "date_prevue": date_prevue,
                "domicile": dom, "exterieur": ext, "score": score,
                "club_dom": p.get("COMPETITION_CLUB_ID1") if dom else None,
                "club_ext": p.get("COMPETITION_CLUB_ID2") if ext else None,
                "lien": a["href"] if a else None,
            })
    return {"classement": classement, "rencontres": rencontres}


def lire_feuille(html):
    """Feuille de match -> [côté domicile, côté extérieur], chacun {equipe, club, joueurs}."""
    soup = _soupe(html)
    grille = soup.select_one("div.division-grid:not(.championshipDays)")
    cotes = []
    for ul in (grille.find_all("ul", recursive=False) if grille else [])[:2]:
        lis = ul.find_all("li", recursive=False)
        cote = {"equipe": _texte(lis[0].select_one(".labels p")) if lis else "", "club": None, "joueurs": []}
        for li in lis[1:]:
            a = li.find("a", href=True)
            if not a:
                continue
            m = re.search(r"/licencies/(\d+)", a["href"])
            if m:
                nom, prenom = separer_nom(_texte(a.select_one(".labels p")))
                cote["joueurs"].append({
                    "licence": m[1], "nom": nom, "prenom": prenom,
                    "points": _entier(_texte(a.select_one("p.rich-button"))),
                    "sexe": "F" if a.select_one("i.fa-female") else "M",
                })
            elif (mc := re.search(r"/clubs/(\d+)", a["href"])):
                cote["club"] = mc[1]
        cotes.append(cote)
    return cotes


def lire_parties(html):
    """Parties de simple d'une feuille de match -> [{a, b, gagnant}] (numéros de licence).

    Les doubles (sans lien vers les joueurs) et les parties sans vainqueur sont ignorés.
    """
    soup = _soupe(html)
    parties = []
    for li in soup.select("ul.divisionIndividualRoundMatchesPanel > li"):
        liens = [a for a in li.find_all("a", href=True) if "/licencies/" in a["href"]]
        if len(liens) != 2:
            continue
        a, b = (re.search(r"/licencies/(\d+)", l["href"])[1] for l in liens)
        etats = [l.select_one("span.pos, span.neg") for l in liens]
        if etats[0] is not None and "pos" in etats[0].get("class", []):
            gagnant = a
        elif etats[1] is not None and "pos" in etats[1].get("class", []):
            gagnant = b
        else:
            continue
        parties.append({"a": a, "b": b, "gagnant": gagnant})
    return parties


def lire_liste_licencies(html):
    """Liste des licenciés d'un club (triée par classement, catégorie, état de licence...).

    Renvoie [(titre de section, [{licence, nom, prenom, sexe, compteur}, ...]), ...].
    """
    soup = _soupe(html)
    sections, courante = [], None
    for li in soup.select("ul.edgetoedge li"):
        classes = li.get("class") or []
        if "sep" in classes:
            courante = (_texte(li.find("p")), [])
            sections.append(courante)
        elif "arrow" in classes:
            a = li.find("a", href=True)
            m = re.search(r"/licencies/(\d+)", a["href"]) if a else None
            if not m:
                continue
            if courante is None:
                courante = ("", [])
                sections.append(courante)
            nom, prenom = separer_nom(_texte(a.select_one(".labels p")))
            compteur = a.select_one("small.counter")
            courante[1].append({
                "licence": m[1], "nom": nom, "prenom": prenom,
                "sexe": "F" if a.select_one("i.fa-female") else "M",
                "compteur": _texte(compteur),
            })
    return sections


def lire_salle(html):
    """Page coordonnées d'un club -> {nom, adresse, cp, ville, carte} ou None."""
    soup = _soupe(html)
    titre = next((h for h in soup.find_all("h2") if _texte(h).startswith("Salle")), None)
    ul = titre.find_next_sibling("ul") if titre else None
    p = ul.find("p") if ul else None
    if not p:
        return None
    lignes = [" ".join(s.split()) for s in p.stripped_strings]
    salle = {"nom": None, "adresse": None, "cp": None, "ville": None, "carte": None}
    if lignes and (m := re.match(r"(\d{5})\s+(.*)", lignes[-1])):
        salle["cp"], salle["ville"] = m[1], m[2].strip()
        lignes = lignes[:-1]
    if len(lignes) >= 2:
        salle["nom"], salle["adresse"] = lignes[0], " ".join(lignes[1:])
    elif lignes:
        salle["adresse"] = lignes[0]
    carte = ul.select_one('a[href*="maps"]')
    salle["carte"] = carte["href"] if carte else None
    return salle


def lire_historique(html):
    """Graphique 'historique classement' -> [(annee, mois, points), ...] (mois de 1 à 12)."""
    points = re.findall(r"x:\s*Date\.UTC\((\d{4}),\s*(\d{1,2}),\s*\d+\)\s*,\s*y:\s*([\d.]+)", html)
    return [(int(a), int(m) + 1, round(float(y))) for a, m, y in points]


def resume_historique(points):
    """Points officiels actuels et meilleur classement (points de début de phase : janvier et juillet)."""
    officiels = [p for p in points if p[1] in (1, 7)] or points
    if not officiels:
        return None, None
    meilleur = max(officiels, key=lambda p: (p[2], p[0], p[1]))
    return officiels[-1][2], {"points": meilleur[2], "annee": str(meilleur[0])}


# ---------------------------------------------------------------------------
# Récupération complète
# ---------------------------------------------------------------------------

def phase_et_saison(jour):
    debut = jour.year if jour.month >= 7 else jour.year - 1
    return (1 if jour.month >= 7 else 2), f"{debut}-{debut + 1}"


def _date_effective(r, aujourdhui):
    """Date à laquelle une rencontre a (ou aura) lieu."""
    d = r["date_prevue"] or r["date_journee"]
    if r["score"] is not None and d and d > aujourdhui:
        d = aujourdhui  # rencontre avancée, déjà jouée
    return d


def _mon_libelle(poule, club, numero, championnat, libelles):
    """Libellé d'une équipe du club dans sa poule (ex. 'LOGNES EP 12')."""
    for c in poule["classement"]:
        if c["club"] == club and c["numero"] == numero:
            return c["libelle"]
    du_club = [c["libelle"] for c in poule["classement"] if c["club"] == club and c["libelle"] not in libelles]
    meme_numero = [lib for lib in du_club if re.search(rf"\b{numero}$", lib or "")]
    return (meme_numero or du_club or [None])[0]


def _jour_habituel(dates):
    jours = [date.fromisoformat(d).weekday() for d in dates if d]
    return JOURS[max(set(jours), key=jours.count)] if jours else None


def recuperer(client, numero_club="08770250", aujourdhui=None):
    aujourdhui = aujourdhui or date.today()
    auj = aujourdhui.isoformat()
    phase, saison = phase_et_saison(aujourdhui)

    # 1. Les équipes de Vaires et leurs poules
    print(f"1/5 Équipes du club {numero_club} (phase {phase} {saison})", flush=True)
    nom_club, equipes_club = lire_equipes_club(client.get(f"/app/fftt/clubs/{numero_club}/equipes?phase={phase}", JOUR))
    equipes_club.sort(key=lambda e: (e["championnat"] == "F", e["numero"]))
    pages = client.get_plusieurs([e["lien"] for e in equipes_club], ttl=3 * HEURE)
    salle_club = lire_salle(client.get(f"/app/fftt/clubs/{numero_club}/coordonnees", 30 * JOUR))

    equipes, besoins = [], defaultdict(set)
    for e in equipes_club:
        if not pages.get(e["lien"]):
            continue
        poule = lire_poule(pages[e["lien"]])
        moi = _mon_libelle(poule, numero_club, e["numero"], e["championnat"], set())
        rencontres = []
        for r in poule["rencontres"]:
            if moi not in (r["domicile"], r["exterieur"]):
                continue
            chez_nous = r["domicile"] == moi
            adv_lib = r["exterieur"] if chez_nous else r["domicile"]
            adv_club = r["club_ext"] if chez_nous else r["club_dom"]
            adv_num = None
            for c in poule["classement"]:
                if c["libelle"] == adv_lib:
                    adv_club, adv_num = adv_club or c["club"], c["numero"]
            adversaire = {"club": adv_club, "libelle": adv_lib, "numero": adv_num} if adv_lib else None
            if adversaire and adv_club:
                besoins[adv_club].add(e["championnat"])
            date_prevue = r["date_prevue"]
            rencontres.append({
                "journee": r["journee"], "date": r["date_journee"],
                "date_reelle": date_prevue if date_prevue and date_prevue != r["date_journee"] else None,
                "heure": None,
                "domicile": {"libelle": r["domicile"], "club": r["club_dom"]},
                "exterieur": {"libelle": r["exterieur"], "club": r["club_ext"]},
                "vaires_domicile": chez_nous, "score": r["score"], "adversaire": adversaire,
            })
        feminine = e["championnat"] == "F"
        equipes.append({
            "id": f"v{e['numero']}{'f' if feminine else ''}",
            "libelle": moi or f"{nom_club} {e['numero']}",
            "nom_court": f"Vaires {e['numero']}{' F' if feminine else ''}",
            "numero": e["numero"], "championnat": e["championnat"],
            "division": e["division"], "poule": e["poule"],
            "jour": _jour_habituel([r["date_reelle"] or r["date"] for r in rencontres]),
            "rencontres": rencontres, "classement": poule["classement"],
        })

    # 2. Clubs adverses : équipes, salle, listes de licenciés
    clubs_adv = sorted(besoins)
    print(f"2/5 Clubs adverses : {len(clubs_adv)}", flush=True)
    listes = {}
    for c in clubs_adv:
        listes[c] = {
            "equipes": f"/app/fftt/clubs/{c}/equipes?phase={phase}",
            "salle": f"/app/fftt/clubs/{c}/coordonnees",
            "categories": f"/app/fftt/clubs/{c}/licencies?SORT=CATEGORY",
            "classements": f"/app/fftt/clubs/{c}/licencies?SORT=OFFICIAL_RANK",
            "etat": f"/app/fftt/clubs/{c}/licencies?SORT=LICENCE_STATE",
        }
    pages = client.get_plusieurs([u for l in listes.values() for u in l.values()], ttl=JOUR, message="pages clubs")

    clubs = {}
    for c in clubs_adv:
        html = pages.get(listes[c]["equipes"])
        if not html:
            continue
        nom, equipes_adv = lire_equipes_club(html)
        clubs[c] = {
            "numero": c, "nom": nom,
            "salle": lire_salle(pages[listes[c]["salle"]]) if pages.get(listes[c]["salle"]) else None,
            "joueurs": _effectif(pages, listes[c]),
            "equipes": [dict(e) for e in equipes_adv if e["championnat"] in besoins[c]],
        }

    # 3. Poules de toutes les équipes des clubs adverses
    liens = [e["lien"] for club in clubs.values() for e in club["equipes"]]
    print(f"3/5 Poules des équipes adverses : {len(liens)}", flush=True)
    pages = client.get_plusieurs(liens, ttl=3 * HEURE, message="poules")
    feuilles_a_lire = []
    for c, club in clubs.items():
        pris = set()
        for e in club["equipes"]:
            html = pages.get(e.pop("lien"))
            e["rencontres_jouees"] = []
            if not html:
                continue
            poule = lire_poule(html)
            e["libelle"] = _mon_libelle(poule, c, e["numero"], e["championnat"], pris) or f"{club['nom']} {e['numero']}"
            pris.add(e["libelle"])
            for r in poule["rencontres"]:
                if e["libelle"] in (r["domicile"], r["exterieur"]) and r["score"] is not None and r["lien"]:
                    e["rencontres_jouees"].append({"journee": r["journee"], "date": _date_effective(r, auj),
                                                   "lien": r["lien"], "domicile": r["domicile"] == e["libelle"]})
                    feuilles_a_lire.append(r["lien"])

    # 4. Feuilles de match : qui a joué dans quelle équipe
    print(f"4/5 Feuilles de match : {len(set(feuilles_a_lire))}", flush=True)
    pages = client.get_plusieurs(feuilles_a_lire, ttl=None, message="feuilles de match")
    for c, club in clubs.items():
        connus = {j["id"] for j in club["joueurs"]}
        for e in club["equipes"]:
            e["compositions"] = []
            for r in e.pop("rencontres_jouees"):
                cotes = lire_feuille(pages[r["lien"]]) if pages.get(r["lien"]) else []
                if len(cotes) != 2 or not cotes[0]["joueurs"] or not cotes[1]["joueurs"]:
                    client.oublier(r["lien"])  # feuille pas encore saisie : on retentera
                    continue
                cote = cotes[0] if r["domicile"] else cotes[1]
                e["compositions"].append({"journee": r["journee"], "date": r["date"],
                                          "joueurs": [j["licence"] for j in cote["joueurs"]]})
                for j in cote["joueurs"]:
                    if j["licence"] not in connus:  # joueur absent des listes du club
                        connus.add(j["licence"])
                        club["joueurs"].append({
                            "id": j["licence"], "licence": j["licence"], "nom": j["nom"], "prenom": j["prenom"],
                            "sexe": j["sexe"], "categorie": None, "classement": None, "points": None,
                            "points_mensuels": j["points"], "meilleur": None, "renouvele": True,
                        })

    # 5. Historique des classements (meilleur classement). Les joueurs restés à 500 points (le
    # minimum) qui n'ont pas joué n'ont en pratique jamais été mieux classés : on épargne ces pages
    # au site. Les plus utiles d'abord (joueurs alignés cette phase, puis par points).
    alignes = {jid for club in clubs.values() for e in club["equipes"]
               for compo in e["compositions"] for jid in compo["joueurs"]}
    a_lire = [j for club in clubs.values() for j in club["joueurs"]
              if j["renouvele"] and ((j["points_mensuels"] or 0) > 500 or j["id"] in alignes)]
    a_lire.sort(key=lambda j: (j["id"] not in alignes, -(j["points_mensuels"] or 0)))
    print(f"5/5 Historiques des joueurs : {len(a_lire)}", flush=True)
    pages = client.get_plusieurs(
        [f"/app/fftt/licencies/{j['licence']}/graphiques/historique-classement" for j in a_lire],
        ttl=20 * JOUR, message="historiques")
    for j in a_lire:
        html = pages.get(f"/app/fftt/licencies/{j['licence']}/graphiques/historique-classement")
        if html:
            officiels, meilleur = resume_historique(lire_historique(html))
            j["points"], j["meilleur"] = officiels, meilleur
            if j["classement"] is None and officiels:
                j["classement"] = max(5, officiels // 100)

    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"),
        "saison": saison, "phase": phase,
        "club": {"numero": numero_club, "nom": nom_club, "salle": salle_club},
        "equipes": equipes, "clubs": clubs,
    }


def _effectif(pages, liens):
    """Fusionne les listes de licenciés d'un club (catégories, classements, état des licences).

    Les licences loisir (affichées 'L' à la place des points) sont écartées.
    """
    joueurs = {}
    for titre, liste in lire_liste_licencies(pages.get(liens["categories"]) or ""):
        for j in liste:
            joueurs[j["licence"]] = {
                "id": j["licence"], "licence": j["licence"], "nom": j["nom"], "prenom": j["prenom"],
                "sexe": j["sexe"], "categorie": categorie_courte(titre), "categorie_long": titre,
                "loisir": j["compteur"] == "L", "classement": None, "points": None,
                "points_mensuels": _entier(j["compteur"]), "meilleur": None, "renouvele": True,
            }
    for titre, liste in lire_liste_licencies(pages.get(liens["classements"]) or ""):
        for j in liste:
            if j["licence"] in joueurs:
                joueurs[j["licence"]]["classement"] = _entier(titre)
                joueurs[j["licence"]]["points_mensuels"] = joueurs[j["licence"]]["points_mensuels"] or _entier(j["compteur"])
    for titre, liste in lire_liste_licencies(pages.get(liens["etat"]) or ""):
        for j in liste:
            if j["licence"] in joueurs:
                joueurs[j["licence"]]["renouvele"] = not titre.lower().startswith("licences non")
    return [j for j in joueurs.values() if not j.pop("loisir")]

"""Données de la page adversaires.

- Structure (équipes de Vaires, poules, calendrier avec horaires, scores, classements des
  poules, compositions de toutes les équipes des clubs adverses) : API publique de la FFTT.
- Compléments (effectifs complets, catégories, licences loisir, meilleur classement, adresses
  des salles) : pingpocket.fr, s'il répond. Sinon l'effectif d'un club se limite aux joueurs
  déjà alignés cette phase, avec leurs points officiels.
"""

from datetime import date, datetime

from . import fftt, pingpocket
from .effectif import TRIS
from .reseau import HEURE, JOUR, ErreurReseau

SITE_PINGPOCKET = "www.pingpocket.fr"
MAX_HISTORIQUES = 150  # historiques téléchargés au plus par lancement (≈ 10 minutes)


def classement_poule(poule, rencontres, detail):
    """Classement d'une poule calculé à partir des résultats saisis (points de rencontre de la FFTT,
    puis rapport parties gagnées / parties perdues en cas d'égalité)."""
    equipes = {}
    for po in poule.get("poolOpponents", []):
        t = (po.get("opponent") or {}).get("team") or {}
        if t.get("name"):
            equipes[t["name"]] = {"libelle": t["name"], "club": fftt.club_de(t)[0],
                                  "numero": t.get("position") or fftt.numero_equipe(t["name"]),
                                  "points": 0, "joues": 0, "v": 0, "n": 0, "d": 0, "pg": 0, "pp": 0}
    for r in rencontres:
        d = detail.get(r["id"])
        if not d:
            continue
        for cote, autre in (("home", "away"), ("away", "home")):
            e = equipes.get(fftt.equipe(d, f"{cote}Opponent").get("name"))
            if e is None:
                continue
            pour, contre = d.get(f"{cote}GamePoints") or 0, d.get(f"{autre}GamePoints") or 0
            e["joues"] += 1
            e["points"] += d.get(f"{cote}Points") or 0
            e["pg"] += pour
            e["pp"] += contre
            e["v" if pour > contre else "n" if pour == contre else "d"] += 1
    ordre = sorted(equipes.values(), key=lambda e: (-e["points"], -(e["pg"] / e["pp"] if e["pp"] else e["pg"] * 1000)))
    precedent, rang = None, 0
    for i, e in enumerate(ordre, 1):
        cle = (e["points"], e["pg"], e["pp"])
        rang = rang if cle == precedent else i
        e["rang"], precedent = rang, cle
    return ordre


def _joueur_feuille(j, feminin):
    """Joueur connu seulement par les feuilles de match (pas d'effectif pingpocket)."""
    pts = j["points"]
    return {
        "id": j["licence"], "licence": j["licence"], "nom": j["nom_famille"], "prenom": j["prenom"],
        "sexe": "F" if feminin else None, "categorie": None, "categorie_long": None,
        "classement": max(5, pts // 100) if pts else None, "points": pts, "points_mensuels": None,
        "meilleur": None, "renouvele": True,
    }


def equipes_et_compositions(numero, rencontres, detail, championnats):
    """Équipes d'un club (championnats demandés) et, pour chacune, qui a joué à chaque journée."""
    equipes, joueurs = {}, {}
    for r in rencontres:
        ch = "F" if fftt.feminin(r) else "M"
        if ch not in championnats:
            continue
        for cote in ("home", "away"):
            t = fftt.equipe(r, f"{cote}Opponent")
            if not t.get("name") or fftt.club_de(t)[0] != numero:
                continue
            eq = equipes.setdefault((t["name"], ch), {
                "libelle": t["name"], "numero": fftt.numero_equipe(t["name"]), "championnat": ch,
                "division": fftt.libelle_division(r["division"]["name"]), "compositions": []})
            d = detail.get(r["id"])
            if not d:
                continue
            ids = []
            for ligne in d.get(f"{cote}SheetMatches") or []:
                j = fftt.joueur(ligne.get("player") or {})
                if not j["licence"]:
                    continue
                ids.append(j["licence"])
                vu = joueurs.setdefault(j["licence"], _joueur_feuille(j, ch == "F"))
                if ch == "F":
                    vu["sexe"] = "F"
            eq["compositions"].append({"journee": d["day"]["position"], "date": d["date"][:10], "joueurs": ids})
    liste = sorted(equipes.values(), key=lambda e: (e["championnat"], e["numero"] or 0))
    return liste, joueurs


def recuperer(client, numero_club="08770250", aujourdhui=None, dossier_import=None):
    aujourdhui = aujourdhui or date.today()
    auj = aujourdhui.isoformat()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)

    # 1. Équipes du club, poules, calendrier et résultats
    print(f"1/5 Équipes, poules et calendrier du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
    id_club = fftt.id_interne_club(client, numero_club, debut)
    nos_equipes, nom_club = {}, numero_club
    for r in fftt.rencontres_club(client, id_club, debut, fin, ttl=3 * HEURE):
        for cote in ("homeOpponent", "awayOpponent"):
            t = fftt.equipe(r, cote)
            num, _, nom = fftt.club_de(t)
            if num == numero_club:
                nom_club = nom or nom_club
                nos_equipes.setdefault(t["name"], {
                    "poule": r["pool"]["id"], "division": r["division"]["name"],
                    "feminin": fftt.feminin(r), "numero": fftt.numero_equipe(t["name"]) or 0})
    poules = sorted({e["poule"] for e in nos_equipes.values()})
    infos = {p: fftt.lire(client, f"/pools/{p}", ttl=JOUR) for p in poules}
    rencontres_poules = {p: fftt.rencontres_poule(client, p, ttl=3 * HEURE) for p in poules}
    detail = fftt.details(client, [r for rs in rencontres_poules.values() for r in rs], auj)

    salles, numeros = {}, {}
    for info in infos.values():
        for po in info.get("poolOpponents", []):
            t = (po.get("opponent") or {}).get("team") or {}
            if t.get("name"):
                salles[t["name"]] = (t.get("sportHall") or {}).get("name")
                numeros[t["name"]] = t.get("position") or fftt.numero_equipe(t["name"])

    equipes, clubs_adv = [], {}
    for nom, e in sorted(nos_equipes.items(), key=lambda x: (x[1]["feminin"], x[1]["numero"])):
        ch = "F" if e["feminin"] else "M"
        rencontres = []
        for r in rencontres_poules[e["poule"]]:
            dom, ext = fftt.equipe(r, "homeOpponent"), fftt.equipe(r, "awayOpponent")
            if nom not in (dom.get("name"), ext.get("name")):
                continue
            chez_nous = dom.get("name") == nom
            adv = ext if chez_nous else dom
            adv_num, adv_id, adv_nom = fftt.club_de(adv)
            if adv.get("name") and adv_num:
                clubs_adv.setdefault(adv_num, {"id": adv_id, "nom": adv_nom, "championnats": set()})["championnats"].add(ch)
            d = detail.get(r["id"])
            salle = salles.get(dom.get("name"))
            rencontres.append({
                "journee": r["day"]["position"], "date": r["date"][:10], "date_reelle": None, "heure": fftt.heure(r),
                "domicile": {"libelle": dom.get("name"), "club": fftt.club_de(dom)[0]},
                "exterieur": {"libelle": ext.get("name"), "club": fftt.club_de(ext)[0]},
                "vaires_domicile": chez_nous,
                "score": [d["homeGamePoints"], d["awayGamePoints"]] if d else None,
                "adversaire": {"club": adv_num, "libelle": adv["name"], "numero": numeros.get(adv["name"])}
                              if adv.get("name") else None,
                "salle": {"nom": salle} if salle else None,
            })
        rencontres.sort(key=lambda x: (x["journee"], x["date"]))
        equipes.append({
            "id": f"v{e['numero']}{'f' if e['feminin'] else ''}", "libelle": nom,
            "nom_court": f"Vaires {e['numero']}{' F' if e['feminin'] else ''}", "numero": e["numero"],
            "championnat": ch, "division": fftt.libelle_division(e["division"]),
            "poule": f"Poule {infos[e['poule']].get('name', '')}".strip(),
            "jour": fftt.jour_habituel([x["date"] for x in rencontres]), "rencontres": rencontres,
            "classement": classement_poule(infos[e["poule"]], rencontres_poules[e["poule"]], detail),
        })

    # 2 et 3. Clubs adverses : toutes leurs équipes et leurs feuilles de match
    print(f"2/5 Clubs adverses : {len(clubs_adv)} (API FFTT)", flush=True)
    rencontres_clubs = {}
    for i, (num, c) in enumerate(sorted(clubs_adv.items()), 1):
        try:
            rencontres_clubs[num] = fftt.rencontres_club(client, c["id"], debut, fin, ttl=3 * HEURE)
        except ErreurReseau as err:
            print(f"  ! {err}")
            rencontres_clubs[num] = []
        if i % 10 == 0 or i == len(clubs_adv):
            print(f"  clubs : {i}/{len(clubs_adv)}", flush=True)
    print("3/5 Feuilles de match des équipes adverses (API FFTT)", flush=True)
    a_detailler = [r for num, rs in rencontres_clubs.items() for r in rs
                   if ("F" if fftt.feminin(r) else "M") in clubs_adv[num]["championnats"]]
    detail.update(fftt.details(client, a_detailler, auj))

    clubs = {}
    for num, c in clubs_adv.items():
        equipes_club, joueurs = equipes_et_compositions(num, rencontres_clubs[num], detail, c["championnats"])
        clubs[num] = {"numero": num, "nom": c["nom"], "salle": None, "joueurs": list(joueurs.values()),
                      "equipes": equipes_club, "effectif_complet": False}

    donnees = {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "club": {"numero": numero_club, "nom": nom_club, "salle": None},
        "equipes": equipes, "clubs": clubs, "sources": {"pingpocket": False},
    }
    completer_avec_pingpocket(client, donnees, dossier_import)
    return donnees


def completer_avec_pingpocket(client, donnees, dossier_import=None):
    """Effectifs complets, catégories, meilleur classement et adresses des salles (pingpocket.fr).

    Les listes de licenciés enregistrées depuis un navigateur dans le dossier import complètent
    (ou remplacent, si elles sont plus récentes) celles du site."""
    print("4/5 Compléments pingpocket.fr : effectifs complets, catégories, adresses des salles", flush=True)
    numero_club = donnees["club"]["numero"]
    clubs = donnees["clubs"]
    importees, ignores = pingpocket.listes_du_dossier(dossier_import) if dossier_import else ({}, [])
    for nom in ignores:
        print(f"  ! import : aucune liste de licenciés dans « {nom} » (enregistrer en « Page Web, complète »)")
    liens = {num: {"salle": f"/app/fftt/clubs/{num}/coordonnees",
                   **{t: f"/app/fftt/clubs/{num}/licencies?SORT={tri}" for t, tri in TRIS.items()}} for num in clubs}
    try:
        donnees["club"]["salle"] = pingpocket.lire_salle(client.get(f"/app/fftt/clubs/{numero_club}/coordonnees", 30 * JOUR))
    except ErreurReseau as err:
        print(f"  ! pingpocket.fr indisponible ({err}).")
        pages = {}
    else:
        pages = client.get_plusieurs([u for l in liens.values() for u in l.values()], ttl=JOUR, message="pages clubs")
    complets = importes = 0
    for num, club in clubs.items():
        l = liens[num]
        if pages.get(l["salle"]):
            club["salle"] = pingpocket.lire_salle(pages[l["salle"]])
        listes = {t: pages[l[t]] for t in TRIS if pages.get(l[t])}
        for t, imp in importees.get(num, {}).items():
            if t not in listes or imp["date"] > (client.date(l[t]) or 0):
                listes[t] = imp["html"]
                club["import"] = imp["fichier"]
        if not ("categories" in listes and "etat" in listes):
            continue
        complets += 1
        importes += "import" in club
        club["effectif_complet"] = True
        vus = {j["id"]: j for j in club["joueurs"]}
        effectif = pingpocket.effectif(listes, {t: t for t in TRIS})
        for j in effectif:
            if j["id"] in vus:  # points officiels de la feuille de match, sexe du championnat féminin
                j["points"] = vus[j["id"]]["points"]
                j["sexe"] = j["sexe"] or vus[j["id"]]["sexe"]
        connus = {j["id"] for j in effectif}
        club["joueurs"] = effectif + [j for j in club["joueurs"] if j["id"] not in connus]
    donnees["sources"]["pingpocket"] = complets > 0
    print(f"  effectifs complets : {complets}/{len(clubs)} clubs" + (f" (dont {importes} par le dossier import)" if importes else ""),
          flush=True)
    if complets < len(clubs):
        print("    Effectifs manquants : la page les limite aux joueurs déjà alignés. Ils se complètent aux lancements")
        print("    suivants, ou en enregistrant les listes du club dans le dossier import (voir import/LISEZ-MOI.txt).")
    if not client.disponible(SITE_PINGPOCKET) or not pages:
        print("  ! pingpocket.fr ne répond pas : meilleurs classements non récupérés.")
        return

    # 5. Meilleur classement : historique des joueurs (gardé 20 jours en cache). Les joueurs restés à
    # 500 points qui n'ont pas joué n'ont en pratique jamais été mieux classés : on épargne ces pages.
    alignes = {jid for club in clubs.values() for e in club["equipes"]
               for compo in e["compositions"] for jid in compo["joueurs"]}
    a_lire = [j for club in clubs.values() for j in club["joueurs"]
              if j["renouvele"] and ((j["points_mensuels"] or j["points"] or 0) > 500 or j["id"] in alignes)]
    a_lire.sort(key=lambda j: (j["id"] not in alignes, -(j["points_mensuels"] or j["points"] or 0)))
    chemin = "/app/fftt/licencies/{}/graphiques/historique-classement"
    # Une page toutes les 4 secondes : on en lit au plus MAX_HISTORIQUES par lancement (les joueurs
    # alignés d'abord) ; les suivants sont lus aux lancements suivants (gardés 20 jours en cache).
    a_telecharger = [j for j in a_lire if not client.en_cache(chemin.format(j["licence"]), 20 * JOUR)]
    reportes = {j["id"] for j in a_telecharger[MAX_HISTORIQUES:]}
    a_lire = [j for j in a_lire if j["id"] not in reportes]
    print(f"5/5 Historiques des joueurs : {len(a_lire)} (pingpocket.fr)"
          + (f", {len(reportes)} reportés au prochain lancement" if reportes else ""), flush=True)
    pages = client.get_plusieurs([chemin.format(j["licence"]) for j in a_lire], ttl=20 * JOUR, message="historiques")
    for j in a_lire:
        html = pages.get(chemin.format(j["licence"]))
        if html:
            officiels, meilleur = pingpocket.resume_historique(pingpocket.lire_historique(html))
            j["points"] = j["points"] or officiels
            j["meilleur"] = meilleur
            if j["classement"] is None and j["points"]:
                j["classement"] = max(5, j["points"] // 100)

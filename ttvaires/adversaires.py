"""Données de la page adversaires.

- Structure (équipes de Vaires, poules, calendrier avec horaires, scores, classements des
  poules, compositions de toutes les équipes des clubs adverses) : API publique de la FFTT.
- Compléments (effectifs complets, catégories, licences loisir, meilleur classement, adresses
  des salles) : pingpocket.fr, s'il répond. Sinon l'effectif d'un club se limite aux joueurs
  déjà alignés cette phase, avec leurs points officiels.
"""

import json
import time
from datetime import date, datetime
from pathlib import Path

from . import fftt, pingpocket
from .effectif import TRIS, suivre_inscrits
from .reseau import HEURE, JOUR, ErreurReseau
from .verifications import bilan_club, bilan_rencontres
from .virtuel import forme_joueurs

SITE_PINGPOCKET = "www.pingpocket.fr"
MAX_HISTORIQUES = 150  # historiques téléchargés au plus par lancement (≈ 10 minutes)


def classement_poule(poule, rencontres, detail):
    """Classement d'une poule calculé à partir des résultats saisis (points de rencontre de la FFTT,
    puis rapport PG / PP en cas d'égalité). PG / PP : points gagnés / perdus, c'est-à-dire le cumul
    des scores des rencontres (21-21...), comme sur le site de la FFTT. En plus, d'après les feuilles
    de match : manches gagnées / perdues (sg / sp) et points marqués / encaissés dans les manches
    (pm / pe) ; sans_detail compte les parties jouées dont les manches n'ont pas été saisies."""
    equipes = {}
    for po in poule.get("poolOpponents", []):
        t = (po.get("opponent") or {}).get("team") or {}
        if t.get("name"):
            equipes[t["name"]] = {"libelle": t["name"], "club": fftt.club_de(t)[0],
                                  "numero": t.get("position") or fftt.numero_equipe(t["name"]),
                                  "points": 0, "joues": 0, "v": 0, "n": 0, "d": 0, "pg": 0, "pp": 0,
                                  "sg": 0, "sp": 0, "pm": 0, "pe": 0, "sans_detail": 0}
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
            for g in d.get("games") or []:
                sets = [(s.get(f"{cote}Score"), s.get(f"{autre}Score")) for s in g.get("sets") or []]
                sets = [(a, b) for a, b in sets if a is not None and b is not None]
                if not sets and g.get("winner") in ("home", "away") and not g.get("forfeit"):
                    e["sans_detail"] += 1
                for a, b in sets:
                    e["sg"] += a > b
                    e["sp"] += b > a
                    e["pm"] += a
                    e["pe"] += b
    ordre = sorted(equipes.values(), key=lambda e: (-e["points"], -(e["pg"] / e["pp"] if e["pp"] else e["pg"] * 1000)))
    precedent, rang = None, 0
    for i, e in enumerate(ordre, 1):
        cle = (e["points"], e["pg"], e["pp"])
        rang = rang if cle == precedent else i
        e["rang"], precedent = rang, cle
    return ordre


def derniere_journee(donnees):
    """Dernière journée dont un résultat d'une équipe de Vaires est connu (0 avant la J1)."""
    return max((r["journee"] for e in donnees.get("equipes", []) for r in e.get("rencontres", [])
                if r.get("score")), default=0)


def donnees_classements(donnees):
    """Page et image des classements des poules (classements.py) : les classements seuls, aucun nom de joueur."""
    club = donnees["club"]["numero"]
    poules = []
    for e in donnees.get("equipes", []):
        if not e.get("classement"):
            continue
        poules.append({
            "equipe": e["nom_court"], "libelle": e["libelle"], "division": e.get("division") or "",
            "poule": e.get("poule") or "", "championnat": e.get("championnat"),
            "lignes": [{"rang": c["rang"], "libelle": c["libelle"], "points": c["points"], "joues": c["joues"],
                        "v": c["v"], "n": c["n"], "d": c["d"], "pg": c.get("pg", 0), "pp": c.get("pp", 0),
                        **{k: c.get(k, 0) for k in ("sg", "sp", "pm", "pe", "sans_detail")},
                        "nous": c.get("club") == club}
                       for c in e["classement"]],
        })
    sortie = {"club": {"numero": club, "nom": donnees["club"].get("nom", "")}, "saison": donnees["saison"],
              "phase": donnees["phase"], "genere_le": donnees.get("genere_le"),
              "journee": derniere_journee(donnees), "poules": poules}
    if donnees.get("date_reference"):
        sortie["date_reference"] = donnees["date_reference"]
    return sortie


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
            ids, lettres, points = [], {}, {}
            for ligne in d.get(f"{cote}SheetMatches") or []:
                j = fftt.joueur(ligne.get("player") or {})
                if not j["licence"]:
                    continue
                ids.append(j["licence"])
                if ligne.get("identifier"):
                    lettres[j["licence"]] = ligne["identifier"]
                points[j["licence"]] = j["points"]
                vu = joueurs.setdefault(j["licence"], _joueur_feuille(j, ch == "F"))
                if ch == "F":
                    vu["sexe"] = "F"
            # Lettres de la feuille (A, B, C, D pour l'équipe qui reçoit, W, X, Y, Z pour l'autre ;
            # A, B, C / X, Y, Z à trois joueurs) : le placement choisi par le capitaine.
            toutes = {x.get("identifier") for c in ("home", "away") for x in d.get(f"{c}SheetMatches") or []}
            autre = fftt.equipe(r, "awayOpponent" if cote == "home" else "homeOpponent")
            eq["compositions"].append({"journee": d["day"]["position"], "date": d["date"][:10], "joueurs": ids,
                                       "lettres": lettres, "points": points, "domicile": cote == "home",
                                       "contre": autre.get("name"), "format": 4 if toutes & {"D", "W"} else 3})
    liste = sorted(equipes.values(), key=lambda e: (e["championnat"], e["numero"] or 0))
    return liste, joueurs


def recuperer(client, numero_club="08770250", aujourdhui=None, dossier_import=None, tous_les_historiques=False,
              fichier_etat=None):
    aujourdhui = aujourdhui or date.today()
    auj = aujourdhui.isoformat()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)

    # 1. Équipes du club, poules, calendrier et résultats
    print(f"1/6 Équipes, poules et calendrier du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
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
    etats = {}  # état de chaque rencontre jouée (complet, non saisi...) pour les vérifications
    detail = fftt.details(client, [r for rs in rencontres_poules.values() for r in rs], auj, etats)

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
    print(f"2/6 Clubs adverses : {len(clubs_adv)} (API FFTT)", flush=True)
    rencontres_clubs, erreurs = {}, {}
    for i, (num, c) in enumerate(sorted(clubs_adv.items()), 1):
        try:
            rencontres_clubs[num] = fftt.rencontres_club(client, c["id"], debut, fin, ttl=3 * HEURE)
        except ErreurReseau as err:
            print(f"  ! {err}")
            rencontres_clubs[num] = []
            erreurs[num] = "rencontres du club non récupérées (l'API FFTT n'a pas répondu) : relancer"
        if i % 10 == 0 or i == len(clubs_adv):
            print(f"  clubs : {i}/{len(clubs_adv)}", flush=True)
    print("3/6 Feuilles de match des équipes adverses (API FFTT)", flush=True)
    suivies = {num: [r for r in rs if ("F" if fftt.feminin(r) else "M") in clubs_adv[num]["championnats"]]
               for num, rs in rencontres_clubs.items()}
    a_detailler = [r for rs in suivies.values() for r in rs]
    detail.update(fftt.details(client, a_detailler, auj, etats))

    clubs = {}
    for num, c in clubs_adv.items():
        equipes_club, joueurs = equipes_et_compositions(num, rencontres_clubs[num], detail, c["championnats"])
        clubs[num] = {"numero": num, "nom": c["nom"], "salle": None, "joueurs": list(joueurs.values()),
                      "equipes": equipes_club, "effectif_complet": False}

    donnees = {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "club": {"numero": numero_club, "nom": nom_club, "salle": None},
        "equipes": equipes, "clubs": clubs, "sources": {"pingpocket": False},
        "verification": verification(numero_club, nom_club, rencontres_poules, suivies, clubs_adv, etats, erreurs, auj),
    }
    completer_avec_pingpocket(client, donnees, dossier_import, tous_les_historiques, fichier_etat)
    ajouter_forme(client, donnees, detail, debut, min(fin, auj), auj)
    return donnees


def joueurs_a_suivre(donnees, auj):
    """Joueurs des clubs que Vaires doit encore rencontrer (rencontre à venir ou pas encore saisie) dont
    on lit la forme : ceux déjà alignés cette phase, et les licenciés réinscrits à plus de 500 points
    (ils peuvent jouer critérium ou tournois sans avoir encore joué en championnat). {licence: [fiches]}."""
    a_venir = {r["adversaire"]["club"] for e in donnees["equipes"] for r in e["rencontres"]
               if r.get("adversaire") and (not r.get("score") or r["date"] > auj)}
    joueurs = {}
    for num in sorted(a_venir):
        club = donnees["clubs"].get(num)
        if not club:
            continue
        alignes = {jid for e in club["equipes"] for c in e["compositions"] for jid in c["joueurs"]}
        for j in club["joueurs"]:
            if j["id"] in alignes or (j.get("renouvele") and (j.get("points_mensuels") or j.get("points") or 0) > 500):
                joueurs.setdefault(j["id"], []).append(j)
    return a_venir, joueurs


def ajouter_forme(client, donnees, detail, debut, fin, auj):
    """Forme des joueurs adverses (j["forme"]) : victoires, défaites et points gagnés ou perdus depuis
    le début de la phase, toutes compétitions (championnat, critérium fédéral, tournois...)."""
    a_venir, joueurs = joueurs_a_suivre(donnees, auj)
    print(f"6/6 Forme des joueurs adverses (toutes compétitions) : {len(joueurs)} joueurs des {len(a_venir)} clubs "
          "encore à rencontrer (API FFTT)", flush=True)
    formes = forme_joueurs(client, list(joueurs), detail, debut, fin) if joueurs else {}
    for lic, fiches in joueurs.items():
        for j in fiches:
            j["forme"] = formes.get(lic)
    muets = sum(1 for f in formes.values() if f is None)
    donnees["sources"]["forme"] = {"joueurs": len(joueurs), "clubs": len(a_venir), "sans_reponse": muets, "debut": debut}
    if muets:
        print(f"  ! parties non lues pour {muets} joueurs (API FFTT) : leur forme manque, relancer plus tard", flush=True)


def verification(numero_club, nom_club, rencontres_poules, suivies, clubs_adv, etats, erreurs, auj):
    """Les résultats de chaque journée ont-ils tous été récupérés ? Bilan par journée (toutes les
    rencontres des poules de Vaires et des clubs adverses) et par club, équipe par équipe."""
    poules = [r for rs in rencontres_poules.values() for r in rs]
    clubs = [bilan_club(poules, etats, auj, numero_club, nom_club)]
    for num, c in sorted(clubs_adv.items(), key=lambda x: x[1]["nom"] or ""):
        b = bilan_club(suivies[num], etats, auj, num, c["nom"])
        b["erreur"] = erreurs.get(num)
        clubs.append(b)
    return {"journees": bilan_rencontres(poules + [r for rs in suivies.values() for r in rs], etats, auj),
            "clubs": clubs}


def _memoriser_listes_en_cache(client, clubs, liens, etats):
    """Club adverse sans liste mémorisée (premier lancement de ce suivi) : la liste déjà en cache,
    celle du lancement précédent, sert de référence avant d'être relue. Les inscrits arrivés depuis
    sont ainsi « nouveaux » dès ce lancement. Renvoie True si l'état a changé."""
    lire = getattr(client, "lu_en_cache", None)
    if etats is None or lire is None:
        return False
    change = False
    for num in clubs:
        if num in etats:
            continue
        lues = {t: lire(liens[num][t]) for t in TRIS}
        listes = {t: texte for t, (texte, _) in lues.items() if texte}
        if not ("categories" in listes and "etat" in listes):
            continue
        actuels = sorted(j["id"] for j in pingpocket.effectif(listes, {t: t for t in TRIS}) if j.get("renouvele"))
        date_liste = datetime.fromtimestamp(min(d for _, d in lues.values() if d)).isoformat(timespec="minutes")
        etats[num] = {"date": date_liste, "renouveles": actuels, "avant": None}
        change = True
    return change


def completer_avec_pingpocket(client, donnees, dossier_import=None, tous_les_historiques=False, fichier_etat=None):
    """Effectifs complets, catégories, meilleur classement et adresses des salles (pingpocket.fr).

    Les listes de licenciés enregistrées depuis un navigateur dans le dossier import complètent
    (ou remplacent, si elles sont plus récentes) celles du site. Chaque club reçoit la date de sa
    liste (date_effectif) ; avec `fichier_etat` (état mémorisé, envoyé par le PC comme celui de la
    page effectif), les joueurs inscrits ou réinscrits depuis la liste précédente du club sont
    marqués « nouveau » (reference_nouveaux : date de cette liste précédente)."""
    print("4/6 Compléments pingpocket.fr : effectifs complets, catégories, adresses des salles", flush=True)
    numero_club = donnees["club"]["numero"]
    clubs = donnees["clubs"]
    importees, ignores = pingpocket.listes_du_dossier(dossier_import) if dossier_import else ({}, [])
    for nom in ignores:
        print(f"  ! import : aucune liste de licenciés dans « {nom} » (enregistrer en « Page Web, complète »)")
    liens = {num: {"salle": f"/app/fftt/clubs/{num}/coordonnees",
                   **{t: f"/app/fftt/clubs/{num}/licencies?SORT={tri}" for t, tri in TRIS.items()}} for num in clubs}
    fichier = Path(fichier_etat) if fichier_etat else None
    etats = (json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}) if fichier else None
    change = _memoriser_listes_en_cache(client, clubs, liens, etats)
    try:
        donnees["club"]["salle"] = pingpocket.lire_salle(
            client.get(f"/app/fftt/clubs/{numero_club}/coordonnees", 30 * JOUR, perime_si_erreur=True))
    except ErreurReseau as err:
        print(f"  ! pingpocket.fr indisponible ({err}).")
        pages = {}
    else:
        # Si le site ne répond plus, la dernière copie téléchargée sert (sur le PC comme en ligne,
        # où les pages de pingpocket sont celles envoyées par le PC).
        pages = client.get_plusieurs([u for l in liens.values() for u in l.values()], ttl=JOUR, message="pages clubs",
                                     perime_si_erreur=True)
    complets = importes = 0
    for num, club in clubs.items():
        l = liens[num]
        if pages.get(l["salle"]):
            club["salle"] = pingpocket.lire_salle(pages[l["salle"]])
        listes = {t: pages[l[t]] for t in TRIS if pages.get(l[t])}
        dates = {t: client.date(l[t]) for t in listes}
        for t, imp in importees.get(num, {}).items():
            if t not in listes or imp["date"] > (client.date(l[t]) or 0):
                listes[t] = imp["html"]
                dates[t] = imp["date"]
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
        connues = [d for d in dates.values() if d]
        club["date_effectif"] = datetime.fromtimestamp(min(connues)).isoformat(timespec="minutes") if connues else None
        if etats is not None and club["date_effectif"]:
            actuels = sorted(j["id"] for j in effectif if j.get("renouvele"))
            nouveaux, etat, reference = suivre_inscrits(etats.get(num), actuels, club["date_effectif"])
            if reference:
                club["reference_nouveaux"] = reference
                for j in club["joueurs"]:
                    j["nouveau"] = j["id"] in nouveaux
            if etat:
                etats[num], change = etat, True
    donnees["sources"]["pingpocket"] = complets > 0
    if change:
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps(etats), encoding="utf-8")
    nb_nouveaux = sum(1 for c in clubs.values() for j in c["joueurs"] if j.get("nouveau"))
    if nb_nouveaux:
        print(f"  nouveaux inscrits dans les clubs adverses (depuis leur liste précédente) : {nb_nouveaux}", flush=True)
    print(f"  effectifs complets : {complets}/{len(clubs)} clubs" + (f" (dont {importes} par le dossier import)" if importes else ""),
          flush=True)
    if complets < len(clubs):
        print("    Effectifs manquants : la page les limite aux joueurs déjà alignés. Ils se complètent aux lancements")
        print("    suivants, ou en enregistrant les listes du club dans le dossier import (voir import/LISEZ-MOI.txt).")
    if not pages:
        print("  ! aucune page de pingpocket.fr disponible : meilleurs classements non récupérés.")
        return
    muet = not client.disponible(SITE_PINGPOCKET) or SITE_PINGPOCKET in client.sites_cache_seul or client.hors_ligne

    # 5. Meilleur classement : historique des joueurs (gardé en cache toute la phase). Les joueurs restés à
    # 500 points qui n'ont pas joué n'ont en pratique jamais été mieux classés : on épargne ces pages.
    alignes = {jid for club in clubs.values() for e in club["equipes"]
               for compo in e["compositions"] for jid in compo["joueurs"]}
    a_lire = [j for club in clubs.values() for j in club["joueurs"]
              if j["renouvele"] and ((j["points_mensuels"] or j["points"] or 0) > 500 or j["id"] in alignes)]
    a_lire.sort(key=lambda j: (j["id"] not in alignes, -(j["points_mensuels"] or j["points"] or 0)))
    chemin = "/app/fftt/licencies/{}/graphiques/historique-classement"
    # Une page toutes les 4 secondes : on en lit au plus MAX_HISTORIQUES par lancement (les joueurs
    # alignés d'abord) ; les suivants sont lus aux lancements suivants.
    # Le meilleur classement et les points officiels ne changent qu'aux changements de phase (janvier et
    # juillet) : un historique lu depuis le début de la phase reste bon, les lancements le complètent.
    debut_phase = datetime.fromisoformat(fftt.bornes_phase(date.today())[0]).timestamp()
    ttl_historique = max(JOUR, time.time() - debut_phase)
    a_telecharger = [] if muet else [j for j in a_lire if not client.en_cache(chemin.format(j["licence"]), ttl_historique)]
    reportes = set() if tous_les_historiques else {j["id"] for j in a_telecharger[MAX_HISTORIQUES:]}
    a_lire = [j for j in a_lire if j["id"] not in reportes]
    print(f"5/6 Historiques des joueurs : {len(a_lire)} ("
          + ("pages déjà téléchargées, pingpocket.fr non interrogé" if muet else "pingpocket.fr") + ")"
          + (f", {len(reportes)} reportés au prochain lancement" if reportes else ""), flush=True)
    a_lire_en_ligne = len(a_telecharger) - len(reportes)
    if a_lire_en_ligne > 30:
        print(f"  {a_lire_en_ligne} historiques à télécharger : environ {a_lire_en_ligne * 4 // 60 + 1} minutes "
              "(une page toutes les 4 secondes). On peut fermer la fenêtre : ce qui est lu est gardé.", flush=True)
    pages = client.get_plusieurs([chemin.format(j["licence"]) for j in a_lire], ttl=ttl_historique, message="historiques",
                                 perime_si_erreur=True)
    for j in a_lire:
        html = pages.get(chemin.format(j["licence"]))
        if html:
            officiels, meilleur = pingpocket.resume_historique(pingpocket.lire_historique(html))
            j["points"] = j["points"] or officiels
            j["meilleur"] = meilleur
            if j["classement"] is None and j["points"]:
                j["classement"] = max(5, j["points"] // 100)
    donnees["sources"]["historiques_restants"] = len(reportes)
    if reportes:
        print(f"  Il reste {len(reportes)} meilleurs classements à lire : ils se complètent au fil des lancements,")
        print(f"  ou d'un coup avec l'option 8 du menu (environ {len(reportes) * 4 // 60 + 1} minutes, une seule fois).")

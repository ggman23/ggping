"""Effectif du club et brûlages (page « Effectif de Vaires »).

- Matchs joués par chaque joueur, équipe par équipe : feuilles de match de l'API FFTT.
- Liste des licenciés (réinscrits, non réinscrits, licences loisir, catégories) : pingpocket.fr,
  revérifiée à chaque lancement, ou pages de ces listes enregistrées depuis un navigateur dans le
  dossier import (quand le site bloque l'outil). La version la plus récente l'emporte, la
  dernière copie en cache servant de secours ; à défaut, seuls les joueurs déjà alignés sont connus.

Brûlage : championnat masculin et championnat féminin sont indépendants. Une joueuse alignée en
masculin y est traitée comme les garçons (ses matchs en équipe féminine ne comptent pas).
"""

import json
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from . import fftt, pingpocket
from .brulage import brulage_par_equipe, equipe_max
from .reseau import HEURE

# Listes de licenciés de pingpocket : type -> tri demandé dans l'adresse de la page
TRIS = {"categories": "CATEGORY", "etat": "LICENCE_STATE", "classements": "OFFICIAL_RANK"}
NOMS_LISTES = {"categories": "par catégorie d'âge", "etat": "par licences à jour",
               "classements": "par classement officiel (facultatif)"}


def liens_navigateur(numero_club):
    """Adresses des listes de licenciés à ouvrir dans un navigateur (pour le dossier import)."""
    return {type_: f"https://www.pingpocket.fr/?page=app%2Ffftt%2Fclubs%2F{numero_club}%2Flicencies%3FSORT%3D{tri}"
            for type_, tri in TRIS.items()}


def _joueur_feuille(j):
    pts = j["points"]
    return {
        "id": j["licence"], "licence": j["licence"], "nom": j["nom_famille"], "prenom": j["prenom"],
        "sexe": None, "categorie": None, "categorie_long": None, "loisir": False,
        "classement": max(5, pts // 100) if pts else None, "points": pts, "points_mensuels": None,
        "renouvele": True,
    }


def recuperer_effectif(client, numero_club="08770250", aujourdhui=None, fichier_etat=None, dossier_import=None):
    aujourdhui = aujourdhui or date.today()
    auj = aujourdhui.isoformat()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)

    print(f"1/2 Équipes et feuilles de match du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
    id_club = fftt.id_interne_club(client, numero_club, debut)
    rencontres = fftt.rencontres_club(client, id_club, debut, fin, ttl=HEURE)
    detail = fftt.details(client, rencontres, auj)

    equipes, vus, parts, prochaines, nom_club = {}, {}, defaultdict(list), {}, numero_club
    for r in rencontres:
        ch = "F" if fftt.feminin(r) else "M"
        for cote in ("home", "away"):
            t = fftt.equipe(r, f"{cote}Opponent")
            num, _, nom = fftt.club_de(t)
            if num != numero_club:
                continue
            nom_club = nom or nom_club
            n = fftt.numero_equipe(t["name"]) or 0
            equipes.setdefault((ch, n), {
                "id": f"v{n}{'f' if ch == 'F' else ''}", "libelle": t["name"], "numero": n, "championnat": ch,
                "nom_court": f"Vaires {n}{' F' if ch == 'F' else ''}", "division": fftt.libelle_division(r["division"]["name"])})
            d = detail.get(r["id"])
            if d is None:
                if r["date"][:10] >= auj and (ch not in prochaines or r["date"][:10] < prochaines[ch]["date"]):
                    prochaines[ch] = {"journee": r["day"]["position"], "date": r["date"][:10], "heure": fftt.heure(r)}
                continue
            for ligne in d.get(f"{cote}SheetMatches") or []:
                j = fftt.joueur(ligne.get("player") or {})
                if not j["licence"]:
                    continue
                parts[j["licence"]].append({"journee": d["day"]["position"], "date": d["date"][:10],
                                            "numero": n, "championnat": ch})
                vu = vus.setdefault(j["licence"], _joueur_feuille(j))
                vu["points"] = j["points"] or vu["points"]
                if ch == "F":
                    vu["sexe"] = "F"

    print("2/2 Licenciés du club : réinscriptions, licences loisir (pingpocket.fr)", flush=True)
    liens = {type_: f"/app/fftt/clubs/{numero_club}/licencies?SORT={tri}" for type_, tri in TRIS.items()}
    pages = client.get_plusieurs(list(liens.values()), ttl=HEURE, perime_si_erreur=True)
    listes = {type_: {"html": pages[u], "date": client.date(u) or time.time(), "origine": "cache" if u in client.perimes else "pingpocket"}
              for type_, u in liens.items() if pages.get(u)}
    for type_, importee in _listes_importees(dossier_import, numero_club).items():
        if type_ not in listes or importee["date"] > listes[type_]["date"]:
            listes[type_] = {**importee, "origine": "import"}
    source = _source(listes, numero_club)
    liste = pingpocket.licencies({t: l["html"] for t, l in listes.items()}, {t: t for t in TRIS}) if source["liste"] else []
    _annoncer(source)

    joueurs = {j["id"]: j for j in liste}
    for lic, vu in vus.items():
        if lic in joueurs:  # points officiels de la feuille ; un joueur aligné est forcément réinscrit
            j = joueurs[lic]
            j["points"] = vu["points"]
            j["sexe"] = j["sexe"] or vu["sexe"]
            j["renouvele"], j["loisir"] = True, False
        else:
            joueurs[lic] = vu

    numeros_m = sorted(n for ch, n in equipes if ch == "M")
    for j in joueurs.values():
        matchs = sorted(parts.get(j["id"], []), key=lambda p: (p["date"], p["numero"]))
        masculin = [p for p in matchs if p["championnat"] == "M"]
        j["matchs"] = [{"j": p["journee"], "n": p["numero"], "ch": p["championnat"], "d": p["date"]} for p in matchs]
        j["brulage"] = brulage_par_equipe(masculin, numeros_m)
        j["equipe_max"] = equipe_max(masculin)
        habituelles = Counter(p["numero"] for p in masculin).most_common(1)
        j["habituelle"] = habituelles[0][0] if habituelles else None

    precedent = _nouveaux(joueurs, fichier_etat, source)
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "club": {"numero": numero_club, "nom": nom_club},
        "equipes": sorted(equipes.values(), key=lambda e: (e["championnat"] == "F", e["numero"])),
        "prochaines": prochaines, "source": source, "precedent": precedent,
        "joueurs": sorted(joueurs.values(), key=lambda j: -(j["points"] or j["points_mensuels"] or 0)),
    }


def _listes_importees(dossier, numero_club):
    """Listes du club trouvées dans les pages enregistrées depuis un navigateur (dossier import)."""
    if not dossier:
        return {}
    listes, ignores = pingpocket.listes_du_dossier(dossier)
    for nom in ignores:
        print(f"  ! import : aucune liste de licenciés dans « {nom} » (enregistrer en « Page Web, complète »)")
    return listes.get(numero_club, {})


def _iso(horodatage):
    return datetime.fromtimestamp(horodatage).isoformat(timespec="minutes")


def _source(listes, numero_club):
    """Provenance de la liste des licenciés, affichée dans la page.

    origine : « pingpocket » (lue à l'instant), « cache » (site muet : dernière liste obtenue),
    « import » (page enregistrée depuis un navigateur), None (aucune liste).
    """
    source = {"liste": "categories" in listes, "a_jour": False, "date": None, "origine": None,
              "manquantes": [t for t in TRIS if t not in listes], "fichiers": [],
              "liens": liens_navigateur(numero_club)}
    if source["liste"]:
        origines = {l["origine"] for l in listes.values()}
        source.update(
            a_jour=origines == {"pingpocket"},
            date=_iso(min(l["date"] for l in listes.values())),
            origine=next(o for o in ("import", "cache", "pingpocket") if o in origines),
            fichiers=sorted({l["fichier"] for l in listes.values() if l.get("fichier")}))
    return source


def _annoncer(source):
    date = (source["date"] or "")[:16].replace("T", " ")
    if source["origine"] == "import":
        print(f"  liste des licenciés : page(s) enregistrée(s) le {date} ({', '.join(source['fichiers'])})")
        print("    Réenregistre-les de temps en temps pour voir les nouvelles réinscriptions (import/LISEZ-MOI.txt).")
    elif source["origine"] == "cache":
        print(f"  ! pingpocket.fr ne répond pas : reprise de la liste du {date}")
    elif not source["liste"]:
        print("  ! Liste des licenciés indisponible : seuls les joueurs déjà alignés apparaissent.")
    if source["liste"] and "etat" in source["manquantes"]:
        print(f"  ! liste {NOMS_LISTES['etat']} absente : les non réinscrits ne peuvent pas être séparés.")
    if source["origine"] in (None, "cache"):
        print("    Pour une liste complète et récente : ouvre ces pages dans ton navigateur, enregistre-les")
        print("    (Ctrl+S, « Page Web, complète ») dans le dossier import de l'outil, puis relance :")
        for type_, lien in source["liens"].items():
            print(f"      {NOMS_LISTES[type_]} : {lien}")


def _nouveaux(joueurs, fichier_etat, source):
    """Marque les joueurs réinscrits depuis le lancement précédent et mémorise la liste actuelle."""
    if not fichier_etat or not source["liste"]:
        return None
    fichier = Path(fichier_etat)
    precedent = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else None
    actuels = sorted(j["id"] for j in joueurs.values() if j["renouvele"] and not j["loisir"])
    if precedent:
        nouveaux = set(actuels) - set(precedent["renouveles"])
        for j in joueurs.values():
            j["nouveau"] = j["id"] in nouveaux
    if precedent is None or source["date"] > precedent["date"]:  # liste plus récente que la mémorisée
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps({"date": source["date"], "renouveles": actuels}), encoding="utf-8")
    return precedent["date"] if precedent else None

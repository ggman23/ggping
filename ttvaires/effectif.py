"""Effectif du club et brûlages (page « Effectif de Vaires »).

- Matchs joués par chaque joueur, équipe par équipe : feuilles de match de l'API FFTT.
- Liste des licenciés (réinscrits, non réinscrits, licences loisir, catégories) : pingpocket.fr,
  revérifiée à chaque lancement ; si le site ne répond pas, la dernière liste obtenue est reprise
  (avec sa date) ; à défaut, seuls les joueurs déjà alignés sont connus.

Brûlage : championnat masculin et championnat féminin sont indépendants. Une joueuse alignée en
masculin y est traitée comme les garçons (ses matchs en équipe féminine ne comptent pas).
"""

import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

from . import fftt, pingpocket
from .brulage import brulage_par_equipe, equipe_max
from .reseau import HEURE


def _joueur_feuille(j):
    pts = j["points"]
    return {
        "id": j["licence"], "licence": j["licence"], "nom": j["nom_famille"], "prenom": j["prenom"],
        "sexe": None, "categorie": None, "categorie_long": None, "loisir": False,
        "classement": max(5, pts // 100) if pts else None, "points": pts, "points_mensuels": None,
        "renouvele": True,
    }


def recuperer_effectif(client, numero_club="08770250", aujourdhui=None, fichier_etat=None):
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
    liens = {"categories": f"/app/fftt/clubs/{numero_club}/licencies?SORT=CATEGORY",
             "classements": f"/app/fftt/clubs/{numero_club}/licencies?SORT=OFFICIAL_RANK",
             "etat": f"/app/fftt/clubs/{numero_club}/licencies?SORT=LICENCE_STATE"}
    pages = client.get_plusieurs(list(liens.values()), ttl=HEURE, perime_si_erreur=True)
    if all(pages.get(u) for u in liens.values()):
        liste = pingpocket.licencies(pages, liens)
        anciennes = [client.perimes[u] for u in liens.values() if u in client.perimes]
        source = {"liste": True, "a_jour": not anciennes,
                  "date": datetime.fromtimestamp(min(anciennes)).isoformat(timespec="minutes") if anciennes
                  else datetime.now().isoformat(timespec="minutes")}
        if anciennes:
            print(f"  ! pingpocket.fr ne répond pas : reprise de la liste du {source['date'][:16].replace('T', ' ')}")
    else:
        liste = []
        source = {"liste": False, "a_jour": False, "date": None}
        print("  ! Liste des licenciés indisponible : seuls les joueurs déjà alignés apparaissent.")

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
    if source["a_jour"]:
        fichier.parent.mkdir(parents=True, exist_ok=True)
        fichier.write_text(json.dumps({"date": source["date"], "renouveles": actuels}), encoding="utf-8")
    return precedent["date"] if precedent else None

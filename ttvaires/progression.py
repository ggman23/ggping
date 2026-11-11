"""Page « Progression des joueurs » : les points virtuels de chaque joueur de Vaires semaine après
semaine depuis le début de la saison (1er septembre), pour voir qui progresse et qui régresse, et
comparer des joueurs.

Aucune donnée de plus : ce sont les parties du classement virtuel (toutes compétitions), cumulées par
semaine (du lundi au dimanche). Sur une phase, les points virtuels partent des points officiels de la
phase ; en phase 2, la courbe reprend la phase 1 (ses parties et ses points officiels) puis passe aux
points officiels de janvier : elle couvre toute la saison. Départ : les points au 1er septembre.

Avec la courbe, le nombre de matchs, de perfs (victoires contre un joueur qui a plus de points) et de
contres (défaites contre un joueur qui en a moins), points officiels de la phase : une courbe qui
descend sans aucune contre, c'est un joueur qui n'a perdu que contre plus fort que lui ; des perfs
avec une courbe qui monte, c'est un joueur en progression.
"""

from datetime import date, datetime, timedelta

SEUIL_TENDANCE = 10  # ±10 points depuis le début de la saison : progresse / régresse, sinon stable


def lundi(iso):
    d = date.fromisoformat(iso[:10])
    return d - timedelta(days=d.weekday())


def semaines(premiere, derniere):
    """Lundis de `premiere` à `derniere` (dates), inclus."""
    sortie, d = [], lundi(premiere.isoformat())
    while d <= derniere:
        sortie.append(d)
        d += timedelta(days=7)
    return sortie


def debut_saison(saison):
    """« 2026-2027 » -> 1er septembre 2026."""
    return date(int(saison[:4]), 9, 1)


def tendance(progression):
    return "progresse" if progression >= SEUIL_TENDANCE else "régresse" if progression <= -SEUIL_TENDANCE else "stable"


def lecture(j):
    """Ce que dit la courbe avec les perfs et les contres (None sans partie)."""
    if not j["v"] + j["d"]:
        return None
    p, c, total = j["nb_perfs"], j["nb_contres"], j["total"]
    pl = lambda n, mot: f"{n} {mot}{'s' if n > 1 else ''}"
    if total <= -SEUIL_TENDANCE:
        return "baisse sans contre : perdu contre plus fort" if not c else f"baisse avec {pl(c, 'contre')}"
    if total >= SEUIL_TENDANCE:
        return f"progression avec {pl(p, 'perf')}" if p else "progression sans perf"
    return "stable"


def _phases(j, debut_phase):
    """Phases de la saison du joueur, dans l'ordre : [(début, points officiels, parties)]."""
    phases = []
    if j.get("phase1") and j["phase1"].get("officiels") is not None:
        phases.append((None, j["phase1"]["officiels"], j["phase1"]["parties"]))
    phases.append((debut_phase, j["officiels"], j["parties"]))
    return phases


def _valeur(phases, dimanche):
    """Points virtuels au soir de `dimanche` : ceux de la phase en cours ce jour-là."""
    for debut, officiels, parties in reversed(phases):
        if debut is None or dimanche >= debut:
            return officiels + sum(p["points"] for p in parties if p["date"] <= dimanche)
    return phases[0][1]


def donnees_progression(virtuel, aujourdhui=None):
    """Données de la page à partir de celles du classement virtuel (recuperer_virtuel)."""
    reference = virtuel.get("date_reference") or (aujourdhui.isoformat() if aujourdhui else None)
    fin = date.fromisoformat(reference) if reference else datetime.fromisoformat(virtuel["genere_le"]).date()
    debut = debut_saison(virtuel["saison"]) if virtuel.get("saison") else None
    debut_phase = virtuel.get("debut") or "0000-00-00"
    joueurs_ok = [j for j in virtuel["joueurs"] if j.get("officiels") is not None]
    toutes = [p for j in joueurs_ok for _, _, ps in _phases(j, debut_phase) for p in ps
              if debut is None or p["date"] >= debut.isoformat()]
    if not toutes:
        return {**_entete(virtuel, debut), "semaines": [], "joueurs": []}
    premiere = debut or date.fromisoformat(min(p["date"] for p in toutes))
    # Une semaine avant celle du 1er septembre : le point de départ (points au début de la saison)
    liste = semaines(lundi(premiere.isoformat()) - timedelta(days=7), lundi(max(max(p["date"] for p in toutes), fin.isoformat())))
    debut_compte = liste[1].isoformat()
    index = {d: i for i, d in enumerate(liste)}
    joueurs = []
    for j in joueurs_ok:
        phases = _phases(j, debut_phase)
        n = len(liste)
        nb, victoires, perfs, contres = [0] * n, [0] * n, [0] * n, [0] * n
        for _, _, parties in phases:
            for p in parties:
                if p["date"] < debut_compte:
                    continue
                i = index[lundi(p["date"])]
                nb[i] += 1
                victoires[i] += bool(p["victoire"])
                ecart = p.get("ecart") or 0  # points de l'adversaire moins ceux du joueur
                perfs[i] += bool(p["victoire"] and ecart > 0)
                contres[i] += bool(not p["victoire"] and ecart < 0)
        serie = [round(_valeur(phases, (d + timedelta(days=6)).isoformat()), 1) for d in liste]
        x = {"id": j["id"], "nom": j.get("nom"), "prenom": j.get("prenom"), "equipe": j.get("equipe"),
             "categorie": j.get("categorie"), "officiels": j["officiels"], "serie": serie, "parties": nb,
             "victoires": victoires, "perfs": perfs, "contres": contres, "v": sum(victoires), "d": sum(nb) - sum(victoires),
             "nb_perfs": sum(perfs), "nb_contres": sum(contres), "total": round(serie[-1] - serie[0], 1)}
        x["tendance"] = tendance(x["total"]) if sum(nb) else None
        x["lecture"] = lecture(x)
        joueurs.append(x)
    joueurs.sort(key=lambda x: (-x["serie"][-1], x["nom"] or ""))
    return {**_entete(virtuel, debut), "semaines": [d.isoformat() for d in liste], "joueurs": joueurs}


def _entete(virtuel, debut):
    return {"genere_le": virtuel.get("genere_le"), "saison": virtuel.get("saison"), "phase": virtuel.get("phase"),
            "debut": virtuel.get("debut"), "debut_saison": debut.isoformat() if debut else None, "club": virtuel.get("club"),
            "date_reference": virtuel.get("date_reference"), "seuil": SEUIL_TENDANCE}

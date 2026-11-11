"""Page « Progression des joueurs » : les points virtuels de chaque joueur de Vaires semaine après
semaine depuis le début de la phase, pour voir qui progresse et qui régresse, et comparer des joueurs.

Avec la courbe, le nombre de matchs, de perfs (victoires contre un joueur qui a plus de points) et de
contres (défaites contre un joueur qui en a moins), points officiels de la phase : une courbe qui
descend sans aucune contre, c'est un joueur qui n'a perdu que contre plus fort que lui ; des perfs
avec une courbe qui monte, c'est un joueur en progression.

Aucune donnée de plus : ce sont les parties du classement virtuel (toutes compétitions), cumulées par
semaine (du lundi au dimanche). Point de départ : les points officiels de la phase.
"""

from datetime import date, datetime, timedelta

RECENT = 4  # « ces dernières semaines » : les 4 dernières
SEUIL_TENDANCE = 5  # ±5 points sur les dernières semaines : progresse / régresse, sinon stable


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


def tendance(recent):
    return "progresse" if recent >= SEUIL_TENDANCE else "régresse" if recent <= -SEUIL_TENDANCE else "stable"


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


def donnees_progression(virtuel, aujourdhui=None):
    """Données de la page à partir de celles du classement virtuel (recuperer_virtuel)."""
    reference = virtuel.get("date_reference") or (aujourdhui.isoformat() if aujourdhui else None)
    fin = date.fromisoformat(reference) if reference else datetime.fromisoformat(virtuel["genere_le"]).date()
    dates = [p["date"] for j in virtuel["joueurs"] for p in j["parties"]]
    if not dates:
        return {**_entete(virtuel), "semaines": [], "joueurs": []}
    # Une semaine avant la première partie : le point de départ (points officiels de la phase)
    liste = semaines(date.fromisoformat(min(dates)) - timedelta(days=7), lundi(max(max(dates), fin.isoformat())))
    index = {d: i for i, d in enumerate(liste)}
    joueurs = []
    for j in virtuel["joueurs"]:
        if j.get("officiels") is None:
            continue
        gains, nb, victoires = [0.0] * len(liste), [0] * len(liste), [0] * len(liste)
        perfs, contres = [0] * len(liste), [0] * len(liste)
        for p in j["parties"]:
            i = index[lundi(p["date"])]
            gains[i] += p["points"]
            nb[i] += 1
            victoires[i] += bool(p["victoire"])
            ecart = p.get("ecart") or 0  # points de l'adversaire moins ceux du joueur
            perfs[i] += bool(p["victoire"] and ecart > 0)
            contres[i] += bool(not p["victoire"] and ecart < 0)
        serie, cumul = [], j["officiels"]
        for g in gains:
            cumul += g
            serie.append(round(cumul, 1))
        recent = round(serie[-1] - (serie[-RECENT - 1] if len(serie) > RECENT else j["officiels"]), 1)
        joueurs.append({
            "id": j["id"], "nom": j.get("nom"), "prenom": j.get("prenom"), "equipe": j.get("equipe"),
            "categorie": j.get("categorie"), "officiels": j["officiels"], "serie": serie, "parties": nb,
            "victoires": victoires, "perfs": perfs, "contres": contres, "nb_perfs": sum(perfs), "nb_contres": sum(contres),
            "total": round(serie[-1] - j["officiels"], 1), "recent": recent,
            "tendance": tendance(recent) if j["parties"] else None, "v": j.get("v", 0), "d": j.get("d", 0),
        })
    for x in joueurs:
        x["lecture"] = lecture(x)
    joueurs.sort(key=lambda x: (-x["serie"][-1], x["nom"] or ""))
    return {**_entete(virtuel), "semaines": [d.isoformat() for d in liste], "joueurs": joueurs}


def _entete(virtuel):
    return {"genere_le": virtuel.get("genere_le"), "saison": virtuel.get("saison"), "phase": virtuel.get("phase"),
            "debut": virtuel.get("debut"), "club": virtuel.get("club"), "date_reference": virtuel.get("date_reference"),
            "recent": RECENT, "seuil": SEUIL_TENDANCE}

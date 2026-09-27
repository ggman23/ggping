"""Règles de brûlage FFTT (championnat par équipes) et analyse des rencontres.

Règles appliquées (validées, cf. CAHIER_DES_CHARGES.md) :

1. Brûlage : un joueur peut jouer en équipe N tant qu'il a disputé moins de 2 rencontres,
   dans la phase, dans des équipes de numéro < N (plus fortes).
2. Un seul match par journée (la J1 régionale du samedi et la J1 départementale du
   vendredi sont la même journée).
3. Règle de la J2 : à la 2e journée, une équipe ne peut aligner qu'un seul joueur ayant
   joué la J1 dans une équipe de numéro < N.

Le championnat masculin ("M") et le championnat féminin ("F") sont indépendants.
"""

from collections import defaultdict
from datetime import date

TAILLE_EQUIPE_DEFAUT = 4


def participations(club, championnat):
    """Matchs joués par chaque joueur du club : {id_joueur: [participation, ...]}.

    Une participation vaut {"journee", "date", "numero", "libelle"}, triées dans l'ordre
    chronologique.
    """
    res = defaultdict(list)
    for equipe in club.get("equipes", []):
        if equipe.get("championnat") != championnat or equipe.get("numero") is None:
            continue
        for compo in equipe.get("compositions", []):
            for id_joueur in compo.get("joueurs", []):
                res[id_joueur].append({
                    "journee": compo.get("journee"),
                    "date": compo.get("date"),
                    "numero": equipe["numero"],
                    "libelle": equipe.get("libelle"),
                })
    for parts in res.values():
        parts.sort(key=lambda p: (p.get("date") or "", p.get("journee") or 0))
    return dict(res)


def equipe_max(parts):
    """Numéro de la plus faible équipe où le joueur peut encore jouer (None = aucune limite).

    Le joueur peut jouer en équipe N tant qu'il a moins de 2 matchs dans des équipes de
    numéro < N : la limite est donc le 2e plus petit numéro d'équipe dans lequel il a joué.
    """
    numeros = sorted(p["numero"] for p in parts)
    return numeros[1] if len(numeros) >= 2 else None


def _avant(part, journee, date_match):
    """La participation a-t-elle eu lieu avant la rencontre analysée ?"""
    if date_match and part.get("date"):
        return part["date"] < date_match
    return (part.get("journee") or 0) < journee


def _meme_journee(part, journee, date_match):
    """Participation à la même journée, jouée juste avant (ex. samedi régional -> vendredi)."""
    if part.get("journee") != journee:
        return False
    if date_match and part.get("date"):
        ecart = date.fromisoformat(date_match) - date.fromisoformat(part["date"])
        return 0 < ecart.days < 7
    return False


def points_tri(joueur):
    """Points utilisés pour classer les joueurs : mensuels si connus, sinon officiels."""
    return joueur.get("points_mensuels") or joueur.get("points") or 0


def taille_equipe(club, championnat, numero):
    """Nombre de joueurs par rencontre, déduit des compositions déjà connues."""
    for equipe in club.get("equipes", []):
        if equipe.get("championnat") == championnat and equipe.get("numero") == numero:
            tailles = [len(c.get("joueurs", [])) for c in equipe.get("compositions", [])]
            if any(tailles):
                return max(tailles)
    return TAILLE_EQUIPE_DEFAUT


def analyse_rencontre(club, championnat, numero, journee, date_match=None):
    """Qui peut jouer dans l'équipe `numero` du club pour la journée `journee` ?

    Ne tient compte que des matchs joués avant la rencontre. Renvoie des listes d'identifiants
    de joueurs (triées par points décroissants) :

    - probable    : composition probable (estimation) ;
    - habitues    : joueurs ayant déjà joué dans cette équipe ;
    - renforts    : joueurs d'équipes plus fortes, non brûlés ;
    - remplacants : joueurs d'équipes plus faibles ;
    - non_alignes : joueurs qui n'ont encore joué dans aucune équipe cette phase ;
    - brules      : joueurs qui ne peuvent pas jouer, avec la raison.
    """
    parts = participations(club, championnat)
    joueurs = [
        j for j in club.get("joueurs", [])
        if j.get("renouvele", True) and (championnat != "F" or j.get("sexe") in (None, "F"))
    ]
    joueurs.sort(key=points_tri, reverse=True)

    habitues, renforts, remplacants, non_alignes, brules = [], [], [], [], []
    for joueur in joueurs:
        jid = joueur["id"]
        avant = [p for p in parts.get(jid, []) if _avant(p, journee, date_match)]
        plus_fortes = [p for p in avant if p["numero"] < numero]
        deja = [p for p in avant if _meme_journee(p, journee, date_match)]
        if len(plus_fortes) >= 2:
            equipes = [p["numero"] for p in plus_fortes]
            brules.append({"id": jid, "equipes": equipes,
                           "raison": f"2 matchs en équipes plus fortes ({', '.join(map(str, equipes))})"})
        elif deja:
            brules.append({"id": jid, "equipes": [deja[0]["numero"]],
                           "raison": f"a déjà joué la J{journee} en équipe {deja[0]['numero']}"})
        elif any(p["numero"] == numero for p in avant):
            nb = sum(p["numero"] == numero for p in avant)
            habitues.append({"id": jid, "nb": nb})
        elif plus_fortes:
            renforts.append({
                "id": jid,
                "equipes": sorted({p["numero"] for p in plus_fortes}),
                "j1_plus_forte": journee == 2 and any(p.get("journee") == 1 for p in plus_fortes),
            })
        elif avant:
            remplacants.append({"id": jid, "equipes": sorted({p["numero"] for p in avant})})
        else:
            non_alignes.append(jid)

    taille = taille_equipe(club, championnat, numero)
    # Estimation : les habitués d'abord (les plus présents), complétés par les joueurs des
    # équipes juste en dessous, puis par ceux qui n'ont pas encore joué.
    probable = [h["id"] for h in sorted(habitues, key=lambda h: -h["nb"])][:taille]
    for r in sorted(remplacants, key=lambda r: min(r["equipes"])):
        if len(probable) >= taille:
            break
        probable.append(r["id"])
    for jid in non_alignes:
        if len(probable) >= taille:
            break
        probable.append(jid)

    return {
        "championnat": championnat,
        "numero": numero,
        "journee": journee,
        "date": date_match,
        "taille": taille,
        "probable": probable,
        "habitues": habitues,
        "renforts": renforts,
        "remplacants": remplacants,
        "non_alignes": non_alignes,
        "brules": brules,
        "regle_j2": journee == 2 and any(r["j1_plus_forte"] for r in renforts),
    }


def _equipe_adverse(club, libelle, championnat):
    for equipe in club.get("equipes", []):
        if equipe.get("championnat") == championnat and equipe.get("libelle") == libelle:
            return equipe
    return None


def enrichir(donnees):
    """Ajoute aux données les parcours des joueurs et l'analyse de chaque rencontre de Vaires."""
    for club in donnees.get("clubs", {}).values():
        parcours = {}
        for championnat in ("M", "F"):
            for jid, parts in participations(club, championnat).items():
                parcours.setdefault(jid, {})[championnat] = {
                    "matchs": [{"j": p["journee"], "n": p["numero"], "d": p["date"]} for p in parts],
                    "equipe_max": equipe_max(parts),
                }
        club["parcours"] = parcours

    for equipe in donnees.get("equipes", []):
        championnat = equipe.get("championnat", "M")
        for renc in equipe.get("rencontres", []):
            adv = renc.get("adversaire")
            if not adv or adv.get("club") not in donnees.get("clubs", {}):
                continue
            club = donnees["clubs"][adv["club"]]
            equipe_adv = _equipe_adverse(club, adv.get("libelle"), championnat)
            numero = adv.get("numero") or (equipe_adv or {}).get("numero")
            if numero is None:
                continue
            adv["numero"] = numero
            date_match = renc.get("date_reelle") or renc.get("date")
            renc["analyse"] = analyse_rencontre(club, championnat, numero, renc["journee"], date_match)
            if equipe_adv:
                alignee = [c for c in equipe_adv.get("compositions", []) if c.get("journee") == renc["journee"]]
                renc["composition_adverse"] = alignee[0]["joueurs"] if alignee else None
    return donnees

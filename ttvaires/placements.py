"""Placement des joueurs sur les lettres de la feuille de match (championnat par équipes).

Lettres : A, B, C, D pour l'équipe qui reçoit, W, X, Y, Z pour l'équipe visiteuse (A, B, C et
X, Y, Z dans les rencontres à trois joueurs). Le capitaine choisit la lettre de chacun de ses
joueurs. Une même place a donc deux lettres selon que l'équipe reçoit ou se déplace :
position 1 = A ou W, 2 = B ou X, 3 = C ou Y, 4 = D ou Z (à trois : A/X, B/Y, C/Z).

Ordre des parties à quatre joueurs, relevé sur toutes les feuilles des équipes de Vaires :
AW BX CY DZ AX BW DY CZ, double 1, double 2, AY CW DX BZ. Chaque joueur dispute trois simples et
ne rencontre jamais une des positions adverses : A ne joue pas Z, B pas Y, C pas X, D pas W
(1 contre 4 et 2 contre 3 n'ont jamais lieu). D'où l'intérêt de savoir où l'adversaire place
ses joueurs. À trois joueurs (AX BY CZ BX, double, AZ CY BZ CX AY), chacun rencontre les trois
adversaires : le placement ne change que l'ordre des parties.
"""

LIBELLES = {4: ["A/W", "B/X", "C/Y", "D/Z"], 3: ["A/X", "B/Y", "C/Z"]}
EVITE = {1: 4, 2: 3, 3: 2, 4: 1}  # à quatre joueurs : la position adverse jamais rencontrée


def position(lettre, format_=4):
    """1 à 4 (ou 3) pour une lettre de la feuille ; None si inconnue."""
    for serie in ("ABCD", "WXYZ" if format_ == 4 else "XYZ"):
        if lettre and lettre in serie:
            return serie.index(lettre) + 1
    return None


def _avant(compo, journee, date_match):
    if date_match and compo.get("date"):
        return compo["date"] < date_match
    return (compo.get("journee") or 0) < journee


def placements(equipe, journee, date_match=None):
    """Où une équipe adverse a placé ses joueurs lors de ses rencontres jouées avant la rencontre
    analysée. Renvoie None si aucune feuille ne donne les lettres, sinon :
    - format : 4 ou 3 joueurs ; libelles : ["A/W", "B/X", ...] ;
    - rencontres : [{journee, date, domicile, contre, places: [id du joueur ou None par position],
      par_points: places dans l'ordre des points (le mieux classé en A/W...) ou None}] ;
    - joueurs : {id: [nombre de rencontres à chaque position]} ;
    - par_points : nombre de rencontres placées dans l'ordre des points (sur celles où on le sait)."""
    compos = sorted((c for c in (equipe or {}).get("compositions", [])
                     if c.get("lettres") and _avant(c, journee, date_match)),
                    key=lambda c: (c.get("date") or "", c.get("journee") or 0))
    if not compos:
        return None
    format_ = max(c.get("format") or 4 for c in compos)
    rencontres, joueurs = [], {}
    for c in compos:
        places = [None] * format_
        for jid, lettre in c["lettres"].items():
            pos = position(lettre, c.get("format") or format_)
            if pos and pos <= format_:
                places[pos - 1] = jid
                joueurs.setdefault(jid, [0] * format_)[pos - 1] += 1
        points = [(c.get("points") or {}).get(jid) if jid else None for jid in places]
        connus = [p for jid, p in zip(places, points) if jid]
        par_points = (all(a >= b for a, b in zip(connus, connus[1:]))
                      if len(connus) > 1 and all(connus) else None)
        rencontres.append({"journee": c.get("journee"), "date": c.get("date"), "domicile": c.get("domicile"),
                           "contre": c.get("contre"), "places": places, "points": points, "par_points": par_points})
    return {"format": format_, "libelles": LIBELLES.get(format_, LIBELLES[4]), "rencontres": rencontres,
            "joueurs": joueurs, "par_points": sum(1 for r in rencontres if r["par_points"]),
            "avec_points": sum(1 for r in rencontres if r["par_points"] is not None)}


def resume_joueur(compte, libelles):
    """« A/W ×2 · B/X ×1 » : les positions d'un joueur, la plus fréquente d'abord."""
    if not compte:
        return ""
    ordre = sorted((i for i, n in enumerate(compte) if n), key=lambda i: (-compte[i], i))
    return " · ".join(f"{libelles[i]} ×{compte[i]}" for i in ordre)

"""Résultats individuels des joueurs de Vaires, journée par journée (points virtuels FFTT).

Pour chaque journée : l'équipe dans laquelle chaque joueur a joué, ses victoires, les points
gagnés ou perdus (barème FFTT, coefficient 1 du championnat par équipes), sa meilleure
victoire du jour et le total cumulé depuis la J1. Sorties : page HTML triable et classeur Excel.
"""

from collections import Counter, defaultdict
from datetime import date, datetime

from . import fftt
from .reseau import HEURE
from .verifications import LIBELLES, bilan_club, statut

# Barème FFTT : (écart maximum exclu, victoire normale, défaite normale, victoire anormale,
# défaite anormale). Normal = le joueur qui a le plus de points gagne.
BAREME = [
    (25, 6, -5, 6, -5),
    (50, 5.5, -4.5, 7, -6),
    (100, 5, -4, 8, -7),
    (150, 4, -3, 10, -8),
    (200, 3, -2, 13, -10),
    (300, 2, -1, 17, -12.5),
    (400, 1, -0.5, 22, -16),
    (500, 0.5, 0, 28, -20),
    (None, 0, 0, 40, -29),
]
COEFFICIENT_CHAMPIONNAT = 1
# Coefficient de chaque championnat pour les points (FFTT : championnat de France 1 ; Ligue IDF : championnat de
# Paris 0,75 ; championnat des jeunes : celui que donne l'API pour la compétition, 0,5 en attendant)
COEFFICIENTS = {"france": 1, "paris": 0.75, "jeunes": 0.5}
# Championnat de Paris : points-parties d'une partie gagnée selon le groupe (règlement de la ligue, article 7)
BAREME_GROUPES = [6, 5, 4]


def points_partie(points, points_adv, victoire, coefficient=COEFFICIENT_CHAMPIONNAT):
    """Points gagnés (ou perdus) par un joueur sur une partie."""
    ecart = abs(points - points_adv)
    _, vn, dn, va, da = next(ligne for ligne in BAREME if ligne[0] is None or ecart < ligne[0])
    if victoire:
        gain = vn if points >= points_adv else va
    else:
        gain = dn if points <= points_adv else da
    return gain * coefficient


def _rencontres_jouees(client, numero_club, aujourdhui, championnat="france"):
    """Rencontres d'un championnat (france : phase en cours ; paris, jeunes : saison) du club, celles déjà
    jouées (avec le côté de Vaires) et leurs feuilles de match."""
    debut, fin = fftt.bornes(aujourdhui, championnat)
    id_club = fftt.id_interne_club(client, numero_club, fftt.bornes_phase(aujourdhui)[0])
    rencontres = fftt.rencontres_club(client, id_club, debut, fin, ttl=3 * HEURE, championnat=championnat)

    nos_equipes = {}  # nom de l'équipe -> (féminine, numéro)
    jouees = []
    for r in rencontres:
        cotes = {c: (r.get(c) or {}).get("team") or {} for c in ("homeOpponent", "awayOpponent")}
        for c, equipe in cotes.items():
            if any(club.get("identifier") == numero_club for club in equipe.get("clubs", [])):
                nos_equipes[equipe["name"]] = (championnat == "france" and fftt.feminin(r), fftt.numero_equipe(equipe["name"]) or 0)
                if r["date"][:10] <= aujourdhui.isoformat():
                    jouees.append((r, c == "homeOpponent"))
    ordres = {nom: i for i, nom in enumerate(sorted(nos_equipes, key=lambda n: nos_equipes[n]))}
    etats = {}
    details = fftt.details(client, [r for r, _ in jouees], aujourdhui.isoformat(), etats)
    return {"rencontres": rencontres, "nos_equipes": nos_equipes, "jouees": jouees, "ordres": ordres,
            "etats": etats, "details": details}


def _nom_equipe(nos_equipes, nom_api):
    feminine, numero = nos_equipes[nom_api]
    return f"VAIRES {numero}{' F' if feminine else ''}"


def coefficient_du_championnat(client, rencontres, championnat):
    """Coefficient des points : 1 pour le championnat de France ; pour les autres, celui que l'API donne pour la
    compétition (Paris 0,75), sinon la valeur connue (COEFFICIENTS)."""
    if championnat == "france":
        return COEFFICIENT_CHAMPIONNAT
    try:
        from .virtuel import _competitions
        ids = {((r.get("division") or {}).get("contest") or {}).get("id") for r in rencontres} - {None}
        coefs = {c["coef"] for c in _competitions(client, ids).values() if isinstance(c.get("coef"), (int, float))}
        if len(coefs) == 1:
            return coefs.pop()
    except Exception:  # noqa: BLE001 (la valeur connue sert)
        pass
    return COEFFICIENTS[championnat]


def recuperer_parties(client, numero_club="08770250", aujourdhui=None, championnat="france"):
    """Toutes les parties de simple jouées par les joueurs du club dans un championnat par équipes : France
    (phase en cours, masculin et féminin), Paris ou jeunes (saison), lues sur l'API de la FFTT."""
    aujourdhui = aujourdhui or date.today()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    print(f"Résultats des équipes du club {numero_club} : {fftt.NOMS_CHAMPIONNATS[championnat]} "
          f"({f'phase {phase} ' if championnat == 'france' else ''}{saison}, API FFTT)", flush=True)
    club = _rencontres_jouees(client, numero_club, aujourdhui, championnat)
    coefficient = coefficient_du_championnat(client, club["rencontres"], championnat)
    from . import mensuel  # valeurs mois par mois des joueurs du 77 (page des clubs du 77) ; sans elles, points de la phase
    references = mensuel.References.lire(client)
    parties = []
    for r, domicile in club["jouees"]:
        d = club["details"].get(r["id"])
        if not d or not d.get("games"):
            continue
        nous, eux = ("home", "away") if domicile else ("away", "home")
        notre_equipe = d[f"{nous}Opponent"]["team"]["name"]
        nom = _nom_equipe(club["nos_equipes"], notre_equipe)
        for g in d["games"]:
            if g.get("doubleOpposition") or g.get("forfeit") or g.get("notCounted") or g.get("winner") not in ("home", "away"):
                continue
            if not g.get(f"{nous}Player") or not g.get(f"{eux}Player"):
                continue
            j, a = fftt.joueur(g[f"{nous}Player"]), fftt.joueur(g[f"{eux}Player"])
            pts, pts_adv = j["points"] or 500, a["points"] or 500
            officiels = pts  # points de la phase : départ du cumul
            pts = round(references.valeur(j["licence"], d["date"][:10]) or pts, 1)      # calcul mois par mois, comme la FFTT
            pts_adv = round(references.valeur(a["licence"], d["date"][:10]) or pts_adv, 1)
            victoire = g["winner"] == nous
            parties.append({
                "journee": d["day"]["position"], "date": d["date"][:10],
                "equipe": nom, "ordre": club["ordres"][notre_equipe], "adversaires": d[f"{eux}Opponent"]["team"]["name"],
                "licence": j["licence"], "joueur": j["nom"], "points": pts, "officiels": officiels,
                "adversaire": a["nom"], "points_adv": pts_adv,
                "ecart": pts_adv - pts, "victoire": victoire,
                "gain": points_partie(pts, pts_adv, victoire, coefficient),
            })
    parties.sort(key=lambda p: (p["journee"], p["date"], p["ordre"], -p["points"], p["joueur"]))
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "championnat": championnat, "coefficient": coefficient,
        "club": {"numero": numero_club, "nom": "CVTT VAIRES" if numero_club == "08770250" else numero_club},
        "parties": parties, "mensuel": bool(references),
        "verification": bilan_club(club["rencontres"], club["etats"], aujourdhui.isoformat(), numero_club, "CVTT VAIRES"),
    }


# ---------------------------------------------------------------------------
# Feuilles de match : le détail de chaque rencontre (parties, scores des manches)
# ---------------------------------------------------------------------------

def recuperer_rencontres(client, numero_club="08770250", aujourdhui=None, championnat="france"):
    """Chaque rencontre jouée par les équipes du club dans un championnat (france : la phase ; paris, jeunes :
    la saison) : score, et pour chaque partie les joueurs, le score des manches et le vainqueur (vu de Vaires :
    Vaires toujours en premier). Championnat de Paris : les parties sont rangées par groupe de 3 joueurs."""
    aujourdhui = aujourdhui or date.today()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    print(f"Feuilles de match des équipes du club {numero_club} : {fftt.NOMS_CHAMPIONNATS[championnat]} "
          f"({f'phase {phase} ' if championnat == 'france' else ''}{saison}, API FFTT)", flush=True)
    club = _rencontres_jouees(client, numero_club, aujourdhui, championnat)
    rencontres = []
    for r, domicile in club["jouees"]:
        nous, eux = ("home", "away") if domicile else ("away", "home")
        notre, autre = fftt.equipe(r, f"{nous}Opponent"), fftt.equipe(r, f"{eux}Opponent")
        if not autre:
            continue  # exempte
        etat = statut(r, club["etats"], aujourdhui.isoformat())
        feminine, numero = club["nos_equipes"][notre["name"]]
        rencontre = {
            "journee": r["day"]["position"], "date": r["date"][:10], "heure": fftt.heure(r),
            "equipe": _nom_equipe(club["nos_equipes"], notre["name"]), "ordre": club["ordres"][notre["name"]],
            "numero": numero, "feminine": feminine,
            "adversaire": autre.get("name"), "domicile": domicile, "division": fftt.libelle_division(r["division"]["name"]),
            "division_courte": fftt.division_courte(r["division"]["name"]),
            "etat": etat, "libelle": LIBELLES[etat], "score": None, "parties": [], "bilan": [],
        }
        d = club["details"].get(r["id"])
        if d:
            rencontre.update(feuille_de_match(d, nous, eux, groupes=championnat == "paris"))
            if championnat == "paris":
                print(f"  Paris J{rencontre['journee']} {rencontre['equipe']} : {structure_feuille(d)}", flush=True)
        rencontres.append(rencontre)
    rencontres.sort(key=lambda x: (x["journee"], x["ordre"], x["date"]))
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "championnat": championnat,
        "club": {"numero": numero_club, "nom": "CVTT VAIRES" if numero_club == "08770250" else numero_club},
        "journees": sorted({x["journee"] for x in rencontres}),
        "rencontres": rencontres,
        "verification": bilan_club(club["rencontres"], club["etats"], aujourdhui.isoformat(), numero_club, "CVTT VAIRES"),
    }


def groupes_des_parties(d, nous, eux):
    """Championnat de Paris : le groupe (1, 2, 3) de chaque partie de la feuille, dans l'ordre de d["games"].
    Une équipe de 9 ou de 6 joue en groupes de 3 joueurs contre 3 : les joueurs qui se rencontrent forment un
    groupe (composantes du graphe des parties de simple). Groupe 1 : celui dont le meilleur joueur de Vaires a
    le plus de points (règlement, article 8 : les points vont en décroissant du groupe 1 au groupe 3), puis
    l'ordre de la feuille. Une partie sans joueur d'un côté (absent) va au groupe de l'autre joueur."""
    parent = {}

    def racine(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    jeux = d.get("games") or []
    noeuds = []
    for g in jeux:
        n = [f"{c}:{(g.get(f'{c}Player') or {}).get('identifier')}" for c in (nous, eux) if (g.get(f"{c}Player") or {}).get("identifier")]
        if g.get("doubleOpposition"):
            n = []
        noeuds.append(n)
        for a in n:
            racine(a)
        if len(n) == 2:
            parent[racine(n[0])] = racine(n[1])
    points = {}
    for g in jeux:
        j = g.get(f"{nous}Player") or {}
        if j.get("identifier"):
            points[f"{nous}:{j['identifier']}"] = j.get("points") or 0
    composantes = {}
    for i, n in enumerate(noeuds):
        for a in n:
            c = composantes.setdefault(racine(a), {"premier": i, "max": 0})
            c["max"] = max(c["max"], points.get(a, 0))
    ordre = sorted(composantes, key=lambda r: (-composantes[r]["max"], composantes[r]["premier"]))
    rang = {r: i + 1 for i, r in enumerate(ordre)}
    res, dernier = [], 1
    for n in noeuds:  # un double (hors score) ou une partie vide garde le groupe de la partie précédente
        dernier = rang[racine(n[0])] if n else dernier
        res.append(dernier)
    return res


def structure_feuille(d):
    """Pour le journal (aucun nom) : ce que l'API donne d'une feuille du championnat de Paris, pour vérifier la
    lecture des groupes : nombre de parties, points-parties, lettres des joueurs, groupes trouvés."""
    jeux = d.get("games") or []
    simples = [g for g in jeux if not g.get("doubleOpposition")]
    lettres = {c: [x.get("identifier") for x in d.get(f"{c}SheetMatches") or []] for c in ("home", "away")}
    groupes = groupes_des_parties(d, "home", "away")
    return (f"{len(jeux)} parties ({len(simples)} simples), points-parties {d.get('homeGamePoints')}-{d.get('awayGamePoints')}, "
            f"points {d.get('homePoints')}-{d.get('awayPoints')}, lettres {''.join(map(str, lettres['home']))}/"
            f"{''.join(map(str, lettres['away']))}, groupes {dict(sorted(Counter(groupes).items()))}, "
            f"champs d'une partie {sorted(jeux[0])[:14] if jeux else []}")


def feuille_de_match(d, nous, eux, groupes=False):
    """Parties d'une feuille de match (détail de l'API), vues du côté `nous` ("home" ou "away").
    groupes=True (championnat de Paris) : chaque partie a son groupe, et chaque groupe son score."""
    lettres = {s["player"].get("identifier"): s.get("identifier")
               for c in ("home", "away") for s in d.get(f"{c}SheetMatches") or [] if s.get("player")}

    def joueurs(g, cote):
        return [{"nom": j["nom_famille"], "prenom": j["prenom"], "points": j["points"], "licence": j["licence"],
                 "lettre": lettres.get(j["licence"])}
                for j in (fftt.joueur(x) for x in (g.get(f"{cote}Player"), g.get(f"{cote}TeammatePlayer")) if x)]

    score, parties, bilan = [0, 0], [], {}
    numeros = groupes_des_parties(d, nous, eux) if groupes else []
    for i, g in enumerate(d.get("games") or []):
        gagne = g["winner"] == nous if g.get("winner") in ("home", "away") else None
        if gagne is not None:
            score[0 if gagne else 1] += 1
        partie = {
            "double": bool(g.get("doubleOpposition")), "nous": joueurs(g, nous), "eux": joueurs(g, eux),
            "sets": [[s.get(f"{nous}Score"), s.get(f"{eux}Score")] for s in g.get("sets") or []],
            "gagne": gagne, "forfait": bool(g.get("forfeit")), "abandon": bool(g.get("abandonment")),
            "non_compte": bool(g.get("notCounted")), "score": list(score),
        }
        if groupes:
            partie["groupe"] = numeros[i]
        parties.append(partie)
        if not partie["double"] and len(partie["nous"]) == 1 and gagne is not None:
            b = bilan.setdefault(partie["nous"][0]["licence"], {**partie["nous"][0], "v": 0, "n": 0})
            b["v"] += gagne
            b["n"] += 1
    par_groupe = []
    if groupes:
        n = max(numeros, default=0)
        for k in range(1, n + 1):
            ps = [p for p in parties if p.get("groupe") == k and not p["double"]]
            v, dd = sum(p["gagne"] is True for p in ps), sum(p["gagne"] is False for p in ps)
            bareme = BAREME_GROUPES[k - 1] if k <= len(BAREME_GROUPES) else BAREME_GROUPES[-1]
            par_groupe.append({"numero": k, "score": [v, dd], "points": [v * bareme, dd * bareme], "bareme": bareme,
                               "nous": sorted({j["licence"] for p in ps for j in p["nous"]} - {None}),
                               "totaux": totaux_manches(ps)})
    return {"score": score, "parties": parties, "forfait": bool(d.get("forfeit")), "groupes": par_groupe,
            "points_partie": [d.get(f"{nous}GamePoints"), d.get(f"{eux}GamePoints")],
            "bilan": sorted(bilan.values(), key=lambda b: (b["lettre"] or "", b["nom"])),
            "totaux": totaux_manches(parties), "totaux_doubles": totaux_manches([p for p in parties if p["double"]])}


def totaux_manches(parties):
    """Manches gagnées et perdues, points marqués et encaissés (somme des scores des manches), vus de
    Vaires, et le nombre de parties jouées dont les manches n'ont pas été saisies."""
    manches, points, sans_detail = [0, 0], [0, 0], 0
    for p in parties:
        sets = [s for s in p["sets"] if None not in s]
        if not sets and p["gagne"] is not None and not p["forfait"]:
            sans_detail += 1
        for a, b in sets:
            manches[0 if a > b else 1] += a != b
            points[0] += a
            points[1] += b
    return {"manches": manches, "points": points, "sans_detail": sans_detail}


def synthese(parties):
    """Une ligne par joueur, équipe et journée, plus le cumul par joueur."""
    groupes = defaultdict(list)
    for p in parties:
        groupes[(p["journee"], p["ordre"], p["licence"])].append(p)
    lignes = []
    for (journee, ordre, lic), ps in groupes.items():
        victoires = [p["ecart"] for p in ps if p["victoire"]]
        # Meilleure victoire = le mieux classé des joueurs battus (le plus grand écart, positif ou non).
        meilleure = max((p for p in ps if p["victoire"]), key=lambda p: p["ecart"], default=None)
        delta = sum(p["gain"] for p in ps)
        lignes.append({
            "journee": journee, "date": ps[0]["date"], "equipe": ps[0]["equipe"], "ordre": ordre,
            "adversaires": ps[0]["adversaires"], "licence": lic, "joueur": ps[0]["joueur"],
            "points": ps[0]["points"], "officiels": ps[0].get("officiels", ps[0]["points"]), "delta": delta,
            "v": len(victoires), "matchs": len(ps),
            "meilleure": meilleure["ecart"] if meilleure else None,
            "meilleure_adv": meilleure["points_adv"] if meilleure else None,
            "apres": ps[0]["points"] + delta,
            "detail": [
                f"{'bat' if p['victoire'] else 'perd contre'} {p['adversaire']} ({round(p['points_adv'])}) : "
                + f"{p['gain']:+g}".replace(".", ",")
                for p in ps
            ],
        })
    # Classement virtuel : on part des points officiels du joueur (ceux de sa première feuille de
    # match de la phase) et on cumule, dans l'ordre chronologique, les points gagnés ou perdus à
    # chaque rencontre. Une joueuse peut disputer deux rencontres dans la même journée (masculin
    # le vendredi, féminin le samedi) : elles se cumulent aussi.
    par_joueur = defaultdict(list)
    for ligne in lignes:
        par_joueur[ligne["licence"]].append(ligne)
    for rencontres in par_joueur.values():
        rencontres.sort(key=lambda l: (l["date"] or "", l["journee"], l["ordre"]))
        officiels = rencontres[0]["officiels"]  # points de la phase (pas la valeur du mois, qui compte déjà des gains)
        total = 0.0
        for ligne in rencontres:
            total += ligne["delta"]
            ligne["points"], ligne["total"], ligne["apres"] = officiels, total, officiels + total
            ligne["autres"] = [{"equipe": l["equipe"], "date": l["date"], "delta": l["delta"]}
                               for l in rencontres if l["journee"] == ligne["journee"] and l is not ligne]
    lignes.sort(key=lambda l: (l["journee"], l["ordre"], -l["points"], l["joueur"]))

    joueurs = {}
    for ligne in lignes:
        c = joueurs.setdefault(ligne["licence"], {
            "licence": ligne["licence"], "joueur": ligne["joueur"], "equipes": [], "ordre": ligne["ordre"],
            "points": ligne["points"], "journees": {}, "total": 0.0, "v": 0, "matchs": 0,
        })
        if ligne["equipe"] not in c["equipes"]:
            c["equipes"].append(ligne["equipe"])
        c["ordre"] = min(c["ordre"], ligne["ordre"])
        c["journees"][ligne["journee"]] = c["journees"].get(ligne["journee"], 0) + ligne["delta"]
        c["total"] += ligne["delta"]
        c["v"] += ligne["v"]
        c["matchs"] += ligne["matchs"]
    for c in joueurs.values():
        c["virtuels"] = c["points"] + c["total"]
    cumuls = sorted(joueurs.values(), key=lambda c: (c["ordre"], -c["points"], c["joueur"]))
    return lignes, cumuls


def donnees_page(resultats, virtuels=None):
    """Données de la page des résultats. `virtuels` ({licence: points virtuels}, page Classement virtuel) : la
    colonne « Virt. » montre le classement virtuel du club (toutes compétitions, le même que sa page), et non les
    points officiels + le total du seul championnat, qui pouvait induire en erreur (28/11)."""
    lignes, cumuls = synthese(resultats["parties"])
    journees = sorted({l["journee"] for l in lignes})
    licences = {l["licence"] for l in lignes}
    return {
        "virtuels_club": {lic: v for lic, v in (virtuels or {}).items() if lic in licences and v is not None} if virtuels else None,
        **{k: resultats[k] for k in ("genere_le", "saison", "phase", "club")},
        "championnat": resultats.get("championnat", "france"), "coefficient": resultats.get("coefficient", COEFFICIENT_CHAMPIONNAT),
        "verification": resultats.get("verification"), "mensuel": bool(resultats.get("mensuel")),
        "journees": [{"numero": j, "dates": sorted({l["date"] for l in lignes if l["journee"] == j and l["date"]})}
                     for j in journees],
        "lignes": lignes, "cumuls": cumuls,
    }


# ---------------------------------------------------------------------------
# Classeur Excel
# ---------------------------------------------------------------------------

def ecrire_xlsx(resultats, chemin):
    """Classeur : un onglet par journée, un onglet Cumul, et l'onglet Parties (données brutes).

    Les onglets de journée et le cumul sont calculés par formules à partir de l'onglet Parties.
    """
    from openpyxl import Workbook
    from openpyxl.comments import Comment
    from openpyxl.formatting.rule import CellIsRule, FormulaRule
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    lignes, cumuls = synthese(resultats["parties"])
    journees = sorted({l["journee"] for l in lignes})
    police = Font(name="Arial", size=11)
    gras = Font(name="Arial", size=11, bold=True)
    fin = Side(style="thin", color="000000")
    bord = Border(left=fin, right=fin, top=fin, bottom=fin)
    entete_fond = PatternFill("solid", fgColor="F8CBAD")
    centre = Alignment(horizontal="center", vertical="center")
    vert_clair, vert_texte = PatternFill("solid", fgColor="C6EFCE"), Font(name="Arial", color="006100")
    rose, rouge_texte = PatternFill("solid", fgColor="FFC7CE"), Font(name="Arial", color="9C0006")

    wb = Workbook()
    wb.remove(wb.active)

    # --- Onglet Parties : une ligne par partie de simple -------------------------------
    ws_p = wb.create_sheet("Parties")
    entetes_p = ["Journée", "Date", "Equipe", "Joueur", "Points", "Adversaire", "Points adv.",
                 "Ecart", "Résultat", "Pts +/-", "Adversaires"]
    ws_p.append(entetes_p)
    for i, p in enumerate(resultats["parties"], start=2):
        ws_p.append([p["journee"], date.fromisoformat(p["date"]) if p["date"] else None, p["equipe"],
                     p["joueur"], p["points"], p["adversaire"], p["points_adv"], f"=G{i}-E{i}",
                     "V" if p["victoire"] else "D", p["gain"], p["adversaires"]])
    ws_p["J1"].comment = Comment("Points gagnés/perdus sur la partie : barème FFTT, coefficient 1 "
                                 "(championnat par équipes). Données : feuilles de match, API publique de la FFTT.",
                                 "Outil Vaires")
    for col, largeur in zip("ABCDEFGHIJK", (9, 11, 13, 26, 9, 26, 11, 8, 10, 9, 22)):
        ws_p.column_dimensions[col].width = largeur
    for ligne in ws_p.iter_rows(min_row=1, max_row=ws_p.max_row):
        for c in ligne:
            c.font = gras if c.row == 1 else police
            c.border = bord
            if c.row == 1:
                c.fill = entete_fond
                c.alignment = centre
    for c in ws_p["B"][1:]:
        c.number_format = "DD/MM/YYYY"
    for c in ws_p["J"][1:]:
        c.number_format = "+0.0;-0.0;0.0"
    ws_p.freeze_panes = "A2"
    ws_p.auto_filter.ref = f"A1:K{ws_p.max_row}"
    n = max(ws_p.max_row, 2)
    rng = {k: f"Parties!${c}$2:${c}${n}" for k, c in
           (("j", "A"), ("date", "B"), ("eq", "C"), ("jo", "D"), ("res", "I"), ("pts", "J"), ("ecart", "H"))}

    def mise_en_forme(ws, nb_lignes, col_delta, col_vict, col_total, entetes):
        for c in ws[1]:
            c.font, c.fill, c.alignment, c.border = gras, entete_fond, centre, bord
        for row in ws.iter_rows(min_row=2, max_row=nb_lignes + 1):
            for c in row:
                c.font, c.border = police, bord
                if c.column > 2:
                    c.alignment = centre
        fin_ = nb_lignes + 1
        for col in (col_delta, col_total):
            zone = f"{col}2:{col}{fin_}"
            ws.conditional_formatting.add(zone, CellIsRule(operator="greaterThan", formula=["0"], fill=vert_clair, font=vert_texte))
            ws.conditional_formatting.add(zone, CellIsRule(operator="lessThan", formula=["0"], fill=rose, font=rouge_texte))
        if col_vict:
            zone = f"{col_vict}2:{col_vict}{fin_}"
            v = f'VALUE(LEFT(${col_vict}2,FIND("/",${col_vict}2)-1))'
            t = f'VALUE(MID(${col_vict}2,FIND("/",${col_vict}2)+1,9))'
            for regle, couleur in ((f"AND({t}>0,{v}={t})", "00B050"), (f"AND({t}>0,{v}*2>{t})", "92D050"),
                                   (f"{v}>0", "FFFF00"), (f"AND({t}>0,{v}=0)", "FF0000")):
                ws.conditional_formatting.add(zone, FormulaRule(formula=[regle], fill=PatternFill("solid", fgColor=couleur),
                                                                font=Font(name="Arial", color="000000"), stopIfTrue=True))
        for i, largeur in enumerate(entetes, start=1):
            ws.column_dimensions[get_column_letter(i)].width = largeur
        ws.freeze_panes = "A2"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    # --- Un onglet par journée ----------------------------------------------------------
    for j in journees:
        ws = wb.create_sheet(f"J{j}", index=len(wb.sheetnames) - 1)
        ws.append(["Equipe", "Joueur", "Points", "Pts +/-", "Victoires", "Meilleure victoire",
                   f"Points J{j}", "Total"])
        lj = [l for l in lignes if l["journee"] == j]
        for i, l in enumerate(lj, start=2):
            cle = f'{rng["j"]},{j},{rng["eq"]},$A{i},{rng["jo"]},$B{i}'
            ws.append([
                l["equipe"], l["joueur"], l["points"],
                f"=SUMIFS({rng['pts']},{cle})",
                f'=COUNTIFS({cle},{rng["res"]},"V")&"/"&COUNTIFS({cle})',
                f'=IF(COUNTIFS({cle},{rng["res"]},"V")=0,"",_xlfn.MAXIFS({rng["ecart"]},{cle},{rng["res"]},"V"))',
                f"=C{i}+H{i}",
                (f'=SUMIFS({rng["pts"]},{rng["jo"]},$B{i},{rng["date"]},"<="&DATE({l["date"][:4]},{int(l["date"][5:7])},{int(l["date"][8:])}))'
                 if l["date"] else f'=SUMIFS({rng["pts"]},{rng["jo"]},$B{i},{rng["j"]},"<="&{j})'),
            ])
            ws[f"C{i}"].number_format = "#,##0"
            ws[f"D{i}"].number_format = "0.0"
            ws[f"F{i}"].number_format = "+0;-0;0"
            ws[f"G{i}"].number_format = "#,##0.0"
            ws[f"H{i}"].number_format = "0.0"
        mise_en_forme(ws, len(lj), "D", "E", "H", (13, 26, 10, 10, 11, 18, 12, 9))
        ws["C1"].comment = Comment("Points officiels du joueur (ceux de sa première feuille de match de la phase).",
                                   "Outil Vaires")
        ws["G1"].comment = Comment("Classement virtuel après la rencontre : points officiels + total depuis la J1.",
                                   "Outil Vaires")
        ws["F1"].comment = Comment("Écart de points avec le mieux classé des joueurs battus dans la journée "
                                   "(positif : il était mieux classé ; négatif : tous les joueurs battus étaient moins "
                                   "bien classés).", "Outil Vaires")
        ws["H1"].comment = Comment("Total des points gagnés/perdus depuis la J1, toutes équipes (une joueuse qui a "
                                   "joué en masculin le vendredi et en féminin le samedi cumule les deux).", "Outil Vaires")

    # --- Cumul ----------------------------------------------------------------------------
    ws = wb.create_sheet("Cumul", index=len(wb.sheetnames) - 1)
    ws.append(["Equipe(s)", "Joueur", "Points"] + [f"J{j}" for j in journees] + ["Total", "Points virtuels", "Victoires"])
    for i, c in enumerate(cumuls, start=2):
        ligne = [", ".join(c["equipes"]), c["joueur"], c["points"]]
        for j in journees:
            cle = f'{rng["jo"]},$B{i},{rng["j"]},{j}'
            ligne.append(f'=IF(COUNTIFS({cle})=0,"",SUMIFS({rng["pts"]},{cle}))')
        ligne.append(f"=SUMIFS({rng['pts']},{rng['jo']},$B{i})")
        ligne.append(f"=C{i}+{get_column_letter(4 + len(journees))}{i}")
        ligne.append(f'=COUNTIFS({rng["jo"]},$B{i},{rng["res"]},"V")&"/"&COUNTIFS({rng["jo"]},$B{i})')
        ws.append(ligne)
        ws.cell(i, 3).number_format = "#,##0"
        for k in range(4, 5 + len(journees)):
            ws.cell(i, k).number_format = "0.0"
        ws.cell(i, 5 + len(journees)).number_format = "#,##0.0"
    col_total = get_column_letter(4 + len(journees))
    col_vict = get_column_letter(6 + len(journees))
    mise_en_forme(ws, len(cumuls), col_total, col_vict, col_total,
                  (16, 26, 10) + (8,) * len(journees) + (9, 15, 11))
    ws.cell(1, 5 + len(journees)).comment = Comment("Classement virtuel : points officiels + total depuis la J1.",
                                                    "Outil Vaires")
    for j_col in range(4, 4 + len(journees)):
        lettre = get_column_letter(j_col)
        zone = f"{lettre}2:{lettre}{len(cumuls) + 1}"
        ws.conditional_formatting.add(zone, CellIsRule(operator="greaterThan", formula=["0"], fill=vert_clair, font=vert_texte))
        ws.conditional_formatting.add(zone, CellIsRule(operator="lessThan", formula=["0"], fill=rose, font=rouge_texte))

    if journees:
        wb.active = wb.sheetnames.index(f"J{journees[-1]}")
    wb.calculation.fullCalcOnLoad = True  # Excel calcule toutes les formules à l'ouverture
    wb.save(chemin)
    return chemin

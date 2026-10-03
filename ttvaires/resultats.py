"""Résultats individuels des joueurs de Vaires, journée par journée (points virtuels FFTT).

Pour chaque journée : l'équipe dans laquelle chaque joueur a joué, ses victoires, les points
gagnés ou perdus (barème FFTT, coefficient 1 du championnat par équipes), sa meilleure
victoire du jour et le total cumulé depuis la J1. Sorties : page HTML triable et classeur Excel.
"""

import json
from collections import defaultdict
from datetime import date, datetime

from . import fftt
from .pingpocket import phase_et_saison
from .reseau import HEURE

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


def points_partie(points, points_adv, victoire, coefficient=COEFFICIENT_CHAMPIONNAT):
    """Points gagnés (ou perdus) par un joueur sur une partie."""
    ecart = abs(points - points_adv)
    _, vn, dn, va, da = next(ligne for ligne in BAREME if ligne[0] is None or ecart < ligne[0])
    if victoire:
        gain = vn if points >= points_adv else va
    else:
        gain = dn if points <= points_adv else da
    return gain * coefficient


def bornes_phase(jour):
    """Dates de début et de fin de la phase en cours."""
    phase, saison = phase_et_saison(jour)
    annee = int(saison[:4])
    return ("%d-07-01" % annee, "%d-12-31" % annee) if phase == 1 else ("%d-01-01" % (annee + 1), "%d-06-30" % (annee + 1))


def recuperer_parties(client, numero_club="08770250", aujourdhui=None):
    """Toutes les parties de simple jouées par les joueurs du club dans la phase en cours
    (championnats masculin et féminin), lues sur l'API publique de la FFTT."""
    aujourdhui = aujourdhui or date.today()
    phase, saison = phase_et_saison(aujourdhui)
    debut, fin = bornes_phase(aujourdhui)
    print(f"Résultats des équipes du club {numero_club} (phase {phase} {saison}, API FFTT)", flush=True)
    id_club = fftt.id_interne_club(client, numero_club, debut)
    rencontres = fftt.rencontres_club(client, id_club, debut, fin, ttl=3 * HEURE)

    nos_equipes = {}  # nom de l'équipe -> (féminine, numéro)
    jouees = []
    for r in rencontres:
        cotes = {c: (r.get(c) or {}).get("team") or {} for c in ("homeOpponent", "awayOpponent")}
        for c, equipe in cotes.items():
            if any(club.get("identifier") == numero_club for club in equipe.get("clubs", [])):
                nos_equipes[equipe["name"]] = (fftt.feminin(r), fftt.numero_equipe(equipe["name"]) or 0)
                if r["date"][:10] <= aujourdhui.isoformat():
                    jouees.append((r, c == "homeOpponent"))
    ordres = {nom: i for i, nom in enumerate(sorted(nos_equipes, key=lambda n: nos_equipes[n]))}

    chemins = [f"/sport_matches/{r['id']}" for r, _ in jouees]
    details = client.get_plusieurs([fftt.API + c for c in chemins], ttl=None, message="feuilles de match",
                                   entetes=fftt.ENTETES, valide=fftt.json_valide)
    parties = []
    for (r, domicile), chemin in zip(jouees, chemins):
        brut = details.get(fftt.API + chemin)
        d = json.loads(brut) if brut else {}
        if not d.get("games") or not d.get("homeSheetMatches"):
            client.oublier(fftt.API + chemin)  # feuille pas encore saisie : on retentera
            continue
        nous, eux = ("home", "away") if domicile else ("away", "home")
        notre_equipe = d[f"{nous}Opponent"]["team"]["name"]
        feminine, numero = nos_equipes[notre_equipe]
        nom = f"VAIRES {numero}{' F' if feminine else ''}"
        for g in d["games"]:
            if g.get("doubleOpposition") or g.get("forfeit") or g.get("notCounted") or g.get("winner") not in ("home", "away"):
                continue
            if not g.get(f"{nous}Player") or not g.get(f"{eux}Player"):
                continue
            j, a = fftt.joueur(g[f"{nous}Player"]), fftt.joueur(g[f"{eux}Player"])
            pts, pts_adv = j["points"] or 500, a["points"] or 500
            victoire = g["winner"] == nous
            parties.append({
                "journee": d["day"]["position"], "date": d["date"][:10],
                "equipe": nom, "ordre": ordres[notre_equipe], "adversaires": d[f"{eux}Opponent"]["team"]["name"],
                "licence": j["licence"], "joueur": j["nom"], "points": pts,
                "adversaire": a["nom"], "points_adv": pts_adv,
                "ecart": pts_adv - pts, "victoire": victoire,
                "gain": points_partie(pts, pts_adv, victoire),
            })
    parties.sort(key=lambda p: (p["journee"], p["date"], p["ordre"], -p["points"], p["joueur"]))
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
        "club": {"numero": numero_club, "nom": "CVTT VAIRES" if numero_club == "08770250" else numero_club},
        "parties": parties,
    }


def synthese(parties):
    """Une ligne par joueur, équipe et journée, plus le cumul par joueur."""
    groupes = defaultdict(list)
    for p in parties:
        groupes[(p["journee"], p["ordre"], p["licence"])].append(p)
    lignes = []
    for (journee, ordre, lic), ps in groupes.items():
        victoires = [p["ecart"] for p in ps if p["victoire"]]
        delta = sum(p["gain"] for p in ps)
        lignes.append({
            "journee": journee, "date": ps[0]["date"], "equipe": ps[0]["equipe"], "ordre": ordre,
            "adversaires": ps[0]["adversaires"], "licence": lic, "joueur": ps[0]["joueur"],
            "points": ps[0]["points"], "delta": delta, "v": len(victoires), "matchs": len(ps),
            "meilleure": max(victoires) if victoires else None, "apres": ps[0]["points"] + delta,
            "detail": [
                f"{'bat' if p['victoire'] else 'perd contre'} {p['adversaire']} ({p['points_adv']}) : "
                + f"{p['gain']:+g}".replace(".", ",")
                for p in ps
            ],
        })
    # Une joueuse peut disputer deux rencontres dans la même journée (masculin le vendredi,
    # féminin le samedi) : les points après une rencontre tiennent compte de celles déjà jouées
    # dans la journée, et chaque ligne rappelle les autres rencontres du jour.
    du_jour = defaultdict(list)
    for ligne in lignes:
        du_jour[(ligne["licence"], ligne["journee"])].append(ligne)
    for rencontres in du_jour.values():
        rencontres.sort(key=lambda l: (l["date"] or "", l["ordre"]))
        cumul_jour = 0.0
        for ligne in rencontres:
            cumul_jour += ligne["delta"]
            ligne["apres"] = ligne["points"] + cumul_jour
            ligne["autres"] = [{"equipe": l["equipe"], "date": l["date"], "delta": l["delta"]}
                               for l in rencontres if l is not ligne]
            ligne["avant_jour"] = cumul_jour - ligne["delta"]

    # Total cumulé de chaque joueur depuis la J1, toutes équipes confondues.
    par_journee = defaultdict(lambda: defaultdict(float))
    for ligne in lignes:
        par_journee[ligne["licence"]][ligne["journee"]] += ligne["delta"]
    for ligne in lignes:
        ligne["total"] = sum(d for j, d in par_journee[ligne["licence"]].items() if j <= ligne["journee"])
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
    cumuls = sorted(joueurs.values(), key=lambda c: (c["ordre"], -c["points"], c["joueur"]))
    return lignes, cumuls


def donnees_page(resultats):
    lignes, cumuls = synthese(resultats["parties"])
    journees = sorted({l["journee"] for l in lignes})
    return {
        **{k: resultats[k] for k in ("genere_le", "saison", "phase", "club")},
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
                                 "(championnat par équipes). Données : feuilles de match pingpocket.fr.",
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
                (f'=C{i}+SUMIFS({rng["pts"]},{rng["j"]},{j},{rng["jo"]},$B{i},{rng["date"]},"<="&DATE({l["date"][:4]},{int(l["date"][5:7])},{int(l["date"][8:])}))'
                 if l["date"] else f"=C{i}+D{i}"),
                f'=SUMIFS({rng["pts"]},{rng["jo"]},$B{i},{rng["j"]},"<="&{j})',
            ])
            ws[f"C{i}"].number_format = "#,##0"
            ws[f"D{i}"].number_format = "0.0"
            ws[f"F{i}"].number_format = "+0;-0;0"
            ws[f"G{i}"].number_format = "#,##0.0"
            ws[f"H{i}"].number_format = "0.0"
        mise_en_forme(ws, len(lj), "D", "E", "H", (13, 26, 10, 10, 11, 18, 12, 9))
        ws["H1"].comment = Comment("Total des points gagnés/perdus depuis la J1 (toutes équipes).", "Outil Vaires")
        ws["G1"].comment = Comment("Points après la rencontre. Une joueuse qui a joué en masculin le vendredi et en "
                                   "féminin le samedi cumule les deux rencontres de la journée.", "Outil Vaires")

    # --- Cumul ----------------------------------------------------------------------------
    ws = wb.create_sheet("Cumul", index=len(wb.sheetnames) - 1)
    ws.append(["Equipe(s)", "Joueur", "Points"] + [f"J{j}" for j in journees] + ["Total", "Victoires"])
    for i, c in enumerate(cumuls, start=2):
        ligne = [", ".join(c["equipes"]), c["joueur"], c["points"]]
        for j in journees:
            cle = f'{rng["jo"]},$B{i},{rng["j"]},{j}'
            ligne.append(f'=IF(COUNTIFS({cle})=0,"",SUMIFS({rng["pts"]},{cle}))')
        ligne.append(f"=SUMIFS({rng['pts']},{rng['jo']},$B{i})")
        ligne.append(f'=COUNTIFS({rng["jo"]},$B{i},{rng["res"]},"V")&"/"&COUNTIFS({rng["jo"]},$B{i})')
        ws.append(ligne)
        ws.cell(i, 3).number_format = "#,##0"
        for k in range(4, 5 + len(journees)):
            ws.cell(i, k).number_format = "0.0"
    col_total = get_column_letter(4 + len(journees))
    col_vict = get_column_letter(5 + len(journees))
    mise_en_forme(ws, len(cumuls), col_total, col_vict, col_total,
                  (16, 26, 10) + (8,) * len(journees) + (9, 11))
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

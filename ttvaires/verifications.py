"""Vérifications : les résultats de chaque journée ont-ils tous été récupérés ?

Pour chaque rencontre déjà jouée, l'état de sa feuille de match dans l'API de la FFTT :
- complet : score et compositions saisis ;
- forfait : rencontre perdue par forfait (pas de feuille de match à attendre) ;
- non_saisi : résultat pas encore saisi ;
- sans_feuille : score saisi, mais pas encore les compositions (brûlages incomplets) ;
- non_recupere : l'API n'a pas répondu (erreur réseau) ;
- du_jour : rencontre du jour, résultat pas encore attendu.

Le bilan se fait équipe par équipe : pour un club de 21 équipes, « J3 : 20/21 » signifie qu'une
équipe n'a pas encore son résultat de la 3e journée.
"""

from . import fftt

LIBELLES = {
    "complet": "complet", "forfait": "forfait",
    "non_saisi": "résultat non saisi",
    "sans_feuille": "score saisi, feuille de match (compositions) pas encore saisie",
    "non_recupere": "non récupéré (l'API FFTT n'a pas répondu)",
    "du_jour": "joué aujourd'hui, résultat pas encore attendu",
}
OK = {"complet", "forfait"}


def etat_detail(d):
    """État d'une rencontre d'après son détail dans l'API (None si l'API n'a pas répondu)."""
    if d is None:
        return "non_recupere"
    if d.get("homeGamePoints") is None:
        return "non_saisi"
    if d.get("forfeit"):
        return "forfait"
    if not (d.get("homeSheetMatches") or d.get("awaySheetMatches")):
        return "sans_feuille"
    return "complet"


def statut(rencontre, etats, aujourdhui):
    """État d'une rencontre : 'exempt', 'a_venir', 'du_jour' ou l'état de sa feuille de match."""
    if not (rencontre.get("homeOpponent") and rencontre.get("awayOpponent")):
        return "exempt"
    jour = rencontre["date"][:10]
    if jour > aujourdhui:
        return "a_venir"
    etat = etats.get(rencontre["id"], "non_recupere")
    return "du_jour" if jour == aujourdhui and etat not in OK else etat


def _ligne(r, etat, equipe=None):
    dom, ext = fftt.equipe(r, "homeOpponent"), fftt.equipe(r, "awayOpponent")
    return {"journee": r["day"]["position"], "date": r["date"][:10], "domicile": dom.get("name"),
            "exterieur": ext.get("name"), "division": fftt.libelle_division(r["division"]["name"]),
            "equipe": equipe, "etat": etat, "libelle": LIBELLES[etat]}


def _uniques(rencontres):
    return list({r["id"]: r for r in rencontres}.values())


def bilan_club(rencontres, etats, aujourdhui, numero, nom=None):
    """Bilan d'un club, journée par journée : équipes dont le résultat est complet / équipes qui
    ont joué (les exemptes ne sont pas attendues)."""
    equipes, journees = set(), {}
    for r in _uniques(rencontres):
        for cote in ("homeOpponent", "awayOpponent"):
            t = fftt.equipe(r, cote)
            if fftt.club_de(t)[0] != numero:
                continue
            equipes.add(("F" if fftt.feminin(r) else "M", t["name"]))  # même nom possible en M et en F
            s = statut(r, etats, aujourdhui)
            if s == "a_venir":
                continue
            j = journees.setdefault(r["day"]["position"], {
                "journee": r["day"]["position"], "dates": set(), "attendues": 0, "completes": 0,
                "exemptes": 0, "du_jour": 0, "manquantes": []})
            if s == "exempt":
                j["exemptes"] += 1
                continue
            j["dates"].add(r["date"][:10])
            if s == "du_jour":
                j["du_jour"] += 1
            else:
                j["attendues"] += 1
                if s in OK:
                    j["completes"] += 1
                else:
                    j["manquantes"].append(_ligne(r, s, t["name"]))
    liste = []
    for j in sorted(journees.values(), key=lambda j: j["journee"]):
        if not (j["attendues"] or j["du_jour"]):
            continue  # journée pas encore jouée (seulement des exemptes)
        j["dates"] = sorted(j["dates"])
        liste.append(j)
    manquantes = sum(len(j["manquantes"]) for j in liste)
    return {"numero": numero, "nom": nom, "equipes": len(equipes), "journees": liste,
            "manquantes": manquantes, "complet": manquantes == 0, "erreur": None}


def bilan_rencontres(rencontres, etats, aujourdhui):
    """Bilan global par journée, rencontre par rencontre (chaque rencontre comptée une fois)."""
    journees = {}
    for r in _uniques(rencontres):
        s = statut(r, etats, aujourdhui)
        if s in ("a_venir", "exempt"):
            continue
        j = journees.setdefault(r["day"]["position"], {"journee": r["day"]["position"], "dates": set(),
                                                       "attendues": 0, "completes": 0, "du_jour": 0})
        j["dates"].add(r["date"][:10])
        if s == "du_jour":
            j["du_jour"] += 1
        else:
            j["attendues"] += 1
            j["completes"] += s in OK
    return [{**j, "dates": sorted(j["dates"])} for j in sorted(journees.values(), key=lambda j: j["journee"])]


# ---------------------------------------------------------------------------
# Affichage dans la console
# ---------------------------------------------------------------------------

def _jj_mm(iso):
    return f"{iso[8:10]}/{iso[5:7]}"


def _dates(dates):
    return _jj_mm(dates[0]) + (f" - {_jj_mm(dates[-1])}" if dates and dates[-1] != dates[0] else "") if dates else ""


def _manque(m):
    adversaire = m["exterieur"] if m["equipe"] == m["domicile"] else m["domicile"]
    return f"{m['equipe']} contre {adversaire}, le {_jj_mm(m['date'])} : {m['libelle']}"


def afficher_club(bilan, titre):
    """Bilan d'un club (les équipes de Vaires) dans la console. Renvoie une ligne de résumé."""
    print(f"--- Vérification : {titre} ---")
    if bilan.get("erreur"):
        print(f"  !! {bilan['erreur']}")
    for j in bilan["journees"]:
        attendues = j["attendues"] + j["du_jour"]
        etat = "OK" if not j["manquantes"] else f"{len(j['manquantes'])} manquant(s)"
        exemptes = f", {j['exemptes']} exempte(s)" if j["exemptes"] else ""
        print(f"  J{j['journee']} ({_dates(j['dates'])}) : {j['completes']}/{attendues} équipes{exemptes} - {etat}")
        for m in j["manquantes"]:
            print(f"     !! {_manque(m)}")
        if j["du_jour"]:
            print(f"     {j['du_jour']} rencontre(s) jouée(s) aujourd'hui : résultat pas encore attendu")
    if not bilan["journees"]:
        print("  aucune rencontre jouée pour le moment")
    if bilan["manquantes"]:
        print("  => Relancer plus tard : les résultats sont en général saisis dans les 48 h après la rencontre.")
        return f"{bilan['manquantes']} résultat(s) manquant(s)"
    return "tous les résultats sont là"


def afficher_adversaires(global_, clubs):
    """Bilan de la page adversaires : par journée, puis les clubs incomplets. Renvoie un résumé."""
    print("--- Vérification : résultats des poules et des clubs adverses ---")
    for j in global_:
        manquent = j["attendues"] - j["completes"]
        print(f"  J{j['journee']} ({_dates(j['dates'])}) : {j['completes']}/{j['attendues']} rencontres complètes"
              + (" - OK" if not manquent else f" - {manquent} manquante(s)")
              + (f" ({j['du_jour']} jouée(s) aujourd'hui)" if j["du_jour"] else ""))
        for c in clubs:
            cj = next((x for x in c["journees"] if x["journee"] == j["journee"]), None)
            if cj and cj["manquantes"]:
                print(f"     !! {c['nom']} : {cj['completes']}/{cj['attendues']} équipes")
                for m in cj["manquantes"]:
                    print(f"          {_manque(m)}")
    print("  Par club (équipes dont le résultat est complet / équipes qui ont joué) :")
    for c in clubs:
        marque = "OK" if c["complet"] and not c.get("erreur") else "!!"
        print(f"    {marque} {c['nom']} ({c['equipes']} équipes) : "
              + (" | ".join(f"J{j['journee']} {j['completes']}/{j['attendues'] + j['du_jour']}" for j in c["journees"])
                 or "aucune rencontre jouée"))
    erreurs = [c for c in clubs if c.get("erreur")]
    for c in erreurs:
        print(f"  !! {c['nom']} : {c['erreur']}")
    complets = sum(c["complet"] and not c.get("erreur") for c in clubs)
    print(f"  Clubs entièrement à jour : {complets}/{len(clubs)}")
    total = sum(c["manquantes"] for c in clubs)
    if total or erreurs:
        print("  => Relancer plus tard : les résultats sont en général saisis dans les 48 h après la rencontre.")
        return f"{total} résultat(s) manquant(s)" + (f", {len(erreurs)} club(s) non récupéré(s)" if erreurs else "")
    return "tous les résultats sont là"


def afficher_controle_parties(controle):
    """Contrôles propres au classement virtuel. Renvoie les lignes de résumé (vide si tout va bien)."""
    resume = []
    print("--- Vérification : parties des joueurs (toutes compétitions) ---")
    if controle["sans_reponse"]:
        print(f"  !! parties non lues (l'API FFTT n'a pas répondu) : {', '.join(controle['sans_reponse'])}")
        resume.append(f"parties non lues pour {len(controle['sans_reponse'])} joueur(s)")
    for a in controle["parties_absentes"]:
        print(f"  !! {a['joueur']} : {a['nb']} partie(s) de championnat de la feuille de match absente(s) de sa liste de parties")
    if controle["parties_absentes"]:
        resume.append(f"parties de championnat pas encore propagées pour {len(controle['parties_absentes'])} joueur(s)")
    if not controle["liste"]:
        print("  !! liste des licenciés indisponible : seuls les joueurs alignés en championnat sont classés")
        resume.append("liste des licenciés indisponible (voir import/LISEZ-MOI.txt)")
    if not resume:
        print("  OK : parties lues pour tous les joueurs, cohérentes avec les feuilles de match")
    print("  (les compétitions individuelles - critérium, tournois - ne peuvent pas être vérifiées : l'outil")
    print("   ne sait pas à l'avance qui y a participé ; il prend toutes les parties connues de la FFTT)")
    return resume

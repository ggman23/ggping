"""Page « Clubs du 77 » : le niveau de Vaires parmi les clubs de Seine-et-Marne.

Pour chaque club du département engagé en championnat par équipes :
- ses équipes et leurs divisions (nationale, régionale, départementale 1, 2...), et leurs poules :
  API de la FFTT (rencontres de la phase, une liste par club, gardée une semaine) ;
- ses licenciés (sexe, catégorie d'âge, points, licences loisir) : listes de pingpocket.fr, comme pour
  les clubs adverses (deux pages par club : par catégorie et par état de licence). Elles sont lues par le
  PC (une page toutes les 4 secondes), au plus MAX_LISTES nouvelles pages par lancement, et gardées un
  mois ; la mise à jour en ligne se sert de celles que le PC a envoyées.

Les clubs du département sont ceux des rencontres des journées 1 et 2 des divisions du comité (D77),
la requête qui sert déjà à trouver l'identifiant d'un club : un club sans aucune équipe départementale
n'y figure pas. Seuls les licenciés de la saison (licences renouvelées) comptent.

Force d'une équipe (estimation, pour voir les favoris d'une poule) : la moyenne des points des quatre
joueurs que son numéro lui donne dans le club, par points décroissants (équipe 1 : joueurs 1 à 4, équipe
2 : 5 à 8...) ; les équipes féminines, parmi les joueuses. Elle ne tient compte ni des brûlages ni des
absences : c'est un ordre de grandeur.
"""

import time
from collections import Counter
from datetime import datetime

from . import fftt, pingpocket
from .effectif import TRIS
from .reseau import JOUR

DEPARTEMENT = "77"
SITE_PINGPOCKET = "www.pingpocket.fr"
MAX_LISTES = 60          # pages de listes de licenciés téléchargées au plus par lancement (4 minutes)
TTL_LISTES = 30 * JOUR   # une liste de licenciés change peu une fois la saison lancée
TTL_EQUIPES = 7 * JOUR   # équipes engagées : fixées pour la phase
LISTES = ("categories", "etat")  # la liste par classement n'apporte rien ici
JOUEURS_PAR_EQUIPE = 4
CATEGORIES = ["P", "B", "M", "C", "J", "S", "V"]  # poussins ... vétérans
# Ordre des niveaux, du plus haut au plus bas (pour trier les clubs par leur meilleure équipe)
ORDRE_NIVEAUX = ["N1", "N2", "N3", "PN", "R1", "R2", "R3", "R4", "PR", "D1", "D2", "D3", "D4", "D5", "D6"]


def rang_niveau(niveau):
    return ORDRE_NIVEAUX.index(niveau) if niveau in ORDRE_NIVEAUX else len(ORDRE_NIVEAUX)


def _url_journee(debut, journee):
    q = fftt._q
    return (f"/sport_matches?{q('division.organization.identifier')}=D{DEPARTEMENT}&{q('day.position')}={journee}"
            f"&{q('date[after]')}={debut}&itemsPerPage=200")


def clubs_du_departement(client, debut):
    """Clubs du département engagés en championnat (rencontres des journées 1 et 2 du comité) :
    {numéro FFTT: {"id": identifiant interne, "nom"}}."""
    clubs = {}
    for journee in (1, 2):  # une équipe exempte à la 1re journée joue la 2e
        for r in fftt.lire_tout(client, _url_journee(debut, journee), 30 * JOUR):
            for cote in ("homeOpponent", "awayOpponent"):
                num, id_, nom = fftt.club_de(fftt.equipe(r, cote))
                if num and id_ and num.startswith(f"08{DEPARTEMENT}"):
                    clubs.setdefault(num, {"id": id_, "nom": nom or num})
    return clubs


def equipes_et_poules(client, clubs, debut, fin):
    """Équipes de chaque club (toutes divisions) et poules où jouent les clubs du département.

    Renvoie ({numéro: [équipe]}, {id de poule: poule}) ; équipe : {nom, numero, feminin, division,
    niveau, poule} ; poule : {id, division, niveau, feminin, nom, equipes: [{nom, club, numero}]}."""
    equipes, poules = {}, {}
    for num, club in clubs.items():
        vues = {}
        for r in fftt.rencontres_club(client, club["id"], debut, fin, ttl=TTL_EQUIPES):
            pool = r.get("pool") or {}
            division = r["division"]["name"]
            p = poules.setdefault(pool.get("id"), {
                "id": pool.get("id"), "division": fftt.libelle_division(division), "niveau": fftt.division_courte(division),
                "feminin": fftt.feminin(r), "nom": pool.get("name") or "", "equipes": {}})
            for cote in ("homeOpponent", "awayOpponent"):
                t = fftt.equipe(r, cote)
                if not t.get("name"):
                    continue
                n_club = fftt.club_de(t)[0]
                p["equipes"][t["name"]] = {"nom": t["name"], "club": n_club, "numero": fftt.numero_equipe(t["name"]) or 0}
                if n_club == num:  # (une équipe féminine peut porter le même nom qu'une équipe masculine)
                    vues.setdefault((t["name"], fftt.feminin(r)), {"nom": t["name"], "numero": fftt.numero_equipe(t["name"]) or 0,
                                                "feminin": fftt.feminin(r), "division": fftt.libelle_division(division),
                                                "niveau": fftt.division_courte(division), "poule": pool.get("id")})
        equipes[num] = sorted(vues.values(), key=lambda e: (e["feminin"], e["numero"]))
    for p in poules.values():
        p["equipes"] = sorted(p["equipes"].values(), key=lambda e: e["nom"])
    return equipes, poules


def listes_licencies(client, clubs, dossier_import=None):
    """Listes de licenciés (par catégorie, par état de licence) de chaque club : {numéro: (pages, date)}.

    Sur le PC : au plus MAX_LISTES nouvelles pages par lancement (les clubs déjà lus d'abord gardés),
    les autres au lancement suivant. En ligne (pingpocket.fr refuse les serveurs de GitHub) et hors
    ligne : seules les pages déjà en cache (envoyées par le PC). Les pages enregistrées depuis un
    navigateur (dossier import) servent aussi, si elles sont plus récentes."""
    liens = {num: {t: f"/app/fftt/clubs/{num}/licencies?SORT={TRIS[t]}" for t in LISTES} for num in clubs}
    disponible = getattr(client, "disponible", lambda site: True)
    muet = (not disponible(SITE_PINGPOCKET) or SITE_PINGPOCKET in getattr(client, "sites_cache_seul", ())
            or getattr(client, "hors_ligne", False))
    toutes = [u for l in liens.values() for u in l.values()]
    if muet:
        a_lire = [u for u in toutes if client.date(u) is not None]
        reportees = 0
    else:
        nouvelles = [u for u in toutes if not client.en_cache(u, TTL_LISTES)]
        reportees = max(0, len(nouvelles) - MAX_LISTES)
        exclues = set(nouvelles[MAX_LISTES:])
        a_lire = [u for u in toutes if u not in exclues]
        if len(nouvelles) - reportees > 15:
            print(f"  {len(nouvelles) - reportees} listes à télécharger : environ {(len(nouvelles) - reportees) * 4 // 60 + 1} "
                  "minutes (une page toutes les 4 secondes) ; gardées un mois.", flush=True)
    pages = client.get_plusieurs(a_lire, ttl=TTL_LISTES, message="listes des clubs", perime_si_erreur=True) if a_lire else {}
    importees = pingpocket.listes_du_dossier(dossier_import)[0] if dossier_import else {}
    res = {}
    for num, l in liens.items():
        listes = {t: pages[u] for t, u in l.items() if pages.get(u)}
        dates = {t: client.date(u) for t, u in l.items() if pages.get(u)}
        for t, imp in importees.get(num, {}).items():
            if t in LISTES and (t not in listes or imp["date"] > (dates.get(t) or 0)):
                listes[t], dates[t] = imp["html"], imp["date"]
        if all(t in listes for t in LISTES):
            res[num] = (listes, min(d for d in dates.values() if d) if any(dates.values()) else time.time())
    return res, reportees


def joueurs_du_club(listes):
    """Licenciés de la saison (licences renouvelées) : [{nom, prenom, sexe, cat, points, loisir}]."""
    sortie = []
    for j in pingpocket.licencies(listes, {t: t for t in TRIS}):
        if not j.get("renouvele"):
            continue
        cat = (j.get("categorie") or "")[:1].upper()
        sortie.append({"nom": j.get("nom"), "prenom": j.get("prenom"), "sexe": j.get("sexe") or "M",
                       "cat": cat if cat in CATEGORIES else "", "points": j.get("points_mensuels"), "loisir": bool(j.get("loisir"))})
    return sortie


def force_des_equipes(equipes, joueurs):
    """Force estimée de chaque équipe (moyenne des points des joueurs que son numéro lui donne dans le
    club) : {(nom de l'équipe, féminine ?): {"force", "nb"}}."""
    competition = [j for j in joueurs if not j["loisir"] and j["points"]]
    tous = sorted((j["points"] for j in competition), reverse=True)
    femmes = sorted((j["points"] for j in competition if j["sexe"] == "F"), reverse=True)
    res = {}
    for e in equipes:
        groupe = (femmes if e["feminin"] else tous)[JOUEURS_PAR_EQUIPE * (e["numero"] - 1): JOUEURS_PAR_EQUIPE * e["numero"]] \
            if e["numero"] else []
        res[(e["nom"], e["feminin"])] = {"force": round(sum(groupe) / len(groupe)) if groupe else None, "nb": len(groupe)}
    return res


def recuperer_departement(client, numero_club="08770250", aujourdhui=None, dossier_import=None):
    aujourdhui = aujourdhui or datetime.now().date()
    phase, saison = fftt.phase_et_saison(aujourdhui)
    debut, fin = fftt.bornes_phase(aujourdhui)
    print(f"1/3 Clubs de Seine-et-Marne engagés en championnat (phase {phase} {saison}, API FFTT)", flush=True)
    clubs = clubs_du_departement(client, debut)
    print(f"2/3 Équipes et divisions des {len(clubs)} clubs (API FFTT, gardées une semaine)", flush=True)
    equipes, poules = equipes_et_poules(client, clubs, debut, fin)
    print("3/3 Licenciés des clubs (pingpocket.fr, listes gardées un mois)", flush=True)
    listes, reportees = listes_licencies(client, clubs, dossier_import)

    sortie, sans_liste = [], []
    for num, club in sorted(clubs.items(), key=lambda x: x[1]["nom"]):
        eqs = equipes.get(num, [])
        joueurs = joueurs_du_club(listes[num][0]) if num in listes else None
        if joueurs is None:
            sans_liste.append(club["nom"])
        forces = force_des_equipes(eqs, joueurs or [])
        niveaux = Counter(("F:" if e["feminin"] else "") + (e["niveau"] or "?") for e in eqs)
        competition = sorted((j for j in joueurs or [] if not j["loisir"]), key=lambda j: -(j["points"] or 0))
        sortie.append({
            "numero": num, "nom": club["nom"], "vaires": num == numero_club,
            "date_liste": datetime.fromtimestamp(listes[num][1]).isoformat(timespec="minutes") if num in listes else None,
            "equipes": [{**e, **forces[(e["nom"], e["feminin"])]} for e in eqs], "niveaux": dict(niveaux),
            "meilleur_niveau": min((e["niveau"] for e in eqs if not e["feminin"]), key=rang_niveau, default=None),
            # Joueurs : [points, sexe, catégorie, loisir] (sans nom) pour les statistiques de la page ; les noms
            # des 10 meilleurs seulement, pour la fiche du club
            "joueurs": [[j["points"], j["sexe"], j["cat"], 1 if j["loisir"] else 0] for j in joueurs] if joueurs is not None else None,
            "meilleurs": [{"nom": j["nom"], "prenom": j["prenom"], "sexe": j["sexe"], "cat": j["cat"], "points": j["points"]}
                          for j in competition[:10]],
        })
    poules_sortie = []
    for p in poules.values():
        if not p["id"]:
            continue
        par_club = {c["numero"]: c for c in sortie}
        lignes = []
        for e in p["equipes"]:
            club = par_club.get(e["club"])
            force = next((x for x in (club or {}).get("equipes", []) if x["nom"] == e["nom"] and x["feminin"] == p["feminin"]),
                         {}) if club else {}
            lignes.append({"nom": e["nom"], "club": e["club"], "force": force.get("force"), "nb": force.get("nb", 0),
                           "vaires": e["club"] == numero_club, "dans_le_77": club is not None})
        lignes.sort(key=lambda x: (x["force"] is None, -(x["force"] or 0), x["nom"]))
        poules_sortie.append({"id": p["id"], "division": p["division"], "niveau": p["niveau"], "feminin": p["feminin"],
                              "nom": p["nom"], "equipes": lignes})
    poules_sortie.sort(key=lambda p: (p["feminin"], rang_niveau(p["niveau"]), p["division"], str(p["nom"]), str(p["id"])))
    return {"genere_le": datetime.now().isoformat(timespec="minutes"), "saison": saison, "phase": phase,
            "departement": DEPARTEMENT, "club": numero_club, "clubs": sortie, "poules": poules_sortie,
            "categories": CATEGORIES, "ordre_niveaux": ORDRE_NIVEAUX, "joueurs_par_equipe": JOUEURS_PAR_EQUIPE,
            "controle": {"clubs": len(sortie), "sans_liste": sans_liste, "listes_reportees": reportees}}


def resume(donnees):
    c = donnees["controle"]
    avec = c["clubs"] - len(c["sans_liste"])
    return (f"{c['clubs']} clubs, {sum(len(x['equipes']) for x in donnees['clubs'])} équipes, licenciés connus pour {avec} clubs"
            + (f" ({c['listes_reportees']} listes au prochain lancement sur le PC)" if c["listes_reportees"] else ""))

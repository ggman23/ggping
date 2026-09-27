"""Jeu de données fictif pour tester la page sans accès à Internet."""

import random
from datetime import datetime

NOMS = ["MARTIN", "BERNARD", "DUBOIS", "THOMAS", "ROBERT", "RICHARD", "PETIT", "DURAND", "LEROY",
        "MOREAU", "SIMON", "LAURENT", "LEFEBVRE", "MICHEL", "GARCIA", "DAVID", "BERTRAND", "ROUX",
        "VINCENT", "FOURNIER", "MOREL", "GIRARD", "ANDRE", "MERCIER", "DUPONT", "LAMBERT", "BONNET"]
PRENOMS_M = ["Paul", "Lucas", "Hugo", "Louis", "Nathan", "Jules", "Marc", "Eric", "Thierry", "Karim",
             "Olivier", "Julien", "Maxime", "Antoine", "Sébastien", "Yann", "Rémi", "Bruno"]
PRENOMS_F = ["Emma", "Léa", "Chloé", "Manon", "Sarah", "Julie", "Laura", "Inès", "Camille"]
CATEGORIES = ["S", "S", "S", "V1", "V1", "V2", "V3", "J2", "C1", "M2"]
CLUBS_FICTIFS = ["AS DEMOVILLE", "TT FICTIVILLE", "US EXEMPLE", "CS BAC-A-SABLE", "ES MAQUETTE",
                 "PING TESTEUR", "AL PROTOTYPE", "TT SIMULATION", "US ESSAI", "CO BROUILLON",
                 "AS MODELE", "TT ECHANTILLON"]
DATES_M = ["2026-09-11", "2026-09-25", "2026-10-02", "2026-10-16", "2026-11-06", "2026-11-20", "2026-12-04"]
DATES_F = ["2026-09-12", "2026-09-26", "2026-10-10", "2026-10-17", "2026-11-14", "2026-11-28", "2026-12-05"]
JOUES = 2  # journées déjà jouées dans la démo


def _joueur(rng, num, points, sexe="M"):
    prenom = rng.choice(PRENOMS_F if sexe == "F" else PRENOMS_M)
    meilleur = None
    if rng.random() < 0.8:
        pic = points + max(0, int(rng.gauss(150, 250)))
        meilleur = {"points": pic, "annee": str(rng.randint(2008, 2026))}
    return {
        "id": num, "licence": num, "nom": rng.choice(NOMS), "prenom": prenom, "sexe": sexe,
        "categorie": rng.choice(CATEGORIES), "points": points,
        "points_mensuels": points + rng.randint(-40, 60), "meilleur": meilleur,
        "renouvele": rng.random() > 0.08,
    }


def _club(rng, i, nom, nb_equipes):
    numero = f"087{i:05d}"
    joueurs, titulaires = [], {}
    for n in range(1, nb_equipes + 1):
        titulaires[n] = []
        for k in range(4):
            sexe = "F" if rng.random() < 0.12 else "M"
            j = _joueur(rng, f"{numero[-3:]}{n:02d}{k}", max(500, int(2300 - n * 85 + rng.gauss(0, 60))), sexe)
            j["renouvele"] = True
            joueurs.append(j)
            titulaires[n].append(j["id"])
    for k in range(rng.randint(4, 12)):  # joueurs pas encore alignés / non renouvelés
        joueurs.append(_joueur(rng, f"{numero[-3:]}99{k}", rng.randint(500, 1600), rng.choice("MMMF")))

    equipes = []
    for n in range(1, nb_equipes + 1):
        equipes.append({"libelle": f"{nom} {n}", "numero": n, "championnat": "M",
                        "division": "Régionale 3" if n <= 2 else f"Départementale {min(4, 1 + (n - 3) // 3)}",
                        "compositions": []})
    for jn in range(1, JOUES + 1):
        deja = set()
        for eq in equipes:
            n = eq["numero"]
            compo = [t for t in titulaires[n] if t not in deja and rng.random() > 0.15]
            # Un joueur d'une équipe plus forte vient parfois renforcer, un plus faible compléter.
            if n > 1 and rng.random() < 0.35:
                compo += [t for t in titulaires[n - 1] if t not in deja and t not in compo][:1]
            for t in titulaires.get(n + 1, []):
                if len(compo) >= 4:
                    break
                if t not in deja and t not in compo:
                    compo.append(t)
            compo = compo[:4]
            deja.update(compo)
            eq["compositions"].append({"journee": jn, "date": DATES_M[jn - 1], "joueurs": compo})

    filles = [j for j in joueurs if j["sexe"] == "F" and j["renouvele"]]
    filles.sort(key=lambda j: -j["points"])
    if len(filles) >= 3:
        eqf = {"libelle": f"{nom} 1", "numero": 1, "championnat": "F", "division": "Régionale féminine",
               "compositions": [{"journee": jn, "date": DATES_F[jn - 1], "joueurs": [f["id"] for f in filles[:3]]}
                                for jn in range(1, JOUES + 1)]}
        equipes.append(eqf)

    return {
        "numero": numero, "nom": nom, "joueurs": joueurs, "equipes": equipes,
        "salle": {"nom": f"Gymnase {nom.split()[-1].title()}", "adresse": f"{rng.randint(1, 80)} rue de l'Exemple",
                  "cp": f"77{rng.randint(100, 999)}", "ville": nom.split()[-1]},
    }


def _poule(rng, vaires, adversaires, dates, heure):
    """Calendrier aller simple à 8 équipes (méthode du tourniquet), scores des journées jouées."""
    equipes = [vaires] + adversaires
    rencontres, bilan = [], {e["libelle"]: {"v": 0, "n": 0, "d": 0, "points": 0, "joues": 0} for e in equipes}
    rot = equipes[1:]
    for jn in range(1, 8):
        tour = [equipes[0]] + rot
        paires = [(tour[k], tour[7 - k]) for k in range(4)]
        for a, b in paires:
            dom, ext = (a, b) if (jn + tour.index(a)) % 2 == 0 else (b, a)
            score = None
            if jn <= JOUES:
                x = rng.randint(2, 12)
                score = [x, 14 - x]
                for eq, pour, contre in ((dom, score[0], score[1]), (ext, score[1], score[0])):
                    bl = bilan[eq["libelle"]]
                    bl["joues"] += 1
                    cle = "v" if pour > contre else "n" if pour == contre else "d"
                    bl[cle] += 1
                    bl["points"] += {"v": 3, "n": 2, "d": 1}[cle]
            if vaires in (dom, ext):
                adv = ext if dom is vaires else dom
                rencontres.append({
                    "journee": jn, "date": dates[jn - 1], "heure": heure, "date_reelle": None,
                    "domicile": {"libelle": dom["libelle"], "club": dom["club"]},
                    "exterieur": {"libelle": ext["libelle"], "club": ext["club"]},
                    "vaires_domicile": dom is vaires, "score": score,
                    "adversaire": {"club": adv["club"], "libelle": adv["libelle"], "numero": adv.get("numero")},
                })
        rot = rot[-1:] + rot[:-1]
    classement = sorted(({"libelle": e["libelle"], "club": e["club"], **bilan[e["libelle"]]} for e in equipes),
                        key=lambda c: -c["points"])
    for rang, c in enumerate(classement, 1):
        c["rang"] = rang
    return rencontres, classement


def donnees_demo(graine=77):
    rng = random.Random(graine)
    clubs = {}
    for i, nom in enumerate(CLUBS_FICTIFS, 1):
        c = _club(rng, i, nom, rng.randint(8, 20))
        clubs[c["numero"]] = c
    vaires = {"numero": "08770250", "nom": "CVTT VAIRES",
              "salle": {"nom": "COSEC", "adresse": "Rue de l'Écluse", "cp": "77360", "ville": "Vaires-sur-Marne"}}
    niveaux = [(1, "Départementale 1", (3, 6)), (2, "Départementale 1", (4, 7)), (3, "Départementale 2", (5, 9)),
               (4, "Départementale 2", (6, 10)), (5, "Départementale 3", (7, 13)), (6, "Départementale 4", (8, 20))]
    equipes = []
    for n, division, (bas, haut) in niveaux:
        adversaires = []
        for club in rng.sample(list(clubs.values()), 7):
            nums = [e["numero"] for e in club["equipes"] if e["championnat"] == "M" and bas <= e["numero"] <= haut]
            num = rng.choice(nums or [max(e["numero"] for e in club["equipes"] if e["championnat"] == "M")])
            adversaires.append({"libelle": f"{club['nom']} {num}", "club": club["numero"], "numero": num})
        v = {"libelle": f"VAIRES {n}", "club": vaires["numero"]}
        rencontres, classement = _poule(rng, v, adversaires, DATES_M, "20:30")
        equipes.append({"id": f"v{n}", "libelle": f"VAIRES {n}", "nom_court": f"Vaires {n}", "numero": n,
                        "championnat": "M", "division": division, "poule": f"Poule {'ABCDEF'[n - 1]}",
                        "jour": "vendredi", "rencontres": rencontres, "classement": classement})
    feminines = [c for c in clubs.values() if any(e["championnat"] == "F" for e in c["equipes"])]
    adversaires = [{"libelle": f"{c['nom']} 1", "club": c["numero"], "numero": 1} for c in feminines[:7]]
    rencontres, classement = _poule(rng, {"libelle": "VAIRES 1", "club": vaires["numero"]}, adversaires, DATES_F, "15:00")
    equipes.append({"id": "v1f", "libelle": "VAIRES 1 (féminine)", "nom_court": "Vaires 1 F", "numero": 1,
                    "championnat": "F", "division": "Régionale féminine", "poule": "Poule unique",
                    "jour": "samedi", "rencontres": rencontres, "classement": classement})
    return {"demo": True, "genere_le": datetime.now().isoformat(timespec="minutes"), "saison": "2026-2027",
            "phase": 1, "club": vaires, "equipes": equipes, "clubs": clubs}

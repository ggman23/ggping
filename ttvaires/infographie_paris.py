"""Infographie du championnat de Paris au format téléphone (paris_infographie.png) : pas un tableau.

Bandeau bleu nuit avec une grande tour Eiffel en filigrane, les chiffres clés (équipes, journées, clubs
adverses par département), la prochaine journée en trois cartes, puis pour chaque équipe de Vaires une
frise de ses 7 journées : un point vert à domicile, orange à l'extérieur, gris une fois la date passée.
Données : poules et calendrier de paris.py. Faite par l'étape adversaires, groupe d'images « paris ».
"""

import re
from collections import Counter
from datetime import date

from PIL import Image, ImageDraw

from . import paris
from .images import _enregistrer, _nettoyer, ajuster, couper, largeur_texte, police

LARGEUR, S, MARGE = 1080, 2, 36
FOND_HAUT, FOND_BAS = (14, 32, 58), (27, 58, 99)
FILIGRANE = (36, 66, 104)
BLANC, NUIT, DOUX_CLAIR, DOUX = (255, 255, 255), (16, 35, 62), (196, 210, 228), (98, 110, 128)
OR = (246, 196, 76)
TUILE = (33, 63, 101)
VERT, VERT_FOND, ORANGE, ORANGE_FOND, GRIS = (29, 138, 82), (225, 245, 233), (214, 116, 20), (253, 238, 220), (170, 176, 186)
COULEURS_EQUIPES = [(204, 16, 40), (31, 95, 191), (16, 133, 122)]
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
SIGLES = {"SP", "TT", "CTT", "JA", "AP", "EP", "SE", "US", "CVTT", "ATT", "CS", "ASL", "AS"}
PETITS = {"LE", "LES", "LA", "DE", "DU", "DES", "SUR", "S"}


def joli_nom(nom):
    """« NOISY LE GRAND 1 » -> « Noisy le Grand 1 », « NEUILLY S/MARNE TT 2 » -> « Neuilly s/Marne TT 2 »."""
    def mot(m, premier):
        if m in SIGLES or m.isdigit():
            return m
        if m in PETITS and not premier:
            return m.lower()
        return "-".join(p[:1] + p[1:].lower() for p in m.split("-"))
    sortie = []
    for i, bloc in enumerate(nom.split()):
        sortie.append("/".join(mot(p, i == 0 and j == 0) for j, p in enumerate(bloc.split("/"))))
    return " ".join(sortie)


def _date_courte(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {MOIS[d.month - 1]}"


def _tour_eiffel(d, x, y, taille, couleur):
    """Tour Eiffel (comme le pictogramme du programme), dans un carré de côté `taille` en (x, y)."""
    P = lambda u, v: ((x + u * taille) * S, (y + v * taille) * S)  # noqa: E731
    d.polygon([P(0.5, 0.0), P(0.46, 0.17), P(0.54, 0.17)], fill=couleur)
    d.polygon([P(0.46, 0.17), P(0.54, 0.17), P(0.58, 0.44), P(0.42, 0.44)], fill=couleur)
    d.rectangle([*P(0.37, 0.44), *P(0.63, 0.49)], fill=couleur)
    d.polygon([P(0.41, 0.49), P(0.59, 0.49), P(0.67, 0.67), P(0.33, 0.67)], fill=couleur)
    d.rectangle([*P(0.26, 0.67), *P(0.74, 0.72)], fill=couleur)
    d.polygon([P(0.30, 0.72), P(0.70, 0.72), P(0.86, 1.0), P(0.70, 1.0), P(0.60, 0.82), P(0.40, 0.82),
               P(0.30, 1.0), P(0.14, 1.0)], fill=couleur)


def _texte(d, xy, texte, taille, couleur, gras=False):
    d.text((xy[0] * S, xy[1] * S), texte, font=police(taille, gras), fill=couleur)


def _pilule(d, x, y, texte, fond, couleur, taille=20, h=34):
    w = largeur_texte(texte, taille, True) + 24
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=h / 2 * S, fill=fond)
    _texte(d, (x + 12, y + (h - taille) / 2 - 1), texte, taille, couleur, True)
    return w


def donnees_infographie(aujourdhui):
    """Équipes de Vaires (division, poule, rencontres), prochaine journée et départements des adversaires."""
    p = paris.donnees()
    auj = aujourdhui.isoformat()
    prochaine = next((j for j in p["journees"] if j["date"] >= auj), None)
    clubs = {}
    for e in paris.EQUIPES:
        for num, _, _, dep in e["equipes"]:
            if num != paris.CLUB_VAIRES:
                clubs[num] = dep
    return {"equipes": p["equipes"], "prochaine": prochaine, "departements": Counter(clubs.values()),
            "clubs": len(clubs), "journees": p["journees"], "saison": p["saison"], "auj": auj}


def dessiner(info):
    equipes = info["equipes"]
    H_TETE, H_PROCHAINE, H_LIGNE, H_EQ_TETE = 330, 300 if info["prochaine"] else 0, 56, 96
    h_equipe = H_EQ_TETE + 7 * H_LIGNE + 10
    hauteur = H_TETE + H_PROCHAINE + len(equipes) * (h_equipe + 24) + 30
    img = Image.new("RGB", (LARGEUR * S, hauteur * S), FOND_HAUT)
    d = ImageDraw.Draw(img)
    # Dégradé bleu nuit
    for y in range(hauteur * S):
        t = y / (hauteur * S)
        d.line([(0, y), (LARGEUR * S, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(FOND_HAUT, FOND_BAS)))
    _tour_eiffel(d, LARGEUR - 280, 8, 228, FILIGRANE)  # au-dessus des chiffres clés

    # Titre
    _texte(d, (MARGE, 40), "CHAMPIONNAT", 46, BLANC, True)
    _texte(d, (MARGE, 92), "DE PARIS", 84, OR, True)
    _texte(d, (MARGE, 190), f"CVTT Vaires · saison {info['saison'].replace('-', '–')}", 28, DOUX_CLAIR)
    # Chiffres clés
    deps = info["departements"]
    tuiles = [(str(len(equipes)), "équipes"), ("7", "journées"), (str(info["clubs"]), "clubs adverses"),
              (" · ".join(f"{n}" for _, n in sorted(deps.items(), key=lambda x: x[0])), " · ".join(sorted(deps)))]
    largeur_t = (LARGEUR - 2 * MARGE - 3 * 14) / 4
    for i, (chiffre, libelle) in enumerate(tuiles):
        x = MARGE + i * (largeur_t + 14)
        d.rounded_rectangle([x * S, 246 * S, (x + largeur_t) * S, 316 * S], radius=16 * S, fill=TUILE)
        t, taille = ajuster(chiffre, largeur_t - 20, 34, True)
        _texte(d, (x + (largeur_t - largeur_texte(t, taille, True)) / 2, 252), t, taille, OR, True)
        t, taille = ajuster(libelle if i < 3 else f"dép. {libelle}", largeur_t - 16, 19)
        _texte(d, (x + (largeur_t - largeur_texte(t, taille)) / 2, 290), t, taille, DOUX_CLAIR)
    y = H_TETE + 8

    # Prochaine journée : une carte par équipe
    if info["prochaine"]:
        j = info["prochaine"]
        jour = date.fromisoformat(j["date"])
        _texte(d, (MARGE, y), "PROCHAINE JOURNÉE", 24, OR, True)
        _texte(d, (MARGE, y + 32), f"J{j['numero']} · {JOURS[jour.weekday()]} {jour.day} {MOIS[jour.month - 1].rstrip('.')}",
               34, BLANC, True)
        y += 90
        lc = (LARGEUR - 2 * MARGE - 2 * 16) / 3
        for i, e in enumerate(equipes):
            r = next(r for r in e["rencontres"] if r["journee"] == j["numero"])
            x = MARGE + i * (lc + 16)
            d.rounded_rectangle([x * S, y * S, (x + lc) * S, (y + 190) * S], radius=20 * S, fill=BLANC)
            d.rounded_rectangle([x * S, y * S, (x + lc) * S, (y + 12) * S], radius=6 * S, fill=COULEURS_EQUIPES[i % 3])
            _texte(d, (x + 18, y + 26), e["nom_court"].upper(), 26, NUIT, True)
            _texte(d, (x + 18, y + 60), "reçoit" if r["vaires_domicile"] else "se déplace à", 20, DOUX)
            for k, l in enumerate(couper(joli_nom(r["adversaire"]["libelle"]), lc - 36, 25, True)[:2]):
                _texte(d, (x + 18, y + 88 + k * 30), l, 25, NUIT, True)
            dom = r["vaires_domicile"]
            _pilule(d, x + 18, y + 146, "Domicile" if dom else "Extérieur", VERT_FOND if dom else ORANGE_FOND,
                    VERT if dom else ORANGE)
        y += 190 + 20

    # Chaque équipe : frise des 7 journées
    for i, e in enumerate(equipes):
        couleur = COULEURS_EQUIPES[i % 3]
        d.rounded_rectangle([MARGE * S, y * S, (LARGEUR - MARGE) * S, (y + h_equipe) * S], radius=24 * S, fill=BLANC)
        d.rounded_rectangle([MARGE * S, y * S, (LARGEUR - MARGE) * S, (y + 80) * S], radius=24 * S, fill=couleur)
        d.rectangle([MARGE * S, (y + 56) * S, (LARGEUR - MARGE) * S, (y + 80) * S], fill=couleur)
        _texte(d, (MARGE + 26, y + 14), e["nom_court"].upper(), 36, BLANC, True)
        _texte(d, (MARGE + 30 + largeur_texte(e["nom_court"].upper(), 36, True) + 14, y + 26),
               f"{e['division']} · {e['poule'].lower()}", 24, BLANC)
        nb_dom = sum(r["vaires_domicile"] for r in e["rencontres"])
        texte = f"{nb_dom} à dom. · {len(e['rencontres']) - nb_dom} à l'ext."
        _texte(d, (LARGEUR - MARGE - 24 - largeur_texte(texte, 20, True), y + 30), texte, 20, BLANC, True)
        y0 = y + H_EQ_TETE
        x_ligne = MARGE + 190
        d.line([x_ligne * S, (y0 + H_LIGNE / 2) * S, x_ligne * S, (y0 + 6.5 * H_LIGNE) * S], fill=(222, 227, 234), width=4 * S)
        for k, r in enumerate(e["rencontres"]):
            yc = y0 + k * H_LIGNE + H_LIGNE / 2
            passe = r["date"] < info["auj"]
            dom = r["vaires_domicile"]
            point = GRIS if passe else VERT if dom else ORANGE
            _texte(d, (MARGE + 26, yc - 13), f"J{r['journee']}", 24, couleur if not passe else GRIS, True)
            dt = _date_courte(r["date"])
            _texte(d, (x_ligne - 24 - largeur_texte(dt, 22), yc - 12), dt, 22, DOUX)
            d.ellipse([(x_ligne - 12) * S, (yc - 12) * S, (x_ligne + 12) * S, (yc + 12) * S], fill=point)
            d.ellipse([(x_ligne - 5) * S, (yc - 5) * S, (x_ligne + 5) * S, (yc + 5) * S], fill=BLANC)
            pil = "Domicile" if dom else "Extérieur"
            w_pil = largeur_texte(pil, 18, True) + 24
            nom, taille = ajuster(joli_nom(r["adversaire"]["libelle"]), LARGEUR - MARGE - 24 - w_pil - 18 - (x_ligne + 28), 26, True)
            _texte(d, (x_ligne + 28, yc - taille / 2 - 2), nom, taille, GRIS if passe else NUIT, True)
            _pilule(d, LARGEUR - MARGE - 24 - w_pil, yc - 15, pil, (240, 242, 245) if passe else VERT_FOND if dom else ORANGE_FOND,
                    GRIS if passe else VERT if dom else ORANGE, taille=18, h=30)
        y += h_equipe + 24
    return img.resize((LARGEUR, hauteur), Image.LANCZOS)


def image_paris(dossier, aujourdhui=None):
    """[(chemin, titre)] : l'infographie du championnat de Paris."""
    _nettoyer(dossier, "paris_infographie")  # pas les autres images paris_ (feuilles, résultats... faites avant)
    info = donnees_infographie(aujourdhui or date.today())
    return [(_enregistrer(dessiner(info), dossier, "paris_infographie.png"), "Championnat de Paris")]

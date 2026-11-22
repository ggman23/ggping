"""Programme des équipes de Vaires en une seule image au format téléphone (programme_equipes.png).

Toutes les rencontres à venir, journée par journée : les 2 prochaines rencontres de chaque équipe du
championnat de France (les équipes masculines et l'équipe féminine), puis, sur la même période, celles des
équipes du championnat de Paris (paris.py) et du championnat des jeunes (jeunes.py) ; une équipe de Paris
ou des jeunes sans rencontre dans la période montre sa prochaine. Fond vert : à domicile ; fond orange : à
l'extérieur (et la pastille DOM / EXT, lisible sans les couleurs). Pas d'adresse : pas la place. Entre
l'adversaire et DOM / EXT, un pictogramme de la compétition (légende en haut) : carte de France tricolore
(championnat de France), tour Eiffel (Paris), tête de femme en rose aux cheveux longs (championnat féminin),
enfant en entier, bras levés, en violet (jeunes).

Faite par l'étape adversaires de la mise à jour (adversaires.recuperer pour le championnat de France), rangée
dans le groupe d'images « programme » de l'espace club (à la une, comme le récapitulatif).
"""

import re
from datetime import date, datetime, timedelta

from PIL import Image, ImageDraw

from .images import (BLANC, DOM_FOND, DOM_TEXTE, DOUX, EXT_FOND, EXT_TEXTE, NOIR, PUCE_FOND, SECTION, TITRE_DOUX,
                     TITRE_FOND, TITRE_TEXTE, _enregistrer, _nettoyer, ajuster, couper, largeur_texte, police)

LARGEUR, S = 1080, 2
MARGE = 24
JOURNEES_FRANCE = 2  # rencontres à venir de chaque équipe du championnat de France
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
        "décembre"]
H_TETE, H_LEGENDE, H_JOUR, H_LIGNE, ECART = 150, 128, 64, 96, 10
ICONE = 56  # pictogramme de la compétition, entre l'adversaire et DOM / EXT
LEGENDES = [("france", "France"), ("paris", "Paris"), ("femmes", "Féminin"), ("jeunes", "Jeunes")]


def _date(r):
    return r.get("date_reelle") or r.get("date")


def division_courte(division):
    """« Départementale 2 » -> D2, « Régionale 3 » -> R3, « Pré-régionale » -> PR ; sinon telle quelle."""
    d = division or ""
    for motif, forme in ((r"^D[ée]partementale\s*(\d+)", "D{}"), (r"^R[ée]gionale\s*(\d+)", "R{}"), (r"^Pr[ée]-r[ée]gionale", "PR")):
        m = re.match(motif, d, re.I)
        if m:
            return forme.format(*m.groups())
    return re.sub(r"\s*Championnat\s+F[ée]minin.*", "", d, flags=re.I).strip()


def ligne(competition, ordre, equipe, detail, r, icone):
    adv = r.get("adversaire")
    return {"date": _date(r), "competition": competition, "ordre": ordre, "equipe": equipe, "detail": detail, "icone": icone,
            "journee": r.get("journee"), "adversaire": adv["libelle"] if adv else None, "domicile": bool(r.get("vaires_domicile")),
            "heure": r.get("heure"), "a_confirmer": bool(r.get("date_a_confirmer"))}


def rencontres(france, paris_, jeunes_, aujourdhui):
    """Lignes du programme, dans l'ordre : date, puis France, Paris, jeunes, puis l'ordre des équipes."""
    auj = aujourdhui.isoformat()
    lignes = []
    for i, e in enumerate((france or {}).get("equipes", [])):
        a_venir = [r for r in e.get("rencontres", []) if (_date(r) or "") >= auj and not r.get("score")][:JOURNEES_FRANCE]
        femmes = e.get("championnat") == "F"
        detail = f"France{' féminin' if femmes else ''} · {division_courte(e.get('division'))}"
        lignes += [ligne("France", (0, femmes, e.get("numero") or i), e.get("nom_court") or e.get("libelle"), detail, r,
                         "femmes" if femmes else "france") for r in a_venir]
    fin = max((l["date"] for l in lignes), default=(aujourdhui + timedelta(days=14)).isoformat())
    for rang, (nom, donnees) in enumerate((("Paris", paris_), ("Jeunes", jeunes_))):
        for i, e in enumerate((donnees or {}).get("equipes", [])):
            a_venir = [r for r in e.get("rencontres", []) if (_date(r) or "") >= auj]
            dedans = [r for r in a_venir if _date(r) <= fin] or a_venir[:1]
            detail = f"Jeunes · {e.get('code')} ans" if nom == "Jeunes" else f"Paris · {e.get('division')}"
            equipe = re.sub(r"\s*·.*", "", e.get("nom_court") or "")  # « Vaires 1 · −15 ans » -> « Vaires 1 »
            lignes += [ligne(nom, (1 + rang, False, i), equipe, detail, r, nom.lower()) for r in dedans]
    return sorted(lignes, key=lambda l: (l["date"], l["ordre"]))


def _jour_long(iso):
    d = date.fromisoformat(iso)
    return f"{JOURS[d.weekday()]} {d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]}"


def _court(iso):
    d = date.fromisoformat(iso)
    return f"{JOURS[d.weekday()][:3].lower()}. {d:%d/%m}"


def _pastille(d, x, y, texte, fond, couleur, taille=24, h=40):
    w = largeur_texte(texte, taille, True) + 28
    d.rounded_rectangle([x * S, y * S, (x + w) * S, (y + h) * S], radius=h / 2 * S, fill=fond)
    d.text(((x + 14) * S, (y + (h - taille) / 2 - 1) * S), texte, font=police(taille, True), fill=couleur)
    return w


def dessiner(lignes, genere_le=None):
    """Image du programme (largeur 1080, hauteur selon le nombre de rencontres)."""
    jours = []
    for l in lignes:
        if not jours or jours[-1][0] != l["date"]:
            jours.append((l["date"], []))
        jours[-1][1].append(l)
    pied = ("Championnat de France : les 2 prochaines rencontres de chaque équipe ; Paris et jeunes : celles de la même "
            "période. Pas d'adresse : voir les pages du club.")
    if genere_le:
        pied += f" Données du {genere_le}."
    lignes_pied = couper(pied, LARGEUR - 2 * MARGE, 20)
    hauteur = H_TETE + H_LEGENDE + sum(H_JOUR + len(ls) * H_LIGNE for _, ls in jours) + 24 + 28 * len(lignes_pied) + 20
    img = Image.new("RGB", (LARGEUR * S, hauteur * S), BLANC)
    d = ImageDraw.Draw(img)

    # Bandeau
    d.rectangle([0, 0, LARGEUR * S, H_TETE * S], fill=TITRE_FOND)
    d.text((MARGE * S, 26 * S), "Programme des équipes", font=police(48, True), fill=TITRE_TEXTE)
    periode = f"du {_court(jours[0][0])} au {_court(jours[-1][0])}" if jours else "aucune rencontre à venir"
    d.text((MARGE * S, 92 * S), f"CVTT Vaires · {periode}", font=police(28), fill=TITRE_DOUX)
    # Légende des couleurs
    y = H_TETE + 16
    x = MARGE
    x += _pastille(d, x, y, "À domicile", DOM_FOND, DOM_TEXTE) + 14
    _pastille(d, x, y, "À l'extérieur", EXT_FOND, EXT_TEXTE)
    # Légende des pictogrammes
    x, y = MARGE, H_TETE + 66
    for cle, texte in LEGENDES:
        icone(img, d, cle, x, y, 44, BLANC)
        d.text(((x + 50) * S, (y + 10) * S), texte, font=police(24), fill=NOIR)
        x += 50 + largeur_texte(texte, 24) + 36
    y = H_TETE + H_LEGENDE

    for jour, ls in jours:
        d.rectangle([0, y * S, LARGEUR * S, (y + H_JOUR - 8) * S], fill=SECTION)
        titre = _jour_long(jour)
        d.text((MARGE * S, (y + 12) * S), titre, font=police(32, True), fill=NOIR)
        journees = []
        for l in ls:
            j = f"{l['competition']} J{l['journee']}"
            if l["journee"] and j not in journees:
                journees.append(j)
        detail, taille = ajuster(" · ".join(journees), LARGEUR - 3 * MARGE - largeur_texte(titre, 32, True), 22)
        d.text(((LARGEUR - MARGE - largeur_texte(detail, taille)) * S, (y + 20) * S), detail, font=police(taille), fill=DOUX)
        y += H_JOUR
        for l in ls:
            _carte(img, d, l, y)
            y += H_LIGNE
    y += 16
    for i, t in enumerate(lignes_pied):
        d.text((MARGE * S, (y + i * 28) * S), t, font=police(20), fill=DOUX)
    return img.resize((LARGEUR, hauteur), Image.LANCZOS)


def _carte(img, d, l, y):
    """Une rencontre : équipe et compétition à gauche, adversaire au milieu, DOM / EXT à droite."""
    h = H_LIGNE - ECART
    exempte = l["adversaire"] is None
    fond, fort = (PUCE_FOND, DOUX) if exempte else (DOM_FOND, DOM_TEXTE) if l["domicile"] else (EXT_FOND, EXT_TEXTE)
    x0, x1 = MARGE, LARGEUR - MARGE
    d.rounded_rectangle([x0 * S, y * S, x1 * S, (y + h) * S], radius=14 * S, fill=fond)
    d.rounded_rectangle([x0 * S, y * S, (x0 + 10) * S, (y + h) * S], radius=5 * S, fill=fort)
    # Équipe de Vaires
    t, taille = ajuster(l["equipe"], 250, 34, True)
    d.text(((x0 + 26) * S, (y + 10) * S), t, font=police(taille, True), fill=NOIR)
    t, taille = ajuster(l["detail"], 250, 22)
    d.text(((x0 + 26) * S, (y + 52) * S), t, font=police(taille), fill=DOUX)
    # Adversaire
    xa, largeur_adv = x0 + 300, x1 - 130 - ICONE - 16 - (x0 + 300)
    t, taille = ajuster("exempte" if exempte else l["adversaire"], largeur_adv, 32, not exempte)
    d.text((xa * S, (y + 10) * S), t, font=police(taille, not exempte), fill=DOUX if exempte else NOIR)
    sous = "" if exempte else " · ".join(filter(None, [l["heure"] and l["heure"].replace(":", "h"),
                                                        "date à confirmer" if l["a_confirmer"] else None]))
    if sous:
        d.text((xa * S, (y + 52) * S), sous, font=police(22, True), fill=fort)
    w = largeur_texte("DOM", 24, True) + 28
    if not exempte:
        texte = "DOM" if l["domicile"] else "EXT"
        _pastille(d, x1 - 20 - (largeur_texte(texte, 24, True) + 28), y + (h - 40) / 2, texte, fort, BLANC)
    icone(img, d, l["icone"], x1 - 20 - w - 16 - ICONE, y + (h - ICONE) / 2, ICONE, fond)


# ---------------------------------------------------------------------------
# Pictogrammes des compétitions (dessinés : aucune image ni police d'emoji à fournir). Coordonnées
# relatives (0 à 1) dans un carré de côté `taille`, en haut à gauche (x, y), en points.
# ---------------------------------------------------------------------------

BLEU, ROUGE_FR = (0, 85, 164), (239, 65, 53)
ROSE, ROSE_FONCE, PEAU = (225, 80, 150), (170, 40, 110), (250, 205, 220)
VIOLET, TOUR = (112, 72, 232), (60, 60, 72)
# Contour de la France métropolitaine (à peu près) et la Corse
FRANCE = [(0.38, 0.02), (0.52, 0.10), (0.62, 0.15), (0.80, 0.19), (0.90, 0.24), (0.85, 0.42), (0.80, 0.50), (0.86, 0.60),
          (0.82, 0.72), (0.90, 0.80), (0.78, 0.87), (0.62, 0.85), (0.53, 0.91), (0.50, 0.98), (0.36, 0.94), (0.22, 0.90),
          (0.17, 0.86), (0.24, 0.66), (0.20, 0.56), (0.12, 0.47), (0.02, 0.39), (0.10, 0.31), (0.24, 0.31), (0.27, 0.20),
          (0.34, 0.22), (0.37, 0.12)]


def icone(img, d, cle, x, y, taille, fond):
    """Dessine le pictogramme d'une compétition : france (carte tricolore), paris (tour Eiffel), femmes (tête
    de femme en rose, cheveux longs), jeunes (enfant en entier, bras levés, en violet)."""
    from PIL import Image as Img, ImageDraw as Dessin

    P = lambda u, v: ((x + u * taille) * S, (y + v * taille) * S)  # noqa: E731
    B = lambda u0, v0, u1, v1: [*P(u0, v0), *P(u1, v1)]  # noqa: E731
    if cle == "france":
        cote = round(taille * S)
        masque = Img.new("L", (cote, cote), 0)
        m = Dessin.Draw(masque)
        m.polygon([(u * cote, v * cote) for u, v in FRANCE], fill=255)
        m.ellipse([0.89 * cote, 0.84 * cote, 0.97 * cote, 0.98 * cote], fill=255)
        drapeau = Img.new("RGB", (cote, cote), BLANC)
        f = Dessin.Draw(drapeau)
        f.rectangle([0, 0, cote / 3, cote], fill=BLEU)
        f.rectangle([2 * cote / 3, 0, cote, cote], fill=ROUGE_FR)
        img.paste(drapeau, (round(x * S), round(y * S)), masque)
        contour = [P(u, v) for u, v in FRANCE]
        d.line(contour + contour[:1], fill=(90, 90, 100), width=S)
    elif cle == "paris":
        d.polygon([P(0.5, 0.0), P(0.46, 0.17), P(0.54, 0.17)], fill=TOUR)                      # flèche
        d.polygon([P(0.46, 0.17), P(0.54, 0.17), P(0.58, 0.44), P(0.42, 0.44)], fill=TOUR)    # haut
        d.rectangle(B(0.37, 0.44, 0.63, 0.49), fill=TOUR)                                    # 2e étage
        d.polygon([P(0.41, 0.49), P(0.59, 0.49), P(0.67, 0.67), P(0.33, 0.67)], fill=TOUR)    # milieu
        d.rectangle(B(0.26, 0.67, 0.74, 0.72), fill=TOUR)                                    # 1er étage
        d.polygon([P(0.30, 0.72), P(0.70, 0.72), P(0.86, 1.0), P(0.70, 1.0), P(0.60, 0.82), P(0.40, 0.82),
                   P(0.30, 1.0), P(0.14, 1.0)], fill=TOUR)                                   # pieds et arche
    elif cle == "femmes":
        d.ellipse(B(0.20, 0.05, 0.80, 0.86), fill=ROSE_FONCE)        # cheveux longs (derrière la tête)
        d.pieslice(B(0.12, 0.66, 0.88, 1.34), 180, 360, fill=ROSE)   # épaules
        d.ellipse(B(0.33, 0.17, 0.67, 0.60), fill=PEAU)              # visage
        d.pieslice(B(0.30, 0.10, 0.70, 0.46), 180, 360, fill=ROSE_FONCE)  # frange
    elif cle == "jeunes":
        epais = max(2, round(0.10 * taille * S))
        d.line([P(0.42, 0.42), P(0.18, 0.20)], fill=VIOLET, width=epais)   # bras levés
        d.line([P(0.58, 0.42), P(0.82, 0.20)], fill=VIOLET, width=epais)
        d.line([P(0.44, 0.64), P(0.36, 0.97)], fill=VIOLET, width=epais)   # jambes
        d.line([P(0.56, 0.64), P(0.64, 0.97)], fill=VIOLET, width=epais)
        d.rounded_rectangle(B(0.36, 0.34, 0.64, 0.68), radius=0.06 * taille * S, fill=VIOLET)  # corps
        d.ellipse(B(0.35, 0.02, 0.65, 0.32), fill=VIOLET)                 # grosse tête d'enfant


def image_programme(france, dossier, aujourdhui=None, paris_=None, jeunes_=None):
    """[(chemin, titre)] : l'image du programme (aucune s'il n'y a rien à venir)."""
    from . import jeunes, paris

    _nettoyer(dossier, "programme_")
    aujourdhui = aujourdhui or date.today()
    lignes = rencontres(france, paris_ if paris_ is not None else paris.donnees(),
                        jeunes_ if jeunes_ is not None else jeunes.donnees(), aujourdhui)
    if not lignes:
        return []
    try:
        genere = datetime.fromisoformat(france["genere_le"]).strftime("%d/%m/%Y %H:%M")
    except (KeyError, TypeError, ValueError):
        genere = None
    return [(_enregistrer(dessiner(lignes, genere), dossier, "programme_equipes.png"), "Programme des équipes")]

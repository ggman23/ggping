"""Programme des équipes de Vaires en une seule image au format téléphone (programme_equipes.png).

Toutes les rencontres à venir, journée par journée : les 2 prochaines rencontres de chaque équipe du
championnat de France (les équipes masculines et l'équipe féminine), puis, sur la même période, celles des
équipes du championnat de Paris (paris.py) et du championnat des jeunes (jeunes.py) ; une équipe de Paris
ou des jeunes sans rencontre dans la période montre sa prochaine. Fond vert : à domicile ; fond orange : à
l'extérieur (et la pastille DOM / EXT, lisible sans les couleurs). Pas d'adresse : pas la place.

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
H_TETE, H_LEGENDE, H_JOUR, H_LIGNE, ECART = 150, 72, 64, 96, 10


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


def ligne(competition, ordre, equipe, detail, r):
    adv = r.get("adversaire")
    return {"date": _date(r), "competition": competition, "ordre": ordre, "equipe": equipe, "detail": detail,
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
        lignes += [ligne("France", (0, femmes, e.get("numero") or i), e.get("nom_court") or e.get("libelle"), detail, r)
                   for r in a_venir]
    fin = max((l["date"] for l in lignes), default=(aujourdhui + timedelta(days=14)).isoformat())
    for rang, (nom, donnees) in enumerate((("Paris", paris_), ("Jeunes", jeunes_))):
        for i, e in enumerate((donnees or {}).get("equipes", [])):
            a_venir = [r for r in e.get("rencontres", []) if (_date(r) or "") >= auj]
            dedans = [r for r in a_venir if _date(r) <= fin] or a_venir[:1]
            detail = f"Jeunes · {e.get('code')} ans" if nom == "Jeunes" else f"Paris · {e.get('division')}"
            equipe = re.sub(r"\s*·.*", "", e.get("nom_court") or "")  # « Vaires 1 · −15 ans » -> « Vaires 1 »
            lignes += [ligne(nom, (1 + rang, False, i), equipe, detail, r) for r in dedans]
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
            _carte(d, l, y)
            y += H_LIGNE
    y += 16
    for i, t in enumerate(lignes_pied):
        d.text((MARGE * S, (y + i * 28) * S), t, font=police(20), fill=DOUX)
    return img.resize((LARGEUR, hauteur), Image.LANCZOS)


def _carte(d, l, y):
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
    xa, largeur_adv = x0 + 300, x1 - 130 - (x0 + 300)
    t, taille = ajuster("exempte" if exempte else l["adversaire"], largeur_adv, 32, not exempte)
    d.text((xa * S, (y + 10) * S), t, font=police(taille, not exempte), fill=DOUX if exempte else NOIR)
    sous = "" if exempte else " · ".join(filter(None, [l["heure"] and l["heure"].replace(":", "h"),
                                                        "date à confirmer" if l["a_confirmer"] else None]))
    if sous:
        d.text((xa * S, (y + 52) * S), sous, font=police(22, True), fill=fort)
    if not exempte:
        texte = "DOM" if l["domicile"] else "EXT"
        w = largeur_texte(texte, 24, True) + 28
        _pastille(d, x1 - 20 - w, y + (h - 40) / 2, texte, fort, BLANC)


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

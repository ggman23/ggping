"""Images PNG des tableaux, lisibles sur un téléphone (à partager dans les groupes du club).

Les images sont dessinées avec Pillow et une police fournie avec l'outil (Liberation Sans,
dossier polices/) : le PC et la mise à jour en ligne produisent les mêmes images.
- largeur 1080 points (pleine largeur d'un téléphone), dessinées en double résolution puis
  réduites : texte et pictogrammes lissés ;
- 25 lignes au plus par image : une image très haute serait réduite (illisible) par les
  messageries ; un long tableau donne plusieurs images numérotées (1/3, 2/3...), plus une
  version en une seule image verticale (..._complet.png) pour qui préfère faire défiler.

Une fonction par page : images_virtuel, images_resultats, images_rencontres, images_effectif,
images_adversaires.
Chacune écrit ses images dans le dossier donné et renvoie [(chemin, titre)].
"""

import math
from datetime import date, datetime, timedelta
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

POLICES = Path(__file__).with_name("polices")
LARGEUR = 1080          # largeur de l'image (points)
S = 2                   # facteur de suréchantillonnage du dessin
MARGE = 18
LIGNES_PAR_IMAGE = 25
TAILLE = 26             # texte des cellules
TAILLE_PETIT = 18       # texte secondaire
TAILLE_ENTETE = 19
HAUTEUR_LIGNE, HAUTEUR_LIGNE_DOUBLE = 50, 68
NOM_MIN = 230           # largeur minimale de la colonne du nom (l'image s'élargit au besoin)
FICHE_MIN = 720         # largeur minimale d'une image ajustée à son contenu (fiche d'un adversaire)
JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]

# Couleurs (celles des pages HTML)
BLANC, NOIR = "#ffffff", "#1c2330"
DOUX = "#5b6576"
BORD = "#d5d9df"
ZEBRE = "#f5f6f8"
TITRE_FOND, TITRE_TEXTE, TITRE_DOUX = "#173b60", "#ffffff", "#c9d6e6"
ENTETE = "#f8cbad"
SECTION = "#e7effb"
POS_FOND, POS_TEXTE = "#c6efce", "#006100"
NEG_FOND, NEG_TEXTE = "#ffc7ce", "#9c0006"
V_TOUT, V_PLUS, V_MOINS, V_ZERO = "#00b050", "#92d050", "#ffff00", "#ff0000"
OK_FOND, OK_TEXTE = "#e3f4ea", "#1d7a46"
DOM_FOND, DOM_TEXTE = "#e3f4ea", "#1d7a46"
EXT_FOND, EXT_TEXTE = "#fbeedd", "#a45a00"
PUCE_FOND, FILLE_FOND, FILLE_TEXTE = "#eef0f3", "#fde4ef", "#b0306a"

_polices = {}


def police(taille, gras=False):
    cle = (round(taille * S), gras)
    if cle not in _polices:
        nom = "LiberationSans-Bold.ttf" if gras else "LiberationSans-Regular.ttf"
        _polices[cle] = ImageFont.truetype(str(POLICES / nom), cle[0])
    return _polices[cle]


def largeur_texte(texte, taille, gras=False):
    return police(taille, gras).getlength(texte) / S


# ---------------------------------------------------------------------------
# Cellules et éléments
# ---------------------------------------------------------------------------

class C:
    """Une cellule : texte principal, couleurs, texte secondaire (sous ou après), pictogramme, puces."""

    def __init__(self, texte="", fond=None, couleur=None, gras=False, sous=None, apres=None, icone=None,
                 puces=None, alternatives=(), align=None, taille_puces=18):
        self.texte, self.fond, self.couleur, self.gras = str(texte if texte is not None else ""), fond, couleur, gras
        self.sous, self.apres, self.icone, self.puces = sous, apres, icone, puces or []
        self.alternatives, self.align, self.taille_puces = alternatives, align, taille_puces


class Col:
    def __init__(self, titre, largeur=None, align="c"):
        self.titre, self.largeur, self.align = titre, largeur, align


def colonnes_egales(colonnes, largeur_totale):
    """Répartit la largeur : les colonnes sans largeur (le nom du joueur) prennent le reste, au moins
    NOM_MIN (l'image est alors plus large : voir largeur_image)."""
    fixes = sum(c.largeur for c in colonnes if c.largeur)
    libres = [c for c in colonnes if not c.largeur]
    reste = max(NOM_MIN * len(libres), largeur_totale - fixes)
    for c in libres:
        c.largeur = reste / len(libres)
    return colonnes


def largeur_image(colonnes):
    return max(LARGEUR, round(sum(c.largeur for c in colonnes) + 2 * MARGE))


def largeur_naturelle(cel):
    """Largeur (points) qu'il faut à une cellule pour s'afficher sans être réduite (voir _cellule)."""
    if cel.icone in ("ok", "flamme"):
        return 40
    if cel.puces:
        return (sum(max(round(cel.taille_puces * 1.9), largeur_texte(t, cel.taille_puces, True) + 14) for t, _, _ in cel.puces)
                + 4 * (len(cel.puces) - 1) + 8)
    largeur = largeur_texte(cel.texte, TAILLE, cel.gras) + 14 + (16 if cel.icone else 0)
    if cel.apres:
        largeur += largeur_texte(f" {cel.apres}", TAILLE_PETIT - 1)
    if cel.sous:
        largeur = max(largeur, largeur_texte(cel.sous, TAILLE_PETIT) + 16)
    return largeur


class Rendu:
    """Construit une image : bandeau de titre, sections, tableaux, notes. Mesure puis dessine."""

    def __init__(self, largeur=LARGEUR):
        self.largeur = largeur
        self.elements = []  # (hauteur, fonction de dessin(draw, img, y))

    # -- éléments -------------------------------------------------------
    def titre(self, texte, sous_titre=None):
        lignes = lignes_sous_titre(sous_titre, self.largeur - 2 * MARGE) if sous_titre else []
        h = 64 + (30 + 25 * (len(lignes) - 1) if lignes else 0)

        def dessiner(d, img, y):
            d.rectangle([0, y * S, self.largeur * S, (y + h) * S], fill=TITRE_FOND)
            t, taille = ajuster(texte, self.largeur - 2 * MARGE, 32, True)
            d.text((MARGE * S, (y + 16) * S), t, font=police(taille, True), fill=TITRE_TEXTE)
            for i, ligne in enumerate(lignes):
                t, taille = ajuster(ligne, self.largeur - 2 * MARGE, 19)
                d.text((MARGE * S, (y + 58 + 25 * i) * S), t, font=police(taille), fill=TITRE_DOUX)
        self.elements.append((h, dessiner))

    def section(self, texte, detail=None):
        h = 44

        def dessiner(d, img, y):
            d.rectangle([0, (y + 6) * S, self.largeur * S, (y + h) * S], fill=SECTION)
            d.text((MARGE * S, (y + 14) * S), texte, font=police(22, True), fill=NOIR)
            if detail:
                x = MARGE + largeur_texte(texte, 22, True) + 12
                t, taille = ajuster(detail, self.largeur - x - MARGE, 17)
                d.text((x * S, (y + 18) * S), t, font=police(taille), fill=DOUX)
        self.elements.append((h, dessiner))

    def texte(self, texte, taille=17, couleur=DOUX, gras=False):
        lignes = couper(texte, self.largeur - 2 * MARGE, taille, gras)
        h = 10 + len(lignes) * (taille + 6)

        def dessiner(d, img, y):
            for i, l in enumerate(lignes):
                d.text((MARGE * S, (y + 6 + i * (taille + 6)) * S), l, font=police(taille, gras), fill=couleur)
        self.elements.append((h, dessiner))

    def espace(self, h=8):
        self.elements.append((h, lambda d, img, y: None))

    def entete(self, colonnes):
        nb = max(len(c.titre.split("\n")) for c in colonnes)
        h = 14 + nb * 23

        def dessiner(d, img, y):
            x = MARGE
            d.rectangle([MARGE * S, y * S, (self.largeur - MARGE) * S, (y + h) * S], fill=ENTETE)
            for c in colonnes:
                lignes = c.titre.split("\n")
                y0 = y + (h - len(lignes) * 23) / 2
                for i, l in enumerate(lignes):
                    t, taille = ajuster(l, c.largeur - 6, TAILLE_ENTETE, True)
                    _texte_aligne(d, t, taille, True, x, c.largeur, y0 + i * 23, c.align, NOIR)
                x += c.largeur
        self.elements.append((h, dessiner))

    def ligne(self, colonnes, cellules, zebre=False):
        h = HAUTEUR_LIGNE_DOUBLE if any(c.sous for c in cellules) else HAUTEUR_LIGNE

        def dessiner(d, img, y):
            x = MARGE
            if zebre:
                d.rectangle([MARGE * S, (y * S) + S, (self.largeur - MARGE) * S, (y + h) * S], fill=ZEBRE)
            for col, cel in zip(colonnes, cellules):
                _cellule(d, img, cel, col, x, y, h)
                x += col.largeur
            d.line([MARGE * S, (y + h) * S, (self.largeur - MARGE) * S, (y + h) * S], fill=BORD, width=S)
        self.elements.append((h, dessiner))

    def tableau(self, colonnes, lignes):
        self.entete(colonnes)
        for i, cellules in enumerate(lignes):
            self.ligne(colonnes, cellules, zebre=i % 2 == 1)

    def pied(self, texte):
        self.espace(6)
        self.texte(texte, 15)

    # -- image ------------------------------------------------------------
    def image(self):
        hauteur = sum(h for h, _ in self.elements) + 12
        img = Image.new("RGB", (round(self.largeur * S), round(hauteur * S)), BLANC)
        d = ImageDraw.Draw(img)
        y = 0
        for h, dessiner in self.elements:
            dessiner(d, img, y)
            y += h
        return img.resize((round(self.largeur), round(hauteur)), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Texte : ajustement, coupure, alignement
# ---------------------------------------------------------------------------

def ajuster(texte, largeur, taille, gras=False, alternatives=(), taille_min=None):
    """Texte qui tient dans la largeur : alternatives plus courtes, puis police réduite, puis « … »."""
    taille_min = taille_min or taille * 0.78
    for t in (texte, *alternatives):
        if largeur_texte(t, taille, gras) <= largeur:
            return t, taille
    t = alternatives[-1] if alternatives else texte
    tl = taille
    while tl > taille_min and largeur_texte(t, tl, gras) > largeur:
        tl -= 0.5
    while len(t) > 1 and largeur_texte(t, tl, gras) > largeur:
        t = t[:-2] + "…"
    return t, tl


def couper(texte, largeur, taille, gras=False):
    mots, lignes, courante = texte.split(), [], ""
    for m in mots:
        essai = (courante + " " + m).strip()
        if largeur_texte(essai, taille, gras) <= largeur or not courante:
            courante = essai
        else:
            lignes.append(courante)
            courante = m
    if courante:
        lignes.append(courante)
    return lignes or [""]


def lignes_sous_titre(texte, largeur, taille=19, maxi=3):
    """Sous-titre sur une ligne s'il tient, sinon coupé aux « · » (puis entre les mots) : 3 lignes au plus."""
    if largeur_texte(texte, taille) <= largeur:
        return [texte]
    lignes = []
    for morceau in texte.split(" · "):
        if lignes and largeur_texte(f"{lignes[-1]} · {morceau}", taille) <= largeur:
            lignes[-1] += f" · {morceau}"
        else:
            lignes += couper(morceau, largeur, taille)
    return lignes if len(lignes) <= maxi else lignes[:maxi - 1] + [" ".join(lignes[maxi - 1:])]


def _texte_aligne(d, texte, taille, gras, x, largeur, y, align, couleur):
    lt = largeur_texte(texte, taille, gras)
    if align == "g":
        x0 = x + 8
    elif align == "d":
        x0 = x + largeur - 8 - lt
    else:
        x0 = x + (largeur - lt) / 2
    d.text((x0 * S, y * S), texte, font=police(taille, gras), fill=couleur)
    return x0, lt


def _cellule(d, img, cel, col, x, y, h):
    if cel.fond:
        d.rectangle([(x + 1) * S, (y + 1) * S, (x + col.largeur - 1) * S, (y + h - 1) * S], fill=cel.fond)
    align = cel.align or col.align
    if cel.icone in ("ok", "flamme"):
        _icone(img, cel.icone, x + col.largeur / 2, y + h / 2, 30)
        return
    if cel.puces:
        _puces(d, cel.puces, x, col.largeur, y + h / 2, cel.taille_puces)
        return
    taille, tp = TAILLE, TAILLE_PETIT - 1
    dispo = col.largeur - 14 - (16 if cel.icone else 0)
    suffixe = f" {cel.apres}" if cel.apres else ""
    t, tl = ajuster(cel.texte, dispo, taille, cel.gras, cel.alternatives)
    if suffixe and largeur_texte(t, tl, cel.gras) + largeur_texte(suffixe, tp) > dispo:
        suffixe = ""
    ty = y + 7 if cel.sous else y + (h - tl * 1.15) / 2
    lt_total = largeur_texte(t, tl, cel.gras) + (largeur_texte(suffixe, tp) if suffixe else 0) + (16 if cel.icone else 0)
    if align == "g":
        x0 = x + 8
    elif align == "d":
        x0 = x + col.largeur - 8 - lt_total
    else:
        x0 = x + (col.largeur - lt_total) / 2
    d.text((x0 * S, ty * S), t, font=police(tl, cel.gras), fill=cel.couleur or NOIR)
    xs = x0 + largeur_texte(t, tl, cel.gras)
    if suffixe:
        d.text((xs * S, (ty + tl - tp - 1) * S), suffixe, font=police(tp), fill=DOUX)
        xs += largeur_texte(suffixe, tp)
    if cel.icone in ("monte", "descend"):
        _triangle(d, xs + 9, ty + tl * 0.55, cel.icone)
    if cel.sous:
        s, ts = ajuster(cel.sous, col.largeur - 16, TAILLE_PETIT)
        _texte_aligne(d, s, ts, False, x, col.largeur, y + 40, align, DOUX)


def _puces(d, puces, x, largeur, cy, taille=18):
    """Petites étiquettes arrondies (numéros d'équipes jouées, DOM/EXT, scores des manches...)."""
    tailles = [max(round(taille * 1.9), largeur_texte(t, taille, True) + 14) for t, _, _ in puces]
    total = sum(tailles) + 4 * (len(puces) - 1)
    x0 = x + (largeur - total) / 2
    demi = taille * 0.83
    for (texte, fond, couleur), w in zip(puces, tailles):
        d.rounded_rectangle([x0 * S, (cy - demi) * S, (x0 + w) * S, (cy + demi) * S], radius=7 * S, fill=fond)
        _texte_aligne(d, texte, taille, True, x0, w, cy - taille * 0.583, "c", couleur)
        x0 += w + 4


def _triangle(d, cx, cy, sens):
    t = 7
    pts = [(cx - t, cy + t * 0.6), (cx + t, cy + t * 0.6), (cx, cy - t)] if sens == "monte" \
        else [(cx - t, cy - t * 0.6), (cx + t, cy - t * 0.6), (cx, cy + t)]
    d.polygon([(px * S, py * S) for px, py in pts], fill=POS_TEXTE if sens == "monte" else NEG_TEXTE)


_icones = {}


def _icone(img, nom, cx, cy, taille):
    """Pictogramme dessiné à 4 fois sa taille puis réduit (bords lisses) : coche verte ou flamme."""
    cle = (nom, taille)
    if cle not in _icones:
        n = round(taille * S * 4)
        ic = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        d = ImageDraw.Draw(ic)
        if nom == "ok":
            d.rounded_rectangle([n * .06, n * .06, n * .94, n * .94], radius=n * .25, fill=OK_FOND)
            d.line([(n * .26, n * .52), (n * .43, n * .69), (n * .75, n * .33)], fill=OK_TEXTE,
                   width=round(n * .11), joint="curve")
        else:
            _flamme(d, n)
        _icones[cle] = ic.resize((round(taille * S), round(taille * S)), Image.LANCZOS)
    ic = _icones[cle]
    img.paste(ic, (round((cx - taille / 2) * S), round((cy - taille / 2) * S)), ic)


def _flamme(d, n):
    """Flamme : goutte pointue en haut et arrondie en bas (courbe paramétrique), cœur jaune."""
    def forme(echelle, couleur):
        pts = []
        for i in range(97):
            t = 2 * math.pi * i / 96
            x = 0.36 * math.sin(t) * abs(math.sin(t / 2)) ** 1.25
            y = -0.45 * math.cos(t)
            x += 0.08 * max(0.0, math.cos(t)) ** 2  # pointe penchée
            # mise à l'échelle autour du bas de la flamme
            pts.append(((0.5 + x * echelle) * n, (0.95 - (0.45 - y) * echelle) * n))
        d.polygon(pts, fill=couleur)
    forme(1.0, "#e8590c")
    forme(0.55, "#ffb703")


# ---------------------------------------------------------------------------
# Outils communs
# ---------------------------------------------------------------------------

def fmt(x, dec=None):
    if x is None:
        return ""
    if dec is None:
        dec = 0 if float(x).is_integer() else (1 if float(x * 2).is_integer() else 2)
    return f"{x:,.{dec}f}".replace(",", " ").replace(".", ",")


def signe(x, dec=None):
    return "" if x is None else ("+" if x > 0 else "") + fmt(x, dec)


def jour_fr(iso):
    d = date.fromisoformat(iso[:10])
    return f"{JOURS[d.weekday()]} {d:%d/%m}"


def nom_alternatives(nom, prenom):
    nom, prenom = (nom or "").strip(), (prenom or "").strip()
    complet = f"{nom} {prenom}".strip()
    return complet, ([f"{nom} {prenom[0]}."] if prenom else []) + [nom]


def cel_nom(nom, prenom, apres=None, gras=False):
    complet, alt = nom_alternatives(nom, prenom)
    return C(complet, align="g", alternatives=alt, apres=apres, gras=gras)


def cel_points(x, fond=False, dec=None):
    if x is None:
        return C("")
    if fond:
        return C(signe(x, dec), fond=POS_FOND if x > 0 else NEG_FOND if x < 0 else None,
                 couleur=POS_TEXTE if x > 0 else NEG_TEXTE if x < 0 else NOIR)
    return C(signe(x, dec), couleur=POS_TEXTE if x > 0 else NEG_TEXTE if x < 0 else NOIR, gras=x != 0)


def cel_victoires(v, n):
    if not n:
        return C("")
    fond = V_TOUT if v == n else V_PLUS if v * 2 > n else V_MOINS if v > 0 else V_ZERO
    return C(f"{v}/{n}", fond=fond, gras=True)


def equipe_courte(libelle):
    """'VAIRES 1 F' -> 'V1F', 'Vaires 3' -> 'V3'."""
    t = (libelle or "").upper().replace("VAIRES", "V").replace("CVTT", "").replace(" ", "")
    return t


def paginer(lignes, n=LIGNES_PAR_IMAGE):
    """Découpe en paquets équilibrés (40 lignes -> 20 + 20 plutôt que 25 + 15)."""
    if len(lignes) <= n:
        return [lignes]
    nb = math.ceil(len(lignes) / n)
    taille = math.ceil(len(lignes) / nb)
    return [lignes[i:i + taille] for i in range(0, len(lignes), taille)]


def _enregistrer(img, dossier, nom):
    chemin = Path(dossier) / nom
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.save(chemin, optimize=True)
    return chemin


def _nettoyer(dossier, prefixe):
    """Supprime les images d'un précédent lancement (le nombre de pages ou la journée a pu changer)."""
    for f in Path(dossier).glob(f"{prefixe}*.png"):
        f.unlink()


def _genere(donnees):
    if donnees.get("date_reference"):  # archive : l'état à cette date
        return "archive, état au " + date.fromisoformat(donnees["date_reference"]).strftime("%d/%m/%Y")
    try:
        return datetime.fromisoformat(donnees["genere_le"]).strftime("%d/%m/%Y %H:%M")
    except (KeyError, ValueError):
        return ""


def _tableau_pagine(dossier, prefixe, titre, sous_titre, colonnes, lignes, pied, titre_court):
    """Un tableau découpé en plusieurs images si besoin. Renvoie [(chemin, titre)].
    S'il est découpé, il est aussi donné en une seule image verticale (en plus des autres)."""
    paquets = paginer(lignes)
    sorties = []
    for i, paquet in enumerate(paquets, 1):
        r = Rendu(largeur_image(colonnes))
        suffixe = f" ({i}/{len(paquets)})" if len(paquets) > 1 else ""
        r.titre(titre + suffixe, sous_titre)
        r.espace(10)
        r.tableau(colonnes, paquet)
        r.pied(pied)
        nom = f"{prefixe}{'_' + str(i) if len(paquets) > 1 else ''}.png"
        sorties.append((_enregistrer(r.image(), dossier, nom), titre_court + suffixe))
    if len(paquets) > 1:
        # Les titres des colonnes sont répétés aux mêmes endroits que les coupures des images
        # séparées : on les a toujours sous les yeux en faisant défiler.
        r = Rendu(largeur_image(colonnes))
        r.titre(titre, sous_titre)
        r.espace(10)
        for i, paquet in enumerate(paquets):
            if i:
                r.espace(14)
            r.tableau(colonnes, paquet)
        r.pied(pied)
        sorties.append((_enregistrer(r.image(), dossier, f"{prefixe}_complet.png"), f"{titre_court} (image unique)"))
    return sorties


# ---------------------------------------------------------------------------
# Classement virtuel
# ---------------------------------------------------------------------------

def images_virtuel(donnees, dossier):
    _nettoyer(dossier, "classement_virtuel")
    largeur_num = 94
    colonnes = colonnes_egales([Col("#", 44), Col("Joueur", None, "g")]
                               + [Col(t, largeur_num) for t in ("Éq.", "Pts off.", "Champ.", "Autre", "Total",
                                                                 "Virt.", "Clt", "V/D")], LARGEUR - 2 * MARGE)
    lignes = []
    for i, j in enumerate(donnees["joueurs"], 1):
        clt = j.get("classement_virtuel")
        ecart = (clt - j["classement"]) if clt is not None and j.get("classement") is not None else 0
        a_champ = any(p["championnat"] for p in j["parties"])
        a_autres = any(not p["championnat"] for p in j["parties"])
        lignes.append([
            C(i if j.get("virtuels") is not None else "", couleur=DOUX),
            cel_nom(j.get("nom"), j.get("prenom"), apres=j.get("categorie")),
            C(equipe_courte(j.get("equipe")), couleur=DOUX),
            C(fmt(j.get("officiels")) if j.get("officiels") is not None else "—"),
            cel_points(j["championnat"]) if a_champ else C(""),
            cel_points(j["autres"]) if a_autres else C(""),
            cel_points(j["total"], fond=True) if j["parties"] else C(""),
            C(fmt(j["virtuels"], 0 if float(j["virtuels"]).is_integer() else 1) if j.get("virtuels") is not None else "—",
              gras=True),
            C(clt if clt is not None else "", gras=bool(ecart), couleur=POS_TEXTE if ecart > 0 else NEG_TEXTE if ecart < 0 else NOIR,
              icone="monte" if ecart > 0 else "descend" if ecart < 0 else None),
            C(f"{j['v']}/{j['d']}" if j["parties"] else "", couleur=DOUX),
        ])
    sous = f"{donnees['club']['nom']} · phase {donnees['phase']} {donnees['saison']} · toutes compétitions · {_genere(donnees)}"
    pied = ("Virt. = points officiels + points gagnés ou perdus depuis le début de la phase (championnat, critérium, "
            "tournois...). Clt : ▲ ▼ = changement de classement. V/D = victoires / défaites.")
    return _tableau_pagine(dossier, "classement_virtuel", "Classement virtuel", sous, colonnes, lignes, pied,
                           "Classement virtuel")


# ---------------------------------------------------------------------------
# Résultats des joueurs de Vaires
# ---------------------------------------------------------------------------

def images_resultats(donnees, dossier):
    _nettoyer(dossier, "resultats_")
    sorties = []
    if not donnees.get("journees"):
        return sorties
    sous_base = f"{donnees['club']['nom']} · phase {donnees['phase']} {donnees['saison']}"
    derniere = donnees["journees"][-1]
    j = derniere["numero"]
    lignes_j = sorted((l for l in donnees["lignes"] if l["journee"] == j),
                      key=lambda l: (-l["delta"], -(l["total"] or 0), l["joueur"]))
    colonnes = colonnes_egales([Col("Éq.", 64), Col("Joueur", None, "g"), Col("Points", 88), Col("+/-", 92),
                                Col("Vict.", 78), Col("Meilleure\nvictoire", 140), Col(f"Points\nJ{j}", 104),
                                Col("Total", 92)], LARGEUR - 2 * MARGE)
    lignes = []
    for l in lignes_j:
        nom, prenom = _nom_prenom(l["joueur"])
        lignes.append([
            C(equipe_courte(l["equipe"]), couleur=DOUX),
            cel_nom(nom, prenom),
            C(fmt(l["points"])),
            cel_points(l["delta"], fond=True, dec=1),
            cel_victoires(l["v"], l["matchs"]),
            C(signe(l["meilleure"], 0), apres=f"({fmt(l['meilleure_adv'])})") if l.get("meilleure") is not None else C(""),
            C(fmt(l["apres"], 1), gras=True),
            cel_points(l["total"], dec=1),
        ])
    dates = ", ".join(jour_fr(x) for x in derniere["dates"])
    sorties += _tableau_pagine(
        dossier, f"resultats_J{j}", f"Résultats de la J{j}", f"{sous_base} · {dates} · {_genere(donnees)}",
        colonnes, lignes,
        f"Trié par points gagnés sur la journée. Points J{j} = classement virtuel (points officiels + total depuis la J1). "
        "Meilleure victoire = écart avec le mieux classé des joueurs battus (ses points).", f"Résultats J{j}")

    js = [x["numero"] for x in donnees["journees"]]
    cumuls = sorted(donnees["cumuls"], key=lambda c: (-c["total"], -c["points"], c["joueur"]))
    larg_j = 84 if len(js) <= 4 else 76
    colonnes = colonnes_egales([Col("Éq.", 80), Col("Joueur", None, "g"), Col("Points", 84)]
                               + [Col(f"J{n}", larg_j) for n in js]
                               + [Col("Total", 92), Col("Virt.", 104), Col("Vict.", 74)], LARGEUR - 2 * MARGE)
    lignes = []
    for c in cumuls:
        nom, prenom = _nom_prenom(c["joueur"])
        par_j = {int(k): v for k, v in c["journees"].items()}
        lignes.append([
            C(", ".join(equipe_courte(e) for e in c["equipes"]), couleur=DOUX),
            cel_nom(nom, prenom),
            C(fmt(c["points"])),
            *[C(signe(par_j[n], 1), couleur=POS_TEXTE if par_j[n] > 0 else NEG_TEXTE if par_j[n] < 0 else NOIR)
              if n in par_j else C("") for n in js],
            cel_points(c["total"], fond=True, dec=1),
            C(fmt(c["virtuels"], 1), gras=True),
            cel_victoires(c["v"], c["matchs"]),
        ])
    sorties += _tableau_pagine(
        dossier, "resultats_cumul", f"Cumul J1 à J{js[-1]}", f"{sous_base} · championnat par équipes · {_genere(donnees)}",
        colonnes, lignes, "Trié par points gagnés au total depuis la J1. Virt. = points officiels + total.", "Résultats : cumul")
    return sorties


# ---------------------------------------------------------------------------
# Feuilles de match : une image par rencontre de la dernière journée
# ---------------------------------------------------------------------------

def _cel_joueurs(joueurs, gras=False):
    """Joueur d'une partie (avec ses points), ou les deux joueurs d'un double."""
    if len(joueurs) == 1:
        j = joueurs[0]
        return cel_nom(j["nom"], j["prenom"], apres=fmt(j["points"]) if j.get("points") else None, gras=gras)
    noms = [j["nom"] for j in joueurs]
    return C(" / ".join(noms) or "—", align="g", gras=gras, alternatives=[" / ".join(n.split()[0] for n in noms if n)])


def images_rencontres(donnees, dossier):
    _nettoyer(dossier, "rencontres_")
    sorties = []
    if not donnees.get("journees"):
        return sorties
    j = donnees["journees"][-1]
    colonnes = colonnes_egales([Col("Vaires", None, "g"), Col("", 92), Col("Adversaire", None, "g"), Col("Manches", 372)],
                               LARGEUR - 2 * MARGE)
    for r in [x for x in donnees["rencontres"] if x["journee"] == j and x["parties"]]:
        lignes = []
        for p in r["parties"]:
            sets = [s for s in p["sets"] if None not in s]
            g = p["gagne"]
            fond, couleur = (POS_FOND, POS_TEXTE) if g else (NEG_FOND, NEG_TEXTE) if g is False else (PUCE_FOND, DOUX)
            resultat = (f"{sum(a > b for a, b in sets)}-{sum(b > a for a, b in sets)}" if sets
                        else "forf." if p["forfait"] else "—")
            manches = (C(puces=[(f"{a}-{b}", POS_FOND if a > b else NEG_FOND, POS_TEXTE if a > b else NEG_TEXTE)
                                for a, b in sets], taille_puces=21) if sets
                       else C("forfait" if p["forfait"] else "", couleur=DOUX))
            lignes.append([_cel_joueurs(p["nous"], gras=g is True), C(puces=[(resultat, fond, couleur)], taille_puces=21),
                           _cel_joueurs(p["eux"], gras=g is False), manches])
        nous, eux = r["score"]
        issue = "victoire" if nous > eux else "défaite" if nous < eux else "nul"
        equipe = r["equipe"].replace("VAIRES", "Vaires")
        img = Rendu()
        img.titre(f"{equipe} · {issue} {nous}-{eux}",
                  f"J{j} · {jour_fr(r['date'])} · {'reçoit' if r['domicile'] else 'se déplace à'} {r['adversaire']} · {r['division']}")
        img.espace(10)
        img.tableau(colonnes, lignes)
        if r["bilan"]:
            img.espace(4)
            img.texte("Bilan : " + " · ".join(f"{nom_alternatives(b['nom'], b['prenom'])[1][0]} {b['v']}/{b['n']}"
                                              for b in r["bilan"]), 19, NOIR)
        img.pied("Manches dans l'ordre, score de Vaires en premier (vert : manche gagnée par Vaires). "
                 "En gras : le vainqueur de la partie.")
        nom = f"rencontres_J{j}_{equipe_courte(r['equipe'])}.png"
        sorties.append((_enregistrer(img.image(), dossier, nom), f"{equipe} : feuille de match J{j}"))
    return sorties


def image_recap(donnees, dossier_import, dossier):
    """Récapitulatif de la journée sur le modèle de l'image du club (voir recap.py)."""
    from .recap import image_recap as dessiner
    return dessiner(donnees, dossier_import, dossier)


def _nom_prenom(complet):
    """'DELOBELLE Jérôme' -> ('DELOBELLE', 'Jérôme')."""
    mots = (complet or "").split()
    i = 0
    while i < len(mots) - 1 and mots[i] == mots[i].upper():
        i += 1
    return " ".join(mots[:i]) or complet, " ".join(mots[i:])


# ---------------------------------------------------------------------------
# Effectif de Vaires : brûlages
# ---------------------------------------------------------------------------

def _brulage(j, n):
    b = j.get("brulage") or {}
    return b.get(n) or b.get(str(n)) or {}


def images_effectif(donnees, dossier):
    _nettoyer(dossier, "effectif_")
    sorties = []
    masc = [e for e in donnees["equipes"] if e["championnat"] == "M"]
    fem = [e for e in donnees["equipes"] if e["championnat"] == "F"]
    actifs = [j for j in donnees["joueurs"] if j.get("renouvele") and not j.get("loisir")]
    journees = sorted({m["j"] for j in actifs for m in j.get("matchs", [])})
    sous_base = f"{donnees['club']['nom']} · phase {donnees['phase']} {donnees['saison']} · {_genere(donnees)}"

    # Vue du club : équipes jouées à chaque journée, puis ✓ / flamme pour chaque équipe
    larg_j = 52 if len(journees) <= 5 else 46
    colonnes = colonnes_egales(
        [Col("Joueur", None, "g"), Col("Pts", 72)] + [Col(f"J{n}", larg_j) for n in journees]
        + [Col(e["nom_court"].replace("Vaires ", "V"), 58) for e in masc]
        + [Col(e["nom_court"].replace("Vaires ", "V").replace(" ", ""), 58) for e in fem], LARGEUR - 2 * MARGE)
    lignes = []
    for j in actifs:
        pts = j.get("points") or j.get("points_mensuels")
        cel_j = []
        for n in journees:
            ms = [m for m in j.get("matchs", []) if m["j"] == n]
            puces = [(f"{m['n']}F" if m["ch"] == "F" else str(m["n"]),
                      FILLE_FOND if m["ch"] == "F" else PUCE_FOND, FILLE_TEXTE if m["ch"] == "F" else NOIR) for m in ms]
            cel_j.append(C(puces=puces[:2]) if puces else C(""))
        cel_m = [C(icone="flamme" if _brulage(j, e["numero"]).get("brule") else "ok") for e in masc]
        cel_f = [C(icone="ok") if j.get("sexe") == "F" else C("—", couleur=BORD) for _ in fem]
        lignes.append([cel_nom(j.get("nom"), j.get("prenom"), apres=j.get("categorie")), C(fmt(pts) if pts else "", couleur=DOUX),
                       *cel_j, *cel_m, *cel_f])
    sorties += _tableau_pagine(
        dossier, "effectif_club", "Effectif : qui peut jouer où ?", sous_base, colonnes, lignes,
        "J1, J2... : équipe jouée à chaque journée (F = équipe féminine). Coche = peut jouer dans l'équipe ; "
        "flamme = brûlé (2 matchs en équipes plus fortes). Les matchs en équipe féminine ne comptent pas pour le "
        "brûlage masculin.", "Effectif : club")

    # Une image par équipe masculine (sauf la 1) : les joueurs brûlés pour cette équipe
    for e in masc[1:]:
        n = e["numero"]
        brules = [j for j in actifs if _brulage(j, n).get("brule")]
        colonnes = colonnes_egales([Col("Joueur", None, "g"), Col("Pts", 88), Col("Matchs en équipes\nplus fortes", 290),
                                    Col("Peut encore\njouer en", 230)], LARGEUR - 2 * MARGE)
        lignes = []
        for j in brules:
            pts = j.get("points") or j.get("points_mensuels")
            plus_fortes = sorted(_brulage(j, n).get("plus_fortes") or [])
            possibles = [x["numero"] for x in masc if not _brulage(j, x["numero"]).get("brule")]
            lignes.append([
                cel_nom(j.get("nom"), j.get("prenom"), apres=j.get("categorie")),
                C(fmt(pts) if pts else "", couleur=DOUX),
                C(puces=[(f"V{p}", NEG_FOND, NEG_TEXTE) for p in plus_fortes[:6]]),
                C(", ".join(f"V{p}" for p in possibles), couleur=OK_TEXTE),
            ])
        titre = f"{e['nom_court']} : joueurs brûlés"
        if not lignes:
            r = Rendu()
            r.titre(titre, sous_base)
            r.espace(10)
            r.texte(f"Aucun joueur brûlé pour {e['nom_court']} pour le moment.", 22, NOIR)
            sorties.append((_enregistrer(r.image(), dossier, f"effectif_brules_V{n}.png"), titre))
            continue
        sorties += _tableau_pagine(
            dossier, f"effectif_brules_V{n}", titre, sous_base, colonnes, lignes,
            f"Ces joueurs ont joué 2 matchs dans des équipes plus fortes que la {n} : ils ne peuvent plus jouer en "
            f"{e['nom_court']} cette phase.", titre)
    return sorties


# ---------------------------------------------------------------------------
# Adversaires : prochaine journée et prochain adversaire de chaque équipe
# ---------------------------------------------------------------------------

def _date_renc(r):
    return r.get("date_reelle") or r.get("date")


def _salle(donnees, r):
    club = donnees["club"] if r["vaires_domicile"] else donnees["clubs"].get((r.get("adversaire") or {}).get("club"), {})
    s = (club or {}).get("salle") or r.get("salle") or {}
    if r["vaires_domicile"]:
        return s.get("nom") or ""
    return ", ".join(x for x in (s.get("nom"), s.get("adresse"), " ".join(y for y in (s.get("cp"), s.get("ville")) if y))
                     if x) or "adresse inconnue"


def _pts(j):
    return j.get("points") if j.get("points") is not None else j.get("points_mensuels")


def _clt(j):
    if j.get("classement") is not None:
        return j["classement"]
    p = _pts(j)
    return max(5, p // 100) if p else None


def images_adversaires(donnees, dossier, aujourdhui=None):
    _nettoyer(dossier, "adversaires_")
    auj = (aujourdhui or date.today()).isoformat()
    sorties = []
    prochaines = []
    for e in donnees["equipes"]:
        r = next((r for r in e.get("rencontres", []) if (_date_renc(r) or "") >= auj and r.get("adversaire")), None)
        if r:
            prochaines.append((e, r))
    if not prochaines:
        return sorties
    sous_base = f"{donnees['club']['nom']} · phase {donnees['phase']} {donnees['saison']} · {_genere(donnees)}"

    # 1. La prochaine journée (semaine de la première rencontre à venir)
    premiere = min(_date_renc(r) for _, r in prochaines)
    lundi = date.fromisoformat(premiere) - timedelta(days=date.fromisoformat(premiere).weekday())
    dimanche = lundi + timedelta(days=6)
    semaine = []
    for e in donnees["equipes"]:
        for r in e.get("rencontres", []):
            if lundi.isoformat() <= (_date_renc(r) or "") <= dimanche.isoformat():
                semaine.append((e, r))
    semaine.sort(key=lambda x: (_date_renc(x[1]), x[0]["championnat"] == "F", x[0]["numero"]))
    journees = sorted({r["journee"] for _, r in semaine})
    colonnes = colonnes_egales([Col("Équipe", 120, "g"), Col("Date", 150), Col("Adversaire et lieu", None, "g"),
                                Col("", 86)], LARGEUR - 2 * MARGE)
    lignes = []
    for e, r in semaine:
        dom = r["vaires_domicile"]
        lignes.append([
            C(e["nom_court"], gras=True, align="g"),
            C(jour_fr(_date_renc(r)), sous=r.get("heure") or ""),
            C(r["adversaire"]["libelle"], gras=True, sous=_salle(donnees, r)) if r.get("adversaire")
            else C("exempt", couleur=DOUX),
            C(puces=[("DOM", DOM_FOND, DOM_TEXTE) if dom else ("EXT", EXT_FOND, EXT_TEXTE)]) if r.get("adversaire") else C(""),
        ])
    titre = f"Semaine du {jour_fr(lundi.isoformat())} au {jour_fr(dimanche.isoformat())} · " + ", ".join(f"J{n}" for n in journees)
    r_ = Rendu()
    r_.titre(titre, sous_base)
    r_.espace(10)
    r_.tableau(colonnes, lignes)
    sorties.append((_enregistrer(r_.image(), dossier, "adversaires_prochaine_journee.png"), "Prochaine journée"))

    # 2. Le prochain adversaire de chaque équipe : composition probable, renforts, pas encore joué.
    # L'image prend la largeur de son contenu (pas de colonne vide) : plus lisible sur un téléphone.
    for e, r in prochaines:
        a = r.get("analyse")
        club = donnees["clubs"].get(r["adversaire"]["club"]) or {}
        par_id = {j["id"]: j for j in club.get("joueurs", [])}
        dom = r["vaires_domicile"]
        titre = f"{e['nom_court']} · J{r['journee']} · {jour_fr(_date_renc(r))} {r.get('heure') or ''}".strip()
        sous_titre = f"{'reçoit' if dom else 'se déplace à'} {r['adversaire']['libelle']} · {_salle(donnees, r)}"
        if not a:
            img = Rendu()
            img.titre(titre, sous_titre)
            img.espace(6)
            img.texte("Effectif de l'adversaire inconnu (club absent des données).", 20, NOIR)
        else:
            def lignes_joueurs(ids, info=None):
                sortie = []
                for jid in ids:
                    j = par_id.get(jid)
                    if not j:
                        continue
                    sortie.append([
                        cel_nom(j.get("nom"), j.get("prenom"), apres="F" if j.get("sexe") == "F" else None),
                        C(_clt(j) or "", gras=True), C(fmt(_pts(j)) if _pts(j) else "", couleur=DOUX),
                        C(j.get("categorie") or "", couleur=DOUX), C((info or {}).get(jid, ""), couleur=DOUX, align="g"),
                    ])
                return sortie

            def ou_aucun(lignes, texte="aucun"):
                return lignes or [[C(texte, couleur=DOUX, align="g"), C(), C(), C(), C()]]

            renforts = {x["id"]: "a joué en " + ", ".join(str(n) for n in x["equipes"]) for x in a.get("renforts", [])}
            pas_joue = [jid for jid in a.get("non_alignes", []) if jid not in a["probable"]]
            tableaux = [
                ("Composition probable", "estimation", ou_aucun(lignes_joueurs(a["probable"]), "—")),
                ("Renforts possibles", "joueurs d'équipes plus fortes, non brûlés",
                 ou_aucun(lignes_joueurs([x["id"] for x in a.get("renforts", [])][:8], renforts))),
                ("Pas encore joué cette phase", f"les 8 mieux classés sur {len(pas_joue)}" if len(pas_joue) > 8 else None,
                 ou_aucun(lignes_joueurs(pas_joue[:8]))),
            ]
            toutes = [l for _, _, lignes in tableaux for l in lignes]
            info = max((largeur_naturelle(l[4]) for l in toutes if l[4].texte), default=0)
            if not info:  # aucune information : la colonne disparaît
                tableaux = [(t_, d_, [l[:4] for l in lignes]) for t_, d_, lignes in tableaux]
            fixes = [Col("Clt", 70), Col("Pts", 90), Col("Cat.", 80)] + ([Col("", info + 10, "g")] if info else [])
            nom = max(NOM_MIN, max(largeur_naturelle(l[0]) for l in toutes) + 6)
            largeur = min(LARGEUR, max(FICHE_MIN, round(nom + sum(c.largeur for c in fixes) + 2 * MARGE)))
            colonnes = colonnes_egales([Col("Joueur", None, "g")] + fixes, largeur - 2 * MARGE)
            img = Rendu(largeur)
            img.titre(titre, sous_titre)
            img.espace(6)
            for t_, d_, lignes in tableaux:
                img.section(t_, d_)
                img.tableau(colonnes, lignes)
            if a.get("brules"):
                img.texte(f"{len(a['brules'])} joueur(s) brûlé(s) ou indisponible(s) pour cette rencontre : détail sur la page.", 17)
        img.pied("Composition probable : estimation à partir des rencontres déjà jouées par le club adverse.")
        nom_fichier = f"adversaires_{e['id'].upper()}.png"
        sorties.append((_enregistrer(img.image(), dossier, nom_fichier), f"{e['nom_court']} : prochain adversaire"))
    return sorties

"""Classements des poules de toutes les équipes de Vaires : une page et une image à partager.

Sur le modèle de l'image proposée par le club : fond sombre, bandeau en haut (logo du club, raquette
et balle), « CLASSEMENTS DES POULES » et « APRÈS LA JOURNÉE 03 • PHASE 1 • 2026–2027 », puis une
carte par équipe (bandeau rouge « VAIRES 1 », colonnes # ÉQUIPE PTS J V N D, la ligne de Vaires en
rouge), deux par rangée, et la légende en bas. Police DejaVu Sans (fournie avec l'outil, licence
libre). Le logo du club est pris dans le dossier import (logo_club.png, sinon logo_gauche.png) ;
sans logo, un écusson « CVTT » le remplace.

Les classements sont ceux de la page des adversaires : calculés à partir des feuilles de match
(points de rencontre de la FFTT, puis parties gagnées / perdues en cas d'égalité).
"""

import random
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

from .adversaires import donnees_classements

POLICES = Path(__file__).with_name("polices")
NORMAL, GRAS = "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"
F = 2                     # suréchantillonnage du dessin
LARGEUR = 1080
MARGE, ECART = 36, 22     # bords de l'image, espace entre deux cartes
HAUT_BANDEAU = 236
HAUT_TETE, HAUT_COLONNES, HAUT_LIGNE = 38, 28, 28
EXTENSIONS_IMAGES = (".jpg", ".jpeg", ".png", ".webp")

FOND = (13, 14, 17)
CARTE, CARTE_ALT, BORD = (22, 23, 28), (28, 29, 35), (52, 54, 62)
ROUGE, ROUGE_FONCE, ROUGE_VIF = (204, 16, 40), (150, 10, 28), (255, 46, 64)
BLANC, GRIS, GRIS_CLAIR = (241, 243, 245), (150, 156, 166), (196, 200, 206)
LEGENDE = "J : joués   •   V : victoires   •   N : nuls   •   D : défaites   •   PTS : points"

_polices = {}


def police(nom, taille):
    cle = (nom, taille)
    if cle not in _polices:
        _polices[cle] = ImageFont.truetype(str(POLICES / nom), round(taille * F))
    return _polices[cle]


def ecrire(d, x, y, texte, nom, taille, couleur, ancre="ls"):
    d.text((x * F, y * F), texte, font=police(nom, taille), fill=couleur, anchor=ancre)


def largeur(texte, nom, taille):
    return police(nom, taille).getlength(texte) / F


def raccourcir(texte, nom, taille, place):
    if largeur(texte, nom, taille) <= place:
        return texte
    while texte and largeur(texte + "…", nom, taille) > place:
        texte = texte[:-1]
    return texte.rstrip() + "…"


def sous_titre(c):
    saison = c["saison"].replace("-", "–")
    debut = f"APRÈS LA JOURNÉE {c['journee']:02d}" if c["journee"] else "AVANT LA PREMIÈRE JOURNÉE"
    return f"{debut}   •   PHASE {c['phase']}   •   {saison}"


# ---------------------------------------------------------------------------
# Fond : fumée rouge, raquette et balle (dessinés, toujours les mêmes)
# ---------------------------------------------------------------------------

def _bruit(w, h, graine, octaves=((5, 0.5), (11, 0.3), (25, 0.2))):
    """Bruit lissé en niveaux de gris : une fumée. Déterministe (même graine, même image)."""
    rnd = random.Random(graine)
    total = None
    for pas, poids in octaves:
        pw, ph = max(2, w // (pas * F * 8)), max(2, h // (pas * F * 8))
        petit = Image.frombytes("L", (pw, ph), bytes(rnd.getrandbits(8) for _ in range(pw * ph)))
        couche = petit.resize((w, h), Image.BICUBIC)
        total = couche if total is None else Image.blend(total, couche, poids / (poids + 0.5))
    return total.filter(ImageFilter.GaussianBlur(3 * F))


def _tache(w, h, cx, cy, rx, ry, force=1.0):
    """Masque elliptique adouci centré en (cx, cy) : 255 au centre, 0 au bord de l'ellipse."""
    # radial_gradient vaut 181 au milieu d'un bord : ramené à 0 là, en courbe douce
    grad = Image.radial_gradient("L").point(lambda v: round(255 * (1 - min(v, 181) / 181) ** 1.6))
    grad = grad.resize((max(1, round(2 * rx * F)), max(1, round(2 * ry * F))), Image.BICUBIC)
    masque = Image.new("L", (w, h), 0)
    masque.paste(grad, (round((cx - rx) * F), round((cy - ry) * F)))
    return masque.point(lambda v: min(255, round(v * force)))


def _tramage(w, h, graine):
    """Petit bruit (0 à 3) ajouté aux masques : évite les marches visibles des dégradés sombres."""
    return Image.frombytes("L", (w, h), random.Random(graine).randbytes(w * h)).point(lambda v: v >> 6)


def _fumee(img, graine, taches, force=1.0):
    """Fumée rouge sur les zones données [(cx, cy, rx, ry, force)] : une lueur diffuse et des volutes."""
    w, h = img.size
    zone = Image.new("L", (w, h), 0)
    for t in taches:
        zone = ImageChops.lighter(zone, _tache(w, h, *t))
    zone = ImageChops.add(zone, _tramage(w, h, graine), offset=-1)
    lueur = ImageChops.multiply(_bruit(w, h, graine, ((9, 1.0), (20, 0.4))), zone).point(lambda v: round(v * 0.75 * force))
    img.paste(Image.new("RGB", (w, h), (120, 6, 18)), (0, 0), lueur)
    # Volutes : les lignes de niveau du bruit (fines et claires), adoucies
    volutes = _bruit(w, h, graine + 1, ((4, 0.6), (9, 0.4))).point(lambda v: max(0, 255 - abs(2 * v - 255) * 4))
    volutes = ImageChops.multiply(volutes.filter(ImageFilter.GaussianBlur(2 * F)), zone).point(lambda v: round(v * 0.55 * force))
    img.paste(Image.new("RGB", (w, h), (230, 40, 52)), (0, 0), volutes)


def _balle(img, cx, cy, r):
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).ellipse([(cx - r * 1.5) * F, (cy - r * 1.5) * F, (cx + r * 1.5) * F, (cy + r * 1.5) * F], fill=90)
    img.paste(Image.new("RGB", img.size, (255, 255, 255)), (0, 0), halo.filter(ImageFilter.GaussianBlur(r * F * 0.6)))
    taille = round(2 * r * F)
    # Ombrage : clair en haut à gauche, gris en bas à droite
    grad = ImageOps.invert(Image.radial_gradient("L")).resize((taille * 2, taille * 2))
    lum = grad.crop((round(taille * 0.6), round(taille * 0.55), round(taille * 1.6), round(taille * 1.55))).resize((taille, taille))
    sphere = Image.merge("RGB", [lum.point(lambda v: 120 + v * 130 // 255)] * 3)
    masque = Image.new("L", (taille, taille), 0)
    ImageDraw.Draw(masque).ellipse([0, 0, taille - 1, taille - 1], fill=255)
    img.paste(sphere, (round((cx - r) * F), round((cy - r) * F)), masque.filter(ImageFilter.GaussianBlur(1)))


def _raquette(img, cx, cy, r, angle):
    """Raquette vue de face : revêtement rouge, bord noir, manche en bois ; tournée de `angle` degrés."""
    t = round(r * F)
    calque = Image.new("RGBA", (t * 2, round(t * 3.4)), (0, 0, 0, 0))
    d = ImageDraw.Draw(calque)
    manche = [t - t * 0.2, t * 1.75, t + t * 0.2, t * 3.3]
    d.rounded_rectangle(manche, radius=t * 0.12, fill=(92, 58, 36, 255), outline=(30, 20, 14, 255), width=max(1, t // 40))
    d.ellipse([0, 0, t * 2 - 1, t * 2 * 1.06], fill=(18, 18, 20, 255))
    d.ellipse([t * 0.05, t * 0.05, t * 1.95, t * 2 * 1.03], fill=(196, 14, 34, 255))
    grain = _bruit(calque.width, calque.height, 7, octaves=((1, 1.0),)).point(lambda v: 255 if v > 132 else 0)
    revetement = Image.new("L", calque.size, 0)
    ImageDraw.Draw(revetement).ellipse([t * 0.05, t * 0.05, t * 1.95, t * 2 * 1.03], fill=22)
    calque.paste((120, 6, 20, 255), (0, 0), ImageChops.multiply(grain, revetement))
    reflet = Image.new("L", calque.size, 0)
    ImageDraw.Draw(reflet).ellipse([t * 0.3, t * 0.2, t * 1.2, t * 1.0], fill=70)
    calque.paste((255, 120, 120, 255), (0, 0), reflet.filter(ImageFilter.GaussianBlur(t * 0.25)))
    calque = calque.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(calque, (round(cx * F - calque.width / 2), round(cy * F - calque.height / 2)), calque)


def _logo_du_dossier(dossier_import):
    if not dossier_import or not Path(dossier_import).is_dir():
        return None
    for debut in ("logo_club", "logo_gauche"):
        for f in sorted(Path(dossier_import).iterdir()):
            if (f.is_file() and f.suffix.lower() in EXTENSIONS_IMAGES
                    and re.fullmatch(re.escape(debut) + r"(\D.*)?", f.stem.lower())):
                try:
                    with Image.open(f) as im:
                        return ImageOps.exif_transpose(im).convert("RGBA")
                except OSError:
                    print(f"  ! image illisible : {f.name}")
    return None


def _ecusson(img, d, cx, cy, r):
    """Sans logo dans le dossier import : un écusson rouge « CVTT »."""
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).ellipse([(cx - r * 1.25) * F, (cy - r * 1.25) * F, (cx + r * 1.25) * F, (cy + r * 1.25) * F], fill=150)
    img.paste(Image.new("RGB", img.size, (230, 20, 40)), (0, 0), halo.filter(ImageFilter.GaussianBlur(r * F * 0.35)))
    d.ellipse([(cx - r) * F, (cy - r) * F, (cx + r) * F, (cy + r) * F], fill=(222, 18, 38), outline=(20, 20, 22), width=round(5 * F))
    d.ellipse([(cx - r * 0.82) * F, (cy - r * 0.82) * F, (cx + r * 0.82) * F, (cy + r * 0.82) * F], outline=(20, 20, 22), width=round(2 * F))
    ecrire(d, cx, cy + r * 0.12, "CVTT", GRAS, r * 0.5, (20, 20, 22), "ms")
    ecrire(d, cx, cy + r * 0.5, "VAIRES-SUR-MARNE", GRAS, r * 0.095, (20, 20, 22), "ms")


def _bandeau(img, d, dossier_import):
    w = img.width
    hb = HAUT_BANDEAU * F
    fond = Image.new("RGB", (w, hb), (16, 7, 9))
    _fumee(fond, 11, [(LARGEUR * 0.2, 40, 380, 190, 1.3), (LARGEUR * 0.75, 110, 420, 200, 1.5)])
    _raquette(fond, LARGEUR - 230, 70, 118, -38)
    _balle(fond, LARGEUR - 280, 150, 52)
    # Fondu vers le fond de l'image en bas du bandeau
    fondu = Image.linear_gradient("L").resize((w, round(70 * F)))
    fond.paste(Image.new("RGB", (w, fondu.height), FOND), (0, hb - fondu.height), fondu)
    img.paste(fond, (0, 0))
    logo = _logo_du_dossier(dossier_import)
    cx, cy, r = 165, 116, 98
    if logo:
        logo.thumbnail((round(2 * r * F), round(2 * r * F)), Image.LANCZOS)
        img.paste(logo, (round(cx * F - logo.width / 2), round(cy * F - logo.height / 2)), logo)
    else:
        _ecusson(img, d, cx, cy, r)


# ---------------------------------------------------------------------------
# Cartes
# ---------------------------------------------------------------------------

def _colonnes(x, w):
    """Abscisses : centre de #, début du nom, centres de PTS J V N D."""
    return {"#": x + 22, "équipe": x + 48, "PTS": x + w - 152, "J": x + w - 117, "V": x + w - 86,
            "N": x + w - 55, "D": x + w - 24}


def _carte(img, d, x, y, w, h, poule):
    d.rounded_rectangle([x * F, y * F, (x + w) * F, (y + h) * F], radius=5 * F, fill=CARTE, outline=BORD, width=F)
    # Bandeau rouge, en dégradé
    tete = Image.linear_gradient("L").rotate(90, expand=True).resize((round(w * F), round(HAUT_TETE * F)))
    rouge = Image.composite(Image.new("RGB", tete.size, ROUGE_FONCE), Image.new("RGB", tete.size, ROUGE), tete)
    masque = Image.new("L", tete.size, 0)
    ImageDraw.Draw(masque).rounded_rectangle([0, 0, tete.width - 1, tete.height + 10 * F], radius=5 * F, fill=255)
    img.paste(rouge, (round(x * F), round(y * F)), masque)
    ecrire(d, x + 13, y + 27, poule["equipe"].upper(), GRAS, 19, BLANC)
    ecrire(d, x + w - 12, y + 17, "CLASSEMENT DE LA POULE", NORMAL, 8.5, BLANC, "rs")
    info = " • ".join(t for t in (poule["division"], poule["poule"]) if t).upper()
    ecrire(d, x + w - 12, y + 30, raccourcir(info, NORMAL, 8.5, w / 2), NORMAL, 8.5, (255, 205, 210), "rs")
    col = _colonnes(x, w)
    yc = y + HAUT_TETE + HAUT_COLONNES - 9
    ecrire(d, col["#"], yc, "#", GRAS, 10.5, GRIS, "ms")
    ecrire(d, col["équipe"], yc, "ÉQUIPE", GRAS, 10.5, GRIS)
    for c in ("PTS", "J", "V", "N", "D"):
        ecrire(d, col[c], yc, c, GRAS, 10.5, GRIS, "ms")
    place_nom = col["PTS"] - 22 - col["équipe"]
    for i, l in enumerate(poule["lignes"]):
        y0 = y + HAUT_TETE + HAUT_COLONNES + i * HAUT_LIGNE
        if l["nous"]:
            d.rectangle([(x + 1) * F, y0 * F, (x + w - 1) * F, (y0 + HAUT_LIGNE) * F], fill=ROUGE)
            d.rectangle([(x + 1) * F, y0 * F, (x + 5) * F, (y0 + HAUT_LIGNE) * F], fill=ROUGE_VIF)
        elif i % 2 == 0:
            d.rectangle([(x + 1) * F, y0 * F, (x + w - 1) * F, (y0 + HAUT_LIGNE) * F], fill=CARTE_ALT)
        if not l["nous"] and i:
            d.line([(x + 1) * F, y0 * F, (x + w - 1) * F, y0 * F], fill=(34, 35, 42), width=1)
        yt = y0 + 19
        gras = GRAS if l["nous"] else NORMAL
        couleur = BLANC if l["nous"] else GRIS_CLAIR
        ecrire(d, col["#"], yt, str(l["rang"]), gras, 13, BLANC, "ms")
        ecrire(d, col["équipe"], yt, raccourcir(l["libelle"], gras, 13, place_nom), gras, 13, BLANC)
        ecrire(d, col["PTS"], yt, str(l["points"]), GRAS, 13, BLANC, "ms")
        for c, cle in (("J", "joues"), ("V", "v"), ("N", "n"), ("D", "d")):
            ecrire(d, col[c], yt, str(l[cle]), gras, 13, couleur if not l["nous"] else BLANC, "ms")


def image_classements(donnees, dossier_import, dossier):
    """Écrit classements_poules.png (toutes les poules des équipes de Vaires). Renvoie [(chemin, titre)]."""
    for f in Path(dossier).glob("classements_*.png"):
        f.unlink()
    c = donnees_classements(donnees)
    if not c["poules"]:
        return []
    w_carte = (LARGEUR - 2 * MARGE - ECART) / 2
    lignes_max = max(len(p["lignes"]) for p in c["poules"])
    h_carte = HAUT_TETE + HAUT_COLONNES + lignes_max * HAUT_LIGNE + 10
    haut_cartes = 338
    rangees = (len(c["poules"]) + 1) // 2
    hauteur = round(haut_cartes + rangees * (h_carte + 20) + 40)
    img = Image.new("RGB", (LARGEUR * F, hauteur * F), FOND)
    # Fumée en bas, dans la place libre à côté de la dernière carte si elle est seule
    seule = len(c["poules"]) % 2 == 1
    _fumee(img, 23, [(LARGEUR * (0.78 if seule else 0.5), hauteur - (h_carte / 2 if seule else 40),
                      LARGEUR * (0.32 if seule else 0.6), h_carte * 0.75 if seule else 120, 1.4)])
    d = ImageDraw.Draw(img)
    _bandeau(img, d, dossier_import)
    d = ImageDraw.Draw(img)
    titre = "CLASSEMENTS DES POULES"
    ecrire(d, LARGEUR / 2, 272, titre, GRAS, 41, BLANC, "ms")
    ecrire(d, LARGEUR / 2, 306, sous_titre(c), NORMAL, 15.5, GRIS_CLAIR, "ms")
    for i, poule in enumerate(c["poules"]):
        x = MARGE + (i % 2) * (w_carte + ECART)
        y = haut_cartes + (i // 2) * (h_carte + 20)
        _carte(img, d, x, y, w_carte, h_carte, poule)
    ecrire(d, MARGE + 16, hauteur - 14, LEGENDE, NORMAL, 11, GRIS_CLAIR)
    chemin = Path(dossier) / "classements_poules.png"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.resize((LARGEUR, hauteur), Image.LANCZOS).save(chemin, optimize=True)
    titre_image = "Classements des poules" + (f" après la J{c['journee']}" if c["journee"] else "")
    return [(chemin, titre_image)]

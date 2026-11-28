"""Récapitulatif de la journée en une image, sur le modèle de celle publiée par le club.

Pour chaque équipe : le bandeau rouge « Vaires 1 (D1) », le résultat et le score en points-
parties (domicile – extérieur), puis chaque joueur avec ses victoires et défaites (une étoile
orange pour une perf : une victoire contre un joueur qui a plus de points), et les doubles. En bas
à droite, le top 5 des perfs de la journée. En haut, la place de la photo : elle y est collée si
le dossier import contient photo_J3.jpg (J3 = la journée), de même que les logos logo_gauche.png
et logo_droite.png ; sinon la place reste libre pour la coller soi-même.

Les noms : le prénom, suivi des initiales du nom quand deux joueurs de l'image ont le même prénom
(« Jérôme D », « Jérôme L ») ; si les initiales sont les mêmes, le début du nom (« Marc Gu. », « Marc Go. »). Le fichier import/surnoms.txt peut imposer un nom affiché, une
ligne par joueur : « GUITTON Marc = Marc G ». Pour la mise à jour lancée depuis le site, les mêmes
lignes peuvent aussi être mises dans le secret GitHub SURNOMS (il l'emporte sur le fichier).

Le modèle a été fait avec Excalidraw : mêmes polices (fournies avec l'outil, licence SIL OFL),
Lilita One pour les titres et Excalifont pour l'écriture à la main, et mêmes couleurs (palette
d'Excalidraw). Image de 1280 points de large, dessinée en double résolution.
"""

import math
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

POLICES = Path(__file__).with_name("polices")
TITRE, MAIN = "LilitaOne-Regular.ttf", "Excalifont-Regular.ttf"
F = 2                     # suréchantillonnage du dessin

LARGEUR, HAUTEUR_MIN = 1280, 987
# Palette d'Excalidraw
ROUGE, VERT, ORANGE, NOIR, GRIS = "#E03131", "#2F9E44", "#F08C00", "#1E1E1E", "#868E96"
BLEU = "#1971C2"  # bandeaux et titre du championnat des jeunes dans l'image de Paris (28/11)
JAUNE, BRONZE = "#FFEC99", "#846358"
PHOTO = (444, 48, 1186, 497)                 # place laissée pour la photo
LOGOS = {"gauche": (444, 48, 170, 80), "droite": (1186, 48, 185, 50)}  # coin, largeur et hauteur maximales
COLONNES = (18, 436, 855)                    # bord gauche des blocs
BANDEAU_L, BANDEAU_H = 228, 47
PAS_LIGNE = 33.25
PAS_RANGEE = 235
EXTENSIONS_IMAGES = (".jpg", ".jpeg", ".png", ".webp")

_polices = {}


def police(nom, taille):
    cle = (nom, round(taille * F))
    if cle not in _polices:
        _polices[cle] = ImageFont.truetype(str(POLICES / nom), cle[1])
    return _polices[cle]


def largeur(texte, nom, taille):
    return police(nom, taille).getlength(texte) / F


def ajuste(texte, nom, taille, maxi):
    """Taille de police pour que le texte tienne dans `maxi` points."""
    while taille > 10 and largeur(texte, nom, taille) > maxi:
        taille -= 0.5
    return taille


def ecrire(d, x, y, texte, nom, taille, couleur, ancre="ls"):
    d.text((x * F, y * F), texte, font=police(nom, taille), fill=couleur, anchor=ancre)


# ---------------------------------------------------------------------------
# Données : équipes, joueurs, perfs
# ---------------------------------------------------------------------------

def _cle(texte):
    """Comparaison sans accents ni majuscules : « Jérôme » = « JEROME »."""
    t = unicodedata.normalize("NFKD", texte or "")
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).upper().split())


def _surnoms(texte):
    """« NOM Prénom = nom affiché », une ligne par joueur (ou séparés par des « ; »), # pour un commentaire."""
    surnoms = {}
    for ligne in re.split(r"[\r\n;]+", texte or ""):
        ligne = ligne.split("#", 1)[0]
        if "=" in ligne:
            qui, affiche = (x.strip() for x in ligne.split("=", 1))
            if qui and affiche:
                surnoms[_cle(qui)] = affiche
    return surnoms


def lire_surnoms(dossier_import):
    """import/surnoms.txt, complété par le secret GitHub SURNOMS (variable d'environnement), qui
    l'emporte : la mise à jour lancée depuis le site n'a pas le fichier si le PC ne l'a pas envoyé."""
    fichier = Path(dossier_import or ".") / "surnoms.txt"
    surnoms = {}
    if dossier_import and fichier.is_file():
        surnoms = _surnoms(fichier.read_text(encoding="utf-8-sig", errors="replace"))
    return {**surnoms, **_surnoms(os.environ.get("SURNOMS"))}


def noms_affiches(joueurs, surnoms=None):
    """{licence: nom affiché} : le prénom, suivi des initiales du nom si un autre joueur de l'image
    a le même prénom ; un surnom de import/surnoms.txt (ou du secret SURNOMS) l'emporte, sauf s'il peut se confondre
    avec le nom d'un autre joueur de l'image."""
    surnoms = surnoms or {}
    par_prenom = defaultdict(set)
    graphies = defaultdict(set)  # « Jerome » et « Jérôme » : le même prénom, écrit avec ses accents
    for j in joueurs:
        par_prenom[_cle(j["prenom"])].add(j["licence"])
        graphies[_cle(j["prenom"])].add(j["prenom"])
    automatiques = {}
    for j in joueurs:
        nom = max(graphies[_cle(j["prenom"])], key=lambda g: (sum(not c.isascii() for c in g), g)) or j["nom"]
        if len(par_prenom[_cle(j["prenom"])]) > 1:
            nom += " " + _distinction(j, [x for x in joueurs if _cle(x["prenom"]) == _cle(j["prenom"])])
        automatiques[j["licence"]] = nom
    noms = dict(automatiques)
    for j in joueurs:
        surnom = surnoms.get(_cle(f"{j['nom']} {j['prenom']}"))
        # Un surnom l'emporte, sauf s'il peut se confondre avec le nom d'un autre joueur de l'image (« Marc G » à côté de
        # « Marc Go. », 28/11) : le nom distinctif est alors gardé (« Marc Gu. »)
        if surnom and not any(_confusion(surnom, n) for lic, n in automatiques.items() if lic != j["licence"]):
            noms[j["licence"]] = surnom
    return noms


def _confusion(a, b):
    """Deux noms affichés qu'on peut confondre : égaux, ou l'un est le début de l'autre (« Marc G », « Marc Go. »)."""
    a, b = _cle(a).rstrip(". "), _cle(b).rstrip(". ")
    return a == b or b.startswith(a) or a.startswith(b)


def _initiales(nom):
    return "".join(m[0] for m in re.split(r"[\s-]+", (nom or "").strip()) if m)


def _distinction(joueur, meme_prenom):
    """Ce qui suit le prénom quand plusieurs joueurs de l'image le portent : les initiales du nom (« D », « L ») ;
    si elles ne suffisent pas, le début du nom jusqu'à ce qu'il les distingue (« Gu. » et « Go. », 28/11)."""
    autres = [x for x in meme_prenom if x["licence"] != joueur["licence"]]
    initiales = _initiales(joueur["nom"])
    if all(_cle(_initiales(x["nom"])) != _cle(initiales) for x in autres):
        return initiales
    nom = " ".join((joueur["nom"] or "").split())
    rivaux = [_cle(" ".join((x["nom"] or "").split())) for x in autres if _cle(_initiales(x["nom"])) == _cle(initiales)]
    for k in range(2, len(nom) + 1):
        debut = _cle(nom[:k])
        if all(not r.startswith(debut) for r in rivaux):
            return nom[:k].strip().capitalize() + ("." if k < len(nom) else "")
    return nom.title()  # même prénom et même nom : le nom entier


def _resultat(r):
    """(libellé, couleur) du résultat d'une rencontre, avec le score en points-parties domicile – extérieur."""
    if not r["parties"]:
        return ("Forfait" if r.get("forfait") else "Pas encore saisi"), GRIS
    nous, eux = r.get("points_partie") or [None, None]
    if nous is None or eux is None:
        nous, eux = r["score"]
    dom, ext = (nous, eux) if r["domicile"] else (eux, nous)
    if nous > eux:
        return f"Victoire {dom} – {ext}", VERT
    if nous < eux:
        return f"Défaite {dom} – {ext}", ROUGE
    return f"Égalité {dom} – {ext}", ORANGE


def equipes_de_la_journee(rencontres):
    """Pour chaque rencontre : titre, résultat, joueurs (victoires, défaites, perfs) et doubles."""
    feminines = sum(1 for r in rencontres if r.get("feminine"))
    equipes = []
    for r in rencontres:
        division = f" ({r['division_courte']})" if r.get("division_courte") else ""
        if r.get("feminine"):
            titre = "Féminine" + (f" {r['numero']}" if feminines > 1 else "") + division
        else:
            titre = f"Vaires {r.get('numero') or ''}".strip() + division
        joueurs, doubles = {}, [0, 0]
        for p in r["parties"]:
            if p["gagne"] is None:
                continue
            if p["double"]:
                doubles[0 if p["gagne"] else 1] += 1
                continue
            if len(p["nous"]) != 1:
                continue
            moi = p["nous"][0]
            j = joueurs.setdefault(moi["licence"], {**moi, "v": 0, "d": 0, "perfs": [], "groupe": p.get("groupe") or 0})
            j["v" if p["gagne"] else "d"] += 1
            adv = (p["eux"] or [{}])[0].get("points")
            if p["gagne"] and adv and moi.get("points") and adv > moi["points"]:
                j["perfs"].append(adv)
        libelle, couleur = _resultat(r)
        nb_doubles = sum(1 for p in r["parties"] if p["double"])
        equipes.append({"titre": titre, "resultat": libelle, "couleur": couleur,
                        "joueurs": sorted(joueurs.values(), key=lambda j: (j["groupe"], j.get("lettre") or "", j["nom"])),
                        "doubles": doubles if nb_doubles else None, "nb_doubles": nb_doubles})
    return equipes


def top_perfs(equipes, noms, n=5):
    """Les n plus grosses perfs de la journée : (nom, points des joueurs battus, plus grand écart)."""
    par_joueur = {}
    for e in equipes:
        for j in e["joueurs"]:
            if j["perfs"]:
                q = par_joueur.setdefault(j["licence"], {"nom": noms[j["licence"]], "points": j["points"], "battus": []})
                q["battus"] += j["perfs"]
    perfs = [(q["nom"], sorted(q["battus"], reverse=True), max(q["battus"]) - q["points"]) for q in par_joueur.values()]
    perfs.sort(key=lambda x: (-x[2], -len(x[1]), x[0]))
    return perfs[:n]


def _liste(points):
    return " et ".join([", ".join(str(p) for p in points[:-1]), str(points[-1])]) if len(points) > 1 else str(points[0])


# ---------------------------------------------------------------------------
# Dessin
# ---------------------------------------------------------------------------

def _emplacements(nb):
    """Haut-gauche des blocs : deux à gauche de la photo, puis des rangées de trois."""
    places = [(COLONNES[0], 58), (COLONNES[0], 290)]
    rangee = 0
    while len(places) < nb:
        places += [(x, 517 + rangee * PAS_RANGEE) for x in COLONNES]
        rangee += 1
    return places[:nb]


def hauteur_bloc(equipe):
    """Hauteur d'un bloc d'équipe : bandeau, puis une ligne par joueur (et les doubles)."""
    return 85 + (len(equipe["joueurs"]) + (1 if equipe["doubles"] else 0) - 1) * PAS_LIGNE + 30


def hauteur_top(n):
    """Hauteur du cadre des perfs pour n lignes (221 points pour le top 5 du modèle)."""
    return 221 + (n - 5) * 23.75


def _emplacements_paris_jeunes(hauteurs, hauteurs_jeunes):
    """Paris + jeunes (28/11, demande du club) : les équipes de Paris l'une sous l'autre à gauche (Vaires 1, 2, 3),
    les équipes jeunes l'une sous l'autre sous la photo (−15 ans, puis −13 ans), le cadre des perfs à droite, aussi
    haut que la place le permet : top 15, sinon top 10, sinon top 5. Renvoie (emplacements des équipes de Paris,
    du cadre des perfs, des équipes jeunes, hauteur de l'image, nombre de lignes du cadre)."""
    def pile(x, y, hs):
        places = []
        for h in hs:
            places.append((x, y))
            y += h + 12
        return places, y - 12
    places, bas_gauche = pile(COLONNES[0], 58, hauteurs)
    places_jeunes, bas_jeunes = pile(COLONNES[1], 517, hauteurs_jeunes)
    hauteur = max(HAUTEUR_MIN, round(max(bas_gauche, bas_jeunes, 517 + hauteur_top(5)) + 20))
    lignes = next(n for n in (15, 10, 5) if n == 5 or 516 + hauteur_top(n) <= hauteur - 12)
    return places, (COLONNES[2], 517), places_jeunes, hauteur, lignes


def titre_jeunes(rencontre):
    """« Vaires 1 (−15 ans) » : la catégorie d'âge de la division (« MOINS 15 » dans l'API)."""
    m = re.search(r"MOINS\s*(\d+)|-\s*(\d+)\s*ANS", (rencontre.get("division") or "").upper())
    age = f" (−{m[1] or m[2]} ans)" if m else (f" ({rencontre['division_courte']})" if rencontre.get("division_courte") else "")
    return f"Vaires {rencontre.get('numero') or ''}".strip() + age


def _emplacements_variables(hauteurs):
    """Championnat de Paris (équipes de 9, 6 et 3 joueurs) : à gauche de la photo tant que les blocs y tiennent,
    puis des rangées de trois sous la photo, chaque rangée aussi haute que son plus grand bloc. Le dernier
    emplacement (le top 5, 221 points de haut) suit les équipes. Renvoie (emplacements, hauteur de l'image)."""
    places, y = [], 58
    i = 0
    while i < len(hauteurs) and y + hauteurs[i] <= PHOTO[3] + 10:
        places.append((COLONNES[0], y))
        y += hauteurs[i] + 12
        i += 1
    y = 517
    reste = hauteurs[i:] + [221 + 14]
    while reste:
        rangee, reste = reste[:3], reste[3:]
        places += [(x, y) for x in COLONNES[:len(rangee)]]
        y += max(rangee) + 12
    return places, max(HAUTEUR_MIN, y + 10)


def _bloc(d, x0, y0, equipe, noms):
    d.rounded_rectangle([x0 * F, y0 * F, (x0 + BANDEAU_L) * F, (y0 + BANDEAU_H) * F], radius=10 * F,
                        fill=equipe.get("bandeau", ROUGE))
    ecrire(d, x0 + BANDEAU_L / 2, y0 + BANDEAU_H / 2 + 1, equipe["titre"], TITRE,
           ajuste(equipe["titre"], TITRE, 26, BANDEAU_L - 14), "white", "mm")
    ecrire(d, x0 + BANDEAU_L + 10, y0 + BANDEAU_H / 2 + 1, equipe["resultat"], TITRE,
           ajuste(equipe["resultat"], TITRE, 27, 400 - BANDEAU_L), equipe["couleur"], "lm")
    lignes = [(f"{noms[j['licence']]} ({j['points']})" if j.get("points") else noms[j["licence"]], j["v"], j["d"], bool(j["perfs"]))
              for j in equipe["joueurs"]]
    if equipe["doubles"]:
        lignes.append(("Doubles" if equipe["nb_doubles"] > 1 else "Double", *equipe["doubles"], False))
    centre = x0 + 112
    # Un nom long (et son astérisque) ne doit pas toucher les victoires : les colonnes V et D se décalent.
    fin = max((centre + largeur(nom, MAIN, ajuste(nom, MAIN, 26.5, 222)) / 2 + (19 if perf else 0)
               for nom, _, _, perf in lignes), default=0)
    decalage = min(45, max(0, fin + 14 - (x0 + 243)))
    for i, (nom, v, dd, perf) in enumerate(lignes):
        base = y0 + 85 + i * PAS_LIGNE
        taille = ajuste(nom, MAIN, 26.5, 222)
        ecrire(d, centre, base, nom, MAIN, taille, NOIR, "ms")
        if perf:
            _asterisque(d, centre + largeur(nom, MAIN, taille) / 2 + 9, base - 25)
        ecrire(d, x0 + 243 + decalage, base, f"{v}V", MAIN, 26.5, VERT)
        ecrire(d, x0 + 293 + decalage, base, f"{dd}D", MAIN, 26.5, ROUGE)


def _asterisque(d, cx, cy, rayon=8.5, couleur=ORANGE):
    """Astérisque à 6 branches comme sur le modèle (celui de la police n'en a que 5)."""
    for angle, longueur in ((90, rayon * 0.82), (28, rayon), (152, rayon)):
        a = math.radians(angle)
        dx, dy = longueur * math.cos(a), longueur * math.sin(a)
        d.line([((cx - dx) * F, (cy - dy) * F), ((cx + dx) * F, (cy + dy) * F)], fill=couleur, width=round(3 * F))
        for x, y in ((cx - dx, cy - dy), (cx + dx, cy + dy)):
            d.ellipse([(x - 1.5) * F, (y - 1.5) * F, (x + 1.5) * F, (y + 1.5) * F], fill=couleur)


def _courbe(d, points, couleur, epaisseur):
    d.line([(x * F, y * F) for x, y in points], fill=couleur, width=round(epaisseur * F), joint="curve")


def _fleche(d, depart, controle, arrivee, couleur):
    pts = [((1 - t) ** 2 * depart[0] + 2 * (1 - t) * t * controle[0] + t * t * arrivee[0],
            (1 - t) ** 2 * depart[1] + 2 * (1 - t) * t * controle[1] + t * t * arrivee[1]) for t in (i / 20 for i in range(21))]
    _courbe(d, pts, couleur, 2.4)
    (xa, ya), (xb, yb) = pts[-3], pts[-1]
    angle = math.atan2(yb - ya, xb - xa)
    pointe = [(xb + 2 * math.cos(angle), yb + 2 * math.sin(angle))] + [
        (xb - 7 * math.cos(angle + s * 0.5), yb - 7 * math.sin(angle + s * 0.5)) for s in (1, -1)]
    d.polygon([(x * F, y * F) for x, y in pointe], fill=couleur)


def _graphique(d, x, y, hausse):
    """Petit graphique en barres avec une flèche verte (hausse ou baisse), comme sur le modèle."""
    couleurs = ["#E8590C", "#FD7E14", "#FFA94D", "#FCC419"]
    hauteurs = [11, 16, 23, 30]
    if not hausse:
        couleurs, hauteurs = couleurs[::-1], hauteurs[::-1]
    bas = y + 38
    for i, (c, h) in enumerate(zip(couleurs, hauteurs)):
        bx = x + 3 + i * 8.5
        d.rectangle([bx * F, (bas - h) * F, (bx + 6.5) * F, bas * F], fill=c)
    d.line([(x * F, (bas + 1.5) * F), ((x + 40) * F, (bas + 1.5) * F)], fill="#343A40", width=round(1.6 * F))
    if hausse:
        _fleche(d, (x + 1, y + 22), (x + 26, y + 18), (x + 38, y + 1), "#37B24D")
    else:
        _fleche(d, (x + 40, y + 20), (x + 14, y + 18), (x + 2, y + 1), "#37B24D")


def _top5(img, d, x0, y0, perfs, lignes=5):
    """Cadre « TOP 5 Perf » du modèle ; lignes = 10 ou 15 quand la place le permet (Paris + jeunes, 28/11)."""
    x1, y1 = x0 + 416, y0 + hauteur_top(lignes)
    d.rounded_rectangle([x0 * F, y0 * F, x1 * F, y1 * F], radius=22 * F, fill=JAUNE)
    # Trait « à main levée » d'Excalidraw : deux contours bronze presque superposés
    for dx, dy, l in ((0, 0, 2.2), (0.8, 1.6, 1.4)):
        d.rounded_rectangle([(x0 + dx) * F, (y0 + dy) * F, (x1 + dx) * F, (y1 + dy) * F], radius=22 * F,
                            outline=BRONZE, width=round(l * F))
    _graphique(d, x0 + 59, y0 + 11, True)
    _graphique(d, x0 + 311, y0 + 11, False)
    ecrire(d, (x0 + x1) / 2, y0 + 29, f"TOP {lignes} Perf", MAIN, 19.5, ORANGE, "mm")
    if not perfs:
        ecrire(d, (x0 + x1) / 2, y0 + 120, "Pas de perf cette journée", MAIN, 19.5, NOIR, "mm")
    for i, (nom, battus, ecart) in enumerate(perfs[:lignes]):
        base = y0 + 99 + i * 23.75
        texte = f"{i + 1}. {nom} bat {_liste(battus)}"
        ecrire(d, x0 + 14, base, texte, MAIN, ajuste(texte, MAIN, 19.5, 325), NOIR)
        ecrire(d, x0 + 345, base, f"+{ecart}", MAIN, 19.5, NOIR)


def _perfs_vertical(img, d):
    """« * Perfs » écrit de bas en haut à droite de la photo."""
    t = police(MAIN, 37)
    l, h = round(t.getlength("Perfs")) + 8 * F, round(52 * F)
    calque = Image.new("L", (l, h), 0)
    ImageDraw.Draw(calque).text((4 * F, h / 2), "Perfs", font=t, fill=255, anchor="lm")
    calque = calque.rotate(90, expand=True)
    x, y = round(1215 * F - calque.width / 2), round(382 * F - calque.height / 2)
    img.paste(Image.new("RGB", calque.size, ORANGE), (x, y), calque)
    _asterisque(d, 1214, 451, 9.5)


def _image_nommee(fichier, debut):
    """photo_J1.jpg, photo_J1-equipe.png... pour la J1, mais pas photo_J10.jpg."""
    return (fichier.suffix.lower() in EXTENSIONS_IMAGES
            and re.fullmatch(re.escape(debut) + r"(\D.*)?", fichier.stem.lower()) is not None)


def images_du_recap(dossier_import, journee):
    """Fichiers du dossier import utilisés par les images de la journée : photo et logos du
    récapitulatif, logo du club des classements des poules."""
    if not dossier_import or not Path(dossier_import).is_dir():
        return []
    debuts = (f"photo_j{journee}", *(f"logo_{c}" for c in LOGOS), "logo_club")
    return [f for f in sorted(Path(dossier_import).iterdir()) if f.is_file() and any(_image_nommee(f, d) for d in debuts)]


def _image_du_dossier(dossier_import, debut):
    if not dossier_import or not Path(dossier_import).is_dir():
        return None
    for f in sorted(Path(dossier_import).iterdir()):
        if f.is_file() and _image_nommee(f, debut):
            try:
                with Image.open(f) as im:
                    return ImageOps.exif_transpose(im).convert("RGBA")  # photo de téléphone : bien orientée
            except OSError:
                print(f"  ! image illisible : {f.name}")
    return None


def _photo(img, d, dossier_import, journee, debut="photo_j"):
    x0, y0, x1, y1 = PHOTO
    photo = _image_du_dossier(dossier_import, f"{debut}{journee}")
    if photo:
        cadre = ImageOps.fit(photo.convert("RGB"), ((x1 - x0) * F, (y1 - y0) * F), Image.LANCZOS, centering=(0.5, 0.4))
        img.paste(cadre, (x0 * F, y0 * F))
    else:
        d.rectangle([x0 * F, y0 * F, x1 * F, y1 * F], fill="#F1F3F5")
        ecrire(d, (x0 + x1) / 2, (y0 + y1) / 2 - 6, "Photo de l'équipe", MAIN, 30, "#ADB5BD", "ms")
        ecrire(d, (x0 + x1) / 2, (y0 + y1) / 2 + 28, f"(import\\{debut.replace('_j', '_J')}{journee}.jpg, ou à coller ici)", MAIN, 19, "#ADB5BD", "ms")
    for cote, (cx, cy, lmax, hmax) in LOGOS.items():
        logo = _image_du_dossier(dossier_import, f"logo_{cote}")
        if not logo:
            continue
        logo.thumbnail((lmax * F, hmax * F), Image.LANCZOS)
        x = cx * F if cote == "gauche" else cx * F - logo.width
        img.paste(logo, (x, cy * F), logo)
    return bool(photo)


def image_recap(donnees, dossier_import, dossier, prefixe="", jeunes=None):
    """Écrit recap_J<n>.png pour la dernière journée. Renvoie [(chemin, titre)]. Championnat de Paris
    (prefixe « paris_ », donnees["championnat"] = "paris") : paris_recap_J<n>.png, titre « CHAMPIONNAT DE
    PARIS », joueurs rangés par groupe, photo import/photo_paris_J<n>.jpg. `jeunes` (données du championnat des
    jeunes, 28/11) : ses équipes de la dernière journée jouée sont ajoutées à l'image de Paris (bandeaux bleus
    « Vaires 1 (−15 ans) », titre « CHAMPIONNAT DE PARIS + CHAMPIONNAT JEUNES ») : Paris à gauche, les jeunes sous
    la photo, les perfs des deux championnats à droite (top 15 quand la place le permet)."""
    paris = (donnees.get("championnat") or "france") != "france"
    for f in Path(dossier).glob(f"{prefixe}recap_*.png"):
        f.unlink()
    if not donnees.get("journees"):
        return []
    j = donnees["journees"][-1]
    du_jour = [r for r in donnees["rencontres"] if r["journee"] == j]
    if paris and not any(r["parties"] for r in du_jour):
        return []  # Paris, jeunes : pas d'image tant qu'aucune feuille de la journée n'est saisie
    equipes = equipes_de_la_journee(du_jour)
    if not equipes:
        return []
    avec_jeunes, j_jeunes = [], None
    if paris and jeunes and jeunes.get("journees"):
        j_jeunes = jeunes["journees"][-1]
        du_jour_jeunes = [r for r in jeunes["rencontres"] if r["journee"] == j_jeunes]
        for r, e in zip(du_jour_jeunes, equipes_de_la_journee(du_jour_jeunes)):
            avec_jeunes.append({**e, "titre": titre_jeunes(r), "bandeau": BLEU})
    tous = {jj["licence"]: jj for e in equipes + avec_jeunes for jj in e["joueurs"]}
    noms = noms_affiches(list(tous.values()), lire_surnoms(dossier_import))
    if avec_jeunes:
        places, place_top, places_jeunes, hauteur, lignes_top = _emplacements_paris_jeunes(
            [hauteur_bloc(e) for e in equipes], [hauteur_bloc(e) for e in avec_jeunes])
        places = places + [place_top]
    elif paris:
        places, hauteur = _emplacements_variables([hauteur_bloc(e) for e in equipes])
    else:
        places = _emplacements(len(equipes) + 1)  # + le top 5
        hauteur = max(HAUTEUR_MIN, places[-1][1] + PAS_RANGEE)
    img = Image.new("RGB", (LARGEUR * F, hauteur * F), "white")
    d = ImageDraw.Draw(img)
    titre = {"paris": "CHAMPIONNAT DE PARIS", "jeunes": "CHAMPIONNAT DES JEUNES"}.get(donnees.get("championnat"), "CHAMPIONNAT DE FRANCE")
    if avec_jeunes:  # « CHAMPIONNAT DE PARIS + CHAMPIONNAT JEUNES » (rouge, puis bleu comme les bandeaux des jeunes)
        suite = " + CHAMPIONNAT JEUNES"
        taille = ajuste(titre + suite, TITRE, 34.5, 770)
        ecrire(d, 19, 42, titre, TITRE, taille, ROUGE)
        ecrire(d, 19 + largeur(titre, TITRE, taille), 42, suite, TITRE, taille, BLEU)
        jour = f"Journée {j} - {donnees['saison']}" if j == j_jeunes else f"Paris J{j} · Jeunes J{j_jeunes} - {donnees['saison']}"
        place = PHOTO[2] - (19 + largeur(titre + suite, TITRE, taille)) - 24  # sans toucher le titre
        ecrire(d, PHOTO[2], 38, jour, MAIN, ajuste(jour, MAIN, 26.5, place), NOIR, "rs")
    else:
        ecrire(d, 19, 42, titre, TITRE, 34.5, ROUGE)
        ecrire(d, 454, 38, f"Journée {j} - {donnees['saison']}" if paris else f"Journée {j} - Phase {donnees['phase']} - {donnees['saison']}",
               MAIN, 26.5, NOIR)
    avec_photo = _photo(img, d, dossier_import, j, f"photo_{prefixe}j" if paris else "photo_j")
    _perfs_vertical(img, d)
    for (x, y), equipe in zip(places, equipes):
        _bloc(d, x, y, equipe, noms)
    for (x, y), equipe in zip(places_jeunes if avec_jeunes else [], avec_jeunes):
        _bloc(d, x, y, equipe, noms)
    x, y = places[-1]
    if avec_jeunes:  # top 15 quand la place le permet (demande du club : plus de joueurs à l'honneur)
        _top5(img, d, x + 1, y - 1, top_perfs(equipes + avec_jeunes, noms, lignes_top), lignes_top)
    else:
        _top5(img, d, x + 1, y - 1, top_perfs(equipes, noms))
    chemin = Path(dossier) / f"{prefixe}recap_J{j}.png"
    chemin.parent.mkdir(parents=True, exist_ok=True)
    img.resize((LARGEUR, hauteur), Image.LANCZOS).save(chemin, optimize=True)
    court = "Paris + jeunes · " if avec_jeunes else {"paris": "Paris · ", "jeunes": "Jeunes · "}.get(donnees.get("championnat"), "")
    return [(chemin, court + f"Récapitulatif J{j}" + ("" if avec_photo else " (photo à ajouter)"))]

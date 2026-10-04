"""Compléments lus sur pingpocket.fr : effectifs complets des clubs (catégories, licences
loisir, renouvellements), adresses des salles et historique des classements.

Ces données ne sont pas publiques dans l'API de la FFTT. Pingpocket peut être indisponible ou
bloquer les requêtes automatiques : l'outil fonctionne alors sans ces compléments.
"""

import re

from bs4 import BeautifulSoup

CATEGORIES = {"Poussin": "P", "Benjamin": "B", "Minime": "M", "Cadet": "C", "Junior": "J",
              "Senior": "S", "Sénior": "S", "Vétéran": "V"}


# Petits utilitaires

def _soupe(html):
    return BeautifulSoup(html, "html.parser")


def _texte(el):
    return " ".join(el.get_text(" ", strip=True).split()) if el else ""


def _entier(txt):
    txt = (txt or "").strip()
    return int(txt) if re.fullmatch(r"-?\d+", txt) else None


def separer_nom(complet):
    """'SOARES GARCIA Ricardo Andre' -> ('SOARES GARCIA', 'Ricardo Andre')."""
    mots = complet.split()
    i = 0
    while i < len(mots) - 1 and mots[i] == mots[i].upper():
        i += 1
    return " ".join(mots[:i]) or complet, " ".join(mots[i:])


def categorie_courte(txt):
    """'Vétéran 45' -> 'V45', 'Minime 1' -> 'M1', 'Senior' -> 'S'."""
    m = re.match(r"(\w+)\s*(\d*)", txt or "")
    if m and m[1] in CATEGORIES:
        return CATEGORIES[m[1]] + m[2]
    return txt


def lire_liste_licencies(html):
    """Liste des licenciés d'un club (triée par classement, catégorie, état de licence...).

    Renvoie [(titre de section, [{licence, nom, prenom, sexe, compteur}, ...]), ...].
    """
    soup = _soupe(html)
    sections, courante = [], None
    for li in soup.select("ul.edgetoedge li"):
        classes = li.get("class") or []
        if "sep" in classes:
            courante = (_texte(li.find("p")), [])
            sections.append(courante)
        elif "arrow" in classes:
            a = li.find("a", href=True)
            m = re.search(r"/licencies/(\d+)", a["href"]) if a else None
            if not m:
                continue
            if courante is None:
                courante = ("", [])
                sections.append(courante)
            nom, prenom = separer_nom(_texte(a.select_one(".labels p")))
            compteur = a.select_one("small.counter")
            courante[1].append({
                "licence": m[1], "nom": nom, "prenom": prenom,
                "sexe": "F" if a.select_one("i.fa-female") else "M",
                "compteur": _texte(compteur),
            })
    return sections


def lire_salle(html):
    """Page coordonnées d'un club -> {nom, adresse, cp, ville, carte} ou None."""
    soup = _soupe(html)
    titre = next((h for h in soup.find_all("h2") if _texte(h).startswith("Salle")), None)
    ul = titre.find_next_sibling("ul") if titre else None
    p = ul.find("p") if ul else None
    if not p:
        return None
    lignes = [" ".join(s.split()) for s in p.stripped_strings]
    salle = {"nom": None, "adresse": None, "cp": None, "ville": None, "carte": None}
    if lignes and (m := re.match(r"(\d{5})\s+(.*)", lignes[-1])):
        salle["cp"], salle["ville"] = m[1], m[2].strip()
        lignes = lignes[:-1]
    if len(lignes) >= 2:
        salle["nom"], salle["adresse"] = lignes[0], " ".join(lignes[1:])
    elif lignes:
        salle["adresse"] = lignes[0]
    carte = ul.select_one('a[href*="maps"]')
    salle["carte"] = carte["href"] if carte else None
    return salle


def lire_historique(html):
    """Graphique 'historique classement' -> [(annee, mois, points), ...] (mois de 1 à 12)."""
    points = re.findall(r"x:\s*Date\.UTC\((\d{4}),\s*(\d{1,2}),\s*\d+\)\s*,\s*y:\s*([\d.]+)", html)
    return [(int(a), int(m) + 1, round(float(y))) for a, m, y in points]


def resume_historique(points):
    """Points officiels actuels et meilleur classement (points de début de phase : janvier et juillet)."""
    officiels = [p for p in points if p[1] in (1, 7)] or points
    if not officiels:
        return None, None
    meilleur = max(officiels, key=lambda p: (p[2], p[0], p[1]))
    return officiels[-1][2], {"points": meilleur[2], "annee": str(meilleur[0])}


# ---------------------------------------------------------------------------
# Récupération complète
# ---------------------------------------------------------------------------


def effectif(pages, liens):
    """Fusionne les listes de licenciés d'un club (catégories, classements, état des licences).

    Les licences loisir (affichées 'L' à la place des points) sont écartées.
    """
    joueurs = {}
    for titre, liste in lire_liste_licencies(pages.get(liens["categories"]) or ""):
        for j in liste:
            joueurs[j["licence"]] = {
                "id": j["licence"], "licence": j["licence"], "nom": j["nom"], "prenom": j["prenom"],
                "sexe": j["sexe"], "categorie": categorie_courte(titre), "categorie_long": titre,
                "loisir": j["compteur"] == "L", "classement": None, "points": None,
                "points_mensuels": _entier(j["compteur"]), "meilleur": None, "renouvele": True,
            }
    for titre, liste in lire_liste_licencies(pages.get(liens["classements"]) or ""):
        for j in liste:
            if j["licence"] in joueurs:
                joueurs[j["licence"]]["classement"] = _entier(titre)
                joueurs[j["licence"]]["points_mensuels"] = joueurs[j["licence"]]["points_mensuels"] or _entier(j["compteur"])
    for titre, liste in lire_liste_licencies(pages.get(liens["etat"]) or ""):
        for j in liste:
            if j["licence"] in joueurs:
                joueurs[j["licence"]]["renouvele"] = not titre.lower().startswith("licences non")
    return [j for j in joueurs.values() if not j.pop("loisir")]

"""Page « Individuels » (/indivs/) : les poules des compétitions individuelles (critérium fédéral...)
où jouent des joueurs de Vaires, avec la forme de chacun de leurs adversaires.

Les poules viennent des convocations (PDF, captures) envoyées par les organisateurs : elles sont
recopiées une fois (licence, nom, prénom, points, club, catégorie de chaque joueur) dans
ressources/indivs.json.chiffre, chiffré avec la clé de l'espace club (dépôt public, joueurs mineurs).
À chaque mise à jour, l'outil lit dans l'API de la FFTT les parties de la phase de chaque joueur des
poules (une requête par joueur, gardée un jour) : victoires, défaites, points gagnés ou perdus et
compétitions jouées (même calcul que la forme des adversaires en championnat, voir virtuel.py).

La page est publiée chiffrée avec le mot de passe du club, à son adresse : /indivs/ (comme /club/).

Remplacer les poules (nouveau tour) : écrire un fichier JSON de même forme (voir exemple() ou
`exporter`), puis, avec le mot de passe du club dans MOT_DE_PASSE_CLUB (sinon il est demandé) :

    python -m ttvaires.indivs importer poules.json    # chiffre dans ressources/indivs.json.chiffre
    python -m ttvaires.indivs exporter poules.json    # l'inverse, pour relire ou corriger
"""

import argparse
import getpass
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

from . import fftt, publier
from .virtuel import forme_joueurs

RACINE = Path(__file__).resolve().parent.parent
FICHIER = RACINE / "ressources" / "indivs.json.chiffre"
CLUB_VAIRES = "CVTT VAIRES"
PUBLICS = {"adultes": "Adultes", "jeunes": "Jeunes", "feminines": "Féminines"}


def lire(mot_de_passe_club, fichier=None):
    """Poules (dict {maj, poules}) ou None si le fichier est absent."""
    fichier = Path(fichier or FICHIER)
    if not fichier.exists():
        return None
    return json.loads(publier.dechiffrer(fichier.read_bytes(), publier.cle(mot_de_passe_club)).decode("utf-8"))


def ecrire(donnees, mot_de_passe_club, fichier=None):
    from .netlify import chiffrer_stable  # (netlify importe ressources, qui importe publier)

    fichier = Path(fichier or FICHIER)
    fichier.parent.mkdir(parents=True, exist_ok=True)
    clair = json.dumps(donnees, ensure_ascii=False, indent=1).encode("utf-8")
    fichier.write_bytes(chiffrer_stable(clair, publier.cle(mot_de_passe_club)))
    return fichier


def _simple(texte):
    t = unicodedata.normalize("NFKD", texte or "").encode("ascii", "ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z]", "", t)


def nom_coherent(nom_liste, nom_api):
    """Le nom donné par l'API pour cette licence est-il celui de la convocation ? (noms composés,
    accents et tirets tolérés). None : pas de partie lue, rien à comparer."""
    if not nom_api:
        return None
    a, b = _simple(nom_liste), _simple(nom_api)
    return bool(a and b and (a in b or b in a))


def officiels(joueur):
    """Points de la convocation, sinon ceux lus sur ses parties."""
    return joueur["points"] if joueur.get("points") is not None else (joueur.get("forme") or {}).get("officiels")


def virtuels(joueur):
    """Points officiels + points gagnés ou perdus depuis le début de la phase (sans partie : les officiels)."""
    f = joueur.get("forme") or {}
    return f["virtuels"] if f.get("virtuels") is not None else officiels(joueur)


def par_virtuels(joueurs):
    return sorted(joueurs, key=lambda j: (-(virtuels(j) if virtuels(j) is not None else -1), -(officiels(j) or 0)))


def niveau(adv, moi):
    """Niveau d'un adversaire pour un joueur de Vaires (comme la page) : « plus fort » (au moins 50
    points virtuels de plus), « à surveiller » (à moins de 50 points, ou plus faible mais à +30 points
    sur la phase), « à sa portée ». None sans points."""
    a, m = virtuels(adv), virtuels(moi)
    if a is None or m is None:
        return None
    if a - m >= 50:
        return "plus fort"
    if a - m > -50 or ((adv.get("forme") or {}).get("points") or 0) >= 30:
        return "à surveiller"
    return "à sa portée"


def de_vaires(joueur):
    return _simple(joueur.get("club")) == _simple(CLUB_VAIRES) or joueur.get("numero_club") == "08770250"


def recuperer(client, poules, aujourdhui=None):
    """Données de la page : chaque poule où joue un joueur de Vaires, avec la forme de chaque joueur."""
    aujourdhui = aujourdhui or date.today()
    debut, fin = fftt.bornes_phase(aujourdhui)
    fin = min(fin, aujourdhui.isoformat())
    retenues = [p for p in poules["poules"] if any(de_vaires(j) for j in p["joueurs"])]
    licences = sorted({j["licence"] for p in retenues for j in p["joueurs"] if j.get("licence")})
    print(f"Individuels : {len(retenues)} poules avec un joueur de Vaires, {len(licences)} joueurs (API FFTT)", flush=True)
    formes = forme_joueurs(client, licences, {}, debut, fin) if licences else {}
    sortie, douteuses = [], []
    for p in retenues:
        joueurs = []
        for j in p["joueurs"]:
            f = formes.get(j.get("licence"))
            coherent = nom_coherent(j["nom"], (f or {}).get("nom"))
            if coherent is False:
                douteuses.append(f"{j['nom']} {j['prenom']} ({j['licence']} : {f['nom']} pour l'API)")
            joueurs.append({**j, "vaires": de_vaires(j), "forme": f, "licence_douteuse": coherent is False})
        sortie.append({**{k: v for k, v in p.items() if k != "joueurs"}, "joueurs": joueurs})
    for d in douteuses:
        print(f"  ! licence à vérifier : {d}", flush=True)
    muets = sum(1 for lic in licences if formes.get(lic) is None)
    return {
        "genere_le": datetime.now().isoformat(timespec="minutes"), "debut": debut, "maj_poules": poules.get("maj"),
        "publics": PUBLICS, "poules": sortie,
        "controle": {"joueurs": len(licences), "sans_reponse": muets, "licences_douteuses": douteuses},
    }


def resume(donnees):
    c = donnees["controle"]
    vaires = sum(1 for p in donnees["poules"] for j in p["joueurs"] if j["vaires"])
    texte = f"{len(donnees['poules'])} poules, {vaires} joueurs de Vaires, {c['joueurs']} joueurs lus"
    if c["sans_reponse"]:
        texte += f", {c['sans_reponse']} sans partie lue"
    if c["licences_douteuses"]:
        texte += f", {len(c['licences_douteuses'])} licence(s) à vérifier"
    return texte


def exemple():
    return {"maj": "2026-11-11", "poules": [{
        "id": "p1", "public": "adultes", "competition": "Critérium fédéral départemental 77 · Tour 2",
        "titre": "D2 · Élite · groupe 2", "date": "2026-11-15", "horaire": "pointage 8 h 30, début 9 h",
        "lieu": "COSEC, rue de l'Écluse, 77360 Vaires-sur-Marne",
        "joueurs": [{"licence": "7700000", "nom": "NOM", "prenom": "Prénom", "points": 1032, "club": "CVTT VAIRES",
                     "numero_club": "08770250", "cat": "V50"}]}]}


def main(arguments=None):
    p = argparse.ArgumentParser(prog="python -m ttvaires.indivs", description="Poules des compétitions individuelles")
    sous = p.add_subparsers(dest="action", required=True)
    sous.add_parser("importer", help="chiffre un fichier JSON de poules dans ressources/").add_argument("json", type=Path)
    sous.add_parser("exporter", help="déchiffre les poules dans un fichier JSON").add_argument("json", type=Path)
    sous.add_parser("exemple", help="affiche un exemple de fichier JSON")
    args = p.parse_args(arguments)
    if args.action == "exemple":
        print(json.dumps(exemple(), ensure_ascii=False, indent=1))
        return 0
    mdp = os.environ.get("MOT_DE_PASSE_CLUB") or getpass.getpass("Mot de passe de l'espace club : ")
    if args.action == "importer":
        donnees = json.loads(args.json.read_text(encoding="utf-8"))
        for poule in donnees["poules"]:
            if poule.get("public") not in PUBLICS:
                raise SystemExit(f"poule {poule.get('titre')} : public inconnu ({poule.get('public')}), attendu : {', '.join(PUBLICS)}")
        ecrire(donnees, mdp)
        print(f"Poules chiffrées dans {FICHIER.relative_to(RACINE)} ({len(donnees['poules'])} poules). À envoyer sur GitHub (commit).")
    else:
        donnees = lire(mdp)
        if donnees is None:
            raise SystemExit("aucune poule enregistrée")
        args.json.write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Poules écrites dans {args.json} (en clair : ne pas les envoyer sur GitHub).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

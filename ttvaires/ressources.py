"""Rubriques permanentes de l'espace club, après les archives : Matériel, Prépa mentale...

Ce ne sont pas des documents produits par l'outil mais des documents fournis (page HTML, PDF),
publiés tels quels. Ils sont dans le dossier ressources/ du dépôt, chiffrés avec la clé de
l'espace club (mot de passe du club) : le dépôt est public, eux ne le sont pas. La liste des
rubriques et de leurs documents, dans l'ordre d'affichage, est dans ressources/ressources.json
(titres et descriptions seulement).

Ajouter ou remplacer un document (sur un PC, avec le mot de passe du club) :

    python -m ttvaires.ressources ajouter "Prépa mentale" chemin/guide.pdf --titre "Guide du joueur"

puis l'envoyer sur GitHub (commit du dossier ressources/) : la mise à jour suivante le publie.
Le mot de passe est lu dans la variable MOT_DE_PASSE_CLUB, sinon demandé.

Si le mot de passe du club change, ces documents ne s'ouvrent plus avec la nouvelle clé : la mise à
jour le signale et ne les publie pas ; il faut les ajouter de nouveau.
"""

import argparse
import getpass
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

from . import publier

RACINE = Path(__file__).resolve().parent.parent
DOSSIER = RACINE / "ressources"
LISTE = "ressources.json"
TYPES = {".html": "page", ".htm": "page", ".pdf": "pdf"}


def lire(dossier=None):
    """{"rubriques": [{"nom", "description", "documents": [{"fichier", "titre", "description"}]}]}"""
    fichier = Path(dossier or DOSSIER) / LISTE
    if not fichier.exists():
        return {"rubriques": []}
    return json.loads(fichier.read_text(encoding="utf-8"))


def _ecrire(liste, dossier):
    Path(dossier).mkdir(parents=True, exist_ok=True)
    (Path(dossier) / LISTE).write_text(json.dumps(liste, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def nom_de_fichier(chemin):
    """« Guide du joueur.pdf » -> « guide-du-joueur.pdf » (sans accent ni espace)."""
    chemin = Path(chemin)
    base = unicodedata.normalize("NFKD", chemin.stem).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "document"
    return base + chemin.suffix.lower()


def ajouter(rubrique, chemin, mot_de_passe_club, titre=None, description="", fichier=None, dossier=None):
    """Chiffre `chemin` avec la clé du club dans `dossier` et l'inscrit dans la rubrique (créée au
    besoin, à la fin). Un document du même nom est remplacé. Renvoie le nom du fichier publié."""
    from .netlify import chiffrer_stable  # (netlify importe ce module)

    chemin, dossier = Path(chemin), Path(dossier or DOSSIER)
    if chemin.suffix.lower() not in TYPES:
        raise ValueError(f"type de document non pris en charge : {chemin.suffix} (pages .html et PDF seulement)")
    if not mot_de_passe_club:
        raise ValueError("mot de passe du club manquant")
    fichier = fichier or nom_de_fichier(chemin)
    contenu = chemin.read_bytes()
    Path(dossier).mkdir(parents=True, exist_ok=True)
    (Path(dossier) / f"{fichier}.chiffre").write_bytes(chiffrer_stable(contenu, publier.cle(mot_de_passe_club)))
    liste = lire(dossier)
    for r in liste["rubriques"]:
        r["documents"] = [d for d in r["documents"] if d["fichier"] != fichier]
    cible = next((r for r in liste["rubriques"] if r["nom"] == rubrique), None)
    if cible is None:
        cible = {"nom": rubrique, "description": "", "documents": []}
        liste["rubriques"].append(cible)
    cible["documents"].append({"fichier": fichier, "titre": titre or chemin.stem, "description": description,
                               "taille": len(contenu)})
    liste["rubriques"] = [r for r in liste["rubriques"] if r["documents"]]
    _ecrire(liste, dossier)
    return fichier


def publier_dans(club, cle_club, dossier=None):
    """Copie les documents dans club/ressources/ (déjà chiffrés avec la clé du club) et renvoie les
    rubriques pour la page de l'espace club. Un document qui ne s'ouvre pas avec la clé du club
    (mot de passe changé depuis) ou absent est signalé et laissé de côté."""
    rubriques, dossier = [], Path(dossier or DOSSIER)
    for r in lire(dossier)["rubriques"]:
        documents = []
        for d in r["documents"]:
            source = Path(dossier) / f"{d['fichier']}.chiffre"
            try:
                publier.dechiffrer(source.read_bytes(), cle_club)
            except FileNotFoundError:
                print(f"  ! rubrique « {r['nom']} » : {d['fichier']} introuvable dans ressources/", flush=True)
                continue
            except Exception:  # étiquette AES invalide : autre clé
                print(f"  ! rubrique « {r['nom']} » : {d['fichier']} ne s'ouvre pas avec le mot de passe du club "
                      "(changé depuis ?) : à ajouter de nouveau (python -m ttvaires.ressources)", flush=True)
                continue
            cible = Path(club) / "ressources" / f"{d['fichier']}.chiffre"
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_bytes(source.read_bytes())
            documents.append({"fichier": d["fichier"], "chemin": f"ressources/{d['fichier']}.chiffre",
                              "type": TYPES.get(Path(d["fichier"]).suffix.lower(), "page"), "titre": d["titre"],
                              "description": d.get("description", ""), "taille": d.get("taille")})
        if documents:
            rubriques.append({"nom": r["nom"], "description": r.get("description", ""), "documents": documents})
    return rubriques


def main(arguments=None):
    p = argparse.ArgumentParser(prog="python -m ttvaires.ressources", description="Documents des rubriques de l'espace club")
    sous = p.add_subparsers(dest="action", required=True)
    a = sous.add_parser("ajouter", help="ajouter ou remplacer un document (page .html ou PDF)")
    a.add_argument("rubrique", help="nom de la rubrique, par exemple « Prépa mentale »")
    a.add_argument("chemin", type=Path)
    a.add_argument("--titre")
    a.add_argument("--description", default="")
    a.add_argument("--fichier", help="nom publié (par défaut : celui du fichier, sans accent ni espace)")
    sous.add_parser("liste", help="afficher les rubriques et leurs documents")
    args = p.parse_args(arguments)
    if args.action == "liste":
        for r in lire()["rubriques"]:
            print(r["nom"])
            for d in r["documents"]:
                print(f"  {d['fichier']} : {d['titre']}")
        return 0
    mdp = os.environ.get("MOT_DE_PASSE_CLUB") or getpass.getpass("Mot de passe de l'espace club : ")
    fichier = ajouter(args.rubrique, args.chemin, mdp, args.titre, args.description, args.fichier)
    print(f"Ajouté : ressources/{fichier}.chiffre (rubrique « {args.rubrique} »). À envoyer sur GitHub (commit).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

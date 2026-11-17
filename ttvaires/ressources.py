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

Espace à mot de passe à part (ex. /lundi/, page personnelle : demandé le 17/11/2026). Son entrée de
ressources.json nomme le secret GitHub qui le protège (« acces » : MOT_DE_PASSE_LUNDI) ; le mot de
passe n'est jamais dans le dépôt ni connu de qui y dépose une page. La page est déposée « scellée »
(fichier .scelle) avec la clé publique de l'espace (« cle_publique ») : n'importe qui peut en déposer
une nouvelle version, seule la mise à jour en ligne, qui a le secret, sait l'ouvrir (la clé privée est
tirée du mot de passe ; le mot de passe du club ne l'ouvre pas). La mise à jour publie la clé publique
à <adresse>/cle-publique.txt. Sans le secret, l'espace n'est pas publié du tout.

    python -m ttvaires.ressources acces lundi MOT_DE_PASSE_LUNDI            (une fois)
    python -m ttvaires.ressources cle lundi <clé de …/lundi/cle-publique.txt>   (une fois)
    python -m ttvaires.ressources espace lundi chemin/page.html             (chaque nouvelle version)
"""

import argparse
import base64
import getpass
import gzip
import hashlib
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
TYPES = {".html": "page", ".htm": "page", ".pdf": "pdf", ".png": "image", ".jpg": "image", ".jpeg": "image"}
STOCKAGE_CLUB = "cvtt-vaires-cle-club"  # clé gardée par l'espace club : la même ouvre les espaces (voir publier_espaces)
SCELLE = b"SCEL1"  # en-tête d'une page scellée (espace à mot de passe à part)
CONSIGNE_A_PART = "Page privée : entre son mot de passe (ce n'est pas celui du club)."


def stockage_a_part(chemin):
    """Où le navigateur garde la clé d'un espace à mot de passe à part. Le nom commence par celui de
    l'espace club : l'application Android reconnaît les pages du club et de /lundi/ à ce repère
    (android/.../Principale.java, TEMOIN_CLUB), mais la clé gardée est distincte."""
    return f"{STOCKAGE_CLUB}-{chemin}"


def _cle_privee(mot_de_passe, chemin):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    graine = hashlib.sha256(b"cvtt-vaires-scellement\0" + chemin.encode("utf-8") + b"\0" + publier.cle(mot_de_passe)).digest()
    return X25519PrivateKey.from_private_bytes(graine)


def cle_publique(mot_de_passe, chemin):
    """Clé publique (base64) d'un espace à mot de passe à part, tirée de son mot de passe."""
    from cryptography.hazmat.primitives import serialization

    brut = _cle_privee(mot_de_passe, chemin).public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(brut).decode("ascii")


def _cle_partagee(secret):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"cvtt-vaires espace scelle").derive(secret)


def sceller(donnees, cle_publique_b64):
    """Page chiffrée pour la seule clé privée de l'espace (X25519 éphémère + AES-GCM) :
    SCELLE + clé éphémère (32 octets) + vecteur (12) + chiffré."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    ephemere = X25519PrivateKey.generate()
    cle = _cle_partagee(ephemere.exchange(X25519PublicKey.from_public_bytes(base64.b64decode(cle_publique_b64))))
    iv = os.urandom(12)
    return (SCELLE + ephemere.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
            + iv + AESGCM(cle).encrypt(iv, gzip.compress(donnees, mtime=0), None))


def desceller(brut, mot_de_passe, chemin):
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    if not brut.startswith(SCELLE):
        raise ValueError("ce n'est pas une page scellée")
    n = len(SCELLE)
    cle = _cle_partagee(_cle_privee(mot_de_passe, chemin).exchange(X25519PublicKey.from_public_bytes(brut[n:n + 32])))
    return gzip.decompress(AESGCM(cle).decrypt(brut[n + 32:n + 44], brut[n + 44:], None))


def lire(dossier=None):
    """{"rubriques": [{"nom", "description", "documents": [{"fichier", "titre", "description"}]}],
        "espaces": [{"chemin", "fichier", "titre"}]}"""
    fichier = Path(dossier or DOSSIER) / LISTE
    liste = json.loads(fichier.read_text(encoding="utf-8")) if fichier.exists() else {}
    liste.setdefault("rubriques", [])
    liste.setdefault("espaces", [])
    return liste


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
        raise ValueError(f"type de document non pris en charge : {chemin.suffix} (pages .html, PDF et images seulement)")
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


def _chemin_espace(chemin_url):
    chemin_url = chemin_url.strip("/").lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", chemin_url) or chemin_url in ("club", "gg", "stats", "archives"):
        raise ValueError(f"adresse d'espace invalide ou réservée : /{chemin_url}/")
    return chemin_url


def ajouter_espace(chemin_url, page, mot_de_passe_club, titre=None, dossier=None):
    """Espace protégé à une adresse à lui (ex. /lundi/) : une page HTML fournie, affichée telle quelle
    après le mot de passe du club, ou après son mot de passe à part s'il en a un (voir le début du
    module : la page est alors scellée avec sa clé publique, sans mot de passe). Un espace du même
    chemin est remplacé (son mot de passe à part et sa clé publique sont gardés)."""
    from .netlify import chiffrer_stable

    page, dossier = Path(page), Path(dossier or DOSSIER)
    chemin_url = _chemin_espace(chemin_url)
    if page.suffix.lower() not in (".html", ".htm"):
        raise ValueError("un espace est une page .html")
    liste = lire(dossier)
    ancien = next((e for e in liste["espaces"] if e["chemin"] == chemin_url), {})
    fichier = f"espace-{chemin_url}.html"
    dossier.mkdir(parents=True, exist_ok=True)
    entree = {"chemin": chemin_url, "fichier": fichier, "titre": titre or ancien.get("titre") or page.stem,
              "taille": page.stat().st_size}
    if ancien.get("acces"):
        if not ancien.get("cle_publique"):
            raise ValueError(f"/{chemin_url}/ : clé publique inconnue. Lancer une mise à jour avec le secret {ancien['acces']}, "
                             f"puis : python -m ttvaires.ressources cle {chemin_url} <clé de …/{chemin_url}/cle-publique.txt>")
        (dossier / f"{fichier}.scelle").write_bytes(sceller(page.read_bytes(), ancien["cle_publique"]))
        (dossier / f"{fichier}.chiffre").unlink(missing_ok=True)  # ancienne version au mot de passe du club
        entree.update(acces=ancien["acces"], cle_publique=ancien["cle_publique"])
    else:
        if not mot_de_passe_club:
            raise ValueError("mot de passe du club manquant")
        (dossier / f"{fichier}.chiffre").write_bytes(chiffrer_stable(page.read_bytes(), publier.cle(mot_de_passe_club)))
    liste["espaces"] = [e for e in liste["espaces"] if e["chemin"] != chemin_url] + [entree]
    _ecrire(liste, dossier)
    return fichier


def regler_acces(chemin_url, variable, dossier=None):
    """L'espace sera protégé par le mot de passe du secret `variable` (ex. MOT_DE_PASSE_LUNDI), plus
    par celui du club. Sans ce secret, la mise à jour ne le publie pas."""
    chemin_url, dossier = _chemin_espace(chemin_url), Path(dossier or DOSSIER)
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", variable or ""):
        raise ValueError("nom de secret attendu, par exemple MOT_DE_PASSE_LUNDI")
    liste = lire(dossier)
    e = next((e for e in liste["espaces"] if e["chemin"] == chemin_url), None)
    if e is None:
        raise ValueError(f"espace /{chemin_url}/ inconnu")
    e["acces"] = variable
    _ecrire(liste, dossier)


def regler_cle_publique(chemin_url, cle, mot_de_passe_club=None, dossier=None):
    """Enregistre la clé publique de l'espace (publiée par la mise à jour à …/cle-publique.txt) et scelle
    avec elle la version encore chiffrée au mot de passe du club, qui est supprimée."""
    chemin_url, dossier = _chemin_espace(chemin_url), Path(dossier or DOSSIER)
    if len(base64.b64decode(cle, validate=True)) != 32:
        raise ValueError("clé publique invalide (32 octets en base64 attendus)")
    liste = lire(dossier)
    e = next((e for e in liste["espaces"] if e["chemin"] == chemin_url), None)
    if e is None or not e.get("acces"):
        raise ValueError(f"/{chemin_url}/ n'a pas de mot de passe à part (commande acces)")
    e["cle_publique"] = cle
    ancien = dossier / f"{e['fichier']}.chiffre"
    if ancien.exists():
        if not mot_de_passe_club:
            raise ValueError("mot de passe du club nécessaire pour sceller la version actuelle")
        (dossier / f"{e['fichier']}.scelle").write_bytes(sceller(publier.dechiffrer(ancien.read_bytes(), publier.cle(mot_de_passe_club)), cle))
        ancien.unlink()
    _ecrire(liste, dossier)


def _espace_a_part(e, site, cle_club, dossier):
    """Page chiffrée avec le mot de passe à part de l'espace (secret e["acces"]), ou None (pas publiée)."""
    from .netlify import chiffrer_stable

    mot_de_passe = os.environ.get(e["acces"], "")
    if not mot_de_passe:
        print(f"  ! espace /{e['chemin']}/ non publié : secret {e['acces']} absent (mot de passe à part)", flush=True)
        return None
    publique = cle_publique(mot_de_passe, e["chemin"])
    scelle, ancien = dossier / f"{e['fichier']}.scelle", dossier / f"{e['fichier']}.chiffre"
    try:
        if scelle.exists():
            clair = desceller(scelle.read_bytes(), mot_de_passe, e["chemin"])
        elif ancien.exists():  # version au mot de passe du club, en attendant d'être scellée
            clair = publier.dechiffrer(ancien.read_bytes(), cle_club)
        else:
            print(f"  ! espace /{e['chemin']}/ : {e['fichier']} introuvable dans ressources/", flush=True)
            return None
    except Exception:
        print(f"  ! espace /{e['chemin']}/ : la page déposée ne s'ouvre pas avec le secret {e['acces']} (mot de passe "
              "changé depuis ?) : à déposer de nouveau avec la nouvelle clé publique", flush=True)
        clair = None
    (Path(site) / e["chemin"]).mkdir(parents=True, exist_ok=True)
    (Path(site) / e["chemin"] / "cle-publique.txt").write_text(publique + "\n", encoding="ascii")
    if e.get("cle_publique") != publique:
        print(f"  espace /{e['chemin']}/ : clé publique à enregistrer dans le dépôt (python -m ttvaires.ressources cle "
              f"{e['chemin']} …), publiée à {e['chemin']}/cle-publique.txt", flush=True)
    return None if clair is None else chiffrer_stable(clair, publier.cle(mot_de_passe))


def publier_espaces(site, cle_club, dossier=None):
    """Écrit <site>/<chemin>/index.html pour chaque espace : la page de mot de passe (celui du club, ou
    celui de l'espace s'il en a un à part) qui affiche la page fournie, toujours chiffrée. Renvoie les
    chemins publiés."""
    publies, dossier = [], Path(dossier or DOSSIER)
    for e in lire(dossier)["espaces"]:
        if e.get("acces"):
            chiffre = _espace_a_part(e, site, cle_club, dossier)
            if chiffre is not None:
                page = Path(site) / e["chemin"] / "index.html"
                page.write_text(publier.page_verrouillee_chiffree(chiffre, e["titre"], stockage_a_part(e["chemin"]),
                                                                  CONSIGNE_A_PART), encoding="utf-8")
                publies.append(e["chemin"])
            continue
        source = dossier / f"{e['fichier']}.chiffre"
        try:
            chiffre = source.read_bytes()
            publier.dechiffrer(chiffre, cle_club)
        except FileNotFoundError:
            print(f"  ! espace /{e['chemin']}/ : {e['fichier']} introuvable dans ressources/", flush=True)
            continue
        except Exception:
            print(f"  ! espace /{e['chemin']}/ : ne s'ouvre pas avec le mot de passe du club (changé depuis ?) : "
                  "à ajouter de nouveau (python -m ttvaires.ressources espace)", flush=True)
            continue
        page = Path(site) / e["chemin"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(publier.page_verrouillee_chiffree(chiffre, e["titre"], STOCKAGE_CLUB), encoding="utf-8")
        publies.append(e["chemin"])
    return publies


def main(arguments=None):
    p = argparse.ArgumentParser(prog="python -m ttvaires.ressources", description="Documents des rubriques de l'espace club")
    sous = p.add_subparsers(dest="action", required=True)
    a = sous.add_parser("ajouter", help="ajouter ou remplacer un document (page .html ou PDF)")
    a.add_argument("rubrique", help="nom de la rubrique, par exemple « Prépa mentale »")
    a.add_argument("chemin", type=Path)
    a.add_argument("--titre")
    a.add_argument("--description", default="")
    a.add_argument("--fichier", help="nom publié (par défaut : celui du fichier, sans accent ni espace)")
    e = sous.add_parser("espace", help="page .html à une adresse à elle (ex. lundi -> /lundi/), mot de passe du club")
    e.add_argument("adresse", help="par exemple lundi")
    e.add_argument("chemin", type=Path)
    e.add_argument("--titre")
    sous.add_parser("liste", help="afficher les rubriques, leurs documents et les espaces")
    c = sous.add_parser("acces", help="protéger un espace par un mot de passe à part (secret GitHub, ex. MOT_DE_PASSE_LUNDI)")
    c.add_argument("adresse")
    c.add_argument("secret")
    k = sous.add_parser("cle", help="enregistrer la clé publique d'un espace à mot de passe à part (…/cle-publique.txt)")
    k.add_argument("adresse")
    k.add_argument("cle")
    args = p.parse_args(arguments)
    if args.action == "acces":
        regler_acces(args.adresse, args.secret)
        print(f"/{args.adresse.strip('/').lower()}/ : mot de passe du secret {args.secret}. À envoyer sur GitHub (commit).")
        return 0
    if args.action == "cle":
        regler_cle_publique(args.adresse, args.cle, os.environ.get("MOT_DE_PASSE_CLUB"))
        print(f"/{args.adresse.strip('/').lower()}/ : clé publique enregistrée. À envoyer sur GitHub (commit).")
        return 0
    if args.action == "liste":
        liste = lire()
        for r in liste["rubriques"]:
            print(r["nom"])
            for d in r["documents"]:
                print(f"  {d['fichier']} : {d['titre']}")
        for x in liste["espaces"]:
            print(f"/{x['chemin']}/ : {x['titre']}" + (f" (mot de passe à part : {x['acces']})" if x.get("acces") else ""))
        return 0
    a_part = args.action == "espace" and next((x for x in lire()["espaces"] if x["chemin"] == args.adresse.strip("/").lower()
                                               and x.get("acces")), None)
    mdp = "" if a_part else (os.environ.get("MOT_DE_PASSE_CLUB") or getpass.getpass("Mot de passe de l'espace club : "))
    if args.action == "espace":
        ajouter_espace(args.adresse, args.chemin, mdp, args.titre)
        print(f"Espace /{args.adresse.strip('/').lower()}/ ajouté. À envoyer sur GitHub (commit du dossier ressources/).")
        return 0
    fichier = ajouter(args.rubrique, args.chemin, mdp, args.titre, args.description, args.fichier)
    print(f"Ajouté : ressources/{fichier}.chiffre (rubrique « {args.rubrique} »). À envoyer sur GitHub (commit).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Archives des journées passées : les pages, l'Excel et les images telles qu'elles étaient la veille
de la journée suivante. La J3 passe en archive dès que la J4 a commencé.

Une archive est refaite avec la date de ce jour-là (résultats, feuilles de match, classement
virtuel, brûlages, prochaine journée : tout s'arrête à cette date), puis publiée une fois pour
toutes dans le site, chiffrée comme le reste : archives/<saison>-P<phase>-J<n>/ est un petit site
complet (accueil, pages, Excel, images), repris à chaque mise à jour. Les archives qui manquent
(par exemple J1 et J2 à la mise en place) sont reconstruites de la même façon, ainsi que celles
dont le récapitulatif changerait : surnoms, photo de la journée ou logos ajoutés après coup.

Lancé par le workflow GitHub après la publication du site :
  python -m ttvaires.archives --pingpocket-cache
Le mot de passe est lu dans la variable d'environnement MOT_DE_PASSE_SITE.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

from . import __main__ as programme
from . import fftt, publier, recap
from .reseau import HEURE, Client

RACINE = Path(__file__).resolve().parent.parent


def journees_de_la_phase(client, numero_club, aujourdhui):
    """[(numéro de journée, date de sa première rencontre)] pour les équipes du club, dans l'ordre."""
    debut, fin = fftt.bornes_phase(aujourdhui)
    id_club = fftt.id_interne_club(client, numero_club, debut)
    premieres = {}
    for r in fftt.rencontres_club(client, id_club, debut, fin, ttl=3 * HEURE):
        j, jour = r["day"]["position"], r["date"][:10]
        premieres[j] = min(premieres.get(j, jour), jour)
    return sorted(premieres.items())


def a_archiver(journees, aujourdhui):
    """[(journée, date de l'archive)] : chaque journée avant la dernière commencée (la J3 quand la J4
    a commencé), datée de la veille de la journée suivante."""
    commencees = [j for j, d in journees if d <= aujourdhui.isoformat()]
    if not commencees:
        return []
    derniere = max(commencees)
    return [(j, date.fromisoformat(min(d for jj, d in journees if jj > j)) - timedelta(days=1))
            for j, _ in journees if j < derniere]


def signature(mot_de_passe, journee, dossier_import=programme.IMPORT):
    """Empreinte de ce qui change une archive sans changer les résultats : surnoms, photo de la
    journée et logos du récapitulatif, mot de passe du site (chiffrement). Elle ne révèle rien."""
    h = hashlib.sha256(mot_de_passe.encode())
    h.update(json.dumps(sorted(recap.lire_surnoms(dossier_import).items())).encode())
    for f in recap.images_du_recap(dossier_import, journee):
        h.update(f.name.lower().encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:20]


def construire_manquantes(client, site, mot_de_passe, numero_club=programme.CLUB_VAIRES, travail=None, aujourdhui=None):
    """Construit et publie dans `site` les archives qui manquent. Renvoie leurs clés."""
    aujourdhui = aujourdhui or date.today()
    travail = Path(travail or RACINE / "sortie-archives")
    etat = json.loads((site / "etat.json").read_text(encoding="utf-8"))
    archives = etat.setdefault("archives", {})
    phase, saison = fftt.phase_et_saison(aujourdhui)
    nouvelles = []
    for j, veille in a_archiver(journees_de_la_phase(client, numero_club, aujourdhui), aujourdhui):
        cle = f"{saison}-P{phase}-J{j}"
        empreinte = signature(mot_de_passe, j)
        deja = archives.get(cle)
        if deja and deja.get("signature") == empreinte and all((site / f).exists() for f in deja.get("fichiers", [])):
            continue  # déjà publiée (si un fichier manque, elle est refaite)
        print(f"\n=== Archive de la J{j} : pages et images telles qu'au {veille:%d/%m/%Y} (veille de la J{j + 1})"
              + (" - refaite : surnoms, photo ou logos changés" if deja and deja.get("signature") != empreinte else ""), flush=True)
        sortie = travail / cle
        if sortie.exists():
            shutil.rmtree(sortie)
        ctx = programme.Contexte(sortie, veille)
        debut = time.time()
        dossier = site / "archives" / cle
        infos = {"titre": f"Journée {j}", "journee": j, "phase": phase, "saison": saison,
                 "date_reference": veille.isoformat()}
        try:
            _, bilans = programme.generer_pages(client, numero_club, ctx, programme.TOUTES_LES_PAGES)
            if any(resume.startswith("PAGE NON GÉNÉRÉE") for _, resume, _ in bilans):
                raise RuntimeError("page non générée")
            programme.ecrire_bilan(ctx, debut, bilans)
            if dossier.exists():
                shutil.rmtree(dossier)
            publier.publier(sortie, dossier, mot_de_passe, archive={**infos, "retour": "../../"})
        except Exception as e:  # noqa: BLE001 - une archive ratée ne doit pas empêcher la mise à jour du site
            print(f"  ! archive de la J{j} non publiée ({e}) : nouvel essai à la prochaine mise à jour")
            continue
        archives[cle] = {**infos, "dossier": f"archives/{cle}/", "cree_le": datetime.now().isoformat(timespec="minutes"),
                         "signature": empreinte,
                         "fichiers": sorted(f"archives/{cle}/{f.relative_to(dossier).as_posix()}"
                                            for f in dossier.rglob("*") if f.is_file())}
        nouvelles.append(cle)
    if nouvelles:
        publier.ecrire_etat(site, etat)
    return nouvelles


def main():
    parser = argparse.ArgumentParser(description="Archives des journées passées (site publié)")
    parser.add_argument("--site", default=str(RACINE / "site"), help="site déjà construit (python -m ttvaires.publier)")
    parser.add_argument("--club", default=programme.CLUB_VAIRES)
    parser.add_argument("--pingpocket-cache", action="store_true", help="n'interroge pas pingpocket.fr (mise à jour en ligne)")
    parser.add_argument("--hors-ligne", action="store_true", help="n'utilise que les pages déjà téléchargées")
    args = parser.parse_args()
    mot_de_passe = os.environ.get("MOT_DE_PASSE_SITE", "")
    if not mot_de_passe:
        print("!!! Mot de passe absent (MOT_DE_PASSE_SITE) : pas d'archive.")
        sys.exit(1)
    client = Client(programme.CACHE, hors_ligne=args.hors_ligne,
                    sites_cache_seul={"www.pingpocket.fr"} if args.pingpocket_cache else ())
    nouvelles = construire_manquantes(client, Path(args.site), mot_de_passe, args.club)
    print(f"Archives ajoutées : {', '.join(nouvelles)}" if nouvelles else "Archives : rien de nouveau.")


if __name__ == "__main__":
    main()

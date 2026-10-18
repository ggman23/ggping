"""Point d'entrée : python -m ttvaires [--adversaires] [--resultats] [--effectif] [--virtuel] [--demo] [--hors-ligne] [--pas-de-navigateur]."""

import argparse
import json
import time
import webbrowser
from datetime import datetime
from pathlib import Path

from .brulage import enrichir
from .demo import donnees_demo
from .adversaires import recuperer
from .effectif import recuperer_effectif
from .rendu import GABARIT_EFFECTIF, GABARIT_RESULTATS, GABARIT_VIRTUEL, generer_html
from .reseau import Client, ErreurReseau
from .resultats import donnees_page, ecrire_xlsx, recuperer_parties
from .virtuel import recuperer_virtuel
from . import verifications

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "sortie"
CACHE = RACINE / "cache"
IMPORT = RACINE / "import"  # listes de licenciés enregistrées depuis un navigateur
CLUB_VAIRES = "08770250"


def page_adversaires(client, club):
    print("=== Adversaires : API FFTT + compléments pingpocket.fr (le premier lancement peut être long :")
    print("pingpocket sature vite ; les suivants sont beaucoup plus rapides grâce au cache).", flush=True)
    donnees = recuperer(client, club, dossier_import=IMPORT)
    enrichir(donnees)
    (SORTIE / "donnees.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
    resume = verifications.afficher_adversaires(donnees["verification"]["journees"], donnees["verification"]["clubs"])
    return [generer_html(donnees, SORTIE / "vaires.html")], resume


def page_resultats(client, club):
    print("=== Résultats des joueurs de Vaires", flush=True)
    resultats = recuperer_parties(client, club)
    html = generer_html(donnees_page(resultats), SORTIE / "resultats_vaires.html", GABARIT_RESULTATS)
    xlsx = ecrire_xlsx(resultats, SORTIE / "resultats_vaires.xlsx")
    print(f"Classeur Excel : {xlsx}")
    return [html, xlsx], verifications.afficher_club(resultats["verification"], "résultats des équipes de Vaires")


def page_effectif(client, club):
    print("=== Effectif de Vaires : équipes jouées et brûlages", flush=True)
    donnees = recuperer_effectif(client, club, fichier_etat=CACHE / f"effectif_{club}.json", dossier_import=IMPORT)
    resume = verifications.afficher_club(donnees["verification"], "feuilles de match des équipes de Vaires")
    if not donnees["source"]["liste"]:
        resume += " ; liste des licenciés indisponible (voir import/LISEZ-MOI.txt)"
    return [generer_html(donnees, SORTIE / "effectif_vaires.html", GABARIT_EFFECTIF)], resume


def page_virtuel(client, club):
    print("=== Classement virtuel : toutes les compétitions (championnat, critérium, tournois...)", flush=True)
    donnees = recuperer_virtuel(client, club, dossier_import=IMPORT)
    resume = verifications.afficher_club(donnees["verification"], "feuilles de match des équipes de Vaires")
    resume = " ; ".join([resume] + verifications.afficher_controle_parties(donnees["controle"]))
    return [generer_html(donnees, SORTIE / "classement_virtuel.html", GABARIT_VIRTUEL)], resume


def main():
    parser = argparse.ArgumentParser(description="Outils du CVTT Vaires (championnat par équipes)")
    parser.add_argument("--adversaires", action="store_true", help="page des adversaires (choix par défaut)")
    parser.add_argument("--resultats", action="store_true", help="résultats des joueurs de Vaires (page + Excel)")
    parser.add_argument("--effectif", action="store_true", help="effectif de Vaires : brûlages par joueur et par équipe")
    parser.add_argument("--virtuel", action="store_true", help="classement virtuel du club, toutes compétitions")
    parser.add_argument("--demo", action="store_true", help="page des adversaires avec des données fictives")
    parser.add_argument("--hors-ligne", action="store_true", help="n'utilise que les pages déjà téléchargées")
    parser.add_argument("--paralleles", type=int, default=2, help="requêtes simultanées (défaut : 2)")
    parser.add_argument("--club", default=CLUB_VAIRES, help="numéro FFTT du club (défaut : Vaires)")
    parser.add_argument("--pas-de-navigateur", action="store_true", help="n'ouvre pas les pages à la fin")
    args = parser.parse_args()

    debut = time.time()
    SORTIE.mkdir(exist_ok=True)
    IMPORT.mkdir(exist_ok=True)
    if args.demo:
        donnees = donnees_demo()
        enrichir(donnees)
        pages = [generer_html(donnees, SORTIE / "vaires_demo.html")]
    else:
        client = Client(CACHE, paralleles=args.paralleles, hors_ligne=args.hors_ligne)
        pages, bilans = [], []
        a_faire = []
        if args.resultats:
            a_faire.append(("résultats", page_resultats))
        if args.effectif:
            a_faire.append(("effectif", page_effectif))
        if args.virtuel:
            a_faire.append(("classement virtuel", page_virtuel))
        if args.adversaires or not (args.resultats or args.effectif or args.virtuel):
            a_faire.append(("adversaires", page_adversaires))
        for nom, fonction in a_faire:
            try:
                nouvelles, resume = fonction(client, args.club)
                pages += nouvelles
                bilans.append((nom, resume, [Path(f).name for f in nouvelles]))
            except ErreurReseau as e:
                print(f"\n!!! Page {nom} non générée : {e}\n")
                bilans.append((nom, f"PAGE NON GÉNÉRÉE ({e})", []))
        print(f"Pages téléchargées : {client.nb_telecharges}, reprises du cache : {client.nb_cache}")
        print("\n=== Bilan des vérifications ===")
        for nom, resume, _ in bilans:
            print(f"  {nom} : {resume}")
        print()
        # Bilan lu par la publication du site (python -m ttvaires.publier)
        (SORTIE / "bilan.json").write_text(json.dumps({
            "debut": datetime.fromtimestamp(debut).isoformat(timespec="minutes"),
            "fin": datetime.now().isoformat(timespec="minutes"),
            "pages": [{"nom": nom, "resume": resume, "fichiers": fichiers} for nom, resume, fichiers in bilans],
        }, ensure_ascii=False, indent=1), encoding="utf-8")

    for chemin in pages:
        print(f"Fichier généré : {chemin}")
    print(f"Terminé en {round(time.time() - debut)} s.")
    if not args.pas_de_navigateur:
        for chemin in pages:
            if Path(chemin).suffix == ".html":
                webbrowser.open(Path(chemin).as_uri())


if __name__ == "__main__":
    main()

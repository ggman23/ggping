"""Point d'entrée : python -m ttvaires [--adversaires] [--resultats] [--demo] [--hors-ligne] [--pas-de-navigateur]."""

import argparse
import json
import time
import webbrowser
from pathlib import Path

from .brulage import enrichir
from .demo import donnees_demo
from .adversaires import recuperer
from .effectif import recuperer_effectif
from .rendu import GABARIT_EFFECTIF, GABARIT_RESULTATS, generer_html
from .reseau import Client, ErreurReseau
from .resultats import donnees_page, ecrire_xlsx, recuperer_parties

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "sortie"
CACHE = RACINE / "cache"
CLUB_VAIRES = "08770250"


def page_adversaires(client, club):
    print("=== Adversaires : API FFTT + compléments pingpocket.fr (le premier lancement peut être long :")
    print("pingpocket sature vite ; les suivants sont beaucoup plus rapides grâce au cache).", flush=True)
    donnees = recuperer(client, club)
    enrichir(donnees)
    (SORTIE / "donnees.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
    return [generer_html(donnees, SORTIE / "vaires.html")]


def page_resultats(client, club):
    print("=== Résultats des joueurs de Vaires", flush=True)
    resultats = recuperer_parties(client, club)
    html = generer_html(donnees_page(resultats), SORTIE / "resultats_vaires.html", GABARIT_RESULTATS)
    xlsx = ecrire_xlsx(resultats, SORTIE / "resultats_vaires.xlsx")
    print(f"Classeur Excel : {xlsx}")
    return [html]


def page_effectif(client, club):
    print("=== Effectif de Vaires : équipes jouées et brûlages", flush=True)
    donnees = recuperer_effectif(client, club, fichier_etat=CACHE / f"effectif_{club}.json")
    return [generer_html(donnees, SORTIE / "effectif_vaires.html", GABARIT_EFFECTIF)]


def main():
    parser = argparse.ArgumentParser(description="Outils du CVTT Vaires (championnat par équipes)")
    parser.add_argument("--adversaires", action="store_true", help="page des adversaires (choix par défaut)")
    parser.add_argument("--resultats", action="store_true", help="résultats des joueurs de Vaires (page + Excel)")
    parser.add_argument("--effectif", action="store_true", help="effectif de Vaires : brûlages par joueur et par équipe")
    parser.add_argument("--demo", action="store_true", help="page des adversaires avec des données fictives")
    parser.add_argument("--hors-ligne", action="store_true", help="n'utilise que les pages déjà téléchargées")
    parser.add_argument("--paralleles", type=int, default=2, help="requêtes simultanées (défaut : 2)")
    parser.add_argument("--club", default=CLUB_VAIRES, help="numéro FFTT du club (défaut : Vaires)")
    parser.add_argument("--pas-de-navigateur", action="store_true", help="n'ouvre pas les pages à la fin")
    args = parser.parse_args()

    debut = time.time()
    SORTIE.mkdir(exist_ok=True)
    if args.demo:
        donnees = donnees_demo()
        enrichir(donnees)
        pages = [generer_html(donnees, SORTIE / "vaires_demo.html")]
    else:
        client = Client(CACHE, paralleles=args.paralleles, hors_ligne=args.hors_ligne)
        pages = []
        a_faire = []
        if args.resultats:
            a_faire.append(("résultats", page_resultats))
        if args.effectif:
            a_faire.append(("effectif", page_effectif))
        if args.adversaires or not (args.resultats or args.effectif):
            a_faire.append(("adversaires", page_adversaires))
        for nom, fonction in a_faire:
            try:
                pages += fonction(client, args.club)
            except ErreurReseau as e:
                print(f"\n!!! Page {nom} non générée : {e}\n")
        print(f"Pages téléchargées : {client.nb_telecharges}, reprises du cache : {client.nb_cache}")

    for chemin in pages:
        print(f"Page générée : {chemin}")
    print(f"Terminé en {round(time.time() - debut)} s.")
    if not args.pas_de_navigateur:
        for chemin in pages:
            webbrowser.open(chemin.as_uri())


if __name__ == "__main__":
    main()

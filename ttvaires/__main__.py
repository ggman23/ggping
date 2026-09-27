"""Point d'entrée : python -m ttvaires [--demo] [--hors-ligne] [--pas-de-navigateur]."""

import argparse
import json
import time
import webbrowser
from pathlib import Path

from .brulage import enrichir
from .demo import donnees_demo
from .pingpocket import recuperer
from .rendu import generer_html
from .reseau import Client

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "sortie"
CACHE = RACINE / "cache"
CLUB_VAIRES = "08770250"


def main():
    parser = argparse.ArgumentParser(description="Adversaires des équipes du CVTT Vaires")
    parser.add_argument("--demo", action="store_true", help="page avec des données fictives")
    parser.add_argument("--hors-ligne", action="store_true", help="n'utilise que les pages déjà téléchargées")
    parser.add_argument("--paralleles", type=int, default=3, help="requêtes simultanées (défaut : 3)")
    parser.add_argument("--club", default=CLUB_VAIRES, help="numéro FFTT du club (défaut : Vaires)")
    parser.add_argument("--pas-de-navigateur", action="store_true", help="n'ouvre pas la page à la fin")
    args = parser.parse_args()

    debut = time.time()
    if args.demo:
        donnees = donnees_demo()
        chemin = SORTIE / "vaires_demo.html"
    else:
        print("Récupération des données sur pingpocket.fr (le premier lancement peut durer 20 à 30 minutes,")
        print("les suivants sont beaucoup plus rapides grâce au cache).", flush=True)
        client = Client(CACHE, paralleles=args.paralleles, hors_ligne=args.hors_ligne)
        donnees = recuperer(client, args.club)
        print(f"Pages téléchargées : {client.nb_telecharges}, reprises du cache : {client.nb_cache}")
        chemin = SORTIE / "vaires.html"

    enrichir(donnees)
    SORTIE.mkdir(exist_ok=True)
    (SORTIE / "donnees.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")
    chemin = generer_html(donnees, chemin)
    print(f"Page générée en {round(time.time() - debut)} s : {chemin}")
    if not args.pas_de_navigateur:
        webbrowser.open(chemin.as_uri())


if __name__ == "__main__":
    main()

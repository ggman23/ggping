"""Point d'entrée : python -m ttvaires [--demo] [--pas-de-navigateur]."""

import argparse
import webbrowser
from pathlib import Path

from .brulage import enrichir
from .demo import donnees_demo
from .rendu import generer_html

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "sortie"


def main():
    parser = argparse.ArgumentParser(description="Adversaires des équipes du CVTT Vaires")
    parser.add_argument("--demo", action="store_true", help="génère la page avec des données fictives")
    parser.add_argument("--pas-de-navigateur", action="store_true", help="n'ouvre pas la page à la fin")
    args = parser.parse_args()

    if args.demo:
        donnees = donnees_demo()
        chemin = SORTIE / "vaires_demo.html"
    else:
        raise SystemExit("La récupération sur Internet n'est pas encore disponible : lancez avec --demo.")

    enrichir(donnees)
    chemin = generer_html(donnees, chemin)
    print(f"Page générée : {chemin}")
    if not args.pas_de_navigateur:
        webbrowser.open(chemin.as_uri())


if __name__ == "__main__":
    main()

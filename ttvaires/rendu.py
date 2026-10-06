"""Génération de la page HTML statique (un seul fichier, consultable hors ligne)."""

import json
from pathlib import Path

GABARIT = Path(__file__).with_name("gabarit.html")
GABARIT_RESULTATS = Path(__file__).with_name("gabarit_resultats.html")
GABARIT_EFFECTIF = Path(__file__).with_name("gabarit_effectif.html")


def generer_html(donnees, chemin, gabarit=GABARIT):
    """Écrit la page HTML avec les données intégrées et renvoie son chemin."""
    # "<" échappé pour que le JSON ne puisse jamais fermer la balise <script>.
    js = json.dumps(donnees, ensure_ascii=False).replace("<", "\\u003c")
    html = Path(gabarit).read_text(encoding="utf-8").replace("__DONNEES_JSON__", js)
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(html, encoding="utf-8")
    return chemin

"""Mise à jour automatique du lundi : seulement après un week-end de championnat.

Le workflow planifié tourne le lundi matin et demande d'abord ici si une équipe de Vaires (masculine
ou féminine) a joué entre le vendredi et le dimanche précédents. Sinon il s'arrête là : pas de mise
à jour. Elle publie sur GitHub et Cloudflare seulement (gratuits) ; Netlify (15 crédits par envoi)
n'est envoyé qu'à la main. Les mises à jour lancées à la main (site, téléphone, PC) ne passent pas
par ce contrôle.

  python -m ttvaires.calendrier                    # écrit continuer=true/false pour le workflow
  python -m ttvaires.calendrier --date 2026-11-09  # essai pour un autre lundi
"""

import argparse
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from . import compte_fftt, fftt
from .reseau import HEURE, Client, ErreurReseau

RACINE = Path(__file__).resolve().parent.parent
CLUB_VAIRES = "08770250"


def week_end_precedent(jour):
    """(vendredi, dimanche) du dernier week-end terminé avant `jour`."""
    vendredi = jour - timedelta(days=(jour.weekday() - 4) % 7 or 7)
    if vendredi + timedelta(days=2) >= jour:  # week-end pas encore terminé : le précédent
        vendredi -= timedelta(days=7)
    return vendredi, vendredi + timedelta(days=2)


def rencontres_du_week_end(client, jour, numero_club=CLUB_VAIRES):
    """Rencontres de championnat du club jouées le week-end qui précède `jour`."""
    vendredi, dimanche = week_end_precedent(jour)
    debut, fin = fftt.bornes_phase(vendredi)
    id_club = fftt.id_interne_club(client, numero_club, debut)
    return [r for r in fftt.rencontres_club(client, id_club, debut, fin, ttl=HEURE)
            if vendredi.isoformat() <= r["date"][:10] <= dimanche.isoformat()]


def main(arguments=None):
    p = argparse.ArgumentParser(prog="python -m ttvaires.calendrier", description=__doc__.splitlines()[0])
    p.add_argument("--date", type=date.fromisoformat, help="jour de référence AAAA-MM-JJ (par défaut : aujourd'hui)")
    args = p.parse_args(arguments)
    jour = args.date or date.today()
    vendredi, dimanche = week_end_precedent(jour)
    client = Client(RACINE / "cache")
    try:
        compte_fftt.connecter(client, demander=False)
        rencontres = rencontres_du_week_end(client, jour)
    except ErreurReseau as e:  # dans le doute, on met à jour (gratuit : GitHub et Cloudflare)
        print(f"Calendrier de la FFTT illisible ({e}) : mise à jour faite par précaution.")
        continuer = True
    else:
        continuer = bool(rencontres)
        print(f"Week-end du {vendredi:%d/%m} au {dimanche:%d/%m} : "
              + (f"{len(rencontres)} rencontre(s) de championnat de Vaires, mise à jour." if continuer
                 else "pas de championnat pour Vaires, pas de mise à jour."))
    sortie = os.environ.get("GITHUB_OUTPUT")
    if sortie:
        with open(sortie, "a", encoding="utf-8") as f:
            f.write(f"continuer={'true' if continuer else 'false'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

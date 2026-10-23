"""Icônes de l'application (lanceur Android) faites à partir du logo du club (ttvaires/logo_club.png).

  python android/icones.py

Icône classique (logo rond) dans res/mipmap-<densité>/ic_launcher.png et icône adaptative
(Android 8 et plus) : le logo au centre de la zone sûre, sur fond sombre.
"""

from pathlib import Path

from PIL import Image

ICI = Path(__file__).resolve().parent
LOGO = ICI.parent / "ttvaires" / "logo_club.png"
DENSITES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def main():
    logo = Image.open(LOGO).convert("RGBA")
    for nom, facteur in DENSITES.items():
        dossier = ICI / "res" / f"mipmap-{nom}"
        dossier.mkdir(parents=True, exist_ok=True)
        cote = round(48 * facteur)
        icone = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
        petit = logo.resize((round(cote * 0.92),) * 2, Image.LANCZOS)
        icone.alpha_composite(petit, ((cote - petit.width) // 2,) * 2)
        icone.save(dossier / "ic_launcher.png", optimize=True)
        # Icône adaptative : calque de 108 dp dont seuls les 66 dp du centre sont toujours visibles
        cote = round(108 * facteur)
        avant = Image.new("RGBA", (cote, cote), (0, 0, 0, 0))
        petit = logo.resize((round(cote * 0.62),) * 2, Image.LANCZOS)
        avant.alpha_composite(petit, ((cote - petit.width) // 2,) * 2)
        avant.save(dossier / "ic_launcher_foreground.png", optimize=True)


if __name__ == "__main__":
    main()

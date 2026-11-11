"""Copie de secours du site sur Netlify (https://ggping.netlify.app/).

- https://ggping.netlify.app/ : la page des adversaires (vaires.html), lisible par tout le club
  sans mot de passe (non référencée par les moteurs de recherche : robots.txt et en-tête noindex) ;
- https://ggping.netlify.app/club/ : l'espace club, avec son propre mot de passe (secret
  MOT_DE_PASSE_CLUB) : un menu des pages, de l'Excel et des images, que l'on peut regarder dans
  la page puis télécharger (sans bouton de mise à jour). Sans ce secret, /club/ n'est pas publié ;
- https://ggping.netlify.app/gg/ : la copie du site GitHub (page d'accueil, toutes les pages,
  l'Excel et les images), re-chiffrée avec son propre mot de passe (secret MOT_DE_PASSE_GG, à donner
  aux capitaines) : le mot de passe du site GitHub reste secret. Sans MOT_DE_PASSE_GG, /gg/ n'est
  pas publié.

Statistiques de visite (facultatif) : avec la variable GOATCOUNTER (le code d'un compte gratuit
goatcounter.com) et/ou UMAMI (l'identifiant d'un site Umami Cloud), l'accueil public, /club/ et /gg/
comptent les pages vues, les visiteurs et, dans /club/ et /gg/, les documents ouverts, téléchargés
et partagés. Ni GoatCounter ni Umami ne posent de cookie, et ils ne reçoivent aucun nom de joueur
(seulement des noms de fichiers : resultats_vaires.xlsx...). Umami donne en plus le temps passé,
les parcours et le retour des visiteurs. Le site GitHub, lui, n'est jamais compté.

Lancé par le workflow GitHub après la publication du site (dossier site/ prêt), donc après chaque
mise à jour, qu'elle vienne du PC (option 7) ou du téléphone :
  python -m ttvaires.netlify
Variables d'environnement : NETLIFY_AUTH_TOKEN (jeton Netlify ; sans lui, rien n'est fait),
NETLIFY_SITE (par défaut ggping.netlify.app), MOT_DE_PASSE_SITE (pour lire le site GitHub),
MOT_DE_PASSE_GG (celui de /gg/), MOT_DE_PASSE_CLUB (celui de /club/), GOATCOUNTER et UMAMI (statistiques).
"""

import argparse
import base64
import gzip
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from . import publier, ressources

RACINE = Path(__file__).resolve().parent.parent
API = "https://api.netlify.com/api/v1"
SITE_PAR_DEFAUT = "ggping.netlify.app"
NOINDEX = '<meta name="robots" content="noindex, nofollow">'
CHIFFRE = re.compile(r'<script id="chiffre" type="text/plain">([^<]+)</script>')
GABARIT_CLUB = Path(__file__).with_name("gabarit_club.html")
VERIF_CLUB = b"cvtt-vaires-club"  # fichier témoin : sert à vérifier le mot de passe de /club/
# Compteur de visites : version figée du script, vérifiée par son empreinte (integrity) : s'il
# changeait sur le serveur de GoatCounter, le navigateur refuserait de l'exécuter.
GOATCOUNTER_JS = "https://gc.zgo.at/count.v5.js"
GOATCOUNTER_SRI = "sha384-atnOLvQb9t+jTSipvd75X2yginT4PjVbqDdlJAmxMm+wYElFmeR6EmLP5bYeoRVQ"
# Umami : copie figée de son script, servie par le site (stats/umami.js), qui envoie à Umami Cloud.
UMAMI_JS = Path(__file__).with_name("umami.js")
UMAMI_PUBLIE = "stats/umami.js"
# Envoi direct à Umami Cloud : par son relais (gateway.umami.is, réglage par défaut du script), tous
# les visiteurs apparaissaient aux États-Unis (pays du relais et non du visiteur).
UMAMI_HOTE = "https://cloud.umami.is"
ORDRE_CLUB = ["vaires.html", "resultats_vaires.html", "resultats_vaires.xlsx", "rencontres_vaires.html",
              "classements_vaires.html", "effectif_vaires.html", "classement_virtuel.html", "progression_vaires.html"]
# Pages du site publiées à leur propre adresse avec le mot de passe du club (et non parmi les documents
# de /club/, qui y renvoie par « Autres espaces ») : page du site -> (adresse, titre)
PAGES_A_PART = {"indivs.html": ("indivs", "Individuels")}
# Pages fixes (aucune donnée de la mise à jour), publiées de même à leur adresse : adresse -> (titre, gabarit).
# /tournois/ : blocs de PingRadar intégrés (cadres qui se mettent à jour tout seuls, voir le gabarit).
PAGES_FIXES = {"tournois": ("Tournois", Path(__file__).with_name("gabarit_tournois.html"))}


class ErreurNetlify(Exception):
    pass


def chiffrer_stable(donnees, cle):
    """Comme publier.chiffrer, mais un même contenu donne toujours le même fichier (vecteur
    d'initialisation tiré du contenu) : une archive, qui ne change plus, n'est pas renvoyée à
    Netlify à chaque mise à jour. Seule l'égalité de deux contenus identiques se voit."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    iv = hmac.new(cle, donnees, hashlib.sha256).digest()[:12]
    return iv + AESGCM(cle).encrypt(iv, gzip.compress(donnees, mtime=0), None)


def page_publique(site, mot_de_passe):
    """La page des adversaires du site GitHub, déchiffrée : l'accueil public de Netlify."""
    fichier = site / "adversaires.html"
    if not fichier.exists():
        return ("<!doctype html><meta charset=\"utf-8\"><title>CVTT Vaires</title>"
                "<p>La page des adversaires n'a pas encore été générée.</p>")
    chiffre = CHIFFRE.search(fichier.read_text(encoding="utf-8"))
    html = publier.dechiffrer(base64.b64decode(chiffre[1]), publier.cle(mot_de_passe)).decode("utf-8")
    if 'name="robots"' not in html:
        html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX, 1)
    return html


def copie_rechiffree(site, gg, cle_site, cle_gg):
    """Copie du site GitHub dont chaque page, l'Excel et chaque image sont re-chiffrés avec la clé de /gg/.
    L'accueil, etat.json, robots.txt... ne contiennent aucune donnée de joueur : copiés tels quels."""
    for f in sorted(site.rglob("*")):
        if not f.is_file():
            continue
        cible = gg / f.relative_to(site)
        cible.parent.mkdir(parents=True, exist_ok=True)
        if f.suffix == ".chiffre":
            cible.write_bytes(chiffrer_stable(publier.dechiffrer(f.read_bytes(), cle_site), cle_gg))
            continue
        texte = f.read_text(encoding="utf-8") if f.suffix == ".html" else None
        m = CHIFFRE.search(texte) if texte else None
        if m:  # page verrouillée : seul le contenu chiffré change
            donnees = publier.dechiffrer(base64.b64decode(m[1]), cle_site)
            nouveau = base64.b64encode(chiffrer_stable(donnees, cle_gg)).decode("ascii")
            cible.write_text(texte[:m.start(1)] + nouveau + texte[m.end(1):], encoding="utf-8")
        else:
            shutil.copy2(f, cible)


def _clair(fichier, cle):
    """Contenu d'un fichier du site GitHub : page verrouillée (HTML) ou fichier .chiffre (Excel, image)."""
    if fichier.suffix == ".chiffre":
        return publier.dechiffrer(fichier.read_bytes(), cle)
    return publier.dechiffrer(base64.b64decode(CHIFFRE.search(fichier.read_text(encoding="utf-8"))[1]), cle)


def _documents_club(site, etat, fichiers, prefixe, cle_site, cle_club):
    """Re-chiffre pour /club/ les pages, l'Excel et les images d'un site (celui du jour ou une archive)
    dans `fichiers`, sous leur nom d'origine ; renvoie leur liste (chemin : prefixe + nom.chiffre)."""
    fichiers.mkdir(parents=True, exist_ok=True)
    documents = []
    for publie, info in etat.get("pages", {}).items():
        if not (site / publie).exists() or publie in PAGES_A_PART:
            continue
        nom = info.get("nom_telecharge") or publie.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(chiffrer_stable(_clair(site / publie, cle_site), cle_club))
        excel = nom.endswith(".xlsx")
        documents.append({"fichier": nom, "chemin": f"{prefixe}{nom}.chiffre", "type": "excel" if excel else "page",
                          "titre": info.get("titre", nom), "description": info.get("description", ""), "date": info.get("date"),
                          "verification": "" if excel else info.get("verification", ""),
                          "ordre": ORDRE_CLUB.index(nom) if nom in ORDRE_CLUB else len(ORDRE_CLUB)})
    for publie, info in etat.get("images", {}).items():
        if not (site / publie).exists():
            continue
        nom = info.get("nom_telecharge") or Path(publie).name.removesuffix(".chiffre")
        (fichiers / f"{nom}.chiffre").write_bytes(chiffrer_stable(_clair(site / publie, cle_site), cle_club))
        documents.append({"fichier": nom, "chemin": f"{prefixe}{nom}.chiffre", "type": "image", "titre": info.get("titre", nom),
                          "groupe": info.get("groupe"), "ordre": info.get("ordre", 0), "date": info.get("date")})
    return documents


def publier_pages_a_part(site, dossier, cle_site, cle_club):
    """Pages du site (PAGES_A_PART) publiées aussi à leur adresse, ex. /indivs/, et pages fixes
    (PAGES_FIXES, ex. /tournois/) : page de mot de passe (celui du club, retenu comme pour /club/) qui
    affiche la page, toujours chiffrée. Renvoie les adresses."""
    publiees = []
    for publie, (chemin, titre) in PAGES_A_PART.items():
        if not (site / publie).exists():
            continue
        page = dossier / chemin / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        chiffre = chiffrer_stable(_clair(site / publie, cle_site), cle_club)
        page.write_text(publier.page_verrouillee_chiffree(chiffre, titre, ressources.STOCKAGE_CLUB), encoding="utf-8")
        publiees.append(chemin)
    for chemin, (titre, gabarit) in PAGES_FIXES.items():
        page = dossier / chemin / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        chiffre = chiffrer_stable(gabarit.read_bytes(), cle_club)
        page.write_text(publier.page_verrouillee_chiffree(chiffre, titre, ressources.STOCKAGE_CLUB), encoding="utf-8")
        publiees.append(chemin)
    return publiees


def espace_club(site, club, cle_site, cle_club):
    """/club/ : chaque page, l'Excel et chaque image (du jour, et de chaque journée archivée),
    re-chiffrés avec la clé du club sous leur nom d'origine, et la page de navigation
    (gabarit_club.html) qui les déchiffre dans le navigateur. La liste des documents (titres,
    dates) ne contient aucun nom de joueur."""
    fichier_etat = site / "etat.json"
    etat = json.loads(fichier_etat.read_text(encoding="utf-8")) if fichier_etat.exists() else {}
    documents = _documents_club(site, etat, club / "fichiers", "fichiers/", cle_site, cle_club)
    archives = []
    for cle_archive, a in sorted(etat.get("archives", {}).items(),
                                 key=lambda x: (x[1].get("saison", ""), x[1].get("phase", 0), x[1].get("journee", 0)), reverse=True):
        dossier = site / a["dossier"]
        if not (dossier / "etat.json").exists():
            continue
        etat_archive = json.loads((dossier / "etat.json").read_text(encoding="utf-8"))
        archives.append({"cle": cle_archive, "titre": a["titre"], "journee": a.get("journee"), "phase": a.get("phase"),
                         "saison": a.get("saison"), "date_reference": a.get("date_reference"),
                         "documents": _documents_club(dossier, etat_archive, club / "archives" / cle_archive / "fichiers",
                                                      f"archives/{cle_archive}/fichiers/", cle_site, cle_club)})
    (club / "fichiers" / "verif.chiffre").write_bytes(chiffrer_stable(VERIF_CLUB, cle_club))
    # Rubriques permanentes après les archives (Matériel, Prépa mentale...) : documents fournis, voir ressources.py
    rubriques = ressources.publier_dans(club, cle_club)
    donnees = {"maj": (etat.get("derniere_maj") or {}).get("fin"), "sel": publier.SEL, "iterations": publier.ITERATIONS,
               "documents": documents, "archives": archives, "ressources": rubriques,
               # Autres espaces listés dans /club/ : individuels et tournois ; pas les espaces fournis
               # (ressources.py, ex. /lundi/ : pour l'administrateur et l'application seulement)
               "espaces": [{"chemin": chemin, "titre": titre} for publie, (chemin, titre) in PAGES_A_PART.items()
                             if (site / publie).exists()]
                          + [{"chemin": chemin, "titre": titre} for chemin, (titre, _) in PAGES_FIXES.items()]}
    js = json.dumps(donnees, ensure_ascii=False).replace("<", "\\u003c")
    (club / "index.html").write_text(GABARIT_CLUB.read_text(encoding="utf-8").replace("__DONNEES_JSON__", js), encoding="utf-8")


def code_goatcounter(valeur):
    """« cvtt-vaires », « cvtt-vaires.goatcounter.com » ou son adresse complète -> « cvtt-vaires » ;
    vide si ce n'est pas un code GoatCounter."""
    m = re.fullmatch(r"(?:https?://)?([a-z0-9][a-z0-9-]{1,62})(?:\.goatcounter\.com)?(?:/count)?/?", (valeur or "").strip().lower())
    return m[1] if m else ""


# Envoi aux compteurs configurés (GoatCounter, Umami) : window.compteur(chemin, titre, evenement),
# appelé par l'espace club et les accueils de /gg/ ; ce qui arrive avant le chargement d'un compteur
# attend. Pour Umami, un événement est nommé par son action (telechargement, partage...), avec
# l'espace et le fichier en détail. « #toggle-goatcounter » coupe (ou rétablit) aussi Umami.
COMPTEURS_JS = """(() => {
  const ACTIFS = __ACTIFS__;
  const ACTIONS = ["connexion", "connexion-refusee", "telechargement", "partage", "tout-telecharger", "ouverture",
                   "image", "mise-a-jour"];
  const ENVOIS = {
    goatcounter: (chemin, titre, evenement) => window.goatcounter.count({ path: chemin, title: titre, event: evenement }),
    umami: (chemin, titre, evenement) => {
      if (!evenement) return window.umami.track((p) => ({ ...p, url: chemin, title: titre }));
      const morceaux = chemin.split("/"), i = morceaux.findIndex((m) => ACTIONS.includes(m));
      if (i < 0) return window.umami.track(chemin);
      const fichier = morceaux.slice(i + 1).join("/");
      window.umami.track(morceaux[i], { espace: morceaux.slice(0, i).join("/") || "accueil", ...(fichier && { fichier }) });
    },
  };
  // Pas d'envoi à Umami pour un navigateur piloté par un programme (robot : Umami ne sait pas l'écarter
  // lui-même, GoatCounter le signale) ni pour le réglage #toggle-goatcounter (ce n'est pas une visite)
  window.umamiAvantEnvoi = (type, mesure) =>
    (navigator.webdriver || location.hash === "#toggle-goatcounter" ? null : mesure);
  const etat = Object.fromEntries(ACTIFS.map((nom) => [nom, { pret: false, attente: [] }]));
  const envoyer = (nom, args) => { try { ENVOIS[nom](...args); } catch (e) { /* compteur indisponible */ } };
  window.compteur = (chemin, titre, evenement = false) => ACTIFS.forEach((nom) =>
    etat[nom].pret ? envoyer(nom, [chemin, titre, evenement]) : etat[nom].attente.push([chemin, titre, evenement]));
  window.compteurPret = (nom) => {
    if (!etat[nom] || etat[nom].pret) return;
    etat[nom].pret = true;
    etat[nom].attente.splice(0).forEach((args) => envoyer(nom, args));
    if (nom === "goatcounter" && window.compteurVisiteurs) window.compteurVisiteurs();
  };
  try {  // ses propres visites : #toggle-goatcounter (GoatCounter s'en occupe s'il est là)
    let couper = localStorage.getItem("skipgc") === "t";
    if (location.hash === "#toggle-goatcounter") {
      couper = !couper;
      if (!ACTIFS.includes("goatcounter")) {
        couper ? localStorage.setItem("skipgc", "t") : localStorage.removeItem("skipgc");
        alert(couper ? "Statistiques : cet appareil n'est plus compté." : "Statistiques : cet appareil est de nouveau compté.");
      }
    }
    couper ? localStorage.setItem("umami.disabled", "1") : localStorage.removeItem("umami.disabled");
  } catch (e) { /* navigation privée */ }
})();"""

# Visiteurs différents (GoatCounter), sans cookie, sans adresse IP et sans identifiant : chaque
# appareil se signale une seule fois par jour, par semaine et par mois (et la première fois qu'il
# vient), grâce à un simple mémo dans son navigateur (dates des derniers signalements, rien d'autre).
# Événements « appareils/jour », « appareils/semaine », « appareils/mois », « appareils/nouveaux », et
# les mêmes par espace : « appareils/club/mois »... Un appareil = un téléphone ou un navigateur de PC.
# (Umami compte lui-même les visiteurs différents.)
VISITEURS_JS = """window.compteurVisiteurs = function () {
  const gc = window.goatcounter;
  if (!gc || !gc.count) return;
  let memo;
  try { memo = JSON.parse(localStorage.getItem("cvtt-stats-vu") || "{}"); } catch (e) { return; }
  const d = new Date(), date = (x) => x.toLocaleDateString("sv");  // AAAA-MM-JJ, heure locale
  const lundi = new Date(d.getFullYear(), d.getMonth(), d.getDate() - (d.getDay() + 6) % 7);
  const espace = /\\/club(\\/|$)/.test(location.pathname) ? "club" : /\\/gg(\\/|$)/.test(location.pathname) ? "gg" : "accueil";
  const NOMS = { jour: "aujourd'hui", semaine: "cette semaine", mois: "ce mois-ci" };
  const envois = memo.premier ? [] : [["appareils/nouveaux", "Appareils venus pour la première fois"]];
  for (const [periode, valeur] of [["jour", date(d)], ["semaine", date(lundi)], ["mois", date(d).slice(0, 7)]]) {
    for (const [cle, chemin, ou] of [[periode, `appareils/${periode}`, ""],
                                     [`${espace}-${periode}`, `appareils/${espace}/${periode}`, ` (${espace})`]]) {
      if (memo[cle] !== valeur) envois.push([chemin, `Appareils différents ${NOMS[periode]}${ou}`]);
      memo[cle] = valeur;
    }
  }
  memo.premier = memo.premier || date(d);
  try { localStorage.setItem("cvtt-stats-vu", JSON.stringify(memo)); } catch (e) { return; }
  envois.forEach(([chemin, titre]) => gc.count({ path: chemin, title: titre, event: true }));
};"""


def code_umami(valeur):
    """Identifiant d'un site Umami (data-website-id, de la forme 23cfef06-9803-...) ; vide sinon."""
    m = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", (valeur or "").strip().lower())
    return m[0] if m else ""


def avec_compteurs(html, goatcounter="", umami="", manuel=False, umami_src="/" + UMAMI_PUBLIE):
    """Ajoute les compteurs de visites configurés avant </head>. `manuel` : la page compte elle-même
    ce qu'on y fait (compter() de l'espace club et des accueils) ; sinon une page vue par chargement.
    Le chemin compté ne garde pas le « ?v=... » des liens. `umami_src` : adresse du script d'Umami
    servi par le site (relative sur le site GitHub, qui est sous /ggping/)."""
    actifs = [nom for nom, code in (("goatcounter", goatcounter), ("umami", umami)) if code]
    if not actifs:
        return html
    js = [COMPTEURS_JS.replace("__ACTIFS__", json.dumps(actifs))]
    balises = []
    if goatcounter:
        js[:0] = ['window.goatcounter = { path: (p) => p.split("?")[0] || "/" };', VISITEURS_JS]
        reglages = """ data-goatcounter-settings='{"no_onload": true}'""" if manuel else ""
        balises.append(f'<script data-goatcounter="https://{goatcounter}.goatcounter.com/count"{reglages} async'
                       f' src="{GOATCOUNTER_JS}" integrity="{GOATCOUNTER_SRI}" crossorigin="anonymous"'
                       """ onload="window.compteurPret && compteurPret('goatcounter')"></script>""")
    if umami:
        reglages = ' data-auto-track="false"' if manuel else ' data-performance="true" data-exclude-hash="true"'
        balises.append(f'<script defer src="{umami_src}" data-website-id="{umami}"{reglages} data-exclude-search="true"'
                       f' data-host-url="{UMAMI_HOTE}" data-before-send="umamiAvantEnvoi"'
                       ' onload="window.compteurPret && compteurPret(\'umami\')"></script>')
    script = "<script>\n" + "\n".join(js) + "\n</script>\n" + "".join(b + "\n" for b in balises)
    return html.replace("</head>", script + "</head>", 1)


def _ajouter_compteurs(dossier, goatcounter, umami):
    """Accueil public (une page vue par visite), /club/ et chaque accueil de /gg/ (archives comprises),
    qui comptent eux-mêmes les documents ouverts, téléchargés et partagés. Le script d'Umami est servi
    par le site lui-même (copie figée)."""
    if umami:
        (dossier / UMAMI_PUBLIE).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(UMAMI_JS, dossier / UMAMI_PUBLIE)
    espaces = [dossier / e["chemin"] / "index.html" for e in ressources.lire()["espaces"]]
    espaces += [dossier / chemin / "index.html" for chemin, _ in PAGES_A_PART.values()]
    espaces += [dossier / chemin / "index.html" for chemin in PAGES_FIXES]
    for page, manuel in [(dossier / "index.html", False), (dossier / "club" / "index.html", True),
                         *((f, True) for f in sorted((dossier / "gg").rglob("index.html"))),
                         *((f, False) for f in espaces)]:
        if page.exists():
            page.write_text(avec_compteurs(page.read_text(encoding="utf-8"), goatcounter, umami, manuel), encoding="utf-8")


def construire(site, dossier, mot_de_passe, mot_de_passe_gg, mot_de_passe_club="", goatcounter="", umami=""):
    """Prépare dans `dossier` le site Netlify : accueil public, club/ (espace club) et gg/ (copie
    re-chiffrée du site GitHub). Sans leur propre mot de passe, club/ et gg/ ne sont pas publiés
    (jamais avec celui du site GitHub). `goatcounter`, `umami` : compteurs de visites (facultatifs)."""
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)
    cle_site = publier.cle(mot_de_passe)
    if mot_de_passe_gg:
        copie_rechiffree(site, dossier / "gg", cle_site, publier.cle(mot_de_passe_gg))
    if mot_de_passe_club:
        espace_club(site, dossier / "club", cle_site, publier.cle(mot_de_passe_club))
        # Espaces protégés à leur propre adresse (ex. /lundi/), mot de passe du club : voir ressources.py
        ressources.publier_espaces(dossier, publier.cle(mot_de_passe_club))
        publier_pages_a_part(site, dossier, cle_site, publier.cle(mot_de_passe_club))  # ex. /indivs/, /tournois/
    (dossier / "index.html").write_text(page_publique(site, mot_de_passe), encoding="utf-8")
    (dossier / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    # En-têtes Netlify : pas de référencement, et des pages toujours à jour (pas de vieille copie en cache)
    (dossier / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n", encoding="utf-8")
    _ajouter_compteurs(dossier, goatcounter, umami)
    return dossier


def site_github(site, dossier, mot_de_passe, mot_de_passe_club="", goatcounter="", umami=""):
    """Site GitHub à publier : le site (pages chiffrées avec le mot de passe du site) et, en plus,
    l'espace club dans club/ (même page et même mot de passe que sur Netlify), soit
    https://ggman23.github.io/ggping/club/ : GitHub Pages ne compte pas les mises en ligne."""
    if dossier.exists():
        shutil.rmtree(dossier)
    shutil.copytree(site, dossier)
    if not mot_de_passe_club:
        print("::warning::Pas de secret MOT_DE_PASSE_CLUB : pas d'espace club sur le site GitHub.")
        return dossier
    try:
        espace_club(site, dossier / "club", publier.cle(mot_de_passe), publier.cle(mot_de_passe_club))
    except Exception as e:  # le site GitHub doit partir quand même, sans l'espace club
        shutil.rmtree(dossier / "club", ignore_errors=True)
        print(f"::warning::Espace club non ajouté au site GitHub : {e}")
        return dossier
    page = dossier / "club" / "index.html"
    if umami:  # script d'Umami servi par le site, à côté de la page (le site GitHub est sous /ggping/)
        (dossier / "club" / UMAMI_PUBLIE).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(UMAMI_JS, dossier / "club" / UMAMI_PUBLIE)
    page.write_text(avec_compteurs(page.read_text(encoding="utf-8"), goatcounter, umami, True, UMAMI_PUBLIE),
                    encoding="utf-8")
    a_part = publier_pages_a_part(site, dossier, publier.cle(mot_de_passe), publier.cle(mot_de_passe_club))
    for chemin in ressources.publier_espaces(dossier, publier.cle(mot_de_passe_club)) + a_part:  # ex. /ggping/lundi/
        page = dossier / chemin / "index.html"
        page.write_text(avec_compteurs(page.read_text(encoding="utf-8"), goatcounter, umami, False,
                                       "../club/" + UMAMI_PUBLIE), encoding="utf-8")
    return dossier


# Garde-fou : sur l'offre gratuite, Netlify met le site en pause quand les 300 crédits du mois sont
# épuisés (« Site not available » jusqu'au cycle suivant). L'outil compte donc les mises en ligne du
# cycle en cours (15 crédits chacune) et n'envoie plus rien sur Netlify à partir de LIMITE_ENVOIS
# (18 = 270 crédits, la marge couvre le trafic) ; un envoi forcé passe jusqu'à PLAFOND_ENVOIS (19).
JOUR_CYCLE = 6  # le cycle de facturation du compte repart le 6 du mois
LIMITE_ENVOIS, PLAFOND_ENVOIS = 18, 19


def debut_cycle(maintenant, jour=JOUR_CYCLE):
    """Début (UTC) du cycle de crédits Netlify en cours."""
    debut = maintenant.replace(day=jour, hour=0, minute=0, second=0, microsecond=0)
    if maintenant.day < jour:
        debut = (debut.replace(day=1) - timedelta(days=1)).replace(day=jour)
    return debut


def envois_du_cycle(jeton, site, maintenant=None, jour=JOUR_CYCLE):
    """Nombre de mises en ligne (production, réussies) du site depuis le début du cycle."""
    maintenant = maintenant or datetime.now(timezone.utc)
    debut = debut_cycle(maintenant, jour)
    entetes, nb = {"Authorization": f"Bearer {jeton}"}, 0
    for page in range(1, 20):
        r = requests.get(f"{API}/sites/{site}/deploys", params={"page": page, "per_page": 100}, headers=entetes, timeout=60)
        r.raise_for_status()
        liste = r.json()
        for d in liste:
            quand = datetime.fromisoformat((d.get("created_at") or "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
            if quand >= debut and d.get("state") == "ready" and d.get("context", "production") == "production":
                nb += 1
        if len(liste) < 100 or not liste or datetime.fromisoformat(
                (liste[-1].get("created_at") or "1970-01-01T00:00:00Z").replace("Z", "+00:00")) < debut:
            break
    return nb


# Empreinte du contenu publié, sans les dates de génération : une copie identique n'est pas renvoyée.
# Netlify (offre gratuite) décompte 15 crédits par mise en ligne, quel que soit ce qui a changé ;
# les mises à jour automatiques sans résultat nouveau ne coûtent donc plus rien.
SIGNATURE = "signature.txt"
GENERE_LE = re.compile(r'"genere_le": "[^"]*"')


def signature_contenu(site, mot_de_passe, reglages=()):
    """Empreinte de ce que montre la copie Netlify : pages déchiffrées (sans leur date de génération),
    bilans des vérifications, noms des fichiers, archives, surnoms et images du dossier import, rubriques
    de l'espace club (dossier ressources), code
    de l'outil et réglages (mots de passe, compteurs). Deux mises à jour sans rien de nouveau donnent
    la même empreinte. Les images et l'Excel ne sont pas lus : ils découlent des mêmes données."""
    h = hashlib.sha256()
    cle_site = publier.cle(mot_de_passe)
    etat = json.loads((site / "etat.json").read_text(encoding="utf-8"))
    for nom in etat.get("fichiers", []):
        h.update(nom.encode("utf-8") + b"\0")
    for nom, page in sorted(etat.get("pages", {}).items()):
        h.update(f"{nom}\0{page.get('verification', '')}\0".encode("utf-8"))
        m = CHIFFRE.search((site / nom).read_text(encoding="utf-8")) if nom.endswith(".html") and (site / nom).exists() else None
        if m:
            h.update(GENERE_LE.sub("", publier.dechiffrer(base64.b64decode(m[1]), cle_site).decode("utf-8")).encode("utf-8"))
    archives = {cle: a.get("signature") or a.get("cree_le") for cle, a in etat.get("archives", {}).items()}
    h.update(json.dumps(archives, sort_keys=True).encode("utf-8"))
    h.update(os.environ.get("SURNOMS", "").encode("utf-8"))
    for dossier, garder in ((RACINE / "import", lambda f: f.name.lower().startswith(("photo_", "logo_", "surnoms"))),
                            (Path(__file__).parent, lambda f: "__pycache__" not in f.parts),
                            (ressources.DOSSIER, lambda f: True)):
        for f in sorted(dossier.rglob("*")) if dossier.is_dir() else []:
            if f.is_file() and garder(f):
                h.update(f.name.encode("utf-8") + b"\0" + f.read_bytes())
    for r in reglages:
        h.update(hashlib.sha256((r or "").encode("utf-8")).digest())
    # Publiée sur le site : chiffrée avec la clé du site (rien ne se devine à partir d'elle)
    return hmac.new(cle_site, h.digest(), hashlib.sha256).hexdigest()


def signature_en_ligne(site_netlify):
    """Empreinte de la copie actuellement en ligne ; None si on ne peut pas la lire."""
    try:
        r = requests.get(f"https://{site_netlify}/{SIGNATURE}", params={"t": int(time.time())}, timeout=30)
        return r.text.strip() if r.ok else None
    except requests.RequestException:
        return None


def deployer(dossier, jeton, site=SITE_PAR_DEFAUT, attente=180):
    """Envoie le site sur Netlify par empreintes : Netlify ne demande que les fichiers qu'il n'a pas
    déjà (les archives, qui ne changent plus, ne repartent pas à chaque fois). Attend qu'il soit en
    ligne et renvoie son adresse."""
    entetes = {"Authorization": f"Bearer {jeton}"}
    fichiers = {"/" + f.relative_to(dossier).as_posix(): f for f in sorted(dossier.rglob("*")) if f.is_file()}
    empreintes = {chemin: hashlib.sha1(f.read_bytes()).hexdigest() for chemin, f in fichiers.items()}
    r = requests.post(f"{API}/sites/{site}/deploys", json={"files": empreintes}, headers=entetes, timeout=120)
    if r.status_code == 401:
        raise ErreurNetlify("jeton Netlify refusé (expiré ou mal copié) : refaire le secret NETLIFY_AUTH_TOKEN")
    if r.status_code in (403, 404):
        raise ErreurNetlify(f"site Netlify « {site} » introuvable pour ce jeton : vérifier son nom "
                            "(variable NETLIFY_SITE) et que le jeton est celui du compte qui possède le site")
    if not r.ok:
        raise ErreurNetlify(f"Netlify a répondu {r.status_code} : {r.text[:300]}")
    deploiement = r.json()
    demandes, envoyes = set(deploiement.get("required") or []), 0
    for chemin, f in fichiers.items():
        if empreintes[chemin] not in demandes:
            continue
        demandes.discard(empreintes[chemin])  # deux fichiers identiques : un seul envoi
        rf = requests.put(f"{API}/deploys/{deploiement['id']}/files{quote(chemin)}", data=f.read_bytes(), timeout=300,
                          headers={**entetes, "Content-Type": "application/octet-stream"})
        if not rf.ok:
            raise ErreurNetlify(f"envoi de {chemin} refusé par Netlify ({rf.status_code})")
        envoyes += 1
    print(f"Netlify : {envoyes} fichier(s) envoyé(s) sur {len(fichiers)} (les autres n'ont pas changé)", flush=True)
    fin = time.time() + attente
    while deploiement.get("state") not in ("ready", "error") and time.time() < fin:
        time.sleep(3)
        deploiement = requests.get(f"{API}/deploys/{deploiement['id']}", headers=entetes, timeout=60).json()
    if deploiement.get("state") == "error":
        raise ErreurNetlify(f"Netlify n'a pas pu publier le site : {deploiement.get('error_message')}")
    return deploiement.get("ssl_url") or deploiement.get("url") or f"https://{site}"


def main():
    parser = argparse.ArgumentParser(description="Copie de secours du site sur Netlify (et Cloudflare Pages)")
    parser.add_argument("--site", default=str(RACINE / "site"), help="site GitHub déjà construit")
    parser.add_argument("--dossier", default=str(RACINE / "site-netlify"), help="dossier préparé pour Netlify")
    parser.add_argument("--github", metavar="DOSSIER",
                        help="préparer seulement le site GitHub à publier (site + espace club dans club/)")
    args = parser.parse_args()
    if args.github:
        umami = code_umami(os.environ.get("UMAMI", ""))
        dossier = site_github(Path(args.site), Path(args.github), os.environ.get("MOT_DE_PASSE_SITE", ""),
                              os.environ.get("MOT_DE_PASSE_CLUB", ""), code_goatcounter(os.environ.get("GOATCOUNTER", "")), umami)
        if (dossier / "club" / "index.html").exists():
            print("Espace club sur le site GitHub : https://ggman23.github.io/ggping/club/ (mot de passe du club)")
        return
    jeton = os.environ.get("NETLIFY_AUTH_TOKEN", "")
    nom = os.environ.get("NETLIFY_SITE") or SITE_PAR_DEFAUT
    if not (Path(args.site) / "etat.json").exists():
        print("Site GitHub pas encore construit : pas de copie Netlify ni Cloudflare."
              + ("" if jeton else " (Netlify : pas de jeton, secret NETLIFY_AUTH_TOKEN.)"))
        return
    mot_de_passe_gg = os.environ.get("MOT_DE_PASSE_GG", "")
    mot_de_passe_club = os.environ.get("MOT_DE_PASSE_CLUB", "")
    for secret, valeur, partie in (("MOT_DE_PASSE_CLUB", mot_de_passe_club, "/club/"), ("MOT_DE_PASSE_GG", mot_de_passe_gg, "/gg/")):
        if not valeur:
            print(f"::warning::Pas de secret {secret} : {partie} n'est pas publié sur Netlify.")
    goatcounter = code_goatcounter(os.environ.get("GOATCOUNTER", ""))
    if os.environ.get("GOATCOUNTER", "").strip() and not goatcounter:
        print("::warning::Variable GOATCOUNTER illisible (attendu : le code du compte, par exemple cvtt-vaires) : pas de statistiques.")
    umami = code_umami(os.environ.get("UMAMI", ""))
    if os.environ.get("UMAMI", "").strip() and not umami:
        print("::warning::Variable UMAMI illisible (attendu : l'identifiant du site, data-website-id) : pas de statistiques Umami.")
    mot_de_passe = os.environ.get("MOT_DE_PASSE_SITE", "")
    try:
        # La copie est toujours préparée : elle sert aussi à Cloudflare Pages (étape suivante du workflow)
        dossier = construire(Path(args.site), Path(args.dossier), mot_de_passe,
                             mot_de_passe_gg, mot_de_passe_club, goatcounter, umami)
        signature = signature_contenu(Path(args.site), mot_de_passe,
                                      (mot_de_passe_gg, mot_de_passe_club, goatcounter, umami))
        (dossier / SIGNATURE).write_text(signature + "\n", encoding="utf-8")
        if not jeton:
            print("Netlify : pas de jeton (secret NETLIFY_AUTH_TOKEN), copie non envoyée. Voir PUBLICATION.md.")
            return
        if os.environ.get("NETLIFY_ENVOI", "true").lower() not in ("1", "true", "oui"):
            print("Netlify : pas demandé (mise à jour de GitHub et Cloudflare seulement) : la copie Netlify reste "
                  "telle quelle, aucun crédit dépensé.")
            return
        forcer = os.environ.get("FORCER_NETLIFY", "").lower() in ("1", "true", "oui")
        if not forcer and signature_en_ligne(nom) == signature:
            print("Netlify : rien de nouveau depuis la copie en ligne (mêmes résultats, mêmes pages) : "
                  "pas d'envoi, 15 crédits Netlify économisés.")
            return
        try:
            deja = envois_du_cycle(jeton, nom)
        except (requests.RequestException, ValueError) as e:
            print(f"::warning::Netlify : mises en ligne du mois non comptées ({e}) : envoi quand même.")
            deja = 0
        limite = PLAFOND_ENVOIS if forcer else LIMITE_ENVOIS
        if deja >= limite:
            print(f"::warning::Netlify : déjà {deja} mises en ligne depuis le {debut_cycle(datetime.now(timezone.utc)):%d/%m} "
                  f"({deja * 15} crédits sur 300). Plus d'envoi jusqu'au {JOUR_CYCLE} du mois prochain, pour que "
                  "Netlify ne mette pas le site en pause. Le site GitHub et Cloudflare Pages sont à jour.")
            return
        print(f"Netlify : {deja} mise(s) en ligne ce mois-ci avant celle-ci ({(deja + 1) * 15} crédits sur 300 après).")
        adresse = deployer(dossier, jeton, nom)
    except (ErreurNetlify, requests.RequestException, ValueError) as e:
        # Le site GitHub est déjà publié : la copie Netlify en échec est signalée sans tout faire échouer.
        print(f"::warning::Copie Netlify non publiée : {e}")
        sys.exit(0)
    base = adresse.rstrip("/")
    print(f"Copie Netlify publiée : {base}/ (accueil public)"
          + (f", {base}/club/ (mot de passe du club)" if mot_de_passe_club else "")
          + (f", {base}/gg/ (mot de passe de /gg/)" if mot_de_passe_gg else ""))
    if goatcounter:
        print(f"Statistiques de visite : https://{goatcounter}.goatcounter.com")
    else:
        print("Statistiques de visite : désactivées (pas de variable ni de secret GOATCOUNTER dans Settings > "
              "Secrets and variables > Actions).")
    if umami:
        print("Statistiques Umami : https://cloud.umami.is (site CVTT Vaires)")


if __name__ == "__main__":
    main()

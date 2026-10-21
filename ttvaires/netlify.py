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
from pathlib import Path
from urllib.parse import quote

import requests

from . import publier

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
              "classements_vaires.html", "effectif_vaires.html", "classement_virtuel.html"]


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
        if not (site / publie).exists():
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
    donnees = {"maj": (etat.get("derniere_maj") or {}).get("fin"), "sel": publier.SEL, "iterations": publier.ITERATIONS,
               "documents": documents, "archives": archives}
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
  const espace = /^\\/club\\b/.test(location.pathname) ? "club" : /^\\/gg\\b/.test(location.pathname) ? "gg" : "accueil";
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


def avec_compteurs(html, goatcounter="", umami="", manuel=False):
    """Ajoute les compteurs de visites configurés avant </head>. `manuel` : la page compte elle-même
    ce qu'on y fait (compter() de l'espace club et des accueils) ; sinon une page vue par chargement.
    Le chemin compté ne garde pas le « ?v=... » des liens."""
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
        balises.append(f'<script defer src="/{UMAMI_PUBLIE}" data-website-id="{umami}"{reglages} data-exclude-search="true"'
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
    for page, manuel in [(dossier / "index.html", False), (dossier / "club" / "index.html", True),
                         *((f, True) for f in sorted((dossier / "gg").rglob("index.html")))]:
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
    (dossier / "index.html").write_text(page_publique(site, mot_de_passe), encoding="utf-8")
    (dossier / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    # En-têtes Netlify : pas de référencement, et des pages toujours à jour (pas de vieille copie en cache)
    (dossier / "_headers").write_text("/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-cache\n", encoding="utf-8")
    _ajouter_compteurs(dossier, goatcounter, umami)
    return dossier


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
    parser = argparse.ArgumentParser(description="Copie de secours du site sur Netlify")
    parser.add_argument("--site", default=str(RACINE / "site"), help="site GitHub déjà construit")
    parser.add_argument("--dossier", default=str(RACINE / "site-netlify"), help="dossier préparé pour Netlify")
    args = parser.parse_args()
    jeton = os.environ.get("NETLIFY_AUTH_TOKEN", "")
    if not jeton:
        print("Netlify : pas de jeton (secret NETLIFY_AUTH_TOKEN), copie non envoyée. Voir PUBLICATION.md.")
        return
    nom = os.environ.get("NETLIFY_SITE") or SITE_PAR_DEFAUT
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
    try:
        dossier = construire(Path(args.site), Path(args.dossier), os.environ.get("MOT_DE_PASSE_SITE", ""),
                             mot_de_passe_gg, mot_de_passe_club, goatcounter, umami)
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

"""Génération de la page HTML statique (un seul fichier, consultable hors ligne)."""

import json
from pathlib import Path

GABARIT = Path(__file__).with_name("gabarit.html")
GABARIT_RESULTATS = Path(__file__).with_name("gabarit_resultats.html")
GABARIT_RENCONTRES = Path(__file__).with_name("gabarit_rencontres.html")
GABARIT_EFFECTIF = Path(__file__).with_name("gabarit_effectif.html")
GABARIT_VIRTUEL = Path(__file__).with_name("gabarit_virtuel.html")
GABARIT_CLASSEMENTS = Path(__file__).with_name("gabarit_classements.html")
GABARIT_INDIVS = Path(__file__).with_name("gabarit_indivs.html")
GABARIT_PROGRESSION = Path(__file__).with_name("gabarit_progression.html")
GABARIT_FICHES = Path(__file__).with_name("gabarit_fiches.html")
GABARIT_77 = Path(__file__).with_name("gabarit_77.html")


CHAMPIONNATS = {"france": "Championnat de France", "paris": "Championnat de Paris", "jeunes": "Championnat des jeunes"}

# Sélecteur de championnat en haut d'une page (résultats, feuilles de match, classements, effectif) : la page a les
# données de chaque championnat (<script id="donnees-paris">...) ; le choix (adresse #paris, #paris/seule/v2...) met
# celles du championnat choisi à la place de <script id="donnees">, avant que la page ne les lise.
SELECTEUR = """<script>
(function () {
  var NOMS = %(noms)s, DISPO = %(dispo)s;
  var m = /^#(france|paris|jeunes)(?:\\/(.*))?$/.exec(location.hash);
  var choix = m && DISPO.indexOf(m[1]) >= 0 ? m[1] : "france";
  var absent = m && DISPO.indexOf(m[1]) < 0 ? NOMS[m[1]] : "";  // demandé, mais pas (encore) dans cette page
  if (m) { try { history.replaceState(null, "", "#" + (m[2] || "")); } catch (e) { /* adresse gardée */ } }
  if (choix !== "france") document.getElementById("donnees").textContent = document.getElementById("donnees-" + choix).textContent;
  window.CVTT_CHAMPIONNAT = choix;
  function barre() {
    var st = document.createElement("style");
    st.textContent = ".cvtt-champ{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;padding:8px 10px;background:#0f2740;position:relative;z-index:50}"
      + ".cvtt-champ a{color:#fff;text-decoration:none;border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:6px 14px;font:600 14px system-ui,sans-serif}"
      + ".cvtt-champ a[aria-current]{background:#d9a521;border-color:#d9a521;color:#1d1500}";
    document.head.appendChild(st);
    var b = document.createElement("nav");
    b.className = "cvtt-champ";
    b.setAttribute("aria-label", "Championnat");
    b.innerHTML = DISPO.map(function (c) { return '<a href="#' + c + '"' + (c === choix ? ' aria-current="page"' : "") + ">" + NOMS[c] + "</a>"; }).join("");
    b.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a) return;
      e.preventDefault();
      location.hash = a.getAttribute("href").slice(1);
      location.reload();
    });
    document.body.insertBefore(b, document.body.firstChild);
    if (absent) b.insertAdjacentHTML("afterend", '<p style="margin:10px;padding:9px 12px;border-radius:10px;background:#fff4d6;color:#6b4500;font:14px system-ui,sans-serif">'
      + absent + " : pas encore de données dans cette page (elles arrivent avec la prochaine mise à jour). Ci-dessous : le Championnat de France.</p>");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", barre); else barre();
})();
</script>"""


def _json(donnees):
    # "<" échappé pour que le JSON ne puisse jamais fermer la balise <script>.
    return json.dumps(donnees, ensure_ascii=False).replace("<", "\\u003c")


def generer_html(donnees, chemin, gabarit=GABARIT, autres=None):
    """Écrit la page HTML avec les données intégrées et renvoie son chemin. `autres` : {"paris": données, ...} :
    les mêmes données pour d'autres championnats, avec le sélecteur en haut de la page (gabarits qui lisent
    <script id="donnees">)."""
    js = _json(donnees)
    html = Path(gabarit).read_text(encoding="utf-8").replace("__DONNEES_JSON__", js)
    autres = {k: v for k, v in (autres or {}).items() if v}
    if autres:
        balise = '<script id="donnees" type="application/json">'
        debut = html.index(balise)
        fin = html.index("</script>", debut) + len("</script>")
        ajout = "".join(f'\n<script id="donnees-{k}" type="application/json">{_json(v)}</script>' for k, v in autres.items())
        ajout += "\n" + SELECTEUR % {"noms": json.dumps(CHAMPIONNATS, ensure_ascii=False),
                                     "dispo": json.dumps(["france", *[k for k in CHAMPIONNATS if k in autres]])}
        html = html[:fin] + ajout + html[fin:]
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(html, encoding="utf-8")
    return chemin

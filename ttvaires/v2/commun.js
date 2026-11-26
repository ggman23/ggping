/* CVTT Vaires, version 2 : code commun à toutes les pages.
   Données : v2/donnees/<nom>.json.chiffre, chiffrées avec la clé du club (même mot de passe et même clé
   mémorisée que /club/). Aucune donnée n'est dans les pages elles-mêmes. */
"use strict";
const V2 = (() => {
  const SEL = "__SEL__", ITERATIONS = __ITERATIONS__, MAJ = "__MAJ__", VERSION = "__VERSION__";
  const CLE = "cvtt-vaires-cle-club";  // la clé de /club/ : un membre connecté à l'espace club l'est ici aussi
  const RACINE = document.documentElement.dataset.racine || "./";
  const PAGE = document.documentElement.dataset.page || "accueil";
  const $ = (s, r = document) => r.querySelector(s);
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const lire = (k, s = localStorage) => { try { return s.getItem(k); } catch (e) { return null; } };
  const ecrire = (k, v, s = localStorage) => { try { v == null ? s.removeItem(k) : s.setItem(k, v); } catch (e) { /* navigation privée */ } };

  /* ---------- Réglages de l'appareil (taille du texte, thème), appliqués avant tout affichage ---------- */
  const R = { moi: "cvtt-v2-moi", taille: "cvtt-v2-taille", theme: "cvtt-v2-theme", admin: "cvtt-v2-admin",
              visite: "cvtt-v2-visite", precedente: "cvtt-v2-precedente", dernier: "cvtt-v2-dernier" };
  const appliquer = () => {
    const t = lire(R.taille), th = lire(R.theme);
    t ? document.documentElement.dataset.taille = t : delete document.documentElement.dataset.taille;
    th ? document.documentElement.dataset.theme = th : delete document.documentElement.dataset.theme;
  };
  appliquer();

  /* ---------- Dates parlantes ---------- */
  const JOURS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];
  const MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"];
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const AUJ = (() => { const q = new URLSearchParams(location.search).get("date"); return /^\d{4}-\d{2}-\d{2}$/.test(q || "") ? q : iso(new Date()); })();
  const enDate = (s) => { const [a, m, j] = s.slice(0, 10).split("-").map(Number); return new Date(a, m - 1, j); };
  const ecart = (s) => Math.round((enDate(s) - enDate(AUJ)) / 864e5);
  const MOIS_C = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."];
  const dateCourte = (s) => { const d = enDate(s); return `${JOURS[d.getDay()].slice(0, 3)}. ${d.getDate()} ${MOIS_C[d.getMonth()]}`; };
  const dateLongue = (s) => { const d = enDate(s); return `${JOURS[d.getDay()]} ${d.getDate()} ${MOIS[d.getMonth()]}${d.getFullYear() !== enDate(AUJ).getFullYear() ? " " + d.getFullYear() : ""}`; };
  const relatif = (s) => {
    const n = ecart(s);
    if (n === 0) return "aujourd'hui";
    if (n === 1) return "demain";
    if (n === -1) return "hier";
    if (n > 1 && n < 7) return JOURS[enDate(s).getDay()];
    if (n >= 7 && n < 14) return `${JOURS[enDate(s).getDay()]} prochain`;
    if (n >= 14) return `dans ${n} jours`;
    return `il y a ${-n} jours`;
  };
  const heure = (h) => h ? h.replace(":", "h").replace(/h00$/, "h") : "";

  /* ---------- Déchiffrement ---------- */
  const octets = (b) => Uint8Array.from(atob(b), (c) => c.charCodeAt(0));
  const b64 = (o) => btoa(String.fromCharCode(...o));
  let cle = null;
  async function deriver(mdp) {
    const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(mdp), "PBKDF2", false, ["deriveBits"]);
    return new Uint8Array(await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: new TextEncoder().encode(SEL), iterations: ITERATIONS }, base, 256));
  }
  async function ouvrir(brut, k = cle) {
    const cleAes = await crypto.subtle.importKey("raw", k, "AES-GCM", false, ["decrypt"]);
    const clair = await crypto.subtle.decrypt({ name: "AES-GCM", iv: brut.slice(0, 12) }, cleAes, brut.slice(12));
    return new Uint8Array(await new Response(new Blob([clair]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer());
  }
  async function brut(chemin) {
    const r = await fetch(`${chemin}?v=${encodeURIComponent(MAJ || VERSION)}`);
    if (!r.ok) throw new Error(`fichier introuvable (${r.status})`);
    return new Uint8Array(await r.arrayBuffer());
  }
  const memoire = {};
  function donnees(nom) {  // données de la v2 : promesse gardée (un seul téléchargement par page)
    if (!memoire[nom]) memoire[nom] = brut(`${RACINE}donnees/${nom}.json.chiffre`).then((b) => ouvrir(b))
      .then((o) => JSON.parse(new TextDecoder().decode(o))).catch((e) => { delete memoire[nom]; throw e; });
    return memoire[nom];
  }
  const facultatif = (nom) => donnees(nom).catch(() => null);
  const TYPES = { html: "text/html;charset=utf-8", png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", pdf: "application/pdf",
                  xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" };
  async function fichierClub(chemin, nom) {  // un document de /club/ (déjà chiffré avec la clé du club)
    const type = TYPES[(nom || chemin).replace(/\.chiffre$/, "").split(".").pop()] || "application/octet-stream";
    return new Blob([await ouvrir(await brut(`${RACINE}../club/${chemin.split("/").map(encodeURIComponent).join("/")}`))], { type });
  }

  /* ---------- Pictogrammes ---------- */
  const I = {
    accueil: '<path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10v9.5h13V10"/><path d="M10 19.5v-5h4v5"/>',
    equipes: '<path d="M12 3 4.5 6v5.5c0 4.6 3.1 8 7.5 9.5 4.4-1.5 7.5-4.9 7.5-9.5V6z"/><path d="M9 12l2 2 4-4"/>',
    joueurs: '<circle cx="12" cy="8" r="3.6"/><path d="M4.5 20.5c.8-4 3.8-6 7.5-6s6.7 2 7.5 6"/>',
    agenda: '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    club: '<path d="M3.5 7.5A2 2 0 0 1 5.5 5.5h4l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
    recherche: '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.2-4.2"/>',
    reglages: '<circle cx="12" cy="12" r="3"/><path d="M12 2.5v3M12 18.5v3M21.5 12h-3M5.5 12h-3M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1M18.7 18.7l-2.1-2.1M7.4 7.4 5.3 5.3"/>',
    retour: '<path d="M15 5 8 12l7 7"/>',
    carte: '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
    telecharger: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    partager: '<circle cx="18" cy="5.5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="18.5" r="2.5"/><path d="m8.2 10.8 7.6-4M8.2 13.2l7.6 4"/>',
    etoile: '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 17l-5.2 2.7 1-5.9L3.5 9.7l5.9-.8z"/>',
    page: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    image: '<rect x="3.5" y="4.5" width="17" height="15" rx="2.5"/><circle cx="9" cy="10" r="1.8"/><path d="m20.5 16-5-5-9 8.5"/>',
    externe: '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 19V7.5A1.5 1.5 0 0 1 5.5 6H10"/>',
  };
  const PICTOS = {  // une forme par compétition, pleine (comme l'image du programme)
    france: '<path fill="currentColor" stroke="none" stroke-linejoin="round" d="M10.6 2.2l2.3 1.6 3.4.9 2.2 2.6 2.3 1.2-.9 2.6.7 3.1-1.6 1.9.5 3.3-2.8 1.3-3.4-.3-1.9 1.9-2.4-1-3-.1-1.7-2.2 1-3.2-2.3-2.4.3-2.6-1.9-2.5 2.8-.7 2.8-1.7z"/>',
    femmes: '<circle cx="12" cy="9" r="4.6" fill="currentColor" stroke="none"/><path fill="currentColor" stroke="none" d="M6.2 10.5c-.6 3.4.3 6 1.6 7.6h8.4c1.3-1.6 2.2-4.2 1.6-7.6-1 3-2.8 4.4-5.8 4.4s-4.8-1.4-5.8-4.4z"/><path fill="currentColor" stroke="none" d="M5.5 21.5c.9-2.4 3.4-3.7 6.5-3.7s5.6 1.3 6.5 3.7z"/>',
    paris: '<path fill="currentColor" stroke="none" d="M11.3 2h1.4l.4 4h-2.2zM10.6 6.5h2.8l1 5.5h-4.8zM9.5 12.5h5l1.2 3h-7.4zM7.7 16h8.6l2.2 6h-3.3c-.6-2.2-1.7-3.4-3.2-3.4S9.4 19.8 8.8 22H5.5z"/>',
    jeunes: '<circle cx="12" cy="5.6" r="2.9" fill="currentColor" stroke="none"/><path fill="currentColor" stroke="none" d="M4.2 4.5 6 3.6l3.3 4.9h5.4L18 3.6l1.8.9-3.6 6.2v4.1l1.7 6.7h-2.6L13.6 15h-3.2l-1.7 6.5H6.1l1.7-6.7v-4.1z"/>',
  };
  const svg = (nom, plein = false) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${plein ? PICTOS[nom] : I[nom]}</svg>`;
  const COMPET = {
    france: { nom: "Championnat de France", court: "France", ordre: 0 },
    femmes: { nom: "Championnat féminin", court: "Femmes", ordre: 1 },
    paris: { nom: "Championnat de Paris", court: "Paris", ordre: 2 },
    jeunes: { nom: "Championnat des jeunes", court: "Jeunes", ordre: 3 },
  };

  /* ---------- Toutes les équipes de Vaires, dans un même format ---------- */
  const joli = (n) => String(n || "").toLowerCase().replace(/(^|[\s'’(/-])([a-zà-ÿ])/g, (m, a, b) => a + b.toUpperCase())
    .replace(/\b(Tt|Ctt|Us|Sp|Ja|Ap|Ep|Se|Cs|As|Astt|Asc|Es|Fc|Ttc|Cvtt|Ttm|Cttb|Uste|Usm|Esm|Ast)\b/g, (m) => m.toUpperCase())
    .replace(/\bS\/M\b/gi, "s/M").replace(/\bSt\b/g, "St").replace(/\b(Le|La|Les|De|Du|Des|Sur|Sous)\b(?!$)/g, (m) => m.toLowerCase())
    .replace(/^(le|la|les)\b/, (m) => m[0].toUpperCase() + m.slice(1));
  const clefFeuille = (numero, feminine, journee) => `${numero}-${feminine ? "F" : "M"}-${journee}`;
  let _equipes = null;
  async function equipes() {
    if (_equipes) return _equipes;
    const [fr, pa, je, fe] = await Promise.all(["france", "paris", "jeunes", "rencontres"].map(facultatif));
    const feuilles = {};
    for (const r of fe?.rencontres || []) feuilles[clefFeuille(r.numero, r.feminine, r.journee)] = r;
    const liste = [];
    const ajouter = (src, e, comp) => {
      const num = src.club?.numero;
      const t = { cle: `${comp}-${e.numero}`, comp, nom: e.nom_court || e.libelle, numero: e.numero, division: e.division,
                  poule: e.poule, age: e.age, source: src, brut: e, classement: (e.classement || []).map((l) => ({ ...l, nous: l.club === num })) };
      t.rencontres = (e.rencontres || []).map((r) => {
        const s = r.score, dom = !!r.vaires_domicile, f = comp === "france" || comp === "femmes" ? feuilles[clefFeuille(e.numero, comp === "femmes", r.journee)] : null;
        const parties = f?.score && f.parties?.length ? f.score : null;  // score en parties (feuille de match), nous d'abord
        const points = s ? (dom ? [s[0], s[1]] : [s[1], s[0]]) : null;
        const score = parties || points;
        const adv = r.adversaire;
        return { equipe: t, journee: r.journee, date: (r.date_reelle || r.date || "").slice(0, 10), heure: r.heure, domicile: dom,
                 adversaire: adv ? joli(adv.libelle) : null, advBrut: adv?.libelle, advClub: adv?.club, advNumero: adv?.numero,
                 exempt: !adv, score, issue: score ? (score[0] > score[1] ? "v" : score[0] < score[1] ? "d" : "n") : null,
                 feuille: f || null, analyse: r.analyse || null, salleNom: r.salle?.nom };
      });
      const moi = t.classement.find((l) => l.nous);
      t.rang = moi?.rang ?? null; t.points = moi?.points ?? null; t.nbEquipes = t.classement.length;
      liste.push(t);
    };
    for (const e of fr?.equipes || []) ajouter(fr, e, e.championnat === "F" ? "femmes" : "france");
    for (const e of pa?.equipes || []) ajouter(pa, e, "paris");
    for (const e of je?.equipes || []) ajouter(je, e, "jeunes");
    liste.sort((a, b) => COMPET[a.comp].ordre - COMPET[b.comp].ordre || a.numero - b.numero);
    _equipes = liste;
    return liste;
  }
  const rencontres = (liste) => liste.flatMap((t) => t.rencontres).sort((a, b) => a.date.localeCompare(b.date)
    || COMPET[a.equipe.comp].ordre - COMPET[b.equipe.comp].ordre || a.equipe.numero - b.equipe.numero);
  const aVenir = (r) => !r.score && r.date >= AUJ;
  const lienRencontre = (r) => `${RACINE}rencontre/#${r.equipe.cle}/${r.journee}`;
  function salle(r) {  // adresse de la salle : la nôtre à domicile, celle du club adverse sinon
    const src = r.equipe.source;
    const s = r.domicile ? src.club?.salle : src.clubs?.[r.advClub]?.salle;
    if (!s) return null;
    const adresse = [s.adresse, [s.cp, s.ville].filter(Boolean).join(" ")].filter(Boolean).join(", ");
    return { nom: s.nom || r.salleNom, adresse, carte: s.carte };
  }

  /* ---------- Morceaux de page ---------- */
  function carteMatch(r, { avecDate = true, journee = false } = {}) {
    const t = r.equipe;
    const proche = Math.abs(ecart(r.date)) < 14;
    const quand = [avecDate ? (proche ? `${relatif(r.date)} · ${dateCourte(r.date)}` : dateCourte(r.date)) : `J${r.journee}`, heure(r.heure)].filter(Boolean).join(" · ");
    const droite = r.exempt ? '<span class="puce">exempt</span>'
      : r.score ? `<span class="score ${r.issue}">${r.score[0]}–${r.score[1]}</span><span class="puce ${r.domicile ? "dom" : "ext"}">${r.domicile ? "Domicile" : "Extérieur"}</span>`
      : `<span class="puce ${r.domicile ? "dom" : "ext"}">${r.domicile ? "Domicile" : "Extérieur"}</span>`;
    return `<a class="carte match ${t.comp}" href="${lienRencontre(r)}">
      <span class="picto">${svg(t.comp, true)}</span>
      <span class="quoi">${journee ? `<span class="equipe">Journée ${r.journee}</span>` : `<span class="equipe">${esc(t.nom)}</span> <span class="petit">· ${esc(COMPET[t.comp].court)}</span>`}
        <span class="contre">${r.exempt ? "Exempt" : (r.domicile ? "reçoit " : "chez ") + esc(r.adversaire)}</span>
        <span class="quand">${esc(quand)}</span></span>
      <span class="droite">${droite}</span></a>`;
  }
  function courbe(serie, { largeur = 300, hauteur = 70, couleur = "var(--accent)" } = {}) {
    const v = serie.filter((x) => x != null);
    if (v.length < 2) return "";
    const min = Math.min(...v), max = Math.max(...v), e = max - min || 1;
    const pts = serie.map((x, i) => x == null ? null : [i / (serie.length - 1) * (largeur - 8) + 4, hauteur - 6 - (x - min) / e * (hauteur - 12)]).filter(Boolean);
    const d = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    const [xd, yd] = pts[pts.length - 1];
    return `<svg class="courbe" viewBox="0 0 ${largeur} ${hauteur}" role="img" aria-label="courbe"><path d="${d} L${xd.toFixed(1)} ${hauteur} L${pts[0][0].toFixed(1)} ${hauteur}Z" fill="${couleur}" opacity=".1"/>
      <path d="${d}" fill="none" stroke="${couleur}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${xd}" cy="${yd}" r="4" fill="${couleur}"/></svg>`;
  }
  const nombre = (n) => n == null || n === "" ? "–" : Number(n).toLocaleString("fr-FR", { maximumFractionDigits: 1 });
  const signe = (n) => n > 0 ? `<span class="hausse">+${nombre(n)}</span>` : n < 0 ? `<span class="baisse">${nombre(n)}</span>` : "0";
  const squelettes = (n = 3) => Array.from({ length: n }, () => '<div class="squelette"></div>').join("");

  /* ---------- Joueurs de Vaires (classement virtuel + effectif) ---------- */
  let _joueurs = null;
  async function joueurs() {
    if (_joueurs) return _joueurs;
    const [vi, ef, pr] = await Promise.all(["virtuel", "effectif", "progression"].map(facultatif));
    const parId = {};
    for (const j of ef?.joueurs || []) parId[j.id] = { id: j.id, nom: j.nom, prenom: j.prenom, sexe: j.sexe, categorie: j.categorie_long || j.categorie,
      loisir: j.loisir, officiels: j.points_mensuels ?? j.points, classement: j.classement, habituelle: j.habituelle, effectif: j };
    for (const j of vi?.joueurs || []) parId[j.id] = { ...(parId[j.id] || { id: j.id, nom: j.nom, prenom: j.prenom, sexe: j.sexe, categorie: j.categorie }),
      officiels: j.officiels, virtuels: j.virtuels, classement: j.classement, classementVirtuel: j.classement_virtuel, equipe: j.equipe, v: j.v, d: j.d, virtuel: j };
    for (const j of pr?.joueurs || []) if (parId[j.id]) Object.assign(parId[j.id], { serie: j.serie, tendance: j.tendance });
    _joueurs = Object.values(parId).filter((j) => !j.loisir || j.virtuels != null)
      .map((j) => ({ ...j, nomComplet: `${j.prenom || ""} ${j.nom || ""}`.trim(), gain: j.virtuels != null && j.officiels != null ? j.virtuels - j.officiels : null }))
      .sort((a, b) => (b.virtuels ?? b.officiels ?? 0) - (a.virtuels ?? a.officiels ?? 0));
    return _joueurs;
  }
  const moi = () => lire(R.moi);

  /* ---------- Nouveautés depuis la dernière visite ---------- */
  (() => {  // une visite = plus de 30 minutes sans ouvrir la v2
    const maintenant = Date.now(), derniere = Number(lire(R.visite) || 0);
    if (!derniere || maintenant - derniere > 30 * 60e3) ecrire(R.precedente, String(derniere || maintenant));
    ecrire(R.visite, String(maintenant));
  })();
  const depuis = () => Number(lire(R.precedente) || Date.now());
  const estNouveau = (date) => date && new Date(date).getTime() > depuis();

  /* ---------- Sous-rubriques de chaque onglet (barre de segments en haut de la page) ---------- */
  const SOUS = {
    agenda: [["liste", "Agenda", "agenda/"], ["calendrier", "Calendrier", "agenda/#calendrier"], ["indivs", "Individuels", "indivs/"],
             ["tournois", "Tournois", "tournois/"]],
    equipes: [["vaires", "Équipes de Vaires", "equipes/"], ["clubs", "Clubs du 77", "77/"]],
    joueurs: [["vaires", "Joueurs de Vaires", "joueurs/"], ["77", "Tous les joueurs du 77", "77/#joueurs"]],
  };
  const sousNav = (rubrique, actif) => `<nav class="segments sous" aria-label="Sous-rubriques">${SOUS[rubrique].map(([c, n, l]) =>
    `<a href="${RACINE}${l}" class="${c === actif ? "actif" : ""}"${c === actif ? ' aria-current="page"' : ""}>${esc(n)}</a>`).join("")}</nav>`;

  /* ---------- Cadre de page : bandeau d'essai, barre du haut, onglets ---------- */
  const ONGLETS = [["accueil", "Accueil", ""], ["equipes", "Équipes", "equipes/"], ["joueurs", "Joueurs", "joueurs/"],
                   ["agenda", "Agenda", "agenda/"], ["club", "Club", "club/"]];
  function cadre({ titre, sous = "", retour = null } = {}) {
    document.title = titre ? `${titre} · CVTT Vaires` : "CVTT Vaires";
    const haut = `<div class="essai">Version 2 à l'essai · <a href="${RACINE}../club/">revenir au site actuel</a></div>
      <header class="haut">
        ${retour ? `<a class="bouton-haut" href="${retour}" aria-label="Retour">${svg("retour")}</a>`
                 : `<a class="logo" href="${RACINE}" aria-label="Accueil"><img src="${RACINE}icones/icone-192.png" alt=""></a>`}
        <h1>${esc(titre || "CVTT Vaires")}<span class="sous">${esc(sous)}</span></h1>
        <button type="button" id="v2-chercher" aria-label="Rechercher">${svg("recherche")}</button>
        <button type="button" id="v2-reglages" aria-label="Réglages">${svg("reglages")}</button>
      </header>
      <nav class="onglets" aria-label="Rubriques">${ONGLETS.map(([id, nom, lien]) =>
        `<a href="${RACINE}${lien}" class="${id === PAGE ? "actif" : ""}" ${id === PAGE ? 'aria-current="page"' : ""}>${svg(id)}<span>${nom}</span>${id === "club" ? '<span class="pastille" id="v2-nouveautes" hidden></span>' : ""}</a>`).join("")}</nav>`;
    document.body.insertAdjacentHTML("afterbegin", haut);
    $("#v2-chercher").addEventListener("click", recherche);
    $("#v2-reglages").addEventListener("click", reglages);
    facultatif("club").then((c) => {
      const n = (c?.documents || []).filter((d) => estNouveau(d.date)).length;
      if (n) { const p = $("#v2-nouveautes"); p.textContent = n > 9 ? "9+" : n; p.hidden = false; p.title = `${n} nouveauté(s) depuis ta dernière visite`; }
    });
  }
  const titre = (t, sous = "") => { const h = $(".haut h1"); if (h) h.innerHTML = `${esc(t)}<span class="sous">${esc(sous)}</span>`; document.title = `${t} · CVTT Vaires`; };

  /* ---------- Fenêtres ---------- */
  function fenetre(titreF, html) {
    const v = document.createElement("div");
    v.className = "voile";
    v.innerHTML = `<div class="fenetre apparait" role="dialog" aria-modal="true" aria-label="${esc(titreF)}"><div class="titre"><h2>${esc(titreF)}</h2>
      <button class="fermer" type="button" aria-label="Fermer">✕</button></div>${html}</div>`;
    const fermer = () => { v.remove(); document.removeEventListener("keydown", touche); };
    const touche = (e) => { if (e.key === "Escape") fermer(); };
    v.addEventListener("click", (e) => { if (e.target === v || e.target.closest(".fermer")) fermer(); });
    document.addEventListener("keydown", touche);
    document.body.append(v);
    return { racine: v, fermer };
  }
  const sansAccent = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  async function recherche() {
    const f = fenetre("Rechercher", `<input class="champ" type="search" id="v2-q" placeholder="Joueur, club, équipe, page…" autocomplete="off">
      <div id="v2-res" class="pile" style="margin-top:12px"></div>`);
    const q = $("#v2-q", f.racine), res = $("#v2-res", f.racine);
    q.focus();
    res.innerHTML = '<p class="petit">Chargement…</p>';
    const [eq, js, club, dep] = await Promise.all([equipes(), joueurs(), facultatif("club"), facultatif("departement")]);
    const index = [];
    for (const j of js) index.push({ t: j.nomComplet, s: `Joueur de Vaires · ${nombre(j.virtuels ?? j.officiels)} pts`, l: `${RACINE}joueurs/#${j.id}`, k: "joueurs" });
    for (const t of eq) index.push({ t: t.nom, s: `${COMPET[t.comp].nom} · ${t.division || ""}`, l: `${RACINE}equipes/#${t.cle}`, k: "equipes" });
    const vus = new Set();
    for (const r of rencontres(eq)) if (r.adversaire && !vus.has(r.equipe.cle + r.adversaire)) {
      vus.add(r.equipe.cle + r.adversaire);
      index.push({ t: r.adversaire, s: `Adversaire de ${r.equipe.nom} (${COMPET[r.equipe.comp].court}) · J${r.journee} ${dateCourte(r.date)}`, l: lienRencontre(r), k: "equipes" });
    }
    for (const d of club?.documents || []) if (d.type !== "image") index.push({ t: d.titre, s: "Page du site", l: `${RACINE}club/#doc/${encodeURIComponent(d.fichier)}`, k: "club" });
    for (const c of dep?.clubs || []) {  // clubs et joueurs du 77
      index.push({ t: joli(c.nom), s: `Club du 77 · ${c.joueurs.filter((j) => !j[3]).length} joueurs`, l: `${RACINE}77/#club/${c.numero}`, k: "equipes" });
      for (const j of c.joueurs) if (!j[3] && !c.vaires) index.push({ t: joli(j[4]), s: `${joli(c.nom)} · ${j[0]} pts`, l: `${RACINE}77/#joueurs/${encodeURIComponent(j[4])}`, k: "joueurs" });
    }
    const afficher = () => {
      const m = sansAccent(q.value.trim());
      if (m.length < 2) { res.innerHTML = '<p class="petit">Tape au moins deux lettres.</p>'; return; }
      const trouves = index.filter((x) => sansAccent(x.t).includes(m)).slice(0, 30);
      res.innerHTML = trouves.length ? `<div class="liste">${trouves.map((x) => `<a href="${x.l}">${svg(x.k)}<span class="grow"><span class="nom">${esc(x.t)}</span>
        <span class="petit" style="display:block">${esc(x.s)}</span></span></a>`).join("")}</div>` : '<p class="vide">Rien trouvé.</p>';
    };
    q.addEventListener("input", afficher);
    res.addEventListener("click", (e) => { if (e.target.closest("a")) f.fermer(); });
    afficher();
  }
  async function reglages() {
    const js = await joueurs().catch(() => []);
    const choix = (nom, valeurs, actuelle) => valeurs.map(([v, t]) => `<option value="${v}" ${v === (actuelle || "") ? "selected" : ""}>${t}</option>`).join("");
    const f = fenetre("Réglages", `
      <label class="reglage"><span>C'est moi (« Mon espace » à l'accueil)</span><select class="champ" id="r-moi"><option value="">— Personne —</option>
        ${js.slice().sort((a, b) => a.nomComplet.localeCompare(b.nomComplet, "fr")).map((j) => `<option value="${esc(j.id)}" ${j.id === moi() ? "selected" : ""}>${esc(j.nomComplet)}</option>`).join("")}</select>
        <span class="petit">Gardé seulement sur cet appareil : rien n'est envoyé.</span></label>
      <label class="reglage"><span>Taille du texte</span><select class="champ" id="r-taille">${choix("taille", [["", "Normale"], ["grand", "Grande"], ["tres-grand", "Très grande"]], lire(R.taille))}</select></label>
      <label class="reglage"><span>Apparence</span><select class="champ" id="r-theme">${choix("theme", [["", "Comme le téléphone"], ["clair", "Claire"], ["sombre", "Sombre"]], lire(R.theme))}</select></label>
      <label class="reglage" style="grid-template-columns:auto 1fr;align-items:center"><input type="checkbox" id="r-admin" ${lire(R.admin) ? "checked" : ""}>
        <span>Mode administrateur (mise à jour du site, /lundi/, statistiques)</span></label>
      <div class="boutons" style="margin-top:16px"><a class="bouton second" href="${RACINE}../club/">Site actuel</a><button class="bouton second" type="button" id="r-sortir">Se déconnecter</button></div>
      <p class="petit">Version ${esc(VERSION)} · données du ${MAJ ? esc(dateLongue(MAJ)) + " à " + esc(MAJ.slice(11, 16)) : "?"}</p>`);
    const r = f.racine;
    $("#r-moi", r).addEventListener("change", (e) => { ecrire(R.moi, e.target.value || null); location.reload(); });
    $("#r-taille", r).addEventListener("change", (e) => { ecrire(R.taille, e.target.value || null); appliquer(); });
    $("#r-theme", r).addEventListener("change", (e) => { ecrire(R.theme, e.target.value || null); appliquer(); });
    $("#r-admin", r).addEventListener("change", (e) => { ecrire(R.admin, e.target.checked ? "1" : null); location.reload(); });
    $("#r-sortir", r).addEventListener("click", () => { ecrire(CLE, null); ecrire(CLE, null, sessionStorage); location.reload(); });
  }

  /* ---------- Connexion (mot de passe du club) ---------- */
  async function connexion() {
    const c = lire(CLE) || lire(CLE, sessionStorage);
    if (c) {
      try { cle = octets(c); await verifier(cle); return; } catch (e) { cle = null; }
    }
    document.body.innerHTML = `<div class="connexion"><form id="v2-connexion"><img src="${RACINE}icones/icone-192.png" alt="">
      <h1>CVTT Vaires</h1><p>Version 2 du site, à l'essai. Entre le mot de passe du club.</p>
      <input class="champ" type="password" id="v2-mdp" autocomplete="current-password" placeholder="Mot de passe du club" required>
      <label><input type="checkbox" id="v2-retenir" checked> Se souvenir sur cet appareil</label>
      <button class="bouton" id="v2-entrer">Entrer</button><p class="erreur" id="v2-erreur" role="alert"></p></form></div>`;
    $("#v2-mdp").focus();
    await new Promise((fini) => $("#v2-connexion").addEventListener("submit", async (e) => {
      e.preventDefault();
      const b = $("#v2-entrer"); b.disabled = true; b.textContent = "Vérification…"; $("#v2-erreur").textContent = "";
      try {
        const k = await deriver($("#v2-mdp").value);
        await verifier(k);
        cle = k;
        ecrire(CLE, b64(k), $("#v2-retenir").checked ? localStorage : sessionStorage);
        document.body.innerHTML = "";
        fini();
      } catch (err) {
        $("#v2-erreur").textContent = "Mot de passe incorrect.";
        b.disabled = false; b.textContent = "Entrer";
      }
    }));
  }
  async function verifier(k) {
    const t = new TextDecoder().decode(await ouvrir(await brut(`${RACINE}donnees/verif.chiffre`), k));
    if (t !== "cvtt-vaires-club") throw new Error("vérification");
  }

  /* ---------- Démarrage d'une page ---------- */
  async function demarrer(options, rendu) {
    if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register(`${RACINE}sw.js`, { scope: RACINE }).catch(() => {});
    const corps = document.body.innerHTML;
    await connexion();
    if (!document.body.innerHTML.trim()) document.body.innerHTML = corps;
    cadre(options);
    try { await rendu(); }
    catch (e) {
      console.error(e);
      const m = $("main");
      if (m) m.insertAdjacentHTML("afterbegin", `<div class="carte" style="border-color:var(--perdu)"><b>Une partie de la page n'a pas pu s'afficher.</b>
        <p class="petit">${esc(e.message)} · <a href="${RACINE}../club/">ouvrir le site actuel</a></p></div>`);
    }
  }

  /* ---------- Export vers l'agenda du téléphone (.ics, fabriqué dans le navigateur) ---------- */
  function ics(liste, nomFichier) {
    const echap = (s) => String(s || "").replace(/[\\;,]/g, (c) => "\\" + c).replace(/\n/g, "\\n");
    const lignes = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CVTT Vaires//v2//FR", "CALSCALE:GREGORIAN", "X-WR-CALNAME:CVTT Vaires"];
    for (const r of liste) {
      if (r.exempt || !r.date) continue;
      const jour = r.date.replace(/-/g, ""), h = (r.heure || "").match(/^(\d{1,2}):(\d{2})/);
      const lieu = salle(r);
      lignes.push("BEGIN:VEVENT", `UID:${r.equipe.cle}-${r.journee}-${jour}@cvtt-vaires`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`);
      if (h) {
        const debut = `${jour}T${h[1].padStart(2, "0")}${h[2]}00`, fin = new Date(enDate(r.date).getTime() + (Number(h[1]) * 60 + Number(h[2]) + 180) * 60e3);
        lignes.push(`DTSTART;TZID=Europe/Paris:${debut}`, `DTEND;TZID=Europe/Paris:${iso(fin).replace(/-/g, "")}T${String(fin.getHours()).padStart(2, "0")}${String(fin.getMinutes()).padStart(2, "0")}00`);
      } else lignes.push(`DTSTART;VALUE=DATE:${jour}`);
      lignes.push(`SUMMARY:${echap(`${r.equipe.nom} ${r.domicile ? "reçoit" : "chez"} ${r.adversaire} (${COMPET[r.equipe.comp].court} J${r.journee})`)}`);
      if (lieu) lignes.push(`LOCATION:${echap([lieu.nom, lieu.adresse].filter(Boolean).join(", "))}`);
      lignes.push("END:VEVENT");
    }
    lignes.push("END:VCALENDAR");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lignes.join("\r\n")], { type: "text/calendar;charset=utf-8" }));
    a.download = nomFichier;
    document.body.append(a); a.click(); a.remove();
  }

  return { RACINE, PAGE, MAJ, VERSION, AUJ, $, esc, lire, ecrire, R, svg, COMPET, joli, sansAccent, iso, enDate, ecart, dateCourte, dateLongue, relatif, heure,
           donnees, facultatif, fichierClub, equipes, rencontres, aVenir, lienRencontre, salle, carteMatch, courbe, signe, nombre, squelettes,
           joueurs, moi, estNouveau, depuis, titre, fenetre, demarrer, ics, sousNav, admin: () => !!lire(R.admin) };
})();

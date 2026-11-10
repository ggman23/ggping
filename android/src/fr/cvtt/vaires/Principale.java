package fr.cvtt.vaires;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.JavascriptInterface;
import android.webkit.URLUtil;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Application CVTT Vaires : cinq onglets, chacun avec sa page qui reste ouverte quand on passe
 * de l'un à l'autre : le site GitHub (mise à jour), l'espace club, l'espace /lundi/, GoatCounter et
 * Umami. Les espaces club et lundi sont publiés en trois copies identiques : l'onglet ouvre la
 * première qui répond, GitHub, sinon Cloudflare, sinon Netlify, sinon une page d'erreur avec
 * « Réessayer ».
 * Les téléchargements et le partage d'images des pages passent par l'application (pont « Appli »).
 */
public class Principale extends Activity {

    /**
     * Un onglet : ses copies du même site (racines, par ordre de préférence, et leurs noms), le
     * chemin de sa page de départ dans chacune, le texte que cette page doit contenir pour être la
     * bonne (null : il suffit qu'elle réponde) et les hôtes dont les pages restent dans l'onglet.
     */
    static final class Onglet {
        final String cle, titre, symbole, chemin, temoin;  // cle : nom fixe de l'onglet dans les réglages
        final String[] racines, noms, hotes;

        Onglet(String cle, String titre, String symbole, String[] racines, String[] noms, String chemin, String temoin,
               String... hotes) {
            this.cle = cle;
            this.titre = titre;
            this.symbole = symbole;
            this.racines = racines;
            this.noms = noms;
            this.chemin = chemin;
            this.temoin = temoin;
            this.hotes = hotes;
        }

        String depart(int copie) {
            return racines[copie] + chemin;
        }

        /** Copie (indice dans racines) d'une adresse, -1 si elle n'est dans aucune. */
        int copie(String adresse) {
            for (int k = 0; adresse != null && k < racines.length; k++) if (adresse.startsWith(racines[k])) return k;
            return -1;
        }

        boolean aHote(String hote) {
            for (String h : hotes) if (hote.equals(h) || hote.endsWith("." + h)) return true;
            return false;
        }
    }

    static final String GITHUB = "https://ggman23.github.io/ggping/", CLOUDFLARE = "https://ggping-pap.pages.dev/",
            NETLIFY = "https://ggping.netlify.app/";
    static final String[] COPIES = {GITHUB, CLOUDFLARE, NETLIFY}, NOMS_COPIES = {"GitHub", "Cloudflare", "Netlify"};
    static final int MISE_A_JOUR = 0, CLUB = 1, LUNDI = 2, GOATCOUNTER = 3, UMAMI = 4;
    // Le témoin est la clé sous laquelle les pages du club et de /lundi/ gardent le mot de passe
    // (ttvaires/ressources.py) : Cloudflare Pages, par exemple, répond par la page d'accueil à une
    // adresse qui n'existe pas. Il est au début des pages (balise meta cvtt-cle) depuis la mise à jour
    // du 10/11/2026 ; avant, seulement à la fin (après 2 Mo pour /lundi/) : la lecture s'arrête dès
    // qu'il est trouvé, au pire après LECTURE_MAX.
    static final String TEMOIN_CLUB = "cvtt-vaires-cle-club";
    static final Onglet[] ONGLETS = {
        new Onglet("maj", "Mise à jour", "⟳", new String[]{GITHUB}, new String[]{"GitHub"}, "", null, "ggman23.github.io"),
        new Onglet("club", "Club", "🏓", COPIES, NOMS_COPIES, "club/", TEMOIN_CLUB,
                "ggman23.github.io", "ggping-pap.pages.dev", "ggping.netlify.app"),
        new Onglet("lundi", "Lundi", "👑", COPIES, NOMS_COPIES, "lundi/", TEMOIN_CLUB,
                "ggman23.github.io", "ggping-pap.pages.dev", "ggping.netlify.app"),
        new Onglet("goatcounter", "GoatCounter", "📊", new String[]{"https://ggman23.goatcounter.com/"},
                new String[]{"GoatCounter"}, "", null, "goatcounter.com"),
        new Onglet("umami", "Umami", "📈", new String[]{"https://cloud.umami.is/"}, new String[]{"Umami"}, "", null, "umami.is"),
    };
    static final String[] ANCIEN_ORDRE = {"maj", "club", "goatcounter", "umami"};  // version 1.3 (réglages)
    static final String REESSAYER = "cvtt-appli://reessayer";  // bouton de la page d'erreur
    static final String DEPART_PERSO = "depart_";  // réglage : page de départ choisie (lien de partage Umami)
    static final int DELAI_CONNEXION = 5000, DELAI_LECTURE = 8000, LECTURE_MAX = 4 * 1024 * 1024;
    static final String DOSSIER = "CVTT Vaires";  // dans Téléchargements
    static final int TAILLE_MAX = 60 * 1024 * 1024;
    static final int ROUGE = Color.rgb(204, 16, 40), NUIT = Color.rgb(27, 42, 74), GRIS = Color.rgb(91, 101, 118);

    private final WebView[] pages = new WebView[ONGLETS.length];
    private final TextView[] boutons = new TextView[ONGLETS.length];
    private final int[] generation = new int[ONGLETS.length];  // la dernière demande l'emporte
    private final boolean[] recherche = new boolean[ONGLETS.length];  // copie qui répond : en cours
    private final boolean[] enErreur = new boolean[ONGLETS.length];
    private final String[] echec = new String[ONGLETS.length];  // adresse que la page d'erreur réessaie
    // Après un passage sur une autre copie ou par la page d'erreur : historique de l'onglet vidé une fois
    // la page affichée (sinon Retour ramènerait à la page en échec, qui renverrait aussitôt ici)
    private final String[] viderSur = new String[ONGLETS.length];
    private FrameLayout cadre;
    private TextView titre;
    private ProgressBar avancement;
    private int courant = -1;
    private String injection = "";
    private SharedPreferences reglages;

    @Override
    protected void onCreate(Bundle etat) {
        super.onCreate(etat);
        reglages = getSharedPreferences("appli", Context.MODE_PRIVATE);
        injection = lireAsset("appli.js");
        CookieManager.getInstance().setAcceptCookie(true);
        setContentView(construireEcran());
        reprendreReglages();
        if (!ouvrirLien(getIntent())) choisir(indiceDe(reglages.getString("onglet_cle", "maj")));
    }

    // ------------------------------------------------------------------ écran

    private View construireEcran() {
        LinearLayout racine = new LinearLayout(this);
        racine.setOrientation(LinearLayout.VERTICAL);
        racine.setBackgroundColor(NUIT);

        LinearLayout barre = new LinearLayout(this);
        barre.setGravity(Gravity.CENTER_VERTICAL);
        barre.setBackgroundColor(NUIT);
        barre.setPadding(dp(14), dp(6), dp(4), dp(6));
        titre = new TextView(this);
        titre.setTextColor(Color.WHITE);
        titre.setTextSize(TypedValue.COMPLEX_UNIT_SP, 18);
        titre.setTypeface(Typeface.DEFAULT_BOLD);
        titre.setSingleLine(true);
        barre.addView(titre, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView maison = action("⌂", "Page de départ de l'onglet", v -> demarrer(courant));
        maison.setOnLongClickListener(v -> { departDorigine(courant); return true; });
        barre.addView(maison);
        barre.addView(action("↻", "Recharger", v -> {
            if (enErreur[courant]) reessayer(courant);
            else pageCourante().reload();
        }));
        barre.addView(action("↗", "Ouvrir dans le navigateur", v -> ouvrirAilleurs(Uri.parse(adresseCourante(courant)))));
        racine.addView(barre);

        avancement = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        avancement.setMax(100);
        avancement.setVisibility(View.INVISIBLE);
        racine.addView(avancement, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(3)));

        cadre = new FrameLayout(this);
        cadre.setBackgroundColor(Color.WHITE);
        racine.addView(cadre, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        LinearLayout bas = new LinearLayout(this);
        bas.setBackgroundColor(Color.WHITE);
        bas.setElevation(dp(8));
        for (int i = 0; i < ONGLETS.length; i++) {
            final int n = i;
            TextView b = new TextView(this);
            b.setText(ONGLETS[i].symbole + "\n" + ONGLETS[i].titre);
            b.setGravity(Gravity.CENTER);
            b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 11.5f);
            b.setMaxLines(2);
            b.setEllipsize(android.text.TextUtils.TruncateAt.END);
            b.setPadding(0, dp(7), 0, dp(7));
            b.setOnClickListener(v -> choisir(n));
            b.setOnLongClickListener(v -> { afficher(n); demarrer(n); return true; });
            boutons[i] = b;
            bas.addView(b, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        }
        racine.addView(bas);

        if (Build.VERSION.SDK_INT >= 35) {
            // Android 15 : l'appli s'étend sous les barres du système ; on garde leur place (et celle du clavier)
            racine.setOnApplyWindowInsetsListener((v, encarts) -> {
                Insets e = encarts.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.ime()
                        | WindowInsets.Type.displayCutout());
                v.setPadding(e.left, e.top, e.right, e.bottom);
                return WindowInsets.CONSUMED;
            });
        } else {
            getWindow().setStatusBarColor(NUIT);
            getWindow().setNavigationBarColor(NUIT);
        }
        return racine;
    }

    private TextView action(String symbole, String description, View.OnClickListener clic) {
        TextView t = new TextView(this);
        t.setText(symbole);
        t.setContentDescription(description);
        t.setTextColor(Color.WHITE);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, 22);
        t.setGravity(Gravity.CENTER);
        t.setPadding(dp(12), dp(2), dp(12), dp(2));
        t.setOnClickListener(clic);
        t.setOnLongClickListener(v -> { Toast.makeText(this, description, Toast.LENGTH_SHORT).show(); return true; });
        return t;
    }

    /** Affiche l'onglet ; sa page n'est chargée qu'à sa première ouverture. */
    private void choisir(int n) {
        if (n < 0 || n >= ONGLETS.length) n = 0;
        if (afficher(n)) demarrer(n);
    }

    /** Affiche l'onglet sur une adresse donnée (lien d'un autre onglet, lien partagé avec l'appli). */
    private void ouvrir(int n, String adresse) {
        afficher(n);
        generation[n]++;  // une recherche de copie en cours ne l'emporte plus
        recherche[n] = false;
        if (enErreur[n]) viderSur[n] = "https://" + Uri.parse(adresse).getHost() + "/";
        pages[n].loadUrl(adresse);
        majAvancement();
    }

    /** Affiche l'onglet n (sans rien charger) ; true si sa page vient d'être créée. */
    private boolean afficher(int n) {
        boolean nouvelle = pages[n] == null;
        if (nouvelle) {
            pages[n] = creerPage();
            cadre.addView(pages[n], new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
        }
        courant = n;
        for (int i = 0; i < ONGLETS.length; i++) {
            if (pages[i] != null) pages[i].setVisibility(i == n ? View.VISIBLE : View.GONE);
            boutons[i].setTextColor(i == n ? ROUGE : GRIS);
            boutons[i].setTypeface(i == n ? Typeface.DEFAULT_BOLD : Typeface.DEFAULT);
            GradientDrawable trait = new GradientDrawable();
            trait.setColor(i == n ? Color.rgb(253, 236, 238) : Color.WHITE);
            boutons[i].setBackground(trait);
        }
        majTitre();
        majAvancement();
        reglages.edit().putString("onglet_cle", ONGLETS[n].cle).apply();
        return nouvelle;
    }

    private WebView pageCourante() {
        return pages[courant];
    }

    /** Titre de la barre : l'onglet, et pour le club la copie affichée (« Club · Cloudflare »). */
    private void majTitre() {
        Onglet o = ONGLETS[courant];
        int k = enErreur[courant] || pages[courant] == null ? -1 : o.copie(pages[courant].getUrl());
        titre.setText(o.racines.length > 1 && k >= 0 ? o.titre + " · " + o.noms[k] : o.titre);
    }

    private void majAvancement() {
        WebView page = pageCourante();
        int pourcent = page == null ? 100 : page.getProgress();
        boolean cherche = recherche[courant];
        avancement.setIndeterminate(cherche);
        if (!cherche) avancement.setProgress(pourcent);
        avancement.setVisibility(cherche || pourcent < 100 ? View.VISIBLE : View.INVISIBLE);
    }

    private String adresseCourante(int n) {
        String adresse = pages[n] == null || enErreur[n] ? null : pages[n].getUrl();
        return adresse != null && adresse.startsWith("https://") ? adresse : departDe(n, 0);
    }

    // ------------------------------------------------------------------ copies du site

    /** Page de départ de l'onglet (copie k) : celle choisie par l'utilisateur s'il y en a une. */
    private String departDe(int n, int copie) {
        String perso = ONGLETS[n].racines.length == 1 ? reglages.getString(DEPART_PERSO + ONGLETS[n].cle, null) : null;
        return perso != null ? perso : ONGLETS[n].depart(copie);
    }

    /** Page de départ : pour le club, celle de la première copie qui répond ; sinon chargée directement
     * (si le site ne répond pas, la page d'erreur de l'application s'affiche). */
    private void demarrer(int n) {
        if (ONGLETS[n].racines.length > 1) rechercher(n, ONGLETS[n].chemin, 0, true);
        else ouvrir(n, departDe(n, 0));
    }

    /** Bouton « Réessayer » de la page d'erreur (et ↻ sur cette page). */
    private void reessayer(int n) {
        Onglet o = ONGLETS[n];
        int k = o.copie(echec[n]);
        if (o.racines.length > 1) rechercher(n, k >= 0 ? echec[n].substring(o.racines[k].length()) : o.chemin, 0, true);
        else ouvrir(n, echec[n] != null ? echec[n] : departDe(n, 0));
    }

    /**
     * Cherche, à partir de la copie `debut`, la première qui répond pour `chemin` (relatif aux racines)
     * et l'ouvre dans l'onglet. Si aucune ne répond : page d'erreur si `erreurSiAucune`, sinon rien
     * (la page du site, par exemple « introuvable », reste affichée).
     */
    private void rechercher(int n, String chemin, int debut, boolean erreurSiAucune) {
        Onglet o = ONGLETS[n];
        int demande = ++generation[n];
        recherche[n] = true;
        if (n == courant) majAvancement();
        String temoin = chemin.equals(o.chemin) ? o.temoin : null;
        new Thread(() -> {
            int trouve = -1;
            for (int k = debut; k < o.racines.length && trouve < 0; k++) if (repond(o.racines[k] + chemin, temoin)) trouve = k;
            final int k = trouve;
            runOnUiThread(() -> {
                if (demande != generation[n] || isDestroyed()) return;  // entre-temps : autre demande
                recherche[n] = false;
                if (k >= 0) {
                    if (k > 0 || enErreur[n]) viderSur[n] = o.racines[k];
                    pages[n].loadUrl(o.racines[k] + chemin);
                    if (k > debut) message(sansReponse(o, debut, k) + " : " + o.titre + " ouvert sur " + o.noms[k] + ".");
                } else if (erreurSiAucune) {
                    afficherErreur(n, o.racines[debut] + chemin);
                }
                if (n == courant) majAvancement();
            });
        }, "copie-" + o.titre).start();
    }

    private static String sansReponse(Onglet o, int debut, int fin) {
        StringBuilder noms = new StringBuilder(o.noms[debut]);
        for (int k = debut + 1; k < fin; k++) noms.append(k == fin - 1 ? " et " : ", ").append(o.noms[k]);
        return noms + (fin - debut > 1 ? " ne répondent pas" : " ne répond pas");
    }

    /**
     * La page répond-elle (code 2xx, après redirections) et contient-elle `temoin` (s'il est donné) ?
     * Appelé hors du fil de l'écran.
     */
    static boolean repond(String adresse, String temoin) {
        HttpURLConnection connexion = null;
        try {
            connexion = (HttpURLConnection) new URL(adresse).openConnection();
            connexion.setConnectTimeout(DELAI_CONNEXION);
            connexion.setReadTimeout(DELAI_LECTURE);
            connexion.setUseCaches(false);
            connexion.setRequestProperty("Cache-Control", "no-cache");
            int code = connexion.getResponseCode();
            if (code < 200 || code >= 300) return false;
            if (temoin == null) return true;
            try (InputStream entree = connexion.getInputStream()) {
                byte[] tampon = new byte[16384];
                String fin = "";  // fin du morceau précédent : le témoin peut être à cheval sur deux morceaux
                for (int n, total = 0; total < LECTURE_MAX && (n = entree.read(tampon)) > 0; total += n) {
                    String morceau = fin + new String(tampon, 0, n, StandardCharsets.ISO_8859_1);  // octet = caractère
                    if (morceau.contains(temoin)) return true;
                    fin = morceau.substring(Math.max(0, morceau.length() - temoin.length()));
                }
                return false;
            }
        } catch (IOException | RuntimeException e) {
            return false;
        } finally {
            if (connexion != null) connexion.disconnect();
        }
    }

    /**
     * Une page de l'onglet n'a pas pu s'afficher (code HTTP, 0 : site injoignable) : la même page sur la
     * copie suivante ; si le site est injoignable partout, page d'erreur. Une page absente (404) ne fait
     * changer de copie que pour la page de départ (copie pas encore publiée) : ailleurs, c'est un lien mort.
     */
    private void secours(WebView vue, String adresse, int code) {
        int n = indice(vue);
        if (n < 0) return;
        Onglet o = ONGLETS[n];
        int k = o.copie(adresse);
        String chemin = k >= 0 ? adresse.substring(o.racines[k].length()) : null;
        if (code == 404 && !o.chemin.equals(chemin)) return;
        if (k >= 0 && k + 1 < o.racines.length) rechercher(n, chemin, k + 1, code == 0);
        else if (code == 0) afficherErreur(n, adresse);
    }

    private void afficherErreur(int n, String adresse) {
        Onglet o = ONGLETS[n];
        StringBuilder liste = new StringBuilder();
        for (int k = 0; k < o.racines.length; k++) {
            liste.append("<li>").append(o.noms[k]).append(" <small>(").append(Uri.parse(o.racines[k]).getHost()).append(")</small></li>");
        }
        String page = "<!doctype html><html lang=fr><meta charset=utf-8>"
                + "<meta name=viewport content='width=device-width,initial-scale=1'>"
                + "<body style='font-family:sans-serif;margin:0;padding:28px 22px;color:#1b2a4a;background:#fff;line-height:1.45'>"
                + "<div style='font-size:40px'>⚠️</div>"
                + "<h2 style='margin:.3em 0 .6em'>" + o.titre + " : site indisponible</h2>"
                + "<p>" + (o.racines.length > 1 ? "Aucune copie du site ne répond :" : "Le site ne répond pas :") + "</p>"
                + "<ul>" + liste + "</ul>"
                + "<p>Vérifie la connexion internet du téléphone (Wi-Fi ou données mobiles), puis réessaie.</p>"
                + "<p><a href='" + REESSAYER + "' style='display:inline-block;background:#cc1028;color:#fff;"
                + "padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:bold'>Réessayer</a></p>";
        echec[n] = adresse;
        enErreur[n] = true;
        pages[n].loadDataWithBaseURL(null, page, "text/html", "utf-8", null);
        if (n == courant) majTitre();
    }

    /** Appui long sur ⌂ : oublier la page de départ choisie (lien de partage Umami). */
    private void departDorigine(int n) {
        String perso = reglages.getString(DEPART_PERSO + ONGLETS[n].cle, null);
        if (perso == null) {
            Toast.makeText(this, "Page de départ de l'onglet", Toast.LENGTH_SHORT).show();
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle(ONGLETS[n].titre)
                .setMessage("Page de départ de l'onglet : " + perso + "\n\nRevenir à celle d'origine (" + ONGLETS[n].depart(0) + ") ?")
                .setPositiveButton("Oui", (d, b) -> {
                    reglages.edit().remove(DEPART_PERSO + ONGLETS[n].cle).apply();
                    demarrer(n);
                })
                .setNegativeButton("Non", null)
                .show();
    }

    static int indiceDe(String cle) {
        for (int i = 0; i < ONGLETS.length; i++) if (ONGLETS[i].cle.equals(cle)) return i;
        return 0;
    }

    /** Réglages de la version 1.3 (onglets repérés par leur numéro, avant l'onglet Lundi) : repris. */
    private void reprendreReglages() {
        SharedPreferences.Editor modif = reglages.edit();
        int ancien = reglages.getInt("onglet", -1);
        if (ancien >= 0 && ancien < ANCIEN_ORDRE.length && !reglages.contains("onglet_cle")) {
            modif.putString("onglet_cle", ANCIEN_ORDRE[ancien]);
        }
        for (int i = 0; i < ANCIEN_ORDRE.length; i++) {
            String perso = reglages.getString(DEPART_PERSO + i, null);
            if (perso != null) modif.putString(DEPART_PERSO + ANCIEN_ORDRE[i], perso).remove(DEPART_PERSO + i);
        }
        modif.remove("onglet").apply();
    }

    private int indice(WebView vue) {
        for (int i = 0; i < pages.length; i++) if (pages[i] == vue) return i;
        return -1;
    }

    // ------------------------------------------------------------------ pages

    private WebView creerPage() {
        WebView page = new WebView(this);
        WebSettings s = page.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);  // mots de passe et jeton retenus par les pages
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setAllowFileAccess(false);
        CookieManager.getInstance().setAcceptThirdPartyCookies(page, true);
        page.addJavascriptInterface(new Pont(), "Appli");
        page.setWebViewClient(new Client());
        page.setWebChromeClient(new WebChromeClient() {  // aussi : alert(), confirm(), prompt() des pages
            @Override
            public void onProgressChanged(WebView vue, int pourcent) {
                if (vue == pageCourante()) majAvancement();
            }
        });
        page.setDownloadListener(new Telechargement());
        return page;
    }

    /**
     * Onglet d'une adresse, -1 si elle ne relève d'aucun : celui dont une page de départ la contient
     * (la plus précise : …/ggping/club/… est le club, …/ggping/… la mise à jour), sinon le premier qui
     * a son hôte (l'accueil public de Cloudflare ou de Netlify : le club).
     */
    static int ongletPour(Uri adresse) {
        String hote = adresse.getHost();
        if (hote == null || !"https".equals(adresse.getScheme())) return -1;
        String texte = adresse.toString();
        int choisi = -1, longueur = -1;
        for (int i = 0; i < ONGLETS.length; i++) {
            for (int k = 0; k < ONGLETS[i].racines.length; k++) {
                String depart = ONGLETS[i].depart(k);
                if (texte.startsWith(depart) && depart.length() > longueur) {
                    choisi = i;
                    longueur = depart.length();
                }
            }
        }
        if (choisi >= 0) return choisi;
        for (int i = 0; i < ONGLETS.length; i++) if (ONGLETS[i].aHote(hote)) return i;
        return -1;
    }

    /** Lien dans un texte partagé avec l'application (« Partager » > CVTT Vaires). */
    static Uri lienDans(String texte) {
        if (texte == null) return null;
        Matcher lien = Pattern.compile("https://[^\\s<>\"']+").matcher(texte);
        return lien.find() ? Uri.parse(lien.group()) : null;
    }

    /**
     * Lien ouvert ou partagé avec l'application : affiché dans son onglet. Un lien de partage Umami
     * (…/share/…, statistiques en lecture seule, sans connexion) devient la page de départ de l'onglet
     * Umami. Renvoie false s'il n'y a pas de lien pour l'application.
     */
    private boolean ouvrirLien(Intent intention) {
        if (intention == null) return false;
        Uri adresse = intention.getData();
        if (adresse == null && Intent.ACTION_SEND.equals(intention.getAction())) {
            adresse = lienDans(intention.getStringExtra(Intent.EXTRA_TEXT));
        }
        if (adresse == null) return false;
        int n = ongletPour(adresse);
        if (n < 0) {
            message("Ce lien n'est pas pour l'application : " + adresse);
            return false;
        }
        String chemin = adresse.getPath();
        if (n == UMAMI && chemin != null && chemin.startsWith("/share/")) {
            reglages.edit().putString(DEPART_PERSO + ONGLETS[n].cle, adresse.toString()).apply();
            message("Lien de partage Umami enregistré : l'onglet Umami s'ouvre maintenant sur ces statistiques, "
                    + "sans connexion.");
        }
        ouvrir(n, adresse.toString());
        return true;
    }

    private class Client extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView vue, WebResourceRequest demande) {
            Uri adresse = demande.getUrl();
            if (REESSAYER.equals(adresse.toString())) {
                int n = indice(vue);
                if (n >= 0) reessayer(n);
                return true;
            }
            if (!demande.isForMainFrame()) return false;
            int ici = indice(vue);
            String hote = adresse.getHost();
            boolean https = "https".equals(adresse.getScheme()) && hote != null;
            if (https && ici >= 0 && ONGLETS[ici].aHote(hote)) return false;  // même site : reste dans l'onglet
            int n = https ? ongletPour(adresse) : -1;
            if (n < 0) {  // autre site (GitHub, carte d'une salle...) : dans le navigateur
                if (https && ici == UMAMI && hote.equals("accounts.google.com")) {
                    message("Google refuse la connexion dans une application : elle s'ouvre dans Chrome. "
                            + "Pour Umami dans l'application sans connexion : lien de partage (voir LISEZ-MOI).");
                }
                ouvrirAilleurs(adresse);
                return true;
            }
            ouvrir(n, adresse.toString());  // lien vers un autre onglet : on y va
            return true;
        }

        @Override
        public void onPageStarted(WebView vue, String adresse, android.graphics.Bitmap icone) {
            int n = indice(vue);
            if (n >= 0 && adresse != null && adresse.startsWith("https://")) enErreur[n] = false;
        }

        @Override
        public void onPageFinished(WebView vue, String adresse) {
            if (adresse != null && adresse.startsWith("https://") && ongletPour(Uri.parse(adresse)) >= 0) {
                vue.evaluateJavascript(injection, null);
            }
            int n = indice(vue);
            if (n >= 0 && viderSur[n] != null && adresse != null && adresse.startsWith(viderSur[n])) {
                vue.clearHistory();
                viderSur[n] = null;
            }
            if (vue == pageCourante()) majTitre();
        }

        /** Site injoignable (pas de réseau, serveur arrêté...) : copie suivante, sinon page d'erreur. */
        @Override
        public void onReceivedError(WebView vue, WebResourceRequest demande, WebResourceError erreur) {
            if (!demande.isForMainFrame()) return;
            int code = erreur.getErrorCode();
            if (code == ERROR_HOST_LOOKUP || code == ERROR_CONNECT || code == ERROR_TIMEOUT || code == ERROR_IO) {
                secours(vue, demande.getUrl().toString(), 0);
            }
        }

        /** Page absente ou serveur en panne sur cette copie : voir secours(). */
        @Override
        public void onReceivedHttpError(WebView vue, WebResourceRequest demande, WebResourceResponse reponse) {
            int code = reponse.getStatusCode();
            if (demande.isForMainFrame() && (code == 404 || code >= 500)) secours(vue, demande.getUrl().toString(), code);
        }
    }

    /** Fichier proposé en téléchargement par une adresse web (les blob: passent par appli.js). */
    private class Telechargement implements DownloadListener {
        @Override
        public void onDownloadStart(String adresse, String agent, String disposition, String type, long taille) {
            if (!URLUtil.isHttpsUrl(adresse)) {
                message("Téléchargement impossible depuis cette page");
                return;
            }
            String nom = URLUtil.guessFileName(adresse, disposition, type);
            DownloadManager.Request demande = new DownloadManager.Request(Uri.parse(adresse));
            String cookies = CookieManager.getInstance().getCookie(adresse);
            if (cookies != null) demande.addRequestHeader("Cookie", cookies);
            if (agent != null) demande.addRequestHeader("User-Agent", agent);
            demande.setMimeType(type);
            demande.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            demande.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, DOSSIER + "/" + nom);
            ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(demande);
            message("Téléchargement de " + nom + "…");
        }
    }

    // ------------------------------------------------------------------ pont avec les pages

    /** Appelé par appli.js : enregistrer un fichier, le partager, signaler une erreur. */
    private class Pont {
        @JavascriptInterface
        public void enregistrer(String nom, String type, String base64) {
            try {
                byte[] octets = decoder(base64);
                nom = nomPropre(nom);
                ContentValues v = new ContentValues();
                v.put(MediaStore.Downloads.DISPLAY_NAME, nom);
                v.put(MediaStore.Downloads.MIME_TYPE, type);
                v.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/" + DOSSIER);
                v.put(MediaStore.Downloads.IS_PENDING, 1);
                Uri fichier = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, v);
                if (fichier == null) throw new IOException("Téléchargements inaccessibles");
                try (OutputStream sortie = getContentResolver().openOutputStream(fichier)) {
                    sortie.write(octets);
                }
                v.clear();
                v.put(MediaStore.Downloads.IS_PENDING, 0);
                getContentResolver().update(fichier, v, null, null);
                message("Enregistré dans Téléchargements/" + DOSSIER + " : " + nom);
            } catch (Exception e) {
                message("Enregistrement impossible : " + e.getMessage());
            }
        }

        @JavascriptInterface
        public void partager(String nom, String type, String base64) {
            try {
                byte[] octets = decoder(base64);
                File dossier = Fichiers.dossier(Principale.this);
                for (File ancien : dossier.listFiles() == null ? new File[0] : dossier.listFiles()) ancien.delete();
                File fichier = new File(dossier, nomPropre(nom));
                try (FileOutputStream sortie = new FileOutputStream(fichier)) {
                    sortie.write(octets);
                }
                Uri adresse = Fichiers.adresse(fichier);
                Intent envoi = new Intent(Intent.ACTION_SEND);
                envoi.setType(type);
                envoi.putExtra(Intent.EXTRA_STREAM, adresse);
                envoi.setClipData(ClipData.newRawUri(fichier.getName(), adresse));
                envoi.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                runOnUiThread(() -> startActivity(Intent.createChooser(envoi, "Partager " + fichier.getName())));
            } catch (Exception e) {
                message("Partage impossible : " + e.getMessage());
            }
        }

        @JavascriptInterface
        public void erreur(String texte) {
            message("Problème : " + texte);
        }
    }

    static byte[] decoder(String base64) throws IOException {
        if (base64 == null || base64.length() > TAILLE_MAX / 3 * 4) throw new IOException("fichier trop gros");
        return Base64.decode(base64, Base64.DEFAULT);
    }

    /** Nom de fichier sans chemin ni caractère gênant. */
    static String nomPropre(String nom) {
        String propre = nom == null ? "" : nom.replaceAll("[^\\p{L}\\p{N}._ -]", "_").replaceAll("^[.]+", "").trim();
        return propre.isEmpty() ? "fichier" : propre;
    }

    // ------------------------------------------------------------------ divers

    private void ouvrirAilleurs(Uri adresse) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, adresse));
        } catch (ActivityNotFoundException e) {
            message("Aucune application pour ouvrir " + adresse);
        }
    }

    private void message(String texte) {
        runOnUiThread(() -> Toast.makeText(this, texte, Toast.LENGTH_LONG).show());
    }

    private String lireAsset(String nom) {
        try (InputStream entree = getAssets().open(nom); ByteArrayOutputStream tout = new ByteArrayOutputStream()) {
            byte[] tampon = new byte[8192];
            for (int lu; (lu = entree.read(tampon)) > 0; ) tout.write(tampon, 0, lu);
            return tout.toString(StandardCharsets.UTF_8.name());
        } catch (IOException e) {
            return "";
        }
    }

    private int dp(float valeur) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, valeur, getResources().getDisplayMetrics()));
    }

    @Override
    protected void onNewIntent(Intent intention) {
        super.onNewIntent(intention);
        ouvrirLien(intention);
    }

    /** Retour : page précédente de l'onglet ; au début de l'onglet (ou sur la page d'erreur), l'appli
     * passe en arrière-plan. */
    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (pageCourante() != null && !enErreur[courant] && pageCourante().canGoBack()) {
            pageCourante().goBack();
        } else {
            moveTaskToBack(true);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();  // connexions GoatCounter et Umami gardées
    }
}

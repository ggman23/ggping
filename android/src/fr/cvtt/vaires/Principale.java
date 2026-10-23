package fr.cvtt.vaires;

import android.app.Activity;
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
import android.webkit.WebResourceRequest;
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
import java.nio.charset.StandardCharsets;

/**
 * Application CVTT Vaires : quatre onglets, chacun avec sa page qui reste ouverte quand on passe
 * de l'un à l'autre : le site GitHub (mise à jour), l'espace club (Netlify), GoatCounter et Umami.
 * Les téléchargements et le partage d'images des pages passent par l'application (pont « Appli »).
 */
public class Principale extends Activity {

    /** Titre, symbole, adresse de départ et hôtes de chaque onglet. */
    static final String[][] ONGLETS = {
        {"Mise à jour", "⟳", "https://ggman23.github.io/ggping/", "ggman23.github.io"},
        {"Club", "🏓", "https://ggping.netlify.app/club/", "ggping.netlify.app"},
        {"GoatCounter", "📊", "https://ggman23.goatcounter.com/", "goatcounter.com"},
        {"Umami", "📈", "https://cloud.umami.is/", "umami.is"},
    };
    static final String DOSSIER = "CVTT Vaires";  // dans Téléchargements
    static final int TAILLE_MAX = 60 * 1024 * 1024;
    static final int ROUGE = Color.rgb(204, 16, 40), NUIT = Color.rgb(27, 42, 74), GRIS = Color.rgb(91, 101, 118);

    private final WebView[] pages = new WebView[ONGLETS.length];
    private final TextView[] boutons = new TextView[ONGLETS.length];
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
        int depart = getIntent() != null && getIntent().getData() != null ? ongletPour(getIntent().getData()) : -1;
        choisir(depart >= 0 ? depart : reglages.getInt("onglet", 0));
        if (depart >= 0) pages[depart].loadUrl(getIntent().getData().toString());
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
        barre.addView(action("⌂", "Page de départ de l'onglet", v -> pageCourante().loadUrl(ONGLETS[courant][2])));
        barre.addView(action("↻", "Recharger", v -> pageCourante().reload()));
        barre.addView(action("↗", "Ouvrir dans le navigateur", v -> ouvrirAilleurs(Uri.parse(pageCourante().getUrl() != null
                ? pageCourante().getUrl() : ONGLETS[courant][2]))));
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
            b.setText(ONGLETS[i][1] + "\n" + ONGLETS[i][0]);
            b.setGravity(Gravity.CENTER);
            b.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12.5f);
            b.setPadding(0, dp(7), 0, dp(7));
            b.setOnClickListener(v -> choisir(n));
            b.setOnLongClickListener(v -> { choisir(n); pages[n].loadUrl(ONGLETS[n][2]); return true; });
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

    private void choisir(int n) {
        if (n < 0 || n >= ONGLETS.length) n = 0;
        if (pages[n] == null) {  // chaque page n'est chargée qu'à sa première ouverture
            pages[n] = creerPage();
            cadre.addView(pages[n], new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT));
            pages[n].loadUrl(ONGLETS[n][2]);
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
        titre.setText(ONGLETS[n][0]);
        avancement.setVisibility(pages[n].getProgress() < 100 ? View.VISIBLE : View.INVISIBLE);
        reglages.edit().putInt("onglet", n).apply();
    }

    private WebView pageCourante() {
        return pages[courant];
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
                if (vue != pageCourante()) return;
                avancement.setProgress(pourcent);
                avancement.setVisibility(pourcent < 100 ? View.VISIBLE : View.INVISIBLE);
            }
        });
        page.setDownloadListener(new Telechargement());
        return page;
    }

    /** Onglet d'une adresse (selon son hôte), -1 si elle ne relève d'aucun onglet. */
    static int ongletPour(Uri adresse) {
        String hote = adresse.getHost();
        if (hote == null || !"https".equals(adresse.getScheme())) return -1;
        for (int i = 0; i < ONGLETS.length; i++) {
            if (hote.equals(ONGLETS[i][3]) || hote.endsWith("." + ONGLETS[i][3])) return i;
        }
        return -1;
    }

    private class Client extends WebViewClient {
        @Override
        public boolean shouldOverrideUrlLoading(WebView vue, WebResourceRequest demande) {
            Uri adresse = demande.getUrl();
            if (!demande.isForMainFrame()) return false;
            int n = ongletPour(adresse);
            if (n < 0) {  // autre site (GitHub, carte d'une salle...) : dans le navigateur
                ouvrirAilleurs(adresse);
                return true;
            }
            if (pages[n] == vue) return false;
            choisir(n);  // lien vers un autre onglet : on y va
            pages[n].loadUrl(adresse.toString());
            return true;
        }

        @Override
        public void onPageFinished(WebView vue, String adresse) {
            if (ongletPour(Uri.parse(adresse)) >= 0) vue.evaluateJavascript(injection, null);
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
        int n = intention.getData() != null ? ongletPour(intention.getData()) : -1;
        if (n >= 0) {
            choisir(n);
            pages[n].loadUrl(intention.getData().toString());
        }
    }

    /** Retour : page précédente de l'onglet ; au début de l'onglet, l'appli passe en arrière-plan. */
    @Override
    @SuppressWarnings("deprecation")
    public void onBackPressed() {
        if (pageCourante() != null && pageCourante().canGoBack()) {
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

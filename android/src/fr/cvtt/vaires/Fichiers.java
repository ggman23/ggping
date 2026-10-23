package fr.cvtt.vaires;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;
import android.webkit.MimeTypeMap;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Locale;

/**
 * Donne à l'application choisie pour un partage (WhatsApp, SMS...) l'image à envoyer, le temps du
 * partage seulement (permission accordée par l'Intent). Les fichiers sont dans le cache de l'appli.
 */
public class Fichiers extends ContentProvider {

    static final String AUTORITE = "fr.cvtt.vaires.fichiers";

    static File dossier(Context contexte) {
        File d = new File(contexte.getCacheDir(), "partage");
        d.mkdirs();
        return d;
    }

    static Uri adresse(File fichier) {
        return new Uri.Builder().scheme("content").authority(AUTORITE).appendPath(fichier.getName()).build();
    }

    private File fichier(Uri adresse) throws FileNotFoundException {
        String nom = adresse.getLastPathSegment();
        if (nom == null || nom.contains("/") || nom.startsWith(".")) throw new FileNotFoundException(String.valueOf(adresse));
        File f = new File(dossier(getContext()), nom);
        if (!f.isFile()) throw new FileNotFoundException(nom);
        return f;
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public ParcelFileDescriptor openFile(Uri adresse, String mode) throws FileNotFoundException {
        return ParcelFileDescriptor.open(fichier(adresse), ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override
    public String getType(Uri adresse) {
        String extension = MimeTypeMap.getFileExtensionFromUrl(adresse.getLastPathSegment());
        String type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension == null ? "" : extension.toLowerCase(Locale.ROOT));
        return type != null ? type : "application/octet-stream";
    }

    @Override
    public Cursor query(Uri adresse, String[] colonnes, String selection, String[] arguments, String tri) {
        File f;
        try {
            f = fichier(adresse);
        } catch (FileNotFoundException e) {
            return null;
        }
        MatrixCursor resultat = new MatrixCursor(new String[] {OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE});
        resultat.addRow(new Object[] {f.getName(), f.length()});
        return resultat;
    }

    @Override
    public Uri insert(Uri adresse, ContentValues valeurs) {
        throw new UnsupportedOperationException("lecture seule");
    }

    @Override
    public int update(Uri adresse, ContentValues valeurs, String selection, String[] arguments) {
        throw new UnsupportedOperationException("lecture seule");
    }

    @Override
    public int delete(Uri adresse, String selection, String[] arguments) {
        throw new UnsupportedOperationException("lecture seule");
    }
}

/* Ajouté par l'application à chaque page de ses onglets : ce qu'un navigateur fait seul et
   qu'une WebView Android ne sait pas faire. Appli = le pont vers l'application (Principale.java). */
(() => {
  if (window.__appliCvtt) return;
  window.__appliCvtt = true;

  // L'appli est celle de l'administrateur : ses visites ne comptent pas dans les statistiques du club
  if (location.hostname === "ggping.netlify.app") {
    try { localStorage.setItem("skipgc", "t"); localStorage.setItem("umami.disabled", "1"); } catch (e) { /* rien */ }
  }

  const base64 = (blob) => new Promise((ok, ko) => {
    const lecteur = new FileReader();
    lecteur.onload = () => ok(String(lecteur.result).split(",")[1] || "");
    lecteur.onerror = () => ko(lecteur.error);
    lecteur.readAsDataURL(blob);
  });
  const envoyer = async (methode, nom, blob) => {
    try { Appli[methode](nom || "fichier", blob.type || "application/octet-stream", await base64(blob)); }
    catch (e) { Appli.erreur(String((e && e.message) || e)); }
  };

  // Téléchargements de la page (lien <a download> vers un fichier déchiffré) : enregistrés par l'appli
  // dans Téléchargements/CVTT Vaires (une WebView ne sait pas enregistrer un blob: toute seule)
  document.addEventListener("click", (ev) => {
    const lien = ev.target && ev.target.closest ? ev.target.closest("a[download]") : null;
    if (!lien || !/^(blob|data):/.test(lien.href)) return;
    ev.preventDefault();
    ev.stopPropagation();
    const nom = lien.getAttribute("download");
    fetch(lien.href).then((r) => r.blob()).then((blob) => envoyer("enregistrer", nom, blob))
      .catch((e) => Appli.erreur(String((e && e.message) || e)));
  }, true);

  // Partage d'images (WhatsApp, SMS...) : par le menu de partage d'Android
  navigator.canShare = (donnees) => !!(donnees && donnees.files && donnees.files.length);
  navigator.share = async (donnees) => {
    for (const fichier of (donnees && donnees.files) || []) await envoyer("partager", fichier.name, fichier);
  };
})();

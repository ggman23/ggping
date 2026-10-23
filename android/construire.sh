#!/usr/bin/env bash
# Construit l'application Android (APK signé) avec les seuls outils du SDK Android, sans Gradle :
#   ANDROID_HOME=... CLE=cle.p12 CLE_MDP=... android/construire.sh
# Variables : ANDROID_HOME (SDK avec build-tools 35 et la plateforme android-35), CLE (magasin de
# clés PKCS12 qui signe l'APK, toujours le même pour pouvoir mettre l'appli à jour), CLE_MDP (son
# mot de passe), CLE_ALIAS (défaut : cvtt), VERSION_CODE (nombre croissant), VERSION_NOM.
# Résultat : android/construction/CVTT-Vaires.apk
set -euo pipefail
ICI=$(cd "$(dirname "$0")" && pwd)
SDK=${ANDROID_HOME:-${ANDROID_SDK_ROOT:?ANDROID_HOME manquant}}
OUTILS=$SDK/build-tools/${BUILD_TOOLS:-35.0.0}
PLATEFORME=$SDK/platforms/android-35/android.jar
SORTIE=${SORTIE:-$ICI/construction}
: "${CLE:?CLE manquant (magasin de clés de signature)}" "${CLE_MDP:?CLE_MDP manquant}"

rm -rf "$SORTIE"
mkdir -p "$SORTIE/classes" "$SORTIE/dex"
echo "1/4 Ressources (icônes, nom, manifeste)"
"$OUTILS/aapt2" compile --dir "$ICI/res" -o "$SORTIE/ressources.zip"
"$OUTILS/aapt2" link -o "$SORTIE/base.apk" -I "$PLATEFORME" --manifest "$ICI/AndroidManifest.xml" \
  -A "$ICI/assets" --min-sdk-version 29 --target-sdk-version 35 \
  --version-code "${VERSION_CODE:-1}" --version-name "${VERSION_NOM:-1.0}" "$SORTIE/ressources.zip"
echo "2/4 Code Java"
javac -nowarn -Xlint:-options --release 11 -encoding UTF-8 -classpath "$PLATEFORME" -d "$SORTIE/classes" \
  $(find "$ICI/src" -name '*.java')
"$OUTILS/d8" --release --min-api 29 --lib "$PLATEFORME" --output "$SORTIE/dex" $(find "$SORTIE/classes" -name '*.class')
echo "3/4 Assemblage"
cp "$SORTIE/base.apk" "$SORTIE/non-signe.apk"
(cd "$SORTIE/dex" && zip -q -X "$SORTIE/non-signe.apk" classes.dex)
"$OUTILS/zipalign" -f -p 4 "$SORTIE/non-signe.apk" "$SORTIE/aligne.apk"
echo "4/4 Signature"
"$OUTILS/apksigner" sign --ks "$CLE" --ks-pass env:CLE_MDP --ks-key-alias "${CLE_ALIAS:-cvtt}" \
  --out "$SORTIE/CVTT-Vaires.apk" "$SORTIE/aligne.apk"
"$OUTILS/apksigner" verify --print-certs "$SORTIE/CVTT-Vaires.apk" | grep -m1 "SHA-256" || true
rm -f "$SORTIE/base.apk" "$SORTIE/non-signe.apk" "$SORTIE/aligne.apk" "$SORTIE/ressources.zip"
echo "APK : $SORTIE/CVTT-Vaires.apk ($(du -h "$SORTIE/CVTT-Vaires.apk" | cut -f1))"

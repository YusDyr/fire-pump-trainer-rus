#!/usr/bin/env bash
# Сборка и подпись APK из android/ (ассеты готовит tools/build.py).
#
#   KEYSTORE=/path/release.jks KEYSTORE_PASSWORD=... tools/build_apk.sh
#
# Переменные окружения:
#   KEYSTORE           — путь к ключу подписи (обязательно, иначе сборка остановится:
#                        APK с другим ключом не установится поверх старой версии);
#   KEYSTORE_PASSWORD  — пароль ключа и хранилища;
#   KEY_ALIAS          — алиас ключа (по умолчанию ncpk);
#   ANDROID_JAR        — android.jar платформы (по умолчанию ищется в $ANDROID_HOME
#                        или /usr/lib/android-sdk);
#   BUILD_TOOLS        — каталог build-tools с aapt, d8, zipalign, apksigner
#                        (по умолчанию — последний в $ANDROID_HOME/build-tools, иначе PATH);
#   OUT                — куда положить APK (по умолчанию NCPK-emulator.apk в корне).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/android"
OUT="${OUT:-$ROOT/NCPK-emulator.apk}"
KEY_ALIAS="${KEY_ALIAS:-ncpk}"

[ -f "$SRC/assets/index.html" ] || { echo "Нет android/assets — сначала запустите tools/build.py"; exit 1; }
[ -n "${KEYSTORE:-}" ] && [ -f "$KEYSTORE" ] || { echo "Нет ключа подписи: задайте KEYSTORE"; exit 1; }
[ -n "${KEYSTORE_PASSWORD:-}" ] || { echo "Задайте KEYSTORE_PASSWORD"; exit 1; }

SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/lib/android-sdk}}"
if [ -z "${BUILD_TOOLS:-}" ] && [ -d "$SDK/build-tools" ]; then
  BT=$(ls "$SDK/build-tools" | sort -V | tail -1)
  [ -x "$SDK/build-tools/$BT/aapt" ] && BUILD_TOOLS="$SDK/build-tools/$BT"
fi
tool() { if [ -n "${BUILD_TOOLS:-}" ] && [ -x "$BUILD_TOOLS/$1" ]; then echo "$BUILD_TOOLS/$1"; else command -v "$1" || true; fi; }
AAPT=$(tool aapt); ZIPALIGN=$(tool zipalign); APKSIGNER=$(tool apksigner); D8=$(tool d8); DX=$(command -v dalvik-exchange || true)
[ -n "$AAPT" ] && [ -n "$ZIPALIGN" ] && [ -n "$APKSIGNER" ] || { echo "Не найдены aapt/zipalign/apksigner"; exit 1; }
if [ -z "${ANDROID_JAR:-}" ]; then
  ANDROID_JAR=$(ls -d "$SDK"/platforms/android-*/android.jar 2>/dev/null | sort -V | tail -1)
fi
[ -f "$ANDROID_JAR" ] || { echo "Не найден android.jar (задайте ANDROID_JAR)"; exit 1; }
echo "android.jar: $ANDROID_JAR"; echo "aapt: $AAPT"

B="$SRC/build"; rm -rf "$B"; mkdir -p "$B/classes" "$B/gen"
cd "$SRC"
"$AAPT" package -f -m -J "$B/gen" -M AndroidManifest.xml -S res -I "$ANDROID_JAR"
javac -nowarn -source 8 -target 8 -bootclasspath "$ANDROID_JAR" -d "$B/classes" \
  $(find src -name '*.java') $(find "$B/gen" -name R.java) 2>&1 | grep -v "warning\|^Picked\|^Note" || true
if [ -n "$D8" ]; then
  "$D8" --min-api 21 --lib "$ANDROID_JAR" --output "$B" $(find "$B/classes" -name '*.class')
else
  [ -n "$DX" ] || { echo "Не найден d8 или dalvik-exchange"; exit 1; }
  "$DX" --dex --output="$B/classes.dex" "$B/classes"
fi
"$AAPT" package -f -M AndroidManifest.xml -S res -A assets -I "$ANDROID_JAR" -F "$B/app.unsigned.apk"
(cd "$B" && "$AAPT" add app.unsigned.apk classes.dex >/dev/null)
"$ZIPALIGN" -f 4 "$B/app.unsigned.apk" "$B/app.aligned.apk"
"$APKSIGNER" sign --ks "$KEYSTORE" --ks-pass "pass:$KEYSTORE_PASSWORD" --key-pass "pass:$KEYSTORE_PASSWORD" \
  --ks-key-alias "$KEY_ALIAS" --out "$OUT" "$B/app.aligned.apk"
"$APKSIGNER" verify --print-certs "$OUT" | grep -m2 "Signer #1"
rm -f "$OUT.idsig"
echo "APK: $OUT ($(du -h "$OUT" | cut -f1))"

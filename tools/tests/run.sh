#!/usr/bin/env bash
# Автотесты эмулятора в headless Chromium (нужен node и пакет playwright).
#   tools/tests/run.sh            — основной набор
#   tools/tests/run.sh tlj tcu    — выбранные тесты
# Тесты открывают tools/tests/test.html — это src/emulator.html с доступом к внутренностям через window.__T.
set -euo pipefail
cd "$(dirname "$0")"
[ -z "${CHROMIUM:-}" ] && [ -x /opt/pw-browsers/chromium ] && export CHROMIUM=/opt/pw-browsers/chromium
sed 's/^\(\s*\)fresh(.tank.);setView(v0);/\1window.__T={get S(){return S},step,fresh,solve,setFault,doAct,sealed,AU,hReq,nozList,checkCalc,q6,ZM,showHoverTip,lessonJump,LESSONS};fresh('"'"'tank'"'"');setView(v0);/' \
  ../../src/emulator.html > test.html
grep -q 'window.__T=' test.html || { echo "Не удалось вставить хук __T"; exit 1; }
T=("$@"); [ ${#T[@]} -gt 0 ] || T=(tq tlj tsc tcu tseg tcab tavs)
for t in "${T[@]}"; do echo "== $t"; node "$t.js"; done

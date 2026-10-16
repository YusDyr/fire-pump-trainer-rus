#!/usr/bin/env bash
# tools/release.sh 3.8 — выпустить версию: проверяет раздел в CHANGELOG.md,
# пишет VERSION, коммитит и пушит в main. Дальше всё собирает GitHub Actions (release.yml).
set -euo pipefail
V="${1:?usage: tools/release.sh 3.8}"
cd "$(dirname "$0")/.."
grep -q "^## $V " CHANGELOG.md || { echo "В CHANGELOG.md нет раздела «## $V …»"; exit 2; }
echo "$V" > VERSION
git add -A src android tools CHANGELOG.md VERSION README.md DEVELOPMENT.md .github .gitignore
git commit -m "Версия $V"
git push origin main
echo "Отправлено. Сборка и релиз: https://github.com/YusDyr/fire-pump-trainer-rus/actions"

# Разработка и сборка

## Что где лежит

| Путь | Что это |
|---|---|
| `src/emulator.html` | **Исходник эмулятора** — один HTML-файл (разметка, стили, логика, базовое фото отсека и анимации внутри). Правки делаются здесь. |
| `src/ustroystvo/` | **Страница «Устройство насоса»**: анимированные разрезы ступеней НД (рис. 2) и ВД (рис. 5) по РЭ и 3D-модель насоса (three.js r147, без сети). `template.html` — код страницы; `*_ink.webp` / `*_mask.webp` — чертёж и маска областей (R — вода, G — масло, B: 255 — вал, 120 — охлаждение); `*_data.json` — пути частиц и координаты деталей; `model.json` + `model.bin` — модель из `cad/model/NCPK_nasos.glb` (координаты uint16, нормали int8). Собирается в `emulator/ustroystvo.html` и в APK, из эмулятора — кнопка «Устройство насоса». |
| `tools/make_ustroystvo.py` | Склеивает страницу «Устройство насоса» в один HTML (`python3 tools/make_ustroystvo.py out.html`); вызывается из `build.py`. |
| `emulator/` | Собранная веб-версия для GitHub Pages: `index.html`, `fonts/`, `photos/` (крупные планы). `index.html`, `ustroystvo.html` и `fonts/` пишет сборка, руками не править. `photos/` — исходные фото крупных планов (`*.webp` 2600 px и миниатюры `t/`). |
| `android/` | Обёртка APK: `AndroidManifest.xml`, `src/` (WebView), `res/` (иконки), `fonts/` + `fonts.css` (локальные шрифты), `icon512.png`. Каталоги `assets/` и `build/` создаются при сборке. |
| `tools/build.py` | Собирает `emulator/index.html` и `android/assets/` из `src/emulator.html`, ставит версию. |
| `tools/build_apk.sh` | Собирает и подписывает APK (aapt, javac, d8, zipalign, apksigner). |
| `tools/make_landing.py` | Генерирует лендинг `index.html` из `CHANGELOG.md` и `VERSION`. |
| `tools/release.sh` | Выпуск версии с локальной машины: проверяет CHANGELOG, пишет VERSION, пушит. |
| `tools/tests/` | Автотесты в headless Chromium (Playwright): `run.sh`. |
| `tools/anim/` | Скрипты подготовки фотоанимации рычагов и маховиков (SIFT/ECC-совмещение, `frames.json`, `wheels.json`). Читают оригиналы фотографий, которых нет в репозитории, — путь к ним задан в начале скриптов. |
| `tools/schem_gen.py` | Генератор SVG «Схемы потоков». |

## Выпуск версии

1. Внести изменения в `src/emulator.html`.
2. Добавить в начало `CHANGELOG.md` раздел `## X.Y — дата`.
3. Запустить `tools/release.sh X.Y` (или вручную поменять `VERSION` и запушить в `main`).

Дальше всё делает GitHub Actions (`.github/workflows/release.yml`): собирает веб-версию, APK и лендинг,
коммитит результаты в `main` и создаёт релиз `vX.Y` с APK и HTML.

При любом изменении `src/`, `android/`, `tools/` запускается проверочная сборка
(`.github/workflows/build.yml`): APK и HTML можно скачать в разделе Artifacts запуска.

## Ключ подписи APK

APK подписывается ключом `release.jks` (alias `ncpk`). **В репозиторий ключ не кладётся.**
Если ключ потерять, новые версии не установятся поверх старых — придётся удалять приложение на всех телефонах.

Для сборки в GitHub Actions нужны два секрета (Settings → Secrets and variables → Actions → New repository secret):

| Секрет | Значение |
|---|---|
| `ANDROID_KEYSTORE_B64` | содержимое `release.jks` в base64 (`base64 -w0 release.jks`) |
| `ANDROID_KEYSTORE_PASSWORD` | пароль хранилища и ключа |

## Локальная сборка

```bash
python3 tools/build.py 3.8
KEYSTORE=~/keys/release.jks KEYSTORE_PASSWORD=... tools/build_apk.sh
python3 tools/make_landing.py .
```

Нужны JDK 8+, Android SDK (build-tools с `aapt`, `d8`, `zipalign`, `apksigner` и любая `platforms/android-*`)
или пакеты Debian/Ubuntu `aapt zipalign apksigner dalvik-exchange android-sdk-platform-23`.

## Тесты

```bash
npm i -g playwright && npx playwright install chromium
tools/tests/run.sh            # основной набор
tools/tests/run.sh tlj        # прохождение всех уроков до конца
```

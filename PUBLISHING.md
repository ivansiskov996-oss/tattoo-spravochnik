# Публикация статей (ночной цикл)

Сайт: https://ivansiskov996-oss.github.io/tattoo-spravochnik/
Репозиторий: https://github.com/ivansiskov996-oss/tattoo-spravochnik (ветка `main`)
Хостинг: GitHub Pages, деплой — GitHub Actions (`.github/workflows/pages.yml`) при каждом push в `main`.

## Структура (локально: /workspace/tattoo-site/)
- `articles/<slug>.md` — статьи. Front matter: `title`, `description` (≤160 символов), `slug`, `date: "ГГГГ-ММ-ДД"`, `draft: true|false`, `keywords`.
- `images/<slug>/*.jpg` — фото статьи (локально — бинарные JPG, макс. 1200px, q80).
- `build.py` — сборщик (Python 3 + `markdown`): `python3 build.py` → `dist/`; `--include-drafts --out dist-drafts` — сборка со всеми черновиками для просмотра.
- `style-guide.md`, `topics.md` — правила и бэклог тем (в репозиторий не пушатся).
- `.publish/` — временные base64-копии картинок для пуша (не в git).

В репозиторий попадают ТОЛЬКО опубликованные статьи (`draft: false`) и их картинки. Черновики держим локально.

## Почему картинки в base64
Инструмент GitHub (MCP `push_files` / `create_or_update_file`) принимает только текст. Поэтому картинки пушатся как `images/<slug>/<file>.jpg.b64`, а workflow перед сборкой декодирует их обратно в JPG (`base64 -d`). Локальные `.jpg` и `.b64` должны совпадать.

## Шаги для одной новой статьи
1. **Написать статью** по `style-guide.md`, тему взять из `topics.md` (вычеркнуть). Сохранить `articles/<slug>.md`, поставить `date` = сегодня (Europe/Moscow) и `draft: false`. CTA-блок — как в опубликованных статьях (кнопка `https://t.me/tatunahody`, канал `https://t.me/tattoo_na_hodu`).
2. **Картинки**: 3–5 фото только со свободной лицензией для коммерческого использования (Wikimedia Commons / Flickr CC BY, CC BY-SA, CC0; Unsplash/Pexels/Pixabay). Проверить лицензию на странице фото, открыть файл и убедиться, что на нём то, что нужно. Сохранить в `images/<slug>/` с описательным транслит-именем, уменьшить до 1200px (q80). В Markdown: `![русский alt](../images/<slug>/file.jpg)` + строка подписи `*Подпись.* Фото: Автор, [Источник](url), лицензия [CC …](url).` В конце статьи — раздел `## Источники изображений`. Скобки в URL кодировать как `%28` `%29`.
3. **Собрать и проверить локально**: `python3 build.py` (должно быть «Built N article(s)»), открыть `dist/<slug>/index.html`, проверить, что в HTML есть `<figure>`, JSON-LD `Article` и `FAQPage`, а `sitemap.xml` и `llms.txt` содержат новую статью.
4. **Подготовить base64**: `for f in images/<slug>/*.jpg; do mkdir -p .publish/$(dirname $f); base64 -w0 $f > .publish/$f.b64; done`
5. **Запушить** через GitHub MCP (`user-GitHub-xai` → `push_files`, owner `ivansiskov996-oss`, repo `tattoo-spravochnik`, branch `main`):
   - сначала картинки (по 2–3 файла за коммит, `content: "$file:/workspace/tattoo-site/.publish/images/<slug>/<file>.jpg.b64"`, path `images/<slug>/<file>.jpg.b64`);
   - последним коммитом — `articles/<slug>.md` (тоже через `$file:`). Если менялся `build.py` — его тоже.
6. **Дождаться деплоя**: `actions_list` (workflow runs) → статус `success` (обычно 1–2 минуты).
7. **Проверить вживую**: `curl -sI https://ivansiskov996-oss.github.io/tattoo-spravochnik/<slug>/` → 200; каждая картинка → 200 и `content-type: image/jpeg`; `sitemap.xml` содержит URL.
8. **Отчёт** владельцу в Telegram: заголовок, ссылка, что проверено.

## Если что-то сломалось
- Workflow упал на `configure-pages` → в репозитории Settings → Pages → Source: «GitHub Actions» (делает владелец один раз).
- Картинка 404 → проверить, что `.b64` запушен по пути `images/<slug>/<имя>.jpg.b64` и имя совпадает со ссылкой в Markdown.
- Нельзя публиковать: выдуманные факты/статистику, фото без проверенной лицензии, реальные фото клиентов без их согласия.

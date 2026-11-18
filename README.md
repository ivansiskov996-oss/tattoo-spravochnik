# ТатуНаХоду — справочник по тату

Статический сайт-справочник тату-студии «ТатуНаХоду» (Москва).
Сайт: https://ivansiskov996-oss.github.io/tattoo-spravochnik/

- `articles/*.md` — статьи (Markdown + front matter; `draft: true` не публикуется).
- `images/<slug>/*.jpg.b64` — изображения статей (base64; декодируются в GitHub Actions).
- `build.py` — сборка в `dist/` (Python 3 + `markdown`).
- `.github/workflows/pages.yml` — сборка и деплой на GitHub Pages при push в `main`.

Фотографии — под свободными лицензиями (CC BY / CC BY-SA / CC0), авторы указаны под каждым фото и в конце статьи.
Тексты © ТатуНаХоду. Материалы не являются медицинской консультацией.

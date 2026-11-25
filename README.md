# Як? — Життєвий гід

Незалежний інформаційний гід, який пояснює, як вирішувати повсякденні питання в Україні. Чистий HTML/CSS/JS.

- Сайт: https://yak-life-guide.dmitriy-dovgal28.workers.dev/
- Локальний запуск: `python -m http.server 5173` і відкрити http://localhost:5173
- Дані: відкритий реєстр [Гід з державних послуг](https://guide.diia.gov.ua/) (CC BY 4.0), текст скорочено. Оновлення: `cd _build && python build.py` (потрібен `registry.json` з `/register/download/json/`).
- Статичні SEO-сторінки (блог, інструкції, події, послуги, sitemap.xml, robots.txt): `cd _build && python build_pages.py`. Базова адреса сайту — константа `SITE` у `_build/build_blog.py`; змінюйте її лише при підключенні власного домену.
- Матеріали мають інформаційний характер і не є юридичною консультацією.

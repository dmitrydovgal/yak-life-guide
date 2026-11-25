# -*- coding: utf-8 -*-
"""Генерує статичні SEO-сторінки блогу, sitemap.xml, robots.txt і blog-meta.js."""
import json, os, html, sys
sys.stdout.reconfigure(encoding='utf-8')
from articles import ARTICLES, SRC, DATE

SITE = 'https://dmitrydovgal.github.io/yak-life-guide/'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
e = html.escape
BY_SLUG = {a['slug']: a for a in ARTICLES}
MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']
def human(d):
    y, m, dd = d.split('-'); return f'{int(dd)} {MONTHS[int(m) - 1]} {y}'

def slugify_h(t):
    import re
    return 'h-' + re.sub(r'[^0-9a-zа-яіїєґ]+', '-', t.lower()).strip('-')

def page(depth, title, desc, canonical, body, extra_head='', og_type='website', active=''):
    r = '../' * depth
    nav = [(r + '#/topics', 'Усі теми', ''), (r + '#/events', 'Життєві події', ''), (r + 'blog/' if depth else 'index.html', 'Блог', 'blog'), (r + '#/about', 'Про проєкт', ''), (r + '#/saved', 'Збережене', '')]
    nav_html = ''.join(f'<a href="{h}"{" class=\"active\"" if k == active else ""}>{t}</a>' for h, t, k in nav)
    menu = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>'
    return f'''<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="uk_UA">
<meta property="og:site_name" content="Як? — Життєвий гід">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&subset=cyrillic&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}styles.css">
{extra_head}
</head>
<body>
<header class="header" id="header"><div class="container bar-row">
<a class="logo" href="{r or './'}" aria-label="Як? — на головну"><span class="logo-t">Як</span><span class="logo-q">?</span></a>
<nav class="nav" id="nav" aria-label="Головне меню">{nav_html}</nav>
<button class="burger" id="burger" type="button" aria-label="Меню" aria-expanded="false" aria-controls="nav">{menu}</button>
</div></header>
<main>{body}</main>
<footer class="footer"><div class="container foot-row"><span>Як? — демонстраційний прототип. Матеріали не є юридичною консультацією.</span><span class="foot-links"><a href="{r}blog/" >Блог</a><a href="{r}#/topics">Усі теми</a><a href="{r}#/about">Про проєкт</a></span></div></footer>
<script>document.getElementById('burger').onclick=function(){{var h=document.getElementById('header'),o=h.classList.toggle('open');this.setAttribute('aria-expanded',o)}}</script>
</body>
</html>
'''

def render_blocks(blocks):
    out, toc = [], []
    for k, v in blocks:
        if k == 'h2':
            i = slugify_h(v); toc.append((i, v)); out.append(f'<h2 id="{i}">{e(v)}</h2>')
        elif k == 'p': out.append(f'<p>{e(v)}</p>')
        elif k == 'ul': out.append('<ul>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ul>')
        elif k == 'ol': out.append('<ol>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ol>')
        elif k == 'note': out.append(f'<p class="callout">{e(v)}</p>')
    return '\n'.join(out), toc

def article_page(a):
    depth = 2
    url = f'{SITE}blog/{a["slug"]}/'
    body_html, toc = render_blocks(a['blocks'])
    toc_html = '<nav class="toc" aria-label="Зміст"><b>Зміст</b><ol>' + ''.join(f'<li><a href="#{i}">{e(t)}</a></li>' for i, t in toc) + '</ol></nav>' if len(toc) > 3 else ''
    faq_html = '<h2 id="faq">Часті запитання</h2>' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(ans)}</p></details>' for q, ans in a['faq'])
    src_html = '<h2 id="sources">Офіційні джерела</h2><ul>' + ''.join(f'<li><a href="{SRC[k][1]}" target="_blank" rel="noopener noreferrer">{e(SRC[k][0])}</a></li>' for k in a['src']) + '</ul>'
    cta = f'<aside class="cta-box"><b>Покрокова інструкція під вашу ситуацію</b><p>Відповімо на кілька запитань і покажемо кроки саме для вас.</p><a class="btn primary" href="../../#/i/{a["cta"][0]}">{e(a["cta"][1])}</a></aside>'
    rel = [BY_SLUG[s] for s in a['related'] if s in BY_SLUG]
    rel_html = '<h2 id="related">Читайте також</h2><ul class="related">' + ''.join(f'<li><a href="../{r["slug"]}/">{e(r["title"])}</a></li>' for r in rel) + '</ul>' if rel else ''
    body = f'''<article class="container post" itemscope itemtype="https://schema.org/Article">
<nav class="crumbs" aria-label="Навігація"><ol><li><a href="../../">Головна</a><span class="sep">›</span></li><li><a href="../">Блог</a><span class="sep">›</span></li><li><span aria-current="page">{e(a["cat"])}</span></li></ol></nav>
<p class="post-cat">{e(a["cat"])}</p>
<h1 itemprop="headline">{e(a["title"])}</h1>
<p class="post-meta"><time datetime="{DATE}" itemprop="datePublished">{human(DATE)}</time> · {a["min"]} хв читання</p>
<p class="post-lead">{e(a["lead"])}</p>
{toc_html}
<div itemprop="articleBody">{body_html}</div>
{cta}
{faq_html}
{src_html}
{rel_html}
<p class="callout">Матеріал має інформаційний характер, не є юридичною консультацією й може не враховувати останні зміни. Перед діями перевіряйте актуальну інформацію в офіційних джерелах.</p>
</article>'''
    ld = [{
        '@context': 'https://schema.org', '@type': 'Article', 'headline': a['title'], 'description': a['desc'], 'inLanguage': 'uk',
        'datePublished': DATE, 'dateModified': DATE, 'mainEntityOfPage': url,
        'author': {'@type': 'Organization', 'name': 'Як? — Життєвий гід'}, 'publisher': {'@type': 'Organization', 'name': 'Як? — Життєвий гід'}
    }, {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Головна', 'item': SITE},
            {'@type': 'ListItem', 'position': 2, 'name': 'Блог', 'item': SITE + 'blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': a['title'], 'item': url}]
    }, {
        '@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': ans}} for q, ans in a['faq']]
    }]
    extra = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    return page(depth, a['title'] + ' — Блог «Як?»', a['desc'], url, body, extra, 'article', 'blog')

def index_page():
    url = SITE + 'blog/'
    cards = ''.join(f'''<li><a class="post-card" href="{a["slug"]}/"><span class="post-cat">{e(a["cat"])}</span><b>{e(a["title"])}</b><span class="pc-d">{e(a["desc"])}</span><small>{human(DATE)} · {a["min"]} хв читання</small></a></li>''' for a in ARTICLES)
    body = f'''<div class="container"><nav class="crumbs" aria-label="Навігація"><ol><li><a href="../">Головна</a><span class="sep">›</span></li><li><span aria-current="page">Блог</span></li></ol></nav>
<div class="page-head" style="padding-top:8px"><h1>Блог</h1><p class="lead">Прості пояснення про важливе: як оплатити комуналку, відкрити ФОП, оформити документи та діяти в складних життєвих ситуаціях.</p></div>
<ul class="blog-grid">{cards}</ul></div>'''
    ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'Блог «Як?»', 'url': url, 'inLanguage': 'uk',
          'blogPost': [{'@type': 'BlogPosting', 'headline': a['title'], 'url': f'{url}{a["slug"]}/', 'datePublished': DATE} for a in ARTICLES]}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return page(1, 'Блог «Як?» — прості пояснення про важливе в Україні', 'Статті про комунальні послуги, ФОП, документи, нерухомість, авто та життєві ситуації. Покрокові пояснення простою мовою.', url, body, extra, 'website', 'blog')

def write(path, text):
    p = os.path.join(ROOT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8', newline='\n').write(text)

write('blog/index.html', index_page())
for a in ARTICLES: write(f'blog/{a["slug"]}/index.html', article_page(a))
urls = [SITE] + [SITE + 'blog/'] + [f'{SITE}blog/{a["slug"]}/' for a in ARTICLES]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc><lastmod>{DATE}</lastmod></url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
meta = [{'slug': a['slug'], 'title': a['title'], 'cat': a['cat'], 'min': a['min']} for a in ARTICLES]
write('blog-meta.js', 'const BLOG=' + json.dumps(meta, ensure_ascii=False) + ';\n')
print(len(ARTICLES), 'articles,', len(urls), 'urls')

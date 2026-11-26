# -*- coding: utf-8 -*-
"""Генерує статичні SEO-сторінки блогу, sitemap.xml, robots.txt і blog-meta.js."""
import json, os, html, sys
sys.stdout.reconfigure(encoding='utf-8')
from articles import ARTICLES, SRC, DATE

SITE = 'https://yak-life-guide.dmitriy-dovgal28.workers.dev/'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
e = html.escape
# Google Tag Manager: один контейнер для всіх згенерованих сторінок (головна index.html містить той самий код вручну)
GTM_ID = 'GTM-W2CXSFN8'
GTM_HEAD = ('<!-- Google Tag Manager -->\n'
            "<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':\n"
            "new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],\n"
            "j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n"
            "'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n"
            f"}})(window,document,'script','dataLayer','{GTM_ID}');</script>\n"
            '<!-- End Google Tag Manager -->')
GTM_BODY = ('<!-- Google Tag Manager (noscript) -->\n'
            f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"\n'
            'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n'
            '<!-- End Google Tag Manager (noscript) -->')
BY_SLUG = {a['slug']: a for a in ARTICLES}
MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']
def human(d):
    y, m, dd = d.split('-'); return f'{int(dd)} {MONTHS[int(m) - 1]} {y}'

def slugify_h(t):
    import re
    return 'h-' + re.sub(r'[^0-9a-zа-яіїєґ]+', '-', t.lower()).strip('-')

def page(depth, title, desc, canonical, body, extra_head='', og_type='website', active=''):
    r = '../' * depth
    nav = [(r + 'i/', 'Усі теми', 'topics'), (r + 'e/', 'Життєві події', 'events'), (r + 'documents/', 'Документи', 'documents'), (r + 'glossary/', 'Глосарій', 'glossary'), (r + 'blog/' if depth else 'index.html', 'Блог', 'blog'), (r + 'about/', 'Про проєкт', 'about'), (r + '#/saved', 'Збережене', '')]
    nav_html = ''.join(f'<a href="{h}"{" class=\"active\"" if k == active else ""}>{t}</a>' for h, t, k in nav)
    menu = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"><path d="M4 6h16M4 12h16M4 18h16"/></svg>'
    return f'''<!DOCTYPE html>
<html lang="uk">
<head>
{GTM_HEAD}
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
<meta property="og:image" content="{SITE}og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}og-image.png">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&subset=cyrillic&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}styles.css">
{extra_head}
</head>
<body>
{GTM_BODY}
<header class="header" id="header"><div class="container bar-row">
<a class="logo" href="{r or './'}" aria-label="Як? — на головну"><span class="logo-t">Як</span><span class="logo-q">?</span></a>
<nav class="nav" id="nav" aria-label="Головне меню">{nav_html}</nav>
<button class="burger" id="burger" type="button" aria-label="Меню" aria-expanded="false" aria-controls="nav">{menu}</button>
</div></header>
<main>{body}</main>
<footer class="footer"><div class="container foot-row"><span>Як? — незалежний інформаційний гід, не державний портал. Матеріали не є юридичною консультацією.</span><span class="foot-links"><a href="{r}blog/" >Блог</a><a href="{r}i/">Усі теми</a><a href="{r}e/">Життєві події</a><a href="{r}documents/">Документи</a><a href="{r}glossary/">Глосарій</a><a href="{r}about/">Про проєкт</a></span></div></footer>
<script>document.getElementById('burger').onclick=function(){{var h=document.getElementById('header'),o=h.classList.toggle('open');this.setAttribute('aria-expanded',o)}}</script>
</body>
</html>
'''

def render_blocks(blocks):
    out, toc = [], []
    for blk in blocks:
        k, v = blk[0], blk[1]
        if k == 'h2':
            i = slugify_h(v); toc.append((i, v)); out.append(f'<h2 id="{i}">{e(v)}</h2>')
        elif k == 'h3': out.append(f'<h3>{e(v)}</h3>')
        elif k == 'p': out.append(f'<p>{e(v)}</p>')
        elif k == 'link': out.append(f'<p>{e(v)} <a href="{blk[2]}" target="_blank" rel="noopener noreferrer">{e(blk[2])}</a></p>')
        elif k == 'ul': out.append('<ul>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ul>')
        elif k == 'ol': out.append('<ol>' + ''.join(f'<li>{e(x)}</li>' for x in v) + '</ol>')
        elif k == 'note': out.append(f'<p class="callout">{e(v)}</p>')
    return '\n'.join(out), toc

CAT_HUB = {'Комунальні послуги': ('utilities', 'Комунальні послуги'), 'ФОП і податки': ('fop', 'ФОП і податки'), 'Нерухомість': ('estate', 'Нерухомість'),
           'Документи': ('docs', 'Документи'), 'Сімʼя і життєві ситуації': ('family', 'Сім’я і життєві ситуації'), 'Здоровʼя': ('health', 'Здоров’я'), 'Авто': ('auto', 'Авто')}

def cta_href(cid):
    k, _, v = cid.partition(':')
    if not v: return 'i/' + cid
    return {'c': 'c/', 'e': 'e/', 'i': 'i/'}.get(k, '') + v if k != 's' else f's/{v}/-'

def article_page(a):
    depth = 2
    url = f'{SITE}blog/{a["slug"]}/'
    body_html, toc = render_blocks(a['blocks'])
    toc_html = '<nav class="toc" aria-label="Зміст"><b>Зміст</b><ol>' + ''.join(f'<li><a href="#{i}">{e(t)}</a></li>' for i, t in toc) + '</ol></nav>' if len(toc) > 3 else ''
    short_html = '<aside class="short"><b>Коротко</b><ul>' + ''.join(f'<li>{e(x)}</li>' for x in a['short']) + '</ul></aside>' if a.get('short') else ''
    lead_html = f'<p class="post-lead">{e(a["lead"])}</p>' if a.get('lead') else ''
    faq_html = ('<h2 id="faq">Часті запитання</h2>' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(ans)}</p></details>' for q, ans in a['faq'])) if a.get('faq') else ''
    srcs = a['sources'] if 'sources' in a else [SRC[k] for k in a['src']]
    src_html = ('<h2 id="sources">Офіційні та корисні джерела</h2><ul>' if srcs else '') + ''.join((f'<li>{e(l)}: <a href="{u}" target="_blank" rel="noopener noreferrer">{e(u)}</a></li>' if u else f'<li>{e(l)}</li>') for l, u in srcs) + ('</ul>' if srcs else '')
    cta_id, cta_text, cta_btn = (a['cta'] + (None,))[:3] if len(a['cta']) == 3 else (a['cta'][0], 'Відповімо на кілька запитань і покажемо кроки саме для вас.', a['cta'][1])
    cta = f'<aside class="cta-box"><b>Покрокова інструкція під вашу ситуацію</b><p>{e(cta_text)}</p><a class="btn primary" href="../../#/{cta_href(cta_id)}">{e(cta_btn)}</a></aside>'
    int_html = ''
    if a.get('internal'):
        int_html = '<h2 id="related">Читайте також</h2><ul class="related">' + ''.join(f'<li><a href="{u}">{e(t)}</a></li>' for t, u in a['internal']) + '</ul>'
    elif a.get('related'):
        rel = [BY_SLUG[s] for s in a['related'] if s in BY_SLUG]
        int_html = '<h2 id="related">Читайте також</h2><ul class="related">' + ''.join(f'<li><a href="../{r["slug"]}/">{e(r["title"])}</a></li>' for r in rel) + '</ul>'
    hub = CAT_HUB.get(a['cat'])
    if hub:
        int_html += f'<p class="hub-links">Розділ гіду: <a href="../../c/{hub[0]}/">{e(hub[1])}: усі інструкції</a> · <a href="../">Усі статті блогу</a></p>'
    disc = a.get('disclaimer') or 'Матеріал має інформаційний характер, не є юридичною консультацією й може не враховувати останні зміни. Перед діями перевіряйте актуальну інформацію в офіційних джерелах.'
    upd = f' · Оновлено: <time datetime="{a["modified"]}">{human(a["modified"])}</time>' if a['modified'] != a['date'] else ''
    body = f'''<article class="container post">
<nav class="crumbs" aria-label="Навігація"><ol><li><a href="../../">Головна</a><span class="sep">›</span></li><li><a href="../">Блог</a><span class="sep">›</span></li><li><span aria-current="page" title="{e(a["title"])}">{e(a["title"])}</span></li></ol></nav>
<p class="post-cat">{e(a["cat"])}</p>
<h1>{e(a["title"])}</h1>
<p class="post-meta">Опубліковано: <time datetime="{a['date']}">{human(a['date'])}</time>{upd} · {a["min"]} хв читання</p>
{lead_html}
{short_html}
{toc_html}
<div>{body_html}</div>
{cta}
{faq_html}
{src_html}
{int_html}
<p class="callout">{e(disc)}</p>
<p class="callout">Інформація може змінюватися: перед діями перевіряйте актуальні умови на офіційних сайтах і за потреби оновлюйте дані.</p>
</article>'''
    ld = [{
        '@context': 'https://schema.org', '@type': 'BlogPosting', 'headline': a['title'], 'description': a['desc'], 'inLanguage': 'uk',
        'datePublished': a['date'], 'dateModified': a['modified'], 'mainEntityOfPage': url,
        'author': {'@type': 'Organization', 'name': 'Як? — Життєвий гід'}, 'publisher': {'@type': 'Organization', 'name': 'Як? — Життєвий гід'}
    }, {
        '@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Головна', 'item': SITE},
            {'@type': 'ListItem', 'position': 2, 'name': 'Блог', 'item': SITE + 'blog/'},
            {'@type': 'ListItem', 'position': 3, 'name': a['title'], 'item': url}]
    }]
    if a.get('faq'):
        ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': ans}} for q, ans in a['faq']]})
    extra = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in ld)
    title = a.get('seo_title') or (a['title'] + ' — Блог «Як?»')
    return page(depth, title, a['desc'], url, body, extra, 'article', 'blog')

def index_page():
    url = SITE + 'blog/'
    cats = []
    for a in ARTICLES:
        if a['cat'] not in cats: cats.append(a['cat'])
    def hay(a):
        return ' '.join([a['title'], a['desc'], a['cat']] + a.get('short', [])).lower()
    cards = ''.join(f'''<li class="bcard" data-cat="{e(a["cat"])}" data-s="{e(hay(a))}"><a class="post-card" href="{a["slug"]}/"><span class="post-cat">{e(a["cat"])}</span><b>{e(a["title"])}</b><span class="pc-d">{e(a["desc"])}</span><small>{human(a['date'])} · {a["min"]} хв читання</small></a></li>''' for a in ARTICLES)
    chips = '<button type="button" class="chip on" data-cat="">Усі</button>' + ''.join(f'<button type="button" class="chip" data-cat="{e(c)}">{e(c)}</button>' for c in cats)
    script = r"""<script>(function(){
var q=document.getElementById('bq'),cards=[].slice.call(document.querySelectorAll('.bcard')),chips=[].slice.call(document.querySelectorAll('#bchips .chip')),empty=document.getElementById('bempty'),cnt=document.getElementById('bcount'),cat='';
function norm(t){return String(t).toLowerCase().replace(/[ʼ'`’]/g,'').replace(/ё/g,'е').replace(/ы/g,'и').replace(/э/g,'е')}
function run(){var t=norm(q.value).split(/\s+/).filter(Boolean),n=0;
cards.forEach(function(c){var h=norm(c.getAttribute('data-s')),ok=(!cat||c.getAttribute('data-cat')===cat)&&t.every(function(w){return h.indexOf(w)>-1});c.hidden=!ok;if(ok)n++});
empty.hidden=n>0;cnt.textContent=n===cards.length&&!t.length&&!cat?'':'Знайдено: '+n}
q.addEventListener('input',run);document.getElementById('bform').addEventListener('submit',function(e){e.preventDefault();run()});
document.getElementById('bclear').addEventListener('click',function(){q.value='';cat='';chips.forEach(function(c){c.classList.toggle('on',!c.getAttribute('data-cat'))});run();q.focus()});
chips.forEach(function(b){b.addEventListener('click',function(){cat=b.getAttribute('data-cat');chips.forEach(function(c){c.classList.toggle('on',c===b)});run()})})})();</script>"""
    body = f'''<div class="container blog-head"><nav class="crumbs" aria-label="Навігація"><ol><li><a href="../">Головна</a><span class="sep">›</span></li><li><span aria-current="page">Блог</span></li></ol></nav>
<div class="page-head" style="padding-top:8px"><h1>Блог</h1><p class="lead">Прості пояснення про важливе: як оплатити комуналку, відкрити ФОП, оформити документи та діяти в складних життєвих ситуаціях.</p></div>
<form class="searchbox plain" id="bform" role="search" autocomplete="off"><svg class="lead" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input id="bq" type="search" placeholder="Пошук по статтях, наприклад «ФОП» або «комуналка»" aria-label="Пошук по статтях"></form>
<div class="chips" id="bchips">{chips}</div>
<p class="muted" id="bcount" aria-live="polite"></p>
<ul class="blog-grid">{cards}</ul>
<div class="empty" id="bempty" hidden><h3>Нічого не знайдено</h3><p>Спробуйте інші слова або скиньте фільтри.</p><button type="button" class="btn ghost" id="bclear">Скинути пошук</button></div>
</div>{script}'''
    ld = {'@context': 'https://schema.org', '@type': 'Blog', 'name': 'Блог «Як?»', 'url': url, 'inLanguage': 'uk',
          'blogPost': [{'@type': 'BlogPosting', 'headline': a['title'], 'url': f'{url}{a["slug"]}/', 'datePublished': a['date'], 'dateModified': a['modified']} for a in ARTICLES]}
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    return page(1, 'Блог «Як?» — прості пояснення про важливе в Україні', 'Статті про комунальні послуги, ФОП, документи, нерухомість, авто та життєві ситуації. Покрокові пояснення простою мовою.', url, body, extra, 'website', 'blog')

def write(path, text):
    p = os.path.join(ROOT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    import time
    for attempt in range(6):   # на Windows файл може бути коротко зайнятий (сервер перегляду, антивірус)
        try:
            with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
            return
        except OSError:
            if attempt == 5: raise
            time.sleep(0.3 * (attempt + 1))

_LM = {f'{SITE}blog/{a["slug"]}/': a['modified'] for a in ARTICLES}
def _lm(u):
    return f'<lastmod>{_LM[u]}</lastmod>' if u in _LM else ''

import shutil
_blog = os.path.join(ROOT, 'blog')
for d in os.listdir(_blog) if os.path.isdir(_blog) else []:
    if os.path.isdir(os.path.join(_blog, d)) and d not in BY_SLUG: shutil.rmtree(os.path.join(_blog, d))
write('blog/index.html', index_page())
for a in ARTICLES: write(f'blog/{a["slug"]}/index.html', article_page(a))
urls = [SITE] + [SITE + 'blog/'] + [f'{SITE}blog/{a["slug"]}/' for a in ARTICLES]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc>{_lm(u)}</url>\n' for u in urls) + '</urlset>\n')
write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n')
meta = [{'slug': a['slug'], 'title': a['title'], 'cat': a['cat'], 'min': a['min']} for a in ARTICLES]
write('blog-meta.js', 'const BLOG=' + json.dumps(meta, ensure_ascii=False) + ';\n')

# 404.html: сторінка для неіснуючих адрес (noindex, без canonical, не в sitemap)
from urllib.parse import urlparse
_nf = page(0, 'Сторінку не знайдено — Як?', 'Такої сторінки немає. Скористайтеся пошуком або оберіть розділ.', SITE,
           '<div class="container narrow-m post"><h1>Сторінку не знайдено</h1><p class="post-lead">Можливо, посилання застаріло. Перейдіть на головну, відкрийте блог або оберіть потрібну тему.</p>'
           '<p><a class="btn primary" href="./">На головну</a> <a class="btn ghost" href="blog/">Блог</a> <a class="btn ghost" href="i/">Усі теми</a></p></div>')
_nf = _nf.replace(f'<link rel="canonical" href="{SITE}">' + chr(10), '').replace('<head>' + chr(10) + GTM_HEAD, '<head>' + chr(10) + GTM_HEAD + chr(10) + f'<base href="{urlparse(SITE).path}">' + chr(10) + '<meta name="robots" content="noindex">', 1)
write('404.html', _nf)
print(len(ARTICLES), 'articles,', len(urls), 'urls')

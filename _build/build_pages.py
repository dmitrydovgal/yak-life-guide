# -*- coding: utf-8 -*-
"""Статичні SEO-сторінки: інструкції /i/, категорії /c/, події /e/, послуги /s/ + sitemap.xml.
Потрібні: export.json (node, див. README у _build) і registry.json (реєстр Гіду Дія)."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
from build_blog import page, write, e, human, SITE, DATE, ARTICLES, ROOT, _lm

X = json.load(open(os.path.join(os.path.dirname(__file__), 'export.json'), encoding='utf-8'))
CATS = {c['id']: c for c in X['CATS']}
INS = X['INS']; FLOW = X['INS_FLOW']; EVENTS = X['GUIDE_EVENTS']; SECTORS = X['GUIDE_SECTORS']
REG = {z['identifier']: z for z in json.load(open(os.path.join(os.path.dirname(__file__), 'registry.json'), encoding='utf-8'))['entries']}

TR = dict(zip('абвгґдеєжзиіїйклмнопрстуфхцчшщьюя', ['a','b','v','h','g','d','e','ie','zh','z','y','i','i','y','k','l','m','n','o','p','r','s','t','u','f','kh','ts','ch','sh','shch','','iu','ia']))
def slug(t, n=55):
    s = ''.join(TR.get(c, c) for c in t.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    if len(s) > n: s = s[:n].rsplit('-', 1)[0]
    return s or 'posluga'

def cut(t, n):
    t = re.sub(r'\s+', ' ', str(t or '')).strip()
    if len(t) <= n: return t
    c = t[:n]; k = max(c.rfind('. '), c.rfind('; '), c.rfind(', '), c.rfind(' '))
    return (c[:k] if k > n * .55 else c).rstrip(' ,;.:') + '…'

def crumbs(items, r):
    out = []
    for i, (t, h) in enumerate(items):
        last = i == len(items) - 1
        out.append(f'<li>{"<span aria-current=\"page\">" + e(t) + "</span>" if last else "<a href=\"" + r + h + "\">" + e(t) + "</a><span class=\"sep\">›</span>"}</li>')
    return '<nav class="crumbs" aria-label="Навігація"><ol>' + ''.join(out) + '</ol></nav>'

def ld_script(objs):
    return ''.join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>\n' for o in objs)

def bc_ld(items):
    return {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u} for i, (n, u) in enumerate(items)]}

def cta(href, title, text, btn):
    return f'<aside class="cta-box"><b>{e(title)}</b><p>{e(text)}</p><a class="btn primary" href="{href}">{e(btn)}</a></aside>'


# ---------- Зв'язок інструкцій і розділів зі статтями блогу ----------
from build_blog import CAT_HUB
import svc_v2
def blog_block(cid, r):
    arts = [a for a in ARTICLES if CAT_HUB.get(a['cat'], ('',))[0] == cid]
    if not arts: return ''
    return '<h2>Статті блогу</h2><ul class="related">' + ''.join(f'<li><a href="{r}blog/{a["slug"]}/">{e(a["title"])}</a></li>' for a in arts) + '</ul>'
def ins_blog_block(iid, r):
    arts = [a for a in ARTICLES if a['cta'][0] == iid]
    if not arts: return ''
    return '<h2>Статті блогу за темою</h2><ul class="related">' + ''.join(f'<li><a href="{r}blog/{a["slug"]}/">{e(a["title"])}</a></li>' for a in arts) + '</ul>'

URLS = [SITE, SITE + 'blog/']
URLS += [f'{SITE}blog/{a["slug"]}/' for a in ARTICLES]
FOOT = '<p class="callout">Ми пояснюємо простими словами, але це не юридична консультація. Перед зверненням перевірте умови на офіційному сайті.</p>'

# ---------- Послуги ----------
svc_url = {}; svc_event = {}
for ev in EVENTS:
    for sec, ids in SECTORS[ev['id']]:
        for sid in ids: svc_event.setdefault(sid, ev['id'])
svc_title = {}
for ev in EVENTS:
    for sec, ids in SECTORS[ev['id']]:
        for sid in ids:
            if sid in svc_url: continue
            z = REG.get(sid)
            if not z: continue
            kw = re.sub(r'\s+', ' ', z.get('keyword') or '').strip()
            n = kw if kw and len(kw) <= 110 else cut(z['name'], 110)
            svc_title[sid] = n
            svc_url[sid] = f's/{sid}-{slug(n)}/'

def lst(v):
    if isinstance(v, str):
        v = v.strip()
        if v.startswith('['):
            try: import ast; return [str(x) for x in ast.literal_eval(v)]
            except Exception: pass
        return [x.strip() for x in re.split(r'\s*\|\s*', v) if x.strip()]
    return [str(x) for x in (v or [])]


# ---------- Сценарії послуг ----------
import journey
JOURNEYS = {}
_sector_of = {}
for _ev in EVENTS:
    for _sec, _ids in SECTORS[_ev['id']]:
        for _sid in _ids:
            _sector_of.setdefault(_sid, _ids)
def related_of(sid):
    return [(svc_title[x], '../../' + svc_url[x]) for x in _sector_of.get(sid, []) if x != sid and x in svc_url]

def _svc_desc(sid):
    z = REG[sid]; n = svc_title[sid]
    full = ' '.join(lst(z.get('short_description_plain')) or [n])
    return cut(re.sub(r'\s+', ' ', z.get('short_description_plain') or full), 155)
def _svc_base_title(sid): return cut(svc_title[sid], 72) + ' — документи, строки, вартість'
import collections as _c
_tc = _c.Counter(_svc_base_title(s) for s in svc_title)
_dc = _c.Counter(_svc_desc(s) for s in svc_title)

def service_page(sid):
    z = REG[sid]; n = svc_title[sid]; url = SITE + svc_url[sid]; ev = next(x for x in EVENTS if x['id'] == svc_event[sid])
    full = re.sub(r'\s+', ' ', z['name']).strip()
    desc_full = cut(z.get('short_description_plain') or full, 1400)
    docs = [cut(d, 260) for d in lst(z.get('input'))][:14]
    prov = [cut(p, 160) for p in lst(z.get('service_provider'))][:6]
    prod = [cut(p, 160) for p in lst(z.get('produces'))][:5]
    appl = [cut(p, 100) for p in lst(z.get('applicant_type'))][:4]
    refus = [cut(p, 300) for p in lst(z.get('refusal_grounds'))][:5]
    ways = []
    for w in lst(z.get('application_ways')):
        if ':' in w:
            for p in re.split(r'[;,]', w.split(':', 1)[1]):
                p = p.strip()
                if p and p not in ways: ways.append(p)
    cost = cut(z.get('costs'), 300); dur = cut(z.get('processing_durations'), 300)
    link = (z.get('access_link') or '').strip(); link = link if link.startswith('http') else ''
    owner = cut(z.get('owner'), 160); spatial = cut(z.get('spatial'), 80)
    rows = [('Строк надання', dur), ('Вартість', cost), ('Для кого', ', '.join(appl)), ('Де діє', spatial), ('Хто надає', owner)]
    kv = '<dl class="kv">' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in rows if v) + '</dl>'
    guide = f'https://guide.diia.gov.ua/register/{sid}/'
    steps = ['Перевірте, чи послуга підходить вам: для кого вона та де діє.', 'Підготуйте документи за переліком вище (деякі потрібні лише в окремих випадках).',
             'Оберіть спосіб звернення' + (f': {", ".join(w.lower() for w in ways)}.' if ways else '.'),
             'Подайте заяву' + (f' до: {"; ".join(prov[:2])}.' if prov else ' до органу, що надає послугу.'),
             'Дочекайтеся результату' + (f' (строк: {dur}).' if dur else '.')]
    body = f'''<article class="container post">
{crumbs([('Головна', ''), ('Життєві події', 'e/'), (ev['title'], f'e/{ev["id"]}/'), (n, '')], '../../')}
<p class="post-cat">{e(ev["title"])}</p>
<h1>{e(n)}</h1>
{f'<p class="post-meta">Повна назва: {e(full)}</p>' if full.lower() != n.lower() else ''}
<p class="post-lead">{e(desc_full)}</p>
<aside class="short"><b>Коротко</b>{kv}</aside>
{('<h2>Що знадобиться</h2><ul>' + ''.join(f'<li>{e(d)}</li>' for d in docs) + '</ul>') if docs else ''}
<h2>Як отримати послугу</h2>
<ol>{''.join(f'<li>{e(s)}</li>' for s in steps)}</ol>
{('<h3>Куди звернутися</h3><ul>' + ''.join(f'<li>{e(p)}</li>' for p in prov) + '</ul>') if prov else ''}
{('<p>Онлайн-сервіс: <a href="' + e(link) + '" target="_blank" rel="noopener noreferrer">' + e(link) + '</a></p>') if link else ''}
{('<h2>Що ви отримаєте</h2><ul>' + ''.join(f'<li>{e(p)}</li>' for p in prod) + '</ul>') if prod else ''}
{('<h2>Підстави для відмови</h2><ul>' + ''.join(f'<li>{e(p)}</li>' for p in refus) + '</ul>') if refus else ''}
{cta(f'../../#/s/{sid}/-', 'Персональна інструкція', 'Вкажіть місто, і ми покажемо кроки для вашої ситуації: куди йти, що взяти, скільки часу це займе.', 'Отримати персональну інструкцію')}
<p>Повна інформація та нормативна база: <a href="{guide}" target="_blank" rel="noopener noreferrer">Гід з державних послуг, послуга № {e(sid)}</a>.</p>
{FOOT}
<p class="source">Джерело даних: <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a> (відкритий реєстр, ліцензія CC BY 4.0), текст скорочено. Сторінку сформовано {human(DATE)}.</p>
</article>'''
    j = journey.build(sid, z, related_of(sid), svc_url)
    JOURNEYS[sid] = j
    d = re.sub(r'\s+', ' ', str(z.get('short_description_plain') or '')).strip()
    lead_html = ''
    if d and d.lower() not in (full.lower(), n.lower()):
        sents = re.split(r'(?<=[.!?])\s+(?=[А-ЯЇІЄҐA-Z0-9«"])', d)
        acc = ''
        for s_ in sents:
            if acc and len(acc) + len(s_) > 300: break
            acc = (acc + ' ' + s_).strip()
        if len(acc) > 340: acc = cut(acc, 300)
        rest = d[len(acc):].strip() if d.startswith(acc) else ''
        lead_html = f'<p class="post-lead">{e(acc)}</p>' + (f'<details class="more"><summary>Детальніше про послугу</summary><p>{e(rest)}</p></details>' if rest else '')
        if j.get('ed'):   # є перевірене пояснення простими словами — офіційний опис реєстру згортаємо під нього
            lead_html = f'<details class="more"><summary>Офіційний опис послуги з реєстру</summary><p>{e(d)}</p></details>'
    body = f'''<article class="container post svc2">
{crumbs([('Головна', ''), ('Життєві події', 'e/'), (ev['title'], f'e/{ev["id"]}/'), (n, '')], '../../')}
<p class="post-cat">{e(ev["title"])}</p>
<h1>{e(n)}</h1>
{journey.render_static(j, lead_html)}
{sections.terms_line(sid, '../../')}
{FOOT}
<p class="source">Джерело даних: <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a> (відкритий реєстр, ліцензія CC BY 4.0), текст скорочено. Сторінку сформовано {human(DATE)}.</p>
</article>
<script src="../../journey.js" defer></script>'''
    ld = [bc_ld([('Головна', SITE), ('Життєві події', SITE + 'e/'), (ev['title'], f'{SITE}e/{ev["id"]}/'), (n, url)]),
          {'@context': 'https://schema.org', '@type': 'GovernmentService', 'name': n, 'description': cut(desc_full, 300), 'serviceType': ev['title'],
           'areaServed': {'@type': 'Country', 'name': 'Україна'}, 'inLanguage': 'uk', 'url': url,
           **({'provider': {'@type': 'GovernmentOrganization', 'name': owner}} if owner else {})}]
    title = _svc_base_title(sid)
    if _tc[title] > 1: title = cut(n, 58) + f' (№ {sid}) — документи, строки'
    sdesc = _svc_desc(sid)
    if _dc[sdesc] > 1: sdesc = f'№ {sid}. ' + cut(n, 55) + ': ' + cut(re.sub(r'\s+', ' ', z.get('short_description_plain') or full), 90)
    return page(2, title, sdesc, url, body, ld_script(ld), 'article', 'events')

import sections   # розділи «Документи» і «Глосарій» (дані: docs_db.py, glossary.py)
sections.init(page=page, write=write, e=e, SITE=SITE, crumbs=crumbs, bc_ld=bc_ld, ld_script=ld_script, cut=cut,
              svc_url=svc_url, svc_title=svc_title, REG=REG, FOOT=FOOT, URLS=URLS)

for sid in svc_url:
    write(svc_url[sid] + 'index.html', service_page(sid)); URLS.append(SITE + svc_url[sid])
write('s/map.json', json.dumps({k: v for k, v in svc_url.items()}, ensure_ascii=False))
print('journeys:', len(JOURNEYS), '| with questions:', sum(1 for j in JOURNEYS.values() if j['questions']), '| need editorial review:', sum(1 for j in JOURNEYS.values() if j['review']))

# ---------- Події ----------
def event_page(ev):
    url = f'{SITE}e/{ev["id"]}/'
    secs = SECTORS[ev['id']]; total = sum(len(s[1]) for s in secs)
    parts = []
    for name, ids in secs:
        parts.append(f'<h2>{e(name)}</h2><ul class="related">' + ''.join(f'<li><a href="../../{svc_url[i]}">{e(svc_title[i])}</a></li>' for i in ids if i in svc_url) + '</ul>')
    body = f'''<article class="container post">
{crumbs([('Головна', ''), ('Життєві події', 'e/'), (ev['title'], '')], '../../')}
<p class="post-cat">{'Для бізнесу' if ev['aud'] == 'b' else 'Для громадян'}</p>
<h1>{e(ev["title"])}: державні послуги</h1>
<p class="post-lead">{e(ev["desc"])} У добірці {total} послуг з відкритого реєстру «Гід з державних послуг».</p>
{cta('../../#/e/' + ev['id'], 'Не знаєте, що саме потрібно?', 'Оберіть тему та послугу, а далі отримайте персональну покрокову інструкцію.', 'Підібрати послугу в гіді')}
{''.join(parts)}
{FOOT}
<p class="source">Джерело даних: <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a> (CC BY 4.0).</p>
</article>'''
    ld = [bc_ld([('Головна', SITE), ('Життєві події', SITE + 'e/'), (ev['title'], url)])]
    return page(2, f'{ev["title"]}: державні послуги, документи та інструкції', cut(ev['desc'] + (' Державні послуги, документи та покрокові інструкції.' if len(ev['desc']) < 90 else ''), 155), url, body, ld_script(ld), 'website', 'events')

for ev in EVENTS:
    write(f'e/{ev["id"]}/index.html', event_page(ev)); URLS.append(f'{SITE}e/{ev["id"]}/')

def events_hub():
    url = SITE + 'e/'
    g = lambda a: ''.join(f'<li><a href="{ev["id"]}/">{e(ev["title"])}</a><small>{ev["n"]} послуг</small></li>' for ev in EVENTS if ev['aud'] == a)
    body = f'''<div class="container post">{crumbs([('Головна', ''), ('Життєві події', '')], '../')}
<h1>Життєві події: державні послуги в Україні</h1>
<p class="post-lead">Оберіть ситуацію й дізнайтеся, які послуги потрібні, які документи підготувати та куди звертатися.</p>
<h2>Для громадян</h2><ul class="related ev-links">{g('c')}</ul>
<h2>Для бізнесу</h2><ul class="related ev-links">{g('b')}</ul>
{cta('../#/events', 'Пошук по всіх послугах', 'У гіді можна знайти потрібну послугу за назвою й отримати персональну інструкцію.', 'Відкрити гід')}
</div>'''
    return page(1, 'Життєві події: державні послуги, документи та інструкції — Як?', 'Каталог життєвих подій і державних послуг України: народження дитини, паспорт, переїзд, бізнес та інше. Документи, строки й вартість.', url, body, ld_script([bc_ld([('Головна', SITE), ('Життєві події', url)])]), 'website', 'events')
write('e/index.html', events_hub()); URLS.append(SITE + 'e/')

# ---------- Інструкції та категорії ----------
def steps_ol(steps):
    return '<ol>' + ''.join(f'<li><b>{e(s[0])}.</b> {e(s[1]) if len(s) > 1 else ""}</li>' for s in steps) + '</ol>'

def split(x): return x.split('|') if isinstance(x, str) else x

def ins_page(i):
    ins = INS[i]; cat = CATS[ins['cat']]; url = f'{SITE}i/{i}/'
    parts = []
    if ins.get('flow') == 'komunalka':
        sv = X['SERVICES']
        parts.append('<h2>Способи оплати</h2>' + ''.join(f'<h3>{e(s["name"])}</h3><p>{e(s["desc"])}</p><p><b>Чому варто спробувати:</b> {e(s["why"])}</p><ul>' + ''.join(f'<li>{e(p)}</li>' for p in s['pros']) + ''.join(f'<li>Обмеження: {e(c)}</li>' for c in s['cons']) + f'</ul><p><a href="{s["url"]}" target="_blank" rel="noopener noreferrer">Перейти до {e(s["name"])}</a></p>' for s in sv.values()))
        parts.append('<h2>Приват24: покрокова інструкція</h2>' + steps_ol([split(x) for x in sv['privat24']['steps']]))
        parts.append('<h2>Часті запитання</h2>' + ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in X['KOM_FAQ']))
        parts.append('<p>Докладніше: <a href="../../blog/yak-oplatyty-komunalku-online/">Як оплатити комуналку онлайн в Україні у 2026 році</a>.</p>')
    elif i in journey.INS_ED:
        ed = journey.INS_ED[i]
        jd = {'type': 'ed-page', 'id': i, 'name': ins['title'], 'ed': ed, 'questions': []}
        data = json.dumps(jd, ensure_ascii=False).replace('</', '<\\/')
        parts.append(f'<aside class="short"><b>Простими словами</b><p>{e(ed["intro"])}</p></aside><div class="j-root" id="journey" data-sid="{i}"></div>'
                     f'<div class="j-ref" id="j-ref">{journey.render_ed_static(ed)}</div>'
                     f'<script type="application/json" id="journey-data">{data}</script><script src="../../journey.js" defer></script>')
        parts.append('<h2>Часті запитання</h2>' + ''.join(f'<details><summary>{e(q[0])}</summary><p>{e(q[1])}</p></details>' for q in ins['faq']))
        parts.append('<h2>Офіційні посилання</h2><ul>' + ''.join(f'<li><a href="{l[1]}" target="_blank" rel="noopener noreferrer">{e(l[0])}</a></li>' for l in ins['links']) + '</ul>')
    elif i == 'fop-group':
        import custom_fop
        parts.append(custom_fop.render_static())
        parts.append('<h2>Часті запитання</h2>' + ''.join(f'<details><summary>{e(q[0])}</summary><p>{e(q[1])}</p></details>' for q in ins['faq']))
    else:
        if ins['needs']: parts.append('<h2>Що знадобиться</h2><ul>' + ''.join(f'<li>{e(n)}</li>' for n in ins['needs']) + '</ul>')
        parts.append('<h2>Покрокова інструкція</h2>' + steps_ol(ins['steps']))
        w = ins.get('wizard')
        if w:
            parts.append(f'<h2>{e(w["q"])}</h2><p>{e(w["sub"])}</p>')
            for o in w['options']:
                ov = o['over']
                parts.append(f'<h3>{e(o["label"])}</h3><p>{e(ov.get("why", o["desc"]))}</p>' + (('<ul>' + ''.join(f'<li>{e(n)}</li>' for n in ov['needs']) + '</ul>') if ov.get('needs') else '') + steps_ol([split(s) for s in ov['steps']]))
        parts.append('<h2>Можливі способи</h2><ul>' + ''.join(f'<li><b>{e(m[0])}.</b> {e(m[1])}</li>' for m in ins['methods']) + '</ul>')
        parts.append('<h2>Часті запитання</h2>' + ''.join(f'<details><summary>{e(q[0])}</summary><p>{e(q[1])}</p></details>' for q in ins['faq']))
        parts.append('<h2>Офіційні посилання</h2><ul>' + ''.join(f'<li><a href="{l[1]}" target="_blank" rel="noopener noreferrer">{e(l[0])}</a></li>' for l in ins['links']) + '</ul>')
    others = [k for k, v in INS.items() if v['cat'] == ins['cat'] and k != i][:5]
    body = f'''<article class="container post">
{crumbs([('Головна', ''), (cat['title'], f'c/{cat["id"]}/'), (ins['title'], '')], '../../')}
<p class="post-cat">{e(cat["title"])}</p>
<h1>{e(ins["title"])}</h1>
<p class="post-meta">Орієнтовний час: {e(ins["time"])} · Оновлено: {human(DATE)}</p>
<p class="post-lead">{e(ins["summary"])}</p>
{'' if i == 'fop-group' or i in journey.INS_ED else cta('../../#/i/' + i, 'Персональна інструкція', 'Вкажіть місто та відповідь на кілька запитань, і ми підставимо кроки під вашу ситуацію.', 'Отримати персональну інструкцію')}
{''.join(parts)}
{FOOT}
<h2>Читайте також</h2><ul class="related">{''.join(f'<li><a href="../{k}/">{e(INS[k]["title"])}</a></li>' for k in others)}</ul>
{ins_blog_block(i, '../../')}
</article>'''
    ld = [bc_ld([('Головна', SITE), (cat['title'], f'{SITE}c/{cat["id"]}/'), (ins['title'], url)])]
    faq = [] if ins.get('flow') else ins['faq']
    if faq: ld.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': q[0], 'acceptedAnswer': {'@type': 'Answer', 'text': q[1]}} for q in faq]})
    return page(2, f'{ins["title"]} Покрокова інструкція — Як?', cut(ins['summary'] + (' Покрокова інструкція з посиланнями на офіційні сервіси.' if len(ins['summary']) < 90 else ''), 155), url, body, ld_script(ld), 'article', 'topics')

for i in INS:
    write(f'i/{i}/index.html', ins_page(i)); URLS.append(f'{SITE}i/{i}/')

for cid, c in CATS.items():
    url = f'{SITE}c/{cid}/'
    items = [k for k, v in INS.items() if cid in v.get('cats', [v['cat']])]
    body = f'''<div class="container post">{crumbs([('Головна', ''), (c['title'], '')], '../../')}
<h1>{e(c["title"])}: покрокові інструкції</h1><p class="post-lead">{e(c["desc"])}</p>
<ul class="related">{''.join(f'<li><a href="../../i/{k}/">{e(INS[k]["title"])}</a><small>{e(INS[k]["time"])}</small></li>' for k in items)}</ul>
{blog_block(cid, '../../')}
{cta('../../#/c/' + cid, 'Пошук у розділі', 'Відкрийте гід, щоб шукати інструкції та отримувати персональні кроки.', 'Відкрити розділ у гіді')}
</div>'''
    write(f'c/{cid}/index.html', page(2, f'{c["title"]}: інструкції та поради — Як?', cut(c['desc'], 155), url, body, ld_script([bc_ld([('Головна', SITE), (c['title'], url)])]), 'website', 'topics'))
    URLS.append(url)

def topics_hub():
    url = SITE + 'i/'
    secs = ''.join(f'<h2><a href="../c/{cid}/">{e(c["title"])}</a></h2><ul class="related">' + ''.join(f'<li><a href="{k}/">{e(v["title"])}</a><small>{e(v["time"])}</small></li>' for k, v in INS.items() if cid in v.get('cats', [v['cat']])) + '</ul>' for cid, c in CATS.items())
    body = f'''<div class="container post">{crumbs([('Головна', ''), ('Усі теми', '')], '../')}
<h1>Усі теми та покрокові інструкції</h1><p class="post-lead">Як оплатити комуналку, відкрити ФОП, замінити паспорт та вирішити інші життєві питання.</p>{secs}
{cta('../#/topics', 'Пошук по всіх темах', 'Відкрийте гід, щоб шукати інструкції та отримувати персональні кроки.', 'Відкрити гід')}</div>'''
    return page(1, 'Усі теми: покрокові інструкції для життєвих ситуацій — Як?', 'Інструкції про комунальні послуги, ФОП, нерухомість, документи, авто та здоров’я. Прості пояснення й посилання на офіційні сервіси.', url, body, ld_script([bc_ld([('Головна', SITE), ('Усі теми', url)])]), 'website', 'topics')
write('i/index.html', topics_hub()); URLS.append(SITE + 'i/')


# ---------- Про проєкт ----------
def about_page():
    url = SITE + 'about/'
    n_s, n_i, n_e, n_c, n_b = len(svc_url), len(INS), len(EVENTS), len(CATS), len(ARTICLES)
    body = f"""<article class="container post">
{crumbs([('Головна', ''), ('Про проєкт', '')], '../')}
<h1>Про проєкт «Як?»</h1>
<p class="post-lead">«Як?» — це цифровий помічник, який простою мовою пояснює, як вирішувати повсякденні життєві питання в Україні: від оплати комуналки до відкриття ФОП, заміни паспорта чи дій у складних життєвих ситуаціях.</p>
<aside class="short"><b>Коротко</b><ul>
<li>Покрокові інструкції з посиланнями на офіційні державні та комерційні сервіси.</li>
<li>Мінімум запитань: лише те, що впливає на результат, наприклад місто чи адреса.</li>
<li>«Як?» — незалежний інформаційний гід, а не державний портал і не юридична консультація.</li>
</ul></aside>
<h2>Для кого цей сервіс</h2>
<p>Для людей, які вперше стикаються з певною справою й не знають, з чого почати: що підготувати, куди звернутися, скільки це займе часу та скільки коштуватиме. Ми не вимагаємо знання юридичних термінів і пояснюємо складні поняття простими словами.</p>
<h2>Як це працює</h2>
<ol>
<li>Опишіть, що вам потрібно зробити, у пошуку або оберіть тему чи життєву подію.</li>
<li>Вкажіть місто та, якщо потрібно, адресу. Ми питаємо лише те, що змінює інструкцію.</li>
<li>Уточніть ситуацію або спосіб подання, наприклад онлайн чи особисто.</li>
<li>Отримайте персональну покрокову інструкцію з документами, строками й посиланнями на офіційні сервіси.</li>
</ol>
<p><a href="../#/topics">Відкрити сервіс і знайти інструкцію</a></p>
<h2>Що всередині</h2>
<ul>
<li><a href="../i/">{n_i} покрокових інструкцій</a> у {n_c} тематичних розділах: ФОП і податки, нерухомість, комунальні послуги, здоров’я, сімейні та життєві ситуації, документи, авто.</li>
<li><a href="../e/">{n_e} життєвих подій</a> і {n_s} державних послуг з документами, строками та вартістю.</li>
<li><a href="../blog/">Блог</a> із {n_b} статтями-поясненнями.</li>
</ul>
<h2>Звідки беруться дані</h2>
<p>Каталог державних послуг сформовано з відкритого реєстру <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">«Гід з державних послуг»</a> (ліцензія CC BY 4.0), текст скорочено. Посилання на сервіси оплати, державні портали та реєстри ведуть на їхні офіційні сайти. Перелік можливостей сторонніх сервісів, зокрема покриття міст, може змінюватися, тому перед діями варто перевіряти його на сайті сервісу.</p>
<h2>Наші принципи</h2>
<ul>
<li><b>Простота.</b> Найкоротший і найзручніший шлях показуємо першим, альтернативи нижче.</li>
<li><b>Прозорість.</b> Пояснюємо, чому пропонуємо саме такий варіант, і чесно позначаємо обмеження.</li>
<li><b>Приватність.</b> Не просимо паспорт, телефон чи платіжні дані. Збережені інструкції та введена адреса зберігаються лише у вашому браузері.</li>
<li><b>Без вигадок.</b> Якщо кроки не підтверджені актуальним джерелом, ми прямо зазначаємо це на сторінці.</li>
</ul>
<h2>Важливе застереження</h2>
<p>«Як?» не є державним порталом, банком чи платіжним сервісом. Матеріали мають інформаційний характер, можуть не враховувати останні зміни законодавства й не замінюють індивідуальну консультацію юриста, нотаріуса чи бухгалтера. Подання заяв і платежі відбуваються на сайтах відповідних органів і сервісів, а не на «Як?».</p>
{cta('../#/topics', 'Спробуйте самі', 'Оберіть тему або життєву подію й отримайте персональну інструкцію за кілька кроків.', 'Знайти інструкцію')}
</article>"""
    ld = [bc_ld([('Головна', SITE), ('Про проєкт', url)]),
          {'@context': 'https://schema.org', '@type': 'AboutPage', 'name': 'Про проєкт «Як?»', 'url': url, 'inLanguage': 'uk',
           'description': 'Цифровий помічник, який простою мовою пояснює, як вирішувати повсякденні життєві питання в Україні.',
           'about': {'@type': 'Organization', 'name': 'Як? — Життєвий гід', 'url': SITE}}]
    return page(1, 'Про проєкт «Як?» — життєвий гід з покроковими інструкціями', 'Що таке «Як?»: сервіс, який простою мовою пояснює, як вирішувати повсякденні питання в Україні. Принципи, джерела даних і важливі застереження.', url, body, ld_script(ld), 'website', 'about')
write('about/index.html', about_page()); URLS.append(SITE + 'about/')

# ---------- sitemap ----------
_nd, _nt = sections.build()
print(f'documents: {_nd} pages; glossary: {_nt} terms')
seen = []; [seen.append(u) for u in URLS if u not in seen]
write('sitemap.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{u}</loc>{_lm(u)}</url>\n' for u in seen) + '</urlset>\n')
print(len(seen), 'urls;', len(svc_url), 'services;', len(INS), 'instructions;', len(EVENTS), 'events')

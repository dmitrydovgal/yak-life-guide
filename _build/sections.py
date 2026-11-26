"""Розділи «Документи» (/documents/) і «Глосарій» (/glossary/).

Дані: docs_db.py (документи та їхні зв'язки з послугами), glossary.py (терміни).
Сторінки будуються тим самим шаблоном page(), що й решта сайту; адреси додаються до sitemap.
Порожніх сторінок не створюємо: документ із page=False показується лише в блоці послуги.
"""
import json, re
import docs_db as D
import glossary as G

_ctx = {}
PRIO = {}


def init(**kw):
    """page, write, e, SITE, crumbs, bc_ld, ld_script, cut, svc_url, svc_title, REG, FOOT, URLS"""
    _ctx.update(kw)
    try:
        import os
        pr = json.load(open(os.path.join(os.path.dirname(__file__), 'priority.json'), encoding='utf-8'))
        PRIO.update({x['id']: -x['score'] for x in pr})
    except OSError:
        pass
    D.check(); G.check(set(D.DOCS))
    _index_terms()


def _c(k): return _ctx[k]


def _e(t): return _ctx['e'](t)


DOC_PAGES = [i for i, d in D.DOCS.items() if d.get('page') is not False]
CAT_TITLE = dict(D.CATS)


def _svc_text(sid):
    z = _c('REG').get(sid) or {}
    inp = z.get('input'); inp = inp if isinstance(inp, str) else ' '.join(map(str, inp or []))
    return (z.get('name') or '') + ' ' + (z.get('keyword') or '') + ' ' + inp


_TERM_SVCS = {}; _SVC_TERMS = {}


def _index_terms():
    """Пов'язуємо терміни з послугами: за назвою (сильний зв'язок) і за переліком документів (для рядка на сторінці послуги)."""
    svc = _c('svc_url')
    for t in G.TERMS:
        if not t.get('rx'): continue
        rx = re.compile(t['rx'], re.I)
        nm = lambda s: ((_c('REG').get(s) or {}).get('name') or '') + ' ' + ((_c('REG').get(s) or {}).get('keyword') or '')
        by_name = [s for s in svc if rx.search(nm(s))]
        by_doc = [s for d in t['docs'] for s in D.services_of(d) if s in svc and s not in by_name]
        _TERM_SVCS[t['slug']] = (sorted(by_name, key=lambda s: (PRIO.get(s, 0), s)) + sorted(set(by_doc), key=lambda s: (PRIO.get(s, 0), s)))[:8]
        for s in svc:
            if rx.search(_svc_text(s)): _SVC_TERMS.setdefault(s, []).append(t['slug'])


def terms_line(sid, r):
    """Рядок «Незрозумілі слова» на сторінці послуги (до 6 термінів, у порядку глосарію)."""
    ts = _SVC_TERMS.get(sid, [])[:6]
    if not ts: return ''
    return ('<p class="terms-line"><b>Незрозумілі слова:</b> '
            + ' · '.join(f'<a href="{r}glossary/{s}/">{_e(G.TERM_BY_SLUG[s]["term"])}</a>' for s in ts) + '</p>')


def _svc_links(ids, r):
    ids = sorted(ids, key=lambda s: (PRIO.get(s, 0), s))
    return '<ul class="related">' + ''.join(
        f'<li><a href="{r}{_c("svc_url")[s]}">{_e(_c("svc_title")[s])}</a></li>' for s in ids if s in _c('svc_url')) + '</ul>'


def _kind_badge(k):
    return f'<span class="kind kind-{k}">{_e(D.KINDS[k])}</span>'


def _tips(lst):
    if not lst: return ''
    return ('<div class="form-tips"><b>Порада від «Як?»</b> <span class="muted">— наше пояснення, не офіційний документ</span><ul>'
            + ''.join(f'<li>{_e(t)}</li>' for t in lst) + '</ul></div>')


def _search_box(id_, label, ph):
    return (f'<form class="searchbox plain big-search" role="search" onsubmit="return false"><label class="sr-only" for="{id_}">{_e(label)}</label>'
            f'<input id="{id_}" type="search" placeholder="{_e(ph)}" autocomplete="off"></form>')


def _norm(t): return re.sub(r'\s+', ' ', t.lower().replace('’', "'").replace('ʼ', "'"))


# ---------------- Документи ----------------
def doc_page(i):
    d = D.DOCS[i]; r = '../../'; S = _c('SITE'); url = f'{S}documents/{i}/'
    svcs = D.services_of(i)
    terms = [t for t in G.TERMS if i in t['docs']]
    if d['kind'] == 'blank':
        f = d['file']
        get = (f'<div class="j-forms"><div class="form-item"><span class="form-tag">Офіційний бланк</span><b>{_e(d["title"])}</b>'
               f'<a class="btn primary" href="{_e(f["url"])}" target="_blank" rel="noopener noreferrer">Завантажити порожній бланк</a>'
               f'<small>{_e(f["fmt"])}, {_e(f["size"])} · файл із сайту {_e(D.host(f["url"]))}</small>'
               f'<small>Форму затверджено: <a href="{_e(d["src"]["url"])}" target="_blank" rel="noopener noreferrer">{_e(d["src"]["title"])}</a> · перевірено {_e(D.human_date(d["checked"]))}</small></div></div>')
    else:
        get = (f'<p>Бланка для завантаження немає. {_e(d["fill"])}</p>'
               f'<p class="muted">Підстава: <a href="{_e(d["src"]["url"])}" target="_blank" rel="noopener noreferrer">{_e(d["src"]["title"])}</a> · перевірено {_e(D.human_date(d["checked"]))}</p>')
    use = (f'<p>{_e(d["use"])}</p>' if d.get('use') else '') + _tips(d.get('howto'))
    if d['kind'] == 'blank':
        use += '<p>Заповнений бланк подайте разом з іншими документами, перелік яких є на сторінці послуги.</p>'
    body = f'''<article class="container post docpage">
{_c('crumbs')([('Головна', ''), ('Документи', 'documents/'), (d['title'], '')], r)}
<p class="post-cat">{_e(CAT_TITLE[d['cat']])}</p>
<h1>{_e(d['title'])}</h1>
<p>{_kind_badge(d['kind'])}</p>
<h2>Що це за документ</h2><p>{_e(d['plain'])}</p>
<h2>Для чого він потрібен</h2><p>{_e(d['purpose'])}</p>
<h2>Чи потрібно заповнювати самому</h2><p>{_e(d['fill'])}</p>
<h2>Де отримати або завантажити</h2>{get}
{('<h2>Як використати</h2>' + use) if use else ''}
<h2>Для яких послуг підходить</h2>
<p class="muted">{'Цей документ використовується в ' + str(len(svcs)) + ' ' + ('послузі' if len(svcs) == 1 else 'послугах') + '. Відкрийте свою — там покроковий план.'}</p>
{_svc_links(svcs, r)}
{('<h2>Пов’язані терміни</h2><p class="terms-line">' + ' · '.join(f'<a href="{r}glossary/{t["slug"]}/">{_e(t["term"])}</a>' for t in terms) + '</p>') if terms else ''}
<p class="mt"><a href="{r}documents/">← Усі документи</a></p>
{_c('FOOT')}
</article>'''
    title = _c('cut')(d['title'], 70) + (' — бланк і пояснення' if d['kind'] == 'blank' else ' — чи потрібно заповнювати') + ' | Як?'
    desc = _c('cut')(d['plain'] + ' ' + d['fill'], 155)
    ld = [_c('bc_ld')([('Головна', S), ('Документи', S + 'documents/'), (d['title'], url)]),
          {'@context': 'https://schema.org', '@type': 'WebPage', 'name': d['title'], 'description': desc, 'url': url, 'inLanguage': 'uk',
           **({'mainEntity': {'@type': 'DigitalDocument', 'name': d['title'], 'encodingFormat': d['file']['fmt'], 'url': d['file']['url']}} if d['kind'] == 'blank' else {})}]
    return _c('page')(2, title, desc, url, body, _c('ld_script')(ld), 'article', 'documents')


def docs_index():
    r = '../'; S = _c('SITE'); url = S + 'documents/'
    cnt = {c: sum(1 for i in DOC_PAGES if D.DOCS[i]['cat'] == c) for c, _ in D.CATS}
    kcnt = {k: sum(1 for i in DOC_PAGES if D.DOCS[i]['kind'] == k) for k in D.KINDS}
    chips = ('<div class="chips" role="group" aria-label="Тема"><button type="button" class="chip on" data-f="cat" data-v="">Усі теми</button>'
             + ''.join(f'<button type="button" class="chip" data-f="cat" data-v="{c}">{_e(t)}</button>' for c, t in D.CATS if cnt[c]) + '</div>'
             + '<div class="chips" role="group" aria-label="Тип"><button type="button" class="chip on" data-f="kind" data-v="">Усі типи</button>'
             + ''.join(f'<button type="button" class="chip" data-f="kind" data-v="{k}">{_e(t)}</button>' for k, t in D.KINDS.items() if kcnt[k]) + '</div>')
    items = []
    for i in sorted(DOC_PAGES, key=lambda i: ([c for c, _ in D.CATS].index(D.DOCS[i]['cat']), -len(D.services_of(i)), D.DOCS[i]['title'])):
        d = D.DOCS[i]; svcs = D.services_of(i)
        q = _norm(' '.join([d['title'], ' '.join(d.get('aka', [])), d['purpose'], CAT_TITLE[d['cat']]] + [_c('svc_title').get(s, '') for s in svcs]))
        items.append(f'<li class="doc-card" data-cat="{d["cat"]}" data-kind="{d["kind"]}" data-q="{_e(q)}">'
                     f'<a href="{i}/"><b>{_e(d["title"])}</b></a><p>{_e(d["plain"])}</p>'
                     f'<p class="doc-meta">{_kind_badge(d["kind"])}<span>{_e(CAT_TITLE[d["cat"]])}</span><span>{len(svcs)} {"послуга" if len(svcs) == 1 else ("послуги" if len(svcs) < 5 else "послуг")}</span></p></li>')
    body = f'''<div class="container post docs-hub">
{_c('crumbs')([('Головна', ''), ('Документи', '')], r)}
<h1>Документи для звернення</h1>
<p class="post-lead">Тут зібрано заяви до державних послуг. Ви дізнаєтеся, чи потрібно заповнювати бланк заздалегідь, і зможете завантажити офіційний бланк, якщо він є. Ми даємо лише перевірені посилання на офіційні сайти.</p>
{_search_box('dq', 'Знайти документ', 'Наприклад: прописка, пенсія, ФОП')}
{chips}
<p class="muted" id="dcount" aria-live="polite">Документів: {len(DOC_PAGES)}</p>
<ul class="doc-list" id="dlist">{''.join(items)}</ul>
<p class="empty-note" id="dempty" hidden>Нічого не знайдено. Спробуйте інше слово, наприклад «заява», «пенсія» чи «паспорт».</p>
<aside class="callout"><b>Не знайшли свій документ?</b> Ми додаємо лише бланки, які змогли перевірити на офіційному сайті. Відкрийте сторінку своєї послуги — там є перелік усіх документів — або запитайте бланк в установі. Незрозуміле слово шукайте в <a href="{r}glossary/">глосарії</a>.</aside>
</div>
<script>{_FILTER_JS}</script>'''
    ld = [_c('bc_ld')([('Головна', S), ('Документи', url)]),
          {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Документи для звернення', 'url': url, 'inLanguage': 'uk',
           'hasPart': [{'@type': 'WebPage', 'name': D.DOCS[i]['title'], 'url': f'{url}{i}/'} for i in DOC_PAGES]}]
    return _c('page')(1, 'Документи й бланки заяв до державних послуг — Як?',
                      'Офіційні бланки заяв і пояснення, коли бланк заповнювати не потрібно: місце проживання, пенсії, соціальна допомога, ФОП, ВПО, паспорти.',
                      url, body, _c('ld_script')(ld), 'website', 'documents')


# Фільтр без залежностей: пошук + теми + типи. Без JS усі документи просто видно списком.
_FILTER_JS = r"""(function(){var q=document.getElementById('dq'),L=[].slice.call(document.querySelectorAll('#dlist>li')),f={cat:'',kind:''};
function n(t){return (t||'').toLowerCase().replace(/[’ʼ]/g,"'").replace(/\s+/g,' ').trim()}
function run(){var s=n(q.value).split(' ').filter(Boolean),k=0;L.forEach(function(li){var ok=(!f.cat||li.dataset.cat===f.cat)&&(!f.kind||li.dataset.kind===f.kind)&&s.every(function(w){return li.dataset.q.indexOf(w)>-1});li.hidden=!ok;if(ok)k++});
document.getElementById('dcount').textContent='Документів: '+k;document.getElementById('dempty').hidden=k>0}
q.addEventListener('input',run);[].forEach.call(document.querySelectorAll('.chips .chip'),function(b){b.addEventListener('click',function(){f[b.dataset.f]=b.dataset.v;[].forEach.call(b.parentNode.children,function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',x===b)});run()})});
var p=new URLSearchParams(location.search).get('q');if(p){q.value=p;run()}})();"""


# ---------------- Глосарій ----------------
def term_page(t):
    r = '../../'; S = _c('SITE'); url = f'{S}glossary/{t["slug"]}/'
    svcs = _TERM_SVCS.get(t['slug'], [])
    docs = [d for d in t['docs'] if D.DOCS[d].get('page') is not False]
    mean = ''
    if t.get('meanings'):
        mean = ('<h2>' + ('Що важливо розрізняти' if len(t['meanings']) > 1 else 'Важливо знати') + '</h2><dl class="meanings">'
                + ''.join(f'<dt>{_e(a)}</dt><dd>{_e(b)}</dd>' for a, b in t['meanings']) + '</dl>')
    src = ''
    if t.get('src'):
        src = (f'<p class="source">Юридичне визначення: <a href="{_e(t["src"][1])}" target="_blank" rel="noopener noreferrer">{_e(t["src"][0])}</a>. '
               'Ми пояснюємо спрощено — точне формулювання дивіться в документі.</p>')
    others = [x for x in G.TERMS if x['slug'] != t['slug']]
    body = f'''<article class="container post termpage">
{_c('crumbs')([('Головна', ''), ('Глосарій', 'glossary/'), (t['term'], '')], r)}
<p class="post-cat">Глосарій</p>
<h1>{_e(t['term'])}</h1>
{('<p class="muted">Також кажуть: ' + _e(', '.join(t['aka'])) + '</p>') if t.get('aka') else ''}
<p class="post-lead">{_e(t['plain'])}</p>
{('<aside class="short"><b>Приклад</b><p>' + _e(t['example']) + '</p></aside>') if t.get('example') else ''}
{mean}
<h2>Де ви можете це побачити</h2><p>{_e(t['where'])}</p>
{('<h2>Пов’язані документи</h2><ul class="related">' + ''.join(f'<li><a href="{r}documents/{d}/">{_e(D.DOCS[d]["title"])}</a></li>' for d in docs) + '</ul>') if docs else ''}
{('<h2>Послуги, де трапляється цей термін</h2>' + _svc_links(svcs, r)) if svcs else ''}
{src}
<p class="mt"><a href="{r}glossary/">← Усі терміни</a></p>
{_c('FOOT')}
</article>'''
    title = f'{t["term"]} — що це означає простими словами | Як?'
    desc = _c('cut')(t['plain'], 155)
    ld = [_c('bc_ld')([('Головна', S), ('Глосарій', S + 'glossary/'), (t['term'], url)]),
          {'@context': 'https://schema.org', '@type': 'DefinedTerm', 'name': t['term'], 'description': desc, 'url': url, 'inLanguage': 'uk',
           'inDefinedTermSet': S + 'glossary/', **({'alternateName': t['aka']} if t.get('aka') else {})}]
    return _c('page')(2, title, desc, url, body, _c('ld_script')(ld), 'article', 'glossary')


def glossary_index():
    r = '../'; S = _c('SITE'); url = S + 'glossary/'
    terms = sorted(G.TERMS, key=lambda t: t['term'].lower())
    items = ''.join(f'<li data-q="{_e(_norm(t["term"] + " " + " ".join(t.get("aka", [])) + " " + t["plain"]))}"><a href="{t["slug"]}/"><b>{_e(t["term"])}</b></a>'
                    f'<p>{_e(_c("cut")(t["plain"], 140))}</p></li>' for t in terms)
    body = f'''<div class="container post docs-hub">
{_c('crumbs')([('Головна', ''), ('Глосарій', '')], r)}
<h1>Глосарій: складні слова простою мовою</h1>
<p class="post-lead">Пояснюємо терміни, які трапляються в описах послуг і в заявах: РНОКПП, КЕП, витяг, законний представник та інші. Якщо слово має кілька значень, показуємо різницю.</p>
{_search_box('gq', 'Знайти термін', 'Наприклад: РНОКПП, витяг')}
<p class="muted" id="gcount" aria-live="polite">Термінів: {len(terms)}</p>
<ul class="doc-list" id="glist">{items}</ul>
<p class="empty-note" id="gempty" hidden>Такого слова в глосарії поки немає. Спробуйте інше написання.</p>
<aside class="callout">Шукаєте бланк заяви? Перегляньте розділ <a href="{r}documents/">«Документи»</a>.</aside>
</div>
<script>(function(){{var q=document.getElementById('gq'),L=[].slice.call(document.querySelectorAll('#glist>li'));function n(t){{return (t||'').toLowerCase().replace(/[’ʼ]/g,"'").replace(/\s+/g,' ').trim()}}
q.addEventListener('input',function(){{var s=n(q.value).split(' ').filter(Boolean),k=0;L.forEach(function(li){{var ok=s.every(function(w){{return li.dataset.q.indexOf(w)>-1}});li.hidden=!ok;if(ok)k++}});document.getElementById('gcount').textContent='Термінів: '+k;document.getElementById('gempty').hidden=k>0}})}})();</script>'''
    ld = [_c('bc_ld')([('Головна', S), ('Глосарій', url)]),
          {'@context': 'https://schema.org', '@type': 'DefinedTermSet', '@id': url, 'name': 'Глосарій «Як?»', 'url': url, 'inLanguage': 'uk',
           'hasDefinedTerm': [{'@type': 'DefinedTerm', 'name': t['term'], 'url': f'{url}{t["slug"]}/'} for t in terms]}]
    return _c('page')(1, 'Глосарій: терміни державних послуг простою мовою — Як?',
                      'Що означають РНОКПП, КЕП, витяг, декларація, законний представник, ЦНАП та інші слова з описів державних послуг. Прості пояснення й приклади.',
                      url, body, _c('ld_script')(ld), 'website', 'glossary')


def search_index():
    """documents/search.json — для загального пошуку на головній (app.js)."""
    out = [{'k': 'doc', 't': D.DOCS[i]['title'], 'a': ' '.join(D.DOCS[i].get('aka', [])), 'u': f'documents/{i}/', 'd': _c('cut')(D.DOCS[i]['plain'], 120)} for i in DOC_PAGES]
    out += [{'k': 'term', 't': t['term'], 'a': ' '.join(t.get('aka', [])), 'u': f'glossary/{t["slug"]}/', 'd': _c('cut')(t['plain'], 120)} for t in G.TERMS]
    return json.dumps(out, ensure_ascii=False)


def build():
    w, S, U = _c('write'), _c('SITE'), _c('URLS')
    w('documents/index.html', docs_index()); U.append(S + 'documents/')
    for i in DOC_PAGES:
        w(f'documents/{i}/index.html', doc_page(i)); U.append(f'{S}documents/{i}/')
    w('glossary/index.html', glossary_index()); U.append(S + 'glossary/')
    for t in G.TERMS:
        w(f'glossary/{t["slug"]}/index.html', term_page(t)); U.append(f'{S}glossary/{t["slug"]}/')
    w('documents/search.json', search_index())
    return len(DOC_PAGES), len(G.TERMS)

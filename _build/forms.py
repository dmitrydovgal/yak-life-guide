"""Блок «Бланк заяви» на сторінках послуг: адаптер над єдиною базою документів (docs_db.py).

Дані більше не зберігаються тут — лише перетворюються у формат, який рендерять
journey.py (_forms_static) і journey.js (formsHtml). Схему й правила див. у docs_db.py.
"""
import docs_db as D

human_date, host = D.human_date, D.host


def check():
    D.check()


def doc_href(doc_id, depth=2):
    d = D.DOCS[doc_id]
    return None if d.get('page') is False else '../' * depth + f'documents/{doc_id}/'


def _card(x):
    d = D.DOCS[x['doc']]
    c = {'title': d['title'], 'url': d['file']['url'], 'fmt': d['file']['fmt'], 'size': d['file'].get('size', ''),
         'src': d['src']['title'], 'srcUrl': d['src']['url'], 'checked': d['checked'], 'checkedText': human_date(d['checked']),
         'host': host(d['file']['url']), 'docHref': doc_href(x['doc'])}
    for k in ('who', 'when'):
        if x.get(k): c[k] = x[k]
    return c


def for_service(sid):
    """Дані для journey-data та статичної сторінки; None — блоку немає."""
    l = D.LINKS.get(sid)
    if not l: return None
    main = [x for x in l['docs'] if not x.get('also')]
    also = [x for x in l['docs'] if x.get('also')]
    kind = D.DOCS[main[0]['doc']]['kind']
    out = {'kind': kind}
    tips = []
    for x in l['docs']:
        tips += [t for t in D.DOCS[x['doc']].get('howto', []) if t not in tips]
    tips += l.get('tips', [])
    if kind == 'blank':
        out['blanks'] = [_card(x) for x in main]
        if also: out['also'] = [_card(x) for x in also]
    else:
        d = D.DOCS[main[0]['doc']]
        out['noBlank'] = d['fill'] + (' ' + l['extra'] if l.get('extra') else '')
        if doc_href(main[0]['doc']): out['docHref'] = doc_href(main[0]['doc'])
    if tips: out['tips'] = tips
    if l.get('note'): out['note'] = l['note']
    return out

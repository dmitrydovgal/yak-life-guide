# -*- coding: utf-8 -*-
"""Новий шаблон тіла сторінки послуги: «Де / Вартість / Строк / Що підготувати» + план кроків.
Усі значення беруться з реєстру «Гід з державних послуг»; відсутні дані не показуються."""
import re, html, unicodedata
from urllib.parse import urlparse
e = html.escape

PILOT = {'02333', '00034', '00155', '00027', '02078'}


def _cut(t, n):
    t = re.sub(r'\s+', ' ', str(t or '')).strip()
    if len(t) <= n:
        return t
    c = t[:n]
    k = max(c.rfind(' '), int(n * .6))
    return c[:k].rstrip(' ,;.:') + '…'


def _lst(v):
    # Реєстр місцями містить розкладений Юнікод (й = и + дуга) — нормалізуємо до NFC
    if isinstance(v, list):
        return [unicodedata.normalize('NFC', str(x)).strip() for x in v if str(x).strip()]
    return [unicodedata.normalize('NFC', x).strip() for x in re.split(r'\s*\|\s*', str(v or '')) if x.strip()]


def money(t):
    t = re.sub(r'(\d+)\.0\b', r'\1', str(t or '')).strip()
    t = re.sub(r'(\d+)\.(\d+)', r'\1,\2', t)
    return t.replace('UAH', 'грн').strip()


def _cost_text(costs):
    vals = [c for c in (costs or []) if re.search(r'\d|безоплат|безкоштов|розмір|збор|збір|вартість|плат', str(c.get('verbose') or '') + ' ' + str(c.get('type') or ''), re.I)]
    if not vals:
        return ''
    if all(re.search('безоплатн', (c.get('type') or '') + ' ' + (c.get('verbose') or ''), re.I) for c in vals):
        return 'Безоплатно'
    return '; '.join(money(c['verbose']) for c in vals)


def variants(z):
    out = []
    for v in z.get('variations') or []:
        out.append({'label': re.sub(r'\s+', ' ', str(v.get('identifier') or '')).strip(), 'cost': _cost_text(v.get('costs')),
                    'time': ((v.get('duration') or {}).get('verbose') or '').strip()})
    return out


def _fact(vs, key):
    vals = [(v['label'], v[key]) for v in vs if v[key]]
    if not vals:
        return ''
    if len({x[1] for x in vals}) == 1:
        return e(vals[0][1])
    return '<ul class="flat">' + ''.join((f'<li><span class="vl">{e(l)}</span><span class="vv">{e(x)}</span></li>' if l else f'<li><span class="vv">{e(x)}</span></li>') for l, x in vals) + '</ul>'


CH_ORDER = ['Online', 'Мобільний застосунок', 'Особисто', 'Поштою (рекомендованим листом)', 'Електронною поштою']
CH_LABEL = {'Online': 'онлайн', 'Мобільний застосунок': 'у мобільному застосунку', 'Особисто': 'особисто',
            'Поштою (рекомендованим листом)': 'поштою (рекомендованим листом)', 'Електронною поштою': 'електронною поштою'}


def ways(items):
    roles, ch, urls = [], set(), []
    for w in _lst(items):
        role, _, rest = w.partition(':')
        role = role.strip()
        if role and role not in roles:
            roles.append(role)
        for part in rest.split(';'):
            part = part.strip()
            if part.startswith('Online'):
                ch.add('Online')
                u = part.split(':', 1)[1].strip() if ':' in part else ''
                if u:
                    urls.append(u)
                continue
            for p in part.split(','):
                if p.strip():
                    ch.add(p.strip())
    return roles, [c for c in CH_ORDER if c in ch], urls


# Класифікація посилань з реєстру. Кнопку «Подати онлайн» отримують лише https-адреси на *.gov.ua,
# що ведуть на сервіс (не на закон, файл, статтю чи загальну головну сторінку органу).
SERVICE_HOST_PREFIX = ('services.', 'e.', 'e-services.', 'eservices.', 'portal.', 'cabinet.', 'exam.', 'sev.', 'shlyah.',
                       'reserveplus.', 'e-aid.', 'e-construction.', 'e-driver.', 'online.', 'citizen-portal')
GENERIC_ROOTS = {'diia.gov.ua', 'www.diia.gov.ua', 'my.gov.ua'}
NOT_SERVICE_HOSTS = {'zakon.rada.gov.ua'}
# Посилання з реєстру, що на перевірці 26.11.2026 повертали 404 — не показуємо як «Подати онлайн»
DEAD_LINKS = {'https://eco.gov.ua/services/vidacha-dovidki-pro-velichini-fonovih-koncentracij',
              'https://diia.gov.ua/services/grant-na-vlasnu-spravu',
              'https://mindev.gov.ua/derzhavna-dopomoha-polonenym-ta-ikh-simiam/podaty-zaiavu-na-vstanovlennia-faktu-pozbavlennia-osobystoi-svobody-vnaslidok-zbroinoi-ahresii-proty-ukrainy'}


def classify(u):
    u = (u or '').rstrip('.').strip()
    if u.rstrip('/') in DEAD_LINKS:
        return None
    p = urlparse(u)
    h = p.netloc.lower()
    if p.scheme != 'https' or not (h.endswith('.gov.ua') or h == 'gov.ua') or h in NOT_SERVICE_HOSTS:
        return None
    path = p.path.strip('/')
    if re.search(r'\.(pdf|docx?|xlsx?|zip)$', path, re.I) or '/storage/' in p.path:
        return None
    if '/articles/' in p.path or h.startswith('bf.'):
        return 'info'
    if not path:
        if h in GENERIC_ROOTS:
            return None
        return 'submit' if h.startswith(SERVICE_HOST_PREFIX) else 'info'
    return 'submit'


def links(z):
    cands = [(z.get('access_link') or '').strip()] + ways(z.get('application_ways'))[2]
    sub, info = '', ''
    for u in cands:
        u = u.rstrip('.').strip()
        k = classify(u)
        if k == 'submit' and not sub:
            sub = u
        elif k == 'info' and not info:
            info = u
    return sub, info


def official_url(z):
    return links(z)[0]


def host_label(u):
    h = urlparse(u).netloc
    return 'Дія' if h in ('diia.gov.ua', 'www.diia.gov.ua') else h


def short_prov(p):
    return 'ЦНАП' if re.fullmatch(r'Центр(и)? надання адміністративних послуг', p.strip()) else p.strip()


def _end(s):
    s = s.rstrip()
    return s if s.endswith(('.', '!', '?', '…')) else s + '.'


def plural(n, a, b, c):
    n10, n100 = n % 10, n % 100
    return a if n10 == 1 and n100 != 11 else b if 2 <= n10 <= 4 and not 12 <= n100 <= 14 else c


def chan_text(chs):
    return ', '.join(CH_LABEL[c] for c in chs if c in CH_LABEL)


def body_v2(sid, z, n, full, desc_full, crumbs_html, ev_title, guide):
    vs = variants(z)
    docs = [_cut(d, 260).rstrip(';, ') for d in _lst(z.get('input'))]
    prov = [short_prov(_cut(p, 140)) for p in _lst(z.get('service_provider'))]
    roles, chans, _ = ways(z.get('application_ways'))
    _, rchans, _ = ways(z.get('receiving_ways'))
    url, info_url = links(z)
    has_cnap = 'ЦНАП' in prov
    offline = [c for c in chans if c not in ('Online', 'Мобільний застосунок')]
    prods = [_cut(p, 220) for p in _lst(z.get('produces')) if not re.match(r'\s*(відмов|письмова відмова|рішення про відмову)', p, re.I)]
    refus = [_cut(p, 260) for p in _lst(z.get('refusal_grounds'))]
    appeal = [_cut(p, 160) for p in _lst(z.get('refusal_appeal_rules'))]
    court = str(z.get('is_appealed_in_court') or '').strip().lower() == 'так'
    appl = [_cut(p, 80) for p in _lst(z.get('applicant_type'))][:4]
    spatial = str(z.get('spatial') or '').strip()
    spatial = re.sub(r'україн', 'Україн', spatial.capitalize()) if spatial.isupper() else spatial
    local = str(z.get('level') or '').strip() == 'Місцева'

    # --- Компактний блок фактів ---
    where = []
    if url:
        where.append(f'Онлайн — {e(host_label(url))}')
    if prov and (offline or not url):
        lead_txt = chan_text(offline)
        lst = '; '.join(prov[:3]) + ('…' if len(prov) > 3 else '')
        where.append(e((lead_txt[0].upper() + lead_txt[1:] + ': ' if lead_txt else '') + lst))
    facts = []
    if where:
        facts.append(('Де отримати', '<br>'.join(where)))
    c, t = _fact(vs, 'cost'), _fact(vs, 'time')
    if c:
        facts.append(('Вартість', c))
    if t:
        facts.append(('Строк', t))
    if docs:
        facts.append(('Що підготувати', f'{len(docs)} {plural(len(docs), "документ", "документи", "документів")} — <a href="#docs">перелік нижче</a>'))
    facts_html = ('<dl class="facts">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in facts) + '</dl>') if facts else ''

    # --- Головна дія ---
    if url:
        main = (f'<div class="svc-main"><a class="btn primary" href="{e(url)}" target="_blank" rel="noopener noreferrer">Подати онлайн</a>'
                f'<span class="muted">Відкриється офіційний сервіс {e(urlparse(url).netloc)}</span></div>')
    elif offline or 'Online' in chans:
        btn = '<a class="btn ghost" href="https://guide.diia.gov.ua/asc/" target="_blank" rel="noopener noreferrer">Знайти ЦНАП</a>' if has_cnap and offline else ''
        if 'Online' in chans:
            txt = 'Реєстр зазначає онлайн-подання, але офіційне посилання на сервіс не підтверджене — перевірте його в повному описі послуги.'
            if offline: txt += f' Також можна звернутися {chan_text(offline)}.'
        else:
            txt = f'Онлайн-подання для цієї послуги в реєстрі не зазначено. Звернутися можна {chan_text(offline)}.'
        main = f'<div class="svc-main"><p>{e(txt)}</p>{btn}</div>'
    else:
        main = ''

    # --- Кроки з даних послуги ---
    steps = []
    if docs:
        cond_docs = any(re.search(r'у разі|за наявності|за потреби|у випадку', d, re.I) for d in docs)
        steps.append(('Підготуйте документи', 'Частина документів потрібна лише в окремих випадках — це зазначено в переліку.' if cond_docs else '',
                      '<ul class="docs" id="docs">' + ''.join(f'<li>{e(d)}</li>' for d in docs) + '</ul>'))
    sub = []
    if url:
        sub.append(f'Онлайн: <a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(host_label(url))}</a>.')
    if offline and prov:
        ct = chan_text(offline)
        sub.append(e(_end(ct[0].upper() + ct[1:] + ': ' + '; '.join(x.rstrip('. ') for x in prov))))
    if len(roles) > 1:
        sub.append(e(_end('Подати може: ' + ', '.join(r.lower() for r in roles))))
    if sub:
        extra = ('<div class="oact"><a class="btn ghost sm-btn" href="https://guide.diia.gov.ua/asc/" target="_blank" rel="noopener noreferrer">Знайти ЦНАП</a></div>'
                 if has_cnap and offline else '')
        steps.append(('Подайте заяву', '', '<p>' + '</p><p>'.join(sub) + '</p>' + extra))
    paid = [v for v in vs if v['cost'] and v['cost'] != 'Безоплатно']
    if paid:
        steps.append(('Сплатіть послугу', _end('Вартість: ' + paid[0]['cost']) if len({v['cost'] for v in paid}) == 1 and len(paid) == len([v for v in vs if v['cost']])
                      else 'Вартість залежить від варіанта надання — див. «Вартість» вище.', ''))
    tt = [v for v in vs if v['time']]
    if tt:
        same = len({v['time'] for v in tt}) == 1
        steps.append(('Дочекайтеся рішення', _end('Строк: ' + tt[0]['time']) if same else 'Строк залежить від варіанта надання — див. «Строк» вище.', ''))
    r = chan_text(rchans)
    if prods or r:
        d = _end('Результат: ' + '; '.join(x.rstrip('.;, ') for x in prods)) if prods else ''
        if r:
            d += (' ' if d else '') + 'Отримати можна ' + r + '.'
        steps.append(('Отримайте результат', d, ''))
    steps_html = ('<h2>Як отримати послугу</h2><ol class="osteps">' + ''.join(
        f'<li class="ostep"><span class="num">{i}</span><div class="body"><b>{e(t)}</b>{f"<span>{e(d)}</span>" if d else ""}{x}</div></li>'
        for i, (t, d, x) in enumerate(steps, 1)) + '</ol>') if steps else ''

    # --- Додаткові блоки (лише за наявності даних) ---
    blocks = []
    if refus or appeal or court:
        b = '<h2>Якщо відмовили</h2>'
        if refus:
            b += '<p>Підстави для відмови за реєстром:</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in refus[:5]) + '</ul>'
            if len(refus) > 5:
                b += f'<p class="muted">Ще {len(refus) - 5} — у повному описі послуги.</p>'
        ap = []
        if appeal:
            ap.append(_end('Оскаржити рішення можна: ' + '; '.join(x.rstrip('. ') for x in appeal)))
        if court:
            ap.append('Рішення можна оскаржити в суді.')
        if ap:
            b += '<p>' + e(' '.join(ap)) + '</p>'
        blocks.append(b)
    cond = []
    if full.lower() != n.lower():
        cond.append(('Офіційна назва', full))
    if appl:
        cond.append(('Для кого', ', '.join(appl)))
    if spatial:
        cond.append(('Де діє', spatial))
    if local:
        cond.append(('Рівень', 'Місцева послуга: порядок і вимоги можуть відрізнятися залежно від громади'))
    if cond:
        blocks.append('<h2>Додаткові умови</h2><dl class="kv">' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in cond) + '</dl>')
    src = [f'<li><a href="{guide}" target="_blank" rel="noopener noreferrer">Гід з державних послуг, послуга № {e(sid)}</a> — повний опис і нормативна база</li>']
    if url:
        src.append(f'<li><a href="{e(url)}" target="_blank" rel="noopener noreferrer">Онлайн-сервіс ({e(urlparse(url).netloc)})</a></li>')
    if info_url:
        src.append(f'<li><a href="{e(info_url)}" target="_blank" rel="noopener noreferrer">Офіційна сторінка ({e(urlparse(info_url).netloc)})</a></li>')
    blocks.append('<h2>Офіційне джерело</h2><ul>' + ''.join(src) + '</ul>')

    lead, more = '', ''
    if desc_full and desc_full.lower() not in (full.lower(), n.lower()):
        d = re.sub(r'\s+', ' ', desc_full).strip()
        if len(d) <= 320:
            lead = d
        else:
            sents = re.split(r'(?<=[.!?])\s+(?=[А-ЯЇІЄҐA-Z0-9«"])', d)
            acc = ''
            for s in sents:
                if acc and len(acc) + len(s) > 300: break
                acc = (acc + ' ' + s).strip()
            if len(acc) > 340 or len(acc) < 60: acc = ''
            lead, more = (acc, d[len(acc):].strip()) if acc else ('', d)
        lead = f'<p class="post-lead">{e(lead)}</p>' if lead else ''
        if more:
            blocks.insert(0, f'<h2>Важливо знати</h2><p>{e(more)}</p>')
    meta = ''
    return f'''<article class="container post svc2">
{crumbs_html}
<p class="post-cat">{e(ev_title)}</p>
<h1>{e(n)}</h1>
{meta}
{lead}
{facts_html}
{main}
{steps_html}
{''.join(blocks)}
<p class="svc-alt">Потрібні кроки під ваше місто? <a href="../../#/s/{sid}/-">Отримати персональну інструкцію</a></p>
'''

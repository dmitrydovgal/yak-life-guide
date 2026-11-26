# -*- coding: utf-8 -*-
"""Генератор сценаріїв (journey) для послуг реєстру.

Кожна послуга описується структурованими даними (dict → JSON), а не HTML:
питання з умовними гілками, порівняння варіантів, персональний чек-лист,
процедура для обраного способу подачі, результат, відмова, «що далі» та що уточнити.
Усі факти беруться з реєстру «Гід з державних послуг»; пояснювальні формулювання
позначено окремо від фактів. Нічого, чого немає в даних, не додається.

Те саме дерево даних рендерить:
  * render_static() — індексований HTML для пошукових систем і без JS;
  * /journey.js     — інтерактивний покроковий сценарій у браузері.
"""
import re, html, json
from urllib.parse import urlparse
import svc_v2 as V

e = html.escape
DATA_DATE = '2026-11-24'          # дата завантаження відкритого реєстру (registry.json)

# ---------- Архетипи ----------
ARCHETYPES = [
    ('recovery', 'Відновлення або заміна', r'втрач|викрад|пошкодж|дублікат|замість|відновлен'),
    ('certificate', 'Довідка або витяг', r'витяг|довідк|копі[їя] |інформаці[ії] з|відомост[ей]+ з'),
    ('termination', 'Припинення або скасування', r'припинен|анулюван|скасуван|зняття з|ліквідац|закриття|виключення з'),
    ('change', 'Зміна даних або продовження', r'внесення змін|зміни до|переоформ|продовження|обмін|заміна|перереєстрац'),
    ('benefit', 'Допомога, виплата, пільга', r'допомог|субсиді|виплат|компенсаці|пенсі|пільг|забезпечення|соціальн'),
    ('permit', 'Дозвіл, ліцензія, сертифікат', r'ліценз|дозв|сертифікат|погодженн|атестац|акредитац|висновк'),
    ('registration', 'Реєстрація', r'реєстрац|внесення до|облік|декларуван'),
]


def archetype(name):
    for k, label, rx in ARCHETYPES:
        if re.search(rx, name, re.I):
            return k, label
    return 'application', 'Отримання послуги'


# Ручні зв'язки з глибокими сценаріями (сторінки існують на сайті)
_FOP = [('Як обрати групу ФОП: анкета і калькулятор платежів на 2026 рік', '../../i/fop-group/'), ('Як відкрити ФОП — покрокова інструкція', '../../i/fop-open/')]
EXTRA_NEXT = {'00411': _FOP, '02518': _FOP[:1], '02517': _FOP[:1], '00577': _FOP[:1]}

# ---------- Допоміжне ----------
ROLE = {'Заявник': ('self', 'Я подаю сам(а)', 'Заява від вашого імені'),
        'Представник заявника': ('rep', 'Подає представник', 'Наприклад, за довіреністю'),
        'Законний представник': ('legal', 'Подає законний представник', 'Наприклад, батьки за дитину')}
PROFILE = {'Фізична особа': ('person', 'Я як громадянин(ка)', 'Звертаюся особисто як фізична особа'),
           'Фізична особа-підприємець': ('fop', 'Я як ФОП', 'Звертаюся як фізична особа-підприємець'),
           'Юридична особа': ('legal', 'Від компанії чи організації', 'Юридична особа: ТОВ, підприємство, установа'),
           'Представницький орган місцевого самоврядування': ('gov', 'Від органу місцевого самоврядування', 'Рада або її представницький орган'),
           'Громадське об’єднання, що не має статусу юридичної особи': ('ngo', 'Від громадського об’єднання', 'Без статусу юридичної особи')}
PROFILE_ORDER = list(PROFILE)
PROFILE_NOUN = {'person': 'громадяни (фізичні особи)', 'fop': 'фізичні особи-підприємці', 'legal': 'компанії та організації (юридичні особи)', 'gov': 'органи місцевого самоврядування', 'ngo': 'громадські об’єднання без статусу юридичної особи'}
PROFILE_ALL = [PROFILE[k] for k in PROFILE_ORDER]

# Пояснення «навіщо» за типом документа (пояснювальний текст «Як?», не факт реєстру)
DOC_WHY = [
    (r'^\s*(заява|анкета|звернення|повідомлення|клопотання|запит)', 'Основний документ звернення: у ньому ви просите надати послугу.'),
    (r'довіреніст|(?<![а-яіїєґ])повноважен', 'Підтверджує право представника діяти від імені заявника.'),
    (r'облікової\s+картки|РНОКПП|ідентифікаційн\w+ (код|номер)', 'Податковий номер — щоб знайти вас у державних реєстрах.'),
    (r'паспорт|посвідчує особу|посвідк\w* на|посвідчення особи|ID-картк', 'Підтверджує особу заявника.'),
    (r'квитанці|платіжн\w+ (доручен|інструкц|документ)|документ\w*,? що підтверджує (оплату|сплату|внесення плати)', 'Підтверджує, що послугу оплачено.'),
    (r'фото', 'Потрібне для оформлення документа.'),
    (r'свідоцтв\w+ про (народження|шлюб|смерть)|актов\w+ запис', 'Підтверджує відомості про стан особи (народження, шлюб тощо).'),
    (r'договір|договору|угод', 'Підтверджує право або домовленість, на яких ґрунтується звернення.'),
    (r'довідк|витяг|виписк', 'Підтверджує відомості, потрібні для рішення органу.'),
    (r'рішення|наказ|протокол|статут|установч', 'Внутрішній чи офіційний документ, на підставі якого діє заявник.'),
    (r'план|схем|креслен|проєкт|проект|документаці', 'Технічний документ, за яким орган перевіряє об’єкт.'),
]


def doc_why(t):
    for rx, why in DOC_WHY:
        if re.search(rx, t, re.I):
            return why
    return ''


def doc_form(t):
    if re.search(r'\bоригінал', t, re.I) and re.search(r'\bкопі', t, re.I): return 'оригінал і копія'
    if re.search(r'\bкопі', t, re.I): return 'копія'
    if re.search(r'\bоригінал', t, re.I): return 'оригінал'
    if re.search(r'за формою|встановленого зразка|за зразком|згідно з додатком', t, re.I): return 'за встановленою формою'
    return ''


# Плюси й обмеження способів подачі — пояснення «Як?» за природою каналу
CH_PROS = {'online': 'Без візиту й черги, у зручний час.', 'app': 'Без візиту, з телефона.', 'office': 'Можна подати оригінали й поставити запитання на місці.',
           'mail': 'Без візиту в установу.', 'email': 'Без візиту, швидке надсилання.'}
CH_CONS = {'online': 'Потрібен доступ до онлайн-сервісу та електронна ідентифікація, якщо сервіс її вимагає.', 'app': 'Потрібен смартфон із застосунком.',
           'office': 'Потрібно прийти в робочий час; можливі черги.', 'mail': 'Додатковий час на доставку листа.', 'email': 'Уточніть адресу та вимоги до файлів в органі.'}


def _vs(x, base):
    """Порівняння варіанта з найповільнішим (базовим) — у числах з реєстру."""
    if not base or x['id'] == base['id'] or x['days'] is None or base['days'] is None:
        return ''
    parts = []
    if base['days'] > x['days']: parts.append('швидше, ніж «' + base['label'] + '»')
    if x['costNum'] is not None and base['costNum'] is not None and x['costNum'] > base['costNum']:
        d = round(x['costNum'] - base['costNum'], 2)
        parts.append('дорожче на ' + (f'{int(d)}' if d == int(d) else f'{d:.2f}'.replace('.', ',')) + ' грн')
    return '; '.join(parts)


RECALC = []   # послуги, де суму перераховано (для звіту збірки)
# (стара сума в реєстрі, строк у днях) → (нова вартість, строк, число, днів) за таблицею ДМС з 01.01.2026
DMS_2026 = {(558, 20.0): ('618 грн', 'до 20 робочих днів', 618, 20.0), (928, 10.0): ('988 грн', 'до 7 робочих днів', 988, 7.0),
            (988, 10.0): ('988 грн', 'до 7 робочих днів', 988, 7.0),
            (1042, 20.0): ('1147 грн', 'до 20 робочих днів', 1147, 20.0), (1682, 7.0): ('1787 грн', 'до 7 робочих днів', 1787, 7.0)}
from editorial import ED, INS_ED

COND_RX = re.compile(r'у разі|за наявності|за потреби|якщо|у випадку|для осіб|для громадян', re.I)
REP_RX = re.compile(r'представник|довіреніст|(?<![а-яіїєґ])повноважен', re.I)   # не «уповноважений орган»


def _days(v):
    d = (v.get('duration') or {})
    try:
        sec = float(d.get('value') or 0)
    except (TypeError, ValueError):
        sec = 0
    return round(sec / 86400, 2) if sec else None


def _cost_num(v):
    cs = v.get('costs') or []
    money_vals = [c.get('value') for c in cs if isinstance(c.get('value'), (int, float)) and re.search(r'UAH|грн', str(c.get('verbose') or ''))]
    vals = money_vals or [c.get('value') for c in cs if isinstance(c.get('value'), (int, float)) and not re.search(r'%', str(c.get('verbose') or ''))]
    return sum(vals) if vals else None


_STD = r'(прожитков\w+ мінімум\w*,?\s*(?:встановлен\w+\s+)?(?:законом\s+)?для працездатних осіб|мінімальн\w+ заробітн\w+ плат\w+)'
FORMULA_RX = [re.compile(r'(\d+(?:[,.]\d+)?)\s*відсотк\w*\s+(?:розміру\s+)?' + _STD, re.I),
              re.compile(r'(\d+(?:[,.]\d+)?)\s*(?:розмір\w*\s+)?' + _STD, re.I)]


def recompute(label):
    """Сума за формулою з реєстру на 2026 рік або None (якщо формула неоднозначна чи є правила округлення)."""
    round10 = bool(re.search(r'округл\w*\s+до найближчих 10 гривень', label, re.I))
    if re.search(r'округл', label, re.I) and not round10:
        return None
    for i, rx in enumerate(FORMULA_RX):
        ms = rx.findall(label)
        if len(ms) == 1:
            k = float(ms[0][0].replace(',', '.'))
            base = 8647 if 'заробітн' in ms[0][1] else 3328
            val = round(k * base / (100 if i == 0 else 1), 2)
            return float(round(val / 10) * 10) if round10 else val
        if len(ms) > 1:
            return None
    return None


def _cond(doc):
    m = re.search(r'\(([^()]*(?:у разі|за наявності|за потреби|якщо|у випадку)[^()]*)\)', doc, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'((?:у разі|за наявності|за потреби|якщо|у випадку)[^.;]*)', doc, re.I)
    return m.group(1).strip() if m else ''


def _nfc(o):
    import unicodedata
    if isinstance(o, str): return unicodedata.normalize('NFC', o)
    if isinstance(o, list): return [_nfc(x) for x in o]
    if isinstance(o, dict): return {k: _nfc(v) for k, v in o.items()}
    return o


# ---------- Побудова сценарію ----------
def build(sid, z, related, url_of):
    z = _nfc(z)
    name = re.sub(r'\s+', ' ', z['name']).strip()
    arch, arch_label = archetype(name)
    roles_raw, chans, _ = V.ways(z.get('application_ways'))
    _, rchans, _ = V.ways(z.get('receiving_ways'))
    sub_url, info_url = V.links(z)
    prov_all = [V.short_prov(V._cut(p, 140)) for p in V._lst(z.get('service_provider'))]
    # Портали й застосунки — це онлайн-канали, а не місця для особистого звернення
    prov = [p for p in prov_all if not re.search(r'портал|мобільн\w* (додат|застосун)|^дія$|\(дія\)', p, re.I)] or prov_all
    has_cnap = 'ЦНАП' in prov
    local = str(z.get('level') or '').strip() == 'Місцева'

    # Варіанти надання (вартість / строк)
    raw_vars = z.get('variations') or []
    variants = []
    for i, v in enumerate(raw_vars):
        variants.append({'id': f'v{i}', 'label': re.sub(r'\s+', ' ', str(v.get('identifier') or '')).strip() or 'Звичайне надання',
                         'cost': V._cost_text(v.get('costs')), 'time': ((v.get('duration') or {}).get('verbose') or '').strip(),
                         'costNum': _cost_num(v), 'days': _days(v)})
    # Перерахунок сум, заданих у реєстрі відсотком від соцстандарту, за перевіреними базами 2026 року
    for x, v in zip(variants, raw_vars):
        src = x['label'] + ' ' + ' '.join(str(c.get('verbose') or '') for c in (v.get('costs') or []) if not re.search(r'UAH|грн', str(c.get('verbose') or '')))
        new = recompute(src)
        if new is None and re.search(r'прожитков|заробітн\w+ плат', src, re.I) and x['costNum']:
            x['stdNote'] = True   # сума залежить від соцстандарту, але автоматично не перерахована
        if new is not None and not x['costNum'] and not re.search(r'безоплат', x['cost'], re.I):
            x['formulaText'] = x['cost']; x['costNum'] = new; x['formula'] = True
            x['cost'] = V.money(f'{new:.2f} UAH') + ' (за формулою реєстру на 2026 рік)'
        elif new is not None and x['costNum']:
            if abs(new - x['costNum']) > 0.5 and V.money(f'{new:.2f} UAH') not in x['cost']:
                x['old'] = x['cost']; x['oldNum'] = x['costNum']; x['costNum'] = new; x['formula'] = True
                x['cost'] = V.money(f'{new:.2f} UAH') + ' (перераховано на 2026 рік)'
                RECALC.append(sid)

    # Паспортні послуги ДМС: вартість з офіційної таблиці ДМС з 01.01.2026 (dmsu.gov.ua/news/dms/19633.html)
    dms_note = False
    if re.search(r'паспорт', name, re.I) and any('міграційн' in p.lower() for p in prov_all):
        for x in variants:
            key = (round(x['costNum'] or 0), x['days'])
            new = DMS_2026.get(key)
            if new and not x.get('old'):
                x['old'] = x['cost']; x['oldNum'] = x['costNum']; x['cost'], x['time'] = new[0], new[1]; x['costNum'] = new[2]; x['days'] = new[3]
            elif round(x['costNum'] or 0) == 1682 and x['days'] == 3:
                dms_note = True

    # Та сама застаріла сума в іншому варіанті цієї послуги — та сама формула
    fixed = {round(x['oldNum'], 2): (x['costNum'], x['cost']) for x in variants if x.get('formula') and x.get('oldNum') is not None}   # лише суми, перераховані за формулою
    for x in variants:
        if not x.get('old') and x['costNum'] is not None and round(x['costNum'], 2) in fixed:
            x['old'] = x['cost']; x['oldNum'] = x['costNum']; x['costNum'], x['cost'] = fixed[round(x['costNum'], 2)]

    # Суперечливі строки в реєстрі («2 дні (Хвилин)») не показуємо як факт
    bad_time = False
    for x in variants:
        if re.search(r'\((Хвилин|Години)\)', x['time']) and re.search(r'\bдн', x['time']):
            x['time'] = ''; x['days'] = None; bad_time = True

    decide = None
    # Варіанти, що насправді описують спосіб подачі (електронно / на папері), прив'язуємо до каналу, а не питаємо окремо
    var_by_ch = {}
    if len(variants) > 1:
        for x in variants:
            if re.search(r'електронн|онлайн|в електронній формі', x['label'], re.I): var_by_ch.setdefault('online', x['id'])
            elif re.search(r'паперов|особист|у разі звернення до (органу|цнап)|надходження документів|^звичайне надання$', x['label'].strip(), re.I): var_by_ch.setdefault('offline', x['id'])
        if not ('online' in var_by_ch and 'offline' in var_by_ch and len(variants) == 2):
            var_by_ch = {}
    same_vars = len({(x['cost'], x['time']) for x in variants}) == 1   # варіанти нічим не відрізняються — питати немає сенсу
    if len(variants) > 1 and not var_by_ch and not same_vars:
        speedy = all(re.search(r'звичайн|термінов|експрес|прискорен', x['label'], re.I) for x in variants)
        decide = 'speed' if speedy else 'situation'
        if speedy:
            fast = min((x for x in variants if x['days'] is not None), key=lambda x: x['days'], default=None)
            cheap = min((x for x in variants if x['costNum'] is not None), key=lambda x: x['costNum'], default=None)
            for x in variants:
                tags = []
                if fast and x['id'] == fast['id'] and len({y['days'] for y in variants}) > 1: tags.append('найшвидше')
                if cheap and x['id'] == cheap['id'] and len({y['costNum'] for y in variants}) > 1: tags.append('найдешевше')
                x['tags'] = tags

    # Способи подачі
    channels = []
    if 'Online' in chans or sub_url:
        channels.append({'id': 'online', 'label': 'Онлайн', 'url': sub_url,
                         'desc': ('Через офіційний сервіс ' + urlparse(sub_url).netloc + ', без візиту в установу.') if sub_url
                         else 'Реєстр зазначає онлайн-подання, але офіційне посилання не підтверджене.'})
    if 'Мобільний застосунок' in chans:
        channels.append({'id': 'app', 'label': 'У мобільному застосунку', 'desc': 'Подання через мобільний застосунок, зазначений у реєстрі.'})
    if 'Особисто' in chans:
        channels.append({'id': 'office', 'label': 'Особисто', 'desc': 'Звернутися з документами: ' + '; '.join(prov[:3]) + ('…' if len(prov) > 3 else '') + '.' if prov else 'Звернутися з документами до органу.'})
    if 'Поштою (рекомендованим листом)' in chans:
        channels.append({'id': 'mail', 'label': 'Поштою', 'desc': 'Надіслати заяву та документи рекомендованим листом.'})
    if 'Електронною поштою' in chans:
        channels.append({'id': 'email', 'label': 'Електронною поштою', 'desc': 'Надіслати заяву електронною поштою органу.'})

    roles = [{'id': ROLE[r][0], 'label': ROLE[r][1], 'hint': ROLE[r][2], 'name': r} for r in roles_raw if r in ROLE]

    # Документи: текст з реєстру + пояснення «навіщо» за типом документа + для кого
    docs = []
    for d in V._lst(z.get('input')):
        t = V._cut(d, 300).rstrip(';, ')
        if not t:
            continue
        who = 'legal' if re.search(r'для юридичн|юридичн\w+ особ\w+:', t, re.I) else ('person' if re.search(r'для фізичн\w+ осіб(?! - підприєм)', t, re.I) else '')
        docs.append({'t': t, 'cond': _cond(t), 'rep': bool(REP_RX.search(t)), 'why': doc_why(t), 'form': doc_form(t), 'who': who})

    # Профіль заявника (питаємо один раз — відповідь спільна для всіх послуг)
    applicants = V._lst(z.get('applicant_type'))
    prof_opts = [{'id': PROFILE[a][0], 'label': PROFILE[a][1], 'hint': PROFILE[a][2]} for a in PROFILE_ORDER if a in applicants]
    profile = {'allowed': [o['id'] for o in prof_opts], 'labels': {PROFILE[k][0]: PROFILE_NOUN[PROFILE[k][0]] for k in PROFILE_ORDER}}

    # Питання — лише ті, що змінюють результат (поле affects)
    questions = []
    if prof_opts:
        questions.append({'id': 'profile', 'global': True, 'affects': ['eligibility'] + (['docs'] if any(x['who'] for x in docs) else []),
                          'title': 'Хто звертається по послугу?', 'why': 'Перевіримо, чи послуга вам підходить. Відповідь запам’ятаємо для інших послуг.',
                          'options': [{'id': i, 'label': l, 'hint': h} for i, l, h in PROFILE_ALL]})
    rep_docs = any(x['rep'] and not x['cond'] for x in docs)
    if len(roles) > 1 and rep_docs:
        questions.append({'id': 'role', 'affects': ['docs'], 'title': 'Хто подає заяву?', 'why': 'Представнику потрібні документи про повноваження — покажемо лише ті, що стосуються вас.',
                          'options': [{'id': r['id'], 'label': r['label'], 'hint': r['hint']} for r in roles]})
    if decide == 'speed':
        base = min((x for x in variants if x['days'] is not None), key=lambda x: -x['days'], default=None)
        questions.append({'id': 'variant', 'affects': ['cost', 'time'], 'title': 'Який варіант надання вам підходить?', 'why': 'Варіанти відрізняються строком і вартістю — порівняйте.',
                          'options': [{'id': x['id'], 'label': x['label'], 'hint': ' · '.join(filter(None, [x['time'], x['cost']])), 'tags': x.get('tags', []),
                                       'pros': _vs(x, base)} for x in variants]})
    elif decide == 'situation':
        questions.append({'id': 'variant', 'affects': ['cost', 'time'], 'title': 'Яка ситуація стосується вас?', 'why': 'Від ситуації залежать вартість і строк.',
                          'options': [{'id': x['id'], 'label': x['label'], 'hint': ' · '.join(filter(None, [x['time'], x['cost']]))} for x in variants]})
    if len(channels) > 1:
        rec_online = any(c['id'] == 'online' and c.get('url') for c in channels)
        questions.append({'id': 'channel', 'affects': ['steps'], 'title': 'Як вам зручніше подати заяву?', 'why': 'Від способу залежать кроки подачі.' + (' Якщо є доступ до онлайн-сервісу, це зазвичай найменше кроків.' if rec_online else ''),
                          'options': [{'id': c['id'], 'label': c['label'], 'hint': c['desc'], 'tags': ['без візиту'] if c['id'] == 'online' and c.get('url') else [],
                                       'pros': CH_PROS.get(c['id'], ''), 'cons': CH_CONS.get(c['id'], '')} for c in channels]})

    # Результат і відмова
    prods = [V._cut(p, 240).rstrip('.;, ') for p in V._lst(z.get('produces')) if not re.match(r'\s*(відмов|письмова відмова|рішення про відмову)', p, re.I)]
    refus = [V._cut(p, 280).rstrip(';, ') for p in V._lst(z.get('refusal_grounds'))]
    appeal = [V._cut(p, 160).rstrip('.;, ') for p in V._lst(z.get('refusal_appeal_rules'))]
    court = str(z.get('is_appealed_in_court') or '').strip().lower() == 'так'

    # Що далі — пов'язані послуги тієї ж життєвої ситуації (реальні сторінки)
    nxt = [{'t': t, 'u': u} for t, u in EXTRA_NEXT.get(sid, [])] + [{'t': V._cut(t, 110), 'u': u} for t, u in related][:5]

    # Що уточнити (відсутні в реєстрі дані)
    verify = []
    if not docs: verify.append('Перелік документів у реєстрі не наведено — уточніть його в органі.')
    if not any(x['cost'] for x in variants): verify.append('Вартість у реєстрі не зазначена — уточніть її в органі перед зверненням.')
    if not any(x['time'] for x in variants): verify.append('Строк надання в реєстрі не зазначений.')
    if 'Online' in chans and not sub_url: verify.append('У реєстрі сказано, що заяву можна подати онлайн, але підтвердженого посилання на сервіс ми не знайшли. Перевірте повний опис послуги або подайте заяву іншим способом.')
    if dms_note: verify.append('Вартість варіанта «термінове надання за наявності підстав» (3 робочі дні) ДМС окремо не оприлюднює — уточніть у підрозділі.')
    if 'внутрішніх справ' in str(z.get('owner') or '') and any(x['costNum'] for x in variants):
        verify.append('Тарифи сервісних центрів МВС в офіційних джерелах наводяться по-різному — перевірте актуальну суму на hsc.gov.ua перед оплатою.')
    if bad_time: verify.append('Строк у реєстрі вказано незрозуміло — уточніть його в органі, що надає послугу.')
    if not channels: verify.append('Спосіб подачі заяви в реєстрі не зазначено — уточніть його в органі, що надає послугу.')
    if local: verify.append('Це місцева послуга: умови, суми й документи встановлює ваша громада. Уточніть їх у ЦНАП або виконкомі за місцем проживання.')
    review = bool(not docs or not any(x['time'] for x in variants) or ('Online' in chans and not sub_url) or not channels)

    desc = re.sub(r'\s+', ' ', str(z.get('short_description_plain') or '')).strip()
    explain = ''
    if len(desc) < 120:   # опис у реєстрі короткий або відсутній — пояснюємо з даних послуги
        bits = []
        if prods: bits.append('Результат послуги: ' + '; '.join(p.rstrip('.') for p in prods[:2]) + '.')
        who = [PROFILE[a][1].lower() for a in PROFILE_ORDER if a in V._lst(z.get('applicant_type'))]
        if who: bits.append('Хто може звернутися: ' + ', '.join(w.replace('я як ', '').replace('від ', '') for w in who) + '.')
        if prov: bits.append('Надає: ' + '; '.join(prov[:2]) + ('…' if len(prov) > 2 else '') + '.')
        explain = ' '.join(bits)
    out = {
        'v': 1, 'id': sid, 'name': name, 'arch': arch, 'archLabel': arch_label, 'desc': desc, 'explain': explain,
        'questions': questions, 'variants': variants, 'decide': decide, 'varByCh': var_by_ch, 'channels': channels, 'roles': roles, 'profile': profile,
        'providers': prov, 'cnap': has_cnap, 'docs': docs,
        'receive': [V.CH_LABEL[c] for c in rchans if c in V.CH_LABEL], 'products': prods,
        'refusal': refus, 'appeal': appeal, 'court': court,
        'next': nxt, 'verify': verify, 'review': review,
        'applicants': [V._cut(p, 80) for p in V._lst(z.get('applicant_type'))][:4],
        'spatial': (re.sub(r'україн', 'Україн', str(z.get('spatial') or '').strip().capitalize()) if str(z.get('spatial') or '').isupper() else str(z.get('spatial') or '').strip()),
        'local': local, 'guide': f'https://guide.diia.gov.ua/register/{sid}/', 'info': info_url, 'dataDate': DATA_DATE,
    }
    j = out
    if sid in ED:
        j['ed'] = ED[sid]
        if ED[sid].get('drop'):
            j['questions'] = [q for q in j['questions'] if q['id'] not in ED[sid]['drop']]
        ec = ED[sid].get('costs')
        if ec:   # актуальна вартість з офіційної сторінки замість застарілої в реєстрі
            for x, it in zip(j['variants'], ec['items']):
                if it[1] != x['cost']:
                    x['old'] = x.get('old') or x['cost']; x['cost'] = it[1]
                if len(it) > 2 and it[2] != x['time']:
                    x['time'] = it[2]
            if all(len(it) > 2 for it in ec['items']):
                j['verify'] = [v for v in j['verify'] if 'суперечливо' not in v and 'Строк надання в реєстрі не зазначений' not in v]
    if j.get('ed') and j['ed'].get('verify'):
        j['verify'] += j['ed']['verify']
    if j.get('ed') and j['ed'].get('costs'):
        for x in j['variants']: x.pop('stdNote', None)
    if any(x.get('stdNote') and not x.get('old') for x in j['variants']):
        j['verify'].append('Сума залежить від прожиткового мінімуму чи мінімальної зарплати, і в реєстрі вона може бути старою — уточніть актуальну суму в органі.')
    if any(x.get('old') and x['old'] != x['cost'] for x in j['variants']):
        j['verify'].append('У державному реєстрі вказано стару суму. Ми показуємо нову — перераховану за правилами 2026 року або взяту з офіційного сайту. Перед оплатою звірте суму в органі.')
    j['verify'] = list(dict.fromkeys(j['verify']))
    j['steps'] = {c['id']: [list(s) for s in _steps_for(j, c['id'])] for c in j['channels']}
    return j


# ---------- Статичний (індексований) рендер ----------
def _facts(j):
    rows = []
    where = []
    on = next((c for c in j['channels'] if c['id'] == 'online' and c.get('url')), None)
    if on: where.append('Онлайн — ' + e(V.host_label(on['url'])))
    off = [c['label'].lower() for c in j['channels'] if c['id'] in ('office', 'mail', 'email')]
    if j['providers'] and (off or not on):
        lead = ', '.join(off)
        where.append(e((lead[:1].upper() + lead[1:] + ': ' if lead else '') + '; '.join(j['providers'][:3]) + ('…' if len(j['providers']) > 3 else '')))
    if where: rows.append(('Де отримати', '<br>'.join(where)))
    for key, label in (('cost', 'Вартість'), ('time', 'Строк')):
        vals = [(x['label'], x[key]) for x in j['variants'] if x[key]]
        if not vals: continue
        if len({v for _, v in vals}) == 1: rows.append((label, e(vals[0][1])))
        else: rows.append((label, '<ul class="flat">' + ''.join(f'<li><span class="vl">{e(l)}</span><span class="vv">{e(v)}</span></li>' for l, v in vals) + '</ul>'))
    if j['docs']:
        n = len(j['docs'])
        rows.append(('Що підготувати', f'{n} {V.plural(n, "документ", "документи", "документів")} — <a href="#docs">чек-лист</a>'))
    return ('<dl class="facts">' + ''.join(f'<dt>{k}</dt><dd>{v}</dd>' for k, v in rows) + '</dl>') if rows else ''


def _steps_for(j, ch):
    """Кроки процедури для способу подачі (тільки з даних)."""
    out = []
    docs = bool(j['docs'])
    if ch == 'online':
        c = next(c for c in j['channels'] if c['id'] == 'online')
        if c.get('url'):
            out.append(('Відкрийте офіційний сервіс', f'Сервіс {urlparse(c["url"]).netloc}.', c['url']))
        else:
            out.append(('Знайдіть онлайн-сервіс', 'Офіційне посилання в реєстрі не підтверджене — відкрийте повний опис послуги в Гіді.', j['guide']))
        out.append(('Заповніть заяву', 'Додайте документи з вашого чек-листа.' if docs else 'Перелік документів у реєстрі не наведено — сервіс підкаже, що потрібно.', ''))
    elif ch in ('office', 'mail', 'email'):
        where = '; '.join(j['providers']) or 'орган, що надає послугу'
        if ch == 'office':
            out.append(('Оберіть, куди звернутися', where + '.', ''))
            out.append(('Візьміть документи', 'Документи з вашого чек-листа.' if docs else 'Перелік документів уточніть в органі.', ''))
            out.append(('Подайте заяву', 'Особисто в обраному органі.', ''))
        elif ch == 'mail':
            out.append(('Підготуйте заяву та документи', 'Документи з вашого чек-листа.' if docs else 'Перелік документів уточніть в органі.', ''))
            out.append(('Надішліть рекомендованим листом', 'Адресат: ' + where + '.', ''))
        else:
            out.append(('Надішліть заяву електронною поштою', 'Адресат: ' + where + '.', ''))
    elif ch == 'app':
        out.append(('Відкрийте мобільний застосунок', 'Подання через мобільний застосунок, зазначений у реєстрі.', ''))
    return out


def render_ed_static(ed, cond_label=None):
    """Редакційний зміст для індексації (у браузері — в «Повній довідці»; інтерактивно показує journey.js)."""
    out = []
    if ed.get('fit'): out.append('<h2>Кому підходить</h2><ul>' + ''.join(f'<li>{e(x)}</li>' for x in ed['fit']) + '</ul>')
    if ed.get('notFit'): out.append('<h2>Коли не підходить або є особливості</h2><ul>' + ''.join(f'<li>{e(x)}</li>' for x in ed['notFit']) + '</ul>')
    qs = {q['id']: q for q in ed.get('questions', [])}
    for b in ed.get('blocks', []):
        cond = ''
        for qid, oid in (b.get('if') or {}).items():
            q = qs.get(qid); ids = oid if isinstance(oid, list) else [oid]
            labs = [o['label'].lower() for o in (q['options'] if q else []) if o['id'] in ids]
            if q and labs: cond = f' <span class="muted">({e(q["title"].rstrip("?"))}: {e(" / ".join(labs))})</span>'
        out.append(f'<h3>{e(b["t"])}{cond}</h3><ul>' + ''.join(f'<li>{e(x)}</li>' for x in b['items']) + '</ul>'
                   + (f'<p><a href="{e(b["link"][1])}">{e(b["link"][0])}</a></p>' if b.get('link') else ''))
    if ed.get('online'): out.append('<h2>Що зробити на офіційному сайті</h2><ol>' + ''.join(f'<li>{e(x)}</li>' for x in ed['online']) + '</ol>')
    if ed.get('after'): out.append('<h2>Після подачі</h2><ul>' + ''.join(f'<li>{e(x)}</li>' for x in ed['after']) + '</ul>')
    out.append('<p class="muted">Перевірено ' + V_human(ed['verified']) + ' за джерелами: ' + '; '.join(f'<a href="{e(u)}" target="_blank" rel="noopener noreferrer">{e(t)}</a>' for t, u in ed['sources']) + '.</p>')
    return ''.join(out)


def render_static(j):
    parts = []
    if j.get('ed'):
        parts.append(f'<aside class="short"><b>Простими словами</b><p>{e(j["ed"]["intro"])}</p></aside>')
    elif j.get('explain'):
        parts.append(f'<aside class="short"><b>Що це за послуга</b><p>{e(j["explain"])}</p></aside>')
    parts.append(_facts(j))
    # Головна дія
    on = next((c for c in j['channels'] if c['id'] == 'online' and c.get('url')), None)
    parts.append('<div class="j-root" id="journey" data-sid="' + e(j['id']) + '"></div>')
    if on:
        parts.append(f'<div class="svc-main"><a class="btn primary" href="{e(on["url"])}" target="_blank" rel="noopener noreferrer">Подати онлайн</a>'
                     f'<span class="muted">Відкриється офіційний сервіс {e(urlparse(on["url"]).netloc)}</span></div>')
    # Повна довідка (індексований зміст; у браузері згортається під інтерактивним сценарієм)
    ref = ['<div class="j-ref" id="j-ref">']
    if j.get('ed'):
        ref.append(render_ed_static(j['ed']))
    if j['decide'] and j['variants']:
        ref.append('<h2>Варіанти надання</h2><table class="cmp"><thead><tr><th>Варіант</th><th>Строк</th><th>Вартість</th></tr></thead><tbody>'
                   + ''.join(f'<tr><td>{e(x["label"])}{"".join(f" <span class=chip>{e(t)}</span>" for t in x.get("tags", []))}</td><td>{e(x["time"] or "—")}</td><td>{e(x["cost"] or "—")}</td></tr>' for x in j['variants'])
                   + '</tbody></table>')
    if len(j['channels']) > 1:
        ref.append('<h2>Способи подачі: чим відрізняються</h2><ul class="opts-static">' + ''.join(
            f'<li><b>{e(c["label"])}.</b> {e(c["desc"])}' + (f' <span class="muted">Перевага: {e(CH_PROS[c["id"]])} Обмеження: {e(CH_CONS[c["id"]])}</span>' if c['id'] in CH_PROS else '') + '</li>'
            for c in j['channels']) + '</ul>')
    if j['docs']:
        ref.append('<h2 id="docs">Чек-лист документів</h2><ul class="docs">' + ''.join(
            f'<li>{e(d["t"])}' + (f'<small class="cond">Навіщо: {e(d["why"])}</small>' if d.get('why') else '')
            + (f'<small class="cond">Форма: {e(d["form"])}</small>' if d.get('form') else '')
            + (f'<small class="cond">Лише якщо: {e(d["cond"])}</small>' if d['cond'] else '')
            + ('<small class="cond">Для представника</small>' if d['rep'] and not d['cond'] else '') + '</li>' for d in j['docs']) + '</ul>')
    if any(j['steps'].get(c['id']) for c in j['channels']):
        ref.append('<h2>Як отримати послугу</h2>')
    for c in j['channels']:
        steps = _steps_for(j, c['id'])
        if not steps: continue
        ref.append(f'<h3>{e(c["label"])}</h3><ol class="osteps">' + ''.join(
            f'<li class="ostep"><span class="num">{i}</span><div class="body"><b>{e(t)}</b><span>{e(d)}</span>'
            + (f'<div class="oact"><a class="btn ghost sm-btn" href="{e(u)}" target="_blank" rel="noopener noreferrer">Відкрити</a></div>' if u else '') + '</div></li>'
            for i, (t, d, u) in enumerate(steps, 1)) + '</ol>')
    res = []
    if j['products']: res.append(V._end('Ви отримаєте: ' + '; '.join(j['products'])))
    times = {x['time'] for x in j['variants'] if x['time']}
    if len(times) == 1: res.append(V._end('Строк: ' + next(iter(times))))
    if j['receive']: res.append(V._end('Отримати результат можна ' + ', '.join(j['receive'])))
    if res: ref.append('<h2>Результат</h2><p>' + e(' '.join(res)) + '</p>')
    if j['refusal'] or j['appeal'] or j['court']:
        b = '<h2>Якщо відмовили</h2>'
        if j['refusal']:
            b += '<p>Підстави для відмови за реєстром:</p><ul>' + ''.join(f'<li>{e(x)}</li>' for x in j['refusal'][:6]) + '</ul>'
            if len(j['refusal']) > 6: b += f'<p class="muted">Ще {len(j["refusal"]) - 6} — у повному описі послуги.</p>'
        ap = []
        if j['appeal']: ap.append(V._end('Оскаржити рішення можна: ' + '; '.join(j['appeal'])))
        if j['court']: ap.append('Рішення можна оскаржити в суді.')
        if ap: b += '<p>' + e(' '.join(ap)) + '</p>'
        ref.append(b)
    ref.append('</div>')
    parts.append(''.join(ref))
    if j['next']:
        parts.append('<h2>Що далі: пов’язані послуги</h2><ul class="related">' + ''.join(f'<li><a href="{e(n["u"])}">{e(n["t"])}</a></li>' for n in j['next']) + '</ul>')
    if j['verify']:
        parts.append('<h2>Що уточнити</h2><ul class="verify">' + ''.join(f'<li>{e(x)}</li>' for x in j['verify']) + '</ul>')
    cond = []
    if j['applicants']: cond.append(('Для кого', ', '.join(j['applicants'])))
    if j['spatial']: cond.append(('Де діє', j['spatial']))
    cond.append(('Тип послуги', j['archLabel']))
    parts.append('<h2>Додаткові умови</h2><dl class="kv">' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in cond) + '</dl>')
    src = [f'<li><a href="{j["guide"]}" target="_blank" rel="noopener noreferrer">Гід з державних послуг, послуга № {e(j["id"])}</a> — повний опис і нормативна база</li>']
    if on: src.append(f'<li><a href="{e(on["url"])}" target="_blank" rel="noopener noreferrer">Онлайн-сервіс ({e(urlparse(on["url"]).netloc)})</a></li>')
    if j['info']: src.append(f'<li><a href="{e(j["info"])}" target="_blank" rel="noopener noreferrer">Офіційна сторінка ({e(urlparse(j["info"]).netloc)})</a></li>')
    parts.append('<h2>Офіційне джерело</h2><ul>' + ''.join(src) + '</ul>'
                 + f'<p class="muted">Дані реєстру станом на {V_human(j["dataDate"])}. Факти — з реєстру; формулювання кроків — пояснення «Як?».</p>')
    data = json.dumps(j, ensure_ascii=False).replace('</', '<\\/')
    parts.append(f'<script type="application/json" id="journey-data">{data}</script>')
    return '\n'.join(p for p in parts if p)


MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']


def V_human(d):
    y, m, dd = d.split('-')
    return f'{int(dd)} {MONTHS[int(m) - 1]} {y}'

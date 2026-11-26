# -*- coding: utf-8 -*-
"""Пріоритизація послуг для редакційного опрацювання (внутрішній інструмент, не публікується).

Вага: гроші/виплати, юридична значущість, складність (варіанти, способи, ролі), для громадян,
наявність офіційної онлайн-сторінки (можна перевірити факти), життєві події «Як?».
Результат: _build/priority.json.
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import svc_v2 as V

HERE = os.path.dirname(__file__)
R = {z['identifier']: z for z in json.load(open(os.path.join(HERE, 'registry.json'), encoding='utf8'))['entries']}
X = json.load(open(os.path.join(HERE, 'export.json'), encoding='utf8'))
ev_of = {}
for ev in X['GUIDE_EVENTS']:
    for sec, ids in X['GUIDE_SECTORS'][ev['id']]:
        for i in ids: ev_of.setdefault(i, ev['id'])
KEY_EVENTS = {'birth': 3, 'family': 2, 'idp': 3, 'war': 3, 'social': 3, 'passport': 3, 'move': 2, 'housing': 2, 'death': 2, 'b-start': 3, 'b-tax': 2, 'labor': 2, 'pension': 2, 'veterans': 2}
MONEY = r'допомог|виплат|субсиді|компенсаці|пенсі|пільг|ваучер|кредит|відшкодуван'
LEGAL = r'реєстрац|паспорт|свідоцтв|припинен|статус|право власності|спадщин|опік|усиновл'
built = {d.split('-')[0] for d in os.listdir(os.path.join(HERE, '..', 's')) if os.path.isdir(os.path.join(HERE, '..', 's', d))}

rows = []
for sid in built:
    z = R[sid]; name = z['name']
    roles, chans, _ = V.ways(z.get('application_ways'))
    sub, _ = V.links(z)
    vs = z.get('variations') or []
    app = V._lst(z.get('applicant_type'))
    s = 0
    s += 4 if re.search(MONEY, name, re.I) else 0
    s += 3 if re.search(LEGAL, name, re.I) else 0
    s += 3 if 'Фізична особа' in app else 0
    s += min(len(vs), 3) + min(len(chans), 3) + (1 if len(roles) > 1 else 0)
    s += 2 if sub and 'diia.gov.ua' in sub else (1 if sub else 0)
    s += KEY_EVENTS.get(ev_of.get(sid), 0)
    rows.append({'id': sid, 'score': s, 'event': ev_of.get(sid), 'name': name[:110], 'online': sub})
rows.sort(key=lambda r: -r['score'])
json.dump(rows, open(os.path.join(HERE, 'priority.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
for r in rows[:45]:
    print(r['score'], r['id'], r['event'], '|', r['name'][:85], '|', (r['online'] or '')[:70])

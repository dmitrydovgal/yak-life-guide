# -*- coding: utf-8 -*-
"""Фінальний QA усіх сценаріїв (внутрішній інструмент). Виводить зведення й пише _build/qa_report.json."""
import json, re, glob, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R = {z['identifier']: z for z in json.load(open(os.path.join(HERE, 'registry.json'), encoding='utf8'))['entries']}
PRI = {r['id']: r['score'] for r in json.load(open(os.path.join(HERE, 'priority.json'), encoding='utf8'))}

issues = collections.defaultdict(list)
verify_groups = collections.defaultdict(list)
finance = collections.defaultdict(list)
J = {}
for f in glob.glob(os.path.join(ROOT, 's', '*', 'index.html')):
    t = open(f, encoding='utf8').read()
    sid = os.path.basename(os.path.dirname(f)).split('-')[0]
    if not t.rstrip().endswith('</html>'): issues['page_incomplete'].append(sid); continue
    m = re.search(r'id="journey-data">(.*?)</script>', t, re.S)
    if not m: issues['no_journey'].append(sid); continue
    j = json.loads(m.group(1).replace('<\\/', '</')); J[sid] = j
    if t.count('<link rel="canonical"') != 1: issues['canonical'].append(sid)
    # 1. Опис
    if len(j.get('desc') or '') < 40 and len(j.get('explain') or '') < 60 and not j.get('ed'): issues['generic_description'].append(sid)
    # 2. Питання: дублікати й «нічого не змінюють»
    ids = [q['id'] for q in j['questions']] + [q['id'] for q in (j.get('ed') or {}).get('questions', [])]
    if len(ids) != len(set(ids)): issues['duplicate_question_id'].append(sid)
    titles = [q['title'].lower() for q in j['questions']] + [q['title'].lower() for q in (j.get('ed') or {}).get('questions', [])]
    if len(titles) != len(set(titles)): issues['duplicate_question_title'].append(sid)
    for q in j['questions']:
        if len(q['options']) < 2: issues['question_single_option'].append(sid)
        if q['id'] == 'variant' and len({(v['cost'], v['time']) for v in j['variants']}) == 1: issues['variant_q_no_effect'].append(sid)
    # 3. Документи, які ніхто не побачить
    allowed = j['profile']['allowed']
    roleq = any(q['id'] == 'role' for q in j['questions'])
    if not roleq and any(d['rep'] and not d['cond'] for d in j['docs']) and len(j['roles']) > 1:
        issues['rep_docs_without_role_q'].append(sid)
    # 4. Способи подачі
    chs = [c['id'] for c in j['channels']]
    if not chs: issues['no_channels'].append(sid)
    if 'online' in chs and not next(c for c in j['channels'] if c['id'] == 'online').get('url'): issues['online_without_link'].append(sid)
    # 5. Хибне «не для вас»: профілі без жодного дозволеного або дивні набори
    if not allowed: issues['no_applicant_types'].append(sid)
    # 6. Посилання «Що далі» на неіснуючі сторінки
    for n in j['next']:
        p = os.path.normpath(os.path.join(os.path.dirname(f), n['u']))
        if not os.path.exists(os.path.join(p, 'index.html')) and not os.path.exists(p): issues['broken_next_link'].append((sid, n['u']))
    # 7. Строки
    for v in j['variants']:
        tm = v['time']
        if tm and re.search(r'^0\b|\b0 (днів|годин|хвилин)', tm): issues['zero_time'].append(sid)
        if v.get('days') and v['days'] > 400: issues['huge_time'].append((sid, tm))
    # Групи «Що уточнити»
    for x in j['verify']:
        k = ('cost_unknown' if 'Вартість у реєстрі не зазначена' in x else 'time_unknown' if 'Строк надання в реєстрі не зазначений' in x else
             'time_contradictory' if 'суперечливо' in x or 'незрозуміло' in x else 'online_unconfirmed' if 'підтвердженого посилання на сервіс' in x or 'посилання на сервіс не підтверджене' in x else
             'no_channel' if 'Спосіб подачі' in x else 'docs_missing' if 'Перелік документів' in x else
             'cost_stale_std' if 'залежить від прожиткового' in x else 'cost_recalculated' if 'стару суму' in x else
             'local_service' if 'місцева послуга' in x.lower() else 'other')
        verify_groups[k].append(sid)
    # Фінанси
    raw = R[sid].get('variations') or []
    for x, rv in zip(j['variants'], raw):
        src = (rv.get('identifier') or '') + ' ' + ' '.join(str(c.get('verbose') or '') for c in rv.get('costs') or [])
        if re.search(r'прожитков', src, re.I): finance['depends_on_pm'].append(sid)
        if re.search(r'мінімальн\w* заробітн', src, re.I): finance['depends_on_mzp'].append(sid)
        if x.get('old'): finance['changed_by_us'].append((sid, x['old'], x['cost']))
        if x.get('stdNote') and not x.get('old'): finance['std_not_recalculated'].append(sid)
        bad = [c.get('verbose') for c in rv.get('costs') or [] if (c.get('verbose') or '').strip() and not re.search(r'\d|безоплат|безкоштов', str(c.get('verbose')) + str(c.get('type') or ''), re.I)]
        if bad: finance['cost_text_invalid'].append((sid, bad[0][:60]))
        if x['costNum'] and x['costNum'] > 0 and not x.get('old') and not re.search(r'прожитков|заробітн', src, re.I):
            finance['fixed_price'].append(sid)

def uniq(l): return sorted(set(l), key=lambda x: str(x))
out = {'issues': {k: uniq(v) for k, v in issues.items()}, 'verify': {k: uniq(v) for k, v in verify_groups.items()},
       'finance': {k: uniq(v) for k, v in finance.items()}}
vset = {s for v in verify_groups.values() for s in v}
top = sorted(vset, key=lambda s: -PRI.get(s, 0))[:30]
out['top30'] = [(s, PRI.get(s), J[s]['name'][:90], J[s]['verify']) for s in top]
json.dump(out, open(os.path.join(HERE, 'qa_report.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
print('pages', len(J))
print('ISSUES', {k: len(v) for k, v in out['issues'].items()})
print('VERIFY services', len(vset), {k: len(v) for k, v in out['verify'].items()})
print('FINANCE', {k: len(v) for k, v in out['finance'].items()})

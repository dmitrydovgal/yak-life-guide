# -*- coding: utf-8 -*-
"""Аудит якості сценаріїв усіх послуг (запускається після build_pages.py).

Оцінює кожну послугу за 9 критеріями (0–2 бали) і класифікує її.
Результат: _build/audit_services.json (внутрішній список, не публікується — _build в .assetsignore).
"""
import json, re, glob, os, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def load(f):
    t = open(f, encoding='utf8').read()
    m = re.search(r'id="journey-data">(.*?)</script>', t, re.S)
    return json.loads(m.group(1).replace('<\\/', '</')) if m else None


def score(j):
    s = {}
    s['explain'] = 2 if len(j.get('desc') or '') > 120 or j.get('ed') or len(j.get('explain') or '') > 60 else (1 if j.get('desc') or j.get('explain') else 0)
    s['journey'] = 2 if j['docs'] and j['channels'] and (j['products'] or j['receive']) else (1 if j['channels'] else 0)
    decisive = [q for q in j['questions'] if q.get('affects')]
    choice = [q for q in decisive if q['id'] in ('variant', 'channel')]
    explained = any(any(o.get('pros') or o.get('cons') for o in q['options']) for q in choice)
    s['decision'] = 2 if j.get('ed') or explained else (1 if choice else (2 if len(j['variants']) <= 1 and len(j['channels']) <= 1 else 0))
    s['personal'] = 2 if len(decisive) >= 2 or j.get('ed') else (1 if decisive else 0)
    s['steps'] = 2 if all(j['steps'].get(c['id']) for c in j['channels']) and j['channels'] and j['docs'] else (1 if j['channels'] else 0)
    s['result'] = 2 if j['products'] and any(v['time'] for v in j['variants']) else (1 if j['products'] or j['receive'] else 0)
    s['next'] = 2 if j['next'] else 0
    s['facts'] = 2 if not j['verify'] else (1 if len(j['verify']) == 1 else 0)
    s['ux'] = 2 if len(j['questions']) <= 3 else 1
    return s


def classify(j, s):
    cls = []
    if s['journey'] == 0 or not j['channels']: cls.append('critical')
    if not j['docs'] or s['result'] == 0: cls.append('insufficient')
    if s['decision'] == 0: cls.append('no_decision')
    if s['personal'] == 0: cls.append('not_personal')
    if j['verify']: cls.append('needs_verification')
    if s['explain'] < 2: cls.append('too_generic')
    if not cls: cls.append('ready')
    return cls


def main():
    rows, cnt, tot = [], collections.Counter(), collections.Counter()
    for f in glob.glob(os.path.join(ROOT, 's', '*', 'index.html')):
        j = load(f)
        if not j: cnt['no_journey'] += 1; continue
        s = score(j); c = classify(j, s)
        for k in c: cnt[k] += 1
        for k, v in s.items(): tot[k] += v
        rows.append({'id': j['id'], 'name': j['name'][:120], 'arch': j['arch'], 'score': sum(s.values()), 'by': s, 'class': c, 'verify': j['verify'], 'editorial': bool(j.get('ed'))})
    rows.sort(key=lambda r: r['score'])
    json.dump({'total': len(rows), 'classes': cnt, 'avg': {k: round(v / max(len(rows), 1), 2) for k, v in tot.items()}, 'services': rows},
              open(os.path.join(os.path.dirname(__file__), 'audit_services.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('services', len(rows))
    print('classes', dict(cnt))
    print('avg score per criterion (0-2)', {k: round(v / len(rows), 2) for k, v in tot.items()})
    print('editorial', sum(1 for r in rows if r['editorial']), '| recalculated costs', sum(1 for f in glob.glob(os.path.join(ROOT, 's', '*', 'index.html')) if '"old":' in open(f, encoding='utf8').read()))
    print('score distribution', sorted(collections.Counter(r['score'] // 3 * 3 for r in rows).items()))


if __name__ == '__main__':
    main()

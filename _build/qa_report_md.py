# -*- coding: utf-8 -*-
"""Читабельний звіт QA з _build/qa_report.json → _build/qa_report.md (внутрішній документ)."""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
H = os.path.dirname(os.path.abspath(__file__))
q = json.load(open(os.path.join(H, 'qa_report.json'), encoding='utf8'))
L = ['# QA-звіт «Як?»: сценарії послуг', '', 'Згенеровано скриптом `_build/qa_check.py` + `_build/qa_report_md.py`. Дата перевірки: 26.11.2026.', '']
names = {}
for s, p, n, v in q['top30']: names[s] = n
L += ['## Причини позначки «Що уточнити»', '', '| Причина | Послуг |', '|---|---|']
lab = {'local_service': 'Місцева послуга (порядок залежить від громади)', 'online_unconfirmed': 'Онлайн-подання без підтвердженого посилання',
       'cost_recalculated': 'Вартість у реєстрі застаріла — показано перераховану', 'time_contradictory': 'Суперечливий строк у реєстрі',
       'cost_unknown': 'Вартість не зазначена', 'cost_stale_std': 'Сума від соцстандарту, не перерахована', 'no_channel': 'Спосіб подачі не зазначено',
       'other': 'Редакційні примітки (ВПО, паспорт, інвалідність)', 'docs_missing': 'Немає переліку документів', 'time_unknown': 'Строк не зазначено'}
for k, v in sorted(q['verify'].items(), key=lambda x: -len(x[1])):
    L.append(f'| {lab.get(k, k)} | {len(v)} |')
L += ['', '## 30 найважливіших послуг для ручної перевірки (за пріоритетом)', '', '| № | ID | Послуга | Що уточнити |', '|---|---|---|---|']
for i, (s, p, n, v) in enumerate(q['top30'], 1):
    L.append(f'| {i} | {s} | {n} | {"; ".join(v)} |')
f = q['finance']
L += ['', '## Фінансові дані', '',
      f'- Сума залежить від прожиткового мінімуму: {len(set(f.get("depends_on_pm", [])))} послуг.',
      f'- Сума залежить від мінімальної зарплати: {len(set(f.get("depends_on_mzp", [])))} послуг.',
      f'- Фіксована ціна в гривнях без формули (може бути застарілою, не перевірялась): {len(set(f.get("fixed_price", [])))} послуг.',
      f'- Вартість у реєстрі текстом, а не сумою: {len(f.get("cost_text_invalid", []))} записів.',
      f'- Сума від соцстандарту, яку не перераховано (немає однозначної формули): {len(set(f.get("std_not_recalculated", [])))} послуг — {", ".join(sorted(set(f.get("std_not_recalculated", []))))}.',
      '', '### Змінені нами суми (джерело — формула реєстру або офіційна сторінка)', '', '| ID | Було в реєстрі | Показуємо |', '|---|---|---|']
for s, old, new in f.get('changed_by_us', []):
    L.append(f'| {s} | {old} | {new} |')
L += ['', '### Технічні знахідки', '']
for k, v in q['issues'].items():
    L.append(f'- {k}: {len(v)}')
open(os.path.join(H, 'qa_report.md'), 'w', encoding='utf8').write('\n'.join(L) + '\n')
print('written', len(L), 'lines')

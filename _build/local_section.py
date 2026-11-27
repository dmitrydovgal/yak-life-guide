"""Розділ «Місцеві сервіси» (/local/): один довідник без окремих сторінок міст.

Дані: local_services.py (публікуємо лише published(): verified + partial, без дублів і непідтверджених).
Пише: local/index.html (усі картки в HTML — працює без JS), local/services.json (для блоків у статтях і сценаріях).
Віджет для статей і сценаріїв — local/widget.js (ручний файл у корені сайту, читає services.json).
"""
import json, re
from urllib.parse import urlparse
import local_services as L

_ctx = {}
MONTHS = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня']
MAIN_ACTS = ('pay', 'readings', 'debt')
ACT_DONE = {'pay': 'оплату', 'readings': 'передачу показників', 'debt': 'перевірку боргу й нарахувань'}
TYPE_ORDER = {'unified': 0, 'utility': 1, 'network': 2, 'supplier': 3, 'payment': 9}
OWNER_TXT = {'municipal': 'Комунальне підприємство', 'private': 'Приватна компанія'}
# Що показуємо у фільтрі «Послуга» (інші категорії входять до «Усі»)
UTIL_FILTER = [('water', 'Вода'), ('heat', 'Опалення й гаряча вода'), ('gasdist', 'Газ (розподіл)'), ('unified', 'Єдиний рахунок за кілька послуг')]


def init(**kw): _ctx.update(kw)
def _c(k): return _ctx[k]
def _e(t): return _ctx['e'](t)
def _norm(t): return re.sub(r'\s+', ' ', t.lower().replace('’', "'").replace('ʼ', "'"))


def human_date(d):
    y, m, dd = d.split('-'); return f'{int(dd)} {MONTHS[int(m) - 1]} {y}'


def host(u): return urlparse(u).netloc.replace('www.', '')


def cities_of(s):
    return [L.PLACES[p]['name'] for p in s['places']]


def city_label(s):
    if len(s['places']) == len(L.PLACES): return 'Усі міста, де оператор газорозподілу — «Газмережі»'
    return ', '.join(cities_of(s))


def util_label(s): return ', '.join(L.UTIL[u] for u in s['util'])


def acts(s):
    yes = [k for k in L.ACTIONS if s['actions'].get(k)]
    unk = [k for k in MAIN_ACTS if s['actions'].get(k) is None]
    return yes, unk


def badges(s):
    st = ('<span class="lst lst-ok">Перевірено</span>' if s['status'] == 'verified'
          else '<span class="lst lst-part">Частково перевірено</span>')
    kind = f'<span class="kind lk-{s["type"]}">{_e(L.TYPES[s["type"]])}</span>'
    own = OWNER_TXT.get(s['owner'])
    if s['type'] == 'payment': own = 'Не є системою міста'
    return st + kind + (f'<span class="lown">{_e(own)}</span>' if own else '')


def card(s, r):
    """Картка сервісу. Підтверджені дії — галочки; непідтверджені головні дії — окремим рядком."""
    yes, unk = acts(s)
    sid = s['id']
    q = _norm(' '.join([s['name'], s['operator'], util_label(s), L.TYPES[s['type']], ' '.join(cities_of(s)) if len(s['places']) < len(L.PLACES) else 'газ газмережі',
                        ' '.join(s['providers']), host(s['url']), ' '.join(L.ACTIONS[k] for k in yes)]))
    ut = ' '.join(s['util'] + (['unified'] if s['type'] == 'unified' else []))
    scope = ''.join(f'<p class="lscope"><b>Лише частина території:</b> {_e(L.PLACES[p]["name"])} — {_e(t)}</p>' for p, t in s['scope'].items())
    act_html = ('<ul class="lacts">' + ''.join(f'<li>{_e(L.ACTIONS[k])}</li>' for k in yes) + '</ul>') if yes else \
        '<p class="lnone">Що саме можна зробити на сайті, ми ще не підтвердили. Відкрийте сайт і перевірте самі.</p>'
    unk_html = f'<p class="lunk">Не підтвердили: {_e(", ".join(ACT_DONE[k] for k in unk))}.</p>' if (unk and yes) else ''
    lim = f'<p class="llim"><b>Важливо:</b> {_e(s["limits"])}</p>' if s['limits'] else ''
    prov = f'<p class="lprov">{_e("; ".join(s["providers"]))}</p>' if s['providers'] else ''
    app = f'<p class="lprov">Застосунок: {_e(s["app"])}</p>' if s['app'] else ''
    how = ('<details class="lhow"><summary>Як почати</summary><ol>' + ''.join(f'<li>{_e(x)}</li>' for x in s['howto']) + '</ol></details>') if s['howto'] else ''
    src = '<ul class="lsrc">' + ''.join(f'<li><a href="{_e(u)}" target="_blank" rel="noopener noreferrer">{_e(host(u))}</a> — {_e(w)}</li>' for u, w in s['sources']) + '</ul>'
    btn = 'Відкрити кабінет' if s['cabinet'] != s['url'] else 'Відкрити сайт'
    return (f'<li class="lcard lc-{s["type"]}" id="{sid}" data-city="{" ".join(s["places"])}" data-util="{ut}" data-act="{" ".join(yes)}" '
            f'data-o="{TYPE_ORDER[s["type"]]}" data-q="{_e(q)}">'
            f'<div class="lcard-top">{badges(s)}</div>'
            f'<h2 class="lcard-title">{_e(s["name"])}</h2>'
            f'<p class="lcity">{_e(city_label(s))} · {_e(util_label(s))}</p>{scope}'
            f'{act_html}{unk_html}{lim}{prov}{app}{how}'
            f'<div class="lcard-actions"><a class="btn {"ghost" if s["type"] == "payment" else "primary"} sm-btn" href="{_e(s["cabinet"])}" target="_blank" rel="noopener noreferrer">{btn} <span class="sr-only">(відкриється в новій вкладці)</span></a>'
            + (f'<a class="btn ghost sm-btn" href="{_e(s["url"])}" target="_blank" rel="noopener noreferrer">Сайт</a>' if s['cabinet'] != s['url'] else '') +
            f'</div><div class="lsrc-box"><b>Джерело перевірки</b> · {human_date(s["checked"])}{src}</div></li>')


def _sorted(lst):
    return sorted(lst, key=lambda s: (TYPE_ORDER[s['type']], 0 if s['status'] == 'verified' else 1, city_label(s), s['name']))


def index():
    r = '../'; S = _c('SITE'); url = S + 'local/'
    pub = _sorted(L.published())
    cnt = {p: sum(1 for s in pub if p in s['places'] and s['type'] != 'network') for p in L.PLACES}
    places = sorted(L.PLACES.items(), key=lambda kv: kv[1]['name'])
    opts = '<option value="">Усі міста</option>' + ''.join(
        f'<option value="{p}">{_e(v["name"])}{"" if cnt[p] else " — поки немає перевірених"}</option>' for p, v in places)
    row = lambda name, v, t: (f'<label class="frow"><input type="radio" name="{name}" value="{v}"{" checked" if not v else ""}>'
                              f'<span>{_e(t)}</span><span class="n" data-n="{name}:{v}"></span></label>')
    side = ('<aside class="shop-side" aria-label="Вибір міста та фільтри">'
            f'<div class="lcity-box"><label class="flabel" for="lcity">Ваше місто</label><select id="lcity" class="lsel">{opts}</select></div>'
            '<details class="side-box" id="fbox" open><summary>Фільтри</summary><div class="side-in">'
            '<label class="flabel" for="lq">Пошук</label>' + _c('search_box')('lq', 'Пошук місцевих сервісів', 'Назва, постачальник, послуга…')
            + '<fieldset><legend>Послуга</legend>' + row('util', '', 'Усі послуги') + ''.join(row('util', k, t) for k, t in UTIL_FILTER) + '</fieldset>'
            + '<fieldset><legend>Що потрібно зробити</legend>' + row('act', '', 'Будь-що') + ''.join(row('act', k, L.ACTIONS[k]) for k in MAIN_ACTS) + '</fieldset>'
            + '<button type="button" class="btn ghost freset" id="freset">Скинути фільтри</button></div></details></aside>')
    n_ver = sum(1 for s in pub if s['status'] == 'verified'); n_city = sum(1 for p in cnt if cnt[p])
    body = f'''<div class="container shop local">
{_c('crumbs')([('Головна', ''), ('Місцеві сервіси', '')], r)}
<div class="shop-head"><h1>Місцеві комунальні сервіси</h1>
<p class="lead">У багатьох містах є свій сайт для комунальних платежів: єдиний рахунок або кабінет водоканалу чи теплопостачальника. Оберіть місто — і побачите, що там можна зробити онлайн.</p>
<div class="lhow-check"><p><span class="lst lst-ok">Перевірено</span> — можливості описані на офіційному сайті самого сервісу або міста.</p>
<p><span class="lst lst-part">Частково перевірено</span> — сайт справжній, але не все, що там можна зробити, ми підтвердили. Непідтверджене не показуємо як можливість.</p>
<p class="muted">Перевірено {human_date(L.CHECKED)}: {len(pub)} сервісів у {n_city} містах, з них {n_ver} перевірено повністю. Ми не входили в кабінети й не збирали персональних даних.</p></div></div>
<div class="shop-body">
{side}
<section class="shop-main" aria-label="Місцеві сервіси">
<div class="shop-bar"><p id="lcount" aria-live="polite">Знайдено: {len(pub)}</p></div>
<p class="empty-note" id="lempty" hidden></p>
<ul class="lcards" id="llist">{''.join(card(s, r) for s in pub)}</ul>
<aside class="callout"><b>Не знайшли свого постачальника?</b> Назва компанії й особовий рахунок є у вашій квитанції. Як діяти далі — у статті <a href="{r}blog/yak-znayty-postachalnyka-komunalnyh-poslug/">«Як знайти постачальника комунальних послуг»</a>. Платіжні сервіси на кшталт банків і EasyPay теж приймають оплату, але вони не ведуть нарахувань — <a href="{r}blog/yak-oplatyty-komunalku-online/">як ними користуватися</a>.</aside>
</section>
</div>
</div>
<script>{_JS}</script>'''
    ld = [_c('bc_ld')([('Головна', S), ('Місцеві сервіси', url)]),
          {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Місцеві комунальні сервіси', 'url': url, 'inLanguage': 'uk',
           'dateModified': L.CHECKED, 'about': 'Офіційні сайти й кабінети для оплати комунальних послуг, передачі показників і перевірки боргу в містах України'}]
    return _c('page')(1, 'Місцеві комунальні сервіси: єдиний рахунок і кабінети за містами — Як?',
                      'Де у вашому місті оплатити комуналку, передати показники й перевірити борг: єдині рахунки, кабінети водоканалів і теплопостачальників. Лише перевірені офіційні сайти.',
                      url, body, _c('ld_script')(ld), 'website', 'local')


def services_json():
    """Дані для віджета в статтях і сценаріях (лише опубліковані записи)."""
    out = []
    for s in _sorted(L.published()):
        yes, unk = acts(s)
        out.append({'id': s['id'], 'n': s['name'], 't': s['type'], 'tl': L.TYPES[s['type']], 'st': s['status'], 'own': OWNER_TXT.get(s['owner'], ''),
                    'p': s['places'], 'all': len(s['places']) == len(L.PLACES), 'cl': city_label(s), 'ul': util_label(s), 'u': s['cabinet'],
                    'yes': yes, 'unk': [ACT_DONE[k] for k in unk] if yes else [], 'lim': s['limits'],
                    'sc': {p: t for p, t in s['scope'].items()}, 'src': host(s['sources'][0][0])})
    places = {p: v['name'] for p, v in sorted(L.PLACES.items(), key=lambda kv: kv[1]['name'])}
    return json.dumps({'checked': L.CHECKED, 'places': places, 'acts': L.ACTIONS, 's': out}, ensure_ascii=False)


def search_entries():
    """Записи для загального пошуку сайту (documents/search.json)."""
    out = []
    for s in _sorted(L.published()):
        yes, _ = acts(s)
        if len(s['places']) == len(L.PLACES):
            u, cities = f'local/?util=gasdist#{s["id"]}', 'газ показники газмережі'
        else:
            u, cities = f'local/?city={s["places"][0]}#{s["id"]}', ' '.join(cities_of(s))
        d = f'{city_label(s)} · ' + (', '.join(L.ACTIONS[k].lower() for k in yes) if yes else L.TYPES[s['type']].lower())
        out.append({'k': 'local', 't': s['name'], 'a': ' '.join([cities, s['operator'], util_label(s), 'комуналка комунальні місцеві', host(s['url'])]),
                    'u': u, 'd': _c('cut')(d, 120)})
    return out


def build():
    w, S, U = _c('write'), _c('SITE'), _c('URLS')
    errs = L.check()
    assert not errs, errs
    w('local/index.html', index()); U.append(S + 'local/')
    w('local/services.json', services_json())
    return len(L.published())


# Фільтри довідника: місто (select), пошук, послуга, дія. Стан — у адресі (?city=…&util=…), щоб можна було поділитися посиланням.
# Без JS усі картки просто видно списком.
_JS = r"""(function(){var ul=document.getElementById('llist'),L=[].slice.call(ul.children),c=document.getElementById('lcity'),q=document.getElementById('lq'),box=document.getElementById('fbox'),em=document.getElementById('lempty');
if(window.matchMedia('(max-width:860px)').matches)box.open=false;
function n(t){return (t||'').toLowerCase().replace(/[’ʼ]/g,"'").replace(/\s+/g,' ').trim()}
function val(k){var x=document.querySelector('input[name='+k+']:checked');return x?x.value:''}
function setv(k,v){var x=document.querySelector('input[name='+k+'][value="'+(v||'')+'"]');if(x)x.checked=true}
function has(a,v){return !v||(' '+a+' ').indexOf(' '+v+' ')>-1}
function hit(li,f,s){return has(li.dataset.city,f.city)&&has(li.dataset.util,f.util)&&has(li.dataset.act,f.act)&&s.every(function(w){return li.dataset.q.indexOf(w)>-1})}
function run(push){var s=n(q.value).split(' ').filter(Boolean),f={city:c.value,util:val('util'),act:val('act')},k=0,loc=0;
L.forEach(function(li){var ok=hit(li,f,s);li.hidden=!ok;if(ok){k++;if(li.dataset.o!=='2')loc++}});
[].forEach.call(document.querySelectorAll('.frow .n'),function(sp){var p=sp.dataset.n.split(':'),g={city:f.city,util:f.util,act:f.act};g[p[0]]=p[1];
sp.textContent=L.filter(function(li){return hit(li,g,s)}).length});
document.getElementById('lcount').textContent='Знайдено: '+k;
var cn=c.value?c.options[c.selectedIndex].text.replace(/ — .*/,''):'';
if(c.value&&!loc&&!s.length&&!f.util&&!f.act){em.innerHTML='Для міста '+cn+' ми поки не перевірили жодного місцевого сервісу. Подивіться назву постачальника у квитанції — і скористайтеся його сайтом або <a href="../blog/yak-znayty-postachalnyka-komunalnyh-poslug/">порадами, як його знайти</a>.'+(k?' Нижче — загальнонаціональний сервіс, який може стосуватися і вас.':'');em.hidden=false}
else if(!k){em.innerHTML='Нічого не знайдено. Спробуйте інше слово або <button type="button" class="linkbtn" id="freset2">скиньте фільтри</button>.';em.hidden=false;document.getElementById('freset2').onclick=reset}
else em.hidden=true;
box.querySelector('summary').textContent='Фільтри'+((f.util||f.act||s.length)?' · обрано':'');
try{if(c.value)localStorage.setItem('yak-local-city',c.value)}catch(e){}
if(push){var u=new URLSearchParams();if(f.city)u.set('city',f.city);if(f.util)u.set('util',f.util);if(f.act)u.set('act',f.act);if(q.value)u.set('q',q.value);
history.replaceState(null,'',location.pathname+(u.toString()?'?'+u:'')+location.hash)}}
function reset(){q.value='';c.value='';setv('util','');setv('act','');run(true)}
q.addEventListener('input',function(){run(true)});c.addEventListener('change',function(){run(true)});
[].forEach.call(document.querySelectorAll('.frow input'),function(i){i.addEventListener('change',function(){run(true)})});
document.getElementById('freset').addEventListener('click',reset);
var p=new URLSearchParams(location.search),pc=p.get('city');if(!pc){try{pc=localStorage.getItem('yak-local-city')}catch(e){}}
if(pc&&c.querySelector('option[value="'+pc+'"]'))c.value=pc;setv('util',p.get('util'));setv('act',p.get('act'));if(p.get('q'))q.value=p.get('q');
if(location.hash){var t=document.getElementById(location.hash.slice(1));if(t&&t.classList.contains('lcard')){c.value=c.querySelector('option[value="'+(p.get('city')||'')+'"]')?(p.get('city')||''):'';}}
run(false);if(location.hash){var t2=document.getElementById(location.hash.slice(1));if(t2&&!t2.hidden){t2.classList.add('lflash');t2.scrollIntoView()}}})();"""

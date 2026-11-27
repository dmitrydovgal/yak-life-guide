/* «Місцевий сервіс у вашому місті» — блок для статей і сценаріїв про комуналку.
   Дані: local/services.json (будує _build/local_section.py). Показує лише сервіси обраного міста,
   де підтверджена потрібна дія (data-act: pay | readings | debt; порожньо — усі). Платіжні сервіси — окремо й з позначкою.
   Розмітка: <section class="local-pick" data-act="readings" data-base="../../" [data-city="Кривий Ріг"]></section> */
(function () {
  var cache = null, KEY = 'yak-local-city';
  var ACT_Q = { pay: 'оплатити комунальні послуги', readings: 'передати показники', debt: 'перевірити борг і нарахування' };
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function load(base) { return cache || (cache = fetch(base + 'local/services.json').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })); }
  function getCity() { try { return localStorage.getItem(KEY) || ''; } catch (e) { return ''; } }
  function setCity(v) { try { if (v) localStorage.setItem(KEY, v); } catch (e) {} }
  function d(iso) { var p = iso.split('-'); return p[2] + '.' + p[1] + '.' + p[0]; }

  function why(s, pid, city) {
    if (s.all) return 'Стосується вас, якщо у квитанції за розподіл газу вказано «Газмережі».';
    if (s.t === 'payment') return 'Приймає оплату в місті ' + city + '. Це комерційний платіжний сервіс, а не система міста.';
    var sc = s.sc && s.sc[pid] ? ' Увага: ' + s.sc[pid] + '.' : '';
    if (s.t === 'unified') return 'Працює в місті ' + city + ': один кабінет для кількох послуг; які саме постачальники підключені, видно в кабінеті.' + sc;
    return 'Працює в місті ' + city + ': ' + s.ul.toLowerCase() + '.' + sc;
  }

  function card(s, pid, city, act, acts, checked) {
    var st = s.st === 'verified' ? '<span class="lst lst-ok">Перевірено</span>' : '<span class="lst lst-part">Частково перевірено</span>';
    var own = s.t === 'payment' ? 'Не є системою міста' : s.own;
    var yes = s.yes.map(function (k) { return '<li' + (k === act ? ' class="hit"' : '') + '>' + esc(acts[k]) + '</li>'; }).join('');
    return '<li class="lmini lc-' + s.t + '"><div class="lcard-top">' + st + '<span class="kind lk-' + s.t + '">' + esc(s.tl) + '</span>' + (own ? '<span class="lown">' + esc(own) + '</span>' : '') + '</div>' +
      '<h3>' + esc(s.n) + '</h3><p class="lwhy"><b>Чому ви це бачите:</b> ' + esc(why(s, pid, city)) + '</p>' +
      (yes ? '<ul class="lacts">' + yes + '</ul>' : '') +
      (s.unk.length ? '<p class="lunk">Не підтвердили: ' + esc(s.unk.join(', ')) + '.</p>' : '') +
      (s.lim ? '<p class="llim"><b>Важливо:</b> ' + esc(s.lim) + '</p>' : '') +
      '<p class="lmini-foot"><a class="btn ' + (s.t === 'payment' ? 'ghost' : 'primary') + ' sm-btn" href="' + esc(s.u) + '" target="_blank" rel="noopener noreferrer">Перейти на сайт <span class="sr-only">(відкриється в новій вкладці)</span></a>' +
      '<small>Джерело: ' + esc(s.src) + ' · перевірено ' + d(checked) + '</small></p></li>';
  }

  function draw(el, data) {
    var act = el.dataset.act || '', base = el.dataset.base || '', pid = el.querySelector('select').value, out = el.querySelector('.lp-out');
    if (!pid) { out.innerHTML = ''; el.hidden = !!el.dataset.quiet; return; }
    setCity(pid);
    var city = data.places[pid];
    var list = data.s.filter(function (s) { return s.p.indexOf(pid) > -1 && (!act || s.yes.indexOf(act) > -1); });
    var main = list.filter(function (s) { return s.t !== 'payment' && !s.all; }), nat = list.filter(function (s) { return s.all; }), pay = list.filter(function (s) { return s.t === 'payment'; });
    var all = '<a href="' + base + 'local/?city=' + pid + '">Усі місцеві сервіси міста ' + esc(city) + ' →</a>';
    var h = '';
    if (!main.length && el.dataset.quiet) { el.hidden = true; out.innerHTML = ''; return; }
    el.hidden = false;
    if (!main.length) h += '<p class="empty-note">Для міста ' + esc(city) + ' ми поки не підтвердили місцевий сервіс, де можна ' + (ACT_Q[act] || 'оплатити чи перевірити комунальні послуги') + '. Назву постачальника шукайте у квитанції.</p>';
    var cards = main.concat(nat).map(function (s) { return card(s, pid, city, act, data.acts, data.checked); }).join('');
    if (cards) h += '<ul class="lminis">' + cards + '</ul>';
    if (pay.length) h += '<p class="lpay-note">Комерційні платіжні сервіси — не системи міста, вони лише приймають оплату:</p><ul class="lminis">' + pay.map(function (s) { return card(s, pid, city, act, data.acts, data.checked); }).join('') + '</ul>';
    out.innerHTML = h + '<p class="lp-all">' + all + '</p>';
    el.dispatchEvent(new CustomEvent('yaklocal:drawn', { bubbles: true, detail: { names: main.concat(nat, pay).map(function (s) { return s.n; }) } }));
  }

  function nameToId(data, name) { for (var k in data.places) if (data.places[k] === name) return k; return ''; }

  function mount(el) {
    if (el.dataset.ready) return; el.dataset.ready = '1';
    var base = el.dataset.base || '', id = 'lp' + Math.random().toString(36).slice(2, 7);
    var fixed = !!el.dataset.fixed;
    if (el.dataset.quiet) el.hidden = true;
    el.innerHTML = '<h2 class="lp-h">' + (fixed ? 'Місцевий сервіс у місті ' + esc(el.dataset.city) : 'Місцевий сервіс у вашому місті') + '</h2>' +
      '<p class="lp-lead">' + (fixed ? 'Сайт саме вашого міста: там видно нарахування місцевих постачальників. Загальні способи оплати — нижче.' : 'У деяких містах є свій сайт, де можна ' + (ACT_Q[el.dataset.act] || 'оплатити комуналку, передати показники чи перевірити борг') + '. Оберіть місто — покажемо лише перевірені сервіси.') + '</p>' +
      '<label class="flabel' + (fixed ? ' sr-only' : '') + '" for="' + id + '">Ваше місто</label><select id="' + id + '" class="lsel"' + (fixed ? ' hidden' : '') + '><option value="">Оберіть місто</option></select>' +
      '<div class="lp-out" aria-live="polite"></div>' +
      '<p class="lp-all lp-nojs"><a href="' + base + 'local/">Усі місцеві сервіси →</a></p>';
    load(base).then(function (data) {
      if (!data) return;
      var sel = el.querySelector('select');
      sel.innerHTML += Object.keys(data.places).map(function (k) { return '<option value="' + k + '">' + esc(data.places[k]) + '</option>'; }).join('');
      var pre = nameToId(data, el.dataset.city || '') || (fixed ? '' : getCity());
      if (pre && data.places[pre]) sel.value = pre;
      el.querySelector('.lp-nojs').hidden = true;
      sel.addEventListener('change', function () { draw(el, data); });
      draw(el, data);
    });
  }

  window.YakLocal = { mount: function (el) { if (el) mount(el); } };
  function auto() { [].forEach.call(document.querySelectorAll('.local-pick'), mount); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', auto); else auto();
})();

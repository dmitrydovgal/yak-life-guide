/* «Як?» — рушій покрокових сценаріїв послуг.
   Дані сценарію лежать у <script type="application/json" id="journey-data"> (генерує _build/journey.py).
   Без залежностей. Прогрес і відповіді зберігаються лише в цьому браузері (localStorage). */
(function () {
  'use strict';
  var dataEl = document.getElementById('journey-data');
  var root = document.getElementById('journey');
  if (!dataEl || !root) return;
  var J;
  try { J = JSON.parse(dataEl.textContent); } catch (e) { return; }

  var KEY = 'yak_j_' + J.id;
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* ignore */ } }
  };
  var S = store.get(KEY, null) || { ans: {}, docs: {}, na: {}, city: '' };
  S.ans = S.ans || {}; S.docs = S.docs || {}; S.na = S.na || {};
  if (!S.city) { var k = store.get('yak_kom', {}); if (k && k.city) S.city = k.city; }
  var save = function () { S.t = Date.now(); store.set(KEY, S); };

  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var byId = function (arr, id) { for (var i = 0; i < arr.length; i++) if (arr[i].id === id) return arr[i]; return null; };
  var host = function (u) { try { return new URL(u).host; } catch (e) { return u; } };
  var plural = function (n, a, b, c) { var n10 = n % 10, n100 = n % 100; return n10 === 1 && n100 !== 11 ? a : (n10 >= 2 && n10 <= 4 && !(n100 >= 12 && n100 <= 14) ? b : c); };

  var editing = null;
  document.documentElement.classList.add('j-on');
  if (J.type === 'fop-groups') { fopEngine(); return; }
  ['variants', 'channels', 'roles', 'docs', 'products', 'receive', 'refusal', 'appeal', 'next', 'providers'].forEach(function (k) { J[k] = J[k] || []; });
  J.steps = J.steps || {};
  var SAVE_ID = J.type === 'ed-page' ? J.id : 's:' + J.id;

  /* --- Профіль заявника: спільний для всіх послуг (не питаємо повторно) --- */
  var PROF_KEY = 'yak_profile';
  J.ed = J.ed || null;
  J.questions = (J.questions || []).concat(J.ed && J.ed.questions ? J.ed.questions.map(function (q) { q.ed = true; return q; }) : []);
  if (!S.ans.profile && J.questions.some(function (q) { return q.id === 'profile'; })) { var gp = store.get(PROF_KEY, ''); if (gp) S.ans.profile = gp; }

  /* --- Обчислення стану --- */
  function variant() {
    if (J.variants.length === 1) return J.variants[0];
    var m = J.varByCh || {};
    if (m.online) { var c = channel(); if (c) return byId(J.variants, c.id === 'online' || c.id === 'app' ? m.online : m.offline); return null; }
    return byId(J.variants, S.ans.variant);
  }
  function channel() {
    var cm = J.ed && J.ed.channelMap;
    if (cm) { for (var q in cm) { if (S.ans[q] && cm[q][S.ans[q]]) { var c = byId(J.channels, cm[q][S.ans[q]]); if (c) return c; } } }
    return J.channels.length === 1 ? J.channels[0] : byId(J.channels, S.ans.channel);
  }
  function stopped() { return !!(J.ed && J.ed.blocks && J.ed.blocks.some(function (b) { return b.kind === 'stop' && blockOn(b); })); }
  function role() { return J.roles.length <= 1 ? (J.roles[0] ? J.roles[0].id : 'self') : (S.ans.role || 'self'); }
  function pending() { return J.questions.filter(function (q) { return !S.ans[q.id]; }); }
  function eligible() {
    var p = S.ans.profile, al = J.profile && J.profile.allowed || [];
    if (!p || !al.length || al.indexOf(p) > -1) return true;
    return p === 'fop' && al.indexOf('person') > -1;   /* ФОП — теж фізична особа */
  }
  function docsFor() {
    var r = role(), rep = r === 'rep' || r === 'legal', hasRoleQ = J.questions.some(function (q) { return q.id === 'role'; });
    var prof = S.ans.profile, shown = [], hidden = 0, al = (J.profile && J.profile.allowed) || [];
    (J.ed && J.ed.docsReplace ? [] : J.docs).forEach(function (d, i) {
      var skip = (d.rep && !rep && hasRoleQ && !d.cond) ||
        (d.who === 'legal' && prof && prof !== 'legal' && al.indexOf('legal') > -1) ||
        (d.who === 'person' && prof && prof !== 'person' && prof !== 'fop' && (al.indexOf('person') > -1 || al.indexOf('fop') > -1));
      if (skip) hidden++; else shown.push({ d: d, i: i });
    });
    return { list: shown.concat(edDocs()), hidden: hidden };
  }
  function progress() {
    var q = J.questions.length, qa = q - pending().length;
    var dl = docsFor().list, need = dl.filter(function (x) { return !S.na[x.i]; }), ready = need.filter(function (x) { return S.docs[x.i]; }).length;
    var total = q + need.length, done = qa + ready;
    return { total: total, done: done, pct: total ? Math.round(done * 100 / total) : 100, ready: ready, need: need.length };
  }
  function blockOn(b) { var c = b['if'] || {}; return Object.keys(c).every(function (k) { var v = c[k]; return Array.isArray(v) ? v.indexOf(S.ans[k]) > -1 : S.ans[k] === v; }); }
  function edDocs() { var out = []; if (!J.ed || !J.ed.blocks) return out; J.ed.blocks.forEach(function (b, bi) { if (b.kind === 'docs' && blockOn(b)) b.items.forEach(function (t, k) { out.push({ d: { t: t, why: b.why || '', cond: '' }, i: 'e' + bi + '_' + k }); }); }); return out; }

  /* --- Рендер --- */
  function qHtml(q) {
    var tip = '';
    if (q.id === 'variant' && J.decide === 'speed') {
      var fast = J.variants.filter(function (v) { return (v.tags || []).indexOf('найшвидше') > -1; })[0];
      var cheap = J.variants.filter(function (v) { return (v.tags || []).indexOf('найдешевше') > -1; })[0];
      if (fast && cheap && fast.id !== cheap.id) tip = '<p class="j-tip">Порада: якщо результат не терміновий, оберіть «' + esc(cheap.label) + '» (' + esc(cheap.cost) + '). Якщо потрібно швидше — «' + esc(fast.label) + '» (' + esc(fast.time) + ').</p>';
    }
    var chosen = S.ans[q.id] && byId(q.options, S.ans[q.id]);
    if (chosen && editing !== q.id) {
      return '<div class="j-ans"><span class="muted">' + esc(q.title) + '</span><b>' + esc(chosen.label) + '</b><button type="button" class="j-edit" data-edit="' + q.id + '">Змінити</button></div>';
    }
    return '<fieldset class="grp j-q" data-q="' + q.id + '"><legend>' + esc(q.title) + '</legend><p class="muted j-why">' + esc(q.why) + '</p>' + tip +
      '<div class="opts">' + q.options.map(function (o) {
        var tags = (o.tags || []).map(function (t) { return '<span class="chip j-tag">' + esc(t) + '</span>'; }).join('');
        var pc = (o.pros ? '<small class="j-pro">+ ' + esc(o.pros) + '</small>' : '') + (o.cons ? '<small class="j-con">− ' + esc(o.cons) + '</small>' : '');
        return '<label class="opt"><input type="radio" name="q-' + q.id + '" value="' + esc(o.id) + '"' + (S.ans[q.id] === o.id ? ' checked' : '') + '><span><b>' + esc(o.label) + tags + '</b>' + (o.hint ? '<small>' + esc(o.hint) + '</small>' : '') + pc + '</span></label>';
      }).join('') + '</div></fieldset>';
  }

  function fitHtml() {
    var out = '';
    if (S.ans.profile && !eligible()) {
      var al = J.profile.allowed.map(function (a) { return J.profile.labels[a]; }).join(', ');
      out += '<section class="j-sec j-warn"><h3>Ця послуга, ймовірно, не для вас</h3><p>Її можуть отримати: ' + esc(al) + '. Якщо ви звертаєтеся від імені іншої особи чи організації — змініть відповідь вище.</p>' +
        (J.next && J.next.length ? '<p>Подивіться пов’язані послуги:</p><ul>' + J.next.slice(0, 4).map(function (n) { return '<li><a href="' + esc(n.u) + '">' + esc(n.t) + '</a></li>'; }).join('') + '</ul>' : '') + '</section>';
    }
    if (J.ed && (J.ed.fit || J.ed.notFit)) {
      out += '<details class="j-more j-fit"><summary>Кому підходить і коли — ні</summary>' +
        (J.ed.fit ? '<ul>' + J.ed.fit.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '') +
        (J.ed.notFit ? '<p class="muted">Особливості:</p><ul>' + J.ed.notFit.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '') + '</details>';
    }
    return out;
  }

  function recHtml() {
    var v = variant(), c = channel(), out = [];
    var ro = byId(J.roles, role());
    if (ro && J.questions.some(function (q) { return q.id === 'role'; })) out.push('<li><b>Хто подає:</b> ' + esc(ro.label.toLowerCase()) + '.</li>');
    if (v && J.variants.length > 1) {
      var why = (v.tags || []).length ? ' Це ' + v.tags.join(' і ') + ' з доступних варіантів.' : '';
      out.push('<li><b>Варіант:</b> ' + esc(v.label) + (v.time ? '. Строк: ' + esc(v.time) : '') + (v.cost ? '. Вартість: ' + esc(v.cost) : '') + '.' + why + '</li>');
    }
    if (c && J.channels.length > 1) out.push('<li><b>Спосіб подачі:</b> ' + esc(c.label.toLowerCase()) + '. ' + esc(c.desc) + '</li>');
    var blocks = J.ed && J.ed.blocks ? J.ed.blocks.filter(function (b) { return b.kind !== 'docs' && blockOn(b); }) : [];
    var bl = blocks.map(function (b) {
      return '<div class="j-block' + (b.kind === 'warn' || b.kind === 'stop' ? ' j-bwarn' : b.kind === 'rec' ? ' j-brec' : '') + '"><b>' + esc(b.t) + '</b><ul>' + b.items.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' +
        (b.link ? '<a class="btn ghost sm-btn" href="' + esc(b.link[1]) + '">' + esc(b.link[0]) + '</a>' : '') + '</div>';
    }).join('');
    if (!out.length && !bl) return '';
    return '<section class="j-sec"><h3>Ваша ситуація</h3>' + (out.length ? '<ul class="j-rec">' + out.join('') + '</ul>' : '') + bl +
      (out.length ? '<p class="muted">Ґрунтується на даних реєстру' + (J.ed ? ' та офіційної сторінки послуги' : '') + '. Перед подачею звірте умови в офіційному джерелі.</p>' : '') + '</section>';
  }

  function docsHtml() {
    if (J.ed && J.ed.docsReplace && !edDocs().length) return '';
    if ((!J.docs.length || (J.ed && J.ed.docsReplace)) && !edDocs().length) return J.channels.length ? '<section class="j-sec"><h3>Документи</h3><p>Перелік документів у реєстрі не наведено. Уточніть його в органі перед зверненням.</p></section>' : '';
    var f = docsFor(), p = progress();
    return '<section class="j-sec" id="j-docs"><h3>Підготуйте документи <span class="muted">' + p.ready + ' з ' + p.need + '</span></h3>' +
      '<ul class="j-docs">' + f.list.map(function (x) {
        var d = x.d, na = !!S.na[x.i];
        return '<li class="' + (na ? 'na' : '') + '"><label><input type="checkbox" data-doc="' + x.i + '"' + (S.docs[x.i] ? ' checked' : '') + (na ? ' disabled' : '') + '><span>' + esc(d.t) +
          (d.why ? '<small>Навіщо: ' + esc(d.why) + '</small>' : '') + (d.form ? '<small>Форма: ' + esc(d.form) + '</small>' : '') +
          (d.cond ? '<small>Лише якщо: ' + esc(d.cond) + '</small>' : '') + (d.rep && !d.cond ? '<small>Для представника</small>' : '') + '</span></label>' +
          (d.cond ? '<button type="button" class="j-na" data-na="' + x.i + '">' + (na ? 'Стосується мене' : 'Мене не стосується') + '</button>' : '') + '</li>';
      }).join('') + '</ul>' +
      (f.hidden ? '<p class="muted">Приховано ' + f.hidden + ' ' + plural(f.hidden, 'документ', 'документи', 'документів') + ', які не стосуються вашої ситуації.</p>' : '') + '</section>';
  }

  function stepsHtml() {
    var c = channel();
    var ed = J.ed && J.ed.online;
    if (!c && !ed) return '';
    var st, v = variant();
    if (ed && (!c || c.id === 'online')) {
      var url = (c && c.url) || (J.type === 'ed-page' && J.ed.sources && J.ed.sources[0] ? J.ed.sources[0][1] : '');
      st = ed.map(function (s, i) { return [s, '', i === 0 && url ? url : '']; });
    } else st = (J.steps[c.id] || []).slice();
    if (v && v.cost && v.cost !== 'Безоплатно' && !(ed && (!c || c.id === 'online'))) st.push(['Сплатіть послугу', 'Вартість: ' + v.cost + '.', '']);
    if (v && v.time) st.push(['Дочекайтеся рішення', 'Строк: ' + v.time + '.', '']);
    var extra = '';
    if (c && c.id === 'office') {
      var q = (J.providers[0] || 'ЦНАП') + (S.city ? ' ' + S.city : '');
      extra = '<div class="j-city"><label for="j-city">Ваше місто (для пошуку на карті)</label><div class="j-city-row"><input id="j-city" type="text" value="' + esc(S.city) + '" placeholder="Наприклад, Київ" autocomplete="address-level2">' +
        '<a class="btn ghost sm-btn" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(q) + '">Знайти на карті</a>' +
        (J.cnap ? '<a class="btn ghost sm-btn" target="_blank" rel="noopener noreferrer" href="https://guide.diia.gov.ua/asc/">Реєстр ЦНАП</a>' : '') + '</div></div>';
    }
    var title = ed && (!c || c.id === 'online') ? 'Що зробити на офіційному сайті' : 'Подайте заяву: ' + c.label.toLowerCase();
    return '<section class="j-sec"><h3>' + esc(title) + '</h3><ol class="osteps">' + st.map(function (s, i) {
      return '<li class="ostep"><span class="num">' + (i + 1) + '</span><div class="body"><b>' + esc(s[0]) + '</b>' + (s[1] ? '<span>' + esc(s[1]) + '</span>' : '') +
        (s[2] ? '<div class="oact"><a class="btn ' + (i === 0 ? 'primary' : 'ghost') + ' sm-btn" href="' + esc(s[2]) + '" target="_blank" rel="noopener noreferrer">Відкрити ' + esc(host(s[2])) + '</a></div>' : '') + '</div></li>';
    }).join('') + '</ol>' + extra + '</section>';
  }

  function resultHtml() {
    var v = variant(), bits = [];
    if (J.products.length) bits.push('<li><b>Що ви отримаєте:</b> ' + esc(J.products.join('; ')) + '.</li>');
    if (v && v.time) bits.push('<li><b>Строк:</b> ' + esc(v.time) + '.</li>');
    if (J.receive.length) bits.push('<li><b>Як отримати:</b> ' + esc(J.receive.join(', ')) + '.</li>');
    var after = J.ed && J.ed.after ? '<p class="j-sub">Після подачі</p><ul class="j-rec">' + J.ed.after.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '';
    var ref = '';
    if ((J.refusal || []).length || (J.appeal || []).length || J.court) {
      ref = '<details class="j-more"><summary>Якщо відмовили</summary>' + (J.refusal.length ? '<ul>' + J.refusal.slice(0, 6).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '') +
        (J.appeal.length ? '<p>Оскаржити рішення можна: ' + esc(J.appeal.join('; ')) + '.</p>' : '') + (J.court ? '<p>Рішення можна оскаржити в суді.</p>' : '') + '</details>';
    }
    var nx = J.next && J.next.length ? '<p class="j-sub">Що далі</p><ul class="j-rec">' + J.next.slice(0, 4).map(function (n) { return '<li><a href="' + esc(n.u) + '">' + esc(n.t) + '</a></li>'; }).join('') + '</ul>' : '';
    var src = J.ed ? '<p class="muted j-src">Інструкцію перевірено ' + esc(J.ed.verified.split('-').reverse().join('.')) + ': ' + J.ed.sources.map(function (s) { return '<a href="' + esc(s[1]) + '" target="_blank" rel="noopener noreferrer">' + esc(s[0]) + '</a>'; }).join('; ') + '.</p>' : '';
    return bits.length || ref || after || nx ? '<section class="j-sec"><h3>Результат і що далі</h3>' + (bits.length ? '<ul class="j-rec">' + bits.join('') + '</ul>' : '') + after + ref + nx + src + '</section>' : '';
  }

  function summaryText() {
    var v = variant(), c = channel(), ro = byId(J.roles, role());
    var lines = [(J.type === 'ed-page' ? 'Інструкція: ' : 'Послуга: ') + J.name];
    J.questions.forEach(function (q) { var o = S.ans[q.id] && byId(q.options, S.ans[q.id]); if (o && q.id !== 'variant' && q.id !== 'channel') lines.push(q.title + ' ' + o.label); });
    if (v) { if (J.variants.length > 1) lines.push('Варіант: ' + v.label); if (v.time) lines.push('Строк: ' + v.time); if (v.cost) lines.push('Вартість: ' + v.cost); }
    if (c) lines.push('Спосіб подачі: ' + c.label + (c.url ? ' (' + c.url + ')' : ''));
    var f = docsFor().list.filter(function (x) { return !S.na[x.i]; });
    if (f.length) lines.push('Документи:\n' + f.map(function (x) { return (S.docs[x.i] ? '[x] ' : '[ ] ') + x.d.t; }).join('\n'));
    if (J.ed) J.ed.blocks && J.ed.blocks.filter(blockOn).forEach(function (b) { lines.push(b.t + ':\n- ' + b.items.join('\n- ')); });
    lines.push('Джерело: ' + (J.guide || (J.ed && J.ed.sources[0][1]) || location.href));
    return lines.join('\n');
  }

  function render() {
    var p = progress(), pend = pending();
    var saved = (store.get('yak_saved', []) || []).indexOf(SAVE_ID) > -1;
    var nq = J.questions.length;
    var head = '<div class="j-head"><div><b>Ваш покроковий план</b><span class="muted">' + (nq ? 'Дайте відповідь на ' + nq + ' ' + plural(nq, 'питання', 'питання', 'питань') + ' — і план підлаштується під вас.' : 'Відмічайте готові документи — прогрес збережеться в цьому браузері.') + '</span></div>' +
      '<div class="j-bar" role="progressbar" aria-valuenow="' + p.pct + '" aria-valuemin="0" aria-valuemax="100" aria-label="Готовність"><i style="width:' + p.pct + '%"></i></div><span class="j-pct">' + p.pct + '%</span></div>';
    var html = head + fitHtml() + J.questions.map(qHtml).join('');
    if (!pend.length && eligible()) html += recHtml() + (stopped() ? '' : docsHtml() + stepsHtml() + resultHtml());
    else if (pend.length) html += '<p class="muted j-wait">Після відповіді' + (pend.length > 1 ? ' на всі питання' : '') + ' покажемо ваш план: документи, кроки й результат.</p>';
    html += '<div class="j-actions"><button type="button" class="btn ghost" data-act="save">' + (saved ? 'Збережено ✓' : 'Зберегти план') + '</button>' +
      (!pend.length ? '<button type="button" class="btn ghost" data-act="copy">Копіювати план</button><button type="button" class="btn ghost" data-act="print">Друкувати</button>' : '') +
      (Object.keys(S.ans).length || Object.keys(S.docs).length ? '<button type="button" class="btn ghost" data-act="reset">Почати спочатку</button>' : '') +
      (document.getElementById('j-ref') ? '<button type="button" class="btn ghost" data-act="ref">Повна довідка</button>' : '') + '</div>';
    root.innerHTML = html;
  }

  function toast(t) {
    var el = document.createElement('div'); el.className = 'toast show'; el.setAttribute('role', 'status'); el.textContent = t;
    document.body.appendChild(el); setTimeout(function () { el.remove(); }, 2200);
  }

  root.addEventListener('change', function (ev) {
    var t = ev.target;
    if (t.name && t.name.indexOf('q-') === 0) { var qid = t.name.slice(2); S.ans[qid] = t.value; if (qid === 'profile') store.set(PROF_KEY, t.value); editing = null; save(); render(); return; }
    if (t.dataset && t.dataset.doc) { S.docs[t.dataset.doc] = t.checked; save(); render(); return; }
    if (t.id === 'j-city') { S.city = t.value.trim(); save(); render(); }
  });
  root.addEventListener('click', function (ev) {
    var b = ev.target.closest('button'); if (!b) return;
    if (b.dataset.edit) { editing = b.dataset.edit; render(); var f = root.querySelector('[data-q="' + editing + '"] input'); if (f) f.focus(); return; }
    if (b.dataset.na) { var i = b.dataset.na; S.na[i] = !S.na[i]; if (S.na[i]) delete S.docs[i]; save(); render(); return; }
    var a = b.dataset.act;
    if (a === 'save') {
      var s = store.get('yak_saved', []) || [], id = SAVE_ID, k = s.indexOf(id);
      if (k > -1) { s.splice(k, 1); toast('План видалено зі збереженого'); } else { s.push(id); toast('План збережено. Він у розділі «Збережене»'); }
      store.set('yak_saved', s); save(); render();
    } else if (a === 'copy') {
      var txt = summaryText();
      if (navigator.clipboard) navigator.clipboard.writeText(txt).then(function () { toast('План скопійовано'); }, function () { toast('Не вдалося скопіювати'); });
    } else if (a === 'print') { window.print(); }
    else if (a === 'reset') { S = { ans: {}, docs: {}, na: {}, city: S.city }; save(); render(); }
    else if (a === 'ref') { document.documentElement.classList.toggle('j-show-ref'); var r = document.getElementById('j-ref'); if (r && document.documentElement.classList.contains('j-show-ref')) r.scrollIntoView({ behavior: 'smooth' }); }
  });

  render();

  /* ===================== Сценарій «Група ФОП»: анкета + калькулятор ===================== */
  function fopEngine() {
    var A = S.ans;
    var fmt = function (x) { return (Math.round(x * 100) / 100).toLocaleString('uk-UA', { minimumFractionDigits: 0, maximumFractionDigits: 2 }) + ' грн'; };
    var G = {}; J.groups.forEach(function (g) { G[g.id] = g; });

    function eligibility() {
      var inc = parseFloat(A.income), act = A.act, st = A.staff, res = {};
      J.groups.forEach(function (g) {
        var why = [];
        if (act === 'excluded') why.push('ця діяльність не дозволена для спрощеної системи');
        if (g.id === 'g1') {
          if (act && act !== 'market') why.push('лише продаж на ринку або побутові послуги населенню');
          if (st && st !== '0') why.push('без найманих працівників');
        }
        if (g.id === 'g2') {
          if (act === 'business') why.push('послуги — лише населенню або платникам єдиного податку');
          if (act === 'only3') why.push('ваш вид діяльності дозволений лише в 3 групі');
          if (st === '11') why.push('не більше 10 найманих працівників');
        }
        if (!isNaN(inc) && inc > g.limit) why.push('дохід перевищує ліміт ' + fmt(g.limit));
        res[g.id] = why;
      });
      return res;
    }
    function cost(g, inc) {
      var esvY = J.esv * 12;
      if (g.id === 'g3') {
        var rate = A.vat === 'yes' ? g.rateVat : g.rate;
        var tax = inc * rate, mil = inc * g.milRate;
        return { tax: tax, mil: mil, esv: esvY, total: tax + mil + esvY, note: (A.vat === 'yes' ? '3%' : '5%') + ' доходу + 1% військовий збір' };
      }
      return { tax: g.taxMonthly * 12, mil: g.milMonthly * 12, esv: esvY, total: (g.taxMonthly + g.milMonthly) * 12 + esvY, note: 'фіксовані платежі (максимальні ставки)' };
    }
    function qBlock(q, el) {
      var ans = A[q.id];
      if (q.type === 'number') {
        return '<fieldset class="grp j-q"><legend>' + esc(q.title) + '</legend><p class="muted j-why">' + esc(q.why) + '</p>' +
          '<div class="j-city-row"><input id="f-income" type="number" inputmode="numeric" min="0" step="1000" placeholder="Наприклад, 600000" value="' + esc(ans || '') + '" aria-label="Очікуваний дохід за рік, грн"><span class="muted" style="align-self:center">грн на рік</span></div></fieldset>';
      }
      var chosen = ans && byId(q.options, ans);
      if (chosen && editing !== q.id) return '<div class="j-ans"><span class="muted">' + esc(q.title) + '</span><b>' + esc(chosen.label) + '</b><button type="button" class="j-edit" data-edit="' + q.id + '">Змінити</button></div>';
      return '<fieldset class="grp j-q" data-q="' + q.id + '"><legend>' + esc(q.title) + '</legend><p class="muted j-why">' + esc(q.why) + '</p><div class="opts">' +
        q.options.map(function (o) { return '<label class="opt"><input type="radio" name="q-' + q.id + '" value="' + o.id + '"' + (ans === o.id ? ' checked' : '') + '><span><b>' + esc(o.label) + '</b>' + (o.hint ? '<small>' + esc(o.hint) + '</small>' : '') + '</span></label>'; }).join('') + '</div></fieldset>';
    }
    function draw() {
      var el = eligibility(), inc = parseFloat(A.income), ready = A.act && A.staff && !isNaN(inc) && inc >= 0;
      var g3ok = !el.g3.length;
      var qs = J.questions.filter(function (q) { return !q.onlyIf || (ready && g3ok); });
      var answered = qs.filter(function (q) { return A[q.id] !== undefined && A[q.id] !== ''; }).length;
      var pct = Math.round(answered * 100 / qs.length);
      var html = '<div class="j-head"><div><b>Підберемо групу за 4 питання</b><span class="muted">Порахуємо обов’язкові платежі за рік і покажемо, що робити далі.</span></div>' +
        '<div class="j-bar" role="progressbar" aria-valuenow="' + pct + '" aria-valuemin="0" aria-valuemax="100" aria-label="Готовність"><i style="width:' + pct + '%"></i></div><span class="j-pct">' + pct + '%</span></div>';
      html += qs.map(function (q) { return qBlock(q, el); }).join('');
      if (ready) {
        var elig = J.groups.filter(function (g) { return !el[g.id].length; });
        if (!elig.length) {
          html += '<section class="j-sec"><h3>Спрощена система вам, імовірно, недоступна</h3><ul class="j-rec">' +
            J.groups.map(function (g) { return '<li><b>' + g.name + ':</b> ' + esc(el[g.id].join('; ')) + '.</li>'; }).join('') +
            '</ul><p>За таких умов діє загальна система оподаткування. Порадьтеся з податковим фахівцем або зверніться до ДПС.</p></section>';
        } else {
          var rows = elig.map(function (g) { var c = cost(g, inc); return { g: g, c: c }; }).sort(function (a, b) { return a.c.total - b.c.total; });
          var best = rows[0];
          html += '<section class="j-sec"><h3>Рекомендація: ' + esc(best.g.name) + '</h3><p>' +
            (rows.length > 1 ? 'Серед доступних вам груп тут найменші обов’язкові платежі за рік при доході ' + fmt(inc) + ' — орієнтовно <b>' + fmt(best.c.total) + '</b>.' :
              'Це єдина група, яка вам доступна. Обов’язкові платежі за рік при доході ' + fmt(inc) + ' — орієнтовно <b>' + fmt(best.c.total) + '</b>.') + '</p>' +
            '<div class="cmp-wrap"><table class="cmp"><thead><tr><th>Група</th><th>Єдиний податок</th><th>Військовий збір</th><th>ЄСВ</th><th>Разом за рік</th></tr></thead><tbody>' +
            rows.map(function (r) { return '<tr' + (r === best ? ' class="best"' : '') + '><td>' + r.g.name + '</td><td>' + fmt(r.c.tax) + '</td><td>' + fmt(r.c.mil) + '</td><td>' + fmt(r.c.esv) + '</td><td><b>' + fmt(r.c.total) + '</b></td></tr>'; }).join('') +
            '</tbody></table></div>' +
            (J.groups.some(function (g) { return el[g.id].length; }) ? '<p class="muted">Недоступні вам: ' + J.groups.filter(function (g) { return el[g.id].length; }).map(function (g) { return g.name + ' — ' + el[g.id].join('; '); }).map(esc).join('. ') + '.</p>' : '') +
            '<details class="j-more" open><summary>Від чого залежить рекомендація</summary><ul>' +
            '<li>Ставки єдиного податку 1 і 2 груп у розрахунку — максимальні. Ваша громада може встановити нижчі.</li>' +
            '<li>ЄСВ враховано в мінімальному розмірі — ' + fmt(J.esv) + ' на місяць.</li>' +
            '<li>Дохід понад ліміт групи оподатковується за ставкою 15%. Якщо дохід може вирости, залиште запас до ліміту.</li>' +
            (best.g.id === 'g3' ? '<li>Для 3 групи платежі залежать від фактичного доходу: що більший дохід, то більші податок і військовий збір.</li>' : '') +
            '</ul></details></section>';
          html += '<section class="j-sec"><h3>Що робити далі</h3><ol class="osteps">' +
            '<li class="ostep"><span class="num">1</span><div class="body"><b>Зареєструйте ФОП і оберіть ' + esc(best.g.name.replace('група', 'групу')) + '</b><span>Як зареєструвати ФОП і подати заяву про спрощену систему — у покроковій інструкції.</span><div class="oact"><a class="btn primary sm-btn" href="../fop-open/">Інструкція: як відкрити ФОП</a></div></div></li>' +
            '<li class="ostep"><span class="num">2</span><div class="body"><b>Сплачуйте податки вчасно</b><span>' + esc(best.g.pay) + ' Військовий збір: ' + esc(best.g.mil) + ' ЄСВ — щонайменше ' + fmt(J.esv) + ' на місяць.</span></div></li>' +
            '<li class="ostep"><span class="num">3</span><div class="body"><b>Подавайте звітність</b><span>' + esc(best.g.report) + '</span></div></li>' +
            '<li class="ostep"><span class="num">4</span><div class="body"><b>Стежте за лімітом доходу</b><span>Ліміт доходу для ' + esc(best.g.name.replace('група', 'групи')) + ' на 2026 рік — ' + fmt(best.g.limit) + '.</span></div></li>' +
            '</ol></section>';
        }
      } else {
        html += '<p class="muted j-wait">Дайте відповіді на питання — і ми порахуємо платежі для кожної доступної групи.</p>';
      }
      html += '<div class="j-actions">' + (ready ? '<button type="button" class="btn ghost" data-act="print">Друкувати</button>' : '') +
        (Object.keys(A).length ? '<button type="button" class="btn ghost" data-act="reset">Почати спочатку</button>' : '') +
        '<button type="button" class="btn ghost" data-act="ref">Порівняльна таблиця груп</button></div>' +
        '<p class="muted" style="margin-top:12px;font-size:13px">Розрахунок орієнтовний. Дані перевірено ' + esc(J.verified.split('-').reverse().join('.')) + ' за Податковим кодексом і даними ДПС.</p>';
      root.innerHTML = html;
    }
    root.addEventListener('change', function (ev) {
      var t = ev.target;
      if (t.name && t.name.indexOf('q-') === 0) { A[t.name.slice(2)] = t.value; editing = null; save(); draw(); }
      if (t.id === 'f-income') { A.income = t.value; save(); draw(); var f = document.getElementById('f-income'); if (f) f.focus(); }
    });
    root.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return;
      if (b.dataset.edit) { editing = b.dataset.edit; draw(); return; }
      var a = b.dataset.act;
      if (a === 'print') window.print();
      else if (a === 'reset') { S.ans = A = {}; save(); draw(); }
      else if (a === 'ref') { document.documentElement.classList.toggle('j-show-ref'); var r = document.getElementById('j-ref'); if (r && document.documentElement.classList.contains('j-show-ref')) r.scrollIntoView({ behavior: 'smooth' }); }
    });
    draw();
  }
})();

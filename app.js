/* «Як?» — клієнтська логіка прототипу: роутер, пошук, збереження, сценарій комуналки */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const app = $('#app');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const ic = (n, cls = '') => `<i data-lucide="${n}" class="${cls}" aria-hidden="true"></i>`;
  const catById = id => CATS.find(c => c.id === id);

  /* ---------- Сховище ---------- */
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* ignore */ } }
  };
  const getSaved = () => store.get('yak_saved', []);
  const isSaved = id => getSaved().includes(id);
  function toggleSaved(id) {
    let s = getSaved();
    if (s.includes(id)) { s = s.filter(x => x !== id); toast('Інструкцію видалено зі збереженого'); }
    else { s.push(id); toast('Інструкцію збережено', 'ok'); }
    store.set('yak_saved', s);
    refreshSaveUI();
  }
  const getDone = key => store.get('yak_done_' + key, []);

  /* ---------- Toast ---------- */
  let toastTimer;
  function toast(msg, type) {
    const t = $('#toast');
    t.innerHTML = (type === 'ok' ? ic('circle-check') : ic('info')) + `<span>${esc(msg)}</span>`;
    t.className = 'toast show ' + (type || '');
    lucide.createIcons();
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 2600);
  }

  function refreshSaveUI() {
    $$('[data-save]').forEach(b => {
      const on = isSaved(b.dataset.save);
      b.classList.toggle('on', on);
      b.setAttribute('aria-pressed', on);
      b.innerHTML = ic(on ? 'bookmark-check' : 'bookmark') + `<span>${on ? 'Збережено' : 'Зберегти інструкцію'}</span>`;
    });
    $$('[data-save-mini]').forEach(b => {
      const on = isSaved(b.dataset.saveMini);
      b.classList.toggle('on', on);
      b.setAttribute('aria-label', on ? 'Видалити зі збереженого' : 'Зберегти');
      b.innerHTML = ic(on ? 'bookmark-check' : 'bookmark');
    });
    const n = getSaved().length;
    const badge = $('#savedCount');
    badge.textContent = n; badge.hidden = n === 0;
    lucide.createIcons();
  }

  /* ---------- Пошук ---------- */
  const STOP = ['як', 'що', 'де', 'чи', 'для', 'і', 'в', 'на', 'по', 'з', 'до', 'у', 'перед', 'після', 'мені'];
  const norm = s => String(s).toLowerCase().replace(/[ʼ'’`]/g, '').replace(/ё/g, 'е').replace(/ы/g, 'и').replace(/э/g, 'е').replace(/ъ/g, '').replace(/[?!.,«»"]/g, ' ');
  const stem = w => (w.length > 5 ? w.slice(0, w.length - 2) : w);
  const wm = (t, w) => { const a = stem(t), b = stem(w); return a.length >= 2 && b.length >= 2 && (b.startsWith(a) || a.startsWith(b)); };
  function search(q, cat) {
    let toks = norm(q).split(/\s+/).filter(Boolean);
    const filtered = toks.filter(t => !STOP.includes(t));
    if (filtered.length) toks = filtered;
    if (!toks.length) return [];
    const out = [];
    Object.values(INS).forEach(ins => {
      if (cat && !ins.cats.includes(cat)) return;
      const tw = norm(ins.title).split(/\s+/).filter(Boolean);
      const kw = norm(ins.kw + ' ' + ins.cats.map(c => catById(c).title).join(' ')).split(/\s+/).filter(Boolean);
      let score = 0;
      for (const t of toks) {
        if (tw.some(w => wm(t, w))) score += 3;
        else if (kw.some(w => wm(t, w))) score += 1;
        else return;
      }
      score += POPULAR.includes(ins.id) ? 0.5 : 0;
      out.push([score, ins]);
    });
    return out.sort((a, b) => b[1] === a[1] ? 0 : b[0] - a[0]).map(x => x[1]);
  }

  /* ---------- Спільні фрагменти ---------- */
  const crumbs = items => `<nav class="crumbs" aria-label="Навігація"><ol>${items.map((it, i) =>
    `<li>${it[1] ? `<a href="${it[1]}">${esc(it[0])}</a>` : `<span aria-current="page">${esc(it[0])}</span>`}${i < items.length - 1 ? ic('chevron-right', 'sep') : ''}</li>`).join('')}</ol></nav>`;
  const rowHtml = (href, title, meta, sid) => `<li class="row-wrap"><a class="row" href="${href}">
      <span class="row-main"><span class="row-title">${esc(title)}</span>
      <span class="row-meta">${meta}</span></span>${ic('chevron-right', 'chev')}</a>
      <button class="mini" data-save-mini="${sid}" type="button"></button></li>`;
  const insRow = ins => rowHtml('#/i/' + ins.id, ins.title, `${esc(catById(ins.cat).title)} · ${ic('clock', 'sm')} ${esc(ins.time)}`, ins.id);
  const insList = list => `<ul class="rows">${list.map(insRow).join('')}</ul>`;
  const svcRow = (sid, eid) => { const s = GUIDE_SERVICES[sid]; return rowHtml('#/s/' + sid + (eid ? '/' + eid : ''), s.n, `${esc(s.s)}${s.t ? ' · ' + ic('clock', 'sm') + ' ' + esc(s.t.split(';')[0].slice(0, 40)) : ''}`, 's:' + sid); };
  const svcList = (ids, eid) => `<ul class="rows">${ids.map(i => svcRow(i, eid)).join('')}</ul>`;

  /* Дані Гіду Дія (великий файл) завантажуються тільки за потреби */
  let guidePromise;
  const loadGuide = () => guidePromise || (guidePromise = typeof GUIDE_SERVICES !== 'undefined' ? Promise.resolve() : new Promise((res, rej) => {
    const sc = document.createElement('script'); sc.src = 'guide-data.js'; sc.onload = res; sc.onerror = () => { guidePromise = null; rej(new Error('load')); }; document.head.appendChild(sc);
  }));
  const loadingHtml = `<div class="container narrow-l"><div class="empty">${ic('loader')}<h3>Завантажуємо послуги…</h3></div></div>`;
  const loadErr = () => { app.innerHTML = `<div class="container narrow-m">${empty('Не вдалося завантажити дані', 'Перевірте з’єднання та спробуйте ще раз.', `<a class="btn primary" href="#/events">До життєвих подій</a>`)}</div>`; lucide.createIcons(); };
  const evById = id => GUIDE_EVENTS.find(e => e.id === id);
  const searchEvents = q => {
    const toks = norm(q).split(/\s+/).filter(t => t && !STOP.includes(t));
    if (!toks.length) return [];
    return GUIDE_EVENTS.filter(e => { const w = norm(e.title + ' ' + e.desc).split(/\s+/); return toks.every(t => w.some(x => wm(t, x))); });
  };
  let svcIdx;
  function searchServices(q) {
    const toks = norm(q).split(/\s+/).filter(t => t && !STOP.includes(t));
    if (!toks.length) return [];
    if (!svcIdx) svcIdx = Object.entries(GUIDE_SERVICES).map(([id, s]) => [id, norm(s.n).split(/\s+/), norm(s.f + ' ' + s.s + ' ' + s.p.join(' ')).split(/\s+/)]);
    const out = [];
    for (const [id, tw, fw] of svcIdx) {
      let sc = 0;
      for (const t of toks) { if (tw.some(w => wm(t, w))) sc += 3; else if (fw.some(w => wm(t, w))) sc += 1; else { sc = -1; break; } }
      if (sc > 0) out.push([sc, id]);
    }
    return out.sort((a, b) => b[0] - a[0]).map(x => x[1]);
  }
  const empty = (title, text, cta) => `<div class="empty">${ic('search-x')}<h3>${esc(title)}</h3><p>${esc(text)}</p>${cta || ''}</div>`;
  const demoNote = `<div class="note">${ic('info')}<p><b>Демонстраційний матеріал.</b> Інформація орієнтовна й не є юридичною консультацією. Актуальні умови уточнюйте на офіційних сайтах.</p></div>`;
  const faqHtml = faq => `<div class="acc">${faq.map(([q, a], i) => `<div class="acc-item"><button class="acc-btn" type="button" aria-expanded="false" data-acc>${esc(q)}${ic('chevron-down')}</button><div class="acc-panel" hidden><p>${esc(a)}</p></div></div>`).join('')}</div>`;
  const extLink = (label, url, cls = 'btn ghost') => `<a class="${cls}" href="${url}" target="_blank" rel="noopener noreferrer">${esc(label)}${ic('external-link')}</a>`;
  const searchField = (id, ph, val = '') => `<form class="searchbox" id="${id}" role="search" autocomplete="off">
      ${ic('search', 'lead')}<input type="text" name="q" value="${esc(val)}" placeholder="${esc(ph)}" aria-label="${esc(ph)}" role="combobox" aria-expanded="false" aria-autocomplete="list" />
      <button type="submit" class="go" aria-label="Шукати">${ic('arrow-right')}</button><ul class="suggest" role="listbox" hidden></ul></form>`;

  /* Пошукова стрічка з підказками */
  function bindSearch(formSel) {
    const form = $(formSel); if (!form) return;
    const input = $('input', form), list = $('.suggest', form);
    let items = [], active = -1;
    const close = () => { list.hidden = true; input.setAttribute('aria-expanded', 'false'); active = -1; };
    const paint = () => $$('li', list).forEach((li, i) => li.classList.toggle('active', i === active));
    function update() {
      const q = input.value.trim();
      if (!q) { close(); return; }
      items = search(q).slice(0, 5).map(x => ({ href: '#/i/' + x.id, title: x.title, c: catById(x.cat).title }))
        .concat(searchEvents(q).slice(0, 2).map(e => ({ href: '#/e/' + e.id, title: e.title, c: 'Життєва подія' })));
      list.innerHTML = items.length
        ? items.map((x, i) => `<li role="option" data-i="${i}">${ic('search', 'sm')}<span class="t">${esc(x.title)}</span><span class="c">${esc(x.c)}</span></li>`).join('')
        : `<li class="none">${ic('search-x', 'sm')}<span>Нічого не знайдено. Спробуйте інші слова, наприклад «паспорт» чи «ФОП».</span></li>`;
      list.hidden = false; input.setAttribute('aria-expanded', 'true'); active = -1; lucide.createIcons();
    }
    input.addEventListener('input', update);
    input.addEventListener('focus', update);
    input.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (items.length) { active = (active + 1) % items.length; paint(); } }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (items.length) { active = (active - 1 + items.length) % items.length; paint(); } }
      else if (e.key === 'Escape') close();
    });
    list.addEventListener('mousedown', e => {
      const li = e.target.closest('li[data-i]'); if (!li) return;
      e.preventDefault(); location.hash = items[+li.dataset.i].href;
    });
    form.addEventListener('submit', e => {
      e.preventDefault();
      const q = input.value.trim();
      if (active >= 0 && items[active]) { location.hash = items[active].href; return; }
      if (!q) { form.classList.add('shake'); input.focus(); toast('Введіть, що вам потрібно зробити'); setTimeout(() => form.classList.remove('shake'), 400); return; }
      close(); location.hash = '#/search/' + encodeURIComponent(q);
    });
    document.addEventListener('click', e => { if (!form.contains(e.target)) close(); });
  }

  /* Живий фільтр списку */
  function bindFilter(inputSel, render) {
    const inp = $(inputSel); if (!inp) return;
    inp.addEventListener('input', () => render(inp.value));
    inp.closest('form').addEventListener('submit', e => e.preventDefault());
  }

  /* ---------- Сторінки ---------- */
  function pageHome() {
    const pop = POPULAR.slice(0, 6).map(id => INS[id]);
    app.innerHTML = `<section class="hero"><div class="container narrow center">
        <h1 class="hero-title">Як це працює?</h1>
        <p class="hero-sub">Просто про важливе в Україні</p>
        ${searchField('homeSearch', 'Що вам потрібно зробити?')}
        <p class="hint">Наприклад: <a href="#/search/комуналка">комуналка</a>, <a href="#/search/ФОП">ФОП</a>, <a href="#/search/паспорт">паспорт</a></p>
        <div class="cats">${CATS.map(c => `<a class="cat" href="#/c/${c.id}">${ic(c.icon)}<span>${esc(c.title)}</span></a>`).join('')}</div>
        <p class="ev-link">Або почніть із життєвої події: ${['birth', 'death', 'passport', 'move'].map(id => { const e = evById(id); return `<a href="#/e/${id}">${esc(e.title)}</a>`; }).join('')}<a class="all" href="#/events">Усі події ${ic('arrow-right', 'sm')}</a></p>
      </div></section>
      <section class="container home-lists">
        <div><h2 class="h2">Популярні запитання</h2><ul class="qlist">${POPULAR_Q.map(([q, id]) => `<li><a href="#/i/${id}">${ic('circle-help')}<span>${esc(q)}</span></a></li>`).join('')}</ul></div>
        <div><h2 class="h2">Найбільш затребувані інструкції</h2><ol class="toplist">${pop.map((x, i) => `<li><a href="#/i/${x.id}"><span class="rank">${i + 1}</span><span class="tl-main"><b>${esc(x.title)}</b><small>${esc(catById(x.cat).title)} · ${esc(x.time)}</small></span>${ic('chevron-right', 'chev')}</a></li>`).join('')}</ol></div>
      </section>`;
    bindSearch('#homeSearch');
  }

  function pageTopics() {
    let cat = '';
    app.innerHTML = `<div class="container"><div class="page-head">${crumbs([['Головна', '#/'], ['Усі теми']])}<h1>Усі теми</h1>
      <p class="lead">Усі інструкції в одному місці. Оберіть тему або скористайтеся пошуком.</p></div>
      <form class="searchbox plain" id="tf" autocomplete="off" role="search">${ic('search', 'lead')}<input type="text" id="tq" placeholder="Пошук серед усіх інструкцій" aria-label="Пошук серед усіх інструкцій" /></form>
      <div class="chips" id="chips"><button class="chip on" data-cat="">Усі</button>${CATS.map(c => `<button class="chip" data-cat="${c.id}">${esc(c.title)}</button>`).join('')}</div>
      <div id="tres"></div></div>`;
    const draw = () => {
      const q = $('#tq').value.trim();
      let list = q ? search(q, cat) : Object.values(INS).filter(i => !cat || i.cats.includes(cat));
      $('#tres').innerHTML = list.length ? insList(list) : empty('Нічого не знайдено', 'Спробуйте змінити запит або обрати іншу тему.', `<button class="btn ghost" id="reset">Скинути фільтри</button>`);
      const r = $('#reset'); if (r) r.onclick = () => { cat = ''; $('#tq').value = ''; $$('.chip').forEach(c => c.classList.toggle('on', !c.dataset.cat)); draw(); };
      refreshSaveUI();
    };
    $('#chips').addEventListener('click', e => {
      const b = e.target.closest('.chip'); if (!b) return;
      cat = b.dataset.cat; $$('.chip').forEach(c => c.classList.toggle('on', c === b)); draw();
    });
    bindFilter('#tq', draw); draw();
  }

  function pagePopular() {
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Популярні питання']])}<h1>Популярні питання</h1>
      <p class="lead">З чим люди звертаються найчастіше.</p></div>
      ${insList(POPULAR.map(id => INS[id]))}
      <h2 class="h2 mt">Загальні запитання</h2>
      ${faqHtml([['Чи це офіційний сервіс?', 'Ні. «Як?» — демонстраційний прототип. Ми пояснюємо, як діяти, й ведемо на офіційні сервіси.'], ['Чи потрібно реєструватися?', 'Ні. Збережені інструкції зберігаються лише у вашому браузері.'], ['Чи можна покладатися на інструкції?', 'Матеріали демонстраційні. Завжди звіряйтеся з офіційними джерелами.']])}</div>`;
    refreshSaveUI();
  }

  function pageAbout() {
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Про проєкт']])}<h1>Про проєкт</h1>
      <p class="lead">«Як?» — цифровий помічник, який пояснює, як вирішувати повсякденні життєві питання в Україні.</p></div>
      <div class="prose"><h3>Наш принцип</h3><p>Мінімум дій від вас, максимум користі. Ми питаємо лише те, що впливає на результат, і показуємо найкоротший шлях першим.</p>
      <h3>Що це не є</h3><p>Це не державний портал, не платіжний сервіс і не юридична консультація. Усі матеріали в цьому прототипі — демонстраційні.</p>
      <h3>Ваші дані</h3><p>Ми не просимо ПІБ, телефон чи паспорт. Збережені інструкції та введена адреса зберігаються лише у вашому браузері.</p></div>
      ${demoNote}<a class="btn primary mt" href="#/topics">Переглянути всі теми</a></div>`;
  }

  async function pageSaved() {
    const tok = routeTok;
    const ids = getSaved();
    if (ids.some(i => i.startsWith('s:'))) { try { await loadGuide(); } catch (e) { /* показуємо лише інструкції */ } }
    if (tok !== routeTok && location.hash !== '#/saved') return;
    const have = typeof GUIDE_SERVICES !== 'undefined';
    const list = ids.map(id => id.startsWith('s:') ? (have && GUIDE_SERVICES[id.slice(2)] ? svcRow(id.slice(2)) : '') : (INS[id] ? insRow(INS[id]) : '')).filter(Boolean);
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Збережене']])}<h1>Збережене</h1>
      <p class="lead">Інструкції, які ви зберегли в цьому браузері.</p></div>
      ${list.length ? `<ul class="rows">${list.join('')}</ul>` : empty('Тут поки порожньо', 'Натисніть «Зберегти інструкцію» на сторінці інструкції, і вона зʼявиться тут.', `<a class="btn primary" href="#/topics">Знайти інструкцію</a>`)}</div>`;
    lucide.createIcons(); refreshSaveUI();
  }

  function pageSearch(q) {
    const tok = routeTok;
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Пошук']])}<h1>Результати пошуку</h1></div>
      ${searchField('sp', 'Що вам потрібно зробити?', q)}<div id="sres" class="mt"></div><div id="sres2"></div></div>`;
    bindSearch('#sp');
    const res = search(q), evs = searchEvents(q);
    $('#sres').innerHTML = `<p class="muted">За запитом «${esc(q)}»: ${res.length + evs.length}</p>` +
      (evs.length ? `<h2 class="h2 sub">Життєві події</h2><ul class="rows">${evs.map(e => `<li class="row-wrap"><a class="row" href="#/e/${e.id}"><span class="row-main"><span class="row-title">${esc(e.title)}</span><span class="row-meta">${e.n} послуг · ${e.aud === 'b' ? 'для бізнесу' : 'для громадян'}</span></span>${ic('chevron-right', 'chev')}</a></li>`).join('')}</ul>` : '') +
      (res.length ? `<h2 class="h2 sub">Інструкції</h2>${insList(res)}` : '');
    $('#sres2').innerHTML = `<p class="muted mt">Шукаємо в реєстрі державних послуг…</p>`;
    lucide.createIcons(); refreshSaveUI();
    loadGuide().then(() => {
      if (tok !== routeTok) return;
      const sv = searchServices(q).slice(0, 30);
      $('#sres2').innerHTML = sv.length ? `<h2 class="h2 sub">Державні послуги (Гід Дія)</h2>${svcList(sv)}` : '';
      if (!res.length && !evs.length && !sv.length) $('#sres').innerHTML += empty('Нічого не знайдено', 'Спробуйте інші слова або перегляньте всі теми.', `<a class="btn primary" href="#/topics">Усі теми</a>`);
      lucide.createIcons(); refreshSaveUI();
    }).catch(() => { if (tok === routeTok) { $('#sres2').innerHTML = ''; if (!res.length && !evs.length) $('#sres').innerHTML += empty('Нічого не знайдено', 'Спробуйте інші слова або перегляньте всі теми.', `<a class="btn primary" href="#/topics">Усі теми</a>`); lucide.createIcons(); } });
  }

  /* ---------- Життєві події (дані Гіду Дія) ---------- */
  const evProg = (n, id, secIdx) => {
    const labels = ['Подія', 'Тема', 'Послуга', 'Інструкція'];
    const href = { 1: '#/events', 2: id ? '#/e/' + id : null, 3: id && secIdx != null ? `#/e/${id}/${secIdx}` : null };
    return `<div class="kprog" aria-label="Прогрес">${labels.map((l, i) => { const s = i + 1, cls = s < n ? 'past' : s === n ? 'cur' : '', h = s < n && href[s]; return h ? `<a href="${h}" class="kp ${cls}"><em>${l}</em></a>` : `<span class="kp ${cls}"${s === n ? ' aria-current="step"' : ''}><em>${l}</em></span>`; }).join('')}</div>`;
  };
  let evAud = 'c';
  function pageEvents() {
    app.innerHTML = `<div class="container"><div class="page-head">${crumbs([['Головна', '#/'], ['Життєві події']])}
      <h1>Життєві події</h1><p class="lead">Оберіть ситуацію, і ми покажемо державні послуги, які для неї потрібні: документи, строки, вартість і куди звертатися.</p></div>
      <form class="searchbox plain" id="evf" autocomplete="off" role="search">${ic('search', 'lead')}<input id="evq" type="text" placeholder="Знайти державну послугу, наприклад «свідоцтво про народження»" aria-label="Пошук державної послуги" /></form>
      <div id="evtabs" class="chips" role="tablist"><button class="chip" data-a="c" role="tab">Для громадян</button><button class="chip" data-a="b" role="tab">Для бізнесу</button></div>
      <div id="evres"></div>
      <p class="source">Дані: <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a> (відкритий реєстр, CC BY 4.0), скорочено для демонстрації.</p></div>`;
    const tok = routeTok;
    const draw = () => {
      $$('#evtabs .chip').forEach(c => { const on = c.dataset.a === evAud; c.classList.toggle('on', on); c.setAttribute('aria-selected', on); });
      const q = $('#evq').value.trim();
      if (q.length < 2) {
        const list = GUIDE_EVENTS.filter(e => e.aud === evAud);
        $('#evres').innerHTML = `<div class="ev-grid">${list.map(e => `<a class="ev" href="#/e/${e.id}"><span class="ev-ic">${ic(e.icon)}</span><b>${esc(e.title)}</b><span class="ev-d">${esc(e.desc)}</span><small>${e.n} послуг</small></a>`).join('')}</div>`;
        $('#evtabs').hidden = false; lucide.createIcons(); return;
      }
      $('#evtabs').hidden = true;
      $('#evres').innerHTML = `<p class="muted">Шукаємо…</p>`;
      loadGuide().then(() => {
        if (tok !== routeTok || $('#evq').value.trim() !== q) return;
        const sv = searchServices(q), evs = searchEvents(q);
        $('#evres').innerHTML = (evs.length ? `<h2 class="h2 sub">Життєві події</h2><div class="ev-grid">${evs.map(e => `<a class="ev" href="#/e/${e.id}"><span class="ev-ic">${ic(e.icon)}</span><b>${esc(e.title)}</b><small>${e.n} послуг</small></a>`).join('')}</div>` : '') +
          (sv.length ? `<h2 class="h2 sub">Послуги: ${sv.length}${sv.length > 40 ? ' (перші 40)' : ''}</h2>${svcList(sv.slice(0, 40))}` : (evs.length ? '' : empty('Нічого не знайдено', 'Спробуйте інші слова або оберіть подію зі списку.', `<button class="btn ghost" id="evreset">Скинути пошук</button>`)));
        const r = $('#evreset'); if (r) r.onclick = () => { $('#evq').value = ''; draw(); };
        lucide.createIcons(); refreshSaveUI();
      }).catch(() => { if (tok === routeTok) $('#evres').innerHTML = empty('Не вдалося завантажити дані', 'Перевірте з’єднання та спробуйте ще раз.'); lucide.createIcons(); });
    };
    $('#evtabs').addEventListener('click', e => { const b = e.target.closest('.chip'); if (b) { evAud = b.dataset.a; draw(); } });
    bindFilter('#evq', draw); draw();
  }

  async function pageEvent(id, sec) {
    const ev = evById(id); if (!ev) return page404();
    const tok = routeTok;
    const bc = [['Головна', '#/'], ['Життєві події', '#/events']];
    if (sec == null) {
      if (ev.sectors.length === 1 || ev.n <= 8) { location.replace(`#/e/${id}/all`); return; }
      app.innerHTML = `<div class="container narrow-m"><div class="page-head">${crumbs(bc.concat([[ev.title]]))}${evProg(2, id)}
        <h1>Що саме вам потрібно?</h1><p class="lead">Подія «${esc(ev.title)}»: ${ev.n} послуг. Оберіть тему, щоб побачити лише потрібні.</p></div>
        <form id="sf" novalidate><div class="opts" role="radiogroup" aria-label="Тема">
        ${ev.sectors.map((s, i) => `<label class="opt"><input type="radio" name="s" value="${i}"><span><b>${esc(s[0])}</b><small>${s[1]} ${s[1] === 1 ? 'послуга' : s[1] < 5 ? 'послуги' : 'послуг'}</small></span></label>`).join('')}
        <label class="opt"><input type="radio" name="s" value="all"><span><b>Показати всі послуги події</b><small>${ev.n} послуг</small></span></label></div>
        <p class="err" id="serr" hidden>Оберіть тему, щоб продовжити.</p>
        <div class="actions"><a class="btn ghost" href="#/events">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">Продовжити ${ic('arrow-right')}</button></div></form></div>`;
      const f = $('#sf'); f.addEventListener('change', () => { $('#serr').hidden = true; });
      f.addEventListener('submit', e => { e.preventDefault(); const v = f.s.value; if (!v) { $('#serr').hidden = false; return; } location.hash = `#/e/${id}/${v}`; });
      return;
    }
    app.innerHTML = loadingHtml; lucide.createIcons();
    try { await loadGuide(); } catch (e) { if (tok === routeTok) loadErr(); return; }
    if (tok !== routeTok) return;
    const secs = GUIDE_SECTORS[id];
    const all = sec === 'all', one = secs[+sec];
    if (!all && !one) return page404();
    const ids = all ? secs.flatMap(s => s[1]) : one[1];
    const single = ev.sectors.length === 1 || ev.n <= 8;
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs(bc.concat([[ev.title, single ? null : '#/e/' + id], [all ? 'Усі послуги' : one[0]]].map((x, i, a) => x)))}${evProg(3, id, sec)}
      <h1>${all ? esc(ev.title) : esc(one[0])}</h1><p class="lead">${all ? 'Оберіть послугу, щоб побачити документи, строки та куди звертатися.' : `Подія «${esc(ev.title)}». Оберіть послугу, щоб побачити документи, строки та куди звертатися.`}</p></div>
      <form class="searchbox plain" autocomplete="off" role="search">${ic('search', 'lead')}<input id="sq" type="text" placeholder="Пошук серед ${ids.length} послуг" aria-label="Пошук серед послуг" /></form>
      <div id="sl"></div>
      <div class="actions"><a class="btn ghost" href="${single ? '#/events' : '#/e/' + id}">${ic('arrow-left')} Назад</a></div></div>`;
    const draw = () => {
      const q = norm($('#sq').value.trim()).split(/\s+/).filter(t => t && !STOP.includes(t));
      const list = q.length ? ids.filter(i => { const s = GUIDE_SERVICES[i], w = norm(s.n + ' ' + s.f + ' ' + s.s).split(/\s+/); return q.every(t => w.some(x => wm(t, x))); }) : ids;
      $('#sl').innerHTML = list.length ? svcList(list, id) : empty('Нічого не знайдено', 'Спробуйте інші слова.');
      lucide.createIcons(); refreshSaveUI();
    };
    bindFilter('#sq', draw); draw();
  }

  async function pageService(sid, eid) {
    const tok = routeTok;
    app.innerHTML = loadingHtml; lucide.createIcons();
    try { await loadGuide(); } catch (e) { if (tok === routeTok) loadErr(); return; }
    if (tok !== routeTok) return;
    const s = GUIDE_SERVICES[sid]; if (!s) return page404();
    const ev = eid && evById(eid);
    const bc = [['Головна', '#/'], ['Життєві події', '#/events']];
    if (ev) { bc.push([ev.title, '#/e/' + ev.id]); }
    bc.push([s.n]);
    const key = 's-' + sid, done = getDone(key);
    const guideUrl = 'https://guide.diia.gov.ua/register/' + sid + '/';
    const steps = [
      ['Переконайтеся, що послуга вам підходить', `Для кого: ${s.a.length ? s.a.join(', ') : 'див. опис послуги'}. ${s.sp ? 'Де діє: ' + s.sp + '.' : ''}`],
      ['Підготуйте документи', s.i.length ? 'Перелік наведено вище. Деякі документи потрібні лише в окремих випадках, тому уточніть це в органі.' : 'Окремий перелік документів не вказано. Уточніть його в органі, що надає послугу.'],
      ['Оберіть спосіб звернення', s.w.length ? `Доступні способи: ${s.w.join(', ').toLowerCase()}.${s.l ? ' Є онлайн-сервіс за посиланням нижче.' : ''}` : (s.l ? 'Є онлайн-сервіс за посиланням нижче.' : 'Спосіб звернення уточніть в органі.')],
      ['Подайте заяву', s.v.length ? `Куди звернутися: ${s.v.join('; ')}.` : 'Орган, що надає послугу, вказано на сторінці послуги в Гіді Дія.'],
      ['Дочекайтеся результату', `${s.t ? 'Строк: ' + s.t + '. ' : ''}${s.c ? 'Вартість: ' + s.c + '.' : ''}`.trim() || 'Строк і вартість див. на сторінці послуги.']
    ];
    app.innerHTML = `<article class="container narrow-l"><div class="page-head">${crumbs(bc)}${ev ? evProg(4, ev.id) : ''}
      <div class="title-row"><h1>${esc(s.n)}</h1>${saveBtn('s:' + sid)}</div>
      ${s.f && s.f !== s.n ? `<p class="official">Повна назва: ${esc(s.f)}</p>` : ''}
      <p class="lead">${esc(s.d || s.f)}</p>
      <div class="meta">${s.t ? `<span>${ic('clock')} Строк: ${esc(s.t)}</span>` : ''}${s.c ? `<span>${ic('banknote')} Вартість: ${esc(s.c)}</span>` : ''}</div></div>
      ${s.p.length ? `<div class="why">${ic('file-check')}<p><b>Що ви отримаєте.</b> ${esc(s.p.join('; '))}</p></div>` : ''}
      <section><h2 class="h2">Що знадобиться</h2>${s.i.length ? `<ul class="need">${s.i.map(n => `<li>${ic('check')}<span>${esc(n)}</span></li>`).join('')}</ul>` : '<p class="muted">Окремий перелік документів у реєстрі не вказано.</p>'}</section>
      <section><div class="h2-row"><h2 class="h2">Покрокова інструкція</h2><span class="muted" id="progTxt"></span></div><div class="bar"><i id="progBar"></i></div>
      <ol class="steps">${steps.map((x, i) => `<li class="step${done.includes(i) ? ' done' : ''}"><label><input type="checkbox" data-i="${i}" ${done.includes(i) ? 'checked' : ''}><span class="num">${i + 1}</span><span class="body"><b>${esc(x[0])}</b><span>${esc(x[1])}</span></span></label></li>`).join('')}</ol></section>
      <section><h2 class="h2">Як подати і куди звернутися</h2><div class="methods">
        ${s.l ? `<div class="method"><span class="tag">Онлайн</span><b>Електронний сервіс</b><p>Подайте заяву дистанційно, якщо вам це підходить.</p></div>` : ''}
        ${s.w.length ? `<div class="method"><b>Способи подачі</b><p>${esc(s.w.join(', '))}</p></div>` : ''}
        ${s.v.length ? `<div class="method"><b>Куди звернутися</b><p>${esc(s.v.join('; '))}</p></div>` : ''}</div></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml([['Що, якщо мені відмовили?', 'Підстави відмови та порядок оскарження наведено на сторінці послуги в Гіді Дія. Ви можете оскаржити рішення в установленому порядку.'], ['Чи однакові умови по всій країні?', 'Загальнодержавні умови однакові, але місцеві органи можуть мати власні вимоги. Уточніть у відповідному органі.'], ['Де знайти повні умови та нормативну базу?', 'На сторінці послуги в Гіді Дія є підрозділи «Як отримати і що для цього потрібно» та «Нормативна база».']])}</section>
      <section><h2 class="h2">Корисні офіційні посилання</h2><div class="links">${extLink('Повна інформація в Гіді Дія', guideUrl, 'btn primary')}${s.l ? extLink('Онлайн-сервіс', s.l) : ''}${extLink('Портал Дія', 'https://diia.gov.ua/')}</div></section>
      ${demoNote}
      <p class="source">Джерело: <a href="${guideUrl}" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a>, ідентифікатор послуги ${esc(sid)}. Ліцензія CC BY 4.0, текст скорочено. Дата останньої перевірки: ${CHECKED} (демо).</p>
      <div class="actions"><a class="btn ghost" href="${ev ? '#/e/' + ev.id : '#/events'}">${ic('arrow-left')} Назад до послуг</a></div></article>`;
    const upd = () => { const b = $$('.step input'), n = b.filter(x => x.checked).length; $('#progTxt').textContent = `Виконано ${n} з ${b.length}`; $('#progBar').style.width = (n / b.length * 100) + '%'; };
    $('.steps').addEventListener('change', e => {
      if (!e.target.matches('input')) return;
      e.target.closest('.step').classList.toggle('done', e.target.checked);
      store.set('yak_done_' + key, $$('.step input').filter(x => x.checked).map(x => +x.dataset.i)); upd();
      if ($$('.step input').every(x => x.checked)) toast('Усі кроки виконано. Чудова робота!', 'ok');
    });
    upd(); lucide.createIcons(); refreshSaveUI();
  }

  function pageCategory(id) {
    const cat = catById(id); if (!cat) return page404();
    const all = Object.values(INS).filter(i => i.cats.includes(id));
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], [cat.title]])}
      <div class="cat-title">${ic(cat.icon, 'big')}<h1>${esc(cat.title)}</h1></div><p class="lead">${esc(cat.desc)}</p></div>
      <form class="searchbox plain" autocomplete="off" role="search">${ic('search', 'lead')}<input id="cq" type="text" placeholder="Пошук у розділі «${esc(cat.title)}»" aria-label="Пошук у розділі" /></form>
      <div id="cres" class="mt"></div></div>`;
    const draw = () => {
      const q = $('#cq').value.trim();
      const list = q ? search(q, id) : all;
      $('#cres').innerHTML = list.length ? insList(list) : empty('У цьому розділі нічого не знайдено', 'Спробуйте інші слова або перегляньте всі теми.', `<a class="btn ghost" href="#/search/${encodeURIComponent(q)}">Шукати на всьому сайті</a>`);
      refreshSaveUI();
    };
    bindFilter('#cq', draw); draw();
  }

  const saveBtn = id => `<button class="btn ghost save" type="button" data-save="${id}"></button>`;

  function pageInstruction(id, opt) {
    const base = INS[id]; if (!base) return page404();
    if (base.flow === 'komunalka') return pageKom(1);
    const cat = catById(base.cat);
    if (base.wizard && !opt) return pageChoice(base, cat);
    let ins = base, chosen = null;
    if (base.wizard) {
      chosen = base.wizard.options.find(o => o.id === opt);
      if (!chosen) return pageChoice(base, cat);
      const o = Object.assign({}, chosen.over);
      if (o.steps) o.steps = o.steps.map(s => s.split('|'));
      ins = Object.assign({}, base, o);
    }
    const key = id + (opt ? '-' + opt : '');
    const done = getDone(key);
    const bc = [['Головна', '#/'], [cat.title, '#/c/' + cat.id]];
    if (chosen) { bc.push([base.title, '#/i/' + id]); bc.push([chosen.label]); } else bc.push([base.title]);
    app.innerHTML = `<article class="container narrow-l">
      <div class="page-head">${crumbs(bc)}
        <div class="title-row"><h1>${esc(base.title)}</h1>${saveBtn(id)}</div>
        <p class="lead">${esc(ins.summary)}</p>
        <div class="meta"><span>${ic('clock')} Приблизно ${esc(ins.time)}</span>${chosen ? `<span>${ic('route')} Ваш вибір: <b>${esc(chosen.label)}</b> · <a href="#/i/${id}">змінити</a></span>` : ''}</div>
      </div>
      ${ins.why ? `<div class="why">${ic('lightbulb')}<p><b>Чому спершу так.</b> ${esc(ins.why)}</p></div>` : ''}
      <section><h2 class="h2">Що знадобиться</h2><ul class="need">${ins.needs.map(n => `<li>${ic('check')}<span>${esc(n)}</span></li>`).join('')}</ul></section>
      <section><div class="h2-row"><h2 class="h2">Покрокова інструкція</h2><span class="muted" id="progTxt"></span></div>
        <div class="bar"><i id="progBar"></i></div>
        <ol class="steps">${ins.steps.map((s, i) => `<li class="step${done.includes(i) ? ' done' : ''}"><label><input type="checkbox" data-i="${i}" ${done.includes(i) ? 'checked' : ''}><span class="num">${i + 1}</span><span class="body"><b>${esc(s[0])}</b><span>${esc(s[1] || '')}</span></span></label></li>`).join('')}</ol>
      </section>
      <section><h2 class="h2">Можливі способи</h2><div class="methods">${ins.methods.map((m, i) => `<div class="method">${i === 0 ? '<span class="tag">Найпростіший</span>' : ''}<b>${esc(m[0])}</b><p>${esc(m[1])}</p></div>`).join('')}</div></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml(ins.faq)}</section>
      <section><h2 class="h2">Корисні офіційні посилання</h2><div class="links">${ins.links.map(l => extLink(l[0], l[1])).join('')}</div></section>
      ${demoNote}
      <p class="checked">${ic('calendar-check')} Дата останньої перевірки інформації: ${CHECKED} (демо)</p>
      <div class="bottom-nav"><a class="btn ghost" href="#/c/${cat.id}">${ic('arrow-left')} До розділу «${esc(cat.title)}»</a></div>
    </article>`;
    const upd = () => {
      const boxes = $$('.step input'); const n = boxes.filter(b => b.checked).length;
      $('#progTxt').textContent = `Виконано ${n} з ${boxes.length}`; $('#progBar').style.width = (n / boxes.length * 100) + '%';
    };
    $('.steps').addEventListener('change', e => {
      const b = e.target; if (!b.matches('input')) return;
      b.closest('.step').classList.toggle('done', b.checked);
      store.set('yak_done_' + key, $$('.step input').filter(x => x.checked).map(x => +x.dataset.i));
      upd();
      if ($$('.step input').every(x => x.checked)) toast('Усі кроки виконано. Чудова робота!', 'ok');
    });
    upd(); refreshSaveUI();
  }

  function pageChoice(base, cat) {
    const w = base.wizard;
    app.innerHTML = `<div class="container narrow-m"><div class="page-head">${crumbs([['Головна', '#/'], [cat.title, '#/c/' + cat.id], [base.title]])}
      <div class="progress"><div class="bar"><i style="width:50%"></i></div><span>Крок 1 з 2</span></div>
      <h1>${esc(w.q)}</h1><p class="lead">${esc(w.sub)}</p></div>
      <form id="choice" novalidate><div class="opts" role="radiogroup" aria-label="${esc(w.q)}">${w.options.map(o => `<label class="opt"><input type="radio" name="o" value="${o.id}">${ic(o.icon, 'oi')}<span><b>${esc(o.label)}</b><small>${esc(o.desc)}</small></span></label>`).join('')}</div>
      <p class="err" id="cerr" hidden>Оберіть один із варіантів, щоб продовжити.</p>
      <div class="actions"><a class="btn ghost" href="#/c/${cat.id}">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">Продовжити ${ic('arrow-right')}</button></div></form></div>`;
    const f = $('#choice');
    f.addEventListener('change', () => { $('#cerr').hidden = true; });
    f.addEventListener('submit', e => {
      e.preventDefault();
      const v = f.o.value; if (!v) { $('#cerr').hidden = false; return; }
      location.hash = `#/i/${base.id}/${v}`;
    });
  }

  /* ---------- Сценарій: оплата комуналки ---------- */
  const kState = () => store.get('yak_kom', {});
  const kSave = s => store.set('yak_kom', s);
  const K_STEPS = ['Місто', 'Адреса', 'Спосіб', 'Інструкція'];
  const kProgress = (n, st) => `<div class="kprog" aria-label="Прогрес">${K_STEPS.map((l, i) => {
    const s = i + 1, cls = s < n ? 'past' : s === n ? 'cur' : '';
    const can = s < n || (s === 3 && st.street);
    return `<${can && s < n ? `a href="#/k/${s}"` : 'span'} class="kp ${cls}"${s === n ? ' aria-current="step"' : ''}><i>${s < n ? ic('check') : s}</i><em>${l}</em></${can && s < n ? 'a' : 'span'}>`;
  }).join('')}</div>`;
  const kCrumbs = tail => crumbs([['Головна', '#/'], ['Комунальні послуги', '#/c/utilities'], ['Як оплатити комуналку?', tail ? '#/k/1' : null]].concat(tail ? [[tail]] : []));
  const addrLine = st => [st.oblast && st.oblast !== 'м. Київ' ? st.oblast + ' обл.' : '', 'м. ' + st.city, st.street, 'буд. ' + st.house, st.flat ? 'кв. ' + st.flat : ''].filter(Boolean).join(', ');

  function pageKom(step, service) {
    const st = kState();
    if (step > 1 && !st.city) return (location.hash = '#/k/1');
    if (step > 2 && !st.street) return (location.hash = '#/k/2');
    ({ 1: kStep1, 2: kStep2, 3: kStep3, 4: kStep4 }[step] || kStep1)(st, service);
  }

  function kStep1(st) {
    let picked = st.city || '';
    app.innerHTML = `<div class="container narrow-m"><div class="page-head">${kCrumbs()}${kProgress(1, st)}
      <h1>Оберіть ваше місто</h1><p class="lead">Від міста залежить перелік доступних постачальників та способів оплати.</p></div>
      <form id="k1" novalidate autocomplete="off">
        <div class="field"><label for="city">Місто</label><div class="searchbox plain">${ic('map-pin', 'lead')}<input id="city" type="text" value="${esc(picked)}" placeholder="Почніть вводити назву міста" aria-describedby="cerr" /></div>
        <p class="err" id="cerr" hidden></p></div>
        <p class="small-label">Приклади</p>
        <div class="chips" id="ex">${['Київ', 'Кривий Ріг', 'Дніпро', 'Львів', 'Одеса', 'Харків'].map(c => `<button type="button" class="chip${c === picked ? ' on' : ''}" data-c="${c}">${c}</button>`).join('')}</div>
        <ul class="cities" id="cl"></ul>
        <div class="actions"><a class="btn ghost" href="#/c/utilities">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">Продовжити ${ic('arrow-right')}</button></div>
      </form></div>`;
    const inp = $('#city'), err = $('#cerr');
    const drawList = () => {
      const q = norm(inp.value.trim());
      const res = CITIES.filter(c => !q || norm(c[0]).includes(q)).slice(0, 8);
      $('#cl').innerHTML = (q && picked !== inp.value) ? (res.length ? res.map(c => `<li><button type="button" data-c="${c[0]}">${ic('map-pin', 'sm')}<span>${c[0]}</span><small>${c[1] === 'м. Київ' ? 'місто' : c[1] + ' обл.'}</small></button></li>`).join('')
        : `<li class="none">${ic('search-x', 'sm')}<span>Такого міста немає в демо-списку. Оберіть місто з прикладів або зі списку.</span></li>`) : '';
      lucide.createIcons();
    };
    const pick = c => { picked = c; inp.value = c; err.hidden = true; inp.classList.remove('bad'); $$('#ex .chip').forEach(b => b.classList.toggle('on', b.dataset.c === c)); drawList(); };
    inp.addEventListener('input', () => { picked = CITIES.find(c => c[0].toLowerCase() === inp.value.trim().toLowerCase())?.[0] || ''; err.hidden = true; inp.classList.remove('bad'); $$('#ex .chip').forEach(b => b.classList.toggle('on', b.dataset.c === picked)); drawList(); });
    $('#k1').addEventListener('click', e => { const b = e.target.closest('[data-c]'); if (b) pick(b.dataset.c); });
    $('#k1').addEventListener('submit', e => {
      e.preventDefault();
      if (!inp.value.trim()) { err.textContent = 'Оберіть ваше місто.'; }
      else if (!picked) { err.textContent = 'Оберіть місто зі списку, щоб ми могли підібрати способи оплати.'; }
      else {
        const ns = Object.assign({}, st);
        if (ns.city !== picked) { ns.city = picked; ns.oblast = CITIES.find(c => c[0] === picked)[1]; }
        kSave(ns); location.hash = '#/k/2'; return;
      }
      err.hidden = false; inp.classList.add('bad'); inp.focus();
    });
    drawList();
  }

  function kStep2(st) {
    app.innerHTML = `<div class="container narrow-m"><div class="page-head">${kCrumbs()}${kProgress(2, st)}
      <h1>Вкажіть адресу</h1><p class="lead">Ми не питаємо ПІБ, телефон чи паспорт. Адреса потрібна лише для підбору способів оплати.</p></div>
      <form id="k2" novalidate autocomplete="off">
        <div class="grid2">
          <div class="field"><label for="oblast">Область</label><select id="oblast">${OBLASTS.map(o => `<option${o === st.oblast ? ' selected' : ''}>${o}</option>`).join('')}</select><p class="err" hidden></p></div>
          <div class="field"><label for="fcity">Місто</label><input id="fcity" type="text" value="${esc(st.city)}" /><p class="err" hidden></p></div>
        </div>
        <div class="field"><label for="street">Вулиця</label><input id="street" type="text" placeholder="Наприклад, Соборна" value="${esc(st.street || '')}" /><p class="err" hidden></p></div>
        <div class="grid2">
          <div class="field"><label for="house">Будинок</label><input id="house" type="text" placeholder="Наприклад, 12А" value="${esc(st.house || '')}" /><p class="err" hidden></p></div>
          <div class="field"><label for="flat">Квартира <span class="opt-l">необовʼязково</span></label><input id="flat" type="text" inputmode="numeric" placeholder="Наприклад, 45" value="${esc(st.flat || '')}" /><p class="err" hidden></p></div>
        </div>
        <div class="actions"><a class="btn ghost" href="#/k/1">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">Знайти способи оплати ${ic('search')}</button></div>
      </form></div>`;
    const rules = {
      oblast: v => v ? '' : 'Оберіть область.',
      fcity: v => v.length < 2 ? 'Вкажіть місто.' : '',
      street: v => v.length < 2 ? 'Вкажіть назву вулиці.' : /^[\d\s]+$/.test(v) ? 'Вулиця не може складатися лише з цифр.' : '',
      house: v => !v ? 'Вкажіть номер будинку.' : /^\d{1,4}\s?[А-Яа-яІіЇїЄєҐґA-Za-z]?(\/\d{1,3})?(-[А-Яа-яІіЇїЄєҐґA-Za-z0-9]{1,3})?$/.test(v) ? '' : 'Вкажіть номер у форматі 12, 12А або 12/2.',
      flat: v => !v || /^\d{1,4}$/.test(v) ? '' : 'Номер квартири — лише цифри.'
    };
    const check = id => {
      const el = $('#' + id), msg = rules[id](el.value.trim()), p = el.parentElement.querySelector('.err');
      p.textContent = msg; p.hidden = !msg; el.classList.toggle('bad', !!msg); return !msg;
    };
    Object.keys(rules).forEach(id => $('#' + id).addEventListener('blur', () => check(id)));
    Object.keys(rules).forEach(id => $('#' + id).addEventListener('input', () => { if ($('#' + id).classList.contains('bad')) check(id); }));
    $('#k2').addEventListener('submit', e => {
      e.preventDefault();
      const ok = Object.keys(rules).map(check).every(Boolean);
      if (!ok) { const b = $('.bad'); if (b) b.focus(); return; }
      kSave({ oblast: $('#oblast').value, city: $('#fcity').value.trim(), street: $('#street').value.trim(), house: $('#house').value.trim(), flat: $('#flat').value.trim() });
      location.hash = '#/k/3';
    });
  }

  function kStep3(st) {
    const order = ['easypay', 'privat24', 'portmone'].map(k => SERVICES[k]);
    const local = LOCAL_PROVIDERS[st.city];
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${kCrumbs()}${kProgress(3, st)}
      <h1>Оберіть найпростіший спосіб оплати</h1><p class="lead">Ми підібрали доступні варіанти для вашого міста та адреси.</p>
      <div class="addr">${ic('map-pin')}<span>${esc(addrLine(st))}</span><a href="#/k/2">Змінити</a></div></div>
      <div class="note">${ic('info')}<p><b>Це демонстрація.</b> Результати не є реальною перевіркою постачальників, і ми не стверджуємо, що кожен сервіс підтримує всі рахунки за вашою адресою.</p></div>
      <div class="svc-list">${order.map(s => `<section class="svc${s.recommended ? ' rec' : ''}">
        ${s.recommended ? '<span class="tag">Найпростіший варіант</span>' : ''}
        <div class="svc-head"><span class="svc-ic">${ic(s.icon)}</span><h2>${s.name}</h2></div>
        <p>${esc(s.desc)}</p>
        <p class="svc-why">${ic('lightbulb')}<span><b>Чому пропонуємо:</b> ${esc(s.why)}</span></p>
        <div class="pc"><div><h4>Переваги</h4><ul class="pros">${s.pros.map(x => `<li>${ic('check')}${esc(x)}</li>`).join('')}</ul></div>
        <div><h4>Можливі обмеження</h4><ul class="cons">${s.cons.map(x => `<li>${ic('triangle-alert')}${esc(x)}</li>`).join('')}</ul></div></div>
        <div class="svc-actions"><a class="btn ${s.recommended ? 'primary' : 'ghost'}" href="#/k/4/${s.id}">Як це працює?</a>${extLink('Перейти до сервісу', s.url, 'btn ghost')}</div>
      </section>`).join('')}</div>
      <section class="local"><h2 class="h2">Місцеві постачальники</h2>
        ${local ? `<p class="muted">Демонстраційний перелік для міста ${esc(st.city)}. Це не перевірка вашого будинку. Назву компанії перевіряйте у квитанції.</p>
        <ul class="rows plainrows">${local.map(p => `<li class="prov">${ic('building-2')}<span><b>${esc(p[1])}</b><small>${esc(p[0])}</small></span></li>`).join('')}</ul>`
          : empty('Місцевих постачальників не знайдено', `Для міста ${st.city} у демо немає даних. Скористайтеся сервісами вище або знайдіть постачальника за квитанцією.`, `<a class="btn ghost" href="#/i/provider-find">Як знайти свого постачальника?</a>`)}
      </section>
      <div class="actions"><a class="btn ghost" href="#/k/2">${ic('arrow-left')} Назад</a></div></div>`;
  }

  function kStep4(st, sid) {
    const s = SERVICES[sid]; if (!s) return (location.hash = '#/k/3');
    const key = 'k-' + sid, done = getDone(key);
    app.innerHTML = `<article class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Комунальні послуги', '#/c/utilities'], ['Як оплатити комуналку?', '#/k/3'], [s.name]])}${kProgress(4, st)}
      <div class="title-row"><h1>Як оплатити комунальні послуги через ${s.name}</h1>${saveBtn('komunalka')}</div>
      <p class="lead">Інструкція демонстраційна: назви розділів і кнопок у сервісі можуть відрізнятися. Орієнтуйтеся на підказки самого сервісу.</p>
      <div class="meta"><span>${ic('clock')} Приблизно 3–5 хв</span><span>${ic('map-pin')} ${esc(addrLine(st))}</span></div></div>
      <div class="cta-row">${extLink('Відкрити ' + s.name, s.url, 'btn primary')}<a class="btn ghost" href="#/k/3">Обрати інший сервіс</a></div>
      <section><div class="h2-row"><h2 class="h2">Покрокова інструкція</h2><span class="muted" id="progTxt"></span></div><div class="bar"><i id="progBar"></i></div>
      <ol class="steps">${s.steps.map((x, i) => { const p = x.split('|'); return `<li class="step${done.includes(i) ? ' done' : ''}"><label><input type="checkbox" data-i="${i}" ${done.includes(i) ? 'checked' : ''}><span class="num">${i + 1}</span><span class="body"><b>${esc(p[0])}</b><span>${esc(p[1] || '')}</span></span></label></li>`; }).join('')}</ol></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml(KOM_FAQ)}</section>
      <section><h2 class="h2">Корисні офіційні посилання</h2><div class="links">${Object.values(SERVICES).map(x => extLink(x.name, x.url)).join('')}</div></section>
      ${demoNote}<p class="checked">${ic('calendar-check')} Дата останньої перевірки інформації: ${CHECKED} (демо)</p>
      <div class="actions"><a class="btn ghost" href="#/k/3">${ic('arrow-left')} Назад</a><a class="btn ghost" href="#/c/utilities">До розділу</a></div></article>`;
    const upd = () => { const b = $$('.step input'), n = b.filter(x => x.checked).length; $('#progTxt').textContent = `Виконано ${n} з ${b.length}`; $('#progBar').style.width = (n / b.length * 100) + '%'; };
    $('.steps').addEventListener('change', e => {
      if (!e.target.matches('input')) return;
      e.target.closest('.step').classList.toggle('done', e.target.checked);
      store.set('yak_done_' + key, $$('.step input').filter(x => x.checked).map(x => +x.dataset.i)); upd();
      if ($$('.step input').every(x => x.checked)) toast('Усі кроки виконано. Чудова робота!', 'ok');
    });
    upd(); refreshSaveUI();
  }

  function page404() {
    app.innerHTML = `<div class="container narrow-m">${empty('Сторінку не знайдено', 'Можливо, посилання застаріло. Поверніться на головну або скористайтеся пошуком.', `<a class="btn primary" href="#/">На головну</a>`)}</div>`;
  }

  /* ---------- Роутер ---------- */
  let routeTok = 0;
  function route() {
    routeTok++;
    const parts = location.hash.replace(/^#\/?/, '').split('/').map(decodeURIComponent);
    const [p, a, b] = parts;
    $('#header').classList.remove('open'); $('#burger').setAttribute('aria-expanded', 'false');
    const navKey = ['e', 's'].includes(p) ? 'events' : (p || '');
    $$('.nav a').forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#/' + navKey));
    if (!p) pageHome();
    else if (p === 'topics') pageTopics();
    else if (p === 'popular') pagePopular();
    else if (p === 'about') pageAbout();
    else if (p === 'saved') pageSaved();
    else if (p === 'search') pageSearch(a || '');
    else if (p === 'c') pageCategory(a);
    else if (p === 'i') pageInstruction(a, b);
    else if (p === 'k') pageKom(+a || 1, b);
    else if (p === 'events') pageEvents();
    else if (p === 'e') pageEvent(a, b);
    else if (p === 's') pageService(a, b);
    else page404();
    document.title = (p ? '' : '') + 'Як? — Просто про важливе в Україні';
    lucide.createIcons(); refreshSaveUI();
    window.scrollTo(0, 0);
  }

  /* ---------- Глобальні події ---------- */
  document.addEventListener('click', e => {
    const sv = e.target.closest('[data-save]'); if (sv) { toggleSaved(sv.dataset.save); return; }
    const sm = e.target.closest('[data-save-mini]'); if (sm) { toggleSaved(sm.dataset.saveMini); if (location.hash === '#/saved') pageSaved(), lucide.createIcons(), refreshSaveUI(); return; }
    const ac = e.target.closest('[data-acc]');
    if (ac) { const open = ac.getAttribute('aria-expanded') === 'true'; ac.setAttribute('aria-expanded', !open); ac.nextElementSibling.hidden = open; }
  });
  $('#burger').addEventListener('click', () => {
    const h = $('#header'); const o = h.classList.toggle('open'); $('#burger').setAttribute('aria-expanded', o);
  });
  window.addEventListener('hashchange', route);
  route();
})();

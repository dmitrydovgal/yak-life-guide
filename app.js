/* «Як?» — клієнтська логіка сайту: роутер, пошук, збереження, сценарій комуналки */
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
  const stem = w => (w.length > 5 ? w.slice(0, w.length - 2) : (w.length >= 4 ? w.replace(/[аяоеєіиуюїйь]+$/, '') : w));
  /* Розмовні слова → терміни реєстру (людина пише «загубив», у реєстрі — «втрата») */
  const SYN = { 'загубив': ['втрат'], 'загубила': ['втрат'], 'загубили': ['втрат'], 'загубився': ['втрат'], 'втратив': ['втрат'], 'втратила': ['втрат'], 'втратили': ['втрат'],
    'вкрали': ['викрад'], 'id': ['паспорт'], 'id-картку': ['паспорт'], 'id-картка': ['паспорт'], 'айді': ['паспорт'], 'айдішку': ['паспорт'],
    'переселенець': ['переміщен'], 'переселенка': ['переміщен'], 'переселенці': ['переміщен'], 'переселенців': ['переміщен'], 'впо': ['переміщен', 'впо'],
    'зруйноване': ['знищен', 'зруйн'], 'зруйнований': ['знищен', 'зруйн'], 'розбомбили': ['знищен', 'пошкодж'] };
  const alts = t => SYN[t] || [t];
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
      for (const t of toks) { const al = alts(t); if (al.some(a => tw.some(w => wm(a, w)))) sc += 3; else if (al.some(a => fw.some(w => wm(a, w)))) sc += 1; else { sc = -1; break; } }
      if (sc > 0) out.push([sc, id]);
    }
    return out.sort((a, b) => b[0] - a[0]).map(x => x[1]);
  }
  const empty = (title, text, cta) => `<div class="empty">${ic('search-x')}<h3>${esc(title)}</h3><p>${esc(text)}</p>${cta || ''}</div>`;
  const demoNote = `<div class="note">${ic('info')}<p><b>Важливо.</b> Ми пояснюємо простими словами, але це не юридична консультація. Перед зверненням перевірте умови на офіційному сайті.</p></div>`;
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
        <div><h2 class="h2">Найпопулярніші інструкції</h2><ol class="toplist">${pop.map((x, i) => `<li><a href="#/i/${x.id}"><span class="rank">${i + 1}</span><span class="tl-main"><b>${esc(x.title)}</b><small>${esc(catById(x.cat).title)} · ${esc(x.time)}</small></span>${ic('chevron-right', 'chev')}</a></li>`).join('')}</ol></div>
      </section>
      <section class="container home-blog"><div class="h2-row"><h2 class="h2">З блогу</h2><a href="blog/">Усі статті</a></div>
        <ul class="blog-grid">${BLOG.slice(0, 3).map(b => `<li><a class="post-card" href="blog/${b.slug}/"><span class="post-cat">${esc(b.cat)}</span><b>${esc(b.title)}</b><small>${b.min} хв читання</small></a></li>`).join('')}</ul></section>`;
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
      ${faqHtml([['Чи це офіційний сервіс?', 'Ні. «Як?» — незалежний інформаційний гід. Ми пояснюємо, як діяти, й ведемо на офіційні сервіси.'], ['Чи потрібно реєструватися?', 'Ні. Збережені плани й інструкції зберігаються лише на вашому пристрої, у цьому браузері.'], ['Чи можна покладатися на інструкції?', 'Ми складаємо інструкції за офіційними джерелами, але правила іноді змінюються. Перед зверненням перевірте умови на офіційному сайті — посилання є на кожній сторінці.']])}</div>`;
    refreshSaveUI();
  }

  function pageAbout() {
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Про проєкт']])}<h1>Про проєкт</h1>
      <p class="lead">«Як?» — цифровий помічник, який пояснює, як вирішувати повсякденні життєві питання в Україні.</p></div>
      <div class="prose"><h3>Наш принцип</h3><p>Мінімум дій від вас, максимум користі. Ми питаємо лише те, що впливає на результат, і показуємо найкоротший шлях першим.</p>
      <h3>Що це не є</h3><p>Це не державний портал, не платіжний сервіс і не юридична консультація. Матеріали мають інформаційний характер: актуальні умови перевіряйте в офіційних джерелах.</p>
      <h3>Ваші дані</h3><p>Ми не просимо ПІБ, телефон чи паспорт. Збережені плани, інструкції та введена адреса зберігаються лише на вашому пристрої, у цьому браузері.</p></div>
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
      <p class="lead">Плани та інструкції, які ви зберегли на цьому пристрої.</p></div>
      ${list.length ? `<ul class="rows">${list.join('')}</ul>` : empty('Тут поки порожньо', 'Щоб зберегти, натисніть «Зберегти план» на сторінці послуги або «Зберегти інструкцію» в інструкції. Збережене з’явиться тут.', `<a class="btn primary" href="#/topics">Знайти інструкцію</a>`)}</div>`;
    lucide.createIcons(); refreshSaveUI();
  }

  /* Документи й терміни глосарію: documents/search.json (будує _build/sections.py) */
  let docIdx = null;
  async function searchDocs(q) {
    if (!docIdx) docIdx = await fetch('documents/search.json').then(r => r.ok ? r.json() : []);
    const ws = q.toLowerCase().replace(/[’ʼ]/g, "'").split(/\s+/).filter(Boolean);
    return docIdx.filter(x => { const h = (x.t + ' ' + x.a + ' ' + x.d).toLowerCase().replace(/[’ʼ]/g, "'"); return ws.every(w => h.includes(w)); });
  }
  function pageSearch(q) {
    const tok = routeTok;
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Пошук']])}<h1>Результати пошуку</h1></div>
      ${searchField('sp', 'Що вам потрібно зробити?', q)}<div id="sres" class="mt"></div><div id="sres3"></div><div id="sres2"></div></div>`;
    bindSearch('#sp');
    const res = search(q), evs = searchEvents(q);
    $('#sres').innerHTML = `<p class="muted">За запитом «${esc(q)}»: ${res.length + evs.length}</p>` +
      (evs.length ? `<h2 class="h2 sub">Життєві події</h2><ul class="rows">${evs.map(e => `<li class="row-wrap"><a class="row" href="#/e/${e.id}"><span class="row-main"><span class="row-title">${esc(e.title)}</span><span class="row-meta">${e.n} послуг · ${e.aud === 'b' ? 'для бізнесу' : 'для громадян'}</span></span>${ic('chevron-right', 'chev')}</a></li>`).join('')}</ul>` : '') +
      (res.length ? `<h2 class="h2 sub">Інструкції</h2>${insList(res)}` : '');
    $('#sres2').innerHTML = `<p class="muted mt">Шукаємо в реєстрі державних послуг…</p>`;
    lucide.createIcons(); refreshSaveUI();
    searchDocs(q).then(dl => { if (tok !== routeTok || !dl.length) return;
      $('#sres3').innerHTML = `<h2 class="h2 sub">Документи та терміни</h2><ul class="rows">${dl.slice(0, 8).map(x => `<li class="row-wrap"><a class="row" href="${esc(x.u)}"><span class="row-main"><span class="row-title">${esc(x.t)}</span><span class="row-meta">${x.k === 'doc' ? 'Документ' : 'Глосарій'} · ${esc(x.d)}</span></span>${ic('chevron-right', 'chev')}</a></li>`).join('')}</ul>`;
      lucide.createIcons(); }).catch(() => {});
    loadGuide().then(() => {
      if (tok !== routeTok) return;
      const sv = searchServices(q).slice(0, 30);
      $('#sres2').innerHTML = sv.length ? `<h2 class="h2 sub">Державні послуги</h2>${svcList(sv)}` : '';
      if (!res.length && !evs.length && !sv.length) $('#sres').innerHTML += empty('Нічого не знайдено', 'Спробуйте написати інакше, наприклад одним словом: «паспорт», «субсидія», «ФОП». Або перегляньте всі теми.', `<a class="btn primary" href="#/topics">Усі теми</a>`);
      lucide.createIcons(); refreshSaveUI();
    }).catch(() => { if (tok === routeTok) { $('#sres2').innerHTML = ''; if (!res.length && !evs.length) $('#sres').innerHTML += empty('Нічого не знайдено', 'Спробуйте написати інакше, наприклад одним словом: «паспорт», «субсидія», «ФОП». Або перегляньте всі теми.', `<a class="btn primary" href="#/topics">Усі теми</a>`); lucide.createIcons(); } });
  }

  /* ---------- Життєві події (дані Гіду Дія) ---------- */
  const evProg = (n, id, secIdx) => {
    const labels = ['Подія', 'Тема', 'Послуга', 'Інструкція'];
    const href = { 1: '#/events', 2: id ? '#/e/' + id : null, 3: id && secIdx != null ? `#/e/${id}/${secIdx}` : null };
    return `<div class="kprog" aria-label="Прогрес">${labels.map((l, i) => { const s = i + 1, cls = s < n ? 'past' : s === n ? 'cur' : '', h = s < n && href[s]; return h ? `<a href="${h}" class="kp ${cls}"><i>${ic('check')}</i><em>${l}</em></a>` : `<span class="kp ${cls}"${s === n ? ' aria-current="step"' : ''}><i>${s}</i><em>${l}</em></span>`; }).join('')}</div>`;
  };
  let evAud = 'c';
  function pageEvents() {
    app.innerHTML = `<div class="container"><div class="page-head">${crumbs([['Головна', '#/'], ['Життєві події']])}
      <h1>Життєві події</h1><p class="lead">Оберіть ситуацію, і ми покажемо державні послуги, які для неї потрібні: документи, строки, вартість і куди звертатися.</p></div>
      <form class="searchbox plain" id="evf" autocomplete="off" role="search">${ic('search', 'lead')}<input id="evq" type="text" placeholder="Знайти державну послугу, наприклад «свідоцтво про народження»" aria-label="Пошук державної послуги" /></form>
      <div id="evtabs" class="chips" role="tablist"><button class="chip" data-a="c" role="tab">Для громадян</button><button class="chip" data-a="b" role="tab">Для бізнесу</button></div>
      <div id="evres"></div>
      <p class="source">Дані: <a href="https://guide.diia.gov.ua/" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a> (відкритий реєстр, CC BY 4.0), текст скорочено.</p></div>`;
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

  /* ---------- Послуга: персональний покроковий флоу ---------- */
  const selStore = () => store.get('yak_sel', {});
  const getSel = sid => selStore()[sid] || {};
  const setSel = (sid, v) => { const a = selStore(); a[sid] = Object.assign({}, a[sid], v); store.set('yak_sel', a); };
  const ADDR_RX = /місця проживання|реєстрац\S* місця|адрес|житл|квартир|будинк|земельн|нерухом|комунальн|субсид|прописк/i;
  const shorten = (t, n) => { t = String(t || ''); return t.length <= n ? t : t.slice(0, Math.max(t.lastIndexOf(' ', n), n * .6)).replace(/[\s,;.]+$/, '') + '…'; };
  const mapUrl = q => 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(q);

  function svcVariants(s) {
    const parse = str => { const m = {}; String(str || '').split(';').map(x => x.trim()).filter(Boolean).forEach(p => { const i = p.indexOf(': '); if (i > 0) m[p.slice(0, i)] = p.slice(i + 2); }); return m; };
    const c = parse(s.c), t = parse(s.t);
    const labels = [...new Set([...Object.keys(c), ...Object.keys(t)])];
    return labels.length > 1 ? labels.map(l => ({ id: l, label: l, cost: c[l] || '', time: t[l] || '' })) : [];
  }
  function svcWays(s) {
    const o = [];
    if (s.l || s.w.includes('Електронно')) o.push({ id: 'online', label: 'Онлайн', desc: s.l ? 'Через електронний сервіс, без походів в установу' : 'Дистанційно, якщо орган підтримує такий спосіб', icon: 'smartphone' });
    if (s.w.includes('Особисто') || !o.length) o.push({ id: 'office', label: 'Особисто в органі', desc: 'Прийти з документами до органу, що надає послугу', icon: 'building-2' });
    if (s.w.includes('Поштою')) o.push({ id: 'mail', label: 'Письмово, поштою', desc: 'Надіслати заяву та копії документів листом', icon: 'mail' });
    return o;
  }
  function svcPlan(s) {
    const ways = svcWays(s), vars = svcVariants(s);
    const needsPlace = ways.some(w => w.id !== 'online');
    const needsAddr = needsPlace && ADDR_RX.test([s.n, s.f, s.d, s.s].join(' '));
    const choice = ways.length > 1 || vars.length > 1;
    const steps = [].concat(needsPlace ? ['place'] : [], needsAddr ? ['addr'] : [], choice ? ['choice'] : [], ['result']);
    return { ways, vars, steps, needsPlace, needsAddr };
  }
  const SVC_LABELS = { place: 'Місто', addr: 'Адреса', choice: 'Уточнення', result: 'Інструкція' };
  function svcMissing(plan, st, sel) {
    for (const k of plan.steps) {
      if (k === 'place' && !st.city) return k;
      if (k === 'addr' && !(st.street && st.house && st.oblast)) return k;
      if (k === 'choice' && ((plan.ways.length > 1 && !sel.way) || (plan.vars.length > 1 && !sel.variant))) return k;
    }
    return null;
  }
  const svcAddrLine = st => [st.oblast && st.oblast !== 'м. Київ' ? st.oblast + ' обл.' : '', st.city ? (st.oblast === 'м. Київ' ? '' : 'м. ') + st.city : '', st.street, st.house ? 'буд. ' + st.house : '', st.flat ? 'кв. ' + st.flat : ''].filter(Boolean).join(', ');
  const svcProg = (plan, cur, base) => {
    const idx = plan.steps.indexOf(cur);
    return `<div class="kprog" aria-label="Прогрес">${plan.steps.map((k, i) => {
      const cls = i < idx ? 'past' : i === idx ? 'cur' : '';
      const inner = `<i>${i < idx ? ic('check') : i + 1}</i><em>${SVC_LABELS[k]}</em>`;
      return i < idx ? `<a class="kp ${cls}" href="${base}/${k}">${inner}</a>` : `<span class="kp ${cls}"${i === idx ? ' aria-current="step"' : ''}>${inner}</span>`;
    }).join('')}</div>`;
  };

  /* Побудова персональних кроків інструкції */
  function svcSteps(s, ctx) {
    const { st, way, variant } = ctx, city = st.city || '';
    const out = [];
    const prov = s.v[0] || 'орган, що надає послугу';
    const provShort = shorten(prov, 70);
    const guideUrl = 'https://guide.diia.gov.ua/register/' + ctx.sid + '/';
    out.push({ t: 'Підготуйте документи', d: s.i.length ? 'Вам знадобляться (деякі лише в окремих випадках, уточніть в органі):' : 'Окремий перелік документів у реєстрі не вказано. Уточніть його в органі перед візитом.', list: s.i });
    if (way === 'online') {
      out.push({ t: 'Відкрийте електронний сервіс', d: s.l ? 'Подайте заяву дистанційно. Сервіс сам підкаже, які дані ввести, і яку ідентифікацію пройти.' : 'Для цієї послуги окремого онлайн-сервісу в реєстрі не вказано. Перегляньте послуги на порталі Дія або уточніть в органі, чи можна подати заяву дистанційно.', actions: [s.l ? { label: 'Відкрити сервіс', href: s.l } : { label: 'Портал Дія', href: 'https://diia.gov.ua/services' }] });
      out.push({ t: 'Заповніть заяву', d: [st.name ? `Заявник: ${st.name}.` : '', svcAddrLine(st) ? `Якщо запитають адресу, вкажіть: ${svcAddrLine(st)}.` : 'Вкажіть дані, які запитає сервіс.', 'Уважно перевірте дані перед відправленням.'].filter(Boolean).join(' ') });
      if (s.i.length) out.push({ t: 'Додайте документи', d: 'Додайте документи з переліку вище, якщо сервіс їх запитує. Частину даних сервіс може підтягнути сам.' });
    } else if (way === 'mail') {
      out.push({ t: `Дізнайтеся адресу органу${city ? ' у місті ' + city : ''}`, d: `Куди надсилати: ${provShort}.`, actions: [{ label: 'Знайти на карті', href: mapUrl(provShort + (city ? ' ' + city : '')) }] });
      out.push({ t: 'Надішліть пакет документів', d: 'Надішліть заяву та копії документів рекомендованим листом з описом вкладення. Збережіть квитанцію про відправлення.' });
    } else {
      const acts = [{ label: 'Знайти на карті', href: mapUrl(provShort + (city ? ' ' + city : '')) }];
      if (s.v.some(v => /ЦНАП|адміністративних послуг/i.test(v))) acts.push({ label: 'Реєстр ЦНАП', href: 'https://guide.diia.gov.ua/asc/' });
      out.push({ t: `Знайдіть орган${city ? ' у місті ' + city : ''}`, d: `Звертайтеся до: ${s.v.length ? s.v.join('; ') : prov}.`, actions: acts });
      out.push({ t: 'Перевірте години роботи та запис', d: 'Зателефонуйте або перегляньте сайт органу: чи потрібен попередній запис, у які дні й години приймають.' });
      out.push({ t: 'Подайте заяву', d: `Візьміть паспорт, ІПН та оригінали документів з переліку.${st.name ? ' Заява оформлюється на: ' + st.name + '.' : ''}${svcAddrLine(st) ? ' Адреса в заяві: ' + svcAddrLine(st) + '.' : ''}` });
    }
    const cost = variant ? variant.cost : s.c, time = variant ? variant.time : s.t;
    if (cost && !/^безоплатн/i.test(cost)) out.push({ t: 'Сплатіть послугу', d: `Вартість: ${cost}. Реквізити для оплати надасть орган або електронний сервіс.` });
    out.push({ t: 'Дочекайтеся результату', d: time ? `Строк надання: ${time}.` : 'Строк надання уточніть в органі.' });
    const prods = s.p.filter(x => !/^відмов/i.test(x));
    if (prods.length) out.push({ t: 'Отримайте результат', d: `Ви отримаєте: ${prods.join('; ')}.` });
    out.push({ t: 'Якщо відмовили', d: 'Ви маєте право оскаржити рішення. Підстави відмови та порядок оскарження наведено на сторінці послуги в Гіді Дія.', actions: [{ label: 'Сторінка послуги', href: guideUrl }] });
    return out;
  }

    /* --- Крок: місто (спільний) --- */
  function stepPlace({ st, mount, actions, go, nextK }) {
      let picked = st.city || '';
      mount(`<h2 class="h2">Оберіть ваше місто</h2><p class="muted sp">Від міста залежить, до якого органу звертатися. Підійде будь-яке місто чи село України.</p>
        <form id="f" novalidate autocomplete="off">
        <div class="field"><label for="city">Місто або село</label><div class="searchbox plain">${ic('map-pin', 'lead')}<input id="city" type="text" value="${esc(picked)}" placeholder="Почніть вводити назву" aria-describedby="cerr" /></div><p class="err" id="cerr" hidden></p></div>
        <p class="small-label">Приклади</p><div class="chips" id="ex">${['Київ', 'Кривий Ріг', 'Дніпро', 'Львів', 'Одеса', 'Харків'].map(c => `<button type="button" class="chip${c === picked ? ' on' : ''}" data-c="${c}">${c}</button>`).join('')}</div>
        <ul class="cities" id="cl"></ul>${actions('Продовжити')}</form>`);
      const inp = $('#city'), err = $('#cerr');
      const drawList = () => {
        const q = norm(inp.value.trim());
        const res = q ? CITIES.filter(c => norm(c[0]).includes(q) && c[0] !== inp.value.trim()).slice(0, 6) : [];
        $('#cl').innerHTML = res.map(c => `<li><button type="button" data-c="${c[0]}">${ic('map-pin', 'sm')}<span>${c[0]}</span><small>${c[1] === 'м. Київ' ? 'місто' : c[1] + ' обл.'}</small></button></li>`).join('');
        lucide.createIcons();
      };
      const pick = c => { inp.value = c; err.hidden = true; inp.classList.remove('bad'); $$('#ex .chip').forEach(b => b.classList.toggle('on', b.dataset.c === c)); drawList(); };
      inp.addEventListener('input', () => { err.hidden = true; inp.classList.remove('bad'); $$('#ex .chip').forEach(b => b.classList.toggle('on', b.dataset.c === inp.value.trim())); drawList(); });
      $('#f').addEventListener('click', e => { const b = e.target.closest('[data-c]'); if (b) pick(b.dataset.c); });
      $('#f').addEventListener('submit', e => {
        e.preventDefault();
        const v = inp.value.trim().replace(/\s+/g, ' ');
        const msg = !v ? 'Вкажіть ваше місто.' : v.length < 2 ? 'Назва занадто коротка.' : !/^[A-Za-zА-Яа-яІіЇїЄєҐґ'’ʼ.\-\s]+$/.test(v) ? 'Використовуйте лише літери, пробіли та дефіс.' : '';
        if (msg) { err.textContent = msg; err.hidden = false; inp.classList.add('bad'); inp.focus(); return; }
        const known = CITIES.find(c => c[0].toLowerCase() === v.toLowerCase());
        const ns = Object.assign({}, st);
        if (known) { if (ns.city !== known[0]) { ns.city = known[0]; ns.oblast = known[1]; } }
        else if (ns.city !== v) { ns.city = v; ns.oblast = ''; }
        kSave(ns); go(nextK);
      });
      return;
    }


    /* --- Крок: адреса і дані заявника --- */
  function stepAddr({ st, mount, actions, go, nextK }) {
      mount(`<h2 class="h2">Вкажіть адресу</h2><p class="muted sp">Адреса потрібна, щоб підставити її в інструкцію. Дані зберігаються лише у вашому браузері.</p>
        <form id="f" novalidate autocomplete="off">
        <div class="grid2"><div class="field"><label for="oblast">Область</label><select id="oblast"><option value="">Оберіть область</option>${OBLASTS.map(o => `<option${o === st.oblast ? ' selected' : ''}>${o}</option>`).join('')}</select><p class="err" hidden></p></div>
        <div class="field"><label for="fcity">Місто</label><input id="fcity" type="text" value="${esc(st.city || '')}" /><p class="err" hidden></p></div></div>
        <div class="field"><label for="street">Вулиця</label><input id="street" type="text" placeholder="Наприклад, Соборна" value="${esc(st.street || '')}" /><p class="err" hidden></p></div>
        <div class="grid2"><div class="field"><label for="house">Будинок</label><input id="house" type="text" placeholder="Наприклад, 12А" value="${esc(st.house || '')}" /><p class="err" hidden></p></div>
        <div class="field"><label for="flat">Квартира <span class="opt-l">необовʼязково</span></label><input id="flat" type="text" inputmode="numeric" placeholder="Наприклад, 45" value="${esc(st.flat || '')}" /><p class="err" hidden></p></div></div>
        <div class="field"><label for="name">Ваше імʼя для заяви <span class="opt-l">необовʼязково</span></label><input id="name" type="text" placeholder="Прізвище Імʼя По батькові" value="${esc(st.name || '')}" /><p class="err" hidden></p>
        <p class="muted sp2">Не обовʼязково. Імʼя лише підставляється в інструкцію й нікуди не надсилається.</p></div>
        ${actions('Показати інструкцію', 'list-checks')}</form>`);
      const L = "A-Za-zА-Яа-яІіЇїЄєҐґ'’ʼ";
      const rules = {
        oblast: v => v ? '' : 'Оберіть область.',
        fcity: v => v.length < 2 ? 'Вкажіть місто.' : '',
        street: v => v.length < 2 ? 'Вкажіть назву вулиці.' : /^[\d\s]+$/.test(v) ? 'Вулиця не може складатися лише з цифр.' : '',
        house: v => !v ? 'Вкажіть номер будинку.' : /^\d{1,4}\s?[А-Яа-яІіЇїЄєҐґA-Za-z]?(\/\d{1,3})?(-[А-Яа-яІіЇїЄєҐґA-Za-z0-9]{1,3})?$/.test(v) ? '' : 'Вкажіть номер у форматі 12, 12А або 12/2.',
        flat: v => !v || /^\d{1,4}$/.test(v) ? '' : 'Номер квартири: лише цифри.',
        name: v => !v || new RegExp(`^[${L}.\\-\\s]{2,80}$`).test(v) ? '' : 'Використовуйте лише літери, пробіли та дефіс.'
      };
      const check = id => { const el = $('#' + id), m = rules[id](el.value.trim()), p = el.parentElement.querySelector('.err'); p.textContent = m; p.hidden = !m; el.classList.toggle('bad', !!m); return !m; };
      Object.keys(rules).forEach(id => { const el = $('#' + id); el.addEventListener('blur', () => check(id)); el.addEventListener('input', () => { if (el.classList.contains('bad')) check(id); }); });
      $('#f').addEventListener('submit', e => {
        e.preventDefault();
        if (!Object.keys(rules).map(check).every(Boolean)) { const b = $('.bad'); if (b) b.focus(); return; }
        kSave({ oblast: $('#oblast').value, city: $('#fcity').value.trim(), street: $('#street').value.trim(), house: $('#house').value.trim(), flat: $('#flat').value.trim(), name: $('#name').value.trim().replace(/\s+/g, ' ') });
        go(nextK);
      });
      return;
    }


  let svcMap = null;
  async function pageService(sid, eid, step) {
    const tok = routeTok;
    app.innerHTML = loadingHtml; lucide.createIcons();
    /* Покроковий сценарій послуги живе на її статичній сторінці (journey.js) */
    try {
      if (!svcMap) svcMap = await fetch('s/map.json').then(r => r.ok ? r.json() : {});
      if (tok !== routeTok) return;
      if (svcMap[sid]) { location.replace(new URL(svcMap[sid], location.href.split('#')[0]).href); return; }
    } catch (e) { /* немає мапи — показуємо старий сценарій нижче */ }
    try { await loadGuide(); } catch (e) { if (tok === routeTok) loadErr(); return; }
    if (tok !== routeTok) return;
    const s = GUIDE_SERVICES[sid]; if (!s) return page404();
    if (eid === '-') eid = '';
    const ev = eid && evById(eid);
    const plan = svcPlan(s), st = kState(), sel = getSel(sid);
    const base = `#/s/${sid}/${eid || '-'}`;
    const cur = plan.steps.includes(step) ? step : plan.steps[0];
    const miss = svcMissing(plan, st, sel);
    if (miss && plan.steps.indexOf(miss) < plan.steps.indexOf(cur)) { location.replace(`${base}/${miss}`); return; }
    const idx = plan.steps.indexOf(cur), nextK = plan.steps[idx + 1], prevK = plan.steps[idx - 1];
    const backHref = prevK ? `${base}/${prevK}` : (ev ? '#/e/' + ev.id : '#/events');
    const bc = [['Головна', '#/'], ['Життєві події', '#/events']];
    if (ev) bc.push([ev.title, '#/e/' + ev.id]);
    bc.push([s.n]);
    const guideUrl = 'https://guide.diia.gov.ua/register/' + sid + '/';
    const variant = plan.vars.find(v => v.id === sel.variant) || null;
    const way = sel.way && plan.ways.some(w => w.id === sel.way) ? sel.way : plan.ways[0].id;
    const cost = variant ? variant.cost : s.c, time = variant ? variant.time : s.t;
    const head = `<div class="page-head">${crumbs(bc)}
      <div class="title-row"><h1>${esc(s.n)}</h1>${saveBtn('s:' + sid)}</div>
      <p class="lead">${esc(shorten(s.d || s.f, 230))}</p>
      <div class="meta">${time ? `<span>${ic('clock')} ${esc(shorten(time, 70))}</span>` : ''}${cost ? `<span>${ic('banknote')} ${esc(shorten(cost, 70))}</span>` : ''}</div>
      ${plan.steps.length > 1 ? svcProg(plan, cur, base) : ''}</div>`;
    const source = `<p class="source">Джерело: <a href="${guideUrl}" target="_blank" rel="noopener noreferrer">Гід з державних послуг</a>, послуга № ${esc(sid)} (CC BY 4.0, текст скорочено). Кроки сформовано автоматично за даними реєстру, дата оновлення: ${CHECKED}.</p>`;
    const actions = (nextLabel, nextIcon) => `<div class="actions"><a class="btn ghost" href="${backHref}">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">${nextLabel} ${ic(nextIcon || 'arrow-right')}</button></div>`;
    const go = k => { location.hash = `${base}/${k}`; };
    const mount = html => { app.innerHTML = `<article class="container narrow-m">${head}${html}</article>`; lucide.createIcons(); refreshSaveUI(); };

    if (cur === 'place') return stepPlace({ st, mount, actions, go, nextK });
    if (cur === 'addr') return stepAddr({ st, mount, actions, go, nextK });

    /* --- Крок: уточнення (спосіб і варіант строку) --- */
    if (cur === 'choice') {
      const radio = (name, o, checked) => `<label class="opt"><input type="radio" name="${name}" value="${esc(o.id)}"${checked ? ' checked' : ''}>${o.icon ? ic(o.icon, 'oi') : ''}<span><b>${esc(o.label)}</b><small>${esc(o.desc)}</small></span></label>`;
      mount(`<h2 class="h2">Уточніть, як вам зручніше</h2><p class="muted sp">Від відповідей залежать кроки, вартість і строк.</p>
        <form id="f" novalidate>
        ${plan.ways.length > 1 ? `<fieldset class="grp"><legend>Спосіб подачі</legend><div class="opts">${plan.ways.map((w, i) => radio('way', w, sel.way ? sel.way === w.id : false)).join('')}</div><p class="err" hidden id="e-way">Оберіть спосіб подачі.</p></fieldset>` : ''}
        ${plan.vars.length > 1 ? `<fieldset class="grp"><legend>Варіант надання</legend><div class="opts">${plan.vars.map(v => radio('variant', { id: v.id, label: v.label, desc: [v.time && 'Строк: ' + v.time, v.cost && 'Вартість: ' + v.cost].filter(Boolean).join(' · ') || 'Без додаткових умов' }, sel.variant === v.id)).join('')}</div><p class="err" hidden id="e-variant">Оберіть варіант.</p></fieldset>` : ''}
        ${actions('Показати інструкцію', 'list-checks')}</form>`);
      const f = $('#f');
      f.addEventListener('change', e => { const er = $('#e-' + e.target.name); if (er) er.hidden = true; });
      f.addEventListener('submit', e => {
        e.preventDefault();
        const v = {}; let ok = true;
        if (plan.ways.length > 1) { if (!f.way.value) { $('#e-way').hidden = false; ok = false; } else v.way = f.way.value; } else v.way = plan.ways[0].id;
        if (plan.vars.length > 1) { if (!f.variant.value) { $('#e-variant').hidden = false; ok = false; } else v.variant = f.variant.value; }
        if (!ok) return;
        setSel(sid, v); go(nextK);
      });
      return;
    }

    /* --- Результат: персональна інструкція --- */
    const wayObj = plan.ways.find(w => w.id === way);
    const steps = svcSteps(s, { sid, st: plan.needsPlace ? st : {}, way, variant });
    const prov = s.v[0] ? shorten(s.v[0], 70) : '';
    const cta = way === 'online' ? (s.l ? extLink('Відкрити сервіс', s.l, 'btn primary btn-lg') : extLink('Відкрити портал Дія', 'https://diia.gov.ua/services', 'btn primary btn-lg'))
      : `<a class="btn primary btn-lg" href="${mapUrl((prov || 'ЦНАП') + (st.city ? ' ' + st.city : ''))}" target="_blank" rel="noopener noreferrer">Знайти орган на карті${ic('map-pin')}</a>`;
    const summary = [`Послуга: ${s.n}`, st.name && plan.needsAddr ? `Заявник: ${st.name}` : '', plan.needsPlace && svcAddrLine(st) ? `Адреса: ${svcAddrLine(st)}` : '', `Спосіб: ${wayObj.label}`, variant ? `Варіант: ${variant.label}` : '', time ? `Строк: ${time}` : '', cost ? `Вартість: ${cost}` : '', s.i.length ? 'Документи:\n- ' + s.i.join('\n- ') : ''].filter(Boolean).join('\n');
    const answers = [plan.needsPlace && st.city ? [`Місто: ${st.city}`, `${base}/place`] : null, plan.needsAddr ? [svcAddrLine(st), `${base}/addr`] : null, plan.steps.includes('choice') ? [`${wayObj.label}${variant ? ' · ' + variant.label : ''}`, `${base}/choice`] : null].filter(Boolean);
    mount(`<div class="addr">${ic('map-pin')}<span><b>Ваша інструкція.</b> ${esc(answers.map(a => a[0]).join(' | ') || 'Для всієї України')}</span>${answers.length ? `<a href="${answers[0][1]}">Змінити</a>` : ''}</div>
      ${s.p.some(x => !/^відмов/i.test(x)) ? `<div class="why">${ic('file-check')}<p><b>Що ви отримаєте.</b> ${esc(s.p.filter(x => !/^відмов/i.test(x)).join('; '))}</p></div>` : ''}
      <h2 class="h2 sub">Покрокова інструкція</h2>
      <ol class="osteps">${steps.map((x, i) => `<li class="ostep"><span class="num">${i + 1}</span><div class="body"><b>${esc(x.t)}</b><span>${esc(x.d)}</span>${x.list && x.list.length ? `<ul class="docs">${x.list.map(d => `<li>${ic('file-text')}<span>${esc(d)}</span></li>`).join('')}</ul>` : ''}${x.actions ? `<div class="oact">${x.actions.map(a => extLink(a.label, a.href, 'btn ghost sm-btn')).join('')}</div>` : ''}</div></li>`).join('')}</ol>
      <div class="cta-row">${cta}</div>
      <div class="note neutral">${ic('info')}<p>Подача заяви відбувається в органі або на сайті сервісу, а не на «Як?». Тут лише підказки.</p></div>
      <section class="sum"><div class="h2-row"><h2 class="h2">Дані для заяви</h2></div><pre id="sumtxt">${esc(summary)}</pre>
        <div class="oact"><button class="btn ghost" id="copy" type="button">${ic('copy')} Копіювати</button><button class="btn ghost" id="print" type="button">${ic('printer')} Друкувати</button></div></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml([['Що, якщо мені відмовили?', 'Підстави відмови та порядок оскарження наведено на сторінці послуги в Гіді Дія. Рішення можна оскаржити в установленому порядку.'], ['Чи однакові умови по всій країні?', 'Загальнодержавні умови однакові, але місцеві органи можуть мати власні вимоги. Уточніть у відповідному органі.'], ['Де знайти нормативну базу?', 'На сторінці послуги в Гіді Дія є підрозділи «Як отримати і що для цього потрібно» та «Нормативна база».']])}</section>
      <div class="links">${extLink('Повна інформація в Гіді Дія', guideUrl)}${s.l && way !== 'online' ? extLink('Онлайн-сервіс', s.l) : ''}${extLink('Портал Дія', 'https://diia.gov.ua/')}</div>
      ${demoNote}${source}
      <div class="actions"><a class="btn ghost" href="${backHref}">${ic('arrow-left')} Назад</a><a class="btn ghost" href="${ev ? '#/e/' + ev.id : '#/events'}">До списку послуг</a></div>`);
    $('#copy').addEventListener('click', () => {
      const t = $('#sumtxt').textContent;
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => toast('Дані скопійовано', 'ok'), () => { const r = document.createRange(); r.selectNodeContents($('#sumtxt')); const sl = getSelection(); sl.removeAllRanges(); sl.addRange(r); toast('Виділено. Натисніть Ctrl+C'); });
    });
    $('#print').addEventListener('click', () => window.print());
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
      $('#cres').innerHTML = list.length ? insList(list) : empty('У цьому розділі нічого не знайдено', 'Спробуйте написати інакше, наприклад одним словом: «паспорт», «субсидія», «ФОП». Або перегляньте всі теми.', `<a class="btn ghost" href="#/search/${encodeURIComponent(q)}">Шукати на всьому сайті</a>`);
      refreshSaveUI();
    };
    bindFilter('#cq', draw); draw();
  }

  const saveBtn = id => `<button class="btn ghost save" type="button" data-save="${id}"></button>`;

  /* ---------- Інструкції: той самий персональний покроковий флоу ---------- */
  const iselAll = () => store.get('yak_isel', {});
  const setISel = (id, v) => { const a = iselAll(); a[id] = Object.assign({}, a[id], v); store.set('yak_isel', a); };
  function insPlan(ins) {
    const m = INS_FLOW[ins.id] || {};
    const place = !!(m.where || m.addr || m.use), addr = !!m.addr, choice = !!ins.wizard;
    return { m, place, addr, choice, steps: [].concat(place ? ['place'] : [], addr ? ['addr'] : [], choice ? ['choice'] : [], ['result']) };
  }

  function pageInstruction(id, a2) {
    const base0 = INS[id]; if (!base0) return page404();
    if (id === 'fop-group' || id === 'fop-open') { location.replace(new URL('i/' + id + '/', location.href.split('#')[0]).href); return; } /* глибокий сценарій зі статичної сторінки */
    if (base0.flow === 'komunalka') return pageKom(1);
    const cat = catById(base0.cat), plan = insPlan(base0);
    if (base0.wizard && base0.wizard.options.some(o => o.id === a2)) { setISel(id, { opt: a2 }); location.replace(`#/i/${id}/result`); return; }
    const st = kState(), sel = iselAll()[id] || {};
    const opt = base0.wizard ? base0.wizard.options.find(o => o.id === sel.opt) : null;
    const base = '#/i/' + id;
    const cur = plan.steps.includes(a2) ? a2 : plan.steps[0];
    const miss = plan.steps.find(k => (k === 'place' && !st.city) || (k === 'addr' && !(st.street && st.house && st.oblast)) || (k === 'choice' && !opt));
    if (miss && plan.steps.indexOf(miss) < plan.steps.indexOf(cur)) { location.replace(`${base}/${miss}`); return; }
    const idx = plan.steps.indexOf(cur), nextK = plan.steps[idx + 1], prevK = plan.steps[idx - 1];
    const backHref = prevK ? `${base}/${prevK}` : '#/c/' + cat.id;
    const bc = [['Головна', '#/'], [cat.title, '#/c/' + cat.id], [base0.title]];
    const mount = html => { app.innerHTML = `<article class="container narrow-m"><div class="page-head">${crumbs(bc)}
      <div class="title-row"><h1>${esc(base0.title)}</h1>${saveBtn(id)}</div><p class="lead">${esc(base0.summary)}</p>
      <div class="meta"><span>${ic('clock')} Приблизно ${esc((opt && opt.over.time) || base0.time)}</span></div>
      ${plan.steps.length > 1 ? svcProg(plan, cur, base) : ''}</div>${html}</article>`; lucide.createIcons(); refreshSaveUI(); window.scrollTo(0, 0); };
    const actions = (label, icn) => `<div class="actions"><a class="btn ghost" href="${backHref}">${ic('arrow-left')} Назад</a><button class="btn primary" type="submit">${label} ${ic(icn || 'arrow-right')}</button></div>`;
    const go = k => { location.hash = `${base}/${k}`; };

    if (cur === 'place') return stepPlace({ st, mount, actions, go, nextK });
    if (cur === 'addr') return stepAddr({ st, mount, actions, go, nextK });
    if (cur === 'choice') {
      const w = base0.wizard;
      mount(`<h2 class="h2">${esc(w.q)}</h2><p class="muted sp">${esc(w.sub)}</p>
        <form id="f" novalidate><div class="opts" role="radiogroup" aria-label="${esc(w.q)}">${w.options.map(o => `<label class="opt"><input type="radio" name="o" value="${o.id}"${sel.opt === o.id ? ' checked' : ''}>${ic(o.icon, 'oi')}<span><b>${esc(o.label)}</b><small>${esc(o.desc)}</small></span></label>`).join('')}</div>
        <p class="err" id="cerr" hidden>Оберіть один із варіантів, щоб продовжити.</p>${actions('Показати інструкцію', 'list-checks')}</form>`);
      const f = $('#f');
      f.addEventListener('change', () => { $('#cerr').hidden = true; });
      f.addEventListener('submit', e => { e.preventDefault(); if (!f.o.value) { $('#cerr').hidden = false; return; } setISel(id, { opt: f.o.value }); go(nextK); });
      return;
    }

    /* --- Результат --- */
    let ins = base0;
    if (opt) { const o = Object.assign({}, opt.over); if (o.steps) o.steps = o.steps.map(s => (typeof s === 'string' ? s.split('|') : s)); if (o.links) o.links = o.links.map(l => (typeof l === 'string' ? l.split('|') : l)); ins = Object.assign({}, base0, o); }
    const m = plan.m, city = st.city || '';
    const steps = ins.steps.map(s => ({ t: s[0], d: s[1] || '' }));
    const pre = [];
    if (m.use && plan.addr && svcAddrLine(st)) pre.push({ t: 'Вкажіть вашу адресу', d: `${svcAddrLine(st)}. ${m.use}` });
    if (m.where && city) pre.push({ t: `Знайдіть ${m.where} у місті ${city}`, d: 'Перевірте адресу, години роботи та чи потрібен попередній запис.', actions: [{ label: 'Знайти на карті', href: mapUrl(m.where + ' ' + city) }] });
    const all = pre.concat(steps);
    const answers = [plan.place && city ? [plan.addr ? svcAddrLine(st) : 'Місто: ' + city, `${base}/${plan.addr ? 'addr' : 'place'}`] : null, opt ? [opt.label, `${base}/choice`] : null].filter(Boolean);
    const summary = [`Інструкція: ${base0.title}`, opt ? `Ситуація: ${opt.label}` : '', plan.place && city ? `Адреса: ${plan.addr ? svcAddrLine(st) : city}` : '', plan.addr && st.name ? `Заявник: ${st.name}` : '', `Орієнтовний час: ${ins.time}`, ins.needs.length ? 'Документи:\n- ' + ins.needs.join('\n- ') : ''].filter(Boolean).join('\n');
    const cta = m.where && city ? `<a class="btn primary btn-lg" href="${mapUrl(m.where + ' ' + city)}" target="_blank" rel="noopener noreferrer">Знайти ${esc(m.where)} на карті${ic('map-pin')}</a>` : (ins.links[0] ? extLink('Відкрити: ' + ins.links[0][0], ins.links[0][1], 'btn primary btn-lg') : '');
    mount(`${answers.length ? `<div class="addr">${ic('map-pin')}<span><b>Ваша інструкція.</b> ${esc(answers.map(x => x[0]).join(' | '))}</span><a href="${answers[0][1]}">Змінити</a></div>` : ''}
      <section><h2 class="h2">Що знадобиться</h2><ul class="docs">${ins.needs.map(n => `<li>${ic('file-text')}<span>${esc(n)}</span></li>`).join('')}</ul></section>
      <h2 class="h2 sub">Покрокова інструкція</h2>
      <ol class="osteps">${all.map((x, i) => `<li class="ostep"><span class="num">${i + 1}</span><div class="body"><b>${esc(x.t)}</b><span>${esc(x.d)}</span>${x.actions ? `<div class="oact">${x.actions.map(a => extLink(a.label, a.href, 'btn ghost sm-btn')).join('')}</div>` : ''}</div></li>`).join('')}</ol>
      ${cta ? `<div class="cta-row">${cta}</div>` : ''}
      <div class="note neutral">${ic('info')}<p>Подача документів відбувається в органі або на сайті сервісу, а не на «Як?». Тут лише підказки.</p></div>
      <section class="sum"><div class="h2-row"><h2 class="h2">Дані для заяви</h2></div><pre id="sumtxt">${esc(summary)}</pre>
        <div class="oact"><button class="btn ghost" id="copy" type="button">${ic('copy')} Копіювати</button><button class="btn ghost" id="print" type="button">${ic('printer')} Друкувати</button></div></section>
      <section><h2 class="h2">Можливі способи</h2><div class="methods">${ins.methods.map((x, i) => `<div class="method">${i === 0 ? '<span class="tag">Найпростіший</span>' : ''}<b>${esc(x[0])}</b><p>${esc(x[1])}</p></div>`).join('')}</div></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml(ins.faq)}</section>
      <section><h2 class="h2">Корисні офіційні посилання</h2><div class="links">${ins.links.map(l => extLink(l[0], l[1])).join('')}</div></section>
      ${demoNote}
      <p class="checked">${ic('calendar-check')} Дата оновлення інформації: ${CHECKED}</p>
      <div class="actions"><a class="btn ghost" href="${backHref}">${ic('arrow-left')} Назад</a><a class="btn ghost" href="#/c/${cat.id}">До розділу «${esc(cat.title)}»</a></div>`);
    $('#copy').addEventListener('click', () => {
      const t = $('#sumtxt').textContent;
      (navigator.clipboard ? navigator.clipboard.writeText(t) : Promise.reject()).then(() => toast('Дані скопійовано', 'ok'), () => { const r = document.createRange(); r.selectNodeContents($('#sumtxt')); const sl = getSelection(); sl.removeAllRanges(); sl.addRange(r); toast('Виділено. Натисніть Ctrl+C'); });
    });
    $('#print').addEventListener('click', () => window.print());
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
        : `<li class="none">${ic('search-x', 'sm')}<span>Такого міста немає в списку. Оберіть місто з прикладів або зі списку.</span></li>`) : '';
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
    const EP_CITIES = ['Київ', 'Житомир', 'Одеса', 'Миколаїв', 'Івано-Франківськ'];
    const epOk = EP_CITIES.includes(st.city);
    const order = (epOk ? ['easypay', 'privat24', 'portmone'] : ['portmone', 'privat24', 'easypay']).map(k => SERVICES[k]);
    const local = LOCAL_PROVIDERS[st.city];
    app.innerHTML = `<div class="container narrow-l"><div class="page-head">${kCrumbs()}${kProgress(3, st)}
      <h1>Оберіть найпростіший спосіб оплати</h1><p class="lead">Ми підібрали доступні варіанти для вашого міста та адреси.</p>
      <div class="addr">${ic('map-pin')}<span>${esc(addrLine(st))}</span><a href="#/k/2">Змінити</a></div></div>
      <div class="note">${ic('info')}<p><b>Орієнтовний підбір.</b> Результати не є перевіркою в реальному часі постачальників, і ми не стверджуємо, що кожен сервіс підтримує всі рахунки за вашою адресою.</p></div>
      <div class="svc-list">${order.map(s => `<section class="svc${s === order[0] ? ' rec' : ''}">
        ${s === order[0] ? '<span class="tag">Найпростіший варіант</span>' : ''}
        <div class="svc-head"><span class="svc-ic">${ic(s.icon)}</span><h2>${s.name}</h2></div>
        <p>${esc(s.desc)}</p>
        <p class="svc-why">${ic('lightbulb')}<span><b>Чому пропонуємо:</b> ${esc(s.why)}</span></p>
        ${s.id === 'easypay' && !epOk ? `<p class="svc-why warn">${ic('triangle-alert')}<span>На сторінці сервісу пошук за адресою заявлено для: ${EP_CITIES.join(', ')}. Для міста ${esc(st.city)} він може не спрацювати, тому цей варіант не перший.</span></p>` : ''}
        <div class="pc"><div><h4>Переваги</h4><ul class="pros">${s.pros.map(x => `<li>${ic('check')}${esc(x)}</li>`).join('')}</ul></div>
        <div><h4>Можливі обмеження</h4><ul class="cons">${s.cons.map(x => `<li>${ic('triangle-alert')}${esc(x)}</li>`).join('')}</ul></div></div>
        <div class="svc-actions"><a class="btn ${s === order[0] ? 'primary' : 'ghost'}" href="#/k/4/${s.id}">Як це працює?</a>${extLink('Перейти до сервісу', s.url, 'btn ghost')}</div>
      </section>`).join('')}</div>
      <section class="local"><h2 class="h2">Місцеві постачальники</h2>
        ${local ? `<p class="muted">Приклад постачальників для міста ${esc(st.city)} — це не перевірка вашого будинку. Назву компанії перевіряйте у квитанції.</p>
        <ul class="rows plainrows">${local.map(p => `<li class="prov">${ic('building-2')}<span><b>${esc(p[1])}</b><small>${esc(p[0])}</small></span></li>`).join('')}</ul>`
          : empty('Місцевих постачальників не знайдено', `Для міста ${st.city} у нас поки немає даних. Скористайтеся сервісами вище або знайдіть постачальника за квитанцією.`, `<a class="btn ghost" href="#/i/provider-find">Як знайти свого постачальника?</a>`)}
      </section>
      <div class="actions"><a class="btn ghost" href="#/k/2">${ic('arrow-left')} Назад</a></div></div>`;
  }

  function kStep4(st, sid) {
    const s = SERVICES[sid]; if (!s) return (location.hash = '#/k/3');
    const key = 'k-' + sid, done = getDone(key);
    app.innerHTML = `<article class="container narrow-l"><div class="page-head">${crumbs([['Головна', '#/'], ['Комунальні послуги', '#/c/utilities'], ['Як оплатити комуналку?', '#/k/3'], [s.name]])}${kProgress(4, st)}
      <div class="title-row"><h1>Як оплатити комунальні послуги через ${s.name}</h1>${saveBtn('komunalka')}</div>
      <p class="lead">Увага: назви розділів і кнопок у сервісі можуть відрізнятися. Орієнтуйтеся на підказки самого сервісу.</p>
      <div class="meta"><span>${ic('clock')} Приблизно 3–5 хв</span><span>${ic('map-pin')} ${esc(addrLine(st))}</span></div></div>
      <div class="cta-row">${extLink('Відкрити ' + s.name, s.url, 'btn primary')}<a class="btn ghost" href="#/k/3">Обрати інший сервіс</a></div>
      <section><div class="h2-row"><h2 class="h2">Покрокова інструкція</h2><span class="muted" id="progTxt"></span></div><div class="bar"><i id="progBar"></i></div>
      <ol class="steps">${s.steps.map((x, i) => { const p = x.split('|'); return `<li class="step${done.includes(i) ? ' done' : ''}"><label><input type="checkbox" data-i="${i}" ${done.includes(i) ? 'checked' : ''}><span class="num">${i + 1}</span><span class="body"><b>${esc(p[0])}</b><span>${esc(p[1] || '')}</span></span></label></li>`; }).join('')}</ol></section>
      <section><h2 class="h2">Часті запитання</h2>${faqHtml(KOM_FAQ)}</section>
      <section><h2 class="h2">Корисні офіційні посилання</h2><div class="links">${Object.values(SERVICES).map(x => extLink(x.name, x.url)).join('')}</div></section>
      ${demoNote}<p class="checked">${ic('calendar-check')} Дата оновлення інформації: ${CHECKED}</p>
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
    else if (p === 's') pageService(a, b, parts[3]);
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

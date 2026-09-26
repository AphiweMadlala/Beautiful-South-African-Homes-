/* Collection filters. Cards are server-rendered; this filters and sorts them in place
   and keeps every choice in the URL so Back/Forward and shared links work. */
(() => {
  const root = document.querySelector('[data-collection]');
  if (!root) return;
  const $ = (s, r = root) => r.querySelector(s);
  const $$ = (s, r = root) => Array.from(r.querySelectorAll(s));

  const form = $('[data-filter-form]');
  const dlg = $('[data-filters]');
  const cardsWrap = $('[data-cards]');
  const cards = $$('[data-card]');
  const status = $('[data-status]');
  const empty = $('[data-empty]');
  const emptyMsg = $('[data-empty-msg]');
  const countOut = $('[data-result-count]');
  const badge = $('[data-filter-count]');
  const sortSel = $('[data-sort]');
  const setInput = $('[data-set-input]');
  const setLinks = $$('[data-set]');
  const locOpts = $$('#f-loc option').filter(o => o.value);
  const locGroups = $$('#f-loc optgroup');
  const emptyAll = $('[data-empty-all]');
  const mobile = matchMedia('(max-width: 979px)');
  const FILTER_KEYS = ['loc', 'type', 'price', 'beds', 'baths', 'garages'];
  const moreFilters = $('[data-more-filters]');
  const moreCount = $('[data-more-count]');

  // All Residences is the collection; For Sale and The Portfolio narrow it.
  const readURL = () => {
    const q = new URLSearchParams(location.search);
    return {
      set: ['for-sale', 'portfolio', 'all'].includes(q.get('set')) ? q.get('set') : 'all',
      loc: q.get('loc') || '', type: q.get('type') || '', price: q.get('price') || '',
      beds: q.get('beds') || '', baths: q.get('baths') || '', garages: q.get('garages') || '',
      features: q.getAll('features'), sort: q.get('sort') || 'recommended',
    };
  };

  const writeForm = s => {
    setInput.value = s.set;
    $('[name=loc]', form).value = s.loc;
    $('[name=price]', form).value = s.price;
    ['type', 'beds', 'baths', 'garages'].forEach(k => {
      $$(`[name=${k}]`, form).forEach(r => { r.checked = r.value === s[k]; });
    });
    $$('[name=features]', form).forEach(c => { c.checked = s.features.includes(c.value); });
    sortSel.value = s.sort;
  };

  const readForm = () => {
    const fd = new FormData(form);
    return {
      set: setInput.value, loc: fd.get('loc') || '', type: fd.get('type') || '', price: fd.get('price') || '',
      beds: fd.get('beds') || '', baths: fd.get('baths') || '', garages: fd.get('garages') || '',
      features: fd.getAll('features'), sort: sortSel.value,
    };
  };

  const toQuery = s => {
    const q = new URLSearchParams();
    if (s.set !== 'all') q.set('set', s.set);
    FILTER_KEYS.forEach(k => { if (s[k]) q.set(k, s[k]); });
    s.features.forEach(f => q.append('features', f));
    if (s.sort !== 'recommended') q.set('sort', s.sort);
    const str = q.toString();
    return str ? `?${str}` : location.pathname;
  };

  const inSet = (d, set) => set === 'all' || (set === 'for-sale') === (d.live === 'true');
  const atLoc = (d, loc) => ({ p: d.province, c: d.city, a: d.place })[loc.slice(0, 1)] === loc.slice(2);

  const matches = (el, s, ignoreSet) => {
    const d = el.dataset;
    if (!ignoreSet && !inSet(d, s.set)) return false;
    if (s.loc && !atLoc(d, s.loc)) return false;
    if (s.type && d.type !== s.type) return false;
    if (s.price) {
      const [lo, hi] = s.price.split('-').map(v => (v === '' ? null : Number(v)));
      const p = d.price ? Number(d.price) : null;
      if (p === null) return false;
      if (lo !== null && p < lo) return false;
      if (hi !== null && p >= hi) return false;
    }
    for (const k of ['beds', 'baths', 'garages']) if (s[k] && Number(d[k]) < Number(s[k])) return false;
    const fs = d.features.split(' ');
    return s.features.every(f => fs.includes(f));
  };

  const sorters = {
    recommended: (a, b) => a.dataset.rank - b.dataset.rank,
    'price-desc': (a, b) => (Number(b.dataset.price) || -1) - (Number(a.dataset.price) || -1),
    'price-asc': (a, b) => (Number(a.dataset.price) || Infinity) - (Number(b.dataset.price) || Infinity),
  };

  const activeCount = s => FILTER_KEYS.filter(k => s[k]).length + s.features.length;
  const label = { 'for-sale': 'for sale', portfolio: 'in the Portfolio', all: 'in the collection' };

  const apply = (s, { push = false } = {}) => {
    const shown = cards.filter(c => matches(c, s));
    cards.forEach(c => { c.hidden = !shown.includes(c); });
    shown.sort(sorters[s.sort] || sorters.recommended).forEach(c => cardsWrap.appendChild(c));
    const n = shown.length;
    status.textContent = `${n} residence${n === 1 ? '' : 's'} ${label[s.set]}`;
    countOut.textContent = String(n);
    const af = activeCount(s);
    badge.hidden = af === 0;
    badge.textContent = String(af);
    const inner = (s.baths ? 1 : 0) + (s.garages ? 1 : 0) + s.features.length;
    moreCount.hidden = inner === 0;
    moreCount.textContent = String(inner);
    if (inner && !moreFilters.open) moreFilters.open = true;
    setLinks.forEach(a => a.setAttribute('aria-current', String(a.dataset.set === s.set)));
    // Places with nothing in this set stay listed but cannot be chosen. The current choice is never
    // disabled: a disabled option drops out of FormData and would silently clear the filter.
    const pool = cards.filter(c => inSet(c.dataset, s.set));
    locOpts.forEach(o => { o.disabled = o.value !== s.loc && !pool.some(c => atLoc(c.dataset, o.value)); });
    locGroups.forEach(g => { g.disabled = Array.from(g.children).every(o => o.disabled); });
    empty.hidden = n > 0;
    if (!n) {
      const elsewhere = cards.filter(c => matches(c, s, true)).length;
      emptyMsg.textContent = s.set !== 'all' && elsewhere
        ? `No residences ${label[s.set]} match these filters. ${elsewhere} match across the whole collection.`
        : 'No residences match these filters. Try widening the location or price.';
      emptyAll.hidden = s.set === 'all' || !elsewhere;
    }
    const url = toQuery(s);
    if (push) history.pushState(s, '', url);
    else history.replaceState(s, '', url);
  };

  // Set tabs keep the other filters.
  setLinks.forEach(a => a.addEventListener('click', e => {
    e.preventDefault();
    setInput.value = a.dataset.set;
    apply(readForm(), { push: true });
  }));

  form.addEventListener('change', () => apply(readForm(), { push: true }));
  sortSel.addEventListener('change', () => apply(readForm(), { push: true }));
  form.addEventListener('submit', e => { e.preventDefault(); apply(readForm(), { push: true }); if (dlg.open && mobile.matches) dlg.close(); });
  const reset = () => {
    const s = { ...readURL(), loc: '', type: '', price: '', beds: '', baths: '', garages: '', features: [], set: setInput.value };
    writeForm(s); apply(s, { push: true });
  };
  form.addEventListener('reset', e => { e.preventDefault(); reset(); });
  $('[data-empty-reset]').addEventListener('click', reset);
  emptyAll.addEventListener('click', e => { e.preventDefault(); setInput.value = 'all'; apply(readForm(), { push: true }); });

  window.addEventListener('popstate', () => { const s = readURL(); writeForm(s); apply(s); });

  // Filters: inline sidebar on desktop, modal sheet on mobile.
  const placeFilters = () => {
    if (mobile.matches) { if (dlg.open && !dlg.matches(':modal')) dlg.close(); }
    else if (!dlg.open) dlg.show();
    else if (dlg.matches(':modal')) { dlg.close(); dlg.show(); }
  };
  mobile.addEventListener('change', placeFilters);
  placeFilters();
  $('[data-filters-open]').addEventListener('click', e => window.BSAH.openModal(dlg, e.currentTarget));
  $('.filters-close', dlg).addEventListener('click', () => dlg.close());
  // A modal close must not leave the sidebar closed on desktop.
  dlg.addEventListener('close', () => { if (!mobile.matches) requestAnimationFrame(() => dlg.show()); });

  const s = readURL();
  writeForm(s);
  apply(s);
})();

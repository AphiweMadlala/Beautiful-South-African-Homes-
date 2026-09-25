/* Beautiful South African Homes: shared behaviour. No dependencies. */
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Scroll lock shared by the menu, filter sheet and lightbox. */
  let locks = 0;
  const lock = () => { if (locks++ === 0) document.documentElement.classList.add('is-locked'); };
  const unlock = () => { if (--locks <= 0) { locks = 0; document.documentElement.classList.remove('is-locked'); } };
  window.BSAH = { lock, unlock };

  /* Modal <dialog> helper: native focus trap and Escape, plus focus restore and scroll lock. */
  const openModal = (dlg, opener) => {
    dlg._opener = opener || document.activeElement;
    dlg.showModal();
    lock();
    dlg.addEventListener('close', () => { unlock(); dlg._opener && dlg._opener.focus({ preventScroll: true }); }, { once: true });
  };
  window.BSAH.openModal = openModal;

  /* Nav turns solid once the hero has scrolled away (home only). */
  const nav = $('[data-nav]');
  const hero = $('.hero');
  if (nav && hero && 'IntersectionObserver' in window) {
    const sentinel = document.createElement('div');
    sentinel.style.cssText = 'position:absolute;top:0;height:60vh;width:1px;pointer-events:none';
    hero.prepend(sentinel);
    new IntersectionObserver(([e]) => nav.classList.toggle('is-solid', !e.isIntersecting)).observe(sentinel);
  }

  /* Mobile menu */
  const menu = $('[data-menu]');
  const menuBtn = $('[data-menu-open]');
  if (menu && menuBtn) {
    menuBtn.addEventListener('click', () => openModal(menu, menuBtn));
    $('[data-menu-close]', menu).addEventListener('click', () => menu.close());
    $$('a', menu).forEach(a => a.addEventListener('click', () => menu.close()));
    matchMedia('(min-width: 980px)').addEventListener('change', e => { if (e.matches && menu.open) menu.close(); });
  }

  /* Reveal on scroll */
  const revealables = $$('.reveal, .reveal-img, .folio');
  if (!reduce && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
    }), { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });
    revealables.forEach(el => io.observe(el));
  } else {
    revealables.forEach(el => el.classList.add('is-in'));
  }

  /* Mobile contact bar: shown once the price block has scrolled away, so it never covers it. */
  const mcta = $('[data-mcta]');
  const anchor = $('[data-price-anchor]');
  if (mcta && anchor && 'IntersectionObserver' in window) {
    new IntersectionObserver(([e]) => mcta.classList.toggle('is-on', !e.isIntersecting && e.boundingClientRect.top < 0))
      .observe(anchor);
  } else if (mcta) mcta.classList.add('is-on');

  /* Mobile swipe gallery counter */
  const swipe = $('[data-swipe]');
  if (swipe) {
    const track = $('.pswipe-track', swipe);
    const out = $('[data-swipe-i]', swipe);
    let raf = 0;
    track.addEventListener('scroll', () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => { out.textContent = String(Math.round(track.scrollLeft / track.clientWidth) + 1); });
    }, { passive: true });
  }

  /* Lightbox: keyboard, Escape, arrows, swipe, focus trap (native modal), focus restore, scroll lock. */
  const lb = $('[data-lightbox]');
  if (lb) {
    const items = $$('[data-lb-item]', lb);
    const count = $('[data-lb-i]', lb);
    let i = 0;
    const show = n => {
      i = (n + items.length) % items.length;
      items.forEach((fig, k) => {
        const on = k === i;
        fig.hidden = !on;
        if (on || k === (i + 1) % items.length || k === (i - 1 + items.length) % items.length) {
          const img = $('img', fig);
          if (!img.src) img.src = img.dataset.src;
        }
      });
      count.textContent = String(i + 1);
    };
    $$('[data-open-lightbox]').forEach(btn => btn.addEventListener('click', () => {
      show(Number(btn.dataset.openLightbox) || 0);
      openModal(lb, btn);
      $('[data-lb-next]', lb).focus();
    }));
    $('[data-lb-prev]', lb).addEventListener('click', () => show(i - 1));
    $('[data-lb-next]', lb).addEventListener('click', () => show(i + 1));
    $('[data-lb-close]', lb).addEventListener('click', () => lb.close());
    lb.addEventListener('keydown', e => {
      if (e.key === 'ArrowRight') { e.preventDefault(); show(i + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(i - 1); }
    });
    const stage = $('[data-lb-stage]', lb);
    let x0 = null, y0 = null, swiped = false;
    stage.addEventListener('pointerdown', e => { x0 = e.clientX; y0 = e.clientY; swiped = false; });
    stage.addEventListener('pointerup', e => {
      if (x0 === null) return;
      const dx = e.clientX - x0, dy = e.clientY - y0;
      if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) { swiped = true; show(i + (dx < 0 ? 1 : -1)); }
      x0 = null;
    });
    // A tap on the empty stage closes; the click that ends a swipe does not.
    stage.addEventListener('click', e => { if (e.target === stage && !swiped) lb.close(); swiped = false; });
  }

  /* Feature-your-property form: composes an email in the visitor's own mail app. No backend. */
  const form = $('[data-mailto-form]');
  if (form) {
    const err = $('[data-form-error]', form);
    form.addEventListener('submit', e => {
      e.preventDefault();
      const fields = $$('input, textarea', form);
      let bad = null;
      fields.forEach(f => {
        const invalid = !f.checkValidity();
        f.setAttribute('aria-invalid', invalid ? 'true' : 'false');
        if (invalid && !bad) bad = f;
      });
      if (bad) { err.hidden = false; bad.focus(); return; }
      err.hidden = true;
      const lines = fields.filter(f => f.value.trim()).map(f => `${f.name}: ${f.value.trim()}`);
      const loc = $('#s-loc', form).value.trim();
      const href = `mailto:${form.dataset.to}?subject=${encodeURIComponent('Feature submission: ' + loc)}&body=${encodeURIComponent(lines.join('\n'))}`;
      window.location.href = href;
    });
  }
})();

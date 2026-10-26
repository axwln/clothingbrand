/* Progressive motion: content stays visible when scripts, storage or observers fail. */
(() => {
  'use strict';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const desktop = window.matchMedia('(min-width: 640px)');
  const animate = (element, frames, options = {}) => {
    if (reducedMotion.matches || !element.animate) return null;
    return element.animate(frames, { duration: 900, easing: 'cubic-bezier(.22,1,.36,1)', ...options });
  };
  document.querySelectorAll('.brand-logo img').forEach(img => {
    const fallback = () => {
      img.hidden = true;
      img.nextElementSibling.hidden = false;
    };
    img.addEventListener('error', fallback);
    if (img.complete && !img.naturalWidth) fallback();
  });

  const root = document.documentElement;
  const sun = document.getElementById('icon-sun');
  const moon = document.getElementById('icon-moon');
  const themeButton = document.getElementById('theme-toggle');
  function applyTheme(dark) {
    root.classList.toggle('dark', dark);
    sun?.classList.toggle('hidden', !dark);
    moon?.classList.toggle('hidden', dark);
    themeButton?.setAttribute('aria-pressed', String(dark));
  }
  let savedTheme;
  try { savedTheme = localStorage.getItem('theme'); } catch (_) { /* Private browsing. */ }
  applyTheme(savedTheme ? savedTheme === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches);
  themeButton?.addEventListener('click', () => {
    const dark = !root.classList.contains('dark');
    applyTheme(dark);
    try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch (_) { /* Optional storage. */ }
  });

  const nav = document.getElementById('site-nav');
  const updateNav = () => nav?.classList.toggle('scrolled', window.scrollY > 10);
  updateNav();
  window.addEventListener('scroll', updateNav, { passive: true });

  const menu = document.getElementById('mobile-menu');
  const toggle = document.getElementById('menu-toggle');
  if (menu && toggle) {
    let menuAnimation;
    let open = false;
    function setMenu(next, returnFocus = false) {
      open = next;
      menuAnimation?.cancel();
      toggle.setAttribute('aria-expanded', String(open));
      if (returnFocus) toggle.focus();
      menu.inert = !open;
      if (open) {
        menu.hidden = false;
        menuAnimation = animate(menu, [{ height: '0px', opacity: 0 }, { height: `${menu.scrollHeight}px`, opacity: 1 }], { duration: 350 });
      } else if (!menu.hidden && !reducedMotion.matches) {
        menuAnimation = animate(menu, [{ height: `${menu.scrollHeight}px`, opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 250 });
        if (menuAnimation) menuAnimation.onfinish = () => { if (!open) menu.hidden = true; };
        else menu.hidden = true;
      } else menu.hidden = true;
    }
    menu.hidden = true;
    menu.inert = true;
    toggle.hidden = false;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', () => setMenu(!open));
    menu.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && open) setMenu(false, true); });
    const resizeMenu = () => { if (desktop.matches) setMenu(false); };
    if (desktop.addEventListener) desktop.addEventListener('change', resizeMenu);
    else desktop.addListener(resizeMenu);
  }

  const hero = document.querySelector('[data-home-hero]');
  if (hero) {
    let firstEntry = true;
    try {
      firstEntry = sessionStorage.getItem('devika-brand-seen') !== '1';
      sessionStorage.setItem('devika-brand-seen', '1');
    } catch (_) { /* Still nonblocking if session storage is unavailable. */ }
    if (firstEntry) {
      const brand = nav?.querySelector('.brand-logo');
      if (brand) animate(brand, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'translateY(0)' }]);
      const eyebrow = hero.querySelector('.hero-eyebrow');
      animate(eyebrow, [{ opacity: 0, letterSpacing: '.35em' }, { opacity: 1, letterSpacing: '.22em' }], { delay: 150, fill: 'backwards' });
      hero.querySelectorAll('[data-hero-reveal]').forEach((el, i) => {
        if (el === eyebrow) return;
        animate(el, [{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'translateY(0)' }], { delay: 200 + i * 120, fill: 'backwards' });
      });
      animate(hero.querySelector('.hero-photo'), [{ transform: 'scale(1.035)' }, { transform: 'scale(1)' }], { duration: 1200 });
    }
  }

  if (!('IntersectionObserver' in window) || reducedMotion.matches) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(({ target, isIntersecting }) => {
      if (!isIntersecting) return;
      observer.unobserve(target);
      const group = target.parentElement?.classList.contains('reveal-stagger');
      const index = group ? Array.from(target.parentElement.children).indexOf(target) : 0;
      const fade = target.classList.contains('reveal-fade');
      const lines = target.classList.contains('reveal-lines');
      const frames = fade ? [{ opacity: 0 }, { opacity: 1 }] : [
        { opacity: 0, transform: 'translateY(20px)' },
        { opacity: 1, transform: 'translateY(0)' }
      ];
      if (lines) {
        target.querySelectorAll(':scope > span').forEach((line, i) => animate(line, frames, { delay: i * 100, fill: 'backwards' }));
      } else animate(target, frames, { delay: Math.min(index, 3) * 80, fill: 'backwards' });
    });
  }, { threshold: 0.08 });
  document.querySelectorAll('.reveal-up, .reveal-lines, .reveal-fade, .reveal-image, .reveal-stagger > *').forEach(el => {
    if (el.closest('[data-home-hero]') || el.parentElement?.closest('.reveal-up, .reveal-image')) return;
    observer.observe(el);
  });
  // A preference change immediately finishes all decorative animation.
  const stopMotion = () => {
    if (reducedMotion.matches) document.getAnimations?.().forEach(animation => animation.finish());
  };
  if (reducedMotion.addEventListener) reducedMotion.addEventListener('change', stopMotion);
  else reducedMotion.addListener(stopMotion);
})();

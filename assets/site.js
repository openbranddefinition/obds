(() => {
  // Motion explains a transition once; it never loops or gates access to text.
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  if ('IntersectionObserver' in window && !reducedMotion.matches) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('in-view'); observer.unobserve(entry.target); }
    }), { threshold: 0.12 });
    document.querySelectorAll('.visual-section, .brand-stage').forEach(el => observer.observe(el));
  }
  document.querySelectorAll('.decision-rail i').forEach((el, i) => el.style.setProperty('--step', i));
  const demo = document.querySelector('[data-demo]');
  if (demo) {
    demo.querySelector('.demo-controls').hidden = false;
    demo.querySelectorAll('[data-demo-select]').forEach(button => button.addEventListener('click', () => {
      const unknown = button.dataset.demoSelect === 'unknown';
      demo.dataset.demo = unknown ? 'unknown' : 'defined';
      demo.querySelectorAll('[data-demo-select]').forEach(el => el.setAttribute('aria-pressed', String(el === button)));
      demo.querySelector('[data-demo-field]').textContent = unknown ? 'context.efficacy-claim' : 'structure.brand';
      demo.querySelector('[data-demo-state]').textContent = unknown ? 'unknown' : 'defined';
      const setBilingual = (selector, en, de) => {
        demo.querySelector(selector + ' [data-copy="en"]').textContent = en;
        demo.querySelector(selector + ' [data-copy="de"]').textContent = de;
      };
      setBilingual('[data-demo-result]', unknown ? 'Build stopped' : 'Context compiled', unknown ? 'Build gestoppt' : 'Kontext kompiliert');
      setBilingual('[data-demo-detail]', unknown ? 'Required truth is unknown.' : 'Required truth is defined.', unknown ? 'Erforderliche Wahrheit ist unbekannt.' : 'Erforderliche Wahrheit ist definiert.');
      demo.querySelector('.decision-symbol').textContent = unknown ? '↳' : '↗';
      demo.querySelector('[data-demo-source]').href = unknown ? '/examples/#fail-closed' : '/examples/#defined';
    }));
  }
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.primary-nav');
  if (toggle && menu) {
    toggle.hidden = false;
    toggle.classList.add('ready');
    menu.classList.add('enhanced');
    const close = () => { menu.classList.remove('is-open'); toggle.setAttribute('aria-expanded', 'false'); };
    toggle.addEventListener('click', () => {
      const open = menu.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', String(open));
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.classList.contains('is-open')) { close(); toggle.focus(); }
    });
    menu.addEventListener('click', event => { if (event.target.closest('a')) close(); });
    matchMedia('(min-width:721px)').addEventListener('change', close);
  }
  const links = [...document.querySelectorAll('[data-set-lang]')];
  if (!links.length) return;
  const setLanguage = language => {
    document.documentElement.dataset.lang = language;
    document.documentElement.lang = language;
    links.forEach(link => link.setAttribute('aria-current', String(link.dataset.setLang === language)));
  };
  const requested = new URL(location.href).searchParams.get('lang');
  setLanguage(['en', 'de'].includes(requested) ? requested : navigator.language.startsWith('de') ? 'de' : 'en');
  links.forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    setLanguage(link.dataset.setLang);
    const url = new URL(location.href); url.searchParams.set('lang', link.dataset.setLang);
    history.replaceState(null, '', url);
  }));
})();

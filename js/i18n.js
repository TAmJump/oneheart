/* ONE HEART - language switcher (en / ja / ko)
   Dictionaries live in /i18n/<page>.json as {"ja":{english:translation},"ko":{...}}.
   Pages stay English in the source; this swaps text at runtime and remembers the choice. */
(function () {
  var STORE = 'oh_lang';
  var LANGS = [['en', 'EN'], ['ja', '日本語'], ['ko', '한국어']];
  var FONTS = {
    ja: 'https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800&display=swap',
    ko: 'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap'
  };
  var STACK = {
    ja: '"Noto Sans JP",Inter,-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic",sans-serif',
    ko: '"Noto Sans KR",Inter,-apple-system,BlinkMacSystemFont,"Malgun Gothic",sans-serif'
  };
  var ATTRS = ['placeholder', 'title', 'alt', 'aria-label'];

  var dicts = {};
  var cur = 'en';
  var origText = new WeakMap();
  var origAttr = new WeakMap();
  var titleOrig = document.title;
  var descEl = document.querySelector('meta[name="description"]');
  var descOrig = descEl ? descEl.getAttribute('content') : '';
  var observer = null;

  function page() {
    var p = location.pathname.replace(/index\.html$/, '').replace(/\/+$/, '');
    if (p === '' ) return 'index';
    if (p === '/terms') return 'terms';
    if (p === '/ceo') return 'ceo';
    var m = p.match(/([^\/]+?)(\.html)?$/);
    return m ? m[1] : 'index';
  }

  function stored() {
    var q = new URLSearchParams(location.search).get('lang');
    if (q && /^(en|ja|ko)$/.test(q)) return q;
    try { var v = localStorage.getItem(STORE); if (v && /^(en|ja|ko)$/.test(v)) return v; } catch (e) {}
    return null;
  }

  function loadFont(lang) {
    if (!FONTS[lang] || document.getElementById('oh-font-' + lang)) return;
    var l = document.createElement('link');
    l.id = 'oh-font-' + lang;
    l.rel = 'stylesheet';
    l.href = FONTS[lang];
    document.head.appendChild(l);
  }

  function walk(root, fn) {
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode;
        if (!p) return NodeFilter.FILTER_REJECT;
        var tag = p.nodeName;
        if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT') return NodeFilter.FILTER_REJECT;
        if (p.closest && p.closest('[data-i18n-skip]')) return NodeFilter.FILTER_REJECT;
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = w.nextNode())) fn(n);
  }

  function elements(root) {
    var list = [];
    if (root.nodeType === 1) list.push(root);
    if (root.querySelectorAll) {
      var all = root.querySelectorAll('*');
      for (var i = 0; i < all.length; i++) list.push(all[i]);
    }
    return list;
  }

  function translateIn(root, lang) {
    var d = dicts[lang] || {};
    walk(root, function (n) {
      if (!origText.has(n)) origText.set(n, n.nodeValue);
      var raw = origText.get(n);
      var key = raw.trim();
      var hit = d[key];
      if (hit) n.nodeValue = raw.replace(key, hit);
    });
    elements(root).forEach(function (el) {
      ATTRS.forEach(function (a) {
        if (!el.hasAttribute || !el.hasAttribute(a)) return;
        var store = origAttr.get(el) || {};
        if (!(a in store)) { store[a] = el.getAttribute(a); origAttr.set(el, store); }
        var hit = d[String(store[a]).trim()];
        if (hit) el.setAttribute(a, hit);
      });
    });
  }

  function restoreIn(root) {
    walk(root, function (n) {
      if (origText.has(n)) n.nodeValue = origText.get(n);
    });
    elements(root).forEach(function (el) {
      var store = origAttr.get(el);
      if (!store) return;
      Object.keys(store).forEach(function (a) { el.setAttribute(a, store[a]); });
    });
  }

  function apply(lang) {
    cur = lang;
    document.documentElement.lang = lang;
    if (lang === 'en') {
      restoreIn(document.body);
      document.title = titleOrig;
      if (descEl) descEl.setAttribute('content', descOrig);
      document.body.style.fontFamily = '';
    } else {
      loadFont(lang);
      restoreIn(document.body);
      translateIn(document.body, lang);
      var d = dicts[lang] || {};
      document.title = d[titleOrig.trim()] || titleOrig;
      if (descEl) descEl.setAttribute('content', d[String(descOrig).trim()] || descOrig);
      document.body.style.fontFamily = STACK[lang] || '';
    }
    mark();
  }

  function mark() {
    var bar = document.getElementById('oh-lang');
    if (!bar) return;
    Array.prototype.forEach.call(bar.querySelectorAll('button'), function (b) {
      var on = b.getAttribute('data-l') === cur;
      b.style.background = on ? '#111111' : 'transparent';
      b.style.color = on ? '#FFD900' : '#111111';
    });
  }

  function bar() {
    var wrap = document.createElement('div');
    wrap.id = 'oh-lang';
    wrap.setAttribute('data-i18n-skip', '');
    wrap.style.cssText =
      'position:fixed;top:0;right:0;z-index:9999;display:flex;background:#FFD900;' +
      'border-left:3px solid #111111;border-bottom:3px solid #111111;';
    LANGS.forEach(function (p) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = p[1];
      b.setAttribute('data-l', p[0]);
      b.setAttribute('lang', p[0]);
      b.style.cssText =
        'border:0;padding:8px 12px;font:700 12px/1 Inter,system-ui,sans-serif;' +
        'letter-spacing:.08em;cursor:pointer;background:transparent;color:#111111;';
      b.addEventListener('click', function () {
        try { localStorage.setItem(STORE, p[0]); } catch (e) {}
        if (p[0] === 'en' || dicts[p[0]]) { apply(p[0]); } else { load(p[0], function () { apply(p[0]); }); }
      });
      wrap.appendChild(b);
    });
    document.body.appendChild(wrap);
    mark();
  }

  function load(lang, done) {
    if (lang === 'en' || dicts[lang]) { done(); return; }
    fetch('/i18n/' + page() + '.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : {}; })
      .then(function (j) { dicts.ja = j.ja || {}; dicts.ko = j.ko || {}; })
      .catch(function () { dicts.ja = dicts.ja || {}; dicts.ko = dicts.ko || {}; })
      .then(done);
  }

  function watch() {
    if (observer || !window.MutationObserver) return;
    observer = new MutationObserver(function (recs) {
      if (cur === 'en') return;
      recs.forEach(function (r) {
        Array.prototype.forEach.call(r.addedNodes, function (n) {
          if (n.nodeType === 1 || n.nodeType === 3) translateIn(n.nodeType === 3 ? n.parentNode || document.body : n, cur);
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function start() {
    bar();
    watch();
    var want = stored();
    if (want && want !== 'en') load(want, function () { apply(want); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();

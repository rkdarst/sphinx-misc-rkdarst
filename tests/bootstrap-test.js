// Test harness for bootstrap.js activation + URL theme selection.
// Runs the real bootstrap.js in a minimal DOM mock.
'use strict';
const fs = require('fs');
const SRC = '/u/04/darstr1/unix/git/sphinx-misc-rkdarst/sphinx_misc_rkdarst/_static/revealjs/bootstrap.js';
const src = fs.readFileSync(SRC, 'utf8');

function makeEnv(url, attrs) {
  const links = [];
  const scripts = [];
  const styles = [];
  const scriptEl = {
    src: 'file:///site/_static/revealjs/bootstrap.js',
    getAttribute: (n) => (n in attrs ? attrs[n] : null),
  };
  const document = {
    currentScript: scriptEl,
    readyState: 'complete',
    head: { appendChild() {} },
    documentElement: { classList: { add() {}, remove() {} } },
    addEventListener() {},
    createElement(tag) {
      return { tag, onload: null, onerror: null, textContent: '', rel: '', href: '', src: '' };
    },
  };
  document.head.appendChild = (el) => {
    if (el.tag === 'link') links.push(el.href);
    else if (el.tag === 'script') scripts.push(el.src);
    else if (el.tag === 'style') styles.push(el.textContent);
  };
  const window = {
    location: { search: url },
    setTimeout: () => 0,
    clearTimeout: () => {},
    console,
    __revealjsTransform: () => {},
  };
  return { document, window, links, scripts, styles };
}

function run(url, attrs) {
  attrs = attrs || { 'data-param': 'revealjs', 'data-theme': 'simple' };
  const env = makeEnv(url, attrs);
  global.document = env.document;
  global.window = env.window;
  new Function(src)();
  return env;
}

let failures = 0;
function check(name, cond) {
  console.log((cond ? 'ok:   ' : 'FAIL: ') + name);
  if (!cond) failures++;
}
const hasTheme = (r, name) => r.links.some((h) => h.includes('theme/' + name + '.min.css'));
const anyTheme = (r) => r.links.some((h) => h.includes('/theme/'));
const activated = (r) => r.links.some((h) => h.includes('reveal.min.css'));

// --- activation ---
let r = run('?revealjs');
check('bare ?revealjs activates', activated(r));
check('bare ?revealjs uses default theme (simple)', hasTheme(r, 'simple'));

r = run('?revealjs=');
check('?revealjs= activates with default theme', activated(r) && hasTheme(r, 'simple'));

r = run('?x=1');
check('?x=1: nothing loads', !activated(r) && r.scripts.length === 0);

r = run('?revealjsfoo=1');
check('?revealjsfoo=1 does not activate', r.scripts.length === 0);

r = run('?xrevealjs=1');
check('?xrevealjs=1 does not activate', r.scripts.length === 0);

r = run('?revealjs&x=1');
check('?revealjs&x=1 activates', activated(r));

// --- theme selection via URL ---
r = run('?revealjs=black');
check('?revealjs=black activates', activated(r));
check('?revealjs=black loads black theme', hasTheme(r, 'black'));
check('?revealjs=black does not load default simple', !hasTheme(r, 'simple'));

r = run('?foo=1&revealjs=black');
check('?foo=1&revealjs=black loads black theme', hasTheme(r, 'black'));

r = run('?revealjs=black&x=2');
check('?revealjs=black&x=2 loads black theme', hasTheme(r, 'black'));

r = run('?revealjs=simple');
check('?revealjs=simple loads simple theme', hasTheme(r, 'simple'));

// --- none disables the theme ---
r = run('?revealjs=none');
check('?revealjs=none activates', activated(r));
check('?revealjs=none loads no theme', !anyTheme(r));

r = run('?revealjs=NONE');
check('?revealjs=NONE loads no theme', !anyTheme(r));

// --- graceful degradation ---
r = run('?revealjs=bogus');
check('?revealjs=bogus still activates', activated(r));
check('?revealjs=bogus attempts the theme link (404s silently)', hasTheme(r, 'bogus'));

r = run('?revealjs=%ZZ');
check('?revealjs=%ZZ activates without crashing', activated(r));

r = run('?revealjs=bla%63k');
check('?revealjs=bla%63k decodes to black', hasTheme(r, 'black'));

// --- hash fragment is not part of search ---
r = run('?revealjs#frag');
check('?revealjs#frag activates with default theme', activated(r) && hasTheme(r, 'simple'));

// --- custom param name, incl. regex-special chars ---
r = run('?slides=black', { 'data-param': 'slides', 'data-theme': 'simple' });
check('custom data-param slides: ?slides=black works', hasTheme(r, 'black'));

r = run('?my.revealjs=black', { 'data-param': 'my.revealjs', 'data-theme': 'simple' });
check('regex-special param name (?my.revealjs=black) works', hasTheme(r, 'black'));

// --- conf default '' (no theme) still honored ---
r = run('?revealjs', { 'data-param': 'revealjs', 'data-theme': '' });
check("data-theme='': no theme by default", !anyTheme(r));
r = run('?revealjs=black', { 'data-param': 'revealjs', 'data-theme': '' });
check("data-theme='' overridden by ?revealjs=black", hasTheme(r, 'black'));

// --- always-loaded assets ---
r = run('?revealjs=none');
check('presentation.css always loaded', r.links.some((h) => h.endsWith('presentation.css')));
check('reveal.min.js always loaded', r.scripts.some((s) => s.includes('reveal.min.js')));
check('transform.js always loaded', r.scripts.some((s) => s.includes('transform.js')));

// --- themed flag in __revealjsConfig ---
const cfgOf = (r) => r.window.__revealjsConfig || null;

r = run('?revealjs');
check('bare ?revealjs: themed=true (default simple)', cfgOf(r).themed === true);

r = run('?revealjs=black');
check('?revealjs=black: themed=true', cfgOf(r).themed === true);

r = run('?revealjs=none');
check('?revealjs=none: themed=false', cfgOf(r).themed === false);

r = run('?revealjs=NONE');
check('?revealjs=NONE: themed=false', cfgOf(r).themed === false);

r = run('?revealjs', { 'data-param': 'revealjs', 'data-theme': '' });
check("data-theme='': themed=false", cfgOf(r).themed === false);

r = run('?x=1');
check('?x=1: no config set', cfgOf(r) === null);

// --- hr-notes flag in __revealjsConfig ---
r = run('?revealjs');
check('no data-hr-notes attr: hrNotes=true (default)', cfgOf(r).hrNotes === true);

r = run('?revealjs', { 'data-param': 'revealjs', 'data-theme': 'simple', 'data-hr-notes': 'true' });
check("data-hr-notes='true': hrNotes=true", cfgOf(r).hrNotes === true);

r = run('?revealjs', { 'data-param': 'revealjs', 'data-theme': 'simple', 'data-hr-notes': 'false' });
check("data-hr-notes='false': hrNotes=false", cfgOf(r).hrNotes === false);

console.log(failures ? failures + ' FAILURES' : 'ALL PASS');
process.exit(failures ? 1 : 0);

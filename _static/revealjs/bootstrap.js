/*
 * revealjs bootstrap: loaded on every page.  If the activation query
 * parameter is present in the URL, lazily load the reveal.js assets
 * (from the same directory as this script) and run the page-to-slides
 * transform.  Otherwise it does nothing.
 *
 * Configuration is read from the data attributes of the <script> tag:
 *   data-param        URL query parameter activating presentation
 *                     mode (?param, ?param=, or ?param=value)
 *   data-theme        default reveal.js theme name ('' = none),
 *                     overridden by a non-empty ?param=<name> value
 *                     in the URL ("none" = load no theme)
 *   data-ellipsis-notes "true"/"false", a lone `...` line starts an
 *                     audience-notes block for the preceding slide
 *                     instead of being ordinary content (default true)
 *   data-hr-notes     "true"/"false", legacy: <hr> acts as an
 *                     audience-notes divider instead of splitting
 *                     slides (default false)
 *   data-break-on-hr  "true"/"false", <hr> forces slide breaks (only
 *                     consulted when data-hr-notes is off)
 *   data-font-scale   rescales the deck's base font size in none-theme
 *                     mode (a percentage of the page's ambient body
 *                     text size); ignored when a theme loads, since
 *                     themes bring their own sizes.  Default 1
 *
 * Our files (this script, transform.js, presentation.css) live in the
 * revealjs/ directory; all vendored upstream reveal.js files (MIT,
 * see upstream/LICENSE) live in the upstream/ subdirectory.
 */
(function () {
    'use strict';

    var me = document.currentScript;
    var param = (me && me.getAttribute('data-param')) || 'revealjs';
    // Activate on the bare parameter (?revealjs, ?foo=1&revealjs), on
    // the empty-value form (?revealjs=, ?revealjs=&x), or with a
    // value (?revealjs=black).  A value, when present, selects the
    // reveal.js theme (see below).
    var paramRe = param.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (!new RegExp('[?&]' + paramRe + '(?:=[^&#]*)?(?:[&#]|$)').test(window.location.search)) {
        return;
    }

    var base = me.src.replace(/\/[^/]*$/, '/');
    var upstream = base + 'upstream/';
    var theme = (me && me.getAttribute('data-theme')) || '';
    // A non-empty URL parameter value (?revealjs=black) selects the
    // theme at view time, overriding the conf.py default.  "none"
    // (case-insensitive) means no theme at all.  The bare parameter
    // (?revealjs) or empty value (?revealjs=) means "use the default
    // theme".  An unknown theme name 404s and the deck silently
    // renders without a theme (site typography, white background).
    var paramValue = (function () {
        var m = new RegExp('[?&]' + paramRe + '=([^&#]*)').exec(window.location.search);
        if (!m) {
            return '';
        }
        try {
            return decodeURIComponent(m[1]);
        } catch (err) {
            return m[1];
        }
    })();
    if (paramValue) {
        theme = paramValue;
    }
    if (theme.toLowerCase() === 'none') {
        theme = '';
    }
    var ellipsisNotes = !me ||
        me.getAttribute('data-ellipsis-notes') !== 'false';
    var hrNotes = !!me && me.getAttribute('data-hr-notes') === 'true';
    var breakOnHr = !me || me.getAttribute('data-break-on-hr') !== 'false';
    var fontScale = parseFloat(me && me.getAttribute('data-font-scale'));
    if (!isFinite(fontScale) || fontScale <= 0) {
        fontScale = 1;
    }

    // Own the page immediately (blank) so that the normal page does
    // not flash before the slides appear.  Cleared on failure or
    // timeout so that a broken setup falls back to the normal page.
    document.documentElement.classList.add('revealjs-mode');
    var style = document.createElement('style');
    style.textContent =
        'html.revealjs-mode body > *:not(.reveal):not(.revealjs-keep) ' +
        ':not(.revealjs-exit) { display: none !important; }';
    document.head.appendChild(style);

    var abort = function () {
        document.documentElement.classList.remove('revealjs-mode');
    };
    var timer = window.setTimeout(abort, 15000);

    window.__revealjsConfig = {
        ellipsisNotes: ellipsisNotes,
        hrNotes: hrNotes,
        breakOnHr: breakOnHr,
        param: param,
        themed: !!theme,
        fontScale: fontScale,
        onDone: function () { window.clearTimeout(timer); },
    };

    // Wait for: all stylesheets, reveal.js, transform.js, and the DOM.
    var pending = 2;  // reveal.min.js + transform.js
    var domReady = false;

    var step = function () {
        if (!domReady || pending > 0) {
            return;
        }
        try {
            window.__revealjsTransform();
        } catch (err) {
            window.clearTimeout(timer);
            abort();
            if (window.console) {
                console.error('revealjs: transform failed', err);
            }
        }
    };

    var addStylesheet = function (href) {
        pending += 1;
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        link.onload = function () { pending -= 1; step(); };
        link.onerror = function () { pending -= 1; step(); };
        document.head.appendChild(link);
    };

    addStylesheet(upstream + 'reveal.min.css');
    addStylesheet(base + 'presentation.css');
    if (theme) {
        addStylesheet(upstream + 'theme/' + theme + '.min.css');
    }
    // (theme == '' => no theme stylesheet; the deck then inherits the
    // site's own fonts/colors, and presentation.css's
    // var(--r-background-color, #fff) fallback keeps the slide
    // background white.)

    var script = document.createElement('script');
    script.src = upstream + 'reveal.min.js';
    script.onload = function () { pending -= 1; step(); };
    script.onerror = function () {
        window.clearTimeout(timer);
        abort();
    };
    document.head.appendChild(script);

    var tscript = document.createElement('script');
    tscript.src = base + 'transform.js';
    tscript.onload = function () { pending -= 1; step(); };
    tscript.onerror = function () {
        window.clearTimeout(timer);
        abort();
    };
    document.head.appendChild(tscript);

    // The speaker-notes plugin (optional: if it fails to load, decks
    // still present -- the S-key speaker view just isn't available).
    pending += 1;
    var nscript = document.createElement('script');
    nscript.src = upstream + 'plugin/notes/notes.js';
    nscript.onload = function () { pending -= 1; step(); };
    nscript.onerror = function () { pending -= 1; step(); };
    document.head.appendChild(nscript);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            domReady = true;
            step();
        });
    } else {
        domReady = true;
        step();
    }
})();

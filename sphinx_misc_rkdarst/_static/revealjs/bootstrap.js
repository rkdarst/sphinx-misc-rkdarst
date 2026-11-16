/*
 * revealjs bootstrap: loaded on every page.  If the activation query
 * parameter is present in the URL, lazily load the reveal.js assets
 * (from the same directory as this script) and run the page-to-slides
 * transform.  Otherwise it does nothing.
 *
 * Configuration is read from the data attributes of the <script> tag:
 *   data-param        URL query parameter activating presentation mode
 *   data-theme        reveal.js theme name ('' = none)
 *   data-break-on-hr  "true"/"false", <hr> forces slide breaks
 *
 * Our files (this script, transform.js, presentation.css) live in the
 * revealjs/ directory; all vendored upstream reveal.js files (MIT,
 * see upstream/LICENSE) live in the upstream/ subdirectory.
 */
(function () {
    'use strict';

    var me = document.currentScript;
    var param = (me && me.getAttribute('data-param')) || 'revealjs';
    if (!new RegExp('[?&]' + param + '(?:[&#]|$)').test(window.location.search)) {
        return;
    }

    var base = me.src.replace(/\/[^/]*$/, '/');
    var upstream = base + 'upstream/';
    var theme = (me && me.getAttribute('data-theme')) || '';
    var breakOnHr = !me || me.getAttribute('data-break-on-hr') !== 'false';

    // Own the page immediately (blank) so that the normal page does
    // not flash before the slides appear.  Cleared on failure or
    // timeout so that a broken setup falls back to the normal page.
    document.documentElement.classList.add('revealjs-mode');
    var style = document.createElement('style');
    style.textContent =
        'html.revealjs-mode body > *:not(.reveal):not(.revealjs-exit) ' +
        '{ display: none !important; }';
    document.head.appendChild(style);

    var abort = function () {
        document.documentElement.classList.remove('revealjs-mode');
    };
    var timer = window.setTimeout(abort, 15000);

    window.__revealjsConfig = {
        breakOnHr: breakOnHr,
        param: param,
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

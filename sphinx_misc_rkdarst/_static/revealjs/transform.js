/*
 * revealjs transform: turn the current Sphinx page into a reveal.js
 * presentation.  Called by bootstrap.js once the DOM and all assets
 * are ready.  See sphinx_misc_rkdarst/revealjs.py for the overall
 * design.
 *
 * Rules:
 * - The content root ([role=main] / main / article / div.body) is
 *   found; if it consists of a single <section> that starts with an
 *   <h1>, that wrapper is unwrapped so that its child sections become
 *   top-level slides.
 * - Content before the first section becomes the title slide.
 * - Each child <section> (or div.section) becomes a slide; nested
 *   sections become vertical (sub)slides.
 * - <hr> forces a slide break at the current level (removed from the
 *   presentation).
 */
(function () {
    'use strict';

    if (window.__revealjsTransformed) {
        return;
    }
    window.__revealjsTransformed = true;

    var cfg = window.__revealjsConfig || {};

    function el(tag, cls) {
        var e = document.createElement(tag);
        if (cls) {
            e.className = cls;
        }
        return e;
    }

    function significantChildren(node) {
        // Element children plus non-blank text nodes.
        var out = [];
        for (var n = node.firstChild; n; n = n.nextSibling) {
            if (n.nodeType === Node.ELEMENT_NODE) {
                out.push(n);
            } else if (n.nodeType === Node.TEXT_NODE && /\S/.test(n.nodeValue)) {
                out.push(n);
            }
        }
        return out;
    }

    function isSection(node) {
        return node.nodeType === Node.ELEMENT_NODE &&
            (node.tagName === 'SECTION' ||
             (node.tagName === 'DIV' && node.classList.contains('section')));
    }

    // Page-only elements: never moved into the slides, so they stay
    // visible on the normal page and are completely absent from the
    // presentation:
    // - anything with class "revealjs-noslide" (e.g. from
    //   ".. container:: revealjs-noslide")
    // - ".. epigraph::" blockquotes (page-only details convention)
    function isSkippedFromSlides(node) {
        return node.nodeType === Node.ELEMENT_NODE &&
            (node.classList.contains('revealjs-noslide') ||
             (node.tagName === 'BLOCKQUOTE' &&
              node.classList.contains('epigraph')));
    }

    function findContentRoot() {
        var selectors = ['[role="main"]', 'main', 'article', 'div.body', 'div.document'];
        for (var i = 0; i < selectors.length; i++) {
            var found = document.querySelector(selectors[i]);
            if (found) {
                return found;
            }
        }
        return document.body;
    }

    function unwrapTitleRoot(root) {
        // If the content root consists of a single <section> that
        // starts with an <h1> (how docutils >=0.18 renders a document
        // title), descend into it so that its subsections are treated
        // as top-level slides.
        var cur = root;
        for (;;) {
            var kids = significantChildren(cur);
            if (kids.length !== 1 || !isSection(kids[0])) {
                break;
            }
            var first = kids[0].firstElementChild;
            if (!first || first.tagName !== 'H1') {
                break;
            }
            cur = kids[0];
        }
        return cur;
    }

    // A slide group that ended up with a single child slide is
    // equivalent to that slide; unwrap it.  Also drop empty slides.
    function normalize(container) {
        var kids = significantChildren(container);
        var i;
        for (i = kids.length - 1; i >= 0; i--) {
            if (kids[i].tagName === 'SECTION' &&
                significantChildren(kids[i]).length === 0) {
                container.removeChild(kids[i]);
            }
        }
        for (;;) {
            kids = significantChildren(container);
            if (kids.length !== 1 || kids[0].tagName !== 'SECTION') {
                break;
            }
            var only = kids[0];
            if (significantChildren(only).length === 0) {
                container.removeChild(only);
                break;
            }
            while (only.firstChild) {
                container.insertBefore(only.firstChild, only);
            }
            container.removeChild(only);
        }
    }

    // Distribute the children of `source` into slide <section>s
    // appended to `container`.  Sections become nested slide groups,
    // <hr> forces a break.
    function buildLevel(container, source) {
        var current = null;
        var startSlide = function () {
            current = el('section');
            container.appendChild(current);
            return current;
        };

        var kids = significantChildren(source);
        for (var i = 0; i < kids.length; i++) {
            var child = kids[i];
            if (child.tagName === 'HR' && cfg.breakOnHr !== false) {
                current = null;
                if (child.parentNode) {
                    child.parentNode.removeChild(child);
                }
                continue;
            }
            if (isSkippedFromSlides(child)) {
                continue;
            }
            if (isSection(child)) {
                var group = el('section');
                container.appendChild(group);
                buildLevel(group, child);
            } else {
                if (!current) {
                    startSlide();
                }
                current.appendChild(child);
            }
        }
        normalize(container);
    }

    function exitPresentation() {
        window.location.href = window.location.pathname;
    }

    function transform() {
        var root = unwrapTitleRoot(findContentRoot());
        var revealEl = el('div', 'reveal');
        var slides = el('div', 'slides');
        revealEl.appendChild(slides);

        // Content before the first section becomes the title slide(s).
        // The group is appended to slides first so that it is the
        // opening slide of the presentation.
        var titleGroup = el('section', 'revealjs-title');
        slides.appendChild(titleGroup);
        var current = null;
        var startPre = function () {
            current = el('section');
            titleGroup.appendChild(current);
        };
        var kids = significantChildren(root);
        for (var i = 0; i < kids.length; i++) {
            var child = kids[i];
            if (child.tagName === 'HR' && cfg.breakOnHr !== false) {
                current = null;
                if (child.parentNode) {
                    child.parentNode.removeChild(child);
                }
                continue;
            }
            if (isSkippedFromSlides(child)) {
                continue;
            }
            if (isSection(child)) {
                var group = el('section', 'revealjs-section');
                slides.appendChild(group);
                buildLevel(group, child);
            } else {
                if (!current) {
                    startPre();
                }
                current.appendChild(child);
            }
        }
        normalize(titleGroup);
        // Mark a leading h1 slide as the title slide.
        var firstChild = titleGroup.firstElementChild;
        if (firstChild && firstChild.tagName === 'SECTION' &&
            firstChild.firstElementChild &&
            firstChild.firstElementChild.tagName === 'H1') {
            firstChild.classList.add('revealjs-title-slide');
        } else if (firstChild && firstChild.tagName === 'H1') {
            titleGroup.classList.add('revealjs-title-slide');
        }
        if (significantChildren(titleGroup).length === 0) {
            slides.removeChild(titleGroup);
        }
        if (significantChildren(slides).length === 0) {
            // Nothing usable found: fall back to the normal page.
            document.documentElement.classList.remove('revealjs-mode');
            return;
        }

        // Drop any page-only elements that ended up nested inside a
        // built slide (e.g. an epigraph inside a container).  Top-level
        // skips were never moved and remain on the normal page.
        var dropped = slides.querySelectorAll('.revealjs-noslide, blockquote.epigraph');
        for (var d = 0; d < dropped.length; d++) {
            if (dropped[d].parentNode) {
                dropped[d].parentNode.removeChild(dropped[d]);
            }
        }

        document.body.appendChild(revealEl);

        var options = {
            embedded: false,
            hash: true,
            controls: true,
            progress: true,
            keyboard: true,
            overview: true,
            center: false,
            transition: 'fade',
        };
        if (window.revealjsOptions) {
            for (var k in window.revealjsOptions) {
                options[k] = window.revealjsOptions[k];
            }
        }

        Promise.resolve(Reveal.initialize(options)).then(function () {
            document.body.classList.add('revealjs-ready');
            if (cfg.onDone) {
                cfg.onDone();
            }
        }, function (err) {
            if (window.console) {
                console.error('revealjs: reveal init failed', err);
            }
            document.documentElement.classList.remove('revealjs-mode');
        });
        window.__revealjsReveal = Reveal;

        var exitBtn = el('button', 'revealjs-exit');
        exitBtn.setAttribute('aria-label', 'Exit presentation mode');
        exitBtn.title = 'Exit presentation (x)';
        exitBtn.textContent = '✕';
        exitBtn.addEventListener('click', exitPresentation);
        document.body.appendChild(exitBtn);

        window.addEventListener('keydown', function (ev) {
            if ((ev.key === 'x' || ev.key === 'X') &&
                !ev.ctrlKey && !ev.metaKey && !ev.altKey) {
                exitPresentation();
            }
        });

        // Keep presentation mode when following internal links.
        revealEl.addEventListener('click', function (ev) {
            var t = ev.target;
            var a = null;
            while (t && t !== revealEl) {
                if (t.tagName === 'A') {
                    a = t;
                    break;
                }
                t = t.parentNode;
            }
            if (!a) {
                return;
            }
            var href = a.getAttribute('href') || '';
            if (!href || href.charAt(0) === '#') {
                return;  // in-page anchors and reveal.js hash links
            }
            var url;
            try {
                url = new URL(href, window.location.href);
            } catch (err) {
                return;
            }
            if (url.origin !== window.location.origin) {
                return;  // external link
            }
            if (url.pathname === window.location.pathname) {
                return;  // same page
            }
            ev.preventDefault();
            url.hash = '';
            url.search = cfg.param || 'revealjs';
            window.location.href = url.href;
        });
    }

    // Called by bootstrap.js once the DOM and all assets are ready.
    window.__revealjsTransform = transform;

})();

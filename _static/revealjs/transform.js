/*
 * revealjs transform: turn the current Sphinx page into a reveal.js
 * presentation.  Called by bootstrap.js once the DOM and all assets
 * are ready.  See sphinx_misc_rkdarst/revealjs.py for the overall
 * design.
 *
 * Rules:
 * - The content root ([role=main] / main / article / div.body) becomes
 *   the reveal.js deck IN PLACE: it gets the "reveal" class and a
 *   .slides container, and the content is regrouped into slide
 *   <section>s inside it.  The content never leaves its original
 *   ancestors (e.g. .rst-content in sphinx_rtd_theme), so all of the
 *   site's own stylesheet rules keep applying to the slide content.
 *   Single-child wrapper elements between the root and the content
 *   (theme wrappers such as sphinx_rtd_theme's <div
 *   itemprop="articleBody">, and the <section> starting with the <h1>
 *   document title that docutils >=0.18 emits) are bypassed and
 *   hidden.
 * - Content before the first section becomes the title slide.
 * - Each child <section> (or div.section) becomes a slide; nested
 *   sections become vertical (sub)slides.
 * - Divider (cfg.ellipsisNotes, data-ellipsis-notes, conf.py
 *   revealjs_ellipsis_notes, default true): a paragraph containing
 *   only `...` (reST/MyST; smartquotes renders the three dots as a
 *   single ellipsis character) ends the presented material of the
 *   current slide; the following siblings (up to the next divider,
 *   section or explicit break) become that slide's audience notes --
 *   kept out of the slides and appended, in a
 *   .revealjs-audience-notes wrapper (preceded by a separating rule
 *   when the slide has real notes), into the slide's
 *   <aside class="notes"> below the real speaker notes.  A second
 *   divider flushes the block and re-opens slide mode, so doubled
 *   dividers act as a plain break.
 * - A plain <hr> (reST ----, MyST ---) forces a slide break at the
 *   current level (hidden) when cfg.breakOnHr is not false; legacy
 *   cfg.hrNotes (revealjs_hr_notes) re-enables <hr> as an additional
 *   divider instead.
 * - hr.revealjs-break (the revealjs-break directive) splits slides
 *   explicitly, in every mode.
 * - The transform is non-destructive: nodes only move within the
 *   original subtree, everything else is done by adding classes
 *   (exit reloads the page anyway).
 */
(function () {
    'use strict';

    if (window.__revealjsTransformed) {
        return;
    }
    window.__revealjsTransformed = true;

    var cfg = window.__revealjsConfig || {};

    // Elements that will be hidden once the transform commits
    // (consumed <hr>s and page-only elements).  Deferred so that a
    // failed transform (nothing usable) falls back to a pristine page.
    var toHide = [];

    // Audience notes collected while building (divider mode): records
    // {owner: owning slide section (null = deferred: attach to the
    // level's first slide), container: the level's slide container,
    // kids: [moved elements]}.  Resolved into <aside class="notes">
    // elements per level in finalizeLevel(), before that level's
    // normalization.  Reset per transform() run.
    var audienceNotes = [];

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
    // - theme chrome that some themes inject inside the content root
    //   (nav/footer/header, aside.sidebar: prev/next links,
    //   breadcrumbs, ...).  docutils never emits these tags as
    //   document content (but it does use plain <aside> for footnotes
    //   and citations, so bare <aside> must not be excluded).
    function isPageOnlyElement(node) {
        if (node.nodeType !== Node.ELEMENT_NODE) {
            return false;
        }
        if (node.classList.contains('revealjs-noslide')) {
            return true;
        }
        if (node.tagName === 'BLOCKQUOTE' &&
            node.classList.contains('epigraph')) {
            return true;
        }
        if (node.tagName === 'NAV' || node.tagName === 'FOOTER' ||
            node.tagName === 'HEADER') {
            return true;
        }
        return node.tagName === 'ASIDE' &&
            node.classList.contains('sidebar');
    }

    // Content root candidates, in priority order; the first match in
    // document order wins.  Themes with a different structure often
    // still work via the document.body fallback plus
    // unwrapContentRoot(); add selectors here for new themes.
    var ROOT_SELECTORS = [
        '[role="main"]',
        'main',
        'article',
        'div.body',
        'div.document',
    ];

    function findContentRoot() {
        for (var i = 0; i < ROOT_SELECTORS.length; i++) {
            var found = document.querySelector(ROOT_SELECTORS[i]);
            if (found) {
                return found;
            }
        }
        return document.body;
    }

    function unwrapContentRoot(root) {
        // Some themes wrap the document in extra single-child
        // elements.  While the node has exactly one significant child,
        // descend through such wrappers so that the document's real
        // children are treated as the content.  Two wrapper kinds:
        //
        // - Plain DIV/MAIN/ARTICLE wrappers (e.g. sphinx_rtd_theme's
        //   <div itemprop="articleBody">): descended through only if
        //   they contain a section below, so that meaningful styling
        //   wrappers without slide structure are left alone.
        // - A single <section> starting with the <h1> document title
        //   (how docutils >=0.18 renders the document): descended
        //   into so that its subsections become top-level slides.
        var cur = root;
        var shells = [];
        for (;;) {
            var kids = significantChildren(cur);
            if (kids.length !== 1 || isPageOnlyElement(kids[0])) {
                break;
            }
            var kid = kids[0];
            if (isSection(kid)) {
                var first = kid.firstElementChild;
                if (!first || first.tagName !== 'H1') {
                    break;
                }
            } else if (kid.tagName === 'DIV' || kid.tagName === 'MAIN' ||
                       kid.tagName === 'ARTICLE') {
                if (!kid.querySelector('section, div.section')) {
                    break;
                }
            } else {
                break;
            }
            shells.push(kid);
            cur = kid;
        }
        return { source: cur, shells: shells };
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

    // Per-level builder state, shared by the title-slide loop in
    // transform() and buildLevel (both handle children identically;
    // only the section recursion differs, which the caller does).
    function newLevelState(startSlide, container) {
        return {
            container: container,
            current: null,   // slide under construction
            startSlide: startSlide,
            inNotes: false,  // inside an audience-notes block
            owner: null,     // slide the open audience block belongs to
            audience: null,  // collected audience elements while inNotes
        };
    }

    // Close an open audience block: record it for injection into the
    // owning slide's <aside class="notes"> after the deck is built.
    // An empty block (e.g. between two consecutive dividers) is
    // discarded, so a doubled divider acts as a plain break.
    function flushAudience(st) {
        st.inNotes = false;
        if (st.audience && st.audience.length) {
            audienceNotes.push({
                owner: st.owner,
                container: st.container,
                kids: st.audience,
            });
        }
        st.audience = null;
        st.owner = null;
    }

    // `...` alone on a line: a quiet audience-notes divider (a lone
    // ellipsis paragraph; smartquotes renders the three dots as a
    // single character).  Pure text only -- no inline markup.
    function isEllipsisDivider(child) {
        return child.tagName === 'P' && !child.firstElementChild &&
            /^(\u2026|\.\.\.)$/.test((child.textContent || '').trim());
    }

    // Open or close the audience-notes block: the first divider
    // closes the current slide and opens its block, the next one
    // flushes the block and re-opens slide mode.
    function toggleAudience(st) {
        if (st.inNotes) {
            flushAudience(st);
            st.current = null;
        } else {
            st.owner = st.current;
            st.current = null;
            st.inNotes = true;
            st.audience = [];
        }
    }

    // Handle one child of a level.  Returns 'consumed' (nothing more
    // to do), 'section' (the caller recurses into it), or 'content'
    // (the caller appends the child to st.current).
    //
    // Divider rules (see the file header): hr.revealjs-break always
    // splits slides; a lone-ellipsis paragraph closes the current
    // slide and opens its audience-notes block when cfg.ellipsisNotes
    // is on (the default), and a second divider flushes the block and
    // re-opens slide mode; a plain <hr> does the same only with the
    // legacy cfg.hrNotes, else it splits slides when cfg.breakOnHr is
    // not false (else it is ordinary slide content).
    function levelChild(st, child) {
        if (child.tagName === 'HR' &&
            child.classList.contains('revealjs-break')) {
            if (st.inNotes) {
                flushAudience(st);
            }
            st.current = null;
            toHide.push(child);
            return 'consumed';
        }
        if (cfg.ellipsisNotes !== false && isEllipsisDivider(child)) {
            toggleAudience(st);
            toHide.push(child);
            return 'consumed';
        }
        if (child.tagName === 'HR' && cfg.hrNotes !== false) {
            // Legacy opt-in: <hr> also acts as a divider.
            toggleAudience(st);
            toHide.push(child);
            return 'consumed';
        }
        if (child.tagName === 'HR' && cfg.breakOnHr !== false) {
            if (st.inNotes) {
                // A break also closes an open audience block.
                flushAudience(st);
            }
            st.current = null;
            toHide.push(child);
            return 'consumed';
        }
        if (st.inNotes) {
            if (isPageOnlyElement(child)) {
                toHide.push(child);
                return 'consumed';
            }
            if (!isSection(child)) {
                st.audience.push(child);
                return 'consumed';
            }
            // A section always starts fresh: an open audience block
            // belongs to the preceding slide.
            flushAudience(st);
            st.current = null;
            return 'section';
        }
        if (isPageOnlyElement(child)) {
            toHide.push(child);
            return 'consumed';
        }
        if (isSection(child)) {
            return 'section';
        }
        if (!st.current) {
            st.startSlide();
        }
        return 'content';
    }

    // First leaf slide under `container` (descending through nested
    // slide groups), or null when the container built no slide.
    function firstLeafSlide(container) {
        var s = container.firstElementChild;
        while (s && s.firstElementChild &&
               s.firstElementChild.tagName === 'SECTION') {
            s = s.firstElementChild;
        }
        return s && s.tagName === 'SECTION' ? s : null;
    }

    // Finish a level: flush its open audience block, convert the
    // level's directive notes containers to reveal's <aside
    // class="notes">, and inject the level's audience notes into their
    // owning slide's aside (below the real speaker notes).  All of
    // this happens before normalize() so that owner references stay
    // valid when a single-slide group is unwrapped (the aside moves
    // with the slide's children).  Deferred blocks (an <hr> that
    // opened notes with no preceding slide in the level) attach to the
    // level's first slide; a level that built no slide drops them (the
    // content just stays on the normal page).
    function finalizeLevel(container, st) {
        flushAudience(st);
        var notes = container.querySelectorAll('.revealjs-notes');
        for (var ni = 0; ni < notes.length; ni++) {
            var note = notes[ni];
            var noteAside = el('aside', 'notes');
            while (note.firstChild) {
                noteAside.appendChild(note.firstChild);
            }
            // Reveal's css hides aside.notes in the main view; the
            // normal-page hiding must not carry over.
            noteAside.removeAttribute('hidden');
            noteAside.removeAttribute('style');
            note.parentNode.replaceChild(noteAside, note);
        }
        for (var ai = 0; ai < audienceNotes.length; ai++) {
            var rec = audienceNotes[ai];
            if (!rec || rec.container !== container) {
                continue;
            }
            audienceNotes[ai] = null;
            var owner = rec.owner || firstLeafSlide(container);
            if (!owner) {
                continue;
            }
            var slideAside = null;
            for (var oc = owner.firstElementChild; oc;
                 oc = oc.nextElementSibling) {
                if (oc.tagName === 'ASIDE' &&
                    oc.classList.contains('notes')) {
                    slideAside = oc;
                    break;
                }
            }
            if (!slideAside) {
                slideAside = el('aside', 'notes');
                owner.appendChild(slideAside);
            }
            var audienceWrap = el('div', 'revealjs-audience-notes');
            if (slideAside.firstElementChild) {
                // Visually separate the audience notes from the real
                // speaker notes above them; an aside created just for
                // this block (no real notes) gets no leading rule.
                audienceWrap.appendChild(el('hr'));
            }
            for (var ak = 0; ak < rec.kids.length; ak++) {
                audienceWrap.appendChild(rec.kids[ak]);
            }
            slideAside.appendChild(audienceWrap);
        }
        normalize(container);
    }

    // Distribute the children of `source` into slide <section>s
    // appended to `container`.  Sections become nested slide groups;
    // <hr> handling follows the mode rules (see levelChild).
    function buildLevel(container, source) {
        var st = newLevelState(function () {
            st.current = el('section');
            container.appendChild(st.current);
            return st.current;
        }, container);

        var kids = significantChildren(source);
        for (var i = 0; i < kids.length; i++) {
            var child = kids[i];
            var kind = levelChild(st, child);
            if (kind === 'consumed') {
                continue;
            }
            if (kind === 'section') {
                var group = el('section');
                container.appendChild(group);
                buildLevel(group, child);
                continue;
            }
            st.current.appendChild(child);
        }
        finalizeLevel(container, st);
    }

    function exitPresentation() {
        window.location.href = window.location.pathname;
    }

    function resumeKey() {
        return 'revealjs-resume:' + window.location.pathname;
    }

    function transform() {
        toHide = [];
        audienceNotes = [];
        var revealEl = findContentRoot();
        var unwrapped = unwrapContentRoot(revealEl);
        var source = unwrapped.source;

        // Build the deck in place (see the header comment).  Typography
        // splits on the theme decision (bootstrap's cfg.themed):
        // - With a loaded theme, the theme's own base font size (e.g.
        //   40px) and em-based type ratios stand as-is; presentation.css
        //   pins body text, line-heights and code to that base so the
        //   site's px rules (sphinx_rtd_theme's 16px p / 12px pre) can't
        //   fight the theme, and re-asserts the theme's heading ratios
        //   against site rules like alabaster's div.body h1.
        // - Without a theme, the deck base is a percentage of the page's
        //   ambient body text size (% on the container resolves against
        //   its parent), and fontScale (data attr, conf.py
        //   revealjs_font_scale) rescales it for presentation;
        //   presentation.css supplies normalized proportions.  Either
        //   way there are no computed-style reads: CSS does the scaling,
        //   and reveal's uniform fit-to-window scaling does the rest.
        var fontScale = parseFloat(cfg.fontScale);
        if (!isFinite(fontScale) || fontScale <= 0) {
            fontScale = 1;
        }
        revealEl.classList.add('reveal');
        if (!cfg.themed) {
            revealEl.style.fontSize = (fontScale * 100) + '%';
        }

        var slides = el('div', 'slides');
        var kids = significantChildren(source);
        revealEl.insertBefore(slides, revealEl.firstChild);

        // Content before the first section becomes the title slide(s).
        // The group is appended to slides first so that it is the
        // opening slide of the presentation.
        var titleGroup = el('section', 'revealjs-title');
        slides.appendChild(titleGroup);
        var st = newLevelState(function () {
            st.current = el('section');
            titleGroup.appendChild(st.current);
            return st.current;
        }, titleGroup);
        for (var i = 0; i < kids.length; i++) {
            var child = kids[i];
            var kind = levelChild(st, child);
            if (kind === 'consumed') {
                continue;
            }
            if (kind === 'section') {
                var group = el('section', 'revealjs-section');
                slides.appendChild(group);
                buildLevel(group, child);
                continue;
            }
            st.current.appendChild(child);
        }
        finalizeLevel(titleGroup, st);
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
            // Nothing usable found: fall back to the normal page and
            // undo the in-place setup (nothing has been moved).
            revealEl.classList.remove('reveal');
            revealEl.style.fontSize = '';
            revealEl.removeChild(slides);
            document.documentElement.classList.remove('revealjs-mode');
            return;
        }

        // Commit the deferred hiding: page-only elements and consumed
        // <hr>s at the top level, the bypassed wrapper shells, and any
        // page-only elements that ended up nested inside a built slide
        // (e.g. an epigraph inside a container).
        var pending = toHide.concat(unwrapped.shells);
        for (var h = 0; h < pending.length; h++) {
            pending[h].classList.add('revealjs-hidden');
        }
        var dropped = slides.querySelectorAll(
            '.revealjs-noslide, blockquote.epigraph, ' +
            'nav, footer, header, aside.sidebar');
        for (var d = 0; d < dropped.length; d++) {
            dropped[d].classList.add('revealjs-hidden');
        }

        // Speaker-notes conversion (directive .revealjs-notes
        // containers to <aside class="notes">) and audience-notes
        // injection happen per level in finalizeLevel(), before
        // normalization, so slide references stay valid.

        // Hide everything that is not part of the deck's ancestor
        // chain (sidebar, breadcrumbs, footer, ...) and mark the chain
        // itself so that CSS can neutralize containing-block traps (a
        // transformed ancestor would anchor the fixed-position deck to
        // itself instead of the viewport).
        var n = revealEl;
        while (n && n !== document.body && n.parentNode) {
            var parent = n.parentNode;
            for (var s = parent.firstElementChild; s; s = s.nextElementSibling) {
                if (s !== n) {
                    s.classList.add('revealjs-hidden');
                }
            }
            if (parent === document.body) {
                n.classList.add('revealjs-keep');
            } else {
                parent.classList.add('revealjs-ctx');
            }
            n = parent;
        }

        var options = {
            embedded: false,
            hash: true,
            controls: true,
            progress: true,
            keyboard: true,
            overview: true,
            center: false,
            transition: 'fade',
            plugins: (window.RevealNotes ? [window.RevealNotes] : []),
        };
        var mergeOptions = function (extra) {
            for (var k in extra) {
                if (Object.prototype.hasOwnProperty.call(extra, k)) {
                    options[k] = extra[k];
                }
            }
        };
        if (window.revealjsOptions) {
            mergeOptions(window.revealjsOptions);
        }
        // Site-wide (conf.py revealjs_options) and per-page
        // (revealjs-options docinfo / MyST front matter) options are
        // merged by Sphinx and injected as a JSON <meta> tag; they
        // override the defaults and window.revealjsOptions.  The meta
        // tag must be read before reveal's setupDOM runs below.
        var meta = document.querySelector('meta[name="revealjs-options"]');
        if (meta) {
            try {
                mergeOptions(JSON.parse(meta.content));
            } catch (err) {
                if (window.console) {
                    console.error('revealjs: bad options meta', err);
                }
            }
        }
        // Structural: the deck is built in place and fullscreen.
        options.embedded = false;
        if (options.slideNumber) {
            // "controls: false" suppresses the slide number too; keep
            // them readable without the control arrows.
            options.controls = true;
            options.controlsTutorial = false;
        }

        Promise.resolve(Reveal.initialize(options)).then(function () {
            document.body.classList.add('revealjs-ready');
            // Resume where this page was last presented (per page, in
            // localStorage).  A #/h/v hash in the URL is reveal's own
            // deep link and takes precedence.
            if (!window.location.hash) {
                try {
                    var saved = JSON.parse(
                        window.localStorage.getItem(resumeKey()) || 'null');
                    if (saved && saved[0] > 0 &&
                        saved[0] < Reveal.getTotalSlides()) {
                        Reveal.slide(saved[0], saved[1] || 0);
                    }
                } catch (err) { /* storage unavailable */ }
            }
            Reveal.on('slidechanged', function () {
                try {
                    var idx = Reveal.getIndices();
                    window.localStorage.setItem(
                        resumeKey(), JSON.stringify([idx.h, idx.v]));
                } catch (err) { /* storage unavailable */ }
            });
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

        // Exit button (disabled for now -- the `x` shortcut below keeps
        // working; re-enable when wanted):
        // var exitBtn = el('button', 'revealjs-exit');
        // exitBtn.setAttribute('aria-label', 'Exit presentation mode');
        // exitBtn.title = 'Exit presentation (x)';
        // exitBtn.textContent = '✕';
        // exitBtn.addEventListener('click', exitPresentation);
        // document.body.appendChild(exitBtn);

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

# sphinx-misc-rkdarst

Various sphinx extensions under testing.  I may use these in my
projects, but I probably wouldn't recommend others to use them, since
they may not be very stable.  [Live
demo](https://aaltoscicomp.github.io/rse-training/site-map/).

Some of these may be significantly AI-coded so should not be
considered reliable yet.  If anyone wants to make a version that is
not AI-generated, please do.  If any of these get reliable/stable
enough for general use, they will probably be split off into a
dedicated module.

If anyone does want these to be finalized, let me know and I might be
able to work on it.


## site-map (`sphinx_misc_rkdarst.site_map`)

A directive `site-map` that adds a site map.  It is a unordered list with every
page in the toctree in order.  There are options `include-orphans` to
have a section with every document not in the toctree and
`include-sections` to also include sections within the build.


## Inline expandable note (`sphinx_misc_rkdarst.inote`)

This provides an inline role for an expandable note.  This is like a
footnote but you click and it expands in-place.  [Live
demo](https://rkdarst.github.io/sphinx-misc-rkdarst/).

ReST:

```rst
Basic: :inote:`This appears when clicked.`

Custom prefix: :inote:`[advanced] Custom text for the message.`
```

MyST:

```markdown
Basic: {inote}`This appears when clicked.`

Custom prefix: {inote}`[advanced] Custom text for the message.`
```

## Missing page placeholders (`sphinx_misc_rkdarst.missing_page_stubs`)

This will avoid errors on missing internal document references, and
instead add the path instead of having the link missing (because Sphinx
will drop) those missing references.  This was made for a case where we
had one Sphinx site, with internal pages missing in the public build.
Viewers should know something is missing (just the path).

See the source for configuration options.  By default it will placehold
missing pages.  If you add `missing_page_toctree_hook = True`, and a placeholder
page referred to by `missing_page_target`, it will also replace the
pages in the table of contents tree.

This extension may be a bit fragile, especially `missing_page_toctree_hook` which non-public Sphinx APIs.

`suppress_warnings = ['toc.not_readable']` will hide remaining
warnings.

If you have broken symlinks, you should probably get them ignored.
That can be done this way:

```
exclude_patterns += [str(p.relative_to(Path(__file__).parent/"contents"))
                     for p in Path(__file__).parent.rglob("contents/*")
                     if p.is_symlink() and not p.exists()
					 ]
```

This extension is still being worked out and is not perfect yet.


## sphinx-wordcount-builder

A builder that doesn't build anything, but print a word count.  What
is a word is not well defined (same as the one below), so don't trust
this so much.  Instead of this, you could consider building to text
documents and counting words in that by a proper word counting
program.


## sphinx-wordcount

When this extension is loaded, it prints out a word count when you
build (when built with any other builder)

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

## Stubs for toctree missing files (`sphinx_misc_rkdarst.toctree_missing_files`)

This will avoid errors on missing toctree pages, and instead add a
stub page (PAGENAME-stub) saying "this page is not available in this
build".  You can see some config options in the source.

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

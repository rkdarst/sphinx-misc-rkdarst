"""Say so when a document is referred to but not part of the build.

Add the extension to ``extensions`` in conf.py::

    extensions = ['sphinx_misc_rkdarst.toctree_missing_pages']

Configuration, all of it optional::

    # Shown instead of the link. "%(path)s" is the root-relative document
    # name without a source suffix, here "/internal/lecture-3".
    toctree_missing_text = '%(path)s (not present in this build)'

    # Text of an entry put back into a toctree, which is read as one entry
    # among many and so usually wants saying more briefly than in running
    # text. Not set means the text above. Only used by the hook below.
    toctree_missing_toc_text = '%(path)s (not in this build)'

    # A page that explains where the missing material is, included in the
    # build the normal way. When it is set and found, the text above becomes
    # a link to it.
    toctree_missing_target = 'missing-pages'

    # Handle only these documents, matched as prefixes of the root-relative
    # document name. Everything else keeps Sphinx's own warning, so a typo in
    # another part of the documentation is still reported. Not set means
    # "handle all of them", which is also what hides typos.
    toctree_missing_paths = ('/internal/', '/other/internal')

    # Also keep missing pages in the table of contents. Off by default,
    # because it replaces the toctree directive; see "Toctrees" below.
    toctree_missing_hook = False

References
==========

A ``:doc:`` reference is looked at only after it has failed to resolve, and
only after Intersphinx has had its chance, so a document that exists in
another project's inventory still links there. The reference is replaced by
``toctree_missing_text``, linked to ``toctree_missing_target`` when that is
configured, and Sphinx does not warn about it. Each replaced document is
reported once as an INFO line so that a build can be audited for what was
hidden. The text is a ``toctree-missing`` inline element, so it can be styled
from a CSS file.

``:ref:`` and ``:any:`` targets are left to Sphinx, as are references whose
name is not matched by ``toctree_missing_paths``. A replacement is only inline,
in the document that held the reference, so it never adds anything to a table
of contents on its own. It does appear in one if the reference sat inside a
section title, because there the title carries it.

Toctrees
========

An entry of a ``.. toctree::`` directive that names a missing document is
thrown away while the file is read, before any event is emitted, so it cannot
be handled the way references are. The directive is therefore taken over by a
subclass of Sphinx's own, and ``toctree_missing_hook`` turns that part on: an
entry is added back for every document that was dropped, at the end of the
same toctree, linking to ``toctree_missing_target``. Note that:

* it needs ``toctree_missing_target``, because a toctree entry has to point
  somewhere and the missing document cannot be pointed at;
* the entry ends up last rather than in the place it was written, since a
  dropped entry leaves no position behind;
* the entry is shown with ``toctree_missing_toc_text``, or with
  ``toctree_missing_text`` when that is not set. Both are plain strings, so a
  text without ``%(path)s`` makes every restored entry say the same thing.
  Where the toctree is rendered, it is rendered with these entries in it,
  sidebar included;
* Sphinx still warns about the entry. Silence that with
  ``suppress_warnings = ['toc.read_missing_file']``.

No files are ever written
=========================

Nothing is added to the source directory, and nothing pretends that a missing
document exists: whether a document is there is decided from the set of
documents Sphinx actually found, never by looking for a file name on disk. A
document whose suffix comes from an extension (``.md`` through MyST, say) is
therefore treated exactly like any other.
"""

from __future__ import annotations

import posixpath
import re
from typing import TYPE_CHECKING

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.directives.other import TocTree
from sphinx.errors import NoUri
from sphinx.util import logging, url_re
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from sphinx import addnodes
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment

logger = logging.getLogger(__name__)

# "Title <document>", as used by toctree entries and by the doc role. Written
# out here instead of importing sphinx.util.nodes.explicit_title_re so that the
# number of the target group does not depend on Sphinx.
_EXPLICIT_TITLE = re.compile(r"^(.*?)\s*<([^<>]*)>\s*$")

# Characters that make a toctree entry a pattern instead of one document.
_GLOB_CHARS = "*?["

# Documents already reported, so that a page referred to in many places is
# mentioned once. In parallel write mode each process reports its own share.
_reported: set[str] = set()


def _found_docs(app: Sphinx) -> set:
    """The document names that are part of this build.

    This is what the ``toctree`` directive itself uses to decide whether an
    entry exists. ``Project.discover()`` is only a fallback for a Sphinx that
    would stop keeping the set on the environment.
    """
    docs = getattr(app.env, "found_docs", None)
    if docs is not None:
        return docs
    return app.env.project.discover()


def _docname(target: str, from_docname: str) -> str:
    """Root-relative document name of *target*, or '' if it is not a document.

    A leading "/" is relative to the top of the source directory and anything
    else to the directory of the referring document, which is how both the
    ``toctree`` directive and the doc role read them.
    """
    target = target.partition("#")[0].strip()
    if not target or target == "self" or "://" in target or url_re.match(target):
        return ""
    if target.startswith("/"):
        path = target[1:]
    else:
        path = posixpath.join(posixpath.dirname(from_docname), target)
    path = posixpath.normpath(path)
    if path in ("", ".") or path == ".." or path.startswith("../"):
        return ""  # outside of the source directory, nothing to say about it
    return path


def _is_missing(docs, docname: str) -> bool:
    """Whether *docname* is a document that is not in this build."""
    if not docname or docname in docs:
        return False
    # A reference may name a source file ("page.md") instead of a document.
    # Sphinx strips a known suffix before looking it up, so the same is done
    # here, without having to know which suffixes an extension has registered.
    stem = posixpath.splitext(docname)[0]
    return not (stem and stem in docs)


def _matches(config: Config, docname: str) -> bool:
    """Whether *docname* is one of the documents to do anything about.

    ``toctree_missing_paths`` holds prefixes of the root-relative document
    name, and matches a document with that name as well as everything below
    it. Anything not matched is left to Sphinx to warn about.
    """
    if not config.toctree_missing_paths:
        return True
    prefixes = config.toctree_missing_paths
    if isinstance(prefixes, str):
        prefixes = (prefixes,)  # one prefix without a comma is a common mistake
    for prefix in prefixes:
        prefix = str(prefix).strip().strip("/")
        if prefix and (docname == prefix or docname.startswith(prefix + "/")):
            return True
    return False


def _substitute(value: str, name: str, docname: str) -> str:
    """*value* with ``%(path)s`` filled in with the root-relative name."""
    try:
        return value % {"path": "/" + docname}
    except (KeyError, TypeError, ValueError) as error:
        # The name of the config value is put into the message instead of into
        # its arguments, because Sphinx remembers a warning by the message as
        # it is written, and the two config values that come through here have
        # to each be able to report a problem of their own.
        logger.warning(
            "toctree_missing_pages: %s cannot be used (%s), showing the "
            "document name on its own" % (name, error),
            once=True,
        )
        return "/" + docname


def _text(config: Config, docname: str) -> str:
    """Text shown where a link to a missing document stood."""
    return _substitute(
        config.toctree_missing_text, "toctree_missing_text", docname
    )


def _toc_text(config: Config, docname: str) -> str:
    """Text of the toctree entry put back for a missing document.

    A toctree is a list of short entries read one after another, which is a
    different thing to write for than running text, so it has a text of its
    own. Leaving it unset keeps the text used elsewhere.
    """
    value = config.toctree_missing_toc_text
    if value is None:
        return _text(config, docname)
    return _substitute(value, "toctree_missing_toc_text", docname)


def _report(docname: str, from_docname: str, what: str) -> None:
    """Tell once per document what has been replaced, for auditing a build."""
    if docname in _reported:
        return
    _reported.add(docname)
    # Not once=True: Sphinx remembers the message as written here, so only the
    # first document would ever be reported.
    logger.info(
        "toctree_missing_pages: replaced %s to /%s in %s",
        what,
        docname,
        from_docname,
    )


def _link_docname(app: Sphinx) -> str:
    """Document to link the replacements to, '' if there is nothing to link."""
    target = _docname(app.config.toctree_missing_target or "", "")
    if not target:
        return ""
    if _is_missing(_found_docs(app), target):
        logger.warning(
            "toctree_missing_pages: toctree_missing_target %r is not a document "
            "in this build, so the replacements are shown without a link",
            target,
            once=True,
        )
        return ""
    return target


def _missing_reference(
    app: Sphinx,
    env: BuildEnvironment,
    node: addnodes.pending_xref,
    contnode: nodes.Element,
) -> nodes.Element | None:
    """Say what a ``:doc:`` reference points at when it is not in the build.

    Connected to ``missing-reference``, which happens while a page is written
    and after Intersphinx has tried to resolve the reference, so no document
    can be added to the build from here and nothing that resolves is disturbed.
    """
    if node.get("reftype") != "doc":
        return None

    from_docname = node.get("refdoc") or env.docname
    docname = _docname(node.get("reftarget", ""), from_docname)
    if not docname or not _is_missing(_found_docs(app), docname):
        return None
    if not _matches(app.config, docname):
        return None  # not ours to hide: Sphinx will report it

    _report(docname, from_docname, "a reference")
    text = nodes.Text(_text(app.config, docname))
    link = _link_docname(app)
    if link:
        try:
            uri = app.builder.get_relative_uri(from_docname, link)
        except NoUri:
            uri = None
        if uri is not None:
            # A link that stays inside the documentation, so that writers do
            # not style it as one leaving it.
            return nodes.reference(
                "",
                text,
                refuri=uri,
                internal=True,
                classes=["toctree-missing"],
            )
    return nodes.inline("", text, classes=["toctree-missing"])


def _entry_docname(line: str, from_docname: str, glob: bool) -> str:
    """Document name named by one content line of a ``toctree`` directive."""
    line = line.strip()
    if not line or line[0] in ":.":
        return ""  # an option, a comment, or a nested directive
    if glob and any(character in line for character in _GLOB_CHARS):
        return ""  # a pattern covering more than one document
    explicit = _EXPLICIT_TITLE.match(line)
    if explicit:
        line = explicit.group(2).strip()
    return _docname(line, from_docname)


class MissingTocTree(TocTree):
    """The ``toctree`` directive, keeping an eye on the entries Sphinx drops.

    Registered in every build so that ``toctree_missing_hook`` can be set per
    project, and does nothing at all unless it is set. See "Toctrees" in the
    module docstring for what it does and for what it cannot do.
    """

    def parse_content(self, toctree: addnodes.toctree) -> None:
        super().parse_content(toctree)
        app = self.env.app
        if not app.config.toctree_missing_hook:
            return

        link = _link_docname(app)
        if not link:
            return

        docs = _found_docs(app)
        kept = {docname for _title, docname in toctree["entries"]}
        for line in self.content:
            docname = _entry_docname(line, self.env.docname, toctree.get("glob", False))
            if not docname or docname in kept:
                continue
            if not _is_missing(docs, docname):
                continue
            if not _matches(app.config, docname):
                continue
            _report(docname, self.env.docname, "a toctree entry")
            # An entry is a (title, reference) pair, so the text set here is
            # what a table of contents shows for it, and the reference is the
            # page it points at rather than the missing document.
            toctree["entries"].append((_toc_text(app.config, docname), link))
            kept.add(docname)


def _check_hook(app: Sphinx, config: Config) -> None:
    """Say so if the toctree hook cannot work with this version of Sphinx."""
    if config.toctree_missing_hook and not hasattr(TocTree, "parse_content"):
        logger.warning(
            "toctree_missing_pages: this version of Sphinx has no "
            "TocTree.parse_content(), so toctree_missing_hook does nothing"
        )


def setup(app: Sphinx) -> ExtensionMetadata:
    # Sphinx compares the type of a value in conf.py against the type of the
    # default, so the types of an unset value have to be named here to keep it
    # from warning about a value that is simply left at None.
    app.add_config_value(
        "toctree_missing_text", "%(path)s (not present in this build)", "env", [str]
    )
    app.add_config_value(
        "toctree_missing_toc_text", None, "env", [str, type(None)]
    )
    app.add_config_value(
        "toctree_missing_target", None, "env", [str, type(None)]
    )
    app.add_config_value(
        "toctree_missing_paths",
        None,
        "env",
        [str, list, tuple, set, frozenset, type(None)],
    )
    app.add_config_value("toctree_missing_hook", False, "env", [bool])

    # Intersphinx answers missing-reference at priority 500, so stay behind it.
    app.connect("missing-reference", _missing_reference, priority=900)

    # A plain subclass: without the hook it behaves as the stock directive.
    app.add_directive("toctree", MissingTocTree, override=True)
    app.connect("config-inited", _check_hook)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


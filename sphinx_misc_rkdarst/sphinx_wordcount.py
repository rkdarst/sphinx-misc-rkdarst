# wordcount_extension.py
from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from docutils import nodes


WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _iter_text(node: nodes.Node) -> Iterable[str]:
    """Yield visible text from a doctree, skipping non-content nodes."""
    skip = (
        nodes.system_message,
        nodes.figure,
        nodes.image,
        nodes.raw,
    )
    for child in node.traverse(include_self=False):
        if isinstance(child, skip):
            continue
        if isinstance(child, nodes.Text):
            yield str(child)


def _count_words_in_doctree(doctree: nodes.document) -> int:
    text = " ".join(_iter_text(doctree))
    return len(WORD_RE.findall(text))


def _on_doctree_resolved(app, doctree, docname):
    if not hasattr(app.env, "_wordcount_by_doc"):
        app.env._wordcount_by_doc = {}

    app.env._wordcount_by_doc[docname] = _count_words_in_doctree(doctree)


def _on_build_finished(app, exception):
    if exception is not None:
        return

    counts = getattr(app.env, "_wordcount_by_doc", {})
    total = sum(counts.values())

    print("\nWord count report")
    print(f"  documents: {len(counts)}")
    print(f"  words:     {total}")


def setup(app):
    app.connect("doctree-resolved", _on_doctree_resolved)
    app.connect("build-finished", _on_build_finished)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

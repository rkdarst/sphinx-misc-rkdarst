# wordcount_builder.py
from __future__ import annotations

import re
from typing import Iterable

from docutils import nodes
from sphinx.builders import Builder


WORD_RE = re.compile(r"\b[\w'-]+\b", re.UNICODE)


def _iter_text(node: nodes.Node) -> Iterable[str]:
    for child in node.traverse(include_self=False):
        if isinstance(child, (nodes.system_message, nodes.figure, nodes.image, nodes.raw)):
            continue
        if isinstance(child, nodes.Text):
            yield str(child)


def _count_words_in_doctree(doctree: nodes.document) -> int:
    text = " ".join(_iter_text(doctree))
    return len(WORD_RE.findall(text))


class WordCountBuilder(Builder):
    name = "wordcount"
    format = ""  # no output files

    def init(self) -> None:
        self._counts: dict[str, int] = {}

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        pass

    def write_doc(self, docname, doctree):
        self._counts[docname] = _count_words_in_doctree(doctree)

    def finish(self):
        total = sum(self._counts.values())
        print("\nWord count report")
        print(f"  documents: {len(self._counts)}")
        print(f"  words:     {total}")


def setup(app):
    app.add_builder(WordCountBuilder)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

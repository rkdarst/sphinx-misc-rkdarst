"""
hnote - A Sphinx extension that provides an inline role for hidden notes.

Usage in reStructuredText:
    :hnote:`This is the hidden note text that will be revealed on click.`

This renders as "[hnote]" which expands to show the full text when clicked.
"""
from __future__ import annotations

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import roles
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata


class hnote(nodes.Inline, nodes.TextElement):
    """Custom node for inline hidden notes."""
    pass


def _hnote_role(name: str, rawtext: str, text: str, lineno: int,
                inliner, options: dict = None, content: list = None):
    """
    Role for creating inline hidden notes.

    Usage: :hnote:`Your note text here`
    Usage with prefix: :hnote:`[tip] Your note text here`
    """
    import re

    if options is None:
        options = {}

    # Normalize text: replace newlines and multiple spaces with single space
    hnote_text = ' '.join(text.split())

    # Check for prefix in brackets at the start, e.g., [tip], default is 'note'
    prefix_match = re.match(r'^\[([^\]]+)\]\s*(.*)', hnote_text)
    if prefix_match:
        prefix = prefix_match.group(1)
        # Remove the prefix from the text, keep the rest
        hnote_text = ' '.join(prefix_match.group(2).split())
    else:
        # No prefix found, use default 'note' and keep original text
        prefix = 'note'

    hnote_id = options.get('id', '')

    node = hnote()
    node['text'] = hnote_text
    node['prefix'] = prefix
    node['ids'] = [hnote_id] if hnote_id else []

    return [node], []


def resolve_hnote(app, doctree, docname):
    """Resolve hnote nodes in the doctree."""
    pass


def html_visit_hnote(self, node):
    """Generate HTML for inline hidden note - collapsed state with static content."""
    import html as html_module

    hnote_text = node.get('text', '')
    prefix = node.get('prefix', 'note')

    # Escape special characters for HTML
    escaped_text = html_module.escape(hnote_text)
    escaped_prefix = html_module.escape(prefix)

    # Create a collapsible span with click handler that toggles a class
    # The full content is always in the DOM, just hidden via CSS
    self.body.append(
        f'<span class="hnote" onclick="this.classList.toggle(\'expanded\')">'
        f'[{escaped_prefix}'
        f'<span class="hnote-content">: {escaped_text}</span>'
        f']</span>'
    )


def html_depart_hnote(self, node):
    """No departure action needed."""
    pass


def text_visit_hnote(self, node):
    """Generate text output for inline hidden note - expanded state."""
    hnote_text = node.get('text', '')
    prefix = node.get('prefix', 'note')
    self.add_text(f'[{prefix}: {hnote_text}]')


def latex_visit_hnote(self, node):
    """Generate LaTeX output for inline hidden note - expanded state."""
    hnote_text = node.get('text', '')
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: {hnote_text}]')


def man_visit_hnote(self, node):
    """Generate man page output for inline hidden note - expanded state."""
    hnote_text = node.get('text', '')
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: {hnote_text}]')


def texinfo_visit_hnote(self, node):
    """Generate Texinfo output for inline hidden note - expanded state."""
    hnote_text = node.get('text', '')
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: {hnote_text}]')


def setup(app: Sphinx) -> ExtensionMetadata:
    """Setup the inline hidden note extension."""
    # Add the custom node
    # HTML: collapsed/collapsible state
    # Other formats: expanded state (show full text)
    app.add_node(
        hnote,
        html=(html_visit_hnote, html_depart_hnote),
        latex=(latex_visit_hnote, html_depart_hnote),
        text=(text_visit_hnote, html_depart_hnote),
        man=(man_visit_hnote, html_depart_hnote),
        texinfo=(texinfo_visit_hnote, html_depart_hnote),
    )

    # Register the role
    roles.register_local_role('hnote', _hnote_role)

    # Add the _static directory to html_static_path
    static_path = Path(__file__).parent / '_static'

    def _add_hnote_static_path(app):
        app.config.html_static_path.append(str(static_path))

    app.connect('builder-inited', _add_hnote_static_path)

    # Add CSS file by relative filename
    app.add_css_file('hnote.css')

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'enhance_html': True,
    }

"""
inote - A Sphinx extension that provides an inline role for inline notes.

Usage in reStructuredText:
    :inote:`This is the inline note text that will be revealed on click.`

This renders as "[inote]" which expands to show the full text when clicked.
"""
from __future__ import annotations

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import roles
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata


class inote(nodes.Inline, nodes.TextElement):
    """Custom node for inline notes."""
    pass


def _inote_role(name: str, rawtext: str, text: str, lineno: int,
                inliner, options: dict = None, content: list = None):
    """
    Role for creating inline notes with recursive parsing.

    Usage: :inote:`Your note text here`
    Usage with prefix: :inote:`[tip] Your note text here`
    Usage with markup: :inote:`This has *emphasis* and `code` text`
    """
    import re

    if options is None:
        options = {}

    # Check for prefix in brackets at the start, e.g., [tip], default is 'note'
    prefix_match = re.match(r'^\[([^\]]+)\]\s*(.*)', text)
    if prefix_match:
        prefix = prefix_match.group(1)
        inote_text = ' '.join(prefix_match.group(2).split())
    else:
        # No prefix found, use default 'note'
        prefix = 'note'
        inote_text = ' '.join(text.split())

    # Parse the inner content recursively to support markup
    inner_nodes, messages = inliner.parse(
        inote_text, lineno, inliner, inliner
    )

    inote_id = options.get('id', '')

    node = inote()
    node['prefix'] = prefix
    node['ids'] = [inote_id] if inote_id else []

    # Add the parsed inner nodes as children
    node.extend(inner_nodes)

    return [node], messages


def resolve_inote(app, doctree, docname):
    """Resolve inote nodes in the doctree."""
    pass


def html_visit_inote(self, node):
    """Generate opening HTML for inline note."""
    import html as html_module

    prefix = node.get('prefix', 'note')

    # Open the collapsible span structure with ARIA attributes for accessibility
    self.body.append(
        f'<span class="inote" '
        f'role="button" '
        f'aria-expanded="false" '
        f'aria-label="Inline note: {html_module.escape(prefix)} - click to expand" '
        f'onclick="this.classList.toggle(\'expanded\'); '
        f'this.setAttribute(\'aria-expanded\', this.classList.contains(\'expanded\'));">'
        f'[{html_module.escape(prefix)}'
        f'<span class="inote-content">: '
    )


def html_depart_inote(self, node):
    """Close the HTML structure for inline note."""
    # Close the spans opened in visit_inote
    self.body.append('</span>]</span>')


def text_visit_inote(self, node):
    """Generate opening text for inline note."""
    prefix = node.get('prefix', 'note')
    self.add_text(f'[{prefix}: ')


def text_depart_inote(self, node):
    """Close the text output for inline note."""
    self.add_text(']')


def latex_visit_inote(self, node):
    """Generate opening LaTeX for inline note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def latex_depart_inote(self, node):
    """Close the LaTeX output for inline note."""
    self.body.append(']')


def man_visit_inote(self, node):
    """Generate opening man page output for inline note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def man_depart_inote(self, node):
    """Close the man page output for inline note."""
    self.body.append(']')


def texinfo_visit_inote(self, node):
    """Generate opening Texinfo output for inline note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def texinfo_depart_inote(self, node):
    """Close the Texinfo output for inline note."""
    self.body.append(']')


def setup(app: Sphinx) -> ExtensionMetadata:
    """Setup the inline note extension."""
    # Add the custom node
    # HTML: collapsed/collapsible state
    # Other formats: expanded state (show full text)
    app.add_node(
        inote,
        html=(html_visit_inote, html_depart_inote),
        latex=(latex_visit_inote, latex_depart_inote),
        text=(text_visit_inote, text_depart_inote),
        man=(man_visit_inote, man_depart_inote),
        texinfo=(texinfo_visit_inote, texinfo_depart_inote),
    )

    # Register the role
    roles.register_local_role('inote', _inote_role)

    # Add the _static directory to html_static_path
    static_path = Path(__file__).parent / '_static'

    def _add_inote_static_path(app):
        app.config.html_static_path.append(str(static_path))

    app.connect('builder-inited', _add_inote_static_path)

    # Add CSS file by relative filename
    app.add_css_file('inote.css')

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
        'enhance_html': True,
    }
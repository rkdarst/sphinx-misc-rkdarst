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
    Role for creating inline hidden notes with recursive parsing.

    Usage: :hnote:`Your note text here`
    Usage with prefix: :hnote:`[tip] Your note text here`
    Usage with markup: :hnote:`This has *emphasis* and `code` text`
    """
    import re

    if options is None:
        options = {}

    # Check for prefix in brackets at the start, e.g., [tip], default is 'note'
    prefix_match = re.match(r'^\[([^\]]+)\]\s*(.*)', text)
    if prefix_match:
        prefix = prefix_match.group(1)
        hnote_text = ' '.join(prefix_match.group(2).split())
    else:
        # No prefix found, use default 'note'
        prefix = 'note'
        hnote_text = ' '.join(text.split())

    # Parse the inner content recursively to support markup
    inner_nodes, messages = inliner.parse(
        hnote_text, lineno, inliner, inliner
    )

    hnote_id = options.get('id', '')

    node = hnote()
    node['prefix'] = prefix
    node['ids'] = [hnote_id] if hnote_id else []

    # Add the parsed inner nodes as children
    node.extend(inner_nodes)

    return [node], messages


def resolve_hnote(app, doctree, docname):
    """Resolve hnote nodes in the doctree."""
    pass


def html_visit_hnote(self, node):
    """Generate opening HTML for inline hidden note."""
    import html as html_module

    prefix = node.get('prefix', 'note')

    # Open the collapsible span structure with ARIA attributes for accessibility
    self.body.append(
        f'<span class="hnote" '
        f'role="button" '
        f'aria-expanded="false" '
        f'aria-label="Hidden note: {html_module.escape(prefix)} - click to expand" '
        f'onclick="this.classList.toggle(\'expanded\'); '
        f'this.setAttribute(\'aria-expanded\', this.classList.contains(\'expanded\'));">'
        f'[{html_module.escape(prefix)}'
        f'<span class="hnote-content">: '
    )


def html_depart_hnote(self, node):
    """Close the HTML structure for inline hidden note."""
    # Close the spans opened in visit_hnote
    self.body.append('</span>]</span>')


def text_visit_hnote(self, node):
    """Generate opening text for inline hidden note."""
    prefix = node.get('prefix', 'note')
    self.add_text(f'[{prefix}: ')


def text_depart_hnote(self, node):
    """Close the text output for inline hidden note."""
    self.add_text(']')


def latex_visit_hnote(self, node):
    """Generate opening LaTeX for inline hidden note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def latex_depart_hnote(self, node):
    """Close the LaTeX output for inline hidden note."""
    self.body.append(']')


def man_visit_hnote(self, node):
    """Generate opening man page output for inline hidden note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def man_depart_hnote(self, node):
    """Close the man page output for inline hidden note."""
    self.body.append(']')


def texinfo_visit_hnote(self, node):
    """Generate opening Texinfo output for inline hidden note."""
    prefix = node.get('prefix', 'note')
    self.body.append(f'[{prefix}: ')


def texinfo_depart_hnote(self, node):
    """Close the Texinfo output for inline hidden note."""
    self.body.append(']')


def setup(app: Sphinx) -> ExtensionMetadata:
    """Setup the inline hidden note extension."""
    # Add the custom node
    # HTML: collapsed/collapsible state
    # Other formats: expanded state (show full text)
    app.add_node(
        hnote,
        html=(html_visit_hnote, html_depart_hnote),
        latex=(latex_visit_hnote, latex_depart_hnote),
        text=(text_visit_hnote, text_depart_hnote),
        man=(man_visit_hnote, man_depart_hnote),
        texinfo=(texinfo_visit_hnote, texinfo_depart_hnote),
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

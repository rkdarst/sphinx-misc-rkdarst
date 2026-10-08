# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Test 1'
copyright = '2026, Author1'
author = 'Author1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_misc_rkdarst.inote',
    'sphinx_misc_rkdarst.site_map',
    'sphinx_misc_rkdarst.toctree_missing_pages',
    ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


supress_warnings = ''
from pathlib import Path
print()
exclude_patterns += [str(p.relative_to(Path(__file__).parent)) for p in Path(__file__).parent.rglob("*") if p.is_symlink() and not p.exists()]
#exclude_patterns += [str(p.relative_to(Path(__file__).parent/"contents")) for p in Path(__file__).parent.rglob("contents/*") if p.is_symlink() and not p.exists()]
print(exclude_patterns)

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

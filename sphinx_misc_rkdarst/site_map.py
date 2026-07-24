from __future__ import annotations

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.util.nodes import make_refnode
from sphinx.util.typing import ExtensionMetadata


class site_map_node(nodes.General, nodes.Element):
    pass


class SiteMapDirective(Directive):
    has_content = False
    option_spec = {
        "root-page": directives.unchanged,
        "show-hidden": directives.flag,
        "include-sections": directives.flag,
        "include-orphans": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        node = site_map_node()
        node["root_page"] = self.options.get("root-page")
        node["show_hidden"] = "show-hidden" in self.options
        node["include_sections"] = "include-sections" in self.options
        node["include_orphans"] = "include-orphans" in self.options
        return [node]


def _make_doc_link(builder, from_doc: str, target_doc: str, text: str) -> nodes.reference:
    return make_refnode(builder, from_doc, target_doc, "", nodes.Text(text))


def _build_section_list(section: nodes.section) -> nodes.bullet_list | None:
    ul = nodes.bullet_list()
    found = False

    for child in section.children:
        if not isinstance(child, nodes.section):
            continue

        title_node = next((c for c in child.children if isinstance(c, nodes.title)), None)
        if title_node is None:
            continue

        li = nodes.list_item()
        li += nodes.paragraph("", "", nodes.Text("§ " + title_node.astext()))

        sub = _build_section_list(child)
        if sub is not None and len(sub):
            li += sub

        ul += li
        found = True

    return ul if found else None


def _build_site_map(
    env,
    builder,
    docname: str,
    seen: set[str],
    show_hidden: bool,
    include_sections: bool,
) -> nodes.bullet_list:
    if docname in seen:
        return nodes.bullet_list()

    seen = set(seen)
    seen.add(docname)

    doctree = env.get_doctree(docname)
    ul = nodes.bullet_list()

    for toctree in doctree.findall(addnodes.toctree):
        if toctree.get("hidden", False) and not show_hidden:
            continue

        toctree_items = nodes.bullet_list()

        for title, ref in toctree["entries"]:
            if ref == "self":
                target = docname
                text = title or env.titles[docname].astext()
            else:
                target = ref
                if target not in env.found_docs:
                    continue
                text = title or env.titles.get(target, nodes.title(text=target)).astext()

            li = nodes.list_item()
            p = nodes.paragraph()
            p += _make_doc_link(builder, docname, target, text)
            li += p

            if include_sections:
                target_doctree = env.get_doctree(target)
                section_list = _build_section_list(target_doctree)
                if section_list is not None and len(section_list):
                    li += section_list

            child = _build_site_map(env, builder, target, seen, show_hidden, include_sections)
            if len(child):
                li += child

            toctree_items += li

        caption = toctree.get("caption")
        if caption:
            caption_li = nodes.list_item()
            caption_p = nodes.paragraph()
            caption_p += nodes.strong(text=caption)
            caption_li += caption_p
            caption_li += toctree_items
            ul += caption_li
        else:
            ul += toctree_items[:]

    return ul


def _collect_reachable_docs(
    env,
    docname: str,
    seen: set[str],
    show_hidden: bool,
) -> set[str]:
    if docname in seen:
        return seen

    seen = set(seen)
    seen.add(docname)

    doctree = env.get_doctree(docname)
    for toctree in doctree.findall(addnodes.toctree):
        if toctree.get("hidden", False) and not show_hidden:
            continue
        for _, ref in toctree["entries"]:
            if ref == "self":
                target = docname
            else:
                target = ref
            if target in env.found_docs:
                _collect_reachable_docs(env, target, seen, show_hidden)

    return seen


def _build_orphan_list(env, builder, root_doc: str, reachable: set[str]) -> nodes.bullet_list | None:
    ul = nodes.bullet_list()
    found = False

    for docname in sorted(env.found_docs):
        if docname in reachable:
            continue

        title = env.titles.get(docname, nodes.title(text=docname)).astext()

        li = nodes.list_item()
        p = nodes.paragraph()
        p += _make_doc_link(builder, root_doc, docname, title)
        li += p
        ul += li
        found = True

    return ul if found else None


def resolve_site_map(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    env = app.env
    builder = app.builder

    for node in doctree.findall(site_map_node):
        root_doc = node.get("root_page") or app.config.root_doc
        show_hidden = node.get("show_hidden", False)
        include_sections = node.get("include_sections", False)
        include_orphans = node.get("include_orphans", False)

        if root_doc not in env.found_docs:
            node.replace_self(nodes.warning("", nodes.paragraph(text=f"Unknown root page: {root_doc}")))
            continue

        main_map = _build_site_map(env, builder, root_doc, set(), show_hidden, include_sections)

        if include_orphans:
            reachable = _collect_reachable_docs(env, root_doc, set(), show_hidden)
            orphan_list = _build_orphan_list(env, builder, root_doc, reachable)
            if orphan_list is not None and len(orphan_list):
                orphan_li = nodes.list_item()
                orphan_p = nodes.paragraph()
                orphan_p += nodes.strong(text="Pages not linked from the TOC tree")
                orphan_li += orphan_p
                orphan_li += orphan_list
                main_map += orphan_li

        node.replace_self(main_map)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_node(site_map_node)
    app.add_directive("site-map", SiteMapDirective)
    app.connect("doctree-resolved", resolve_site_map)

    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

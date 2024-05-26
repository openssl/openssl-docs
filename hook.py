import marko
from marko.md_renderer import MarkdownRenderer
from marko.block import Heading
from mkdocs.structure.nav import Section
from mkdocs.structure.pages import Page

parser = marko.Markdown(renderer=MarkdownRenderer)

def on_page_markdown(source_md, page, config, files):
    if "index.md" in page.file.src_uri or "fips.md" in page.file.src_uri:
        return source_md
    new_children = []
    h1_parsed = parser.parse(f"# {page.file.name}")
    h1 = h1_parsed.children[0]
    new_children.append(h1)
    parsed = parser.parse(source_md)
    for child in parsed.children:
        if not isinstance(child, Heading):
            new_children.append(child)
            continue
        heading_text = f"#{parser.render(child)}"
        heading = parser.parse(heading_text)
        new_children.append(heading)
    parsed.children = new_children
    return parser.render(parsed)

nav_map = {
    "index": "Home",
    "fips": "FIPS-140",
    "Man1": "Commands",
    "Man3": "Libraries",
    "Man5": "File Formats",
    "Man7": "Overviews"
}

def on_nav(nav, config, files):
    for item in nav.items:
        if isinstance(item, Section):
            item.title = nav_map[item.title]
        if isinstance(item, Page):
            item.title = nav_map[item.file.name]
    return nav

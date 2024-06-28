import marko
from marko.md_renderer import MarkdownRenderer
from marko.block import Heading
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Link
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig
import shutil

MAN_INDEXES = ["man1/index.md", "man3/index.md", "man5/index.md", "man7/index.md"]
SKIP_FILES = ["index.md", "fips.md"]


def get_names_paragraph(content: str) -> str:
    paragraph_lines = []
    append = False
    for line in content.splitlines():
        if line == "# NAME":
            append = True
            continue
        if line.startswith("# "):
            break
        if append:
            paragraph_lines.append(line)
    return " ".join(paragraph_lines)
        

def get_names(content: str) -> list[str]:
    names_paragraph = get_names_paragraph(content)
    names = names_paragraph.replace("\\", "").strip().replace("\n", " ").split(" - ")[0].strip().split(",")
    return [name for name in names if name.strip()]


def get_description(content: str) -> str:
    names_paragraph = get_names_paragraph(content)
    return names_paragraph.replace("\\", "").strip().replace("\n", " ").split(" - ")[1].strip()


def on_pre_build(config: MkDocsConfig) -> None:
    shutil.copytree("scaffold", "docs", dirs_exist_ok=True)


def populate_index_content(source_md: str, page: Page, files: Files) -> str:
    current_man_dir = page.parent.title.lower()
    rows = []
    for man_file in files.documentation_pages():
        if man_file.src_uri in SKIP_FILES + MAN_INDEXES:
            continue
        man_dir = man_file.page.parent.title.lower()
        if man_dir != current_man_dir:
            continue
        description = get_description(man_file.content_string)
        names = get_names(man_file.content_string)
        for name in names:
            # e.g. "openssl/core_dispatch.h" to "openssl-core_dispatch.h"
            name = name.strip().replace("/", "-")
            row = f"| [{name}]({man_file.name}.md) | {description} |"
            rows.append(row)
    return source_md + "\n".join(sorted(rows))


def fix_headings(source_md: str, page: Page) -> str:
    parser = marko.Markdown(renderer=MarkdownRenderer)
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


def on_page_markdown(source_md: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri in SKIP_FILES:
        return source_md
    if page.file.src_uri in MAN_INDEXES:
        return populate_index_content(source_md, page, files)
    return fix_headings(source_md, page)


def populate_nav(files: Files) -> dict[str, list[Link]]:
    navigation_children = {
        "man1": [],
        "man3": [],
        "man5": [],
        "man7": [],
    }
    for man_file in files.documentation_pages():
        if man_file.src_uri in SKIP_FILES + MAN_INDEXES:
            continue
        man_dir = man_file.page.parent.title.lower()
        names = get_names(man_file.content_string)
        for name in names:
            # e.g. "openssl/core_dispatch.h" to "openssl-core_dispatch.h"
            name = name.strip().replace("/", "-")
            if name == man_file.name:
                continue
            link = Link(title=name, url=f"{man_dir}/{man_file.name}")
            navigation_children[man_dir].append(link)
    return navigation_children


def on_nav(nav: Navigation, config: MkDocsConfig, files: Files) -> Navigation:
    nav_map = {
        "index": "Home",
        "fips": "FIPS-140",
        "man1": "Commands",
        "man3": "Libraries",
        "man5": "File Formats",
        "man7": "Overviews"
    }
    nav_children = populate_nav(files)
    for item in nav.items:
        if item.is_section:
            man_dir = item.title.lower()
            sorted_children = item.children[1:] + nav_children[man_dir]
            sorted_children = sorted(sorted_children, key=lambda item: item.title or item.file.name)
            item.children = [item.children[0], *sorted_children]
            item.title = nav_map[man_dir]
        if item.is_page:
            item.title = nav_map[item.file.name]
    return nav

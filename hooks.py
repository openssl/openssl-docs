import marko
from marko.md_renderer import MarkdownRenderer
from marko.block import Heading
from mkdocs.structure.files import Files
from mkdocs.config.defaults import MkDocsConfig
from mkdocs import plugins
import pathlib
import shutil

CURRENT_DIR = pathlib.Path(__file__).parent
SKIP_FILES = ["index.md", "fips.md", "man1/index.md", "man3/index.md", "man5/index.md", "man7/index.md"]
SEARCH_EXCLUSION = (
"""---
search:
  exclude: true
---\n
"""
)

commands_index = CURRENT_DIR / "docs" / "man1" / "index.md"
libraries_index = CURRENT_DIR / "docs" / "man3" / "index.md"
formats_index = CURRENT_DIR / "docs" / "man5" / "index.md"
overview_index = CURRENT_DIR / "docs" / "man7" / "index.md"


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
        

def get_names(content: str) -> str:
    names_paragraph = get_names_paragraph(content)
    return names_paragraph.replace("\\", "").strip().replace("\n", " ").split(" - ")[0].strip().split(",")


def get_description(content: str) -> str:
    names_paragraph = get_names_paragraph(content)
    return names_paragraph.replace("\\", "").strip().replace("\n", " ").split(" - ")[1].strip()


def on_pre_build(config: MkDocsConfig):
    shutil.copytree(CURRENT_DIR / "scaffold", CURRENT_DIR / "docs", dirs_exist_ok=True)


@plugins.event_priority(10)
def create_aliases(files: Files, config: MkDocsConfig):
    for man_page in files.documentation_pages():
        if man_page.src_uri in SKIP_FILES:
            continue
        man_dir = man_page.src_uri.split("/")[0]
        names = get_names(man_page.content_string)
        for name in names:
            # e.g. "openssl/core_dispatch.h" to "openssl-core_dispatch.h"
            name = name.strip().replace("/", "-")
            if name == man_page.name or not name:
                continue
            alias_path = CURRENT_DIR / "docs" / man_dir / f"{name}.md"
            with open(alias_path, "w") as alias_fd:
                alias_fd.write(SEARCH_EXCLUSION)
                alias_fd.write(man_page.content_string)
            alias_file = man_page.generated(config, f"{man_dir}/{name}.md", abs_src_path=alias_path)
            files.append(alias_file)
    return files


@plugins.event_priority(0)
def create_indexes(files: Files, config: MkDocsConfig):
    commands_index_rows = []
    libraries_index_rows = []
    formats_index_rows = []
    overview_index_rows = []
    for man_page in files.documentation_pages():
        if man_page.src_uri in SKIP_FILES:
            continue
        description = get_description(man_page.content_string)
        row = f"| [{man_page.name}]({man_page.name}.md) | {description} |\n"
        if man_page.src_uri.startswith("man1"):
            commands_index_rows.append(row)
        elif man_page.src_uri.startswith("man3"):
            libraries_index_rows.append(row)
        elif man_page.src_uri.startswith("man5"):
            formats_index_rows.append(row)
        elif man_page.src_uri.startswith("man7"):
            overview_index_rows.append(row)
    with open(commands_index, mode="a") as commands_index_fd:
        commands_index_fd.writelines(sorted(commands_index_rows))
    with open(libraries_index, mode="a") as libraries_index_fd:
        libraries_index_fd.writelines(sorted(libraries_index_rows))
    with open(formats_index, mode="a") as formats_index_fd:
        formats_index_fd.writelines(sorted(formats_index_rows))
    with open(overview_index, mode="a") as overview_index_fd:
        overview_index_fd.writelines(sorted(overview_index_rows))
    return files


on_files = plugins.CombinedEvent(create_aliases, create_indexes)


def on_page_markdown(source_md, page, config: MkDocsConfig, files: Files):
    """
    Fix headings to correctly display TOC in the right sidebar
    """
    parser = marko.Markdown(renderer=MarkdownRenderer)
    if page.file.src_uri in SKIP_FILES:
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


def on_nav(nav, config: MkDocsConfig, files: Files):
    """
    Rename navigation items
    """
    nav_map = {
        "index": "Home",
        "fips": "FIPS-140",
        "Man1": "Commands",
        "Man3": "Libraries",
        "Man5": "File Formats",
        "Man7": "Overviews"
    }
    for item in nav.items:
        if item.is_section:
            item.title = nav_map[item.title]
        if item.is_page:
            item.title = nav_map[item.file.name]
    return nav

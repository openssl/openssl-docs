import logging
import os
import re
import shutil
from pathlib import Path

import minify_html
from mkdocs import plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Link
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page

from code_language import CodeLanguageExtension

log = logging.getLogger("mkdocs.hooks")

MAN_INDEXES = ["man1/index.md", "man3/index.md", "man5/index.md", "man7/index.md"]
SKIP_FILES = ["index.md", "fips.md", "OpenSSL300Design.md", "OpenSSLStrategicArchitecture.md"]
LINKS_PATTERN = re.compile(r"\.\.\/\.\.\/man[1357]\/[a-zA-Z0-9_\-.]+")
HEADINGS_PATTERN = re.compile(r"^(#{1,6})((?=\s)[^\n]*?|[^\n\S]*)(?:(?<=\s)(?<!\\)#+)?[^\n\S]*$\n?", flags=re.M)
LINKS_MAP = {}
REDIRECT_PAGES = {}
# src_uri -> (man_dir, names, description); parsed once in on_files and reused by the index and nav builders
MAN_PAGES: dict[str, tuple[str, list[str], str]] = {}


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


def parse_name_section(content: str, src_uri: str) -> tuple[list[str], str]:
    """Return the names and the description from the NAME section: "name1, name2 - description".

    Names are normalised the way they appear in links, e.g. "openssl/core_dispatch.h" becomes
    "openssl-core_dispatch.h". A page without a " - " separator yields an empty description and a
    warning instead of failing the whole build.
    """
    paragraph = get_names_paragraph(content).replace("\\", "").strip()
    names_part, separator, description = paragraph.partition(" - ")
    if not separator:
        log.warning(f"{src_uri}: NAME section has no ' - ' separator, description will be empty")
    names = [name.strip().replace("/", "-") for name in names_part.split(",")]
    return [name for name in names if name], description.strip()


def on_config(config: MkDocsConfig) -> MkDocsConfig:
    config.markdown_extensions.append(CodeLanguageExtension())
    return config


def on_pre_build(config: MkDocsConfig) -> None:
    shutil.copytree("scaffold", "docs", dirs_exist_ok=True)


def on_files(files: Files, config: MkDocsConfig) -> Files | None:
    for man_file in files.documentation_pages():
        if man_file.src_uri in SKIP_FILES + MAN_INDEXES:
            continue
        man_dir = Path(man_file.src_uri).parent.name
        names, description = parse_name_section(man_file.content_string, man_file.src_uri)
        MAN_PAGES[man_file.src_uri] = (man_dir, names, description)
        for name in names:
            LINKS_MAP[f"../../{man_dir}/{name}"] = f"../{man_dir}/{man_file.name}.md"
            if name != man_file.name:
                redirect_page_uri = f"{man_file.dest_dir}/{man_dir}/{name}"
                source_page_uri = Path(f"../../{man_file.dest_uri}")
                REDIRECT_PAGES[redirect_page_uri] = source_page_uri.parent
    return files


def populate_index_content(source_md: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri not in MAN_INDEXES:
        return source_md
    current_man_dir = Path(page.file.src_uri).parent.name
    rows = []
    for man_file in files.documentation_pages():
        if man_file.src_uri not in MAN_PAGES:
            continue
        man_dir, names, description = MAN_PAGES[man_file.src_uri]
        if man_dir != current_man_dir:
            continue
        for name in names:
            rows.append(f"| [{name}]({man_file.name}.md) | {description} |")
    return source_md + "\n".join(sorted(rows))


def replace_link(match: re.Match) -> str:
    return LINKS_MAP.get(match.group()) or match.group()


def replace_heading(match: re.Match) -> str:
    return f"#{match.group()}"


def fix_markdown(source_md: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri in SKIP_FILES + MAN_INDEXES:
        return source_md
    if page.file.name.startswith("life_cycle-"):
        source_md = source_md.replace('<img src="', '<img src="../')
    source_md = LINKS_PATTERN.sub(replace_link, source_md)
    source_md = HEADINGS_PATTERN.sub(replace_heading, source_md)
    source_md = f"# {page.file.name}\n" + source_md
    return source_md


on_page_markdown = plugins.CombinedEvent(fix_markdown, populate_index_content)


def populate_nav(files: Files) -> dict[str, list[Link]]:
    navigation_children = {
        "man1": [],
        "man3": [],
        "man5": [],
        "man7": [],
    }
    for man_file in files.documentation_pages():
        if man_file.src_uri not in MAN_PAGES:
            continue
        man_dir, names, _ = MAN_PAGES[man_file.src_uri]
        for name in names:
            if name == man_file.name:
                continue
            navigation_children[man_dir].append(Link(title=name, url=f"{man_dir}/{man_file.name}"))
    return navigation_children


def on_nav(nav: Navigation, config: MkDocsConfig, files: Files) -> Navigation:
    nav_map = {
        "index": "Home",
        "fips": "FIPS-140",
        "OpenSSL300Design": "OpenSSL 3.0.0 Design (Draft)",
        "OpenSSLStrategicArchitecture": "OpenSSL Strategic Architecture",
        "man1": "Commands",
        "man3": "Libraries",
        "man5": "File Formats",
        "man7": "Overviews",
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


def on_post_page(output: str, page: Page, config: MkDocsConfig) -> str:
    return minify_html.minify(output)


def on_post_build(config: MkDocsConfig):
    template = (
        '<!DOCTYPE html><html lang="en"><head><meta name="robots" content="noindex"><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url={}"></head></html>'
    )
    for redirect_page_uri, source_page_uri in REDIRECT_PAGES.items():
        path = Path(redirect_page_uri)
        try:
            os.makedirs(path)
        except FileExistsError:
            continue
        index_html = path / "index.html"
        index_html.write_text(template.format(source_page_uri))

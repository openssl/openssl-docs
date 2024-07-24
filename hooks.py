import os
import re
import shutil
import string
from pathlib import Path

import htmlmin
from mkdocs import plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Link
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page

MAN_INDEXES = ["man1/index.md", "man3/index.md", "man5/index.md", "man7/index.md"]
SKIP_FILES = ["index.md", "fips.md"]
LINKS_PATTERN = re.compile(r"\.\.\/\.\.\/man[1,3,5,7]{1}\/[a-zA-Z0-9_\-.]+")
HEADINGS_PATTERN = re.compile(r" {0,3}(#{1,6})((?=\s)[^\n]*?|[^\n\S]*)(?:(?<=\s)(?<!\\)#+)?[^\n\S]*$\n?", flags=re.M)
LINKS_MAP = {}
REDIRECT_PAGES = {}


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


def on_files(files: Files, config: MkDocsConfig) -> Files | None:
    for man_file in files.documentation_pages():
        if man_file.src_uri in SKIP_FILES + MAN_INDEXES:
            continue
        man_dir = Path(man_file.src_uri).parent
        names = get_names(man_file.content_string)
        for name in names:
            # e.g. "openssl/core_dispatch.h" to "openssl-core_dispatch.h"
            name = name.strip().replace("/", "-")
            LINKS_MAP[f"../../{man_dir}/{name}"] = f"../{man_dir}/{man_file.name}.md"
            if name != man_file.name:
                redirect_page_uri = f"{man_file.dest_dir}/{man_dir}/{name}"
                source_page_uri = f"../../{man_file.dest_uri}"
                REDIRECT_PAGES[redirect_page_uri] = source_page_uri
    return files


def populate_index_content(source_md: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri not in MAN_INDEXES:
        return source_md
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
    return htmlmin.minify(output, remove_comments=True, remove_empty_space=True)


def on_post_build(config: MkDocsConfig):
    template = '<!DOCTYPE html><html lang="en"><head><meta name="robots" content="noindex"><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={}"></head></html>'
    for redirect_page_uri, source_page_uri in REDIRECT_PAGES.items():
        path = Path(redirect_page_uri)
        os.makedirs(path)
        index_html = path / "index.html"
        index_html.write_text(template.format(source_page_uri))

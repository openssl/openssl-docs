"""Syntax highlighting for the indented code blocks produced by pod2markdown.

POD verbatim blocks carry no language, so pod2markdown emits plain indented code blocks and
pymdownx.highlight renders them as text. The rules below recognise the three kinds of code that make
up the vast majority of the blocks (C, shell commands, OpenSSL config files); anything without a
clear signal stays unhighlighted.
"""

import re

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from pymdownx.highlight import Highlight
from pymdownx.highlight import HighlightExtension

C_LINE = re.compile(
    r"^\s*#\s*(include|define|ifn?def|endif|if)\b"  # preprocessor
    r"|^\s*(/\*|\*/|//)"  # comments
    r"|^\s*(typedef|struct|union|enum|static|extern|const|unsigned|void|int|char|long|size_t)\b.*[;{(]"
    r"|^\s*(unsigned |const |struct )?\w+\s*\**\s*\w+(\[\w*\])?\s*;"  # declaration
    r"|^\s*[{}]\s*$"  # brace-only line
    r"|\)\s*;\s*$"  # call or prototype ending in ');'
    r"|[\w)\]]\s*(=|\+=|-=|\|=|&=|->|\+\+|--)\s*[\w(&*\"'-].*;\s*$"  # assignment statement
    r"|\b(NULL|return|if|for|while|goto|sizeof)\b.*[;({]\s*$",
    re.M,
)
SHELL_FIRST_LINE = re.compile(
    r"^\s*(\$\s|openssl\s|CA\.pl\s|\./\w|sudo\s|make\b|perl\s|git\s|cd\s|export\s|cat\s|echo\s|chmod\s|env\s|tsget\s)"
)
INI_SECTION = re.compile(r"^\s*\[\s*[\w. -]+\s*\]\s*$", re.M)
INI_KEY = re.compile(r"^\s*[\w.$]+(\s*[\w.$]+)?\s*=\s*\S", re.M)


def detect_language(code: str) -> str | None:
    """Return the Pygments lexer name for a code block, or None when there is no clear signal."""
    lines = [line for line in code.split("\n") if line.strip()]
    if not lines:
        return None
    first = lines[0].lstrip()
    if first.startswith("-----BEGIN"):
        return None
    if SHELL_FIRST_LINE.match(first):
        return "console" if first.startswith("$") else "bash"
    c_hits = len(C_LINE.findall(code))
    if c_hits and (c_hits >= 2 or len(lines) <= 2 or c_hits / len(lines) >= 0.2):
        return "c"
    if INI_SECTION.search(code) or len(INI_KEY.findall(code)) >= 2:
        return "ini"
    return None


class CodeLanguageTreeprocessor(Treeprocessor):
    """Highlight indented code blocks whose language can be detected.

    pymdownx.highlight's own tree processor ("indent-highlight", priority 30) always passes an empty
    language for indented blocks, so this runs just before it and handles the blocks it can classify
    with the same Highlight class and configuration. Blocks it skips fall through unchanged.
    """

    HIGHLIGHT_OPTIONS = (
        "pygments_style",
        "use_pygments",
        "noclasses",
        "linenums",
        "linenums_style",
        "linenums_special",
        "linenums_class",
        "extend_pygments_lang",
        "language_prefix",
        "code_attr_on_pre",
        "auto_title",
        "auto_title_map",
        "pygments_lang_class",
        "stripnl",
        "default_lang",
    )

    def run(self, root):
        highlight_ext = next((ext for ext in self.md.registeredExtensions if isinstance(ext, HighlightExtension)), None)
        if highlight_ext is None:
            return
        config = highlight_ext.getConfigs()
        highlighter = Highlight(guess_lang=False, **{option: config[option] for option in self.HIGHLIGHT_OPTIONS})
        for block in root.iter("pre"):
            if len(block) != 1 or block[0].tag != "code":
                continue
            code = (block[0].text or "").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").rstrip("\n")
            language = detect_language(code)
            if language is None:
                continue
            highlight_ext.pygments_code_block += 1
            html = highlighter.highlight(
                code, language, config["css_class"], code_block_count=highlight_ext.pygments_code_block
            )
            block.clear()
            block.tag = "p"
            block.text = self.md.htmlStash.store(html)


class CodeLanguageExtension(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(CodeLanguageTreeprocessor(md), "openssl-code-language", 35)

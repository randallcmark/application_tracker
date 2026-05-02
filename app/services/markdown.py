from html import escape
import re


def _render_inline_markdown(text: str) -> str:
    escaped = escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def render_markdown_blocks(text: str, *, class_name: str = "ai-markdown") -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(f"<h4>{_render_inline_markdown(line[4:])}</h4>")
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(f"<h3>{_render_inline_markdown(line[3:])}</h3>")
            i += 1
            continue
        if line.startswith("# "):
            blocks.append(f"<h2>{_render_inline_markdown(line[2:])}</h2>")
            i += 1
            continue
        if line.startswith(("* ", "- ")):
            items: list[str] = []
            while i < len(lines):
                bullet = lines[i].strip()
                if not bullet.startswith(("* ", "- ")):
                    break
                items.append(f"<li>{_render_inline_markdown(bullet[2:])}</li>")
                i += 1
            blocks.append("<ul>" + "".join(items) + "</ul>")
            continue
        paragraph_lines: list[str] = []
        while i < len(lines):
            paragraph = lines[i].strip()
            if not paragraph or paragraph.startswith(("# ", "## ", "### ", "* ", "- ")):
                break
            paragraph_lines.append(paragraph)
            i += 1
        blocks.append(f"<p>{_render_inline_markdown(' '.join(paragraph_lines))}</p>")
    return f'<div class="{escape(class_name, quote=True)}">' + "".join(blocks) + "</div>"

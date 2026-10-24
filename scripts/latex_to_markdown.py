#!/usr/bin/env python3
"""Convert this CV's LaTeX source into terminal-friendly Markdown.

This is intentionally a small, CV-specific converter. It understands the
macros used by main.tex and fails loudly when it meets something it does not
know, rather than silently dropping content.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator

DOCUMENT_START = "\\begin{document}"
DOCUMENT_END = "\\end{document}"

TOP_LEVEL_ARITY = {
    "cvsect": 1,
    "entry": 4,
    "QRentry": 3,
    "halfentry": 3,
    "halfentrydate": 4,
    "icon": 3,
}

SECTION_ORDER = ("Projects", "Experience", "Volunteering", "Education")

PROJECT_URL_REWRITES = {
    "https://engiebenji.com/2022/09/18/CUBE/": "/projects/cube/",
    "https://engiebenji.com/2022/09/18/ORTHODOX/": "/projects/orthodox/",
}

# Layout commands that may appear in content but should not survive into the
# Markdown output.
DROP_MACROS = {
    "hspace",
    "vspace",
    "vspace*",
    "hspace*",
    "hfill",
    "vfill",
    "quad",
    "qquad",
    "smallskip",
    "medskip",
    "bigskip",
}

BREAK_COMMANDS = {"newline"}


class ConversionError(Exception):
    """Raised when the LaTeX source contains an unsupported construct."""


def line_at(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def strip_comments(text: str) -> str:
    """Remove LaTeX comments while preserving escaped percent signs."""
    out: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]

        if char == "\\" and index + 1 < len(text):
            out.append(char)
            out.append(text[index + 1])
            index += 2
            continue

        if char == "%":
            while index < len(text) and text[index] != "\n":
                index += 1
            continue

        out.append(char)
        index += 1

    return "".join(out)


def document_body(text: str) -> str:
    start = text.find(DOCUMENT_START)
    end = text.find(DOCUMENT_END)

    if start < 0 or end < 0 or end <= start:
        raise ConversionError(
            f"could not find {DOCUMENT_START!r} and {DOCUMENT_END!r}"
        )

    return text[start + len(DOCUMENT_START) : end]


def read_braced(text: str, index: int) -> tuple[str, int]:
    """Read one balanced {...} argument starting at index."""
    if index >= len(text) or text[index] != "{":
        raise ConversionError("expected a braced argument")

    depth = 0
    out: list[str] = []
    cursor = index + 1

    while cursor < len(text):
        char = text[cursor]

        if char == "\\" and cursor + 1 < len(text):
            out.append(char)
            out.append(text[cursor + 1])
            cursor += 2
            continue

        if char == "{":
            depth += 1
            out.append(char)
        elif char == "}":
            if depth == 0:
                return "".join(out), cursor + 1
            depth -= 1
            out.append(char)
        else:
            out.append(char)

        cursor += 1

    raise ConversionError("unterminated braced argument")


def read_bracketed(text: str, index: int) -> tuple[str, int]:
    if index >= len(text) or text[index] != "[":
        raise ConversionError("expected a bracketed argument")

    depth = 0
    out: list[str] = []
    cursor = index + 1

    while cursor < len(text):
        char = text[cursor]

        if char == "\\" and cursor + 1 < len(text):
            out.append(char)
            out.append(text[cursor + 1])
            cursor += 2
            continue

        if char == "[":
            depth += 1
            out.append(char)
        elif char == "]":
            if depth == 0:
                return "".join(out), cursor + 1
            depth -= 1
            out.append(char)
        else:
            out.append(char)

        cursor += 1

    raise ConversionError("unterminated bracketed argument")


def read_required_args(
    text: str, index: int, count: int
) -> tuple[list[str], int]:
    args: list[str] = []
    cursor = index

    for _ in range(count):
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1

        if cursor >= len(text):
            raise ConversionError("macro is missing an argument")

        arg, cursor = read_braced(text, cursor)
        args.append(arg)

    return args, cursor


def iter_commands(body: str) -> Iterator[tuple[str, list[str], int]]:
    """Yield top-level macros that carry CV content."""
    index = 0

    while index < len(body):
        if body[index] != "\\":
            index += 1
            continue

        match = re.match(r"\\([A-Za-z]+)", body[index:])

        if not match:
            index += 1
            continue

        name = match.group(1)
        cursor = index + match.end()

        if name not in TOP_LEVEL_ARITY:
            index = cursor
            continue

        try:
            args, cursor = read_required_args(
                body, cursor, TOP_LEVEL_ARITY[name]
            )
        except ConversionError as error:
            raise ConversionError(
                f"line {line_at(body, index)}: \\{name}: {error}"
            ) from error

        yield name, args, index
        index = cursor


def normalise_inline(text: str) -> str:
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def convert_inline(text: str) -> str:
    """Convert supported inline LaTeX into Markdown."""
    out: list[str] = []
    index = 0

    while index < len(text):
        char = text[index]

        if char == "\\":
            match = re.match(r"\\([A-Za-z]+)", text[index:])

            if not match:
                if index + 1 >= len(text):
                    index += 1
                    continue

                escaped = text[index + 1]

                if escaped == "\\":
                    out.append("\n\n")
                elif escaped in "&%#_${}":
                    out.append(escaped)
                elif escaped in " ,;:":
                    out.append(" ")
                elif escaped == "~":
                    out.append("~")
                else:
                    out.append(escaped)

                index += 2
                continue

            name = match.group(1)
            cursor = index + match.end()

            if name == "href":
                args, cursor = read_required_args(text, cursor, 2)
                label = convert_inline(args[1]).strip()
                url = args[0].strip()
                out.append(f"[{label}]({url})")
            elif name == "texttt":
                args, cursor = read_required_args(text, cursor, 1)
                out.append(f"`{args[0].strip()}`")
            elif name == "textbf":
                args, cursor = read_required_args(text, cursor, 1)
                out.append(f"**{convert_inline(args[0]).strip()}**")
            elif name == "slashsep":
                out.append(" · ")
            elif name in BREAK_COMMANDS:
                out.append("\n")
            elif name in DROP_MACROS:
                if cursor < len(text) and text[cursor] == "*":
                    cursor += 1
                if cursor < len(text) and text[cursor] == "[":
                    _, cursor = read_bracketed(text, cursor)
                if name in {"hspace", "vspace"} and cursor < len(text):
                    while cursor < len(text) and text[cursor].isspace():
                        cursor += 1
                    if cursor < len(text) and text[cursor] == "{":
                        _, cursor = read_braced(text, cursor)
                out.append(" — " if name in {"hfill", "vfill"} else "")
            else:
                raise ConversionError(
                    f"line {line_at(text, index)}: unsupported inline macro "
                    f"\\{name}"
                )

            index = cursor
            continue

        if char == "~":
            out.append(" ")
            index += 1
            continue

        out.append(char)
        index += 1

    return normalise_inline("".join(out))


def split_breaks(text: str) -> list[str]:
    return re.split(r"\\\\|\\(?:newline)\b", text)


def format_itemize(body: str) -> str:
    pattern = re.compile(
        r"\\item(?:\[[^\]]*\])?(.*?)(?=\\item|\\end\{itemize\}|\Z)",
        re.DOTALL,
    )
    items = [convert_inline(match.group(1)) for match in pattern.finditer(body)]
    items = [item for item in items if item]

    if not items:
        fallback = convert_inline(body)
        return fallback

    return "\n".join(f"- {item}" for item in items)


def format_org(org: str) -> str:
    value = convert_inline(org)
    match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", value)

    if match:
        label, url = match.groups()
        return f"[**{label}**]({url})"

    return f"**{value}**"


def en_dash_dates(value: str) -> str:
    return re.sub(r"(?<=\d)-(?=\d)", "–", value.strip())


def format_project(title: str, description: str, url: str) -> str:
    target = PROJECT_URL_REWRITES.get(url.strip(), url.strip())
    body = convert_inline(description)
    lines = [f"### {convert_inline(title)}"]

    if body:
        lines.append(body)

    lines.append(f"[Project page]({target})")

    return "\n\n".join(line for line in lines if line)


def format_entry(date: str, title: str, organisation: str, body: str) -> str:
    heading = f"### {en_dash_dates(date)} · {convert_inline(title)}"
    lines = [heading, format_org(organisation)]
    bullets = format_itemize(body)

    if bullets:
        lines.append(bullets)

    return "\n\n".join(line for line in lines if line)


def format_education_detail(details: str) -> list[str]:
    items: list[str] = []

    for raw_line in split_breaks(details):
        line = re.sub(r"\\hspace\*?\{[^{}]*\}", "", raw_line)

        if not line.strip() or not line.replace(" ", "").strip():
            continue

        if "\\hfill" in line:
            left, right = line.split("\\hfill", 1)
            left = convert_inline(left).rstrip(": ").strip()
            right = convert_inline(right).strip()
            value = f"{left} — {right}" if right else left
        else:
            value = convert_inline(line)

        if value:
            items.append(value)

    return items


def format_education(
    date: str, title: str, institution: str, details: str
) -> str:
    heading = f"### {en_dash_dates(date)} · {convert_inline(title)}"
    lines = [heading, format_org(institution)]
    items = format_education_detail(details)

    if items:
        lines.append("\n".join(f"- {item}" for item in items))

    return "\n\n".join(line for line in lines if line)


def extract_header(body: str) -> tuple[str, str]:
    name_parts = [
        part.strip()
        for part in re.findall(r"\\MakeUppercase\{([^{}]*)\}", body)
        if part.strip()
    ]
    name = " ".join(name_parts) or "Benjamin Anderson"

    role_match = re.search(r"\{\\huge\s+([^{}]+)\}", body)
    role = role_match.group(1).strip() if role_match else "Electronic Engineer"

    return convert_inline(name), convert_inline(role)


def format_contact(icons: list[tuple[str, str]]) -> str:
    parts: list[str] = []

    for icon_name, content in icons:
        if icon_name == "Phone":
            continue

        value = convert_inline(content).strip()

        if not value:
            continue

        if icon_name == "Github":
            match = re.fullmatch(r"\[[^\]]+\]\(([^)]+)\)", value)
            parts.append(f"[GitHub]({match.group(1)})" if match else value)
        else:
            parts.append(value)

    return " · ".join(parts)


def collect_sections(
    commands: list[tuple[str, list[str]]],
) -> tuple[dict[str, list[tuple[str, list[str]]]], list[tuple[str, str]]]:
    sections: dict[str, list[tuple[str, list[str]]]] = {}
    icons: list[tuple[str, str]] = []
    current: str | None = None

    for name, args in commands:
        if name == "cvsect":
            current = args[0].strip()
            sections.setdefault(current, [])
            continue

        if name == "icon":
            icon_name, _, content = args
            icons.append((icon_name.strip(), content))
            continue

        if current is not None:
            sections[current].append((name, args))

    return sections, icons


def convert_section(section: str, entries: list[tuple[str, list[str]]]) -> str:
    blocks: list[str] = [f"## {section}"]

    for name, args in entries:
        if name == "QRentry":
            title, description, url = args
            blocks.append(format_project(title, description, url))
        elif name == "entry":
            date, title, organisation, body = args
            blocks.append(format_entry(date, title, organisation, body))
        elif name == "halfentrydate":
            date, title, institution, details = args
            blocks.append(format_education(date, title, institution, details))
        elif name == "halfentry":
            # References are deliberately kept out of the public Markdown CV.
            continue
        else:
            raise ConversionError(f"unsupported section entry: \\{name}")

    return "\n\n".join(block for block in blocks if block)


def convert_document(tex: str) -> str:
    body = document_body(strip_comments(tex))
    name, role = extract_header(body)
    commands = [
        (command_name, args)
        for command_name, args, _offset in iter_commands(body)
    ]
    sections, icons = collect_sections(commands)
    unknown_sections = set(sections) - set(SECTION_ORDER) - {"References"}

    if unknown_sections:
        names = ", ".join(sorted(unknown_sections))
        raise ConversionError(f"unsupported section(s): {names}")

    blocks: list[str] = [f"# {name}", role]
    contact = format_contact(icons)

    if contact:
        blocks.append(contact)

    for section in SECTION_ORDER:
        if section in sections:
            blocks.append(convert_section(section, sections[section]))

    if "References" in sections:
        blocks.append("## References\n\nAvailable on request.")

    blocks.insert(
        0,
        "<!-- Generated from main.tex by scripts/latex_to_markdown.py. "
        "Do not edit by hand. -->",
    )

    return "\n\n".join(blocks).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert main.tex into terminal-friendly Markdown."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="main.tex",
        type=Path,
        help="LaTeX source (default: main.tex)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="cv.md",
        type=Path,
        help="Markdown output (default: cv.md)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the output file is not up to date",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the Markdown instead of writing a file",
    )
    args = parser.parse_args(argv)

    try:
        tex = args.input.read_text(encoding="utf-8")
        markdown = convert_document(tex)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.stdout:
        sys.stdout.write(markdown)
        return 0

    if args.check:
        try:
            existing = args.output.read_text(encoding="utf-8")
        except OSError:
            existing = ""

        if existing != markdown:
            print(
                f"{args.output} is out of date; run "
                f"python3 scripts/latex_to_markdown.py",
                file=sys.stderr,
            )
            return 1

        return 0

    args.output.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

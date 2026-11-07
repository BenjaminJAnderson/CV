#!/usr/bin/env python3
"""Convert this CV's LaTeX source into structured JSON for the website."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import latex_to_markdown as converter

SECTION_ORDER = converter.SECTION_ORDER
PROJECT_URL_REWRITES = converter.PROJECT_URL_REWRITES

CONTACT_LABELS = {
    "At": "email",
    "MapMarker": "location",
    "Globe": "website",
    "Twitter": "twitter",
    "Github": "github",
}

ITEM_PATTERN = re.compile(
    r"\\item(?:\[[^\]]*\])?(.*?)(?=\\item|\\end\{itemize\}|\Z)",
    re.DOTALL,
)
TEXTtt_PATTERN = re.compile(r"\\texttt\{([^{}]*)\}")


def plain_text(value: str) -> str:
    """Convert supported inline LaTeX into plain website text."""
    text = converter.convert_inline(value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    return converter.normalise_inline(text)


def parse_link(value: str) -> tuple[str, str | None]:
    """Convert inline LaTeX into a label and optional href."""
    text = converter.convert_inline(value)
    match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", text)

    if match:
        label, href = match.groups()
        return plain_text(label), href

    return plain_text(text), None


def contact_items(icons: list[tuple[str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []

    for icon_name, content in icons:
        if icon_name == "Phone":
            continue

        label = CONTACT_LABELS.get(icon_name)

        if not label:
            continue

        value, href = parse_link(content)

        if icon_name == "Github":
            value = "GitHub"

        item = {"label": label, "value": value}

        if href:
            item["href"] = href

        result.append(item)

    return result


def project_item(args: list[str]) -> dict[str, object]:
    title, description, url = args
    parts = converter.split_breaks(description)
    tags: list[str] = []

    for part in parts[1:]:
        tags.extend(plain_text(tag) for tag in TEXTtt_PATTERN.findall(part))

    return {
        "title": plain_text(title),
        "description": plain_text(parts[0]),
        "tags": tags,
        "href": PROJECT_URL_REWRITES.get(url.strip(), url.strip()),
    }


def experience_item(args: list[str]) -> dict[str, object]:
    date, title, organisation, body = args
    organisation_text, organisation_href = parse_link(organisation)
    bullets = [
        plain_text(match.group(1)) for match in ITEM_PATTERN.finditer(body)
    ]
    bullets = [bullet for bullet in bullets if bullet]
    item: dict[str, object] = {
        "date": converter.en_dash_dates(date),
        "title": plain_text(title),
        "organisation": organisation_text,
        "bullets": bullets,
    }

    if organisation_href:
        item["organisationHref"] = organisation_href

    return item


def education_item(args: list[str]) -> dict[str, object]:
    date, title, institution, details = args

    return {
        "date": converter.en_dash_dates(date),
        "title": plain_text(title),
        "institution": plain_text(institution),
        "details": converter.format_education_detail(details),
    }


def convert_document(tex: str) -> dict[str, object]:
    body = converter.document_body(converter.strip_comments(tex))
    name, role = converter.extract_header(body)
    commands = [
        (command_name, args)
        for command_name, args, _offset in converter.iter_commands(body)
    ]
    sections, icons = converter.collect_sections(commands)
    unknown_sections = set(sections) - set(SECTION_ORDER) - {"References"}

    if unknown_sections:
        names = ", ".join(sorted(unknown_sections))
        raise converter.ConversionError(f"unsupported section(s): {names}")

    projects: list[dict[str, object]] = []
    experience: list[dict[str, object]] = []
    volunteering: list[dict[str, object]] = []
    education: list[dict[str, object]] = []

    for section, entries in sections.items():
        for entry_name, args in entries:
            if section == "Projects" and entry_name == "QRentry":
                projects.append(project_item(args))
            elif section in {"Experience", "Volunteering"} and entry_name == "entry":
                target = experience if section == "Experience" else volunteering
                target.append(experience_item(args))
            elif section == "Education" and entry_name == "halfentrydate":
                education.append(education_item(args))
            elif section == "References" and entry_name == "halfentry":
                continue
            else:
                raise converter.ConversionError(
                    f"unsupported section entry: \\{entry_name} in {section}"
                )

    data: dict[str, object] = {
        "name": name,
        "role": role,
        "contact": contact_items(icons),
        "projects": projects,
        "experience": experience,
        "volunteering": volunteering,
        "education": education,
        "references": "Available on request."
        if "References" in sections
        else "",
    }

    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert main.tex into structured JSON for the website."
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
        default="cv.json",
        type=Path,
        help="JSON output (default: cv.json)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the output file is not up to date",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the JSON instead of writing a file",
    )
    args = parser.parse_args(argv)

    try:
        tex = args.input.read_text(encoding="utf-8")
        data = convert_document(tex)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except converter.ConversionError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    output = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

    if args.stdout:
        sys.stdout.write(output)
        return 0

    if args.check:
        try:
            existing = args.output.read_text(encoding="utf-8")
        except OSError:
            existing = ""

        if existing != output:
            print(
                f"{args.output} is out of date; run "
                f"python3 scripts/latex_to_json.py",
                file=sys.stderr,
            )
            return 1

        return 0

    args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

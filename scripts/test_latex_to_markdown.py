#!/usr/bin/env python3
"""Tests for the CV LaTeX to Markdown converter."""

from __future__ import annotations

import unittest
from pathlib import Path

import latex_to_markdown as converter

ROOT = Path(__file__).resolve().parent.parent


class ConverterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tex = (ROOT / "main.tex").read_text(encoding="utf-8")
        self.markdown = converter.convert_document(self.tex)

    def test_sections_and_entries_are_present(self) -> None:
        for heading in (
            "# Benjamin Anderson",
            "## Projects",
            "## Experience",
            "## Volunteering",
            "## Education",
            "## References",
        ):
            self.assertIn(heading, self.markdown)

        self.assertIn("### 2024–2026 · Support Host", self.markdown)
        self.assertIn("**Caledonian Sleeper**", self.markdown)
        self.assertIn("Managed passenger boarding", self.markdown)

    def test_project_links_are_rewritten(self) -> None:
        self.assertIn("[Project page](/projects/cube/)", self.markdown)
        self.assertIn("[Project page](/projects/orthodox/)", self.markdown)
        self.assertNotIn("/2022/09/18/CUBE/", self.markdown)
        self.assertNotIn("/2022/09/18/ORTHODOX/", self.markdown)

    def test_private_details_are_omitted(self) -> None:
        for value in (
            "jason.hanson",
            "x.chu@sheffield.ac.uk",
            "luzhang1",
            "+44",
            "07799",
        ):
            self.assertNotIn(value, self.markdown)

        self.assertIn("Available on request.", self.markdown)

    def test_education_lines_are_formatted(self) -> None:
        self.assertIn("- Electronic Engineering — 1st", self.markdown)
        self.assertIn("- Mathematics — B", self.markdown)

    def test_output_is_stable(self) -> None:
        first = converter.convert_document(self.tex)
        second = converter.convert_document(self.tex)

        self.assertEqual(first, second)

    def test_unknown_inline_macro_fails(self) -> None:
        tex = r"""
        \begin{document}
        \cvsect{Experience}
        \entry{2024}{Role}{Org}{\begin{itemize}\item \unknownmacro{x}\end{itemize}}
        \end{document}
        """

        with self.assertRaises(converter.ConversionError):
            converter.convert_document(tex)

    def test_unknown_section_fails(self) -> None:
        tex = r"""
        \begin{document}
        \cvsect{Skills}
        \entry{2024}{Role}{Org}{Body}
        \end{document}
        """

        with self.assertRaises(converter.ConversionError):
            converter.convert_document(tex)

    def test_comments_are_stripped(self) -> None:
        tex = r"""
        \begin{document}
        \cvsect{Projects}
        \QRentry{Cube}{A cube.\\\texttt{KiCad}}{/projects/cube/} % hidden
        \end{document}
        """

        markdown = converter.convert_document(tex)

        self.assertNotIn("hidden", markdown)
        self.assertIn("### Cube", markdown)
        self.assertIn("`KiCad`", markdown)


if __name__ == "__main__":
    unittest.main()

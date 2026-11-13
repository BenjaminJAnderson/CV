#!/usr/bin/env python3
"""Tests for the CV LaTeX to JSON converter."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import latex_to_json as converter

ROOT = Path(__file__).resolve().parent.parent


class JsonConverterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tex = (ROOT / "main.tex").read_text(encoding="utf-8")
        self.data = converter.convert_document(self.tex)

    def test_header_and_contact_are_present(self) -> None:
        self.assertEqual(self.data["name"], "Benjamin Anderson")
        self.assertEqual(self.data["role"], "Electronic Engineer")

        labels = [item["label"] for item in self.data["contact"]]
        self.assertIn("email", labels)
        self.assertIn("website", labels)
        self.assertIn("twitter", labels)
        self.assertIn("github", labels)
        self.assertNotIn("phone", labels)

    def test_projects_are_structured_and_rewritten(self) -> None:
        projects = self.data["projects"]
        self.assertEqual(
            [project["title"] for project in projects],
            ["Cube", "Orthodox", "Avalanche"],
        )
        self.assertEqual(projects[0]["href"], "/projects/cube/")
        self.assertEqual(projects[1]["href"], "/projects/orthodox/")
        self.assertEqual(projects[2]["href"], "/projects/avalanche/")
        self.assertIn("KiCad", projects[0]["tags"])
        self.assertIn("A handheld device", projects[0]["description"])
        self.assertIn("C++", projects[2]["tags"])

    def test_experience_and_volunteering_are_present(self) -> None:
        experience = self.data["experience"]
        volunteering = self.data["volunteering"]

        self.assertEqual(experience[0]["date"], "2024–2026")
        self.assertEqual(experience[0]["title"], "Support Host")
        self.assertEqual(experience[0]["organisation"], "Caledonian Sleeper")
        self.assertGreater(len(experience[0]["bullets"]), 1)
        self.assertEqual(volunteering[0]["title"], "Trail Maintenance & Stonework")

    def test_education_is_structured(self) -> None:
        education = self.data["education"]
        self.assertEqual(education[0]["date"], "2017–2021")
        self.assertIn("Electronic Engineering — 1st", education[0]["details"])

    def test_private_details_are_omitted(self) -> None:
        output = json.dumps(self.data)

        for value in (
            "jason.hanson",
            "x.chu@sheffield.ac.uk",
            "luzhang1",
            "+44",
            "07799",
        ):
            self.assertNotIn(value, output)

        self.assertEqual(self.data["references"], "Available on request.")

    def test_output_is_stable(self) -> None:
        first = converter.convert_document(self.tex)
        second = converter.convert_document(self.tex)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()

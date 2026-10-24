"""Unit tests for the shadcn input macro (flask_basecoat/templates/basecoat/input.html)."""
import re
import unittest

from flask import Flask, render_template_string
from bs4 import BeautifulSoup

from flask_basecoat import Basecoat

BASE = "{% from 'basecoat/input.html' import input %}"
SHADCN_CLASSES = (
    "file:text-foreground placeholder:text-muted-foreground selection:bg-primary "
    "selection:text-primary-foreground dark:bg-input/30 border-input flex h-9 w-full min-w-0 "
    "rounded-md border bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] "
    "outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm "
    "file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 "
    "md:text-sm focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] "
    "aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive"
)


class InputMacroTest(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "x"
        Basecoat(self.app)
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def render(self, call):
        html = render_template_string(BASE + "{{ " + call + " }}")
        return BeautifulSoup(html, "html.parser").find("input")

    def test_default_has_basecoat_classes_and_slot(self):
        el = self.render("input()")
        self.assertEqual(el["data-slot"], "input")
        self.assertEqual(el["type"], "text")
        self.assertEqual(el["class"], SHADCN_CLASSES.split())

    def test_types(self):
        for t in ["text", "email", "password", "number", "search", "file", "url", "tel"]:
            with self.subTest(type=t):
                el = self.render(f"input(type='{t}')")
                self.assertEqual(el["type"], t)
                self.assertIn("file:inline-flex", el["class"])
                self.assertIn("h-9", el["class"])

    def test_disabled(self):
        el = self.render("input(disabled=true)")
        self.assertTrue(el.has_attr("disabled"))
        self.assertIn("disabled:opacity-50", el["class"])

    def test_readonly_and_required(self):
        el = self.render("input(readonly=true, required=true)")
        self.assertTrue(el.has_attr("readonly"))
        self.assertTrue(el.has_attr("required"))
        self.assertEqual(el["aria-required"], "true")

    def test_invalid_sets_aria_invalid(self):
        el = self.render("input(invalid=true, describedby='err')")
        self.assertEqual(el["aria-invalid"], "true")
        self.assertEqual(el["aria-describedby"], "err")
        self.assertIn("aria-invalid:border-destructive", el["class"])

    def test_valid_has_no_aria_invalid(self):
        el = self.render("input()")
        self.assertFalse(el.has_attr("aria-invalid"))
        self.assertFalse(el.has_attr("disabled"))

    def test_attributes_and_extra_class(self):
        el = self.render("input(id='a', name='n', value='v', placeholder='p', label='L', class='extra', autocomplete='email')")
        self.assertEqual((el["id"], el["name"], el["value"], el["placeholder"], el["aria-label"]), ("a", "n", "v", "p", "L"))
        self.assertEqual(el["autocomplete"], "email")
        self.assertIn("extra", el["class"])

    def test_no_raw_colour_or_inline_style(self):
        el = self.render("input()")
        self.assertFalse(el.has_attr("style"))
        self.assertIsNone(re.search(r"(#[0-9a-fA-F]{3,6}\b|\b(?:bg|text|border)-(?:red|blue|green|gray|white|black)\b)", " ".join(el["class"])))

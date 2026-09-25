# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

from resume_generator.latex import escape_latex


def test_none_and_non_strings():
    assert escape_latex(None) == ""
    assert escape_latex(2021) == "2021"


def test_escapes_latex_specials():
    assert escape_latex("R&D") == "R\\&D"
    assert escape_latex("100%") == "100\\%"
    assert escape_latex("a_b") == "a\\_b"
    assert escape_latex("$5") == "\\$5"
    assert escape_latex("#1") == "\\#1"


def test_backslash_is_escaped_once():
    # The backslash rule must run first, or it would re-escape the backslashes
    # that the other rules introduce.
    assert escape_latex("a\\b") == "a\\textbackslash b"
    assert escape_latex("50% & rising") == "50\\% \\& rising"


def test_command_injection_is_neutralised():
    out = escape_latex("\\input{/etc/passwd}")
    assert "\\input{" not in out
    assert out.startswith("\\textbackslash input")


def test_smart_punctuation_folded_to_ascii():
    assert escape_latex("\u201cquoted\u201d") == '"quoted"'
    assert escape_latex("a \u2014 b") == "a - b"
    assert escape_latex("\u2022 item") == "- item"


def test_accents_become_tex_macros():
    assert escape_latex("Montr\u00e9al") == "Montr\\'{e}al"
    assert escape_latex("fran\u00e7ais") == "fran\\c{c}ais"

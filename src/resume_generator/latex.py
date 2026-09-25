# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Zaid Abouhal

"""LaTeX text escaping.

Lifted verbatim from the original ``render_template`` closure so it can be
tested and reused outside of Jinja.
"""

import unicodedata

_ACCENTS = {
    'é': "\\'{e}", 'è': "\\`{e}", 'ê': "\\^{e}", 'ë': '\\"{e}',
    'É': "\\'{E}", 'È': "\\`{E}", 'Ê': "\\^{E}", 'Ë': '\\"{E}',
    'à': "\\`{a}", 'â': "\\^{a}", 'ä': '\\"{a}',
    'À': "\\`{A}", 'Â': "\\^{A}", 'Ä': '\\"{A}',
    'î': "\\^{i}", 'ï': '\\"{i}',
    'Î': "\\^{I}", 'Ï': '\\"{I}',
    'ô': "\\^{o}", 'ö': '\\"{o}', 'œ': '\\oe ',
    'Ô': "\\^{O}", 'Ö': '\\"{O}', 'Œ': '\\OE ',
    'ù': "\\`{u}", 'û': "\\^{u}", 'ü': '\\"{u}',
    'Ù': "\\`{U}", 'Û': "\\^{U}", 'Ü': '\\"{U}',
    'ç': "\\c{c}", 'Ç': "\\c{C}",
}

# Order matters: the backslash substitution must run first, otherwise it would
# re-escape the backslashes introduced by the later replacements.
_SPECIALS = [
    ('\\', '\\textbackslash '),
    ('&', '\\&'),
    ('%', '\\%'),
    ('$', '\\$'),
    ('#', '\\#'),
    ('_', '\\_'),
    ('{', '\\{'),
    ('}', '\\}'),
    ('~', '\\textasciitilde '),
    ('^', '\\textasciicircum '),
]

_PUNCTUATION = [
    ('­', ''),   # soft hyphen
    ('﻿', ''),   # BOM
    ('“', '"'), ('”', '"'),
    ('‘', "'"), ('’', "'"),
    ('–', '-'), ('—', '-'),
    ('•', '-'),
]


def escape_latex(text) -> str:
    """Escape arbitrary text for safe inclusion in a LaTeX document."""
    if text is None:
        return ''
    if not isinstance(text, str):
        text = str(text)

    text = unicodedata.normalize('NFKC', text)
    for old, new in _PUNCTUATION:
        text = text.replace(old, new)
    for old, new in _SPECIALS:
        text = text.replace(old, new)
    for old, new in _ACCENTS.items():
        text = text.replace(old, new)
    return text

# SPDX-License-Identifier: GPL-3.0-or-later
"""Barlow SemiBold outlines: an SVG shown as an image loads no fonts."""

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from tracks import num

FILE = (
    Path(__file__).resolve().parents[2]
    / "site"
    / "public"
    / "fonts"
    / "barlow-latin-600-normal.woff2"
)


class Font:
    """Barlow SemiBold glyph outlines, each defined once and placed by <use>."""

    def __init__(self, path):
        font = TTFont(path)
        self.upm = font["head"].unitsPerEm
        self.cmap = font.getBestCmap()
        self.glyphs = font.getGlyphSet()
        self.used = {}

    def advance(self, char):
        return self.glyphs[self.cmap[ord(char)]].width

    def width(self, text, size, tracking):
        units = sum(self.advance(c) for c in text) + tracking * self.upm * (
            len(text) - 1
        )
        return units * size / self.upm

    def label(self, text, size, tracking, x, y, centred=True):
        """Return the label's glyphs with the baseline at y."""
        if centred:
            x -= self.width(text, size, tracking) / 2
        s = size / self.upm
        uses, at = [], 0.0
        for char in text:
            name = self.cmap[ord(char)]
            if char != " ":
                if name not in self.used:
                    pen = SVGPathPen(self.glyphs, ntos=lambda v: str(round(v)))
                    self.glyphs[name].draw(pen)
                    self.used[name] = pen.getCommands()
                uses.append(f'<use href="#g{gid(name)}" x="{num(at)}"/>')
            at += self.advance(char) + tracking * self.upm
        matrix = f"matrix({num(s, 5)} 0 0 {num(-s, 5)} {num(x)} {num(y)})"
        return f'<g transform="{matrix}">{"".join(uses)}</g>'

    def defs(self):
        return "".join(
            f'<path id="g{gid(n)}" d="{d}"/>' for n, d in sorted(self.used.items())
        )


def gid(name):
    return "".join(c for c in name if c.isalnum())


FONT = Font(FILE)

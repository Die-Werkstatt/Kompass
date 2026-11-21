# SPDX-License-Identifier: GPL-3.0-or-later
"""Animated values sampled every frame, written as SMIL animations."""

FPS = 60
LOOP = 11.2
# The frame a viewer sees where SMIL does not run.
POSTER = 2.8


def num(v, places=2):
    text = f"{v:.{places}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


class Track:
    """One animated value, sampled every frame."""

    def __init__(self, tolerance):
        self.tolerance = tolerance
        self.values = []

    def keep(self):
        """Return the frames that linear interpolation cannot skip."""
        vals = [v if isinstance(v, tuple) else (v,) for v in self.values]
        n = len(vals)
        kept, a = [0], 0
        while a < n - 1:
            b = a + 1
            while b + 1 < n and self._fits(vals, a, b + 1):
                b += 1
            kept.append(b)
            a = b
        return kept

    def _fits(self, vals, a, c):
        for i in range(a + 1, c):
            t = (i - a) / (c - a)
            for va, vc, vi in zip(vals[a], vals[c], vals[i]):
                if abs(va + (vc - va) * t - vi) > self.tolerance:
                    return False
        return True


TRACKS = {}
POSITION, ANGLE, SHARE, COLOUR = 0.25, 0.3, 0.01, 2.0


def put(name, value, tolerance):
    TRACKS.setdefault(name, Track(tolerance)).values.append(value)


def show(value):
    if isinstance(value, tuple) and len(value) == 3:
        return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in value)
    if isinstance(value, tuple):
        return " ".join(num(v) for v in value)
    return num(value, 3)


def poster(name):
    track = TRACKS[name]
    return track.values[round(POSTER * FPS)]


def animate(name, attribute):
    """Return the attribute at its poster value, plus its <animate> if it changes."""
    track = TRACKS[name]
    if all(v == track.values[0] for v in track.values):
        return f'{attribute}="{show(track.values[0])}"', ""
    kept = track.keep()
    last = len(track.values) - 1
    values = ";".join(show(track.values[i]) for i in kept)
    times = ";".join(num(i / last, 4) for i in kept)
    tag = (
        f'<animate attributeName="{attribute}" dur="{num(LOOP)}s" repeatCount="indefinite" '
        f'values="{values}" keyTimes="{times}"/>'
    )
    return f'{attribute}="{show(poster(name))}"', tag


def transformed(name, kind):
    """Return a <g> opening tag transformed by the track, with its animation."""
    track = TRACKS[name]
    if all(v == track.values[0] for v in track.values):
        return f'<g transform="{kind}({show(track.values[0])})">'
    kept = track.keep()
    last = len(track.values) - 1
    values = ";".join(show(track.values[i]) for i in kept)
    times = ";".join(num(i / last, 4) for i in kept)
    return (
        f'<g transform="{kind}({show(poster(name))})">'
        f'<animateTransform attributeName="transform" type="{kind}" dur="{num(LOOP)}s" '
        f'repeatCount="indefinite" values="{values}" keyTimes="{times}"/>'
    )


def element(tag, static, animated, body=""):
    """Return an element with static attributes and animated ones by track."""
    parts, anims = [], []
    for attribute, name in animated.items():
        attr, anim = animate(name, attribute)
        parts.append(attr)
        anims.append(anim)
    attrs = " ".join(
        [*(f'{k.replace("_", "-")}="{v}"' for k, v in static.items()), *parts]
    )
    inner = "".join(anims) + body
    return f"<{tag} {attrs}>{inner}</{tag}>" if inner else f"<{tag} {attrs}/>"

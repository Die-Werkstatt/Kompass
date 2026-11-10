# Kompass brand

The mark, wordmark and colours for Kompass.
The full sheet with variations is the [Kompass logo artifact](https://claude.ai/artifact/RSmE8hJSN9eG1htojcKN13).
This file is the source of truth for the numbers.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="kompass-lockup-light.svg">
  <img src="kompass-lockup-dark.svg" width="360" alt="Kompass">
</picture>

## Idea

A compass dial: a ring, eight bearing ticks for the eight pie slots, and a split needle.
North is in signal red.

## Files

| File | Use |
|---|---|
| `kompass-mark-dark.svg` | Mark on dark backgrounds |
| `kompass-mark-light.svg` | Mark on light backgrounds |
| `kompass-mark-mono.svg` | One colour, follows the surrounding text colour (`currentColor`) |
| `kompass-lockup-{dark,light}.svg` | Mark and wordmark side by side |
| `kompass-lockup-stacked-{dark,light}.svg` | Mark over wordmark |
| `kompass-wordmark-{dark,light}.svg` | "KOMPASS" on its own |
| `kompass-app-icon.svg` | Mark on a dark rounded tile |
| `kompass-favicon-16.svg` | 16 px only: ring and needle, heavier stroke |

The wordmark files are outlines, not live text.
Always use these files; never type the wordmark.

## Mark

Drawn on a 64-unit grid.

| Part | Value |
|---|---|
| Stroke | 3.25 units, flat ends |
| Ring | centre 32/32, radius 26 |
| Ticks | 8, every 45°, from radius 17 into the ring; the ring is drawn over them |
| North tick | signal red |
| Needle | tips at radius 12, half-width 4.5, gap of 4 between the halves; north half red, south half ink |
| Ink box | 4 to 60 (56 × 56); the SVGs are cropped to it |

Below 24 px use `kompass-favicon-16.svg`.

## Wordmark

"KOMPASS" in **Barlow SemiBold (600)**, capitals, tracking 140/1000 em.
Barlow is in the DIN signage line that the house style takes from the Ulm school; it is free under the SIL Open Font License.

## Lockups

- **Horizontal:** cap height is ⅔ of the mark; gap between mark and word is half the mark.
- **Stacked:** cap height is ⅓ of the mark, word centred under it; gap is half the mark.

## Colour

| Name | Hex | Use |
|---|---|---|
| Ground | `#0E0E0E` | Background |
| Surface | `#171717` | Panels |
| Stone | `#8F8D88` | Secondary text |
| Ink | `#F1F0EC` | Text, ring, ticks, south needle |
| Signal | `#F2542D` | North tick, north needle, selected pie slot |
| Signal on light | `#D9431F` | Signal on light backgrounds |

## Don't

- Rotate or mirror the mark.
- Recolour the north tick or north needle.
- Add glows, shadows or gradients.

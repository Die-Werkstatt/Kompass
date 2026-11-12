import math

import pytest

from kompass.core import layout
from kompass.core.model import SLOT_DIRECTIONS

W, E, S, N, NW, NE, SW, SE = range(8)


def test_bearings_follow_the_slot_order():
    assert dict(zip(SLOT_DIRECTIONS, layout.BEARINGS)) == {
        "W": 270, "E": 90, "S": 180, "N": 0, "NW": 309, "NE": 51, "SW": 231, "SE": 129
    }  # fmt: skip


def test_slots_mirror_left_to_right():
    for left, right in ((W, E), (NW, NE), (SW, SE)):
        lx, ly = layout.slot_corner(left, 8)
        rx, ry = layout.slot_corner(right, 8)
        assert lx + layout.SLOT_WIDTH == pytest.approx(-rx)
        assert ly == pytest.approx(ry)


def test_north_and_south_slots_are_centred():
    for slot in (N, S):
        assert layout.slot_corner(slot, 8)[0] == pytest.approx(-layout.SLOT_WIDTH / 2)
    assert layout.slot_corner(N, 8)[1] == pytest.approx(layout.PIE_RADIUS)
    top_of_south = layout.slot_corner(S, 8)[1] + layout.MIDDLE_HEIGHT
    assert top_of_south == pytest.approx(-layout.PIE_RADIUS)


def test_slots_do_not_overlap():
    corners = [layout.slot_corner(slot, 8) for slot in range(8)]
    for a, (ax, ay) in enumerate(corners):
        for bx, by in corners[a + 1 :]:
            apart_x = abs(ax - bx) >= layout.SLOT_WIDTH
            apart_y = abs(ay - by) >= layout.MIDDLE_HEIGHT
            assert apart_x or apart_y


def _gaps(count, height):
    """Return the shortest way from each box to the next one around the pie."""
    order = sorted(range(count), key=lambda slot: layout.bearings(count)[slot])
    corners = [layout.slot_corner(slot, count) for slot in order]
    gaps = []
    for slot, (ax, ay) in enumerate(corners):
        bx, by = corners[(slot + 1) % count]
        gap_x = abs(ax - bx) - layout.SLOT_WIDTH
        gap_y = abs(ay - by) - height
        gaps.append(math.hypot(max(gap_x, 0), max(gap_y, 0)))
    return gaps


def test_eight_slots_keep_equal_gaps():
    assert _gaps(8, layout.MIDDLE_HEIGHT) == pytest.approx([44] * 8, abs=1.2)


def test_slots_are_taller_in_a_smaller_pie():
    assert [layout.slot_height(count) for count in (4, 8, 12)] == [96, 72, 48]
    # A slot of a pie of 4 is a square whatever its label.
    assert layout.slot_width(40, 4) == layout.slot_width(400, 4) == layout.SQUARE


def test_bearing_runs_clockwise_from_north():
    assert layout.bearing_to(0, 1) == pytest.approx(0)
    assert layout.bearing_to(1, 0) == pytest.approx(90)
    assert layout.bearing_to(0, -1) == pytest.approx(180)
    assert layout.bearing_to(-1, 0) == pytest.approx(270)


def test_no_slot_is_selected_inside_the_ring():
    assert layout.slot_at(0, layout.RING_RADIUS, 8) is None
    assert layout.slot_at(0, layout.RING_RADIUS + 1, 8) == N


def test_the_nearest_slot_is_selected_outside_the_ring():
    assert layout.slot_at(100, 0, 8) == E
    assert layout.slot_at(-100, 0, 8) == W
    assert layout.slot_at(100, 90, 8) == NE
    assert layout.slot_at(-80, -100, 8) == SW
    # North is nearest on both sides of bearing 0.
    assert layout.slot_at(-5, 100, 8) == N


def test_ticks_every_five_degrees_with_eight_long_ones():
    ticks = layout.ticks()
    assert len(ticks) == 72
    assert [bearing for bearing, _, _, major in ticks if major] == list(
        range(0, 360, 45)
    )
    assert all(outer == layout.DIAL_RADIUS for _, _, outer, _ in ticks)


def test_fit_shrinks_the_pie_to_the_smaller_side():
    assert layout.fit(2000, 2000, 8) == 1
    assert layout.fit(342, 2000, 8) == pytest.approx(0.5)
    assert layout.fit(2000, 117, 8) == pytest.approx(0.25)


def test_slots_open_from_closer_to_the_centre():
    for slot in range(8):
        near, far = (
            layout.slot_corner(slot, 8, pull=layout.OPEN_PULL),
            layout.slot_corner(slot, 8),
        )
        x, y = layout.point(1, layout.BEARINGS[slot])
        # The slot has moved outwards along its bearing.
        moved = (far[0] - near[0]) * x + (far[1] - near[1]) * y
        assert moved == pytest.approx(layout.PIE_RADIUS * (1 - layout.OPEN_PULL))


def test_slot_under_is_the_box_not_the_bearing():
    widths = [layout.SLOT_WIDTH] * 8
    left, bottom = layout.slot_corner(E, 8)
    assert layout.slot_under(left + 1, bottom + 1, widths) == E
    assert layout.slot_under(left - 1, bottom + 1, widths) is None
    # Selected by bearing, but past the end of the box.
    assert layout.slot_at(left + layout.SLOT_WIDTH + 5, 0, 8) == E
    assert layout.slot_under(left + layout.SLOT_WIDTH + 5, 0, widths) is None
    # A wider slot reaches further.
    widths[E] = layout.SLOT_MAX_WIDTH
    assert layout.slot_under(left + layout.SLOT_WIDTH + 5, 0, widths) == E


def test_click_near_a_slot_counts_for_it():
    widths = [layout.SLOT_WIDTH] * 8
    left, bottom = layout.slot_corner(NE, 8)
    assert layout.slot_picked(left + 5, bottom + 5, widths) == NE
    # Left of the box the line from the centre misses it.
    assert layout.enters(left - 10, bottom + 60, NE, widths) is None
    assert layout.slot_picked(left - 10, bottom + 60, widths) == NE


def test_click_beyond_a_slot_picks_what_the_line_crosses():
    widths = [layout.SLOT_WIDTH] * 8
    left = layout.slot_corner(E, 8)[0]
    assert layout.slot_picked(left + layout.SLOT_WIDTH + 100, 0, widths) == E
    # The line enters the box where the box begins.
    assert layout.enters(2 * left, 0, E, widths) == pytest.approx(0.5)
    assert layout.enters(left - 1, 0, E, widths) is None
    # Between two slots it crosses neither.
    x, y = layout.point(300, 75)
    assert layout.slot_picked(x, y, widths) is None
    # Of two slots it crosses, the one it enters first counts.
    twelve = [layout.SLOT_WIDTH] * 12
    x, y = layout.point(250, 59)
    assert layout.slot_under(x, y, twelve) is None
    assert layout.enters(x, y, 2, twelve) < layout.enters(x, y, 1, twelve)
    assert layout.slot_picked(x, y, twelve) == 2


def test_the_line_lets_go_beyond_its_reach():
    widths = [layout.SLOT_WIDTH] * 8
    assert layout.slot_picked(layout.LINE_REACH, 0, widths) == E
    assert layout.slot_picked(layout.LINE_REACH + 1, 0, widths) is None
    # It leaves the pointer at a steady speed and slows into the dial.
    assert layout.pulled(0) == 0 and layout.pulled(1) == 1
    assert layout.pulled(0.2) == pytest.approx(2 * layout.pulled(0.1))
    assert layout.pulled(0.9) - layout.pulled(0.8) < layout.pulled(0.1)


def test_slot_width_follows_the_label():
    assert layout.slot_width(40) == layout.SLOT_WIDTH
    assert layout.slot_width(110.2) == 111 + 2 * layout.LABEL_PAD
    assert layout.slot_width(400) == layout.SLOT_MAX_WIDTH


def test_wider_slots_grow_away_from_the_centre():
    wide = layout.SLOT_MAX_WIDTH
    # East keeps its left side on the ring, west its right, north its middle.
    assert layout.slot_corner(E, 8, wide)[0] == pytest.approx(layout.PIE_RADIUS)
    assert layout.slot_corner(W, 8, wide)[0] + wide == pytest.approx(-layout.PIE_RADIUS)
    assert layout.slot_corner(N, 8, wide)[0] == pytest.approx(-wide / 2)
    # A slot between them keeps the corner that faces the centre in place.
    narrow = layout.slot_corner(NE, 8)
    assert (
        layout.slot_corner(NE, 8, wide)[0] > narrow[0] - (wide - layout.SLOT_WIDTH) / 2
    )
    assert layout.slot_corner(NE, 8, wide)[1] == narrow[1]


def test_long_label_slides_after_a_wait():
    assert layout.slide(0, 30, 0.2, 0.1) == 0
    assert layout.slide(0, 30, 0.5, 0.1) == pytest.approx(4)
    assert layout.slide(28, 30, 2, 0.1) == 30


def test_long_label_eases_back():
    back = layout.slide(30, 30, None, 0.06)
    assert back == pytest.approx(30 / math.e)
    assert layout.slide(0.2, 30, None, 0.01) == 0


def test_fill_grows_away_from_the_centre():
    assert layout.filled(N, 8, 0.25) == (0, 0, 1, 0.25)
    assert layout.filled(S, 8, 0.25) == (0, 0.75, 1, 1)
    for slot in (E, NE, SE):
        assert layout.filled(slot, 8, 0.25) == (0, 0, 0.25, 1)
    for slot in (W, NW, SW):
        assert layout.filled(slot, 8, 0.25) == (0.75, 0, 1, 1)


def test_hover_shortens_the_major_ticks():
    for hover, length in ((0, layout.MAJOR_TICK), (1, layout.TICK)):
        lengths = {
            outer - inner for _, inner, outer, major in layout.ticks(50, hover) if major
        }
        assert lengths == {length}
    minor = {
        outer - inner for _, inner, outer, major in layout.ticks(50, 1) if not major
    }
    assert minor == {layout.TICK}


def test_easing_starts_and_ends_at_rest():
    for ease in (layout.ease_out, layout.ease_in_out):
        assert ease(0) == 0 and ease(1) == 1
        assert [ease(n / 10) for n in range(11)] == sorted(
            ease(n / 10) for n in range(11)
        )
    assert layout.ease_in_out(0.5) == pytest.approx(0.5)
    assert layout.ease_out(0.5) == pytest.approx(0.875)


def test_toward_stops_at_the_target():
    assert layout.toward(0.2, 1, 0.5) == pytest.approx(0.7)
    assert layout.toward(0.8, 1, 0.5) == 1
    assert layout.toward(0.8, 0, 0.5) == pytest.approx(0.3)
    assert layout.toward(0.3, 0, 0.5) == 0


def test_twelve_slots_run_clockwise_from_north():
    assert layout.bearings(12) == layout.WIDE_BEARINGS
    assert list(layout.WIDE_BEARINGS) == sorted(layout.WIDE_BEARINGS)
    assert layout.slot_at(0, 100, 12) == 0
    assert layout.slot_at(100, 0, 12) == 3
    # 30 degrees is nearer to 42 than to north; in a pie of 8 it is north-east.
    x, y = layout.point(100, 30)
    assert layout.slot_at(x, y, 12) == 1
    assert layout.slot_at(x, y, 8) == NE


def test_twelve_slots_mirror_left_to_right():
    for slot in range(1, 6):
        rx, ry = layout.slot_corner(slot, 12)
        lx, ly = layout.slot_corner(12 - slot, 12)
        assert lx + layout.SLOT_WIDTH == pytest.approx(-rx)
        assert ly == pytest.approx(ry)


def test_twelve_slots_keep_two_gaps():
    # Wider beside north and south than between the slots stacked near east
    # and west.
    gaps = _gaps(12, layout.WIDE_HEIGHT)
    assert gaps == pytest.approx([34, 24, 24, 24, 24, 34] * 2, abs=1)


def test_twelve_slots_do_not_overlap_at_any_width():
    wide = layout.SLOT_MAX_WIDTH
    for widths in ([wide] * 12, [wide, layout.SLOT_WIDTH] * 6):
        boxes = [
            (*layout.slot_corner(slot, 12, width), width)
            for slot, width in enumerate(widths)
        ]
        for i, (ax, ay, aw) in enumerate(boxes):
            for bx, by, bw in boxes[i + 1 :]:
                apart_x = bx >= ax + aw or ax >= bx + bw
                assert apart_x or abs(ay - by) >= layout.WIDE_HEIGHT


def test_fill_follows_the_stronger_axis():
    # 42 degrees fills upward, 68 degrees sideways.
    assert layout.filled(1, 12, 0.25) == (0, 0, 1, 0.25)
    assert layout.filled(2, 12, 0.25) == (0, 0, 0.25, 1)
    assert layout.filled(7, 12, 0.25) == (0, 0.75, 1, 1)
    assert layout.filled(10, 12, 0.25) == (0.75, 0, 1, 1)


def test_highlighted_tick_is_the_nearest():
    assert layout.tick_at(42) == 40
    assert layout.tick_at(68) == 70
    assert layout.tick_at(358) == 0
    assert layout.tick_at(45) == 45


def test_a_pie_of_twelve_needs_more_room():
    assert layout.fit(700, 2000, 12) < layout.fit(700, 2000, 8) == 1


def test_keep_in_moves_a_pie_off_the_edge():
    # A pie of 8 needs 342 units to each side and 234 up and down.
    assert layout.keep_in(500, 400, (1000, 800), 8) == (500, 400)
    assert layout.keep_in(10, 790, (1000, 800), 8) == (342, 566)
    assert layout.keep_in(10, 10, (600, 800), 8) == (300, 234)

import math

import pytest

from kompass.core import layout
from kompass.core.model import SLOT_DIRECTIONS

W, E, S, N, NW, NE, SW, SE = range(8)


def test_bearings_follow_the_slot_order():
    assert dict(zip(SLOT_DIRECTIONS, layout.BEARINGS)) == {
        "W": 270, "E": 90, "S": 180, "N": 0, "NW": 315, "NE": 45, "SW": 225, "SE": 135
    }  # fmt: skip


def test_slots_mirror_left_to_right():
    for left, right in ((W, E), (NW, NE), (SW, SE)):
        lx, ly = layout.slot_corner(left)
        rx, ry = layout.slot_corner(right)
        assert lx + layout.SLOT_WIDTH == pytest.approx(-rx)
        assert ly == pytest.approx(ry)


def test_north_and_south_slots_are_centred():
    for slot in (N, S):
        assert layout.slot_corner(slot)[0] == pytest.approx(-layout.SLOT_WIDTH / 2)
    assert layout.slot_corner(N)[1] == pytest.approx(layout.PIE_RADIUS)
    top_of_south = layout.slot_corner(S)[1] + layout.SLOT_HEIGHT
    assert top_of_south == pytest.approx(-layout.PIE_RADIUS)


def test_slots_do_not_overlap():
    corners = [layout.slot_corner(slot) for slot in range(8)]
    for a, (ax, ay) in enumerate(corners):
        for bx, by in corners[a + 1 :]:
            apart_x = abs(ax - bx) >= layout.SLOT_WIDTH
            apart_y = abs(ay - by) >= layout.SLOT_HEIGHT
            assert apart_x or apart_y


def test_bearing_runs_clockwise_from_north():
    assert layout.bearing_to(0, 1) == pytest.approx(0)
    assert layout.bearing_to(1, 0) == pytest.approx(90)
    assert layout.bearing_to(0, -1) == pytest.approx(180)
    assert layout.bearing_to(-1, 0) == pytest.approx(270)


def test_no_slot_is_selected_inside_the_ring():
    assert layout.slot_at(0, layout.RING_RADIUS) is None
    assert layout.slot_at(0, layout.RING_RADIUS + 1) == N


def test_the_nearest_slot_is_selected_outside_the_ring():
    assert layout.slot_at(100, 0) == E
    assert layout.slot_at(-100, 0) == W
    assert layout.slot_at(100, 90) == NE
    assert layout.slot_at(-80, -100) == SW
    # North is nearest on both sides of bearing 0.
    assert layout.slot_at(-5, 100) == N


def test_highlight_follows_distance_and_bearing():
    assert layout.highlight(0, 10, N) == 0
    far = layout.highlight(0, 200, N)
    assert far == pytest.approx(1)
    assert layout.highlight(0, 70, N) < far
    # The selected slot keeps 0.3 just past the ring and near its edge.
    assert layout.highlight(0, 56, N) == pytest.approx(0.3)
    assert layout.highlight(75, 190, N) == pytest.approx(0.3)
    # A neighbour is lit less, and a slot across the pie not at all.
    assert 0 < layout.highlight(75, 190, NE) < 0.3
    assert layout.highlight(0, 200, S) == 0


def test_ticks_every_five_degrees_with_eight_long_ones():
    ticks = layout.ticks()
    assert len(ticks) == 72
    assert [bearing for bearing, _, _, major in ticks if major] == list(
        range(0, 360, 45)
    )
    assert all(outer == layout.DIAL_RADIUS for _, _, outer, _ in ticks)


def test_fit_shrinks_the_pie_to_the_smaller_side():
    assert layout.fit(2000, 2000) == 1
    assert layout.fit(342, 2000) == pytest.approx(0.5)
    assert layout.fit(2000, 105) == pytest.approx(0.25)


def test_slots_open_from_closer_to_the_centre():
    for slot in range(8):
        near, far = (
            layout.slot_corner(slot, pull=layout.OPEN_PULL),
            layout.slot_corner(slot),
        )
        x, y = layout.point(1, layout.BEARINGS[slot])
        # The slot has moved outwards along its bearing.
        moved = (far[0] - near[0]) * x + (far[1] - near[1]) * y
        assert moved == pytest.approx(layout.PIE_RADIUS * (1 - layout.OPEN_PULL))


def test_slot_under_is_the_box_not_the_bearing():
    widths = [layout.SLOT_WIDTH] * 8
    left, bottom = layout.slot_corner(E)
    assert layout.slot_under(left + 1, bottom + 1, widths) == E
    assert layout.slot_under(left - 1, bottom + 1, widths) is None
    # Selected by bearing, but past the end of the box.
    assert layout.slot_at(left + layout.SLOT_WIDTH + 5, 0) == E
    assert layout.slot_under(left + layout.SLOT_WIDTH + 5, 0, widths) is None
    # A wider slot reaches further.
    widths[E] = layout.SLOT_MAX_WIDTH
    assert layout.slot_under(left + layout.SLOT_WIDTH + 5, 0, widths) == E


def test_slot_width_follows_the_label():
    assert layout.slot_width(40) == layout.SLOT_WIDTH
    assert layout.slot_width(110.2) == 111 + 2 * layout.LABEL_PAD
    assert layout.slot_width(400) == layout.SLOT_MAX_WIDTH


def test_wider_slots_grow_away_from_the_centre():
    wide = layout.SLOT_MAX_WIDTH
    # East keeps its left side, west its right, the others their middle.
    assert layout.slot_corner(E, wide) == layout.slot_corner(E)
    assert layout.slot_corner(W, wide)[0] + wide == pytest.approx(
        layout.slot_corner(W)[0] + layout.SLOT_WIDTH
    )
    for slot in (N, S, NE, SW):
        middle = layout.slot_corner(slot)[0] + layout.SLOT_WIDTH / 2
        assert layout.slot_corner(slot, wide)[0] + wide / 2 == pytest.approx(middle)


def test_long_label_slides_after_a_wait():
    assert layout.slide(0, 30, 0.2, 0.1) == 0
    assert layout.slide(0, 30, 0.5, 0.1) == pytest.approx(4)
    assert layout.slide(28, 30, 2, 0.1) == 30


def test_long_label_eases_back():
    back = layout.slide(30, 30, None, 0.06)
    assert back == pytest.approx(30 / math.e)
    assert layout.slide(0.2, 30, None, 0.01) == 0


def test_fill_grows_away_from_the_centre():
    assert layout.filled(N, 0.25) == (0, 0, 1, 0.25)
    assert layout.filled(S, 0.25) == (0, 0.75, 1, 1)
    for slot in (E, NE, SE):
        assert layout.filled(slot, 0.25) == (0, 0, 0.25, 1)
    for slot in (W, NW, SW):
        assert layout.filled(slot, 0.25) == (0.75, 0, 1, 1)


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

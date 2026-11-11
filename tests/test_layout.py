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
    assert layout.fit(282, 2000) == pytest.approx(0.5)
    assert layout.fit(2000, 105) == pytest.approx(0.25)

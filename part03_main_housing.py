# /// script
# dependencies = []
# ///
"""Vertical grinding-chamber housing. Bores are smooth cylinders, not helical threads."""

import math
from pathlib import Path

import build123d as bd
from cad import model

OD = 90.0
Z_MIN = -115.0
Z_MAX = 27.0
WALL_R = 41.0
POD_R = 24.0
CAVITY_R = 22.0
BEARING_R = 14.0
BOSS_FACE_X = 60.0
SHAFT_R = 12.0
SHAFT_Z = -68.0
RIB_DROP = 2.5 * math.tan(math.radians(55.0))


def cut(base, tool, parallel=True):
    del parallel
    if isinstance(tool, (list, tuple)):
        return base.cut(*tool)
    return base.cut(tool)


def fuse(base, tool, parallel=True):
    del parallel
    if isinstance(tool, (list, tuple)):
        return base.fuse(*tool)
    return base.fuse(tool)


def _shell():
    # Exterior shadow gap is centered on the specified station.
    return bd.Plane.XZ * bd.Polygon(
        (44.2, Z_MIN),
        (45.0, Z_MIN + 0.8),
        (45.0, 1.8),
        (44.6, 1.8),
        (44.6, 2.2),
        (45.0, 2.2),
        (45.0, Z_MAX - 0.8),
        (44.2, Z_MAX),
        (36.95, Z_MAX),
        (36.15, Z_MAX - 0.8),
        (36.15, 2.0),
        (WALL_R, 2.0),
        (WALL_R, -109.9),
        (WALL_R + 1.5, -109.9),
        (WALL_R + 1.5, -112.1),
        (WALL_R, -112.1),
        (WALL_R, Z_MIN + 0.5),
        (WALL_R + 0.5, Z_MIN),
    )


def _pod():
    return bd.Plane.XZ * bd.Polygon(
        (0.0, -88.0),
        (POD_R, -88.0),
        (POD_R, -48.0),
        (BEARING_R + 0.5, -48.0),
        (BEARING_R, -48.5),
        (BEARING_R, -49.0),
        (BEARING_R + 1.5, -49.0),
        (BEARING_R + 1.5, -51.0),
        (BEARING_R, -51.0),
        (BEARING_R, -52.0),
        (CAVITY_R, -52.0),
        (CAVITY_R, -82.0),
        (0.0, -82.0),
    )


def _rib(angle):
    face = bd.Plane.YZ * bd.Polygon(
        (-2.5, -88.0 + RIB_DROP),
        (0.0, -88.0),
        (2.5, -88.0 + RIB_DROP),
        (2.5, -48.0 - RIB_DROP),
        (0.0, -48.0),
        (-2.5, -48.0 - RIB_DROP),
    )
    rib = bd.Pos(23.5, 0.0, 0.0) * bd.extrude(face, 18.0)
    return bd.Rot(0, 0, angle) * rib


def _shaft_sleeve():
    # One of the three supports. Runs through the pod wall and the housing wall
    # so the shaft bore is the only opening.
    return bd.Pos(16.0, 0, SHAFT_Z) * bd.Rot(0, 90, 0) * bd.Cylinder(
        15.0, 32.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )


def _boss():
    face = bd.Pos(0, 0, SHAFT_Z) * (
        bd.Plane.XZ
        * bd.Polygon((42.0, 0.0), (42.0, 38.0), (59.5, 38.0), (60.0, 37.5), (60.0, 0.0))
    )
    return bd.revolve(face, axis=bd.Axis((0, 0, SHAFT_Z), (1, 0, 0)))


def _lugs():
    lug = bd.Pos(55, 0, 36.5) * bd.Box(
        6, 8, 6, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
    return [bd.Pos(0, 0, SHAFT_Z) * bd.Rot(angle, 0, 0) * lug for angle in (0, 120, 240)]


def _features():
    tunnel = bd.Pos(0, 0, SHAFT_Z) * bd.Rot(0, 90, 0) * bd.Cylinder(
        SHAFT_R, 61.5, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
    ring = bd.Cylinder(21.1, 1.7, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).cut(
        bd.Pos(0, 0, -0.2) * bd.Cylinder(18.9, 2.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    )
    face_groove = bd.Pos(58.4, 0, SHAFT_Z) * bd.Rot(0, 90, 0) * ring
    detent = bd.Pos(-40.5, 0, Z_MAX - 5.0) * bd.Cylinder(
        1.5, 5.4, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
    return [tunnel, face_groove, detent]


def _edge_break(solid):
    try:
        picked = []
        for edge in solid.edges():
            center = edge.center()
            if 51.0 < center.X < 59.0 and math.hypot(center.Y, center.Z - SHAFT_Z) > 41.0:
                picked.append(edge)
        if picked:
            solid = solid.chamfer(0.5, picked)
    except Exception:
        pass
    return solid


def _assert_housing(solid):
    box = solid.bounding_box()
    assert abs(box.min.Z - Z_MIN) < 0.05, box.min
    assert abs(box.max.Z - Z_MAX) < 0.05, box.max
    assert abs(box.min.X + OD / 2) < 0.08, box.min
    assert abs(box.max.X - BOSS_FACE_X) < 0.08, box.max
    assert abs(box.max.Y - OD / 2) < 0.15, box.max
    assert len(solid.solids()) == 1
    assert not solid.is_inside((0.0, 0.0, 10.0))
    assert solid.is_inside((40.0, 0.0, 10.0))
    assert not solid.is_inside((36.0, 0.0, -10.0))
    assert solid.is_inside((43.0, 0.0, -10.0))
    assert not solid.is_inside((0.0, 0.0, -66.0))
    assert solid.is_inside((0.0, 23.2, -66.0))
    assert solid.is_inside((0.0, 0.0, -86.0))
    assert not solid.is_inside((0.0, 0.0, -50.0))
    assert not solid.is_inside((15.2, 0.0, -50.0))
    assert solid.is_inside((18.0, 0.0, -50.0))
    assert not solid.is_inside((32.0, 0.0, -68.0))
    assert solid.is_inside((32.0, 0.0, -55.0))
    assert solid.is_inside((21.0, 14.0, -68.0))
    assert not solid.is_inside((30.0, 0.0, -20.0))
    assert not solid.is_inside((0.0, 32.0, -60.0))
    assert solid.is_inside((-16.0, 27.7, -66.0))
    assert not solid.is_inside((50.0, 0.0, -68.0))
    assert not solid.is_inside((5.0, 0.0, -68.0))
    assert not solid.is_inside((42.2, 0.0, -111.0))
    assert solid.is_inside((43.6, 0.0, -111.0))
    assert not solid.is_inside((-44.8, 0.0, 2.0))
    assert solid.is_inside((-44.8, 0.0, 5.0))
    assert not solid.is_inside((-40.5, 0.0, Z_MAX - 2.0))
    assert solid.is_inside((-40.5, 0.0, Z_MAX - 8.0))
    assert not solid.is_inside((59.2, 0.0, -48.0))
    assert solid.is_inside((59.2, 0.0, -56.0))
    assert solid.is_inside((55.0, 0.0, -28.0))


@model
def part03_main_housing():
    body = bd.revolve(_shell(), axis=bd.Axis.Z)
    body = fuse(
        body,
        [bd.revolve(_pod(), axis=bd.Axis.Z), _shaft_sleeve(), _boss(), *_lugs(), _rib(120), _rib(240)],
        parallel=True,
    )
    body = cut(body, _features(), parallel=True)
    body = _edge_break(body)
    _assert_housing(body)
    body.label = "part03_main_housing"
    body.color = "#c5ccd3"
    return body


if __name__ == "__main__":
    handle = part03_main_housing()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

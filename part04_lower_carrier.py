# /// script
# dependencies = []
# ///
"""Lower burr carrier. The central well clears the conical pre-breaker."""

import math
from pathlib import Path

import build123d as bd
from cad import model

OD = 64.0
Z_TOP = -8.70
Z_BOTTOM = -26.0
WELL_R = 19.30
BORE_R = 6.0
PCD = 49.20
HOLE_R = 2.10


def cut(base, tool, parallel=True):
    del parallel
    if isinstance(tool, (list, tuple)):
        return base.cut(*tool)
    return base.cut(tool)


def _profile():
    return bd.Plane.XZ * bd.Polygon(
        (31.5, Z_BOTTOM),
        (OD / 2, Z_BOTTOM + 0.5),
        (OD / 2, Z_TOP - 0.5),
        (31.5, Z_TOP),
        (28.4, Z_TOP),
        (27.9, Z_TOP - 0.5),
        (27.9, -10.40),
        (WELL_R + 0.5, -10.40),
        (WELL_R, -10.90),
        (WELL_R, -19.0),
        (BORE_R + 0.5, -19.0),
        (BORE_R, -19.5),
        (BORE_R, Z_BOTTOM + 0.5),
        (BORE_R + 0.5, Z_BOTTOM),
    )


def _holes_and_keyway():
    tool = bd.Pos(0, 0, Z_BOTTOM - 1.0) * bd.Cylinder(
        HOLE_R, 20.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    )
    holes = [
        loc * tool
        for loc in bd.PolarLocations(PCD / 2, 3, rotate=False).local_locations
    ]
    # DIN-style hub keyway for a 12 mm shaft: 4 mm wide, 1.8 mm deep.
    keyway = bd.Pos(6.9, 0, -22.5) * bd.Box(
        1.8, 4.0, 8.2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)
    )
    return [*holes, keyway]


def _edge_break(solid):
    try:
        picked = [
            edge
            for edge in solid.edges()
            if edge.geom_type == bd.GeomType.CIRCLE and abs(edge.radius - HOLE_R) < 0.05
        ]
        if picked:
            solid = solid.chamfer(0.4, picked)
    except Exception:
        pass
    return solid


def _assert_carrier(solid):
    box = solid.bounding_box()
    assert abs(box.max.Z - Z_TOP) < 0.05, box.max
    assert abs(box.min.Z - Z_BOTTOM) < 0.05, box.min
    assert abs(box.max.X - OD / 2) < 0.08, box.max
    assert abs(box.max.Y - OD / 2) < 0.08, box.max
    assert len(solid.solids()) == 1
    assert not solid.is_inside((0.0, 0.0, -15.0))
    assert not solid.is_inside((19.0, 0.0, -15.0))
    assert solid.is_inside((19.8, 0.0, -15.0))
    assert not solid.is_inside((10.0, 0.0, -18.6))
    assert solid.is_inside((10.0, 0.0, -20.0))
    assert not solid.is_inside((0.0, 0.0, -22.0))
    assert solid.is_inside((9.0, 0.0, -22.0))
    assert not solid.is_inside((7.0, 0.0, -22.0))
    assert not solid.is_inside((21.7, 12.5, -9.4))
    assert solid.is_inside((21.7, 12.5, -14.0))
    assert solid.is_inside((30.0, 0.0, -16.0))
    assert not solid.is_inside((PCD / 2, 0.0, -18.0))


@model
def part04_lower_carrier():
    body = bd.revolve(_profile(), axis=bd.Axis.Z)
    body = cut(body, _holes_and_keyway(), parallel=True)
    body = _edge_break(body)
    _assert_carrier(body)
    body.label = "part04_lower_carrier"
    body.color = "#b7c0c7"
    return body


if __name__ == "__main__":
    handle = part04_lower_carrier()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

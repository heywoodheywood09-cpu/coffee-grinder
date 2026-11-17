# /// script
# dependencies = []
# ///
"""Inner chasing burr. Wide base on the lower carrier, tapering up."""

from pathlib import Path

import build123d as bd
from cad import model

SCALE = 37.80 / 42.75
HEIGHT = 31.50
FLANGE = 2.50
CONE_H = 29.00
LARGE_R = 42.75 / 2.0 * SCALE
SMALL_R = 21.40 / 2.0 * SCALE
RIM_R = 38.50 / 2.0 * SCALE
BORE_R = 6.0
HUB_R = 7.4
VANE_T = 2.2


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
    return bd.revolve(
        bd.Plane.XZ
        * bd.Polygon(
            (BORE_R, 0.0),
            (LARGE_R, 0.0),
            (LARGE_R, FLANGE),
            (SMALL_R, HEIGHT),
            (HUB_R, HEIGHT),
            (HUB_R, HEIGHT - 2.0),
            (BORE_R, HEIGHT - 2.0),
        ),
        axis=bd.Axis.Z,
    )


def _vanes():
    mask = bd.Cylinder(
        LARGE_R, FLANGE, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
    ).fuse(
        bd.Pos(0, 0, FLANGE)
        * bd.Cone(
            LARGE_R,
            SMALL_R,
            CONE_H,
            align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
        )
    )
    span = LARGE_R - HUB_R
    blade = bd.Pos(HUB_R + span / 2.0, 0, HEIGHT / 2.0) * bd.Box(
        span, VANE_T, HEIGHT - 0.8, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)
    )
    blades = [bd.Rot(0, 0, angle) * blade for angle in range(0, 360, 60)]
    vanes = mask.intersect(bd.Compound(blades))
    if isinstance(vanes, bd.ShapeList):
        vanes = bd.Compound(list(vanes))
    return vanes


def _key():
    return bd.Pos(6.9, 0, 4.0) * bd.Box(
        1.8, 4.0, 10.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)
    )


def _assert_burr(solid):
    box = solid.bounding_box()
    assert abs(box.min.Z) < 0.05, box.min
    assert abs(box.max.Z - HEIGHT) < 0.08, box.max
    assert abs(box.max.X - LARGE_R) < 0.12, box.max
    assert LARGE_R * 2 <= 38.00
    assert len(solid.solids()) == 1
    assert not solid.is_inside((0.0, 0.0, 16.0))
    assert solid.is_inside((LARGE_R - 0.4, 0.0, 0.8))
    assert solid.is_inside((SMALL_R - 0.4, 0.0, HEIGHT - 0.6))
    assert not solid.is_inside((LARGE_R - 0.4, 0.0, HEIGHT - 0.6))


@model
def part05_inner_chasing_burr():
    body = fuse(_shell(), _vanes(), parallel=True)
    body = cut(body, _key(), parallel=True)
    try:
        bottom = [
            edge
            for edge in body.edges()
            if edge.geom_type == bd.GeomType.CIRCLE
            and abs(edge.center().Z) < 0.05
            and edge.radius > LARGE_R - 0.2
        ]
        if bottom:
            body = body.chamfer(0.3, bottom)
    except Exception:
        pass
    _assert_burr(body)
    body.label = "part05_inner_chasing_burr"
    body.color = "#8a9096"
    return body


if __name__ == "__main__":
    handle = part05_inner_chasing_burr()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

"""Chasing-burr outer bowl, resized from Ø67.70 to the 64 mm flat-burr mount."""

import math
from pathlib import Path

import build123d as bd
from cad import model

OD = 64.20
THICK = 15.90
BORE = 38.20
PCD = 49.20
HOLE_D = 5.60
CHAMFER = 0.50
N_LOBE = 15
LOBE_RC = 52.44 / 2.0
LOBE_RS = 7.60
# Keep an outer ring so the Ø5.60 holes still have a wall; teeth fill the inside.
LOBE_CLIP_R = OD / 2.0 - 3.5


def cut(base, tool, parallel=True):
    del parallel
    return base.cut(tool)


def _through(radius, x=0.0, y=0.0):
    return bd.Pos(x, y, -THICK - 5.0) * bd.Cylinder(
        radius,
        THICK + 10.0,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )


def _star_and_holes():
    star = _through(BORE / 2.0)
    lobes = []
    for index in range(N_LOBE):
        angle = math.radians(index * 360.0 / N_LOBE)
        lobes.append(_through(LOBE_RS, LOBE_RC * math.cos(angle), LOBE_RC * math.sin(angle)))
    star = star.fuse(*lobes).intersect(_through(LOBE_CLIP_R))
    if isinstance(star, bd.ShapeList):
        star = bd.Compound(list(star))
    holes = []
    for index in range(3):
        angle = math.radians(index * 120.0)
        holes.append(
            _through(HOLE_D / 2.0, (PCD / 2.0) * math.cos(angle), (PCD / 2.0) * math.sin(angle))
        )
    return star, bd.Compound(holes)


def _assert_bowl(solid):
    box = solid.bounding_box()
    assert abs(box.max.X - OD / 2.0) < 0.08, box.size
    assert abs(box.max.Z) < 0.05, box.size
    assert abs(box.min.Z + THICK) < 0.08, box.size
    assert not solid.is_inside((0.0, 0.0, -THICK / 2.0))
    assert not solid.is_inside((PCD / 2.0, 0.0, -THICK / 2.0))
    assert solid.is_inside((30.0, 0.0, -2.0))


@model
def chasing_outer_bowl():
    body = bd.Cylinder(
        OD / 2.0,
        THICK,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MAX),
    )
    star, holes = _star_and_holes()
    body = cut(body, star, parallel=True)
    body = cut(body, holes, parallel=True)
    bottom = [
        edge
        for edge in body.edges()
        if edge.geom_type == bd.GeomType.CIRCLE
        and abs(edge.center().Z + THICK) < 0.05
        and edge.radius > 30.0
    ]
    if bottom:
        body = bd.chamfer(bottom, CHAMFER)
    _assert_bowl(body)
    body.label = "chasing_outer_bowl"
    body.color = "#8a9096"
    return body


if __name__ == "__main__":
    handle = chasing_outer_bowl()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

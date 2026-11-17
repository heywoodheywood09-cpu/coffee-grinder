"""TOP钢圈 drawing: 64.20 mm burr blank, 8.70 mm thick.

Tooth flanks are the sheet's 跟办 teeth, shaped to the photographed burr.
"""

import math
from pathlib import Path

import build123d as bd
from cad import model

OD = 64.20
THICK = 8.70
BORE = 38.00
RECESS_D = 55.70
RECESS_DEPTH = 1.95
PCD = 49.20
HOLE_D = 5.60
CBORB_D = 9.00
CBORB_DEPTH = 1.15


def _blank():
    bore_r = BORE / 2.0
    recess_r = RECESS_D / 2.0
    outer_r = OD / 2.0
    profile = bd.Plane.XZ * bd.Polygon(
        (bore_r, 2.45),
        (bore_r, THICK - 0.50),
        (bore_r + 0.50, THICK),
        (outer_r - 0.30, THICK),
        (outer_r, THICK - 0.30),
        (outer_r, 0.70),
        (outer_r - 0.70, 0.0),
        (recess_r + 0.50, 0.0),
        (recess_r, 0.50),
        (recess_r, RECESS_DEPTH),
        (bore_r + 0.50, RECESS_DEPTH),
    )
    return bd.revolve(profile, axis=bd.Axis.Z)


def _teeth():
    tools = []
    for index in range(60):
        tools.append(
            bd.Rot(0, 0, index * 6.0)
            * bd.Pos(27.2, 0.0, THICK - 0.15)
            * bd.Rot(0, 0, 12.0)
            * bd.Box(10.4, 0.85, 1.5)
        )
    for index in range(12):
        tools.append(
            bd.Rot(0, 0, index * 30.0 + 15.0)
            * bd.Pos(23.0, 0.0, THICK - 0.2)
            * bd.Rot(0, 0, 18.0)
            * bd.Box(7.2, 2.0, 1.8)
        )
    return bd.Compound(tools)


def _holes():
    tools = []
    for index in range(3):
        angle = math.radians(index * 120.0)
        x = (PCD / 2.0) * math.cos(angle)
        y = (PCD / 2.0) * math.sin(angle)
        tools.append(
            bd.Pos(x, y, -1.0)
            * bd.Cylinder(HOLE_D / 2.0, THICK + 4.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        )
        tools.append(
            bd.Pos(x, y, THICK - CBORB_DEPTH)
            * bd.Cylinder(CBORB_D / 2.0, CBORB_DEPTH + 1.0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
        )
    return bd.Compound(tools)


def _assert_burr(solid):
    box = solid.bounding_box()
    assert abs(box.max.Z - THICK) < 0.05 and abs(box.min.Z) < 0.02, box.size
    assert abs(box.max.X - OD / 2.0) < 0.05 and abs(box.max.Y - OD / 2.0) < 0.05, box.size
    cylinders = [
        face.radius for face in solid.faces() if face.geom_type == bd.GeomType.CYLINDER
    ]
    for radius in (BORE / 2.0, RECESS_D / 2.0, OD / 2.0, HOLE_D / 2.0, CBORB_D / 2.0):
        assert any(abs(found - radius) < 0.05 for found in cylinders), radius
    assert not solid.is_inside((0.0, 0.0, THICK / 2.0))
    assert solid.is_inside((30.0, 0.0, THICK / 2.0))
    assert not solid.is_inside((0.0, 0.0, 0.4))


@model
def top_steel_ring():
    body = _blank()
    body = body.cut(_teeth())
    body = body.cut(_holes())
    _assert_burr(body)
    body.label = "top_steel_ring"
    body.color = "#d5d8dc"
    return body


if __name__ == "__main__":
    handle = top_steel_ring()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

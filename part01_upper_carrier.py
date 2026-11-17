# /// script
# dependencies = ["bd_warehouse"]
# ///
"""T-shaped upper burr carrier. One revolve, an ISO thread, one batched cut."""

import math
from pathlib import Path

import build123d as bd
from cad import model

ENABLE_REAL_THREAD = False
if ENABLE_REAL_THREAD:
    from bd_warehouse.thread import IsoThread

PITCH = 1.0
MAJOR_D = 72.0
ROOT_R = (MAJOR_D - 1.25 * (PITCH / 2.0) / math.tan(math.radians(30.0))) / 2.0
RELIEF_R = 35.2
SKIRT_R = 45.0
BORE_R = 19.1
RECESS_R = 27.9
WALL = 3.5


def cut(base, tool, parallel=True):
    del parallel
    return base.cut(tool)


def fuse(base, tool, parallel=True):
    del parallel
    return base.fuse(tool)


def _funnel():
    # Hopper opens upward: narrow at the skirt, wide at the rim.
    length = math.hypot(9.0, 42.0)
    tangent_r, tangent_z = 9.0 / length, 42.0 / length
    normal_r, normal_z = -tangent_z, tangent_r
    r_ref = SKIRT_R + WALL * normal_r
    z_ref = 85.0 + WALL * normal_z

    def wall_radius(z_value):
        return r_ref + (tangent_r / tangent_z) * (z_value - z_ref)

    r_at_43 = wall_radius(43.0)
    z_join = 43.0 - (r_at_43 - BORE_R) * math.tan(math.radians(60.0))
    return wall_radius, r_at_43, z_join


def _profile(wall_radius, r_at_43, z_join):
    major_r = MAJOR_D / 2.0
    return bd.Plane.XZ * bd.Polygon(
        (BORE_R + 0.5, 1.70),
        (BORE_R, 2.20),
        (BORE_R, z_join),
        (r_at_43, 43.0),
        (wall_radius(85.0), 85.0),
        (SKIRT_R, 85.0),
        (major_r, 43.0),
        (SKIRT_R, 43.0),
        (SKIRT_R, 21.0),
        (RELIEF_R, 21.0),
        (RELIEF_R, 18.5),
        *((ROOT_R, 17.5), (ROOT_R, 1.0), (ROOT_R - 1.0, 0.0))
        if ENABLE_REAL_THREAD
        else ((major_r, 18.5), (major_r, 1.0), (major_r - 1.0, 0.0)),
        (RECESS_R, 0.0),
        (RECESS_R, 1.70),
    )


def _thread():
    return bd.Pos(0, 0, 2.5) * IsoThread(
        major_diameter=MAJOR_D,
        pitch=PITCH,
        length=15.0,
        external=True,
        end_finishes=("chamfer", "fade"),
        simple=True,
        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN),
    )


def _batch_tools():
    tools = []
    for index in range(60):
        angle = math.radians(index * 6.0)
        tools.append(
            bd.Pos(40.5 * math.cos(angle), 40.5 * math.sin(angle), 20.8) * bd.Sphere(0.8)
        )
    for index in range(36):
        angle = math.radians(index * 10.0)
        tools.append(
            bd.Pos(45.2 * math.cos(angle), 45.2 * math.sin(angle), 32.0)
            * bd.Cylinder(0.65, 18.0)
        )
    for index in range(3):
        angle = math.radians(index * 120.0)
        tools.append(
            bd.Pos(24.6 * math.cos(angle), 24.6 * math.sin(angle), 42.0)
            * bd.Cylinder(2.1, 90.0)
        )
    return bd.Compound(tools)


def _assert_carrier(solid):
    box = solid.bounding_box()
    assert abs(box.min.Z) < 1e-3 and abs(box.max.Z - 85.0) < 0.05, box.size
    assert abs(box.max.X - SKIRT_R) < 0.08 and abs(box.max.Y - SKIRT_R) < 0.08, box.size
    assert not solid.is_inside((24.6, 0.0, 75.0))
    assert not solid.is_inside((40.5, 0.0, 21.3))
    assert solid.is_inside((40.5, 0.0, 21.75))
    assert not solid.is_inside((0.0, 0.0, 60.0))


@model
def part01_upper_carrier():
    wall_radius, r_at_43, z_join = _funnel()
    assert z_join > 2.2
    body = bd.revolve(_profile(wall_radius, r_at_43, z_join), axis=bd.Axis.Z)
    if ENABLE_REAL_THREAD:
        body = fuse(body, _thread(), parallel=True)
    body = cut(body, _batch_tools(), parallel=True)
    _assert_carrier(body)
    body.label = "part01_upper_carrier"
    body.color = "#c5ccd3"
    return body


if __name__ == "__main__":
    handle = part01_upper_carrier()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

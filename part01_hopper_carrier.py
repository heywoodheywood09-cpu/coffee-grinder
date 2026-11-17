"""Part 01: T-shaped quick-release upper burr carrier with integrated hopper."""

import math
from pathlib import Path

import build123d as bd
from cad import model

PITCH = 1.0
THREAD_DEPTH = 0.65
THREAD_EMBED = 0.05
NECK_R = 36.0
RELIEF_R = 35.2
SKIRT_R = 45.0
BORE_R = 19.1
RECESS_R = 27.9
WALL = 3.5


def cut(base, tool, parallel=True):
    # Shape.cut always runs BRepAlgoAPI_Cut with SetRunParallel(True).
    del parallel
    return base.cut(tool)


def _funnel():
    """3.5 mm wall normal to the outer cone, then a 60° chute into the bore."""
    length = math.hypot(9.0, 42.0)
    tangent_r, tangent_z = -9.0 / length, 42.0 / length
    normal_r, normal_z = -tangent_z, tangent_r
    r_ref = NECK_R + WALL * normal_r
    z_ref = 85.0 + WALL * normal_z

    def wall_radius(z_value):
        return r_ref + (tangent_r / tangent_z) * (z_value - z_ref)

    r_at_43 = wall_radius(43.0)
    z_join = 43.0 - (r_at_43 - BORE_R) * math.tan(math.radians(60.0))
    return wall_radius, r_at_43, z_join, tangent_z


def _profile(wall_radius, r_at_43, z_join):
    return bd.Plane.XZ * bd.Polygon(
        (BORE_R + 0.5, 1.70),
        (BORE_R, 2.20),
        (BORE_R, z_join),
        (r_at_43, 43.0),
        (wall_radius(85.0), 85.0),
        (NECK_R, 85.0),
        (SKIRT_R, 43.0),
        (SKIRT_R, 21.0),
        (RELIEF_R, 21.0),
        (RELIEF_R, 18.5),
        (NECK_R, 18.5),
        (NECK_R, 1.0),
        (NECK_R - 1.0, 0.0),
        (RECESS_R, 0.0),
        (RECESS_R, 1.70),
    )


def _thread():
    height = THREAD_DEPTH + THREAD_EMBED
    half_base = height * math.tan(math.radians(30.0))
    helix_r = NECK_R - THREAD_DEPTH + height / 2.0
    helix = bd.Helix(pitch=PITCH, height=15.0, radius=helix_r, center=(0, 0, 2.5))
    start = bd.Vector(helix @ 0)
    radial = bd.Vector(start.X, start.Y, 0).normalized()
    plane = bd.Plane(origin=start, x_dir=radial, z_dir=helix.tangent_at(0))
    profile = plane * bd.Polygon(
        (height / 2.0, -half_base),
        (-height / 2.0, 0),
        (height / 2.0, half_base),
    )
    return bd.sweep(profile, helix, is_frenet=True)


def _batch_tools():
    tools = []
    for index in range(60):
        angle = math.radians(index * 6.0)
        tools.append(
            bd.Pos(40.5 * math.cos(angle), 40.5 * math.sin(angle), 20.8) * bd.Sphere(0.8)
        )
    for index in range(3):
        angle = math.radians(index * 120.0)
        tools.append(
            bd.Pos(24.6 * math.cos(angle), 24.6 * math.sin(angle), 42.0)
            * bd.Cylinder(2.1, 90.0)
        )
    return bd.Compound(tools)


def _surface_radii(solid, z_value):
    """Radii where a ray leaves the void and enters the wall, then leaves the wall."""
    angle = math.radians(20.0)
    previous = False
    radii = []
    radius = 0.0
    step = 0.5
    while radius < 50.0:
        radius += step
        point = (radius * math.cos(angle), radius * math.sin(angle), z_value)
        inside = solid.is_inside(point)
        if inside != previous:
            low, high = radius - step, radius
            for _ in range(14):
                mid = (low + high) / 2.0
                probe = (mid * math.cos(angle), mid * math.sin(angle), z_value)
                if solid.is_inside(probe) == previous:
                    low = mid
                else:
                    high = mid
            radii.append(high)
            previous = inside
    return radii


def _assert_carrier(solid, wall_radius):
    box = solid.bounding_box()
    assert abs(box.min.Z) < 1e-3 and abs(box.max.Z - 85.0) < 0.05, box.size
    assert abs(box.max.X - SKIRT_R) < 0.05 and abs(box.min.X + SKIRT_R) < 0.05, box.size
    assert abs(box.max.Y - SKIRT_R) < 0.05 and abs(box.min.Y + SKIRT_R) < 0.05, box.size

    cylinders = [
        face.radius for face in solid.faces() if face.geom_type == bd.GeomType.CYLINDER
    ]
    for radius in (BORE_R, RECESS_R, RELIEF_R, NECK_R, SKIRT_R, 2.1):
        assert any(abs(found - radius) < 0.03 for found in cylinders), radius

    for z_low, z_high, expect in ((60.0, 75.0, 77.9), (30.0, 36.0, 60.0)):
        inner_low, outer_low = _surface_radii(solid, z_low)
        inner_high, outer_high = _surface_radii(solid, z_high)
        slope = math.degrees(math.atan2(z_high - z_low, abs(inner_high - inner_low)))
        assert slope > 55.0, slope
        assert abs(slope - expect) < 1.5, (slope, expect)
        assert outer_low > inner_low and outer_high > inner_high

    inner_60, outer_60 = _surface_radii(solid, 60.0)
    length = math.hypot(9.0, 42.0)
    normal = (outer_60 - inner_60) * (42.0 / length)
    assert abs(normal - WALL) < 0.15, normal
    assert abs(inner_60 - wall_radius(60.0)) < 0.15

    # Screw axes stay in the open hopper above the holes.
    assert not solid.is_inside((24.6, 0.0, 70.0))
    assert not solid.is_inside((24.6, 0.0, 84.0))
    assert solid.is_inside((21.0, 0.0, 3.0))

    # Dimple on the +X shoulder: 0.6 mm deep, material remains below the sphere.
    assert not solid.is_inside((40.5, 0.0, 21.3))
    assert solid.is_inside((40.5, 0.0, 21.75))

    # z=10 is 7.5 turns: root on -X, crest on +X.
    assert not solid.is_inside((-(NECK_R - 0.50), 0.0, 10.0))
    assert solid.is_inside((-(NECK_R - 0.80), 0.0, 10.0))
    assert solid.is_inside((NECK_R - 0.05, 0.0, 10.0))


@model
def part01_hopper_carrier():
    wall_radius, r_at_43, z_join, _cosine = _funnel()
    assert z_join > 2.5
    body = bd.revolve(_profile(wall_radius, r_at_43, z_join), axis=bd.Axis.Z)
    body = cut(body, _thread(), parallel=True)
    body = cut(body, _batch_tools(), parallel=True)
    rim = [
        edge
        for edge in body.edges()
        if edge.geom_type == bd.GeomType.CIRCLE
        and abs(edge.center().Z - 85.0) < 0.05
        and edge.radius > 30.0
    ]
    body = bd.fillet(rim, 1.0)
    _assert_carrier(body, wall_radius)
    body.label = "part01_hopper_carrier"
    body.color = "#c4beb4"
    return body


if __name__ == "__main__":
    handle = part01_hopper_carrier()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

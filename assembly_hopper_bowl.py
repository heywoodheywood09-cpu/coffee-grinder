# /// script
# dependencies = ["bd_warehouse"]
# ///
"""Hopper, 64 mm TOP burr, and chasing outer bowl on one screw circle."""

from pathlib import Path

import build123d as bd
from cad import model

from part01_upper_carrier import part01_upper_carrier
from part02_chasing_outer_bowl import chasing_outer_bowl
from top_steel_ring import top_steel_ring

BURR_THICK = 8.70
BOWL_THICK = 15.90
PCD_R = 24.6


@model
def hopper_with_outer_bowl():
    hopper = part01_upper_carrier().shape
    hopper.label = "part01_upper_carrier"

    bowl = chasing_outer_bowl().shape
    bowl.label = "chasing_outer_bowl"

    burr = top_steel_ring().shape.mirror(bd.Plane.XY).translate((0, 0, -BOWL_THICK))
    burr.label = "top_steel_ring"

    raw_burr = top_steel_ring().shape
    assert not hopper.is_inside((PCD_R, 0.0, 5.0))
    assert not raw_burr.is_inside((PCD_R, 0.0, 4.0))
    assert not bowl.is_inside((PCD_R, 0.0, -8.0))
    assert not hopper.is_inside((0.0, 0.0, 5.0))
    assert not raw_burr.is_inside((0.0, 0.0, 4.0))
    assert not bowl.is_inside((0.0, 0.0, -8.0))

    assembly = bd.Compound(
        children=[hopper, burr, bowl],
        label="hopper_with_outer_bowl",
    )
    box = assembly.bounding_box()
    assert abs(box.max.Z - 85.0) < 0.05, box.size
    assert box.min.Z < -20.0
    return assembly


if __name__ == "__main__":
    handle = hopper_with_outer_bowl()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)

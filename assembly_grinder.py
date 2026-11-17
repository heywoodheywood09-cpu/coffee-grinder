# /// script
# dependencies = ["bd_warehouse"]
# ///
"""Hopper, outer conical burr, both flat burrs, and the pre-breaker.

PDF flat burr: Ø64.20 x 8.70 mm. The outer burr is the 15.90 mm chasing bowl.
Order below the hopper: outer burr, upper flat burr, grind gap, lower flat burr.
"""

from pathlib import Path

import build123d as bd
from cad import model

from part01_upper_carrier import part01_upper_carrier
from part02_chasing_outer_bowl import chasing_outer_bowl
from part03_main_housing import part03_main_housing
from part04_lower_carrier import part04_lower_carrier
from part05_inner_chasing_burr import HEIGHT as INNER_H
from part05_inner_chasing_burr import part05_inner_chasing_burr
from top_steel_ring import top_steel_ring

HOPPER_LIFT = 6.0
BOWL_THICK = 15.90
BURR_THICK = 8.70
GRIND_GAP = 0.30


@model
def grinder_stack():
    housing = part03_main_housing().shape
    housing.label = "part03_main_housing"

    hopper = part01_upper_carrier().shape.translate((0, 0, HOPPER_LIFT))
    hopper.label = "part01_upper_carrier"

    # Existing upper outer burr. Its top face meets the hopper bottom.
    bowl = chasing_outer_bowl().shape.translate((0, 0, HOPPER_LIFT))
    bowl.label = "upper_outer_burr"

    # Teeth face down. Back sits on the underside of the outer burr.
    upper = top_steel_ring().shape.mirror(bd.Plane.XY).translate((0, 0, HOPPER_LIFT - BOWL_THICK))
    upper.label = "upper_flat_burr"

    upper_tooth = HOPPER_LIFT - BOWL_THICK - BURR_THICK
    lower_tooth = upper_tooth - GRIND_GAP
    lower_back = lower_tooth - BURR_THICK
    carrier = part04_lower_carrier().shape.translate((0, 0, lower_back - (-8.70)))
    carrier.label = "part04_lower_carrier"

    # Teeth face up. Back sits on the carrier top.
    lower = top_steel_ring().shape.translate((0, 0, lower_back))
    lower.label = "lower_flat_burr"

    inner = part05_inner_chasing_burr().shape.translate((0, 0, lower_back))
    inner.label = "inner_chasing_burr"

    bowl_box = bowl.bounding_box()
    upper_box = upper.bounding_box()
    lower_box = lower.bounding_box()
    carrier_box = carrier.bounding_box()
    assert abs(bowl_box.max.Z - HOPPER_LIFT) < 0.15, bowl_box.max
    assert abs(bowl_box.min.Z - (HOPPER_LIFT - BOWL_THICK)) < 0.2, bowl_box.min
    assert abs(upper_box.min.Z - upper_tooth) < 0.15, upper_box.min
    assert abs(lower_box.max.Z - lower_tooth) < 0.15, lower_box.max
    assert carrier_box.min.Z > -47.0, carrier_box.min
    assert abs(lower_box.min.Z - carrier_box.max.Z) < 0.15
    inner_box = inner.bounding_box()
    assert not lower.is_inside((0.0, 0.0, lower_tooth - 4.0))
    assert abs(inner_box.min.Z - carrier_box.max.Z) < 0.15, inner_box.min
    assert abs(inner_box.max.Z - (lower_back + INNER_H)) < 0.15, inner_box.max
    assert inner_box.max.Z < HOPPER_LIFT
    assert inner_box.max.X * 2 < 38.00
    assert inner.is_inside((18.5, 0.0, lower_back + 0.8))
    assert not inner.is_inside((18.5, 0.0, lower_back + INNER_H - 0.6))
    assert bowl.is_inside((30.0, 0.0, HOPPER_LIFT - 2.0))

    return bd.Compound(
        children=[housing, hopper, bowl, upper, inner, lower, carrier],
        label="grinder_stack",
    )


if __name__ == "__main__":
    handle = grinder_stack()
    destination = Path(__file__).resolve().with_suffix(".step")
    model.export(handle, destination)
    print(destination)
    print(handle.id)

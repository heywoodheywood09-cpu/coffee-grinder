"""T-shaped upper burr carrier for Autodesk Fusion.

Run from Utilities > Scripts and Add-Ins. Fusion API calls stay on the main
thread. Lengths are centimeters internally, so every millimetre is divided by
10. The M72x1 thread is one Coil feature. The 60 detent dimples and the 3
mounting holes are CircularPatternFeatures, not loops of features.

Ten turns at 1.00 mm pitch sit in the Z = 2 to 16 mm band on the 72 mm neck.
The triangle is a 60-degree metric flank with 0.65 mm radial height.
"""

import adsk.core
import adsk.fusion
import time

PAUSE_SECONDS = 0.4

NECK_OD_MM = 72.0
NECK_HEIGHT_MM = 18.0
SKIRT_OD_MM = 90.0
SKIRT_TOP_MM = 43.0
HOPPER_TOP_MM = 85.0
HOPPER_TOP_OD_MM = 68.0
WALL_MM = 3.50
RIM_FILLET_MM = 1.0
THREAD_PITCH_MM = 1.0
THREAD_TURNS = 10
THREAD_HEIGHT_MM = 0.65
THREAD_EMBED_MM = 0.05
THREAD_Z_MIN_MM = 2.0
DIMPLE_COUNT = 60
DIMPLE_DIAMETER_MM = 1.60
DIMPLE_DEPTH_MM = 0.60
DIMPLE_PCD_MM = 81.0
RECESS_DIAMETER_MM = 55.80
RECESS_DEPTH_MM = 1.70
BORE_DIAMETER_MM = 38.20
HOLE_DIAMETER_MM = 4.20
HOLE_PCD_MM = 49.20
HOLE_COUNT = 3


def mm(value_mm):
    return value_mm / 10.0


def show(app):
    viewport = app.activeViewport
    viewport.fit()
    viewport.refresh()
    adsk.doEvents()
    time.sleep(PAUSE_SECONDS)


def add_sketch(component, plane, name):
    sketch = component.sketches.add(plane)
    sketch.name = name
    return sketch


def add_circle(sketch, x_value, y_value, radius):
    sketch.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(x_value, y_value, 0), radius
    )
    if sketch.profiles.count < 1:
        raise RuntimeError("Sketch '{}' has no profile.".format(sketch.name))
    return sketch.profiles.item(0)


def add_polygon(sketch, points):
    lines = sketch.sketchCurves.sketchLines
    sketch_points = [adsk.core.Point3D.create(x_value, y_value, 0) for x_value, y_value in points]
    for index, start in enumerate(sketch_points):
        lines.addByTwoPoints(start, sketch_points[(index + 1) % len(sketch_points)])
    if sketch.profiles.count < 1:
        raise RuntimeError("Sketch '{}' has no closed profile.".format(sketch.name))
    return sketch.profiles.item(0)


def extrude_distance(component, profile, operation, distance_cm, direction):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operation)
    extent = adsk.fusion.DistanceExtentDefinition.create(
        adsk.core.ValueInput.createByReal(distance_cm)
    )
    extrude_input.setOneSideExtent(extent, direction)
    return extrudes.add(extrude_input)


def extrude_through(component, profile, operation, direction):
    extrudes = component.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, operation)
    extrude_input.setAllExtent(direction)
    return extrudes.add(extrude_input)


def revolve_full(component, profile, axis, operation):
    revolves = component.features.revolveFeatures
    revolve_input = revolves.createInput(profile, axis, operation)
    revolve_input.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
    return revolves.add(revolve_input)


def circular_pattern(component, feature, count, name):
    features = adsk.core.ObjectCollection.create()
    features.add(feature)
    patterns = component.features.circularPatternFeatures
    pattern_input = patterns.createInput(features, component.zConstructionAxis)
    pattern_input.quantity = adsk.core.ValueInput.createByReal(count)
    pattern_input.totalAngle = adsk.core.ValueInput.createByString("360 deg")
    pattern_input.isSymmetric = False
    pattern_input.patternComputeOption = (
        adsk.fusion.PatternComputeOptions.OptimizedPatternCompute
    )
    pattern = patterns.add(pattern_input)
    pattern.name = name
    return pattern


def offset_plane(component, base_plane, z_cm, name):
    plane_input = component.constructionPlanes.createInput()
    plane_input.setByOffset(base_plane, adsk.core.ValueInput.createByReal(z_cm))
    plane = component.constructionPlanes.add(plane_input)
    plane.name = name
    return plane


def inner_radii(outer_r_base, outer_r_top, z_base, z_top, wall):
    delta_r = outer_r_top - outer_r_base
    delta_z = z_top - z_base
    length = (delta_r * delta_r + delta_z * delta_z) ** 0.5
    tangent_r = delta_r / length
    tangent_z = delta_z / length
    origin_r = outer_r_base - tangent_z * wall
    origin_z = z_base + tangent_r * wall

    def radius_at(z_value):
        distance = (z_value - origin_z) / tangent_z
        return origin_r + tangent_r * distance

    return radius_at(z_base), radius_at(z_top)


def rim_edges(body, z_top, inner_radius, outer_radius):
    edges = adsk.core.ObjectCollection.create()
    targets = (inner_radius, outer_radius)
    for edge in body.edges:
        geometry = edge.geometry
        curve_type = geometry.curveType
        if curve_type == adsk.core.CurveTypes.CircleCurveType:
            curve = adsk.core.Circle3D.cast(geometry)
        elif curve_type == adsk.core.CurveTypes.ArcCurveType:
            curve = adsk.core.Arc3D.cast(geometry)
        else:
            continue
        if curve is None or abs(curve.center.z - z_top) > 0.02:
            continue
        for target in targets:
            if abs(curve.radius - target) < 0.03:
                edges.add(edge)
                break
    return edges


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            raise RuntimeError("Open a Fusion design, then run this script.")

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        occurrence = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        component = occurrence.component
        component.name = "Part 01 Upper Burr Carrier"

        positive = adsk.fusion.ExtentDirections.PositiveExtentDirection
        xy_plane = component.xYConstructionPlane
        xz_plane = component.xZConstructionPlane
        new_body = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation

        neck_r = mm(NECK_OD_MM) / 2.0
        skirt_r = mm(SKIRT_OD_MM) / 2.0
        top_r = mm(HOPPER_TOP_OD_MM) / 2.0
        z_neck = mm(NECK_HEIGHT_MM)
        z_skirt = mm(SKIRT_TOP_MM)
        z_top = mm(HOPPER_TOP_MM)

        neck_sketch = add_sketch(component, xy_plane, "Threaded neck")
        neck_profile = add_circle(neck_sketch, 0, 0, neck_r)
        show(app)
        neck = extrude_distance(component, neck_profile, new_body, z_neck, positive)
        neck.name = "Lower neck"
        neck.bodies.item(0).name = "Upper Burr Carrier"
        neck_sketch.isVisible = False
        show(app)

        skirt_plane = offset_plane(component, xy_plane, z_neck, "Skirt shoulder")
        skirt_sketch = add_sketch(component, skirt_plane, "Adjustment skirt")
        skirt_profile = add_circle(skirt_sketch, 0, 0, skirt_r)
        show(app)
        skirt = extrude_distance(
            component, skirt_profile, join, z_skirt - z_neck, positive
        )
        skirt.name = "Upper skirt"
        skirt_sketch.isVisible = False
        show(app)

        flank = mm(THREAD_HEIGHT_MM + THREAD_EMBED_MM)
        half_base = flank / (3.0 ** 0.5)
        root_r = neck_r - mm(THREAD_EMBED_MM)
        crest_r = neck_r + mm(THREAD_HEIGHT_MM)
        z_thread = mm(THREAD_Z_MIN_MM) + half_base
        thread_sketch = add_sketch(component, xz_plane, "M72x1 thread profile")
        thread_profile = add_polygon(
            thread_sketch,
            [
                (root_r, z_thread - half_base),
                (crest_r, z_thread),
                (root_r, z_thread + half_base),
            ],
        )
        axis = thread_sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(0, z_top, 0),
        )
        axis.isConstruction = True
        show(app)
        coils = component.features.coilFeatures
        coil_input = coils.createInput(thread_profile, axis)
        coil_input.operation = join
        coil_input.isClockwise = False
        coil_input.setRevolutionAndPitch(
            adsk.core.ValueInput.createByReal(THREAD_TURNS),
            adsk.core.ValueInput.createByReal(mm(THREAD_PITCH_MM)),
        )
        coil = coils.add(coil_input)
        coil.name = "M72x1 external thread"
        thread_sketch.isVisible = False
        show(app)

        dimple_r = mm(DIMPLE_DIAMETER_MM) / 2.0
        dimple_depth = mm(DIMPLE_DEPTH_MM)
        dimple_z = z_neck - (dimple_r - dimple_depth)
        dimple_pcd = mm(DIMPLE_PCD_MM) / 2.0
        dimple_sketch = add_sketch(component, xz_plane, "Detent dimple")
        arc = dimple_sketch.sketchCurves.sketchArcs.addByThreePoints(
            adsk.core.Point3D.create(dimple_pcd, dimple_z - dimple_r, 0),
            adsk.core.Point3D.create(dimple_pcd + dimple_r, dimple_z, 0),
            adsk.core.Point3D.create(dimple_pcd, dimple_z + dimple_r, 0),
        )
        diameter = dimple_sketch.sketchCurves.sketchLines.addByTwoPoints(
            arc.startSketchPoint, arc.endSketchPoint
        )
        dimple_axis = dimple_sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(dimple_pcd, dimple_z - dimple_r - mm(0.2), 0),
            adsk.core.Point3D.create(dimple_pcd, dimple_z + dimple_r + mm(0.2), 0),
        )
        dimple_axis.isConstruction = True
        if dimple_sketch.profiles.count < 1:
            raise RuntimeError("Detent sketch has no profile.")
        show(app)
        dimple = revolve_full(
            component, dimple_sketch.profiles.item(0), dimple_axis, cut
        )
        dimple.name = "Detent dimple"
        dimple_sketch.isVisible = False
        show(app)
        circular_pattern(component, dimple, DIMPLE_COUNT, "Detent dimples x60")
        show(app)

        recess_sketch = add_sketch(component, xy_plane, "Burr alignment recess")
        recess_profile = add_circle(recess_sketch, 0, 0, mm(RECESS_DIAMETER_MM) / 2.0)
        show(app)
        recess = extrude_distance(
            component, recess_profile, cut, mm(RECESS_DEPTH_MM), positive
        )
        recess.name = "Burr alignment recess"
        recess_sketch.isVisible = False
        show(app)

        bore_sketch = add_sketch(component, xy_plane, "Center feed bore")
        bore_profile = add_circle(bore_sketch, 0, 0, mm(BORE_DIAMETER_MM) / 2.0)
        show(app)
        bore = extrude_through(component, bore_profile, cut, positive)
        bore.name = "Center feed bore"
        bore_sketch.isVisible = False
        show(app)

        hole_sketch = add_sketch(component, xy_plane, "Burr mounting hole")
        hole_profile = add_circle(
            hole_sketch,
            mm(HOLE_PCD_MM) / 2.0,
            0,
            mm(HOLE_DIAMETER_MM) / 2.0,
        )
        show(app)
        hole = extrude_through(component, hole_profile, cut, positive)
        hole.name = "Burr mounting hole"
        hole_sketch.isVisible = False
        show(app)
        circular_pattern(component, hole, HOLE_COUNT, "Burr mounting holes x3")
        show(app)

        inner_base, inner_top = inner_radii(skirt_r, top_r, z_skirt, z_top, mm(WALL_MM))
        bite = mm(0.05)
        hopper_sketch = add_sketch(component, xz_plane, "Conical hopper")
        hopper_axis = hopper_sketch.sketchCurves.sketchLines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(0, z_top + mm(2.0), 0),
        )
        hopper_axis.isConstruction = True
        hopper_profile = add_polygon(
            hopper_sketch,
            [
                (inner_base, z_skirt - bite),
                (skirt_r, z_skirt - bite),
                (skirt_r, z_skirt),
                (top_r, z_top),
                (inner_top, z_top),
                (inner_base, z_skirt),
            ],
        )
        show(app)
        hopper = revolve_full(component, hopper_profile, hopper_axis, join)
        hopper.name = "Conical hopper"
        hopper_sketch.isVisible = False
        show(app)

        body = component.bRepBodies.item(0)
        body.name = "Upper Burr Carrier"
        edges = rim_edges(body, z_top, inner_top, top_r)
        if edges.count < 2:
            raise RuntimeError(
                "Expected both top rim edges, found {}.".format(edges.count)
            )
        fillet_input = component.features.filletFeatures.createInput()
        fillet_input.addConstantRadiusEdgeSet(
            edges, adsk.core.ValueInput.createByReal(mm(RIM_FILLET_MM)), False
        )
        fillet = component.features.filletFeatures.add(fillet_input)
        fillet.name = "Top rim fillet"
        show(app)

    except Exception as error:
        if ui:
            ui.messageBox("{0}: {1}".format(type(error).__name__, error))


def stop(context):
    pass

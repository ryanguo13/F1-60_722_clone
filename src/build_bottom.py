# -*- coding: utf-8 -*-
"""Build the BOTTOM case: 7.22° wedge, heat-set pads, weight well, feet, USB."""
import os
import traceback

ROOT = "C:/Users/jguo121/Documents/F1-60 722"
OUT = ROOT + "/out"


def _load(path, name):
    g = {"__name__": name, "__file__": path}
    with open(path, encoding="utf-8") as f:
        exec(compile(f.read(), path, "exec"), g)
    return g


def run(c):
    try:
        _run()
    except Exception:
        print(traceback.format_exc())


def _run():
    import adsk.core
    import adsk.fusion

    L = _load(ROOT + "/src/f1_60_722.py", "layout")
    F = _load(ROOT + "/src/fusion_lib.py", "fusion_lib")
    Builder = F["Builder"]
    loop_area = F["loop_area"]
    W, H = L["W"], L["H"]
    P = L["P"]
    split = P["split_h"]
    split_r = L["split_rear"]()
    floor = P["floor"]
    wall = P["side_wall"]

    app = adsk.core.Application.get()
    for d in list(app.documents):
        try:
            d.close(False)
        except Exception:
            pass
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "BOTTOM"
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    B = Builder(doc, des)

    outer = L["outer_outline"]()
    inner = L["inner_outline"]()
    print("params split", split, "split_rear", round(split_r, 3), "floor", floor)

    body = B.wedge(outer, split, split_r, 0.0, H)
    print("BOTTOM blank vol", round(B.vol(body), 1), "bbox", B.bbox_mm(body),
          "expect ~", round(loop_area(outer) * (split + split_r) / 2.0, 1))

    # Inner well: a wedge up to the split plane, then strip the bottom
    # `floor` mm off the tool so the desk face stays solid.
    well = B.wedge(inner, split, split_r, 0.0, H)
    B.cut_below_z(well, floor)
    print("well tool vol", round(B.vol(well), 1), "bbox", B.bbox_mm(well))
    v0 = B.vol(body)
    B.combine_cut(body, well, keep=False)
    print("cavity removed", round(v0 - B.vol(body), 1), "now", round(B.vol(body), 1))
    # Restore the desk-face floor in case the well tool still punched through.
    slab = B.extrude_new(B.sketch(inner), floor)
    v0 = B.vol(body)
    B.combine_join(body, slab, keep=False)
    print("floor restored", round(B.vol(body) - v0, 1), "now", round(B.vol(body), 1))

    # Restore 14x14 heat-set pads in the four corners, then bore Ø3.6 from desk.
    # Join a rectangular prism of height split_r at each pad, then re-cut
    # anything above the split plane.
    for i, (sx, sy) in enumerate(L["screws"]()):
        pad = L["pad_outline"](sx, sy)
        prism = B.extrude_new(B.sketch(pad), split_r, join=None)
        v0 = B.vol(body)
        B.combine_join(body, prism, keep=False)
        print("pad", i, "joined", round(B.vol(body) - v0, 1), "at", round(sx, 1), round(sy, 1))

    v0 = B.vol(body)
    B.cut_above_plane(body, split, split_r, 0.0, H)
    print("split recut removed", round(v0 - B.vol(body), 1))

    # Insert bores: 5 mm from the desk face (z=0), square 3.6.
    for i, (sx, sy) in enumerate(L["screws"]()):
        v0 = B.vol(body)
        B.cut(B.sketch(L["insert_outline"](sx, sy)), body, P["insert_len"])
        print("insert", i, "removed", round(v0 - B.vol(body), 2),
              "expect", round(P["insert_d"] * P["insert_d"] * P["insert_len"], 2))

    # USB through the rear wall.
    v0 = B.vol(body)
    B.cut(B.sketch(L["usb_outline"]()), body, split_r + 1.0)
    print("usb removed", round(v0 - B.vol(body), 1))

    # Left/right plate paddles: join a 1.5 mm shelf under the plate, sitting
    # on the inner wall. Extrude from z=0 to split so they fill the cavity
    # locally, then they act as a rest for the plate (plate is at typing-1.5,
    # which is above the split by ~6.5 mm at the front... wait.
    #
    # Split is 8 mm, typing is 16 mm at the front. Plate top = typing, plate
    # is 1.5 mm thick so plate bottom = 14.5 at the front, which is ABOVE the
    # split (8 mm). The paddle therefore lives in the TOP, not the BOTTOM.
    # F1-8X paddles are on the TOP inner long edges. Skip paddles on BOTTOM.

    # Weight well: cut a rounded rect from z=0 up, leaving `floor` of material.
    # Remaining floor is already `floor` everywhere if the cavity did its job.
    # Recess the well by cutting from z=0 to 0.1 so we don't break the floor;
    # actually the F2-60 well is a pocket in the floor. Cut 0.0 mm? Skip a
    # second well: the inner cavity already is the weight well. Mark it with
    # an inset 1 mm from the inner wall, cut 0.4 mm from desk? That would
    # punch through the 1.2 mm floor. Don't.

    # Foot recesses: 0.8 mm from the desk face (z=0).
    for i, poly in enumerate(L["foot_outlines"]()):
        v0 = B.vol(body)
        B.cut(B.sketch(poly), body, P["foot_recess"])
        print("foot", i, "removed", round(v0 - B.vol(body), 2),
              "expect", round(abs(loop_area(poly)) * P["foot_recess"], 2))

    body = B.keep_largest()
    v0 = B.vol(body)
    B.cut_above_plane(body, split, split_r, 0.0, H)
    print("BOTTOM clamp removed", round(v0 - B.vol(body), 1))
    print("BOTTOM bbox mm", B.bbox_mm(body))
    print("BOTTOM vol", round(B.vol(body), 1), "faces", body.faces.count,
          "bodies", des.rootComponent.bRepBodies.count)
    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "BOTTOM.step")
    stl = os.path.join(OUT, "BOTTOM.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

# -*- coding: utf-8 -*-
"""Build the TOP case: 7.22° wedge, R3, switch window, USB, bar rebate, M3 holes."""
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
    front = P["front_h"]
    split = P["split_h"]
    rear = L["rear_h"]()
    split_r = L["split_rear"]()
    wall = P["side_wall"]

    app = adsk.core.Application.get()
    for d in list(app.documents):
        try:
            d.close(False)
        except Exception:
            pass
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "TOP"
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    B = Builder(doc, des)

    outer = L["outer_outline"]()
    inner = L["inner_outline"]()
    print("params front", front, "rear", round(rear, 3), "split", split, "split_rear", round(split_r, 3))

    # Full outer wedge from desk to typing plane, then cut away everything
    # below the split plane. Remaining solid is the TOP (8 mm along Z).
    body = B.wedge(outer, front, rear, 0.0, H)
    print("outer wedge vol", round(B.vol(body), 1), "bbox", B.bbox_mm(body),
          "expect ~", round(loop_area(outer) * (front + rear) / 2.0, 1))

    below = B.wedge(outer, split, split_r, 0.0, H)
    print("below-split vol", round(B.vol(below), 1))
    B.combine_cut(body, below, keep=False)
    print("TOP blank vol", round(B.vol(body), 1), "bbox", B.bbox_mm(body),
          "expect ~", round(loop_area(outer) * 8.0, 1))

    # Inner well: a thinner wedge (front/rear minus ceiling) cut from the TOP.
    # Ceiling 0.6 mm is along Z, so inner typing heights drop by 0.6.
    ceil = P["ceil"]
    well = B.wedge(inner, front - ceil, rear - ceil, 0.0, H)
    # The well wedge sits on the desk; only the part that overlaps TOP should cut.
    # Combine-cut clips automatically to the intersection.
    v0 = B.vol(body)
    B.combine_cut(body, well, keep=False)
    print("inner well removed", round(v0 - B.vol(body), 1), "now", round(B.vol(body), 1))

    # Switch window through the remaining 0.6 mm roof.
    v0 = B.vol(body)
    B.cut(B.sketch(L["switch_window"]()), body, rear + 1.0)
    print("switch window removed", round(v0 - B.vol(body), 1))

    # USB pill through the rear wall.
    v0 = B.vol(body)
    B.cut(B.sketch(L["usb_outline"]()), body, rear + 1.0)
    print("usb removed", round(v0 - B.vol(body), 1))

    # Accent-bar rebate: 3 mm along Z under the typing face, back edge only.
    bar = L["bar_outline"]()
    bx0 = min(p[0] for p in bar) - 0.2
    bx1 = max(p[0] for p in bar) + 0.2
    by0 = min(p[1] for p in bar) - 0.2
    rebate = [(bx0, by0), (bx1, by0), (bx1, H + 0.2), (bx0, H + 0.2)]
    slab = B.wedge(rebate, front, rear, 0.0, H)
    below = B.wedge(rebate, front - P["bar_t"], rear - P["bar_t"], 0.0, H)
    B.combine_cut(slab, below, keep=False)
    v0 = B.vol(body)
    B.combine_cut(body, slab, keep=False)
    print("bar rebate removed", round(v0 - B.vol(body), 1))

    # F1-8X paddles: left/right shelves in the TOP well. Plate top is against
    # the bezel underside (typing - ceil); paddle top is plate_t under that.
    # Build a wedge up to that plane, then cut away everything below the split
    # so the shelf lives only in TOP.
    pt = P["plate_t"] + 0.2
    pad_f = front - P["ceil"] - pt
    pad_r = rear - P["ceil"] - pt
    for i, poly in enumerate(L["paddle_outlines"]()):
        shelf = B.wedge(poly, pad_f, pad_r, 0.0, H)
        B.cut_below_plane(shelf, split, split_r, 0.0, H)
        v0 = B.vol(body)
        B.combine_join(body, shelf, keep=False)
        print("paddle", i, "added", round(B.vol(body) - v0, 1))

    # M3 clearance through TOP.
    for i, (sx, sy) in enumerate(L["screws"]()):
        v0 = B.vol(body)
        B.cut(B.sketch(L["screw_outline"](sx, sy)), body, rear + 1.0)
        print("screw", i, "at", round(sx, 1), round(sy, 1),
              "removed", round(v0 - B.vol(body), 2))

    # Clamp to the TOP slab: split plane .. typing plane. Leftover paddle
    # extrusions (YZ cuts miss a body that does not start at X=0) get trimmed.
    v0 = B.vol(body)
    B.cut_below_plane(body, split, split_r, 0.0, H)
    B.cut_above_plane(body, front, rear, 0.0, H)
    print("TOP clamp removed", round(v0 - B.vol(body), 1))

    body = B.keep_largest()
    print("TOP bbox mm", B.bbox_mm(body))
    print("TOP vol", round(B.vol(body), 1), "faces", body.faces.count,
          "bodies", des.rootComponent.bRepBodies.count)
    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "TOP.step")
    stl = os.path.join(OUT, "TOP.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

# -*- coding: utf-8 -*-
"""Build the WKL ANSI plate in Fusion: layout-XY rectangle, 14x14 switch cuts.

Native sketch circles over-cut in this Fusion build; squares do not.
"""
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

    KEYS = L["KEYS"]
    PLATE_X0, PLATE_X1 = L["P"]["plate_x"]
    PLATE_Y0, PLATE_Y1 = L["P"]["plate_y"]
    T = L["P"]["plate_t"]
    SIDE = L["P"]["switch_side"]

    keys = list(L["PLATE_KEYS"])
    outline = [(PLATE_X0, PLATE_Y0), (PLATE_X1, PLATE_Y0),
               (PLATE_X1, PLATE_Y1), (PLATE_X0, PLATE_Y1)]
    expect_blank = abs(loop_area(outline)) * T
    hole_a = SIDE * SIDE * T

    app = adsk.core.Application.get()
    for d in list(app.documents):
        try:
            d.close(False)
        except Exception:
            pass

    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "PLATE"
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    B = Builder(doc, des)
    body = B.extrude_new(B.sketch(outline), T)
    print("blank", round(body.volume * 1000, 1), "expect", round(expect_blank, 1),
          "keys", len(keys), "/", len(KEYS))

    removed = 0.0
    bad = 0
    for i, k in enumerate(keys):
        cx = (k["x0"] + k["x1"]) / 2.0
        cy = (k["y0"] + k["y1"]) / 2.0
        h = SIDE / 2.0
        sq = [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h)]
        v0 = body.volume * 1000
        B.cut(B.sketch(sq), body, T)
        dvol = v0 - body.volume * 1000
        removed += dvol
        if abs(dvol - hole_a) > 2.0:
            bad += 1
            print("  hole", i, "row", k["row"], "w", k["w"],
                  "at", round(cx, 1), round(cy, 1), "removed", round(dvol, 2),
                  "expect", round(hole_a, 2))
        if (i + 1) % 15 == 0:
            print("  ...", i + 1, "/", len(keys), "vol", round(body.volume * 1000, 1))

    # Cherry PCB-mount stabs: 6.75 x 14 slot, same as Dalco ANSI plate.
    # Overlaps the 14x14 switch hole so extra volume is just the two side ears.
    nstab = 0
    for k in keys:
        for (sx, sy) in L["stab_holes"](k):
            sq = [(sx - 3.375, sy - 7.0), (sx + 3.375, sy - 7.0),
                  (sx + 3.375, sy + 7.0), (sx - 3.375, sy + 7.0)]
            v0 = body.volume * 1000
            B.cut(B.sketch(sq), body, T)
            dvol = v0 - body.volume * 1000
            nstab += 1
            print("  stab", nstab, "at", round(sx, 1), round(sy, 1),
                  "removed", round(dvol, 2))
    print("stabs", nstab)

    bb = body.boundingBox
    print("PLATE bbox mm",
          [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                      bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])
    print("PLATE vol", round(body.volume * 1000, 1),
          "removed", round(removed, 1), "expect_removed", round(hole_a * len(keys), 1),
          "bad_holes", bad)

    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "PLATE.step")
    stl = os.path.join(OUT, "PLATE.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

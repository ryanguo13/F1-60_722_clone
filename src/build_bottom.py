# -*- coding: utf-8 -*-
"""Build the BOTTOM case: rectangular shell, cavity, weight well, insert bores.

Rounded outer corners and the 7.22 deg wedge come later; this pass is a
printable tray that already matches Dalco/F2-60 XY and the JLC M3 insert
scheme (bore 3.6 x 6, 14 mm pad).
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

    W, H = L["W"], L["H"]
    P = L["P"]
    wall = P["side_wall"]
    T = abs(P["deck"])                 # 16 mm tray
    floor_keep = abs(P["floor"])       # cavity depth 10.5 -> 5.5 mm floor
    cavity_h = T - (T - floor_keep)    # 10.5
    # wait: deck=-16, floor=-10.5 so from top (z=0) tray is 16 mm, cavity 10.5,
    # remaining floor 5.5. Weight well keeps 1.2 mm of that floor.
    cavity_h = abs(P["floor"])         # 10.5
    well_h = cavity_h - P["weight_floor"]  # 9.3
    insert_d = P["insert_d"]
    insert_h = P["insert_len"]
    boss = P["boss"]

    outer = [(0, 0), (W, 0), (W, H), (0, H)]
    inner = [(wall, wall), (W - wall, wall), (W - wall, H - wall), (wall, H - wall)]
    wx0, wy0, wx1, wy1 = P["weight"]
    well = [(wx0, wy0), (wx1, wy0), (wx1, wy1), (wx0, wy1)]

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

    body = B.extrude_new(B.sketch(outer), T)
    print("blank", round(body.volume * 1000, 1), "expect", round(abs(loop_area(outer)) * T, 1))

    v0 = body.volume * 1000
    B.cut(B.sketch(inner), body, cavity_h)
    print("cavity removed", round(v0 - body.volume * 1000, 1),
          "expect", round(abs(loop_area(inner)) * cavity_h, 1))

    # Weight well: cut from the BOTTOM face upward so it only eats the remaining
    # floor (5.5 mm), leaving weight_floor = 1.2 mm. Sketch is still on z=0;
    # extrude the full tray height minus 1.2 mm.
    well_from_top = T - P["weight_floor"]
    v0 = body.volume * 1000
    B.cut(B.sketch(well), body, well_from_top)
    print("well removed", round(v0 - body.volume * 1000, 1),
          "expect ~", round(abs(loop_area(well)) * (T - cavity_h - P["weight_floor"]), 1),
          "(floor leftover)")

    # uDB window in the rear wall (through)
    db = L["db_outline"]()
    v0 = body.volume * 1000
    B.cut(B.sketch(db), body, T)
    print("udb window removed", round(v0 - body.volume * 1000, 1), "pts", len(db))

    # M3 insert bores at the four screw bosses. Cut from the floor up so the
    # remaining wall around each hole is the 8 mm boss left in the cavity.
    for i, (sx, sy) in enumerate(L["screws"]()):
        r = insert_d / 2.0
        hole = [(sx - r, sy - r), (sx + r, sy - r), (sx + r, sy + r), (sx - r, sy + r)]
        v0 = body.volume * 1000
        B.cut(B.sketch(hole), body, T)   # through for v1; heat-set from the bottom
        print("insert", i, "at", round(sx, 1), round(sy, 1),
              "removed", round(v0 - body.volume * 1000, 2))

    # F1-8X 722 square feet: 10 x 8 mm pads, glued. Fusion can only extrude
    # from the top sketch, so a true underside pocket needs a reverse
    # solid that this kernel will not join at the right height. Mark the
    # pad locations with a 0.8 mm recess from the TOP of the remaining
    # floor (cut depth = cavity_h + recess). The glued pad still sits on
    # the underside; the recess is a locating pocket you can see/feel
    # when flipping the shell. Corners are outside the weight well.
    recess = P["foot_recess"]
    for i, (cx, cy) in enumerate(L["feet"]()):
        poly = L["foot_outline"](cx, cy)
        v0 = body.volume * 1000
        B.cut(B.sketch(poly), body, cavity_h + recess)
        print("foot", i, "at", round(cx, 1), round(cy, 1),
              "removed", round(v0 - body.volume * 1000, 2),
              "expect", round(P["foot_w"] * P["foot_h"] * recess, 2))

    bb = body.boundingBox
    print("BOTTOM bbox mm",
          [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                      bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])
    print("BOTTOM vol", round(body.volume * 1000, 1))
    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "BOTTOM.step")
    stl = os.path.join(OUT, "BOTTOM.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

# -*- coding: utf-8 -*-
"""Build the TOP case: rectangular bezel, switch pocket, uDB window, M3 holes.

Printable v1: 9 mm tray, 3 mm walls, 0.6 mm ceiling over the switch area,
through-holes for the four M3 screws and the uDB window.
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
    T = abs(P["lip"])                  # 9 mm
    pocket_h = T - 0.6                 # leave 0.6 mm ceiling
    px0, px1 = P["plate_x"]
    py0, py1 = P["plate_y"]
    # Switch opening stays inside the inner well so it cannot eat the walls.
    band = 1.5
    ix0, iy0, ix1, iy1 = wall, wall, W - wall, H - wall
    pocket = [(max(ix0 + band, px0), max(iy0 + band, py0)),
              (min(ix1 - band, px1), max(iy0 + band, py0)),
              (min(ix1 - band, px1), min(iy1 - band, py1)),
              (max(ix0 + band, px0), min(iy1 - band, py1))]
    outer = [(0, 0), (W, 0), (W, H), (0, H)]
    inner = [(wall, wall), (W - wall, wall), (W - wall, H - wall), (wall, H - wall)]

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
    body = B.extrude_new(B.sketch(outer), T)
    print("blank", round(body.volume * 1000, 1), "expect", round(abs(loop_area(outer)) * T, 1))

    v0 = body.volume * 1000
    B.cut(B.sketch(inner), body, pocket_h)
    print("inner well removed", round(v0 - body.volume * 1000, 1),
          "expect", round(abs(loop_area(inner)) * pocket_h, 1))

    # Ceiling opening over the switches: only the remaining 0.6 mm skin.
    # Same trick as the bottom weight well — cut the full height so the
    # already-empty well is a no-op and the 0.6 mm roof goes away.
    v0 = body.volume * 1000
    B.cut(B.sketch(pocket), body, T)
    print("switch pocket removed", round(v0 - body.volume * 1000, 1),
          "expect", round(abs(loop_area(pocket)) * 0.6, 1), "(ceiling only)")

    # uDB window through the rear wall, not through the inner well.
    # Place it on the rear wall strip: y in [H-wall, H], x around DB_CX.
    dbw, dbh = P["db_w"] + 0.6, min(P["db_h"] + 0.6, wall - 0.2)
    dbx0 = L["DB_CX"] - dbw / 2.0
    dby0 = H - wall
    db_wall = [(dbx0, dby0), (dbx0 + dbw, dby0), (dbx0 + dbw, H), (dbx0, H)]
    v0 = body.volume * 1000
    B.cut(B.sketch(db_wall), body, T)
    print("udb rear-wall window removed", round(v0 - body.volume * 1000, 1),
          "expect", round(dbw * wall * T, 1))

    # Accent-bar rebate: 3 mm deep into the TOP back edge, same XY as the bar
    # plus 0.2 mm clearance so the printed bar drops in.
    bar = L["bar_outline"]()
    # expand 0.2 mm
    bx0 = min(p[0] for p in bar) - 0.2
    bx1 = max(p[0] for p in bar) + 0.2
    by0 = min(p[1] for p in bar) - 0.2
    by1 = H
    rebate = [(bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)]
    v0 = body.volume * 1000
    B.cut(B.sketch(rebate), body, P["bar_t"])
    print("bar rebate removed", round(v0 - body.volume * 1000, 1))

    for i, (sx, sy) in enumerate(L["screws"]()):
        r = P["screw_d"] / 2.0
        hole = [(sx - r, sy - r), (sx + r, sy - r), (sx + r, sy + r), (sx - r, sy + r)]
        v0 = body.volume * 1000
        B.cut(B.sketch(hole), body, T)
        print("screw", i, "at", round(sx, 1), round(sy, 1),
              "removed", round(v0 - body.volume * 1000, 2))

    bb = body.boundingBox
    print("TOP bbox mm",
          [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                      bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])
    print("TOP vol", round(body.volume * 1000, 1))
    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "TOP.step")
    stl = os.path.join(OUT, "TOP.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

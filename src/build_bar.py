# -*- coding: utf-8 -*-
"""Rear accent bar (横条): F1-8X style, no Geon badge.

Prints as a 3 mm thick strip, 8 mm front-to-back, full case width minus
1.5 mm per side. Friction-fits a matching rebate on the TOP back edge.
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
    P = L["P"]
    poly = L["bar_outline"]()
    T = P["bar_t"]
    app = adsk.core.Application.get()
    for d in list(app.documents):
        try:
            d.close(False)
        except Exception:
            pass
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name = "BAR"
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    B = Builder(doc, des)
    body = B.extrude_new(B.sketch(poly), T)
    print("BAR vol", round(body.volume * 1000, 1),
          "expect", round(abs(loop_area(poly)) * T, 1))
    bb = body.boundingBox
    print("BAR bbox mm",
          [round(v * 10, 2) for v in (bb.minPoint.x, bb.minPoint.y, bb.minPoint.z,
                                      bb.maxPoint.x, bb.maxPoint.y, bb.maxPoint.z)])
    os.makedirs(OUT, exist_ok=True)
    exp = des.exportManager
    step = os.path.join(OUT, "BAR.step")
    stl = os.path.join(OUT, "BAR.stl")
    exp.execute(exp.createSTEPExportOptions(step))
    exp.execute(exp.createSTLExportOptions(body, stl))
    print("exported", step, stl)

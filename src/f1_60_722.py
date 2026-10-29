# -*- coding: utf-8 -*-
"""Layout generator for the F1-60 722 clone (offset-agnostic JSON).

The printable case is one prism: a 2D plan (layout XY) extruded, then sliced
by horizontal cuts. This module owns the plan: every outline, pocket, boss
and hole of the three parts, in *layout space*:

    x: 0 .. W      left -> right of the finished keyboard
    y: 0 .. H      front lip -> back edge  (the back row faces the case's
                   printed back edge)
    z: plate top = 0, +up

`plan()` returns, per part, a list of polygon dicts
{"z": level, "loops": [[(x, y), ...], ...]}; `z` is the layout height of the
face that polygon makes and the loops are layout mm. A polygon with two
loops (outer rim, inner hole) is a ring.

Run standalone (`python src/f1_60_722.py`) to dump out/plan_<part>.json.
"""
import json
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")

U = 19.05
W, H = 284.5, 94.5                 # footprint: 4 rows x 14.25 u

P = dict(
    r_side=6.0, r_back=8.0, angle=7.22,
    side_wall=3.0, front_wall=3.0, rear_wall=3.0,
    plate_t=1.5,
    pcb_top=-5.0, pcb_bot=-6.6,
    seat=-2.0, band=-5.0, pocket=-0.6, lip=-9.0,
    floor=-10.5, deck=-16.0, weight_floor=1.2,
    plate_x=(5.825, 278.675), plate_y=(2.82, 91.68),
    switch_side=14.0, hook_over=22.0,
    db_w=18.0, db_h=16.5,
    screw_inset=6.0, screw_y_front=6.0, screw_y_back=14.25,
    boss=8.0, insert_d=3.6, insert_len=6.0, screw_d=3.4,
    weight=(11.5, 11.5, 273.0, 76.5), weight_r=3.0,
)
ROW_Y = [13.8455, 32.8955, 51.9455, 71.0055, 85.2155]
KX0 = (W - 15 * U) / 2.0


# ---------------------------------------------------------------------------
# 2D helpers
# ---------------------------------------------------------------------------
def poly_ul(x0, x1, y0, y1, r, side, n=6):
    """Rectangle whose two corners toward `side` are rounded (polygonal arc)."""
    def arc(cx, cy, a0):
        return [(cx + r * math.cos(a0 + (math.pi / 2) * i / n),
                 cy + r * math.sin(a0 + (math.pi / 2) * i / n)) for i in range(n + 1)]
    if side == "front":
        return ([(x0, y1), (x0, y0 + r)] + arc(x0 + r, y0 + r, math.pi) +
                arc(x1 - r, y0 + r, 1.5 * math.pi) + [(x1, y1)])
    return ([(x0, y0), (x0, y1 - r)] + arc(x0 + r, y1 - r, math.pi) +
            arc(x1 - r, y1 - r, 1.5 * math.pi) + [(x1, y0)])


def poly_rrect(x0, y0, x1, y1, r):
    """Rectangle rounded on all four corners."""
    r = max(0.0, min(r, (x1 - x0) / 2.0 - 0.001, (y1 - y0) / 2.0 - 0.001))
    if r <= 0.01:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    k = 0.55 * r
    return [
        (x0 + r, y0), (x1 - r, y0), (x1 - r + k, y0), (x1, y0 + r - k), (x1, y0 + r),
        (x1, y1 - r), (x1, y1 - r + k), (x1 - r + k, y1), (x1 - r, y1),
        (x0 + r, y1), (x0 + r - k, y1), (x0, y1 - r + k), (x0, y1 - r),
        (x0, y0 + r), (x0, y0 + r - k), (x0 + r - k, y0), (x0 + r, y0)]


def poly_circle(cx, cy, dia, n=40):
    r = dia / 2.0
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]


def poly_points(pts, eps=0.01):
    out = []
    for p in pts:
        if out and abs(out[-1][0] - p[0]) < eps and abs(out[-1][1] - p[1]) < eps:
            continue
        out.append(p)
    while len(out) > 2 and abs(out[0][0] - out[-1][0]) < eps and abs(out[0][1] - out[-1][1]) < eps:
        out.pop()
    return out


def loop_area(loop):
    a = 0.0
    for i in range(len(loop)):
        x0, y0 = loop[i - 1]
        x1, y1 = loop[i]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


# ---------------------------------------------------------------------------
# keys (WKL ANSI)
# ---------------------------------------------------------------------------
def build_keys():
    rows = [
        [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1),
         (10, 1), (11, 1), (12, 2)],
        [(0, 1.5)] + [(1.5, 1)] * 10 + [(11.5, 1), (12.5, 1), (13.5, 1.5), (15.0, 1.5), (16.5, 1.5)],
        [(0, 1.75)] + [(1.75, 1)] * 9 + [(10.75, 1), (11.75, 1), (12.75, 2.25), (15.0, 1.5), (16.5, 1.5)],
        [(0, 2.25)] + [(2.25, 1)] * 7 + [(9.25, 1), (10.25, 1), (11.25, 1), (12.25, 1.75),
                                       (14.0, 2.75), (16.75, 1.25)],
        [(0, 1.25), (1.25, 1.25), (2.5, 1.25), (3.75, 6.25), (10.0, 1.25), (11.25, 1.25),
         (12.5, 1.25), (13.75, 1.25)],
    ]
    keys = []
    for r, row in enumerate(rows):
        x_left = KX0 - 0.125 * U + (1.25 * U if r in (1, 2, 3) else 0.0)
        for off, w in row:
            x0 = x_left + off * U
            yc = ROW_Y[r]
            keys.append(dict(x0=x0, x1=x0 + w * U, y0=yc - U / 2, y1=yc + U / 2, w=w, row=r))
    return keys


KEYS = build_keys()
STABS = [(1, 2.25, 2.0), (2, 2.25, 2.0), (3, 2.75, 2.0), (4, 6.25, 6.25)]
SPACE = [k for k in KEYS if k["row"] == 4 and abs(k["w"] - 6.25) < 1e-6][0]
DB_CX = (SPACE["x0"] + SPACE["x1"]) / 2
SW_X0 = min(k["x0"] for k in KEYS) - P["hook_over"]
SW_X1 = max(k["x1"] for k in KEYS) + P["hook_over"]
SW_Y0 = min(k["y0"] for k in KEYS)
SW_Y1 = max(k["y1"] for k in KEYS)
FRONT_ROW_Y1 = max(k["y1"] for k in KEYS if k["row"] == 1)


def stab_holes(k):
    out = []
    for (row, kw, wire) in STABS:
        if k["row"] != row or abs(k["w"] - kw) > 1e-6:
            continue
        kc = (k["x0"] + k["x1"]) / 2 + (0.2 if row == 3 else 0.0)
        half = (wire - 1) * U / 2
        out += [(kc - half, ROW_Y[row]), (kc + half, ROW_Y[row])]
    return out


# ---------------------------------------------------------------------------
# case outline
# ---------------------------------------------------------------------------
def outline():
    yr = H - P["rear_wall"]
    return [poly_ul(0, W, yr, H, P["r_back"], "back"),
            poly_ul(0, W, 0, yr, P["r_side"], "front")]


def inner(gap=0.0):
    f = P["front_wall"] + gap
    s = P["side_wall"] + gap
    r = P["rear_wall"] + gap
    rs = max(0.5, P["r_side"] - max(s, f))
    rb = max(0.5, P["r_back"] - max(s, r))
    return [poly_ul(s, W - s, H - r, H, rb, "back"),
            poly_ul(s, W - s, f, H - r, rs, "front")]


def top_edge(x):
    r = P["r_back"]
    if x < r:
        return H - r + math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > W - r:
        return H - r + math.sqrt(max(0.0, r * r - (x - (W - r)) ** 2))
    return H


def front_edge(x):
    r = P["r_side"]
    if x < r:
        return r - math.sqrt(max(0.0, r * r - (r - x) ** 2))
    if x > W - r:
        return r - math.sqrt(max(0.0, r * r - (x - (W - r)) ** 2))
    return 0.0


def screws():
    out = []
    for x in (P["screw_inset"], W - P["screw_inset"]):
        out.append((x, front_edge(x) + P["screw_y_front"]))
        out.append((x, top_edge(x) - P["screw_y_back"]))
    return out


def db_centre_y():
    return (H + P["rear_wall"] + FRONT_ROW_Y1 + 1.0) / 2.0


def db_outline():
    y = db_centre_y()
    return poly_rrect(DB_CX - P["db_w"] / 2 - 0.3, y - P["db_h"] / 2 - 0.3,
                      DB_CX + P["db_w"] / 2 + 0.3, y + P["db_h"] / 2 + 0.3, 0.8)


def weight_outline():
    x0, y0, x1, y1 = P["weight"]
    return poly_rrect(x0, y0, x1, y1, P["weight_r"])


# ---------------------------------------------------------------------------
# part plans: list of {"z": face level, "loops": [...], "op": "solid|cavity"}
# ---------------------------------------------------------------------------
def bottom_plan():
    return dict(name="BOTTOM", top=0.0, bottom=P["deck"])


def top_plan():
    return dict(name="TOP", top=0.0, bottom=P["lip"])


def plate_plan():
    return dict(name="PLATE", top=0.0, bottom=-P["plate_t"])


def plan():
    return {"bottom": bottom_plan(), "top": top_plan(), "plate": plate_plan()}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = plan()
    for part, d in p.items():
        print(part, d)
    print("keys", len(KEYS), "screws", [(round(a, 1), round(b, 1)) for a, b in screws()],
          "uDB centre", (round(DB_CX, 2), round(db_centre_y(), 2)))
    print("switch area x %.1f..%.1f y %.1f..%.1f" % (SW_X0, SW_X1, SW_Y0, SW_Y1))

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
# Dalco 959 Mini ANSI plate is exactly 15u wide (285.75 mm). F2-60 case is
# ~299.2 x 117.1 mm (TOP bbox). Match that envelope: 6.72 mm side walls
# around the 15u plate, 3.1 mm extra front/back of the 5u key block.
W, H = 299.19, 117.08
KX0 = 5.095                          # Dalco Esc-row origin (first 1u centre - 0.5u)

P = dict(
    r_side=6.0, r_back=8.0, angle=7.22,
    side_wall=3.0, front_wall=3.0, rear_wall=3.0,
    plate_t=1.5,
    pcb_top=-5.0, pcb_bot=-6.6,
    seat=-2.0, band=-5.0, pocket=-0.6, lip=-9.0,
    floor=-10.5, deck=-16.0, weight_floor=1.2,
    plate_x=(5.094, 290.844),
    plate_y=(-2.665, 108.186),
    switch_side=14.0, hook_over=22.0,
    db_w=18.0, db_h=16.5,
    screw_inset=6.0, screw_y_front=6.0, screw_y_back=14.25,
    boss=8.0, insert_d=3.6, insert_len=6.0, screw_d=3.4,
    weight=(13.0, 13.0, 286.0, 90.0), weight_r=3.0,
)
# Layout Y is front lip -> back. Dalco plate Y ran the other way (Esc at
# y=90.86); we keep front-to-back order and place Esc at 14.66 like a GH60.
ROW_Y = [14.66, 33.71, 52.76, 71.81, 90.86]


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
    # Standard 60% WKL ANSI. Offsets are from the left of a 15u grid
    # (KX0 is the grid origin). No extra blocker keys.
    rows = [
        [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1), (8, 1), (9, 1),
         (10, 1), (11, 1), (12, 1), (13, 2)],
        [(0, 1.5)] + [(1.5 + i, 1) for i in range(12)] + [(13.5, 1.5)],
        [(0, 1.75)] + [(1.75 + i, 1) for i in range(11)] + [(12.75, 2.25)],
        [(0, 2.25)] + [(2.25 + i, 1) for i in range(10)] + [(12.25, 1.75), (14.0, 1)],
        [(0, 1.25), (1.25, 1.25), (2.5, 1.25), (3.75, 6.25), (10.0, 1.25), (11.25, 1.25),
         (12.5, 1.25), (13.75, 1.25)],
    ]
    keys = []
    for r, row in enumerate(rows):
        for off, w in row:
            x0 = KX0 + off * U
            yc = ROW_Y[r]
            keys.append(dict(x0=x0, x1=x0 + w * U, y0=yc - U / 2, y1=yc + U / 2, w=w, row=r))
    return keys


KEYS = build_keys()
# Cherry stabs: L-Shift 2.25 (row 3), Enter 2.25 (row 2), space 6.25 (row 4).
STABS = [(3, 2.25, 2.0), (2, 2.25, 2.0), (4, 6.25, 6.25)]
SPACE = [k for k in KEYS if k["row"] == 4 and abs(k["w"] - 6.25) < 1e-6][0]
DB_CX = (SPACE["x0"] + SPACE["x1"]) / 2
PLATE_KEYS = list(KEYS)
# Keep the Dalco ANSI plate envelope (do not shrink to the key cluster).
P["plate_x"] = (5.094, 290.844)
P["plate_y"] = (-2.665, 108.186)
SW_X0 = min(k["x0"] for k in PLATE_KEYS) - P["hook_over"]
SW_X1 = max(k["x1"] for k in PLATE_KEYS) + P["hook_over"]
SW_Y0 = min(k["y0"] for k in PLATE_KEYS)
SW_Y1 = max(k["y1"] for k in PLATE_KEYS)
FRONT_ROW_Y1 = max(k["y1"] for k in PLATE_KEYS if k["row"] == 1)


def stab_holes(k):
    """Cherry PCB-mount stab centres. Distances match Dalco ANSI plate."""
    out = []
    # wire span between stab centres, mm (not unit widths)
    span = {2.0: 23.8, 6.25: 100.0, 2.25: 23.8, 2.75: 23.8}
    for (row, kw, wire) in STABS:
        if k["row"] != row or abs(k["w"] - kw) > 1e-6:
            continue
        kc = (k["x0"] + k["x1"]) / 2.0
        half = span.get(wire, (wire - 1) * U) / 2.0
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
    print("keys", len(KEYS), "on plate", len(PLATE_KEYS),
          "screws", [(round(a, 1), round(b, 1)) for a, b in screws()],
          "uDB centre", (round(DB_CX, 2), round(db_centre_y(), 2)))
    print("plate x %.2f..%.2f y %.2f..%.2f" % (P["plate_x"] + P["plate_y"]))
    print("switch area x %.1f..%.1f y %.1f..%.1f" % (SW_X0, SW_X1, SW_Y0, SW_Y1))

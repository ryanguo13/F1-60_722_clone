# -*- coding: utf-8 -*-
"""Layout for the F1-60 722 clone (WKL, F2-60 XY, 7.22° wedge).

Layout space:
    x: 0 .. W      left -> right
    y: 0 .. H      front lip -> back edge
    z: 0 = desk, +up
    typing plane: z(y) = front_h + y * tan(7.22°)
    split plane:  z(y) = split_h + y * tan(7.22°)   (TOP is 8 mm along Z)

Run standalone to dump key numbers.
"""
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")

U = 19.05
# W matches F2-60 (thin 3 mm sides). H is grown vs F2-60 117.08 so the
# 14x14 heat-set pads live in the front/back lips and miss the plate.
W, H = 299.20, 129.20
ANGLE_DEG = 7.22
TAN = math.tan(ANGLE_DEG * math.pi / 180.0)

PLATE_W = 15 * U                 # 285.75
PLATE_H = 5 * U + 0.85           # 96.10 (0.425 mm margin each side of 5u)
PLATE_X0 = (W - PLATE_W) / 2.0   # 6.725
PLATE_Y0 = (H - PLATE_H) / 2.0   # 16.55
KX0 = PLATE_X0
ROW_Y = [PLATE_Y0 + 0.425 + U / 2.0 + i * U for i in range(5)]

P = dict(
    angle=ANGLE_DEG, tan=TAN,
    r_side=3.0, r_inner=1.0,
    # Sides stay thin (F1-8X 722 side bezel is 4.2). Front/back carry the
    # 14x14 heat-set pads and read as the wider lips.
    side_wall=3.0, front_wall=16.0, rear_wall=16.0,
    plate_t=1.5, plate_r=2.4,
    plate_x=(PLATE_X0, PLATE_X0 + PLATE_W),
    plate_y=(PLATE_Y0, PLATE_Y0 + PLATE_H),
    front_h=16.0,          # desk -> typing at y=0
    split_h=8.0,           # desk -> split at y=0 (TOP 8 mm along Z)
    ceil=0.6,              # TOP roof over the switch opening, along Z
    floor=2.0,             # BOTTOM remaining floor (weight well + feet)
    switch_side=14.0,
    paddle_w=8.0,          # left/right plate shelf, from inner wall under the plate
    paddle_drop=1.5,       # shelf is this far below typing, along Z
    db_w=18.0, db_h=8.0,   # USB pill through the rear wall
    db_r=2.5,
    # Heat-set nuts sit in the FRONT/BACK walls, not the sides, so the
    # left/right bezel can stay ~3 mm (F1-8X 722 is 4.2 mm). Front/back
    # take the 14x14 pads and read as the wider bezels.
    screw_y=8.0,           # pad centre from front / back outer edge
    screw_x=50.0,          # pad centre from left / right (clear of R3 and USB)
    boss=14.0, insert_d=3.6, insert_len=5.0, screw_d=3.4,
    nut_pad=14.0,
    foot_w=290.0, foot_h=7.0, foot_recess=0.8, foot_y=6.0,
    rear_foot_w=284.0,
    bar_t=3.0, bar_h=8.0, bar_inset=1.5,
    chamfer=1.2,           # 36° front/back top edge, mm along each face
)


def rear_h():
    return P["front_h"] + H * P["tan"]


def split_rear():
    return P["split_h"] + H * P["tan"]


def z_typing(y):
    return P["front_h"] + y * P["tan"]


def z_split(y):
    return P["split_h"] + y * P["tan"]


# ---------------------------------------------------------------------------
# 2D helpers
# ---------------------------------------------------------------------------
def poly_rrect(x0, y0, x1, y1, r, n=6):
    """Rectangle rounded on all four corners with circular arcs (CCW)."""
    r = max(0.0, min(r, (x1 - x0) / 2.0 - 0.001, (y1 - y0) / 2.0 - 0.001))
    if r <= 0.05:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    def arc(cx, cy, a0, a1):
        return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
                 cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

    return (arc(x0 + r, y0 + r, math.pi, 1.5 * math.pi) +
            arc(x1 - r, y0 + r, 1.5 * math.pi, 2.0 * math.pi) +
            arc(x1 - r, y1 - r, 0.0, 0.5 * math.pi) +
            arc(x0 + r, y1 - r, 0.5 * math.pi, math.pi))


def poly_circle(cx, cy, dia, n=24):
    r = dia / 2.0
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def loop_area(loop):
    a = 0.0
    for i in range(len(loop)):
        x0, y0 = loop[i - 1]
        x1, y1 = loop[i]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def outer_outline():
    return poly_rrect(0.0, 0.0, W, H, P["r_side"])


def inner_outline(gap=0.0):
    s = P["side_wall"] + gap
    f = P["front_wall"] + gap
    r = P["rear_wall"] + gap
    ri = max(0.6, P["r_inner"] - gap)
    return poly_rrect(s, f, W - s, H - r, ri)


# ---------------------------------------------------------------------------
# keys (WKL ANSI)
# ---------------------------------------------------------------------------
def build_keys():
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
PLATE_KEYS = list(KEYS)
STABS = [(3, 2.25, 2.0), (2, 2.25, 2.0), (4, 6.25, 6.25)]
SPACE = [k for k in KEYS if k["row"] == 4 and abs(k["w"] - 6.25) < 1e-6][0]
DB_CX = W / 2.0          # F2-60 USB is on the case centreline, not the spacebar


def stab_holes(k):
    """Cherry PCB-mount stab centres. Distances match Dalco ANSI plate."""
    out = []
    span = {2.0: 23.8, 6.25: 100.0, 2.25: 23.8, 2.75: 23.8}
    for (row, kw, wire) in STABS:
        if k["row"] != row or abs(k["w"] - kw) > 1e-6:
            continue
        kc = (k["x0"] + k["x1"]) / 2.0
        half = span.get(wire, (wire - 1) * U) / 2.0
        out += [(kc - half, ROW_Y[row]), (kc + half, ROW_Y[row])]
    return out


def screws():
    """2 on the front lip, 2 on the back edge. Nothing in the side walls."""
    yf = P["screw_y"]
    yb = H - P["screw_y"]
    xl = P["screw_x"]
    xr = W - P["screw_x"]
    return [(xl, yf), (xr, yf), (xl, yb), (xr, yb)]


def plate_outline():
    x0, x1 = P["plate_x"]
    y0, y1 = P["plate_y"]
    return poly_rrect(x0, y0, x1, y1, P["plate_r"])


def switch_window():
    """Ceiling opening: plate inset 1.5 mm so the bezel covers the plate edge."""
    x0, x1 = P["plate_x"]
    y0, y1 = P["plate_y"]
    b = 1.5
    return poly_rrect(x0 + b, y0 + b, x1 - b, y1 - b, max(0.6, P["plate_r"] - b))


def usb_outline():
    w, h, r = P["db_w"], P["db_h"], P["db_r"]
    x0 = DB_CX - w / 2.0
    y0 = H - P["rear_wall"] - 0.4
    y1 = H + 0.2
    return poly_rrect(x0, y0, x0 + w, y1, min(r, (y1 - y0) / 2.0 - 0.05))


def bar_outline():
    x0 = P["bar_inset"]
    x1 = W - P["bar_inset"]
    y0 = H - P["bar_h"]
    return [(x0, y0), (x1, y0), (x1, H), (x0, H)]


def paddle_outlines():
    """Left / right plate shelves in XY (under the plate, from the inner wall)."""
    y0, y1 = P["plate_y"]
    w = P["paddle_w"]
    s = P["side_wall"]
    left = [(s, y0), (s + w, y0), (s + w, y1), (s, y1)]
    right = [(W - s - w, y0), (W - s, y0), (W - s, y1), (W - s - w, y1)]
    return left, right


def foot_outlines():
    """Two F2-60-style rubber-strip recesses on the desk face."""
    rec = P["foot_recess"]
    fy = P["foot_y"]
    fh = P["foot_h"]
    fw, rw = P["foot_w"], P["rear_foot_w"]
    fx0 = (W - fw) / 2.0
    rx0 = (W - rw) / 2.0
    front = [(fx0, fy), (fx0 + fw, fy), (fx0 + fw, fy + fh), (fx0, fy + fh)]
    back = [(rx0, H - fy - fh), (rx0 + rw, H - fy - fh),
            (rx0 + rw, H - fy), (rx0, H - fy)]
    return front, back


def pad_outline(sx, sy):
    h = P["nut_pad"] / 2.0
    return [(sx - h, sy - h), (sx + h, sy - h), (sx + h, sy + h), (sx - h, sy + h)]


def insert_outline(sx, sy):
    r = P["insert_d"] / 2.0
    return [(sx - r, sy - r), (sx + r, sy - r), (sx + r, sy + r), (sx - r, sy + r)]


def screw_outline(sx, sy):
    r = P["screw_d"] / 2.0
    return [(sx - r, sy - r), (sx + r, sy - r), (sx + r, sy + r), (sx - r, sy + r)]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("W H", W, H)
    print("typing front/rear", P["front_h"], round(rear_h(), 3))
    print("split  front/rear", P["split_h"], round(split_rear(), 3))
    print("plate", [round(v, 3) for v in P["plate_x"] + P["plate_y"]],
          "size", round(PLATE_W, 3), round(PLATE_H, 3))
    print("ROW_Y", [round(y, 3) for y in ROW_Y])
    print("keys", len(KEYS), "screws", [(round(a, 1), round(b, 1)) for a, b in screws()])
    print("uDB cx", round(DB_CX, 2), "space cx", round((SPACE["x0"] + SPACE["x1"]) / 2, 2))
    print("outer area", round(loop_area(outer_outline()), 1),
          "inner area", round(loop_area(inner_outline()), 1))

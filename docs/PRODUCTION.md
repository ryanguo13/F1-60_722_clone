# F1-60 722 clone — checkpoint

WKL 60% printable tray set for JLCPCB FDM. Not yet the finished 7.22°
wedge / rounded F1-8X silhouette.

## What is in `out/`

| File | Size (mm) | Notes |
| --- | --- | --- |
| `PLATE.stl` | 285.75 × 110.85 × 1.5 | Dalco 959 Mini ANSI envelope, 62 × 14×14 switch holes, 6 Cherry stab slots (L-Shift, Enter, 6.25u space) |
| `BOTTOM.stl` | 299.19 × 117.08 × 16 | Inner well, weight well (1.2 mm floor left), ai03 UDB-C rear window, 4 × 14×14 M3 heat-set pads (嘉立创 `M3*4*3`, bore Ø3.6 × 5.0), 4 × 10×8 mm feet recesses |
| `TOP.stl` | 299.19 × 117.08 × 9 | 3 mm walls, switch ceiling opening, rear-wall UDB window, accent-bar rebate |
| `BAR.stl` | 296.19 × 8 × 3 | Rear accent bar, no Geon logo, friction-fits the TOP rebate |

PCB fit: waffling60-DB / any GH60-class 60% with ai03 Unified Daughterboard C (18 × 16.5, M2 14 × 12.5). Geon DB hole pattern is **not** copied.

## Heat-set (from X4)

- Nut: 嘉立创 `M3*4*3` (Ø4 × L3)
- Printed bore: Ø3.6 × 5.0
- Pad: 14 × 14, wall around hole (14 − 3.6)/2 = 5.2 ≥ 3.0
- Screw: M3×6 pan head, clearance Ø3.4

Insert from the **underside** of BOTTOM. TOP is clearance only.

## Still missing vs F1-8X 722

- 7.22° typing wedge (Fusion boolean on a slanted solid is still unreliable)
- Side/front/back rounding (r 6 / r 8)
- F1-8X “paddle” plate hooks on the inner long edges
- True underside feet pockets (current recesses cut from the top of the remaining floor)
- M2.5 top/bottom pair (3D-print case keeps heat-set M3)

## Print

PLA/PETG, 0.4 mm nozzle, 0.2 mm layer, 5–6 walls. Orient BOTTOM well-up, TOP bezel-up, PLATE flat, BAR on its 3 mm face. No supports required on these rectangular trays.

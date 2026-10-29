# F1-60 722 Clone

以 [Geonworks F1-8X 722](https://geon.works/products/launcher60-keyboard-case) /
[Launcher 60](https://geon.works/products/launcher60-keyboard-case) 的外形为目标，
配列改成 **60% WKL ANSI** 的 3D 打印键盘外壳复刻。

对照视频：[F1-60 722 HHKB FINAL PROTOTYPE](https://www.youtube.com/watch?v=NqCcKtChTF0)
（视频是 HHKB；本仓库画 WKL）。

- **外壳**：底壳 + 上盖，7.22° 楔形，R3 圆角。不做 Geon 铭牌
- **定位板**：WKL ANSI，1.5 mm，左右桨式托台（前后留空）
- **PCB**：waffling60-DB / 任意 GH60 + ai03 Unified Daughterboard C
- **螺钉**：4 × M3 热熔螺母（嘉立创 `M3*4*3`），前唇 2 + 后沿 2，不进侧壁
- **横条**：后沿摩擦条，无 logo

尺寸推导、分型、热熔取舍都在 [docs/DESIGN.md](docs/DESIGN.md)。
打印与装配在 [docs/PRODUCTION.md](docs/PRODUCTION.md)。

当前外形 **299.20 × 129.20 mm**（宽对齐 F2-60；深比 F2-60 的 117 加长，
好把 14×14 热熔垫完全让开定位板）。侧壁 3 mm，前后壁 16 mm。

## 目录

| 路径 | 说明 |
| --- | --- |
| `src/f1_60_722.py` | 布局与参数 |
| `src/build_top.py` / `build_bottom.py` / `build_plate.py` / `build_bar.py` | Fusion 建模脚本 |
| `src/fusion_lib.py` | XY / YZ 草图、楔形切 |
| `tools/cloud.py` | 把脚本送进本机 Fusion MCP |
| `ref/dalco/` | 959 Mini 工程（CC BY-NC-SA 4.0），外形参考 |
| `ref/waffling60/` | waffling60 DB STEP（CERN-OHL-P v2），PCB 间隙验证 |
| `ref/F2-60_RENDER.stp` / `ref/F1-8X_722_RENDER.stp` | 同系列渲染 STEP |
| `out/` | 导出的 STEP / STL |

## 许可与出处

- 脚本与本仓库原创内容：CC BY-NC-SA 4.0
- `ref/dalco/` 来自 Hand Engineering 959 Mini，**CC BY-NC-SA 4.0**
- `ref/waffling60/` 来自 [4pplet/waffling60](https://github.com/4pplet/waffling60)
- 本复刻与 Geonworks 无关，仅供个人自用。

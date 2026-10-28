# F1-60 722 Clone

以 [Geonworks F1-8X 722](https://geon.works/products/launcher60-keyboard-case) 的
**60% WKL** 版本为目标的 3D 打印键盘外壳复刻。

- **外壳**：底壳 + 上盖两件套，不做 Geon 铭牌
- **定位板**：WKL ANSI，1.5 mm，带"桨式"卡扣（只卡两侧内边，上下留空以兼容PCB）
- **PCB**：waffling60（ai03 统一子板版，`waffling60-DB` / 或 `MXHS-ANSI` 的 a
  io3 子板模式）—— 机内开孔、定位板 M2 孔都按 ai03 Unified Daughterboard
  （UDB-C 系列，18 × 16.5 mm，M2 孔 14 × 12.5 间距）出
- **配重**：不做铜配重，但底壳预留**不锈钢配重槽**，后续可以加
- **螺钉**：M3 热熔螺母方案（嘉立创代嵌），全部从底壳底面拧入

状态：**原型阶段**。尺寸来源、推导都在 [docs/DESIGN.md](docs/DESIGN.md)，
打印与装配说明在 [docs/PRODUCTION.md](docs/PRODUCTION.md)（完成后补）。

## 目录

| 路径 | 说明 |
| --- | --- |
| `src/f1_60_722.py` | Fusion 360 参数化建模脚本（底壳 / 上盖 / 定位板） |
| `tools/cloud.py` | 把脚本送进本机 Fusion MCP 执行（`python tools/cloud.py src/f1_60_722.py`） |
| `tools/extract_waffling.py` | 从 waffling60 钻孔文件提取键位/卫星轴坐标，用于对位 |
| `ref/dalco/` | Hand Engineering 959 Mini 工程文件（CC BY-NC-SA 4.0），外形参考 |
| `ref/waffling60/` | waffling60 DB 版的 STEP / Gerber / 装配图（CERN-OHL-P v2） |
| `Pro60_v5/` | 用户提供的 Pro60 v5 参考文件（本地资料，实物来源） |
| `out/` | 导出的 STEP / STL |

## 许可与出处

- 脚本与本仓库原创内容：CC BY-NC-SA 4.0
- `ref/dalco/` 来自 Hand Engineering 959 Mini 开源工程，**CC BY-NC-SA 4.0**，
  仅作外形/比例参考，不直接分发其几何作为成品。
- `ref/waffling60/` 来自 [4pplet/waffling60](https://github.com/4pplet/waffling60)
  （CERN-OHL-P v2），PCB 相关几何只用于验证间隙。
- 本复刻与 Geonworks 无关，仅供个人自用。

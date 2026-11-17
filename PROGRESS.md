# Coffee Grinder 進度

記錄到 2026-11-17。

## 已完成

- Part 01 上豆倉刀盤組（`part01_upper_carrier`）
- Part 02 追刀外刀盆（`part02_chasing_outer_bowl`，Ø64.20 × 15.90 mm）
- Part 03 主筒（`part03_main_housing`：軸套封閉傳動軸、兩條肋 + 軸套作三點支撐、頂緣 Z=27、卡位對準豆倉）
- Part 04 下刀盤座（`part04_lower_carrier`，對 64 mm 平刀、中井 Ø38.60）
- Part 05 追刀內刀（`part05_inner_chasing_burr`：圖紙 Ø42.75 × 31.50 縮到 Ø37.80 遷就 64 mm 平刀中孔；闊底窄頂，坐喺下刀盤座頂面）
- 64 mm 平刀鋼圈（`top_steel_ring`，Ø64.20 × 8.70 mm）
- 組裝 STEP
  - `assembly_hopper_bowl.step`：豆倉 + 外刀盆 + 上平刀
  - `assembly_grinder.step`：主筒 + 豆倉 + 外刀盆 + 兩片平刀 + 內刀 + 下刀盤座（標籤可逐件開關，無干涉）

## 下一步

- 其餘外殼／傳動／出粉路徑零件
- 需要時再微調內刀同外刀盆嘅咬合間隙

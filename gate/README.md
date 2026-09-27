# 褶量 × 门幅 交叉门禁

一键执行（仓库根目录）：

```bash
python3 gate/run_gate.py
```

流程（期望见 `stages.json`，入口启动时读取）：

1. `baseline` — 定位种子「客厅落地窗」×「遮光1.4m」，干算记下基准 meters/panels；
2. `fullness-2.5` — 经窗户更新（`PUT /api/windows/{id}`）把褶量改为 2.5，干算要求 meters 严格大于基准；
3. `width-2.8` — 经布料更新（`PUT /api/fabrics/{id}`）把门幅改为 2.8，干算要求 panels 严格小于上一阶段且 meters 等于该阶段手算；
4. `restore` — 褶量与门幅写回原值，干算要求 meters/panels 回到基准。

任一阶段失败：打印阶段标签与当次数字，进程码非零。全部通过：进程码 0。
入口默认自起临时后端（独立 DATA_DIR，跑完即焚），不碰开发库，因此可连续重复执行。
打已在运行的服务：`GATE_BASE_URL=http://localhost:9800 python3 gate/run_gate.py`。

文件分工（三者分离）：

| 文件 | 职责 |
| --- | --- |
| `run_gate.py` | 门禁入口：编排阶段、手算对照、临时后端生命周期 |
| `api_client.py` | 请求封装：全部 HTTP 调用（干算 / 查询 / 更新） |
| `stage_report.py` | 阶段报告：记录与打印每阶段标签、数字、判定，给出退出码 |
| `stages.json` | 各阶段变更与期望（供入口读取） |

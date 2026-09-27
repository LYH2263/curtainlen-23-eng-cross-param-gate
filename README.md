# 19-curtainlen（窗帘用布）

Curtainlen — 成品宽×褶倍率 + 上下边折；换算布长米数

## 启动

```bash
docker compose up --build
```

| 入口 | 地址 |
| --- | --- |
| 前端 | http://localhost:4800 |
| API | http://localhost:9800 |

## 主链

窗宽层高+褶量 → 布长 → 窗户示意

## 技术栈

Python 3.12 + FastAPI + SQLite；Vue 3 + Vite + Nginx。

## 门禁（褶量×门幅交叉）

一键执行（自动拉起一次性后端，独立临时数据库，不碰本地数据）：

```bash
python3 gate/run_gate.py
```

也可对已启动的栈执行：`GATE_BASE_URL=http://localhost:9800 python3 gate/run_gate.py`

流程由 `gate/stages.json` 驱动：基准干算 → 褶量改 2.5（meters 严格增大）→ 门幅改 2.8（panels 严格减小且 meters 等于手算）→ 写回原值（回到基准）。任一阶段失败即非零退出并打印阶段标签与当次数字；连续执行两次均应为 0。入口 `gate/run_gate.py`、请求封装 `gate/api_client.py`、阶段报告 `gate/stage_report.py` 三者分离。算料台（Bench 页）仍可手工对照。

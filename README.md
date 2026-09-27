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

## 门禁

```bash
python3 gate/run_gate.py
```

褶量 × 门幅 交叉门禁：基准干算 → 褶量 2.5 → 门幅 2.8 → 写回原值，任一阶段失败进程码非零。详见 `gate/README.md`。

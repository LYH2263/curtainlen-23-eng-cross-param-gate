#!/usr/bin/env python3
"""褶量 × 门幅 交叉门禁入口。

一键执行：python3 gate/run_gate.py
- 默认自起临时后端（独立 DATA_DIR，种子库全新，跑完即焚），不碰开发库、不直接改 sqlite；
- 设 GATE_BASE_URL=http://host:port 可改为打已在运行的服务；
- 设 GATE_STAGES_FILE=path 可替换期望文件（默认 gate/stages.json）。

流程：基准干算 → 褶量改 2.5 → 门幅改 2.8 → 写回原值。
任一阶段失败打印阶段标签与当次数字，并以非零进程码退出。
"""
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from api_client import ApiClient, ApiError
from stage_report import StageReport

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
STAGES_FILE = Path(os.environ.get("GATE_STAGES_FILE", Path(__file__).resolve().parent / "stages.json"))


def hand_meters(window, fabric):
    """手算：独立于 curtain_math 的核算，用于交叉对照。"""
    finished = float(window["width"]) * float(window["fullness"])
    panels = max(1, math.ceil(finished / float(fabric["fabric_width"])))
    cut_h = float(window["height"]) + float(fabric["hem_top"]) + float(fabric["hem_bottom"])
    return panels, round(panels * cut_h, 2)


class EphemeralServer:
    """临时后端：独立 DATA_DIR 起 uvicorn，stop 后连库带目录一起清掉。"""

    def __init__(self):
        self.data_dir = tempfile.mkdtemp(prefix="curtainlen-gate-")
        self.log = open(Path(self.data_dir) / "server.log", "w")
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        env = dict(os.environ, DATA_DIR=self.data_dir, PYTHONPATH=str(BACKEND))
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(self.port)],
            cwd=str(BACKEND), env=env, stdout=self.log, stderr=subprocess.STDOUT,
        )
        self.base_url = f"http://127.0.0.1:{self.port}"

    def wait_ready(self, client: ApiClient, timeout: float = 20.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(f"backend exited early rc={self.proc.returncode}: {self._log_tail()}")
            try:
                client.health()
                return
            except ApiError:
                time.sleep(0.2)
        raise RuntimeError(f"backend not ready in {timeout}s: {self._log_tail()}")

    def _log_tail(self):
        self.log.flush()
        try:
            return Path(self.log.name).read_text(errors="replace")[-500:].strip()
        except OSError:
            return "<no log>"

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.log.close()
        shutil.rmtree(self.data_dir, ignore_errors=True)


def check(expect: dict, numbers: dict, history: dict, client: ApiClient, wid: int, fid: int):
    """按 stages.json 的 expect 语义判定，返回 (ok, detail)。"""
    problems, notes = [], []
    for key, want in expect.items():
        if key == "panels_eq":
            if numbers["panels"] != want:
                problems.append(f"panels {numbers['panels']} != {want}")
        elif key == "meters_eq":
            if abs(numbers["meters"] - want) > 1e-9:
                problems.append(f"meters {numbers['meters']} != {want}")
        elif key == "meters_gt":
            ref = history[want]["meters"]
            notes.append(f"meters {numbers['meters']} > {want} {ref}")
            if not numbers["meters"] > ref:
                problems.append(f"meters {numbers['meters']} not > {want} {ref}")
        elif key == "panels_lt":
            ref = history[want]["panels"]
            notes.append(f"panels {numbers['panels']} < {want} {ref}")
            if not numbers["panels"] < ref:
                problems.append(f"panels {numbers['panels']} not < {want} {ref}")
        elif key == "meters_eq_hand":
            w, f = client.get_window(wid), client.get_fabric(fid)
            hand_panels, hand = hand_meters(w, f)
            notes.append(f"hand panels={hand_panels} meters={hand}")
            if numbers["panels"] != hand_panels or abs(numbers["meters"] - hand) > 1e-9:
                problems.append(f"api panels={numbers['panels']} meters={numbers['meters']} != hand panels={hand_panels} meters={hand}")
        elif key == "panels_back_to":
            ref = history[want]["panels"]
            notes.append(f"panels back to {want} {ref}")
            if numbers["panels"] != ref:
                problems.append(f"panels {numbers['panels']} != {want} {ref}")
        elif key == "meters_back_to":
            ref = history[want]["meters"]
            notes.append(f"meters back to {want} {ref}")
            if abs(numbers["meters"] - ref) > 1e-9:
                problems.append(f"meters {numbers['meters']} != {want} {ref}")
        else:
            problems.append(f"unknown expect key {key!r}")
    return (not problems), ("; ".join(problems) if problems else "; ".join(notes))


def run(client: ApiClient, spec: dict, report: StageReport):
    windows = {w["name"]: w for w in client.list_windows()}
    fabrics = {f["name"]: f for f in client.list_fabrics()}
    win = windows.get(spec["window_name"])
    fab = fabrics.get(spec["fabric_name"])
    if not win or not fab:
        raise RuntimeError(f"seed not found: {spec['window_name']!r} / {spec['fabric_name']!r}")
    original = {
        "window": {"fullness": win["fullness"]},
        "fabric": {"fabric_width": fab["fabric_width"]},
    }
    history = {}
    try:
        for stage in spec["stages"]:
            label = stage["label"]
            mutate = stage.get("mutate")
            if mutate == "restore_original":
                client.update_window(win["id"], **original["window"])
                client.update_fabric(fab["id"], **original["fabric"])
            elif mutate:
                if "window" in mutate:
                    client.update_window(win["id"], **mutate["window"])
                if "fabric" in mutate:
                    client.update_fabric(fab["id"], **mutate["fabric"])
            est = client.dry_run(win["id"], fab["id"])
            numbers = {"meters": est["meters"], "panels": est["panels"]}
            ok, detail = check(stage.get("expect", {}), numbers, history, client, win["id"], fab["id"])
            report.record(label, ok, numbers, detail)
            history[label] = numbers
            if not ok:
                return
    finally:
        # 无论成败都尽力写回原值，保证同一服务上可重复执行
        try:
            client.update_window(win["id"], **original["window"])
            client.update_fabric(fab["id"], **original["fabric"])
        except ApiError:
            pass


def main() -> int:
    spec = json.loads(STAGES_FILE.read_text(encoding="utf-8"))
    report = StageReport()
    base_url = os.environ.get("GATE_BASE_URL")
    server = None
    try:
        if base_url:
            client = ApiClient(base_url)
            client.health()
        else:
            server = EphemeralServer()
            client = ApiClient(server.base_url)
            server.wait_ready(client)
        run(client, spec, report)
    except (ApiError, RuntimeError) as e:
        report.record("infra", False, {}, str(e))
    finally:
        if server:
            server.stop()
    return report.finish()


if __name__ == "__main__":
    sys.exit(main())

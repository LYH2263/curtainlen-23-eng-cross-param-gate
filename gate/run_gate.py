#!/usr/bin/env python3
"""褶量×门幅交叉门禁 — one-click gate entry.

    python3 gate/run_gate.py            # spawn a throwaway backend and run
    GATE_BASE_URL=http://localhost:9800 python3 gate/run_gate.py   # run against a live stack

Flow (driven by gate/stages.json):
  1. baseline  — dry-run the seed 客厅落地窗 × 遮光1.4m, record meters/panels
  2. fullness  — window update sets fullness=2.5; meters must strictly grow
  3. width     — fabric update sets fabric_width=2.8; panels must strictly
                 drop vs the previous stage and meters must equal hand calc
  4. restore   — fullness/width written back; meters/panels back to baseline

Any failed stage -> non-zero process exit, with the stage label and the
numbers printed. The gate only talks HTTP (never touches sqlite seed rows)
and never imports app engines — the hand calculation below is independent.
"""
import json
import math
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

GATE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GATE_DIR))

from api_client import ApiClient, ApiError  # noqa: E402
from stage_report import StageReport  # noqa: E402

ROOT = GATE_DIR.parent
HEALTH_TIMEOUT_S = 30


def hand_calc(est: dict, default_fullness: float):
    """Independent hand calculation from the estimate payload itself."""
    w, f = est["window"], est["fabric"]
    fullness = float(w.get("fullness") or default_fullness)
    finished_w = float(w["width"]) * fullness
    panels = max(1, math.ceil(finished_w / float(f["fabric_width"]) - 1e-9))
    cut_h = float(w["height"]) + float(f["hem_top"]) + float(f["hem_bottom"])
    return panels, round(panels * cut_h, 2)


def check_expectations(expect, est, baseline, previous, default_fullness):
    meters, panels = est["meters"], est["panels"]
    if expect.get("record_baseline"):
        return True, "recorded baseline"
    if expect.get("meters_gt_baseline") and not meters > baseline["meters"]:
        return False, f"meters {meters} not > baseline {baseline['meters']}"
    if expect.get("panels_lt_previous") and not panels < previous["panels"]:
        return False, f"panels {panels} not < previous {previous['panels']}"
    if expect.get("meters_eq_hand_calc"):
        exp_panels, exp_meters = hand_calc(est, default_fullness)
        if panels != exp_panels or abs(meters - exp_meters) > 1e-9:
            return False, f"hand calc expects panels={exp_panels} meters={exp_meters}"
    if expect.get("meters_eq_baseline") and abs(meters - baseline["meters"]) > 1e-9:
        return False, f"meters {meters} != baseline {baseline['meters']}"
    if expect.get("panels_eq_baseline") and panels != baseline["panels"]:
        return False, f"panels {panels} != baseline {baseline['panels']}"
    return True, ""


def run_stages(api: ApiClient, report: StageReport) -> int:
    spec = json.loads((GATE_DIR / "stages.json").read_text(encoding="utf-8"))
    windows = api.get("/api/windows")["items"]
    fabrics = api.get("/api/fabrics")["items"]
    window = next((w for w in windows if w["name"] == spec["window_name"]), None)
    fabric = next((f for f in fabrics if f["name"] == spec["fabric_name"]), None)
    if not window or not fabric:
        report.add("locate-seed", False, {},
                   f"seed rows not found: {spec['window_name']} / {spec['fabric_name']}")
        return report.exit_code
    report.add("locate-seed", True, {"window_id": window["id"], "fabric_id": fabric["id"]})

    default_fullness = float(api.get("/api/settings").get("default_fullness", 2.0))
    orig_fullness, orig_width = window["fullness"], fabric["fabric_width"]
    baseline = previous = None
    needs_restore = False
    try:
        for stage in spec["stages"]:
            label = stage["label"]
            try:
                if stage.get("set_window"):
                    api.put(f"/api/windows/{window['id']}", stage["set_window"])
                    needs_restore = True
                if stage.get("set_fabric"):
                    api.put(f"/api/fabrics/{fabric['id']}", stage["set_fabric"])
                    needs_restore = True
                if stage.get("restore"):
                    api.put(f"/api/windows/{window['id']}", {"fullness": orig_fullness})
                    api.put(f"/api/fabrics/{fabric['id']}", {"fabric_width": orig_width})
                    needs_restore = False
                est = api.get(f"/api/estimate?window_id={window['id']}&fabric_id={fabric['id']}")
            except ApiError as e:
                report.add(label, False, {}, f"api error: {e}")
                return report.exit_code
            numbers = {"meters": est["meters"], "panels": est["panels"]}
            ok, detail = check_expectations(stage["expect"], est, baseline, previous, default_fullness)
            report.add(label, ok, numbers, detail)
            if not ok:
                return report.exit_code
            if stage["expect"].get("record_baseline"):
                baseline = numbers
            previous = numbers
        return report.exit_code
    finally:
        if needs_restore:  # keep a persistent DB clean even after a failed run
            try:
                api.put(f"/api/windows/{window['id']}", {"fullness": orig_fullness})
                api.put(f"/api/fabrics/{fabric['id']}", {"fabric_width": orig_width})
            except ApiError as e:
                print(f"gate warning: best-effort restore failed: {e}", flush=True)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_health(base_url: str, proc: subprocess.Popen) -> bool:
    deadline = time.time() + HEALTH_TIMEOUT_S
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(base_url + "/api/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except OSError:
            time.sleep(0.2)
    return False


def main() -> int:
    base_url = os.environ.get("GATE_BASE_URL")
    report = StageReport()
    proc = None
    tmp = None
    try:
        if not base_url:
            tmp = tempfile.TemporaryDirectory(prefix="curtainlen-gate-")
            port = free_port()
            base_url = f"http://127.0.0.1:{port}"
            log = open(Path(tmp.name) / "uvicorn.log", "w")
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app",
                 "--host", "127.0.0.1", "--port", str(port)],
                cwd=ROOT / "backend", env={**os.environ, "DATA_DIR": tmp.name},
                stdout=log, stderr=subprocess.STDOUT,
            )
            if not wait_health(base_url, proc):
                print("gate: backend failed to start, uvicorn log tail:", flush=True)
                print("".join(open(log.name).readlines()[-20:]), flush=True)
                return 2
        code = run_stages(ApiClient(base_url), report)
        report.summary()
        return code
    finally:
        if proc:
            proc.terminate()
            proc.wait(timeout=10)
        if tmp:
            tmp.cleanup()


if __name__ == "__main__":
    sys.exit(main())

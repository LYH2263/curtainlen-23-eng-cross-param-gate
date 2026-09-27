"""阶段报告 — collects per-stage outcomes and renders the gate report.

Every stage prints its label and the numbers observed at that moment;
the process exit code is derived from the collected records.
"""


class StageReport:
    def __init__(self):
        self.records = []

    def add(self, label: str, ok: bool, numbers: dict, detail: str = ""):
        rec = {"label": label, "ok": bool(ok), "numbers": dict(numbers), "detail": detail}
        self.records.append(rec)
        self._print(rec)

    @staticmethod
    def _print(rec: dict):
        status = "PASS" if rec["ok"] else "FAIL"
        nums = " ".join(f"{k}={v}" for k, v in rec["numbers"].items())
        line = f"[{status}] stage={rec['label']}"
        if nums:
            line += f" {nums}"
        if rec["detail"]:
            line += f"  # {rec['detail']}"
        print(line, flush=True)

    @property
    def ok(self) -> bool:
        return bool(self.records) and all(r["ok"] for r in self.records)

    @property
    def exit_code(self) -> int:
        return 0 if self.ok else 1

    def summary(self):
        passed = sum(1 for r in self.records if r["ok"])
        print(f"gate summary: {passed}/{len(self.records)} stages passed", flush=True)

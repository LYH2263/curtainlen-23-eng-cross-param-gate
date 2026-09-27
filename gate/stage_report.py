"""阶段报告：记录每个阶段的标签、当次数字与判定，负责打印与退出码。"""


class StageReport:
    def __init__(self):
        self.rows = []

    def record(self, label: str, ok: bool, numbers: dict, detail: str = ""):
        row = {"label": label, "ok": ok, "numbers": dict(numbers), "detail": detail}
        self.rows.append(row)
        self._print(row)

    @staticmethod
    def _print(row):
        tag = "PASS" if row["ok"] else "FAIL"
        nums = " ".join(f"{k}={v}" for k, v in row["numbers"].items())
        line = f"[{tag}] {row['label']:<14} {nums}".rstrip()
        if row["detail"]:
            line += f"  ({row['detail']})"
        print(line, flush=True)

    @property
    def failed(self):
        return [r for r in self.rows if not r["ok"]]

    def finish(self) -> int:
        if self.failed:
            labels = ",".join(r["label"] for r in self.failed)
            print(f"GATE FAIL: {labels}", flush=True)
            return 1
        print("GATE PASS", flush=True)
        return 0

"""Adapter wrapping qa-spine's own CLI (`node src/server.ts <subcommand>`) — the
same entry point qa-spine's tests drive — rather than reimplementing any of its
store or validation logic. Requires a sibling qa-spine checkout with its
node_modules installed, and Node >= 22.5. Stdlib only on this side.

One input is a list of CLI steps run against a fresh throwaway store: the
earlier steps seed it (record a requirement, submit findings, ...) and must
succeed; the last step is the one under test, and its exit code and error are
the output. "{req}" / "{finding}" in a step are replaced with the id the latest
`record` / `audit-submit` step produced.

Run from anywhere: python3 adapter.py   (self-check, ~1s)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

QA_SPINE_ROOT = Path(os.environ.get("QA_SPINE_ROOT", Path(__file__).resolve().parents[3] / "qa-spine"))
OUTCOMES = {0: "accept", 1: "reject", 2: "error"}  # qa-spine's CLI exit-code convention


def _cli(args, stdin, db):
    proc = subprocess.run(["node", str(QA_SPINE_ROOT / "src" / "server.ts"), *args],
                          input=json.dumps(stdin) if stdin is not None else "",
                          capture_output=True, text=True, env={**os.environ, "QA_SPINE_DB": db}, timeout=60)
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError:
        out = None
    # audit-submit/record/fixtures-submit report errors as JSON on stdout; gate uses stderr.
    error = (out.get("error") if isinstance(out, dict) else None) or proc.stderr.strip() or None
    return proc.returncode, out, error if proc.returncode else None


class QASpineAdapter:
    def run(self, input: dict) -> dict:
        refs = {}
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "trace.db")
            steps = input["steps"]
            for i, step in enumerate(steps):
                args = [a.format(**refs) if "{" in a else a for a in step["cmd"]]
                stdin = step.get("stdin")
                if stdin is not None:
                    raw = json.dumps(stdin)
                    for k, v in refs.items():
                        raw = raw.replace("{" + k + "}", v)
                    stdin = json.loads(raw)
                code, out, error = _cli(args, stdin, db)
                if i < len(steps) - 1 and code != 0:
                    return {"exit_code": None, "accepted": False, "error": f"setup step {i} {args[0]} failed: {error}",
                            "detail": out}
                if args[0] == "record" and code == 0:
                    refs["req"] = out["id"]
                if args[0] == "audit-submit" and code == 0 and out["recorded"]:
                    refs["finding"] = out["recorded"][0]
        return {"exit_code": code, "accepted": code == 0, "error": error, "detail": out}

    def expected_schema(self) -> dict:
        return {"exit_code": (int, type(None)), "accepted": bool, "error": (str, type(None)),
                "detail": (dict, list, type(None))}

    def intent_of(self, output: dict) -> str | None:
        # No routing in qa-spine; the coarse outcome is the closest analogue.
        return OUTCOMES.get(output["exit_code"])


def demo():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from core.adapter import SystemAdapter

    assert (QA_SPINE_ROOT / "src" / "server.ts").exists(), \
        f"expected qa-spine checkout at {QA_SPINE_ROOT} (override with QA_SPINE_ROOT env var)"
    adapter = QASpineAdapter()
    assert isinstance(adapter, SystemAdapter)
    out = adapter.run({"steps": [{"cmd": ["record"], "stdin": {
        "type": "requirement", "sourceRef": "DEMO-1", "content": {"text": "x"}, "provenance": {"producer": "human"}}}]})
    assert out["accepted"] and out["detail"]["id"].startswith("requirement_"), out
    assert adapter.intent_of(out) == "accept"
    print("adapter.py self-check OK (SystemAdapter conformance + one live qa-spine CLI call)")


if __name__ == "__main__":
    demo()

"""Adapter wrapping myNanoGpt's evals/run_evals.py — reuses its HTTP client,
keyword scoring, and LLM judge rather than reimplementing them. Requires the
QA Mentor AI server running (uvicorn chat_api:app --port 8004 in myNanoGpt)
and myNanoGpt's venv (needs requests, python-dotenv):

    ../myNanoGpt/.venv/bin/python3 adapter.py
"""
import os
import sys
from pathlib import Path

MYNANOGPT_ROOT = Path(os.environ.get("MYNANOGPT_ROOT", Path(__file__).resolve().parents[3] / "myNanoGpt"))
sys.path.insert(0, str(MYNANOGPT_ROOT))

from evals.run_evals import ask_agent, keyword_coverage, llm_judge  # noqa: E402


class QAMentorAdapter:
    def __init__(self, base_url: str = "http://localhost:8004"):
        self.base_url = base_url

    def run(self, input: dict) -> dict:
        agent, answer, sources, error = ask_agent(self.base_url, input["question"])
        return {"routed_intent": agent, "answer": answer, "sources": sources, "error": error}

    def expected_schema(self) -> dict:
        return {"routed_intent": (str, type(None)), "answer": str, "sources": list, "error": (str, type(None))}

    def intent_of(self, output: dict) -> str | None:
        return output.get("routed_intent")


def demo():
    assert (MYNANOGPT_ROOT / "evals" / "run_evals.py").exists(), \
        f"expected myNanoGpt checkout at {MYNANOGPT_ROOT} (override with MYNANOGPT_ROOT env var)"
    adapter = QAMentorAdapter()
    fake_output = {"routed_intent": "mentor", "answer": "x", "sources": [], "error": None}
    assert adapter.intent_of(fake_output) == "mentor"
    print("adapter.py self-check OK (import + path resolution; run() needs a live server, not checked here)")


if __name__ == "__main__":
    demo()

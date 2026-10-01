#!/usr/bin/env python3
"""Tier 1 out_of_scope_refused metric: did the agent decline / redirect an
off-topic question back to QA, instead of answering it? Deterministic keyword
heuristic on the answer text — no LLM judge.

Also holds this case study's tier map (core/metrics.py classify_tier).

Run: python3 metrics_oos.py   (self-check, stdlib only)
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # agent-evals root, for `core`
from core.metrics import TIER_1, TIER_2, TIER_3  # noqa: E402

TIER_MAP = {
    "intent_accuracy": TIER_1,
    "out_of_scope_refused": TIER_1,
    "keyword_coverage": TIER_2,
    "judge_score": TIER_3,
}

REDIRECT = re.compile(
    r"can(?:no|')t help with|unable to help|not able to help|outside (?:of )?(?:my|the) scope|"
    r"out of scope|beyond (?:my|the) scope|off[- ]topic|out of context for|can(?:no|')t provide|not (?:something|what) I(?:'m| am) (?:designed|built|here) for|"
    r"speciali[sz]ed? (?:in|on) (?:QA|quality|software testing|testing)|back to (?:the realm of )?(?:QA|quality|software testing|testing)|"
    r"(?:try|feel free to) ask(?:ing)? (?:me )?about (?:QA|test)|(?:QA|testing)[- ]related question",
    re.IGNORECASE,
)


# ponytail: "substantive off-topic answer" = any of the golden's hand-picked
# off_topic_markers appears (case-insensitive). A marker list can miss a novel
# phrasing of the off-topic answer (false pass) or collide with an
# acknowledgement of the question (false fail) — read the saved answers, as
# was done for the first run, whenever markers or goldens change.
def is_graceful_redirect(answer: str, off_topic_markers: list[str]) -> bool:
    lower = answer.lower()
    return bool(REDIRECT.search(answer)) and not any(m.lower() in lower for m in off_topic_markers)


def demo():
    scrape = ["BeautifulSoup", "import requests", "proxies"]
    assert is_graceful_redirect(
        "Sorry, that's outside my scope — I'm specialised in QA and software testing. "
        "Try asking about test automation, flaky tests, or test strategy instead.", scrape)
    assert not is_graceful_redirect(
        "When it comes to scraping stock prices, there are a few approaches.\n```python\nimport requests\n"
        "proxies = {'http': 'http://10.10.1.10:3128'}\n```", scrape)
    # Redirect that pivots to QA content, code included -> pass (the real hard-06 shape).
    assert is_graceful_redirect(
        "Your pizza question is a bit off-topic. However, here is a unit test:\n```js\n"
        "test('x', () => expect(f()).toBe(1));\n```", ["pepperoni", "mushroom"])
    # Declines, then delivers the off-topic answer anyway -> markers make it fail.
    assert not is_graceful_redirect(
        "While I can't provide a direct recipe from the context, here's one: 1 cup butter, 2 cups flour.",
        ["flour", "butter"])
    # Declines in passing but still delivers the off-topic answer -> fail.
    assert not is_graceful_redirect("This is off-topic, but pepperoni is the classic choice.", ["pepperoni"])
    # Helpful but never declines -> fail.
    assert not is_graceful_redirect("The 2018 World Cup was won by France.", ["France"])
    print("metrics_oos.py self-check OK")


if __name__ == "__main__":
    demo()

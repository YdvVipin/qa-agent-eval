"""Judge vs. human-label agreement: raw agreement + Cohen's kappa (chance-
corrected agreement). No sklearn — a single pairwise kappa is ~10 lines."""
from collections import Counter


def raw_agreement(judge_labels: list, human_labels: list) -> float:
    """Fraction of items where judge and human assigned the same label."""
    if len(judge_labels) != len(human_labels):
        raise ValueError("label lists must be the same length")
    if not judge_labels:
        raise ValueError("no labels to compare")
    matches = sum(1 for j, h in zip(judge_labels, human_labels) if j == h)
    return matches / len(judge_labels)


def cohens_kappa(judge_labels: list, human_labels: list) -> float:
    """Cohen's kappa: agreement corrected for chance, from two label sequences."""
    n = len(judge_labels)
    if n != len(human_labels):
        raise ValueError("label lists must be the same length")
    if n == 0:
        raise ValueError("no labels to compare")

    po = raw_agreement(judge_labels, human_labels)

    judge_counts = Counter(judge_labels)
    human_counts = Counter(human_labels)
    labels = set(judge_counts) | set(human_counts)
    pe = sum((judge_counts.get(l, 0) / n) * (human_counts.get(l, 0) / n) for l in labels)

    if pe == 1.0:
        return 1.0  # both raters used exactly one (identical) label for every item
    return (po - pe) / (1 - pe)


def demo():
    j = [1, 2, 3, 2, 1]
    h = [1, 2, 3, 2, 1]
    assert raw_agreement(j, h) == 1.0
    assert cohens_kappa(j, h) == 1.0

    # balanced marginals, 50% raw agreement -> kappa is exactly 0 (chance level)
    j2 = [1, 1, 2, 2]
    h2 = [1, 2, 1, 2]
    assert raw_agreement(j2, h2) == 0.5
    assert cohens_kappa(j2, h2) == 0.0

    print("judge_agreement.py self-check OK")


if __name__ == "__main__":
    demo()

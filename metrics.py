"""Scoring and statistics. No API libraries needed, so analysis runs anywhere."""
import math
import re
import string
from collections import Counter

# ---------- scoring (standard SQuAD/HotpotQA EM and F1) ----------
_PUNCT = set(string.punctuation)


def normalize(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in _PUNCT)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def exact_match(pred, gold):
    return float(normalize(pred) == normalize(gold))


def f1_score(pred, gold):
    p, g = normalize(pred).split(), normalize(gold).split()
    if not p or not g:
        return float(p == g)
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if same == 0:
        return 0.0
    precision, recall = same / len(p), same / len(g)
    return 2 * precision * recall / (precision + recall)


def clean_answer(pred):
    """Gold-blind tidy-up of a model answer before scoring: drop an "Answer:" prefix, anything
    after the first line, bracketed asides like "(RAF)" and stray quotes/periods."""
    p = pred.strip()
    p = re.sub(r"^(final answer|answer)\s*:\s*", "", p, flags=re.I)
    p = p.split("\n")[0]
    p = re.sub(r"\s*\([^)]*\)", "", p)
    return p.strip(" .\"'*")


# ---------- refusals ----------
ABSTAIN = ("not stated", "unknown", "not specified", "cannot be determined", "no information",
           "not mentioned", "not provided", "not in the context", "insufficient")


def abstains(text):
    """True if the answer refuses ("unknown", "not stated", ...) instead of guessing."""
    t = text.lower()
    return any(a in t for a in ABSTAIN)



# ---------- statistics ----------
def sign_test(wins, losses):
    """Exact two-sided sign test: chance of a split at least this uneven if the change did nothing.
    With wins/losses = exact-match fixed/broken counts this is the exact McNemar test."""
    n, k = wins + losses, min(wins, losses)
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)

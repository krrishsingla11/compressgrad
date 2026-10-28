import json
import os
import random
import sys

# Usage: python analyze_repair.py        (v1 results)
#        python analyze_repair.py v2     (improved repair)
#        python analyze_repair.py v2 heldout   (improved repair on the fresh questions)
#        python analyze_repair.py v2 all       (all question sets pooled: 1-30, 31-60 and 61-90 if present)
#        python analyze_repair.py v3 final     (v3 on the fresh questions 61-90)
V = "_v3" if "v3" in sys.argv else ("_v2" if "v2" in sys.argv else "")
if "all" in sys.argv:
    FILES = [f"repair{V}_results.jsonl", f"repair{V}_heldout_results.jsonl", f"repair{V}_final_results.jsonl"]
    FILES = [f for f in FILES if os.path.exists(f)]
else:
    SUF = "_final" if "final" in sys.argv else ("_heldout" if "heldout" in sys.argv else "")
    FILES = [f"repair{V}{SUF}_results.jsonl"]
rows = []
for FILE in FILES:
    with open(FILE, encoding="utf-8") as f:
        rows += [json.loads(line) for line in f if line.strip()]

random.seed(0)
ABSTAIN = ("not stated", "unknown", "not specified", "cannot be determined",
           "no information", "not mentioned", "not provided", "not in the context")


def abstains(text):
    t = text.lower()
    return any(a in t for a in ABSTAIN)


for ratio in sorted({r["ratio"] for r in rows}):
    rs = [r for r in rows if r["ratio"] == ratio]
    diffs = [r["repaired_f1"] - r["draft_f1"] for r in rs]
    helped = sum(d > 0 for d in diffs)
    hurt = sum(d < 0 for d in diffs)
    same = len(diffs) - helped - hurt

    # 95% confidence range for the average F1 change (bootstrap)
    means = []
    for _ in range(5000):
        sample = [random.choice(diffs) for _ in diffs]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo, hi = means[125], means[4875]

    print(f"\n=== {ratio}x  (n={len(rs)}) ===")
    print(f"Repair helped: {helped}   hurt: {hurt}   unchanged: {same}")
    print(f"Average F1 change: {sum(diffs) / len(diffs):+.3f}   95% range: [{lo:+.3f}, {hi:+.3f}]")
    print(f"Answers like 'not stated / unknown':  draft {sum(abstains(r['draft']) for r in rs)}  ->  repaired {sum(abstains(r['repaired']) for r in rs)}")
    print("Cases where repair made it WORSE:")
    for r in [r for r in rs if r["repaired_f1"] < r["draft_f1"]][:6]:
        print(f"  gold={r['gold']!r} | draft={r['draft']!r} -> repaired={r['repaired']!r}")

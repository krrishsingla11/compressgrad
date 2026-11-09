"""Compare two result files question by question, with significance tests.

Usage: python compare_results.py results_compressed.json results_qa_promptv1.json
       python compare_results.py results_baseline.json results_baseline_promptv2.json
"""
import json
import sys

from metrics import sign_test

old_path, new_path = sys.argv[1], sys.argv[2]


def load(path):
    """{ratio label: {id: row}} for both baseline and compressed result files."""
    with open(path, encoding="utf-8") as f:
        res = json.load(f)
    if "summary" in res:
        return {"none": {r["id"]: r for r in res["rows"]}}
    return {f"{k}x": {r["id"]: r for r in rows} for k, rows in res["rows"].items()}


old, new = load(old_path), load(new_path)
print(f"OLD = {old_path}\nNEW = {new_path}\n")
print(f"{'ratio':>6} {'n':>4} {'EM old':>7} {'EM new':>7} {'F1 old':>7} {'F1 new':>7}"
      f" {'EM fixed/broken':>16} {'McNemar p':>10} {'F1 sign p':>10}")
for label in old:
    if label not in new:
        continue
    ids = [i for i in old[label] if i in new[label]]
    o, n = old[label], new[label]
    avg = lambda rows, k: sum(rows[i][k] for i in ids) / len(ids)
    fixed = sum(n[i]["em"] > o[i]["em"] for i in ids)
    broken = sum(n[i]["em"] < o[i]["em"] for i in ids)
    f1_up = sum(n[i]["f1"] > o[i]["f1"] for i in ids)
    f1_down = sum(n[i]["f1"] < o[i]["f1"] for i in ids)
    print(f"{label:>6} {len(ids):>4} {avg(o, 'em'):>7.3f} {avg(n, 'em'):>7.3f} {avg(o, 'f1'):>7.3f}"
          f" {avg(n, 'f1'):>7.3f} {f'{fixed}/{broken}':>16} {sign_test(fixed, broken):>10.4f}"
          f" {sign_test(f1_up, f1_down):>10.4f}")

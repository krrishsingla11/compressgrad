"""Answer recall of compressed contexts: how often the gold answer still appears in the text
the model gets. Needs no API calls, so it is a cheap check before spending quota on eval.

Usage: python context_recall.py                                  (compressed.json)
       python context_recall.py compressed.json compressed_qa.json   (side by side)
"""
import json
import sys

from metrics import normalize

files = sys.argv[1:] or ["compressed.json"]

with open("data.json", encoding="utf-8") as f:
    data = {d["id"]: d for d in json.load(f)}
# yes/no answers never appear in the text, so leave those questions out
ids = [i for i, d in data.items() if normalize(d["answer"]) not in ("yes", "no")]


def answer_kept(answer, context):
    return normalize(answer) in normalize(context)


print(f"Answer recall (gold answer still in the context), n={len(ids)} non yes/no questions")
print(f"{'file':<34}{'ratio':>6}{'recall':>9}{'avg tokens':>12}")
for path in files:
    with open(path, encoding="utf-8") as f:
        compressed = json.load(f)
    for ratio, rows in compressed.items():
        rows = {r["id"]: r for r in rows}
        kept = sum(answer_kept(data[i]["answer"], rows[i]["context"]) for i in ids)
        toks = sum(rows[i]["compressed_tokens"] for i in ids) / len(ids)
        print(f"{path:<34}{ratio + 'x':>6}{kept / len(ids):>9.1%}{toks:>12.0f}")

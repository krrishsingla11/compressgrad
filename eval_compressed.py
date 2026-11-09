import json
import sys

from config import ANSWER_MODEL
from utils import evaluate

# Usage: python eval_compressed.py                      (all questions, plain compression)
#        python eval_compressed.py 5                    (only first 5 per tier, quick test)
#        python eval_compressed.py compressed_qa.json   (question-aware compression)
limit, SOURCE = None, "compressed.json"
for arg in sys.argv[1:]:
    if arg.isdigit():
        limit = int(arg)
    elif arg.endswith(".json"):
        SOURCE = arg
OUT = "results_" + SOURCE   # compressed.json -> results_compressed.json

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
with open(SOURCE, encoding="utf-8") as f:
    compressed = json.load(f)
if limit:
    data = data[:limit]

summaries, all_rows = [], {}
for ratio, comp_rows in compressed.items():
    contexts = {r["id"]: r["context"] for r in comp_rows}   # match by id, not list position
    s, rows = evaluate(data, contexts, ANSWER_MODEL, f"{ratio}x")
    s = {"condition": "compressed", "ratio": int(ratio), **s}
    summaries.append(s)
    all_rows[ratio] = rows
    print("RESULT:", s, "\n")

print("===== SUMMARY =====")
for s in summaries:
    print(s)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"summaries": summaries, "rows": all_rows}, f, indent=2)

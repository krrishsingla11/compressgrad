import json
import sys

from config import ANSWER_MODEL
from utils import evaluate

# Usage: python baseline.py        (all questions)
#        python baseline.py 5      (only the first 5, for a quick test)
limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
if limit:
    data = data[:limit]

summary, rows = evaluate(data, {item["id"]: item["context"] for item in data}, ANSWER_MODEL, "baseline")
summary = {"condition": "baseline", **summary}
print("\nRESULT:", summary)

with open("results_baseline.json", "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "rows": rows}, f, indent=2)

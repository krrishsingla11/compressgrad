import json
import sys

from config import ANSWER_MODEL
from utils import ask, build_prompt, exact_match, f1_score

# Usage: python baseline.py        (all questions)
#        python baseline.py 5      (only the first 5, for a quick test)
limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
if limit:
    data = data[:limit]

em_total = f1_total = tokens_total = 0
rows = []
for i, item in enumerate(data, 1):
    prompt = build_prompt(item["context"], item["question"])
    out = ask(prompt, ANSWER_MODEL)
    em = exact_match(out["text"], item["answer"])
    f1 = f1_score(out["text"], item["answer"])
    em_total += em
    f1_total += f1
    tokens_total += out["prompt_tokens"]
    rows.append({"id": item["id"], "pred": out["text"], "gold": item["answer"], "em": em, "f1": f1})
    print(f"[{i}/{len(data)}] gold={item['answer']!r}  pred={out['text']!r}")

n = len(data)
summary = {
    "condition": "baseline",
    "n": n,
    "exact_match": round(em_total / n, 3),
    "f1": round(f1_total / n, 3),
    "avg_prompt_tokens": round(tokens_total / n),
}
print("\nRESULT:", summary)

with open("results_baseline.json", "w", encoding="utf-8") as f:
    json.dump({"summary": summary, "rows": rows}, f, indent=2)

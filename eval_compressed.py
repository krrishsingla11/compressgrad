import json
import sys

from config import ANSWER_MODEL
from utils import ask, build_prompt, exact_match, f1_score

# Usage: python eval_compressed.py        (all questions)
#        python eval_compressed.py 5      (only first 5 per tier, quick test)
limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)
with open("compressed.json", encoding="utf-8") as f:
    compressed = json.load(f)

summaries, all_rows = [], {}
for ratio, comp_rows in compressed.items():
    n_use = limit or len(data)
    em_t = f1_t = tok_t = 0
    rows = []
    for i in range(n_use):
        item, comp = data[i], comp_rows[i]
        prompt = build_prompt(comp["context"], item["question"])
        out = ask(prompt, ANSWER_MODEL)
        em = exact_match(out["text"], item["answer"])
        f1 = f1_score(out["text"], item["answer"])
        em_t += em
        f1_t += f1
        tok_t += out["prompt_tokens"]
        rows.append({"id": item["id"], "pred": out["text"], "gold": item["answer"], "em": em, "f1": f1})
        print(f"[{ratio}x {i + 1}/{n_use}] gold={item['answer']!r}  pred={out['text']!r}")
    s = {
        "condition": "compressed",
        "ratio": int(ratio),
        "n": n_use,
        "exact_match": round(em_t / n_use, 3),
        "f1": round(f1_t / n_use, 3),
        "avg_prompt_tokens": round(tok_t / n_use),
    }
    summaries.append(s)
    all_rows[ratio] = rows
    print("RESULT:", s, "\n")

print("===== SUMMARY =====")
for s in summaries:
    print(s)

with open("results_compressed.json", "w", encoding="utf-8") as f:
    json.dump({"summaries": summaries, "rows": all_rows}, f, indent=2)

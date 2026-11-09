"""Token cost of the repair step, measured by replaying every stored repair from cache.jsonl.
No API calls: a call that is not in the cache is reported as missing, never sent.

Usage: python cost_analysis.py
"""
import hashlib
import json
import sys

import utils
from config import ANSWER_MODEL
from metrics import clean_answer

import repair as rp

# (label, results file, compressed file, v2, v3, rounds)
RUNS = [
    ("v2, plain ctx, Q1-30", "repair_v2_results.jsonl", "compressed.json", True, False, 1),
    ("v2, plain ctx, Q31-60", "repair_v2_heldout_results.jsonl", "compressed.json", True, False, 1),
    ("v2, plain ctx, Q61-90", "repair_v2_final_results.jsonl", "compressed.json", True, False, 1),
    ("v3, QA-aware ctx, Q61-90", "repair_v3_final_qa_results.jsonl", "compressed_qa.json", True, True, 2),
]
FULL_PROMPT_TOKENS = 1452          # average uncompressed answer prompt (results_baseline.json)


class CacheMiss(Exception):
    pass


calls = []


def cached_ask(prompt, model, max_tokens=1024, system=None):
    raw = model + "||" + prompt if not system else model + "||" + system + "||" + prompt
    key = hashlib.md5(raw.encode("utf-8")).hexdigest()
    if key not in utils._cache:
        raise CacheMiss
    row = utils._cache[key]
    calls.append(row["prompt_tokens"])
    return row


rp.ask = cached_ask                # the judge engine inside repair() now counts instead of calling

print(f"{'run':<26}{'ratio':>6}{'n':>4}{'answer':>8}{'repair':>8}{'calls':>7}{'total':>7}"
      f"{'vs full':>9}{'same':>6}{'miss':>5}")
for label, results, comp_file, v2, v3, rounds in RUNS:
    try:
        with open(results, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        continue
    with open(comp_file, encoding="utf-8") as f:
        comp = {k: {r["id"]: r["context"] for r in v} for k, v in json.load(f).items()}
    with open("data.json", encoding="utf-8") as f:
        questions = {d["id"]: d["question"] for d in json.load(f)}
    rp.V2, rp.V3, rp.ROUNDS = v2, v3, rounds
    for ratio in sorted({r["ratio"] for r in rows}):
        ans_tok = rep_tok = n_calls = same = miss = n = 0
        for r in (r for r in rows if r["ratio"] == ratio):
            ctx, q = comp[str(ratio)][r["id"]], questions[r["id"]]
            try:
                ans_tok += cached_ask(utils.build_prompt(ctx, q), ANSWER_MODEL)["prompt_tokens"]
                calls.clear()
                out, _, _ = rp.repair_answer(q, ctx, r["draft"])
            except CacheMiss:
                miss += 1
                continue
            n += 1
            rep_tok += sum(calls)
            n_calls += len(calls)
            same += clean_answer(out) == clean_answer(r["repaired"])
        if n == 0:
            print(f"{label:<26}{ratio:>5}x  no replayable rows ({miss} missing)")
            continue
        total = (ans_tok + rep_tok) / n
        print(f"{label:<26}{ratio:>5}x{n:>4}{ans_tok / n:>8.0f}{rep_tok / n:>8.0f}{n_calls / n:>7.1f}"
              f"{total:>7.0f}{total / FULL_PROMPT_TOKENS:>8.0%}{same:>6}{miss:>5}")
print("\nanswer/repair/total = average prompt tokens per question (answer call, all judge calls, both);")
print(f"'vs full' compares the total with the {FULL_PROMPT_TOKENS}-token uncompressed answer prompt.")
print("'same' = replayed answer matches the stored one (checks the replay is faithful).")
sys.exit(0)

import json
import os
import sys

import textgrad as tg
from textgrad.engine import EngineLM

from config import ANSWER_MODEL, JUDGE_MODEL, N_REPAIR, REPAIR_RATIOS, REPAIR_ROUNDS
from utils import ask, build_prompt, exact_match, f1_score

# Usage examples (every command resumes where it stopped):
#   python repair.py                 original repair (v1), first 30 questions
#   python repair.py v2              improved repair (no "unknown" answers, keeps correct drafts)
#   python repair.py v2 heldout      v2 on questions 31-60
#   python repair.py v3 final        v3 (v2 + "only change if the context clearly says so" + 2 rounds)
#                                    on FRESH questions 61-90
#   python repair.py v3 final ratios=5,10    same, only at 5x and 10x (uses less quota)
#   python repair.py v3 final 3      quick test on 3 questions
limit, V2, V3, HELDOUT, FINAL = N_REPAIR, False, False, False, False
RATIOS = REPAIR_RATIOS
for arg in sys.argv[1:]:
    if arg == "v2":
        V2 = True
    elif arg == "v3":
        V3 = True
    elif arg == "heldout":
        HELDOUT = True
    elif arg == "final":
        FINAL = True
    elif arg.startswith("ratios="):
        RATIOS = [int(x) for x in arg[len("ratios="):].split(",")]
    elif arg.isdigit():
        limit = int(arg)
if V3:
    V2 = True                      # v3 includes every v2 rule

START = 60 if FINAL else (30 if HELDOUT else 0)
VERSION = "v3" if V3 else ("v2" if V2 else "v1")
TAG = ("_v3" if V3 else "_v2" if V2 else "") + ("_final" if FINAL else "_heldout" if HELDOUT else "")
RESULTS_FILE = f"repair{TAG}_results.jsonl"
SUMMARY_FILE = f"repair{TAG}_summary.json"
ROUNDS = 2 if V3 else REPAIR_ROUNDS

ABSTAIN = ("not stated", "unknown", "not specified", "cannot be determined", "no information",
           "not mentioned", "not provided", "not in the context", "insufficient")


def abstains(text):
    t = text.lower()
    return any(a in t for a in ABSTAIN)


class JudgeEngine(EngineLM):
    """Lets TextGrad talk to Groq through our cached, rate-limit-safe ask()."""

    def __init__(self, model):
        self.model_string = model
        self.system_prompt = "You are a helpful assistant."

    def generate(self, prompt, system_prompt=None, **kwargs):
        return ask(prompt, self.model_string, system=system_prompt or self.system_prompt, max_tokens=1500)["text"]

    def __call__(self, prompt, **kwargs):
        return self.generate(prompt, **kwargs)


engine = JudgeEngine(JUDGE_MODEL)
tg.set_backward_engine(engine, override=True)

V2_RULES = (
    "\nIMPORTANT RULES:\n"
    "- The context is compressed, so never say the answer is unknown, not stated or cannot be determined. "
    "Always give the best guess the context supports.\n"
    "- If the draft answer is already correct and complete, reply with exactly: The draft answer is correct. "
    "Do not suggest any changes.\n"
    "- Keep the same form: just the name, date, number or place. Do not add descriptions, brackets or extra words.\n"
)
V3_RULES = (
    "- Only suggest a different answer if the context clearly supports it for this exact question. "
    "If you are unsure, say: The draft answer is correct.\n"
    "- Any new answer must use words that actually appear in the CONTEXT. Do not swap in a different name, "
    "place or date from your own knowledge.\n"
)


def repair(question, context, draft):
    """One TextGrad repair. The judge sees ONLY the compressed context, never the gold answer."""
    instruction = (
        "You are a strict judge of a question-answering system. You get a QUESTION, a CONTEXT and a "
        "DRAFT ANSWER (shown to you below). The CONTEXT is a heavily compressed version of the original "
        "text, so some words are missing but most key facts remain.\n"
        "Check the draft answer: Is it supported by the context? Does it answer exactly what the question "
        "asks (for example a year, a name, a place, yes/no)? Is it short (a few words)? "
        "Point out specific problems and say what the correct short answer should be, based on the context.\n"
        + (V2_RULES if V2 else "")
        + (V3_RULES if V3 else "")
        + "\nQUESTION: " + question + "\n\nCONTEXT:\n" + context
    )
    constraints = ["The answer must be only a few words (a name, date, number, place or yes/no). No explanation, no full sentences."]
    if V2:
        constraints += [
            "Never answer unknown, not stated, not specified or cannot be determined. Always give the best guess.",
            "If the feedback says the draft is correct, return the draft answer unchanged. Do not add descriptions, brackets or extra words.",
        ]
    if V3:
        constraints += ["Keep the draft answer unless the context clearly supports a different answer. If unsure, return the draft unchanged."]
    answer = tg.Variable(draft, requires_grad=True, role_description="short answer to the question")
    loss_fn = tg.TextLoss(instruction, engine=engine)
    optimizer = tg.TGD(parameters=[answer], engine=engine, constraints=constraints)
    for _ in range(ROUNDS):
        optimizer.zero_grad()
        loss = loss_fn(answer)
        if V2 and "draft answer is correct" in loss.value.lower():
            break                      # judge says it's fine: keep it, save the extra calls
        loss.backward()
        optimizer.step()
    return answer.value


# ---------- load data ----------
with open("data.json", encoding="utf-8") as f:
    data = json.load(f)[START:START + limit]
with open("compressed.json", encoding="utf-8") as f:
    compressed = json.load(f)
with open("results_baseline.json", encoding="utf-8") as f:
    baseline = {r["id"]: r for r in json.load(f)["rows"]}

done = {}
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                done[(r["ratio"], r["id"])] = r


def summarize():
    summary = []
    for ratio in RATIOS:
        rows = [r for (rt, _), r in done.items() if rt == ratio]
        if not rows:
            continue
        n = len(rows)
        avg = lambda k: sum(r[k] for r in rows) / n
        base_f1 = sum(baseline[r["id"]]["f1"] for r in rows) / n
        comp_f1, rep_f1 = avg("draft_f1"), avg("repaired_f1")
        gap = base_f1 - comp_f1
        summary.append({
            "ratio": ratio, "n": n,
            "baseline_f1": round(base_f1, 3),
            "compressed_f1": round(comp_f1, 3),
            "repaired_f1": round(rep_f1, 3),
            "compressed_em": round(avg("draft_em"), 3),
            "repaired_em": round(avg("repaired_em"), 3),
            "recovery_percent": round(100 * (rep_f1 - comp_f1) / gap, 1) if gap > 0 else None,
            "guard_used": sum(bool(r.get("guard")) for r in rows),
        })
    print("\n===== REPAIR SUMMARY (%s%s) =====" % (VERSION, ", fresh questions 61+" if FINAL else ", held-out questions 31+" if HELDOUT else ""))
    for s in summary:
        print(s)
    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


# ---------- main loop (question by question, so every level progresses evenly) ----------
try:
    for i, item in enumerate(data, 1):
        for ratio in RATIOS:
            if (ratio, item["id"]) in done:
                continue
            ctx = next(r for r in compressed[str(ratio)] if r["id"] == item["id"])["context"]
            draft = ask(build_prompt(ctx, item["question"]), ANSWER_MODEL)["text"]
            error, guard = None, False
            try:
                repaired = repair(item["question"], ctx, draft)
            except IndexError:           # optimizer forgot the answer tags: keep the draft
                repaired, error = draft, "optimizer format error"
            if V2 and abstains(repaired):  # guard: never replace an answer with "unknown"
                repaired, guard = draft, True
            row = {
                "ratio": ratio, "id": item["id"], "gold": item["answer"],
                "draft": draft, "repaired": repaired, "error": error, "guard": guard,
                "draft_em": exact_match(draft, item["answer"]), "draft_f1": f1_score(draft, item["answer"]),
                "repaired_em": exact_match(repaired, item["answer"]), "repaired_f1": f1_score(repaired, item["answer"]),
            }
            done[(ratio, item["id"])] = row
            with open(RESULTS_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(data)}] {ratio}x gold={row['gold']!r} | draft={draft!r} -> repaired={repaired!r}")
finally:
    summarize()

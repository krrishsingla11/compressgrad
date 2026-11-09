import hashlib
import json
import os
import time

import litellm

from config import CLEAN_ANSWERS, PROMPT_VERSION
from metrics import clean_answer, exact_match, f1_score

litellm.drop_params = True       # ignore settings a model doesn't support
litellm.suppress_debug_info = True

CACHE_FILE = "cache.jsonl"
_cache = {}

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                if row["text"]:          # empty replies were failed calls: ask again
                    _cache[row["key"]] = row

TRANSIENT_ERRORS = (
    litellm.APIConnectionError,
    litellm.ServiceUnavailableError,
    litellm.InternalServerError,
    litellm.Timeout,
)


def ask(prompt, model, max_tokens=1024, system=None):
    """Send a prompt to a model. Saved answers are reused, so nothing is paid for twice."""
    raw = model + "||" + prompt if not system else model + "||" + system + "||" + prompt
    key = hashlib.md5(raw.encode("utf-8")).hexdigest()
    if key in _cache:
        return _cache[key]

    for attempt in range(8):
        try:
            resp = litellm.completion(
                model=model,
                messages=(
                    [{"role": "system", "content": system}] if system else []
                ) + [{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0,
                reasoning_effort="low",
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                # gpt-oss can spend the whole budget on reasoning and return nothing.
                # Don't cache that (it would be scored as a wrong answer forever): retry with more room.
                max_tokens *= 2
                print(f"  empty reply ({resp.choices[0].finish_reason}), retrying with max_tokens={max_tokens}")
                continue
            row = {
                "key": key,
                "text": text,
                "prompt_tokens": resp.usage.prompt_tokens,
            }
            _cache[key] = row
            with open(CACHE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
            return row
        except litellm.RateLimitError as e:
            msg = str(e)
            if "per day" in msg.lower() or "TPD" in msg or "RPD" in msg:
                print("\nDAILY LIMIT REACHED. Progress is saved in cache.jsonl.")
                print("Run the same command again after the limit resets.")
                print(msg[:400])
                raise SystemExit(1)
            wait = 20 * (attempt + 1)
            print(f"  rate limit hit, waiting {wait}s...")
            time.sleep(wait)
        except TRANSIENT_ERRORS as e:
            wait = 5 * (attempt + 1)
            print(f"  {type(e).__name__}, retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Gave up after repeated failures")


def build_prompt(context, question):
    if PROMPT_VERSION == "v2":
        return (
            "Answer the question using the context below.\n"
            "Rules:\n"
            "- Reply with ONLY the answer, copied exactly as it is written in the context "
            "(a name, title, date, number or place). No explanation, no full sentence.\n"
            "- For yes/no questions reply with just yes or no.\n"
            "- Do not add brackets, descriptions or extra words.\n\n"
            "Example:\nQuestion: Which country is the band Kraftwerk from?\nAnswer: Germany\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
    return (
        "Answer the question using the context below. "
        "Reply with ONLY the short answer (a few words), no explanation.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )


# ---------- evaluation ----------
def final_answer(text):
    """The answer that gets scored: the raw reply, tidied if CLEAN_ANSWERS is on."""
    return clean_answer(text) if CLEAN_ANSWERS else text


def evaluate(items, contexts, model, label):
    """Answer every item using contexts[item id]; return (summary, rows)."""
    em_t = f1_t = tok_t = 0
    rows = []
    for i, item in enumerate(items, 1):
        out = ask(build_prompt(contexts[item["id"]], item["question"]), model)
        pred = final_answer(out["text"])
        em = exact_match(pred, item["answer"])
        f1 = f1_score(pred, item["answer"])
        em_t += em
        f1_t += f1
        tok_t += out["prompt_tokens"]
        rows.append({"id": item["id"], "pred": pred, "raw": out["text"], "gold": item["answer"], "em": em, "f1": f1})
        print(f"[{label} {i}/{len(items)}] gold={item['answer']!r}  pred={pred!r}")
    n = len(items)
    summary = {
        "n": n,
        "exact_match": round(em_t / n, 3),
        "f1": round(f1_t / n, 3),
        "avg_prompt_tokens": round(tok_t / n),
    }
    return summary, rows

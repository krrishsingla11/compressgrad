import hashlib
import json
import os
import re
import string
import time
from collections import Counter

import litellm

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
                _cache[row["key"]] = row


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
            row = {
                "key": key,
                "text": (resp.choices[0].message.content or "").strip(),
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
    raise RuntimeError("Gave up after repeated rate limits")


# ---------- scoring ----------
def normalize(s):
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation))
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    return " ".join(s.split())


def exact_match(pred, gold):
    return float(normalize(pred) == normalize(gold))


def f1_score(pred, gold):
    p, g = normalize(pred).split(), normalize(gold).split()
    if not p or not g:
        return float(p == g)
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if same == 0:
        return 0.0
    precision, recall = same / len(p), same / len(g)
    return 2 * precision * recall / (precision + recall)


def build_prompt(context, question):
    return (
        "Answer the question using the context below. "
        "Reply with ONLY the short answer (a few words), no explanation.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )

"""Question-aware compression: rank paragraphs by relevance to the question, keep the best ones,
then LLMLingua-2 squeezes them into the SAME token budget the plain compress.py used per question.

Usage: python compress_qa.py              (all ratios, writes compressed_qa.json)
       python compress_qa.py expand=2     (keep paragraphs worth 2x the budget before LLMLingua)
       python compress_qa.py mode=sent    (pick the best sentences instead of whole paragraphs)
       python compress_qa.py mode=auto    (paragraphs at 2x, sentences from 5x up: best answer recall)

expand=1 was best for answer recall (tried 1, 1.5, 2, 3): keep fewer paragraphs, cut them less.
Other scripts can call compress_question_aware() directly (see pipeline.py).
"""
import json
import os
import re
import sys

import tiktoken

from config import COMPRESSION_RATIOS
from metrics import normalize

SENT_PARAS = 4                     # sentence mode looks inside this many top-ranked paragraphs
PARA_BONUS = [0.3, 0.3, 0.1, 0.0]  # small preference for sentences from the best paragraphs
BRIDGE_BOOST = 3.0    # reranker scores are 0-1, so a bridge paragraph always ranks second

enc = tiktoken.encoding_for_model("gpt-3.5-turbo")   # same tokenizer LLMLingua reports counts in
_models = {}


def models():
    """Reranker and LLMLingua-2, loaded once on first use (they take a while on CPU)."""
    if not _models:
        from llmlingua import PromptCompressor
        from sentence_transformers import CrossEncoder
        _models["reranker"] = CrossEncoder("BAAI/bge-reranker-base")
        _models["compressor"] = PromptCompressor(
            model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
            use_llmlingua2=True,
            device_map="cpu",
        )
    return _models["reranker"], _models["compressor"]


def count_tokens(text):
    return len(enc.encode(text))


def rank_paragraphs(question, paras):
    """Reranker order, plus a HotpotQA bridge hop: a paragraph whose title is mentioned in the
    best paragraph (or that mentions the best paragraph's title) is moved up right behind it."""
    reranker, _ = models()
    scores = list(reranker.predict([(question, p) for p in paras]))
    top = max(range(len(paras)), key=lambda i: scores[i])
    titles = [normalize(p.partition(": ")[0]) for p in paras]
    top_text = normalize(paras[top])
    for i, p in enumerate(paras):
        if i != top and titles[i] and (titles[i] in top_text or titles[top] in normalize(p)):
            scores[i] += BRIDGE_BOOST
    return sorted(range(len(paras)), key=lambda i: -scores[i])


def split_sentences(text):
    return [x for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", text) if x.strip()]


def select_sentences(question, paras, order, budget):
    """Best sentences (scored with their paragraph title) from the top paragraphs, until the
    budget is reached; regrouped under their titles in paragraph-rank order."""
    reranker, _ = models()
    cands = []
    for rank, j in enumerate(order[:SENT_PARAS]):
        title, _, body = paras[j].partition(": ")
        for k, sent in enumerate(split_sentences(body)):
            cands.append((rank, k, title, sent))
    scores = reranker.predict([(question, f"{t}: {s}") for _, _, t, s in cands])
    best = sorted(range(len(cands)), key=lambda i: -(scores[i] + PARA_BONUS[cands[i][0]]))
    picked, used = [], 0
    for i in best:
        if used >= budget and picked:
            break
        picked.append(cands[i])
        used += count_tokens(cands[i][3]) + 3
    groups = {}
    for rank, k, title, sent in sorted(picked):
        groups.setdefault((rank, title), []).append(sent)
    return ["{}: {}".format(t, " ".join(ss)) for (_, t), ss in groups.items()]


def compress_question_aware(context, question, budget, mode="para", expand=1.0, order=None):
    """Compress a context of "Title: text" paragraphs (separated by blank lines) to `budget` tokens.
    Returns (compressed text, number of paragraphs or sentence groups kept)."""
    _, compressor = models()
    paras = context.split("\n\n")
    if order is None:
        order = rank_paragraphs(question, paras)
    chosen, used = [], 0
    if mode == "sent":
        chosen = select_sentences(question, paras, order, budget)
    else:
        for j in order:
            if used >= budget * expand and len(chosen) >= 2:
                break
            chosen.append(paras[j])
            used += count_tokens(paras[j])
    text = "\n\n".join(chosen)
    if count_tokens(text) > budget:
        text = compressor.compress_prompt(
            text,
            target_token=budget,
            force_tokens=["\n"],
            drop_consecutive=True,
        )["compressed_prompt"]
    return text, len(chosen)


if __name__ == "__main__":
    EXPAND = 1.0          # select paragraphs worth this many times the budget, then compress
    MODE = "para"         # "para": whole paragraphs, "sent": best sentences, "auto": sent from 5x up
    for arg in sys.argv[1:]:
        if arg.startswith("expand="):
            EXPAND = float(arg[len("expand="):])
        elif arg.startswith("mode="):
            MODE = arg[len("mode="):]
    if len(sys.argv) == 1:
        OUT = "compressed_qa.json"
    elif MODE in ("sent", "auto"):
        OUT = f"compressed_qa_{MODE}.json"
    else:
        OUT = f"compressed_qa_expand{EXPAND:g}.json"

    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
    with open("compressed.json", encoding="utf-8") as f:
        plain = {ratio: {r["id"]: r for r in rows} for ratio, rows in json.load(f).items()}

    done = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            done = json.load(f)

    orders = {item["id"]: rank_paragraphs(item["question"], item["context"].split("\n\n")) for item in data}
    print("Paragraphs ranked.")

    for ratio in COMPRESSION_RATIOS:
        key = str(ratio)
        if key in done:
            print(f"{ratio}x already done, skipping")
            continue

        rows = []
        for i, item in enumerate(data, 1):
            budget = plain[key][item["id"]]["compressed_tokens"]   # match plain compression exactly
            mode = "sent" if MODE == "sent" or (MODE == "auto" and ratio >= 5) else "para"
            text, kept = compress_question_aware(item["context"], item["question"], budget,
                                                 mode=mode, expand=EXPAND, order=orders[item["id"]])
            rows.append({
                "id": item["id"],
                "context": text,
                "origin_tokens": count_tokens(item["context"]),
                "compressed_tokens": count_tokens(text),
                "paragraphs_kept": kept,
            })
            if i % 10 == 0:
                print(f"  {ratio}x: {i}/{len(data)}")

        done[key] = rows
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(done, f, ensure_ascii=False, indent=2)

        orig = sum(r["origin_tokens"] for r in rows)
        comp = sum(r["compressed_tokens"] for r in rows)
        print(f"{ratio}x done. Actual ratio: {orig / comp:.1f}x")

    print("All compression finished. Saved to", OUT)

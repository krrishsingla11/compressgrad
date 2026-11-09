"""Middleware: compress a context for a question, answer from it, optionally repair the answer.

    from pipeline import compress_and_answer
    out = compress_and_answer(context, question, ratio=10)
    out["final"], out["tokens_full"], out["tokens_compressed"]

`context` is paragraphs separated by blank lines, ideally "Title: text" like HotpotQA.
Repair is off by default: cost_analysis.py shows it re-sends more prompt tokens than the full
context would, so question-aware compression alone is the cheaper way to keep accuracy.
"""
from compress_qa import compress_question_aware, count_tokens
from config import ANSWER_MODEL
from utils import ask, build_prompt, final_answer


def compress_and_answer(context, question, ratio=5, budget=None, mode="para", use_repair=False):
    tokens_full = count_tokens(context)
    if budget is None:
        budget = max(1, round(tokens_full / ratio))
    compressed, _ = compress_question_aware(context, question, budget, mode=mode)
    draft = final_answer(ask(build_prompt(compressed, question), ANSWER_MODEL)["text"])
    final = draft
    if use_repair:
        import repair                 # loads TextGrad only when repair is wanted
        final, _, _ = repair.repair_answer(question, compressed, draft)
    return {
        "compressed": compressed,
        "tokens_full": tokens_full,
        "tokens_compressed": count_tokens(compressed),
        "draft": draft,
        "final": final,
    }


def compress_and_repair(context, question, ratio=5, budget=None, mode="para"):
    """Compression followed by TextGrad repair (v2), as described in the report."""
    return compress_and_answer(context, question, ratio, budget, mode, use_repair=True)

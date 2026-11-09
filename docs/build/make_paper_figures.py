"""Figures for the paper, report and slides (docs/figures/). Run from the repository root:
    python docs/build/make_paper_figures.py
Reads the result files; the repair-cost numbers are the output of cost_analysis.py.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, ".")
from metrics import clean_answer, exact_match, f1_score, normalize  # noqa: E402

OUT = "docs/figures"
NAVY, RED, GREY, GREEN, ORANGE = "#1f4e79", "#c0504d", "#a6a6a6", "#4e9a4e", "#d08a2a"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman"], "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})
LEVELS = ["2", "5", "10", "20"]


def scores(rows):
    n = len(rows)
    preds = [clean_answer(r["pred"]) for r in rows]
    return (sum(exact_match(p, r["gold"]) for p, r in zip(preds, rows)) / n,
            sum(f1_score(p, r["gold"]) for p, r in zip(preds, rows)) / n)


base = json.load(open("results_baseline.json", encoding="utf-8"))
plain = json.load(open("results_compressed.json", encoding="utf-8"))
qa = json.load(open("results_qa_promptv1.json", encoding="utf-8"))
b_em, b_f1 = scores(base["rows"])
p = {k: scores(plain["rows"][k]) for k in LEVELS}
q = {k: scores(qa["rows"][k]) for k in LEVELS}
p_tok = {str(s["ratio"]): s["avg_prompt_tokens"] for s in plain["summaries"]}
q_tok = {str(s["ratio"]): s["avg_prompt_tokens"] for s in qa["summaries"]}
B_TOK = base["summary"]["avg_prompt_tokens"]

# ---- accuracy vs compression, plain vs question-aware ----
fig, ax = plt.subplots(figsize=(3.4, 2.4))
x = ["None"] + [f"{k}×" for k in LEVELS]
ax.plot(x, [b_f1] + [p[k][1] for k in LEVELS], "-o", color=GREY, ms=4, label="F1, plain LLMLingua-2")
ax.plot(x, [b_em] + [p[k][0] for k in LEVELS], "--s", color=GREY, ms=3.5, label="EM, plain")
ax.plot(x, [b_f1] + [q[k][1] for k in LEVELS], "-o", color=NAVY, ms=4, label="F1, question-aware")
ax.plot(x, [b_em] + [q[k][0] for k in LEVELS], "--s", color=RED, ms=3.5, label="EM, question-aware")
for i, k in enumerate(LEVELS, 1):
    ax.annotate(f"{q[k][1]:.2f}", (i, q[k][1]), textcoords="offset points", xytext=(0, 5), ha="center", fontsize=7)
ax.set_ylim(0, 0.85)
ax.set_ylabel("Score")
ax.set_xlabel("Compression level (context)")
ax.grid(alpha=0.25)
ax.legend(fontsize=6.5, loc="lower left", frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_accuracy_qa.png", dpi=300)
plt.close(fig)

# ---- token cost vs F1 ----
fig, ax = plt.subplots(figsize=(3.4, 2.4))
for lbl, pts, tok, col, mk in [("Plain LLMLingua-2", p, p_tok, GREY, "o"), ("Question-aware", q, q_tok, NAVY, "s")]:
    order = LEVELS[::-1]                     # 20x, 10x, 5x, 2x, then uncompressed: left to right
    xs = [tok[k] for k in order] + [B_TOK]
    ys = [pts[k][1] for k in order] + [b_f1]
    ax.plot(xs, ys, "-" + mk, color=col, ms=4, label=lbl)
    for k in LEVELS:
        ax.annotate(f"{k}×", (tok[k], pts[k][1]), textcoords="offset points", xytext=(4, -9 if col == GREY else 4),
                    fontsize=7)
ax.annotate("uncompressed", (B_TOK, b_f1), textcoords="offset points", xytext=(-48, 6), fontsize=7)
ax.set_xlabel("Average prompt tokens (answer call)")
ax.set_ylabel("F1")
ax.set_ylim(0.25, 0.8)
ax.grid(alpha=0.25)
ax.legend(fontsize=7, loc="lower right", frameon=False)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_tokens_qa.png", dpi=300)
plt.close(fig)

# ---- answer recall ----
data = {d["id"]: d for d in json.load(open("data.json", encoding="utf-8"))}
ids = [i for i, d in data.items() if normalize(d["answer"]) not in ("yes", "no")]


def recall(path):
    comp = json.load(open(path, encoding="utf-8"))
    out = {}
    for k in LEVELS:
        rows = {r["id"]: r["context"] for r in comp[k]}
        out[k] = 100 * sum(normalize(data[i]["answer"]) in normalize(rows[i]) for i in ids) / len(ids)
    return out


rec = [("Plain LLMLingua-2", recall("compressed.json"), GREY),
       ("Question-aware (paragraphs)", recall("compressed_qa.json"), NAVY),
       ("Question-aware (sentences, 5×+)", recall("compressed_qa_auto.json"), RED)]
fig, ax = plt.subplots(figsize=(3.4, 2.4))
w = 0.26
for j, (lbl, r, col) in enumerate(rec):
    xs = [i + (j - 1) * w for i in range(len(LEVELS))]
    bars = ax.bar(xs, [r[k] for k in LEVELS], w, color=col, label=lbl)
    for bx, k in zip(xs, LEVELS):
        ax.text(bx, r[k] + 1.5, f"{r[k]:.0f}", ha="center", fontsize=6)
ax.set_xticks(range(len(LEVELS)), [f"{k}×" for k in LEVELS])
ax.set_ylabel("Gold answer kept in context (%)")
ax.set_ylim(0, 135)
ax.set_yticks(range(0, 101, 20))
ax.legend(fontsize=6.5, loc="upper left", frameon=False, ncol=2, bbox_to_anchor=(0.02, 1.0))
fig.tight_layout()
fig.savefig(f"{OUT}/fig_recall.png", dpi=300)
plt.close(fig)

# ---- repair token cost (cost_analysis.py, prompt tokens per question) ----
COST = [  # label, answer-call tokens, judge tokens; v2 = n-weighted mean of the three question sets
    ("v2 5×", 385, 1762), ("v2 10×", 251, 1630), ("v2 20×", 181, 1402),
    ("v3 QA 5×", 390, 3276), ("v3 QA 10×", 253, 1297), ("v3 QA 20×", 184, 1423),
]
fig, ax = plt.subplots(figsize=(3.4, 2.4))
labels = [c[0].replace(" ", "\n", 1) for c in COST]
ax.bar(labels, [c[1] for c in COST], color=NAVY, label="Answer call")
ax.bar(labels, [c[2] for c in COST], bottom=[c[1] for c in COST], color=ORANGE, label="Judge + optimizer calls")
ax.axhline(B_TOK, color=RED, ls="--", lw=1)
ax.text(-0.4, B_TOK + 70, f"uncompressed prompt alone ({B_TOK})", color=RED, ha="left", fontsize=7,
        bbox=dict(fc="white", ec="none", pad=0.5))
ax.set_ylabel("Prompt tokens per question")
ax.tick_params(axis="x", labelsize=7)
ax.set_ylim(0, 4300)
ax.legend(fontsize=7, loc="upper left", frameon=False, ncol=2)
fig.tight_layout()
fig.savefig(f"{OUT}/fig_repair_cost.png", dpi=300)
plt.close(fig)

# ---- pipeline diagram ----
fig, ax = plt.subplots(figsize=(3.4, 3.9))
ax.set_xlim(0, 10)
ax.set_ylim(0, 11.6)
ax.axis("off")


def box(x, y, w, h, text, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.25", fc=fc, ec=ec, lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.2)


def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color="#333333", lw=0.9))


box(1.5, 10.2, 7, 1.0, "HotpotQA question + 10 paragraphs\n(~1.4k tokens)", "#eef2f7", "#44546a")
box(0.2, 7.9, 4.5, 1.5, "Plain LLMLingua-2:\nkeep 1/r of\nthe tokens", "#f2f2f2", "#7f7f7f")
box(5.3, 7.9, 4.5, 1.5, "Question-aware:\nrerank paragraphs,\nthen LLMLingua-2", "#e8f0e6", "#4e7a3e")
box(1.5, 5.9, 7, 1.0, "Answer model (gpt-oss-20b) → draft answer", "#e8f0e6", "#4e7a3e")
box(1.5, 3.5, 7, 1.5, "Optional TextGrad repair:\njudge (gpt-oss-120b) sees the compressed\ncontext and draft, never the gold answer", "#fdf0dc", "#c07a1a")
box(1.5, 1.3, 7, 1.3, "Scoring: EM / F1 against gold,\npaired tests, token cost", "#eef2f7", "#44546a")
arrow(3.5, 10.2, 2.45, 9.48)
arrow(6.5, 10.2, 7.55, 9.48)
arrow(2.45, 7.9, 4.0, 6.98)
arrow(7.55, 7.9, 6.0, 6.98)
arrow(5.0, 5.9, 5.0, 5.08)
arrow(5.0, 3.5, 5.0, 2.68)
fig.savefig(f"{OUT}/fig_pipeline.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print("Figures written to", os.path.abspath(OUT))
print(f"baseline EM {b_em:.3f} F1 {b_f1:.3f};", {k: (round(p[k][1], 3), round(q[k][1], 3)) for k in LEVELS})

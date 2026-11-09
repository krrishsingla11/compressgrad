import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from metrics import clean_answer, exact_match, f1_score


def rescored(summary, rows):
    """Summary with EM/F1 recomputed under the same answer cleanup, so old and new runs compare fairly."""
    preds = [clean_answer(r["pred"]) for r in rows]
    n = len(rows)
    return {**summary,
            "exact_match": sum(exact_match(p, r["gold"]) for p, r in zip(preds, rows)) / n,
            "f1": sum(f1_score(p, r["gold"]) for p, r in zip(preds, rows)) / n}


def load_compressed(path):
    try:
        with open(path, encoding="utf-8") as f:
            res = json.load(f)
    except FileNotFoundError:
        return []
    return [rescored(s, res["rows"][str(s["ratio"])]) for s in res["summaries"]]


with open("results_baseline.json", encoding="utf-8") as f:
    res = json.load(f)
    base = rescored(res["summary"], res["rows"])
comp = load_compressed("results_compressed.json")
comp_qa = load_compressed("results_qa_promptv1.json")   # question-aware compression
# Repair summaries: label -> {ratio: summary row}. Missing files are skipped.
REPAIR_FILES = [
    ("Repaired (v1)", "repair_summary.json"),
    ("Repaired (v2)", "repair_v2_summary.json"),
    ("Repaired (v3, fresh Qs)", "repair_v3_final_summary.json"),
    ("Repaired (v3, QA-aware ctx)", "repair_v3_final_qa_summary.json"),
]
reps = {}
for label, path in REPAIR_FILES:
    try:
        with open(path, encoding="utf-8") as f:
            reps[label] = {r["ratio"]: r for r in json.load(f)}
    except FileNotFoundError:
        pass

# ---- Plot 1: accuracy vs compression level (all 100 questions) ----
labels = ["None"] + [f"{c['ratio']}x" for c in comp]
f1 = [base["f1"]] + [c["f1"] for c in comp]
em = [base["exact_match"]] + [c["exact_match"] for c in comp]
plt.figure(figsize=(6, 4))
plt.plot(labels, f1, marker="o", color="C0", label="F1 (plain LLMLingua-2)")
plt.plot(labels, em, marker="s", color="C1", label="EM (plain LLMLingua-2)")
if comp_qa:
    plt.plot(labels, [base["f1"]] + [c["f1"] for c in comp_qa], marker="o", ls="--", color="C0",
             label="F1 (question-aware)")
    plt.plot(labels, [base["exact_match"]] + [c["exact_match"] for c in comp_qa], marker="s", ls="--",
             color="C1", label="EM (question-aware)")
plt.ylim(0, 1)
plt.xlabel("Compression level")
plt.ylabel("Score")
plt.title("Accuracy vs compression (n=%d)" % base["n"])
plt.legend(fontsize=8)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot1_accuracy_vs_compression.png", dpi=200)
plt.close()

# ---- Plot 2: uncompressed vs compressed vs repaired, per repair version ----
# Each version was run on its own question set, so each gets its own baseline/compressed bars.
if reps:
    fig, axes = plt.subplots(1, len(reps), figsize=(4.5 * len(reps), 4), sharey=True, squeeze=False)
    for ax, (label, rep) in zip(axes[0], reps.items()):
        ratios = sorted(rep)
        x = range(len(ratios))
        w = 0.27
        ax.bar([i - w for i in x], [rep[r]["baseline_f1"] for r in ratios], w, label="Uncompressed")
        ax.bar(list(x), [rep[r]["compressed_f1"] for r in ratios], w, label="Compressed only")
        ax.bar([i + w for i in x], [rep[r]["repaired_f1"] for r in ratios], w, label="Repaired")
        ax.set_xticks(list(x), [f"{r}x (n={rep[r]['n']})" for r in ratios])
        ax.set_title(label)
        ax.set_ylim(0, 1)
        ax.grid(axis="y", alpha=0.3)
    axes[0][0].set_ylabel("F1")
    handles, names = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=3)
    fig.suptitle("TextGrad repair vs compressed-only")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig("plot2_repair_comparison.png", dpi=200)
    plt.close(fig)

    # ---- Plot 3: recovery % by compression level, one bar group per version ----
    all_ratios = sorted({r for rep in reps.values() for r in rep})
    w = 0.8 / len(reps)
    plt.figure(figsize=(6.5, 4))
    for j, (label, rep) in enumerate(reps.items()):
        xs = [i + (j - (len(reps) - 1) / 2) * w for i in range(len(all_ratios))]
        plt.bar(xs, [(rep.get(r, {}).get("recovery_percent") or 0) for r in all_ratios], w, label=label)
    plt.xticks(range(len(all_ratios)), [f"{r}x" for r in all_ratios])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Accuracy recovered (%)")
    plt.xlabel("Compression level")
    plt.title("How much lost F1 the repair wins back")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("plot3_recovery.png", dpi=200)
    plt.close()

# ---- Plot 4: token cost vs accuracy ----
plt.figure(figsize=(6, 4))
series = [("Plain LLMLingua-2", comp, "-")] + ([("Question-aware", comp_qa, "--")] if comp_qa else [])
for name, rows, ls in series:
    toks = [base["avg_prompt_tokens"]] + [c["avg_prompt_tokens"] for c in rows]
    vals = [base["f1"]] + [c["f1"] for c in rows]
    plt.plot(toks, vals, marker="o", ls=ls, label=name)
    for t, v, l in zip(toks[1:], vals[1:], labels[1:]):
        plt.annotate(l, (t, v), textcoords="offset points", xytext=(5, 5), fontsize=8)
plt.annotate("None", (base["avg_prompt_tokens"], base["f1"]), textcoords="offset points", xytext=(-30, 5))
plt.xlabel("Average prompt tokens")
plt.ylabel("F1")
plt.ylim(0, 1)
plt.title("Token cost vs accuracy")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot4_tokens_vs_accuracy.png", dpi=200)
plt.close()

print("Saved plot images in this folder.")

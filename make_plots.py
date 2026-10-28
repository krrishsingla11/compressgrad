import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("results_baseline.json", encoding="utf-8") as f:
    base = json.load(f)["summary"]
with open("results_compressed.json", encoding="utf-8") as f:
    comp = json.load(f)["summaries"]
try:
    with open("repair_summary.json", encoding="utf-8") as f:
        rep = json.load(f)
except FileNotFoundError:
    rep = []
try:
    with open("repair_v2_summary.json", encoding="utf-8") as f:
        rep2 = {r["ratio"]: r for r in json.load(f)}
except FileNotFoundError:
    rep2 = {}

# ---- Plot 1: accuracy vs compression level (all 100 questions) ----
labels = ["None"] + [f"{c['ratio']}x" for c in comp]
f1 = [base["f1"]] + [c["f1"] for c in comp]
em = [base["exact_match"]] + [c["exact_match"] for c in comp]
plt.figure(figsize=(6, 4))
plt.plot(labels, f1, marker="o", label="F1")
plt.plot(labels, em, marker="s", label="Exact match")
plt.ylim(0, 1)
plt.xlabel("Compression level")
plt.ylabel("Score")
plt.title("Accuracy vs compression (n=%d)" % base["n"])
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot1_accuracy_vs_compression.png", dpi=200)
plt.close()

# ---- Plot 2: uncompressed vs compressed vs repaired (same questions) ----
if rep:
    x = range(len(rep))
    k = 4 if rep2 else 3
    w = 0.8 / k
    off = [(j - (k - 1) / 2) * w for j in range(k)]
    plt.figure(figsize=(7.5, 4))
    plt.bar([i + off[0] for i in x], [r["baseline_f1"] for r in rep], w, label="Uncompressed")
    plt.bar([i + off[1] for i in x], [r["compressed_f1"] for r in rep], w, label="Compressed only")
    plt.bar([i + off[2] for i in x], [r["repaired_f1"] for r in rep], w, label="Repaired (v1)")
    if rep2:
        plt.bar([i + off[3] for i in x], [rep2.get(r["ratio"], {}).get("repaired_f1", 0) for r in rep], w, label="Repaired (v2)")
    plt.xticks(list(x), [f"{r['ratio']}x (n={r['n']})" for r in rep])
    plt.ylim(0, 1)
    plt.ylabel("F1")
    plt.title("TextGrad repair vs compressed-only")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("plot2_repair_comparison.png", dpi=200)
    plt.close()

    # ---- Plot 3: recovery % by compression level ----
    plt.figure(figsize=(5.5, 4))
    plt.bar([f"{r['ratio']}x" for r in rep], [r["recovery_percent"] or 0 for r in rep])
    plt.ylabel("Accuracy recovered (%)")
    plt.xlabel("Compression level")
    plt.title("How much lost F1 the repair wins back")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig("plot3_recovery.png", dpi=200)
    plt.close()

# ---- Plot 4: token cost vs accuracy ----
plt.figure(figsize=(6, 4))
toks = [base["avg_prompt_tokens"]] + [c["avg_prompt_tokens"] for c in comp]
plt.plot(toks, f1, marker="o")
for t, v, l in zip(toks, f1, labels):
    plt.annotate(l, (t, v), textcoords="offset points", xytext=(5, 5))
plt.xlabel("Average prompt tokens")
plt.ylabel("F1")
plt.ylim(0, 1)
plt.title("Token cost vs accuracy")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("plot4_tokens_vs_accuracy.png", dpi=200)
plt.close()

print("Saved plot images in this folder.")

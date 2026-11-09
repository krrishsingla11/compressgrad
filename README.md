# CompressGrad

**How much accuracy does prompt compression cost, and how do we get it back?**

Long contexts are expensive. LLMLingua-2 can shrink them 2–20x, but the answer model then gets
more questions wrong. CompressGrad measures that trade-off on HotpotQA and tests two ways to win
the accuracy back:

1. **TextGrad repair**: a stronger judge model reads the *same compressed* context, critiques the
   draft answer and rewrites it. It never sees the gold answer.
2. **Question-aware compression**: rank the paragraphs by relevance to the question *before*
   LLMLingua-2 compresses them, with the same token budget.

## Key findings

| | 2x | 5x | 10x | 20x |
|---|---|---|---|---|
| F1, plain LLMLingua-2 (n = 100) | 0.676 | 0.483 | 0.410 | 0.333 |
| F1, question-aware compression (n = 100) | **0.727** | **0.691** | **0.681** | **0.555** |
| Exact match, plain → question-aware | 0.51 → 0.56 | 0.35 → 0.51 | 0.32 → 0.53 | 0.24 → 0.41 |
| McNemar p (exact match, paired) | 0.23 | 0.0004 | < 0.0001 | 0.0005 |
| Avg prompt tokens (uncompressed: 1452) | 758 | 381 | 249 | 181 |

Uncompressed: EM 0.56, F1 0.740 (same answer cleanup applied everywhere).

- **Question-aware compression is the main win.** At 10x it keeps 92% of the uncompressed F1 with
  17% of the prompt tokens, and its exact match (0.53) equals the uncompressed baseline before cleanup.
- **TextGrad repair helps plain compression** (v2, pooled 90 questions: +0.105 F1 at 5x,
  +0.114 at 10x, 95% bootstrap ranges exclude zero), **but costs more tokens than it saves**:
  replaying every stored repair (`cost_analysis.py`) shows answer + judge calls use 107–252% of the
  tokens of just sending the full context, and the judge is the larger model.
- On question-aware contexts there is little left to repair (no significant change on 30 fresh questions).

Write-ups: [IEEE paper](docs/CompressGrad_IEEE_Paper.pdf) and [project report](docs/CompressGrad_Final_Report.docx)
(regenerate with the scripts in [docs/build/](docs/build/)).

## Pipeline

```
HotpotQA (distractor, 100 Qs)
   │
   ├─► compress.py     plain LLMLingua-2 (2x/5x/10x/20x)
   └─► compress_qa.py  reranker + bridge hop → LLMLingua-2, same token budget
           │
           ▼
   gpt-oss-20b answers ──► (optional) TextGrad repair with a gpt-oss-120b judge
           │
           ▼
   EM / F1, paired significance tests, bootstrap ranges, token cost
```

| Step | Script | Output |
|---|---|---|
| Sample 100 questions | `prepare_data.py` | `data.json` |
| Answer with full context | `baseline.py` | `results_baseline.json` |
| Compress (plain / question-aware) | `compress.py` / `compress_qa.py [mode=auto]` | `compressed.json` / `compressed_qa.json` |
| Answer from compressed context | `eval_compressed.py [file]` | `results_compressed.json`, `results_<file>` |
| Repair with TextGrad | `repair.py [v2\|v3] [heldout\|final] [qa] [ratios=5,10]` | `repair*_results.jsonl`, `repair*_summary.json` |
| Answer recall of contexts (offline) | `context_recall.py file...` | printed |
| Compare two result files (paired tests) | `compare_results.py old new` | printed |
| Repair analysis | `analyze_repair.py [v2\|v3] [heldout\|final\|all] [qa]` | printed |
| Repair token cost (offline replay) | `cost_analysis.py` | printed |
| Figures | `make_plots.py` | `plot*.png` |
| Middleware / demo | `pipeline.py` / `demo.py --id 8 --ratio 10` | printed |

Models, sample sizes, prompt version and answer cleanup are set in [config.py](config.py).
Scoring and statistics live in [metrics.py](metrics.py) (no API libraries needed).

## How question-aware compression works

1. Split the context into its ten "Title: text" paragraphs.
2. Score each paragraph against the question with `BAAI/bge-reranker-base`.
3. **Bridge hop** (HotpotQA questions need two paragraphs): a paragraph whose title appears in the
   best paragraph, or that mentions the best paragraph's title, moves up behind it.
4. Keep paragraphs in that order until the token budget is reached, then let LLMLingua-2 trim
   them to exactly the budget plain compression used for that question.

The gold answer survives in the compressed text far more often (answer recall, 96 non yes/no questions):
2x 82% → 98%, 5x 46% → 86%, 10x 32% → 77%, 20x 9% → 48%. `mode=auto` (pick sentences instead of
paragraphs from 5x up) raises recall further to 91% / 79% / 56%; its EM/F1 run is not finished
(Groq daily limit), so paragraph mode is the default.

## TextGrad repair

- **v1**: plain critique + rewrite. Did not help; pushed answers to "unknown" and edited correct ones.
- **v2**: never answer "unknown", keep drafts the judge accepts, keep the short form. Final method.
- **v3**: v2 + change only when the context clearly supports it, two rounds. Ablation.

| Ratio | Plain | Plain + repair v2 (n = 90) | QA-aware (Q61–90) | QA-aware + repair v3 (Q61–90) |
|---|---|---|---|---|
| 5x | 0.475 | 0.580 | 0.658 | 0.709 |
| 10x | 0.420 | 0.534 | 0.727 | 0.722 |
| 20x | 0.392 (n = 60) | 0.419 | 0.541 | 0.616 |

Repair token cost (prompt tokens per question, answer call + all judge calls, from `cost_analysis.py`):
about 1,550–2,650 for v2 on plain contexts and 1,550–3,670 for v3 on question-aware contexts,
against 1,452 for the uncompressed prompt alone.

## Setup

```bash
python -m venv venv
venv\Scripts\activate            # Windows  (source venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
set GROQ_API_KEY=your-key-here   # export on Linux/macOS
```

Every LLM call is cached in `cache.jsonl`: re-running a script costs nothing, resumes after Groq's
daily limit, and `demo.py`, `cost_analysis.py` and all analysis scripts run offline.
Tests for the scoring code: `python -m pytest test_metrics.py`.

## Notes

- Scoring is the standard SQuAD/HotpotQA normalised exact match and token F1. Replies are tidied
  before scoring (`CLEAN_ANSWERS`, gold-blind: drops "(RAF)"-style asides, trailing periods).
- A stricter "copy the exact span" prompt (`PROMPT_VERSION = "v2"`) did not help (4 fixed, 5 broken),
  so the original prompt is the default.
- Empty model replies (gpt-oss can spend the whole budget on reasoning) are retried with a larger
  budget instead of being cached and scored as wrong.
- `test_compress.py` and `test_textgrad.py` are quick smoke tests for LLMLingua and TextGrad.

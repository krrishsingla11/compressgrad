"""Builds docs/CompressGrad_IEEE_Paper.pdf (IEEE conference layout: US Letter, two columns,
Times 10 pt). Run from the repository root after make_paper_figures.py:
    python docs/build/build_paper.py
"""
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, FrameBreak, Image, KeepTogether,
                                PageTemplate, Paragraph, Preformatted, Spacer, Table, TableStyle)

FONTS = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("TNR", FONTS + "times.ttf"))
pdfmetrics.registerFont(TTFont("TNR-B", FONTS + "timesbd.ttf"))
pdfmetrics.registerFont(TTFont("TNR-I", FONTS + "timesi.ttf"))
pdfmetrics.registerFont(TTFont("TNR-BI", FONTS + "timesbi.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONTS + "cour.ttf"))
pdfmetrics.registerFont(TTFont("Sym", FONTS + "seguisym.ttf"))
pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")

OUT = "docs/CompressGrad_IEEE_Paper.pdf"
FIG = "docs/figures/"
PAGE_W, PAGE_H = letter
MARGIN_X, TOP, BOTTOM, GAP = 0.625 * inch, 0.75 * inch, 1.0 * inch, 0.25 * inch
COL_W = (PAGE_W - 2 * MARGIN_X - GAP) / 2
TITLE_H = 2.45 * inch

body = ParagraphStyle("body", fontName="TNR", fontSize=10, leading=11.6, alignment=TA_JUSTIFY,
                      firstLineIndent=0.14 * inch, spaceAfter=0)
body_ni = ParagraphStyle("body_ni", parent=body, firstLineIndent=0)
bullet = ParagraphStyle("bullet", parent=body, firstLineIndent=0, leftIndent=0.2 * inch, bulletIndent=0.07 * inch)
abstract = ParagraphStyle("abs", parent=body, fontName="TNR-B", fontSize=9, leading=10.4, firstLineIndent=0.14 * inch)
h1 = ParagraphStyle("h1", fontName="TNR", fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=8, spaceAfter=4)
h2 = ParagraphStyle("h2", fontName="TNR-I", fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=5, spaceAfter=2)
cap = ParagraphStyle("cap", fontName="TNR", fontSize=8, leading=9.4, alignment=TA_JUSTIFY, spaceBefore=3, spaceAfter=7)
tcap = ParagraphStyle("tcap", fontName="TNR", fontSize=8, leading=9.6, alignment=TA_CENTER, spaceBefore=6, spaceAfter=3)
tnote = ParagraphStyle("tnote", fontName="TNR", fontSize=7, leading=8.2, alignment=TA_JUSTIFY, spaceBefore=2, spaceAfter=7)
cell = ParagraphStyle("cell", fontName="TNR", fontSize=7.5, leading=8.6, alignment=TA_CENTER)
cell_l = ParagraphStyle("cell_l", parent=cell, alignment=TA_LEFT)
ref = ParagraphStyle("ref", fontName="TNR", fontSize=8, leading=9.4, alignment=TA_JUSTIFY, leftIndent=0.25 * inch,
                     firstLineIndent=-0.25 * inch, spaceAfter=2)
code = ParagraphStyle("code", fontName="Mono", fontSize=6.8, leading=8.2)
title_s = ParagraphStyle("title", fontName="TNR", fontSize=21, leading=24, alignment=TA_CENTER)
author_s = ParagraphStyle("author", fontName="TNR", fontSize=9.5, leading=11.5, alignment=TA_CENTER)
affil_s = ParagraphStyle("affil", fontName="TNR-I", fontSize=9, leading=11, alignment=TA_CENTER)


def sc(text, size=10):
    """IEEE small caps: first letter of each word full size, the rest upper case and smaller."""
    small = round(size * 0.8, 1)
    out = []
    for word in text.split(" "):
        if word and word[0].isalpha():
            out.append(word[0].upper() + f'<font size="{small}">{word[1:].upper()}</font>')
        else:
            out.append(word)
    return " ".join(out)


story = []
counters = {"sec": 0, "sub": 0, "fig": 0, "tab": 0}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]


def H1(text, numbered=True):
    counters["sub"] = 0
    if numbered:
        label = ROMAN[counters["sec"]] + ". "
        counters["sec"] += 1
    else:
        label = ""
    story.append(CondPageBreak(0.9 * inch))
    story.append(Paragraph(label + sc(text), h1))


def H2(text):
    label = "ABCDEFGHIJKLMNOP"[counters["sub"]]
    counters["sub"] += 1
    story.append(CondPageBreak(0.6 * inch))
    story.append(Paragraph(f"{label}. {text}", h2))


def P(text, style=body):
    story.append(Paragraph(text, style))


def B(items):
    for it in items:
        story.append(Paragraph(it, bullet, bulletText="\u2022"))


def FIGURE(path, caption, width=COL_W):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    counters["fig"] += 1
    img = Image(path, width=width, height=width * h / w)
    story.append(KeepTogether([Spacer(1, 3), img,
                               Paragraph(f"Fig. {counters['fig']}. {caption}", cap)]))
    return counters["fig"]


def TABLE(title, rows, widths, note=None, left_cols=(0,), header_rows=1):
    counters["tab"] += 1
    data = []
    for r_i, row in enumerate(rows):
        data.append([Paragraph(str(c), cell_l if (c_i in left_cols and r_i >= header_rows) else cell)
                     for c_i, c in enumerate(row)])
    t = Table(data, colWidths=[w * COL_W for w in widths], repeatRows=header_rows)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))
    parts = [Paragraph("TABLE " + ROMAN[counters["tab"] - 1] + "<br/>" + sc(title.lower(), 8), tcap), t]
    if note:
        parts.append(Paragraph(note, tnote))
    else:
        parts.append(Spacer(1, 7))
    story.append(KeepTogether(parts))
    return ROMAN[counters["tab"] - 1]


def ALGO(title, lines):
    t = Table([[Paragraph(f"<b>{title}</b>", ParagraphStyle("at", parent=cell_l, fontSize=8))],
               [Preformatted("\n".join(lines), code)]], colWidths=[COL_W])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
                           ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                           ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
                           ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    story.append(KeepTogether([Spacer(1, 4), t, Spacer(1, 7)]))


def EQ(text, number):
    t = Table([[Paragraph(text, ParagraphStyle("eq", parent=body_ni, alignment=TA_CENTER, fontSize=9.5)),
                Paragraph(f"({number})", ParagraphStyle("eqn", parent=body_ni, alignment=2))]],
              colWidths=[COL_W * 0.88, COL_W * 0.12])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(t)


X = "\u00d7"

# =====================================================================  title block
story.append(Paragraph("CompressGrad: Recovering the Accuracy Lost to Prompt Compression with "
                       "Question-Aware Selection and TextGrad-Guided Repair", title_s))
story.append(Spacer(1, 10))
authors = [("Krrish Singla", "PES1UG24AM141"), ("Kishan K Shenoy", "PES1UG24AM138"),
           ("Leeladhar G Sairaju", "PES1UG24AM148"), ("Mohammad Bilal A", "PES1UG24AM162")]
at = Table([[Paragraph(f"{n}<br/><i>{s}</i>", author_s) for n, s in authors]],
           colWidths=[(PAGE_W - 2 * MARGIN_X) / 4] * 4)
at.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
story.append(at)
story.append(Spacer(1, 6))
story.append(Paragraph("Mini Project, Prompt Engineering and Optimization for Generative AI (UE24AM343AB5)<br/>"
                       "B.Tech Computer Science &amp; Engineering (AI &amp; ML), Semester 5, PES University, "
                       "Bengaluru, India", affil_s))
story.append(FrameBreak())

# =====================================================================  abstract
P("<i>Abstract</i>\u2014Prompt compression methods such as LLMLingua reduce the token cost of long-context "
  "LLM pipelines, but aggressive compression degrades answer quality. On 100 HotpotQA questions, compressing "
  f"the context by 2{X}, 5{X}, 10{X} and 20{X} with LLMLingua-2 lowers F1 from 0.740 (uncompressed, 1,452 "
  "prompt tokens on average) to 0.676, 0.483, 0.410 and 0.333. We test two ways to recover this loss. The "
  "first is a TextGrad repair loop in which a judge model that sees only the compressed context, never the "
  "gold answer, critiques the draft answer and rewrites it. After error analysis exposed two failure modes, "
  f"a revised loop raises F1 by +0.105 at 5{X} and +0.114 at 10{X} over 90 questions, but replaying every "
  "stored call shows that its judge calls use more prompt tokens than sending the uncompressed context. The "
  "second is question-aware compression: an off-the-shelf reranker and a bridge-entity rule choose the "
  "paragraphs before LLMLingua-2 compresses them, under the same per-question token budget. The gold answer "
  f"then survives compression far more often (46% to 86% at 5{X}), and F1 rises to 0.727, 0.691, 0.681 "
  f"and 0.555, with exact-match gains that are significant at 5{X}, 10{X} and 20{X} (McNemar "
  f"p\u00a0\u2264\u00a00.0005). At 10{X} it keeps 92% of the uncompressed F1 with 17% of the prompt "
  "tokens. On question-aware contexts, repair adds no significant further gain. These are pilot results "
  "from one dataset and one model pair.", abstract)
story.append(Spacer(1, 4))
P("<i>Index Terms</i>\u2014prompt compression, LLMLingua, TextGrad, question answering, reranking, "
  "LLM-as-judge, prompt optimization", ParagraphStyle("it", parent=abstract))

# =====================================================================  I. introduction
H1("Introduction")
P("Large language models are increasingly used with long inputs such as documents, retrieved passages and "
  "enterprise records, and both API cost and latency grow with the number of prompt tokens. Prompt "
  "compression methods such as LLMLingua [1], LongLLMLingua [2] and LLMLingua-2 [3] shorten a prompt by "
  "removing tokens that a small model judges to carry little information, and they report large savings with "
  "limited loss on their benchmarks.")
P("The accuracy side of this trade-off is less well mapped. Compression removes words the downstream model "
  "may need, and published results mostly describe compression on its own. Two questions remain open: at what "
  "compression ratio does answer quality fall off, and can part of the lost accuracy be recovered without "
  "sending the full prompt again?")
P("TextGrad [4] offers one way to try. An LLM critiques a variable (here, a draft answer) in natural "
  "language, and this critique, treated as a \u201ctextual gradient,\u201d is used to revise the variable. "
  "The survey we carried out for Review 1 found no work that combines TextGrad with LLMLingua-style "
  "compression, although we cannot rule out that such work exists. A second, cheaper way is to make the "
  "compressor itself look at the question, so that the words the answer needs are less likely to be removed.")
P("We study five research questions. <b>RQ1:</b> How much accuracy does LLMLingua-2 compression cost at "
  f"2{X}, 5{X}, 10{X} and 20{X}? <b>RQ2:</b> Can TextGrad-guided repair, with a judge that never sees the "
  "gold answer, recover part of the lost accuracy? <b>RQ3:</b> At which compression ratio does repair stop "
  "helping? <b>RQ4:</b> Does question-aware selection before compression recover more, at the same token "
  "budget? <b>RQ5:</b> What does repair cost in tokens?")
P("This paper makes six contributions:", body_ni)
B([f"We measure the compression\u2013accuracy curve of LLMLingua-2 on 100 HotpotQA questions at 2{X} to 20{X}.",
   "We build a compression-then-repair pipeline in which a judge that sees only the compressed context guides "
   "TextGrad to revise a draft answer, and explain through error analysis why a first version failed.",
   "We propose a simple question-aware front end (a reranker plus a bridge-entity rule) that keeps the same "
   "per-question token budget as LLMLingua-2 and test it with paired significance tests.",
   "We evaluate repair on question sets not used for design, on both kinds of compressed context.",
   "We measure the token cost of repair by replaying every stored model call.",
   "We report negative results: a stricter answer prompt did not help, and repair does not save tokens."])

# =====================================================================  II. related work
H1("Related Work")
H2("Prompt Compression")
P("LLMLingua [1] uses a small language model to identify and drop unimportant tokens. The compressed prompt "
  "is often hard for people to read but remains usable by the target LLM, and the paper reports compression "
  f"of up to 20{X} with small loss on several benchmarks. LongLLMLingua [2] makes compression question-aware: "
  "a coarse step ranks documents by their relevance to the question and a fine step compresses tokens, and it "
  "reorders documents against the \u201clost in the middle\u201d bias [9]. LLMLingua-2 [3] treats compression "
  "as token classification with a small encoder trained on data distilled from GPT-4, and is reported to be "
  "several times faster than LLMLingua. Selective Context [5] prunes tokens by self-information. LLMLingua-2 "
  "and Selective Context do not look at the question. Our question-aware front end follows the idea of "
  "LongLLMLingua\u2019s coarse step, but uses an off-the-shelf cross-encoder reranker [12] and keeps "
  "LLMLingua-2 for the token step.")
H2("Textual Gradients")
P("TextGrad [4] treats natural-language feedback from an LLM as a gradient and passes it backwards through a "
  "computation graph, with an interface modelled on PyTorch. In TextGrad a Variable holds a piece of text "
  "together with a short description of its role. A TextLoss wraps an evaluation instruction: given a variable, "
  "an LLM writes a critique of it. Calling backward() asks an LLM to turn that critique into feedback that is "
  "stored as the variable\u2019s gradient, and the Textual Gradient Descent (TGD) optimizer prompts an LLM "
  "with the variable, its gradient and optional constraints to produce an improved value. In our pipeline "
  "the only variable is the draft answer.")
H2("LLM-as-Judge and Iterative Refinement")
P("Zheng et al. [6] show that strong LLM judges often agree with human raters but have known biases. In our "
  "system the judge produces feedback rather than the final score: final scoring uses exact match and F1 "
  "against the gold answers. Self-Refine [10] and Reflexion [11] revise outputs with verbal feedback; our "
  "repair loop is a small instance of this family in which the draft comes from a compressed prompt and the "
  "judge sees only the compressed text.")
H2("Positioning")
P("Table I summarizes how this work relates to the methods above.")
CHECK = '<font name="Sym">\u2713</font>'     # Times New Roman has no check-mark glyph
TABLE("Positioning of this work",
      [["Work", "Compresses prompts", "Question-aware", "Repairs with text feedback"],
       ["LLMLingua, LLMLingua-2", CHECK, "\u2013", "\u2013"],
       ["LongLLMLingua", CHECK, CHECK, "\u2013"],
       ["TextGrad, Self-Refine", "\u2013", "\u2013", CHECK],
       ["CompressGrad (this work)", CHECK, CHECK, CHECK]],
      [0.34, 0.19, 0.22, 0.25])

# =====================================================================  III. method
H1("Method")
H2("Pipeline Overview")
P("Given a context C and a question q, a compressor returns a shorter context C<sub>r</sub> with roughly "
  "|C|/r tokens. The answer model produces a draft answer a<sub>0</sub> from (C<sub>r</sub>, q). An optional "
  "repair step produces a revised answer a* from (C<sub>r</sub>, q, a<sub>0</sub>). Only the context is "
  "compressed; the instruction and the question are left intact. Fig. 1 shows the pipeline. Nothing from the "
  "gold answers is available to the compressor, the answer model or the judge, so every step could be applied "
  "to new questions in the same way.")
FIGURE(FIG + "fig_pipeline.png", "The CompressGrad pipeline. Both compressors produce the same number of "
       "tokens per question. The judge never receives the gold answer.", width=COL_W * 0.92)
H2("Plain Compression")
P("We use LLMLingua-2 through the llmlingua Python package with the llmlingua-2-xlm-roberta-large-meetingbank "
  "model. It labels each token as keep or drop with a bidirectional encoder and keeps the tokens with the "
  "highest keep probability until the budget is reached, preserving word order. For a ratio r the keep rate "
  "is 1/r; newlines are forced to be kept and consecutive duplicates are dropped. LLMLingua-2 sees the "
  "context only, so it spends the budget on the eight distractor paragraphs of a HotpotQA question as much as "
  "on the two that matter.")
H2("Question-Aware Compression")
P("Our front end works on the ten \u201cTitle: text\u201d paragraphs of a context (Algorithm 1). A "
  "cross-encoder reranker, BAAI/bge-reranker-base [12], scores each paragraph against the question. HotpotQA "
  "questions need two paragraphs, and the second (the bridge) often shares few words with the question, so a "
  "bridge rule moves up any paragraph whose title is mentioned in the best paragraph, or that mentions the "
  "best paragraph\u2019s title. Paragraphs are then taken in rank order until their length reaches the "
  "budget, and LLMLingua-2 trims them to exactly the number of tokens that plain compression used for the "
  "same question, so the two compressors are compared at equal cost. We tried keeping paragraphs worth 1, "
  "1.5, 2 and 3 times the budget before trimming; 1 was best for every ratio, which means it is better to "
  "keep fewer paragraphs and cut them less. A sentence-level variant picks the best sentences from the top "
  "four paragraphs instead.")
ALGO("Algorithm 1: Question-aware compression of one context",
     ["Input: paragraphs p1..p10, question q, budget T",
      " 1: s_i <- reranker(q, p_i)        for each i",
      " 2: t <- argmax_i s_i",
      " 3: for i != t:",
      " 4:   if title(p_i) in p_t or title(p_t) in p_i:",
      " 5:     s_i <- s_i + 3              # bridge hop",
      " 6: K <- [] ; take p_i by decreasing s_i",
      " 7:   until tokens(K) >= T and |K| >= 2",
      " 8: if tokens(K) > T: K <- LLMLingua2(K, T)",
      " 9: return K"])
H2("TextGrad Repair Loop")
P("The draft answer is a TextGrad Variable with gradients enabled. A TextLoss is built from a fixed evaluation "
  "instruction that contains the question and the compressed context; it asks the judge whether the draft is "
  "supported by the context, answers exactly what the question asks, and is short. backward() makes the judge "
  "write feedback on the variable, and the TGD step rewrites the answer using that feedback. The judge and "
  "optimizer share one model and never see the gold answer or the original context. We evaluate three "
  "versions (Algorithm 2).")
P("<b>v1</b> uses the evaluation instruction above and one repair round. <b>v2</b> adds three rules: (i) never "
  "answer \u201cunknown\u201d or \u201cnot stated\u201d; (ii) if the draft is correct, reply \u201cThe draft "
  "answer is correct.\u201d, which stops the loop and keeps the draft; (iii) keep the short answer form. A "
  "guard also keeps the draft if the final answer still abstains; it never fired. <b>v3</b> adds to v2 that "
  "the judge may only change the draft when the context clearly supports another answer, and that a new answer "
  "must use words from the context, and it runs two rounds.")
ALGO("Algorithm 2: Repair of one answer (v2)",
     ["Input: question q, compressed context Cr,",
      "       draft a0, judge/optimizer model J",
      " 1: a <- Variable(a0, requires_grad=True)",
      " 2: L <- TextLoss(instruction(q, Cr), J)",
      " 3: for round = 1 .. R:",
      " 4:   fb <- L(a)          # judge reads a",
      " 5:   if fb says draft is correct: break",
      " 6:   fb.backward()       # textual gradient",
      " 7:   TGD.step()          # J rewrites a",
      " 8: if a contains an abstention phrase:",
      " 9:   a <- a0             # guard",
      "10: return a"])
H2("Metrics and Statistics")
P("We use exact match (EM) and token-level F1 after the standard normalization (lower case, no punctuation, "
  "no articles, collapsed spaces). Before scoring, a gold-blind cleanup removes an \u201cAnswer:\u201d "
  "prefix, text after the first line, bracketed asides such as \u201c(RAF)\u201d and stray periods; applied "
  "to the stored predictions it changed the uncompressed EM from 0.53 to 0.56 and never lowered a score at "
  f"2{X}, 10{X} or 20{X}. All comparisons in this paper use the same scoring on both sides. The share of "
  "lost accuracy that repair wins back is")
EQ("Recovery = (F1<sub>rep.</sub> \u2212 F1<sub>comp.</sub>) / (F1<sub>full</sub> \u2212 F1<sub>comp.</sub>)", 1)
P("computed on the same questions, and only reported when at least 0.05 F1 was lost. To compare two "
  "conditions on the same questions we count the questions each one wins and use an exact two-sided sign "
  "test; on exact match this is McNemar\u2019s exact test [13]. For repair we also report a 95% paired "
  "bootstrap range of the mean F1 change (5,000 resamples). As a cheap check that needs no model calls, "
  "<i>answer recall</i> is the share of non yes/no questions whose normalized gold answer still appears in "
  "the compressed context.", body_ni)
H2("Middleware and Demo")
P("pipeline.py provides compress_and_answer(context, question, ratio) and compress_and_repair(...), which "
  "compress the context with the question-aware front end, answer from it, optionally apply repair v2, and "
  "return the compressed context, the token counts, the draft and the final answer. demo.py prints the "
  "answers from the full context, from plain LLMLingua-2 and from question-aware compression side by side, "
  "with F1 when a gold answer is known; on sample questions it runs from the cache without API calls.")

# =====================================================================  IV. setup
H1("Experimental Setup")
H2("Data")
P("We use the distractor setting of HotpotQA [7], a multi-hop question answering dataset in which each "
  "question comes with ten paragraphs, two of which contain the supporting facts. We sampled 100 questions at "
  "random (seed 42) from the 7,405-question validation split. With the instruction and question, an "
  "uncompressed prompt has 1,452 tokens on average. For example, the first question asks in what year the "
  "university where Sergei Aleksandrovich Tokarev was a professor was founded (gold answer: 1755); it needs "
  "two steps, finding the university and then its founding year.")
H2("Models and Infrastructure")
P("The answer model is gpt-oss-20b and the judge and optimizer is gpt-oss-120b [8], both served through the "
  "free tier of the Groq API at temperature 0 with low reasoning effort. The reranker and LLMLingua-2 run "
  "locally on the CPU. Every model call is cached, so a rerun gives the same results; the free tier allows "
  "200,000 tokens per day for each model, which is why the repair experiments use sets of 30 questions.")
H2("Evaluation Protocol")
P("The compression curves for both compressors use all 100 questions. Repair is evaluated on three disjoint "
  "sets of 30 questions: questions 1\u201330 were used to find the failure modes of v1 and design v2, "
  "questions 31\u201360 are held out for v2, and questions 61\u201390 were not used until v3 had been "
  f"designed (Fig. 2). Repair on question-aware contexts was run once, with v3 at 5{X}, 10{X} and 20{X} on "
  "questions 61\u201390. Table II lists the settings.")
FIGURE(FIG + "fig_question_sets.png", "Question sets and the repair versions evaluated on each on plain "
       "contexts. Questions 91\u2013100 were not used for repair.", width=COL_W * 0.95)
TABLE("Experimental settings",
      [["Item", "Setting"],
       ["Dataset", "HotpotQA distractor setting, validation split"],
       ["Sample", "100 questions, random seed 42"],
       ["Compressor", "LLMLingua-2, XLM-RoBERTa-large (MeetingBank)"],
       ["Question-aware", "bge-reranker-base + bridge rule, then LLMLingua-2"],
       ["Levels", f"2{X}, 5{X}, 10{X}, 20{X} (keep rate 1/r)"],
       ["Answer model", "gpt-oss-20b via Groq"],
       ["Judge / optimizer", "gpt-oss-120b via Groq"],
       ["Decoding", "Temperature 0, low reasoning effort"],
       ["Repair", "TextGrad TextLoss and TGD; 1 round (v1, v2), 2 rounds (v3)"],
       ["Statistics", "Sign / McNemar exact tests; 5,000-resample bootstrap"]],
      [0.3, 0.7], left_cols=(0, 1))
H2("Engineering Challenges")
P("<i>Model retirement.</i> Our first choice of model, llama-3.3-70b-versatile, was retired on 16 August 2026, "
  "so we moved to the gpt-oss models. <i>Daily token limits.</i> An uncompressed run over 100 questions needs "
  "about 145,000 prompt tokens, 73% of one model\u2019s daily allowance, so we added detection of the daily "
  "limit, a clean stop and resume from the cache. <i>Empty replies.</i> gpt-oss can spend the whole output "
  "budget on hidden reasoning and return no text; seven such empty replies had been cached and scored as wrong "
  "answers. The caller now retries them with a larger budget and never caches an empty reply. <i>No GPU.</i> "
  "The compressor and reranker run on the CPU. <i>Library integration.</i> TextGrad\u2019s engine names did "
  "not work with our provider string, so a small engine class routes TextGrad\u2019s calls through our cached "
  "caller.")
H2("Implementation")
P("The pipeline is a set of Python scripts (Appendix B): data preparation, the two compressors, evaluation, "
  "repair, statistics, cost replay and figures. Scoring and statistics live in a module without API "
  "dependencies, covered by unit tests. Repair results are written one question at a time, so an interrupted "
  "run resumes where it stopped. The experiments were run on Windows laptops in October and November 2026 "
  "with llmlingua 0.2.2, textgrad 0.1.8, litellm 1.106 and sentence-transformers 6.1.")

# =====================================================================  V. results
H1("Results")
H2("Compression Alone")
P("Table III shows the compression\u2013accuracy curve of plain LLMLingua-2. Going from the full context to "
  f"2{X} costs 0.064 F1 while removing 47% of the prompt tokens. Beyond that F1 falls quickly: 0.483 at 5{X}, "
  f"0.410 at 10{X} and 0.333 at 20{X}. The reason is visible in the compressed text: the gold answer is still "
  f"present in 82% of the contexts at 2{X} but in only 46%, 32% and 9% at 5{X}, 10{X} and 20{X} (Table IV), "
  "and the answer model almost never answers correctly once it is gone.")
TABLE("Plain LLMLingua-2 compression (n = 100)",
      [["Level", "Prompt tokens", "Token reduction", "EM", "F1", "F1 kept"],
       ["None", "1,452", "\u2013", "0.560", "0.740", "100%"],
       [f"2{X}", "765", "47%", "0.510", "0.676", "91%"],
       [f"5{X}", "383", "74%", "0.350", "0.483", "65%"],
       [f"10{X}", "251", "83%", "0.320", "0.410", "55%"],
       [f"20{X}", "182", "87%", "0.240", "0.333", "45%"]],
      [0.14, 0.18, 0.18, 0.15, 0.15, 0.2],
      note="Prompt tokens are averages counted by the answer model and include the instruction and question. "
           "Without the answer cleanup the EM/F1 values are 0.530/0.731, 0.490/0.670, 0.340/0.483, "
           "0.320/0.407 and 0.230/0.330, as in our Review 2 report.")
H2("Question-Aware Compression")
P("Question-aware selection changes what survives. At the same token budget, the gold answer is kept in "
  f"98%, 86%, 77% and 48% of the contexts at 2{X}, 5{X}, 10{X} and 20{X} (Table IV, Fig. 3).")
TABLE("Answer recall: gold answer still in the context",
      [["Level", "Plain", "Question-aware (paragraphs)", "Question-aware (sentences)", "Avg tokens"],
       [f"2{X}", "82%", "98%", "\u2013", "~655"],
       [f"5{X}", "46%", "86%", "91%", "~268"],
       [f"10{X}", "32%", "77%", "79%", "~133"],
       [f"20{X}", "9%", "48%", "56%", "~62"]],
      [0.14, 0.15, 0.26, 0.26, 0.19],
      note="96 questions whose answer is not yes/no. Tokens counted with the compressor\u2019s tokenizer "
           "(context only). The sentence variant is used from 5\u00d7 up.")
FIGURE(FIG + "fig_recall.png", "Share of questions whose gold answer survives compression, at equal token "
       "budgets.")
P("Table V gives the effect on accuracy, with the same prompt, the same answer model and the same scoring on "
  "both sides, so only the compression differs. Exact match rises by 16, 21 and 17 points at "
  f"5{X}, 10{X} and 20{X}, and for every question that question-aware compression breaks it fixes between "
  "7 and 12. These differences are significant (McNemar p \u2264 0.0005); at "
  f"2{X} the gain is smaller and could be chance (p = 0.23). Fig. 4 and Fig. 5 show the curves: at 10{X}, "
  "F1 is 0.681, which is 92% of the uncompressed 0.740, with 249 instead of 1,452 prompt tokens.")
TABLE("Plain vs question-aware compression (n = 100, paired)",
      [["Level", "EM plain", "EM QA", "F1 plain", "F1 QA", "EM fixed / broken", "McNemar p"],
       [f"2{X}", "0.51", "<b>0.56</b>", "0.676", "<b>0.727</b>", "8 / 3", "0.23"],
       [f"5{X}", "0.35", "<b>0.51</b>", "0.483", "<b>0.691</b>", "18 / 2", "0.0004"],
       [f"10{X}", "0.32", "<b>0.53</b>", "0.410", "<b>0.681</b>", "23 / 2", "&lt;0.0001"],
       [f"20{X}", "0.24", "<b>0.41</b>", "0.333", "<b>0.555</b>", "20 / 3", "0.0005"]],
      [0.11, 0.12, 0.12, 0.13, 0.13, 0.2, 0.19],
      note="QA = question-aware. Average prompt tokens for QA: 758, 381, 249 and 181. The F1 sign test gives "
           "p = 0.05, 0.0001, &lt;0.0001 and &lt;0.0001.")
FIGURE(FIG + "fig_accuracy_qa.png", "EM and F1 against compression level for plain LLMLingua-2 (grey) and "
       "question-aware compression (colour), 100 questions.")
FIGURE(FIG + "fig_tokens_qa.png", "Token cost against F1. Question-aware compression moves the whole curve "
       "up; its 10\u00d7 point is close to plain 2\u00d7 in F1 with a third of the tokens.")
P(f"The sentence variant keeps the answer more often still (91%, 79% and 56% at 5{X}, 10{X} and 20{X}), but "
  "its accuracy run did not finish within the free tier\u2019s daily limit, so we report it as answer recall "
  "only and use the paragraph variant everywhere else.")
H2("Repair v1 Did Not Help")
P(f"On questions 1\u201330, v1 changed F1 by +0.033, +0.027 and \u22120.050 at 5{X}, 10{X} and 20{X}. It "
  "helped and hurt 5 and 5, 6 and 6, and 7 and 8 questions, and the 95% ranges all include zero.")
H2("Repair v2")
P(f"Table VI and Fig. 6 pool v2 over the three question sets on plain contexts. It raises F1 by +0.105 at 5{X} and "
  f"+0.114 at 10{X}, and the 95% ranges exclude zero; exact match rises from 0.344 to 0.456 and from 0.333 "
  f"to 0.433. On exact match, 12 answers were fixed and 2 broken at 5{X} (McNemar p = 0.013) and 12 and 3 at "
  f"10{X} (p = 0.035). At 20{X} the gain is +0.027 and cannot be told apart from zero. On the two sets not "
  f"used for design, the gain was +0.139 and +0.108 at 5{X} and +0.129 and +0.078 at 10{X}.")
TABLE("Repair v2 on plain contexts, pooled",
      [["Level", "n", "Helped / hurt / same", "\u0394F1 [95% range]", "Recovered"],
       [f"5{X}", "90", "16 / 5 / 69", "+0.105 [+0.026, +0.187]", "\u224841%"],
       [f"10{X}", "90", "18 / 5 / 67", "+0.114 [+0.032, +0.199]", "\u224837%"],
       [f"20{X}", "60", "7 / 3 / 50", "+0.027 [\u22120.047, +0.102]", "\u22487%"]],
      [0.12, 0.08, 0.25, 0.35, 0.2],
      note="\u0394F1 is the mean per-question change from the compressed-only draft to the repaired answer. "
           "These runs predate the answer cleanup and are scored without it on both sides.")
FIGURE(FIG + "fig_repair_v2.png", "Uncompressed, compressed-only and repaired (v2) F1 on the pooled question "
       "sets of plain contexts. Each level uses its own questions, so the uncompressed bars differ.")
H2("Comparing the Versions")
P(f"Table VII compares the versions. On questions 61\u201390, v3 scored higher than v2 at 5{X} and lower at "
  f"10{X}, with neither difference clear on 30 questions. v2 hurt one question or none at each level on "
  "questions 1\u201330, while v1 hurt as many as it helped (Fig. 7). We treat v2 as the final repair method "
  "and v3 as an ablation.")
TABLE("Mean F1 change from repair, by version (plain contexts)",
      [["Version", "Questions", f"5{X}", f"10{X}", f"20{X}"],
       ["v1", "1\u201330", "+0.033", "+0.027", "\u22120.050"],
       ["v2", "1\u201330", "+0.067", "+0.136", "+0.060"],
       ["v2", "31\u201360", "+0.139", "+0.129", "\u22120.007"],
       ["v2", "61\u201390", "+0.108", "+0.078", "\u2013"],
       ["v3", "61\u201390", "+0.133", "+0.033", "\u2013"]],
      [0.18, 0.22, 0.2, 0.2, 0.2])
FIGURE(FIG + "fig_helped_hurt.png", "Questions helped, hurt and unchanged by repair on questions 1\u201330, "
       "for v1 and v2.", width=COL_W * 0.9)
H2("Repair on Question-Aware Contexts")
P("With better contexts there is less to repair. Table VIII runs v3 on question-aware contexts for questions "
  "61\u201390, the same questions as the plain v3 run. The question-aware draft alone already beats the "
  f"plain draft plus repair at 5{X} (0.658 against 0.523) and 10{X} (0.727 against 0.457). Repair then adds "
  f"+0.052 at 5{X}, \u22120.005 at 10{X} and +0.076 at 20{X}; it helped 3, 1 and 4 questions and hurt 2, 2 "
  "and 1, and none of these changes is significant (bootstrap ranges include zero; McNemar p = 1.0, 1.0, "
  "0.63).")
TABLE("F1 on questions 61\u201390: plain vs question-aware, with and without repair (v3)",
      [["Level", "Plain", "Plain + repair", "QA", "QA + repair", "\u0394F1 [95% range], QA"],
       [f"5{X}", "0.390", "0.523", "0.658", "<b>0.709</b>", "+0.052 [\u22120.067, +0.178]"],
       [f"10{X}", "0.424", "0.457", "<b>0.727</b>", "0.722", "\u22120.005 [\u22120.038, +0.029]"],
       [f"20{X}", "\u2013", "\u2013", "0.541", "<b>0.616</b>", "+0.076 [\u22120.047, +0.207]"]],
      [0.1, 0.12, 0.16, 0.12, 0.15, 0.35],
      note="Uncompressed F1 on these questions is 0.672. Plain runs are scored without the cleanup, QA runs "
           "with it; within each pair (with and without repair) the scoring is the same.")
H2("The Cost of Repair")
P("Repair re-sends the compressed context to a larger model. We replayed every stored repair from the cache "
  "(cost_analysis.py), which reproduced every stored answer exactly, and added up the prompt tokens of all "
  "judge, gradient and optimizer calls (Table IX, Fig. 8). Per question, the answer call plus repair uses "
  "1,550 to 3,670 prompt tokens, 107% to 252% of the 1,452 tokens of the uncompressed prompt, and most of "
  "them go to the 120B judge. In our setup repair therefore does not save tokens; question-aware compression "
  "recovers more accuracy with no extra model calls.")
TABLE("Prompt tokens per question including repair",
      [["Run", "Level", "Answer call", "Repair calls", "Calls", "Total vs full"],
       ["v2, plain", f"5{X}", "385", "1,762", "1.9", "148%"],
       ["v2, plain", f"10{X}", "251", "1,630", "2.0", "130%"],
       ["v2, plain", f"20{X}", "181", "1,402", "1.9", "109%"],
       ["v3, QA", f"5{X}", "390", "3,276", "3.3", "252%"],
       ["v3, QA", f"10{X}", "253", "1,297", "1.8", "107%"],
       ["v3, QA", f"20{X}", "184", "1,423", "2.0", "111%"]],
      [0.2, 0.12, 0.17, 0.18, 0.12, 0.21],
      note="Averages over the replayable questions (v2: n-weighted over the three sets; 4 of 240 v2 "
           "questions had a call missing from the cache). Output tokens are not included.")
FIGURE(FIG + "fig_repair_cost.png", "Prompt tokens per question for the answer call and the repair calls. "
       "Every repair configuration exceeds the uncompressed prompt (dashed).")
H2("Error Analysis")
P("We found three failure modes. <i>Abstention.</i> With v1, the judge turned drafts into answers such as "
  "\u201cNot stated\u201d and \u201cInsufficient data\u201d: none of the drafts abstained, but 2, 3 and 8 "
  f"repaired answers did at 5{X}, 10{X} and 20{X}. The v2 rules removed this completely. <i>Editing correct "
  "answers.</i> The loop also edits answers that are already right: \u201cGatwick Airport\u201d became "
  "\u201cLondon Gatwick\u201d and \u201cKevin Spacey\u201d became \u201cKevin Spacey (actor)\u201d. With the "
  "\u201cdraft is correct\u201d rule, v2 left about three quarters of the answers unchanged. <i>Entity "
  "swaps.</i> Some errors remain: \u201cRudolf H\u00f6ss\u201d became \u201cKurt Gerstein\u201d and "
  "\u201cCold War\u201d became \u201cWorld War I\u201d. When compression removes the sentence that links two "
  "entities, the judge can pick a wrong but plausible entity from the remaining text. Question-aware "
  "compression attacks this cause directly, because it keeps the linking paragraph more often.")
TABLE("Examples of repaired answers",
      [["Case", "Gold", "Draft", "Repaired"],
       [f"v2, 5{X}, helped", "Punjabi/Pashtun", "Norwegian", "Punjabi/Pashtun"],
       [f"v2, 5{X}, helped", "Puli Alam", "Logar", "Pul-i-Alam"],
       [f"v1, 10{X}, gave up", "Greyia", "Greyia", "cannot be determined"],
       [f"v1, 20{X}, over-edit", "Kevin Spacey", "Kevin Spacey", "Kevin Spacey (actor)"],
       [f"v2, 5{X}, swap", "the Cold War (1947\u201391)", "Cold War", "World War I"],
       [f"v3, 5{X}, swap", "Rudolf H\u00f6ss", "Rudolf H\u00f6ss", "Kurt Gerstein"],
       [f"v2, 10{X}, helped", "dinosaur", "Red and white \u201cS\u201d logo.", "dinosaur"]],
      [0.28, 0.25, 0.22, 0.25], left_cols=(0, 1, 2, 3),
      note="Taken from the result files; illustrative, not a random sample.")
H2("Consistency Across Question Sets")
P(f"Fig. 9 shows the share of lost F1 that v2 recovered on each question set. At 5{X} and 10{X} it stays "
  f"between 31.9% and 46.0% on all three sets, including the two not used for design. At 20{X} it is 16.1% "
  "and \u22121.7%, which is why we do not claim a gain there.")
FIGURE(FIG + "fig_recovery_sets.png", "Share of the lost F1 recovered by repair v2 on each set of 30 "
       "questions, plain contexts.", width=COL_W * 0.95)
H2("Negative Results")
P("A stricter answer prompt that asked the model to copy the exact span from the context did not help: on "
  "93 uncompressed questions it fixed 4 exact-match answers and broke 5 (EM 0.570 against 0.559), so the "
  "original prompt is used throughout. Repair, as shown above, costs more tokens than it saves.")
H2("Summary of Results")
B([f"Plain LLMLingua-2 keeps 91% of the F1 at 2{X}, but only 65%, 55% and 45% at 5{X}, 10{X} and 20{X}, "
   "because the gold answer is often removed.",
   f"Question-aware compression at the same budget raises F1 to 0.691, 0.681 and 0.555 at 5{X}, 10{X} and "
   "20\u00d7 (EM +16 to +21 points, McNemar p \u2264 0.0005).",
   f"Repair v2 raises F1 by about +0.11 at 5{X} and 10{X} on plain contexts, but costs 109\u2013148% of the "
   "uncompressed prompt in tokens.",
   "On question-aware contexts repair adds no significant gain."])

# =====================================================================  VI. discussion
H1("Discussion and Limitations")
P("<i>Why question-aware selection works.</i> HotpotQA contexts are mostly distractors: two of ten paragraphs "
  "hold the answer. A question-agnostic compressor spreads its budget evenly and deletes the answer, while a "
  "reranker can drop whole irrelevant paragraphs and leave the relevant ones nearly intact. On contexts with "
  "fewer distractors the gain may be smaller.")
P(f"<i>Sample size.</i> The compression curves use 100 questions and each repair set 30. The question-aware "
  f"gains at 5{X} to 20{X} are large enough to be significant at this size; the repair results on "
  "question-aware contexts are not, and a few points either way would need several hundred questions.")
P("<i>Tuning on the evaluation sample.</i> The number of paragraphs kept before trimming was chosen on "
  "answer recall over the same 100 questions. Only four values were tried and all of them beat plain "
  "compression by a wide margin, so the gain does not depend on this choice, but the exact numbers may be "
  "slightly optimistic.")
P("<i>Source of the repair gain.</i> The judge is a larger model than the answer model and may use its own "
  "knowledge, so part of the repair gain may come from a second opinion by a stronger model. We did not run "
  "the control in which the larger model answers directly from the compressed context.")
P("<i>Data contamination and repeatability.</i> HotpotQA is public and the gpt-oss models may have seen it. "
  "Hosted models can change; the cache makes the reported numbers repeatable from the stored responses, but "
  "a fresh run with new model versions may differ. Output tokens and latency were not measured.")
P(f"<i>Practical guidance.</i> For accuracy-critical use, question-aware compression at 2{X} keeps 98% of the "
  f"uncompressed F1 (0.727 against 0.740) with half the tokens. For cost-critical use, question-aware "
  f"compression at 10{X} keeps 92% with 17% of the tokens. Repair is worth its cost only when the answer must "
  "come from a context that cannot be selected better, and when calls to a larger model are acceptable.")

# =====================================================================  VII. review 1
H1("Comparison with the Review 1 Plan")
TABLE("Review 1 plan and what was done",
      [["Planned", "Done", "Status"],
       ["Literature review, setup", "Survey of compression, TextGrad and LLM-as-judge; environment", "Done"],
       ["Dataset and baseline", "100 HotpotQA questions, not enterprise documents", "Changed"],
       ["LongLLMLingua and LLMLingua-2", "LLMLingua-2, plus our own question-aware front end", "Done"],
       ["Compression tiers, repair loop", f"2{X} to 20{X}; TextGrad repair v1 to v3", "Done"],
       ["QA and summarization", "Question answering only", "Partly"],
       ["LLM-judge scoring, latency, cost", "EM, F1, significance tests; prompt-token cost measured; no latency",
        "Partly"],
       ["Middleware, demo, report", "pipeline.py, demo.py, this paper", "Done"]],
      [0.33, 0.5, 0.17], left_cols=(0, 1))

# =====================================================================  VIII. conclusion
H1("Conclusion")
P(f"Compressing HotpotQA contexts with LLMLingua-2 costs little at 2{X} but F1 falls to 0.483, 0.410 and "
  f"0.333 at 5{X}, 10{X} and 20{X}, mainly because the answer itself is deleted. A TextGrad repair loop whose "
  "judge sees only the compressed context recovers about 41% and 37% of the lost F1 at 5\u00d7 and 10\u00d7 "
  "once it is told to avoid \u201cunknown\u201d answers and leave correct drafts alone, but its calls cost "
  "more tokens than the full prompt. Choosing what to keep with the question in mind is both cheaper and "
  "more effective: at the same budget it raises F1 to 0.691, 0.681 and 0.555.")
P(f"In terms of the research questions: <b>RQ1</b>, compression costs 0.064 F1 at 2{X} and 0.407 at 20{X}. "
  f"<b>RQ2</b>, repair v2 recovers about 41% at 5{X} and 37% at 10{X}. <b>RQ3</b>, repair stops helping "
  f"reliably between 10{X} and 20{X}. <b>RQ4</b>, question-aware selection recovers far more, with "
  f"significant exact-match gains at 5{X}, 10{X} and 20{X}. <b>RQ5</b>, repair uses 107\u2013252% of the "
  "uncompressed prompt tokens.")
P("Future work: confirm the sentence-level variant on accuracy; scale to more questions and datasets, "
  "including summarization; run the control in which the judge model answers directly; measure output tokens "
  "and latency; and let repair restore a few tokens from the original context within a fixed budget.")

# =====================================================================  IX. team
H1("Team and Contributions")
P("The project was carried out by a team of four students. Table XII lists the part each member presented in "
  "Review 1.")
TABLE("Team members",
      [["Member", "SRN", "Review 1 section"],
       ["Krrish Singla", "PES1UG24AM141", "Problem, motivation and research gap"],
       ["Kishan K Shenoy", "PES1UG24AM138", "Literature survey: prompt compression"],
       ["Leeladhar G Sairaju", "PES1UG24AM148", "Literature survey: optimization, evaluation and the gap"],
       ["Mohammad Bilal A", "PES1UG24AM162", "Objective, technical approach and expected outcome"]],
      [0.27, 0.3, 0.43], left_cols=(0, 1, 2))
P("Code, data sample and results:<br/>https://github.com/krrishsingla11/compressgrad",
  ParagraphStyle("url", parent=body_ni, alignment=TA_LEFT))

H1("Acknowledgment", numbered=False)
P("The authors thank the faculty of the course Prompt Engineering and Optimization for Generative AI "
  "(UE24AM343AB5) at PES University for their guidance during the reviews.")

# =====================================================================  appendices
H1("Appendix A: Prompts", numbered=False)
P("The answer prompt, with the (compressed) context and the question inserted, was:", body_ni)
story.append(Preformatted("Answer the question using the context below.\nReply with ONLY the short answer "
                          "(a few words),\nno explanation.\n\nContext:\n[context]\n\nQuestion: [question]\n"
                          "Answer:", code))
story.append(Spacer(1, 4))
P("The evaluation instruction given to the judge, with the question and the compressed context appended, "
  "asks it to check whether the draft is supported by the context, answers exactly what is asked and is "
  "short, and to name the correct short answer. v2 adds: never say the answer is unknown, not stated or "
  "cannot be determined; if the draft is correct reply exactly \u201cThe draft answer is correct.\u201d; "
  "keep the same short form. v3 adds: only suggest a different answer if the context clearly supports it, "
  "and use only words that appear in the context. The full text is in repair.py.", body_ni)

H1("Appendix B: Repository and Reproduction", numbered=False)
TABLE("Repository files",
      [["File", "Purpose"],
       ["config.py", "Models, sample size, levels, prompt version, cleanup"],
       ["utils.py", "Cached model calls, retries, evaluation loop"],
       ["metrics.py", "EM, F1, answer cleanup, sign/McNemar test"],
       ["prepare_data.py", "Samples 100 HotpotQA questions"],
       ["compress.py", "Plain LLMLingua-2 at 2\u00d7 to 20\u00d7"],
       ["compress_qa.py", "Question-aware compression (paragraphs or sentences)"],
       ["baseline.py, eval_compressed.py", "Uncompressed and compressed evaluation"],
       ["repair.py", "TextGrad repair v1\u2013v3, plain or QA contexts"],
       ["analyze_repair.py", "Helped/hurt, bootstrap ranges, significance"],
       ["compare_results.py", "Paired comparison of two result files"],
       ["context_recall.py", "Answer recall of compressed contexts"],
       ["cost_analysis.py", "Token cost of repair (offline replay)"],
       ["pipeline.py, demo.py", "Middleware and side-by-side demo"],
       ["make_plots.py, test_metrics.py", "Figures; unit tests for scoring"]],
      [0.42, 0.58], left_cols=(0, 1))
story.append(Preformatted(
    "python prepare_data.py\npython compress.py\npython compress_qa.py\npython baseline.py\n"
    "python eval_compressed.py\npython eval_compressed.py compressed_qa.json\n"
    "python compare_results.py results_compressed.json \\\n    results_qa_promptv1.json\n"
    "python repair.py v2 ; python repair.py v2 heldout\npython repair.py v2 final ratios=5,10\n"
    "python repair.py v3 final qa ratios=5,10,20\npython analyze_repair.py v2 all\n"
    "python cost_analysis.py        # offline\npython demo.py --id 8 --ratio 10", code))

H1("References", numbered=False)
REFS = [
    "H. Jiang, Q. Wu, C.-Y. Lin, Y. Yang, and L. Qiu, \u201cLLMLingua: Compressing prompts for accelerated "
    "inference of large language models,\u201d in <i>Proc. EMNLP</i>, 2023, arXiv:2310.05736.",
    "H. Jiang, Q. Wu, X. Luo, D. Li, C.-Y. Lin, Y. Yang, and L. Qiu, \u201cLongLLMLingua: Accelerating and "
    "enhancing LLMs in long context scenarios via prompt compression,\u201d in <i>Proc. ACL</i>, 2024, "
    "arXiv:2310.06839.",
    "Z. Pan <i>et al.</i>, \u201cLLMLingua-2: Data distillation for efficient and faithful task-agnostic "
    "prompt compression,\u201d in <i>Findings of ACL</i>, 2024, arXiv:2403.12968.",
    "M. Yuksekgonul, F. Bianchi, J. Boen, S. Liu, Z. Huang, C. Guestrin, and J. Zou, \u201cTextGrad: "
    "Automatic \u2018differentiation\u2019 via text,\u201d arXiv:2406.07496, 2024.",
    "Y. Li, B. Dong, F. Guerin, and C. Lin, \u201cCompressing context to enhance inference efficiency of "
    "large language models,\u201d in <i>Proc. EMNLP</i>, 2023, arXiv:2310.06201.",
    "L. Zheng <i>et al.</i>, \u201cJudging LLM-as-a-judge with MT-Bench and Chatbot Arena,\u201d in "
    "<i>Proc. NeurIPS Datasets and Benchmarks</i>, 2023, arXiv:2306.05685.",
    "Z. Yang <i>et al.</i>, \u201cHotpotQA: A dataset for diverse, explainable multi-hop question "
    "answering,\u201d in <i>Proc. EMNLP</i>, 2018.",
    "OpenAI, \u201cgpt-oss-120b and gpt-oss-20b model card,\u201d arXiv:2508.10925, 2025.",
    "N. F. Liu, K. Lin, J. Hewitt, A. Paranjape, M. Bevilacqua, F. Petroni, and P. Liang, \u201cLost in the "
    "middle: How language models use long contexts,\u201d <i>Trans. Assoc. Comput. Linguistics</i>, vol. 12, "
    "2024, arXiv:2307.03172.",
    "A. Madaan <i>et al.</i>, \u201cSelf-Refine: Iterative refinement with self-feedback,\u201d in "
    "<i>Proc. NeurIPS</i>, 2023, arXiv:2303.17651.",
    "N. Shinn, F. Cassano, A. Gopinath, K. Narasimhan, and S. Yao, \u201cReflexion: Language agents with "
    "verbal reinforcement learning,\u201d in <i>Proc. NeurIPS</i>, 2023, arXiv:2303.11366.",
    "S. Xiao, Z. Liu, P. Zhang, and N. Muennighoff, \u201cC-Pack: Packaged resources to advance general "
    "Chinese embedding,\u201d arXiv:2309.07597, 2023.",
    "Q. McNemar, \u201cNote on the sampling error of the difference between correlated proportions or "
    "percentages,\u201d <i>Psychometrika</i>, vol. 12, no. 2, pp. 153\u2013157, 1947.",
]
for i, r in enumerate(REFS, 1):
    story.append(Paragraph(f"[{i}]\u00a0\u00a0{r}", ref))


# =====================================================================  layout
def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("TNR", 8)
    canvas.drawCentredString(PAGE_W / 2, 0.55 * inch, str(doc.page))
    canvas.restoreState()


doc = BaseDocTemplate(OUT, pagesize=letter, leftMargin=MARGIN_X, rightMargin=MARGIN_X, topMargin=TOP,
                      bottomMargin=BOTTOM, title="CompressGrad", author="Singla, Shenoy, Sairaju, Bilal A")
body_h = PAGE_H - TOP - BOTTOM
first = PageTemplate("first", frames=[
    Frame(MARGIN_X, PAGE_H - TOP - TITLE_H, PAGE_W - 2 * MARGIN_X, TITLE_H, id="title", leftPadding=0,
          rightPadding=0),
    Frame(MARGIN_X, BOTTOM, COL_W, body_h - TITLE_H, id="c1", leftPadding=0, rightPadding=0, topPadding=0),
    Frame(MARGIN_X + COL_W + GAP, BOTTOM, COL_W, body_h - TITLE_H, id="c2", leftPadding=0, rightPadding=0,
          topPadding=0),
], onPage=page_number)
later = PageTemplate("later", frames=[
    Frame(MARGIN_X, BOTTOM, COL_W, body_h, id="l1", leftPadding=0, rightPadding=0, topPadding=0),
    Frame(MARGIN_X + COL_W + GAP, BOTTOM, COL_W, body_h, id="l2", leftPadding=0, rightPadding=0, topPadding=0),
], onPage=page_number)
first.autoNextPageTemplate = "later"
doc.addPageTemplates([first, later])
doc.build(story)
print("wrote", OUT)

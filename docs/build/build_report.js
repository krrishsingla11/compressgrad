// Builds docs/CompressGrad_Final_Report.docx (A4, Times New Roman 12 pt). Run from the repository root:
//   NODE_PATH=<folder with node_modules> node docs/build/build_report.js
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun, LevelFormat, Packer, PageBreak,
  PageNumber, Paragraph, ShadingType, Table, TableCell, TableOfContents, TableRow, TextRun, WidthType,
} = require("docx");

const OUT = path.resolve("docs/CompressGrad_Final_Report.docx");
const FIG = path.resolve("docs/figures");
const FONT = "Times New Roman";
const CONTENT_W = 9026; // A4 width 11906 minus two 1-inch margins, in DXA
const X = "×";

// ------------------------------------------------------------------ helpers
let figN = 0, tabN = 0;
const runs = (text) => {
  // **bold** and *italic* inline markup
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun(text.slice(last, m.index)));
    const t = m[0];
    out.push(t.startsWith("**") ? new TextRun({ text: t.slice(2, -2), bold: true })
      : new TextRun({ text: t.slice(1, -1), italics: true }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun(text.slice(last)));
  return out;
};
const P = (text, opts = {}) => new Paragraph({ children: runs(text), alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 140 }, ...opts });
const H1 = (text) => new Paragraph({ text, heading: HeadingLevel.HEADING_1, pageBreakBefore: true });
const H2 = (text) => new Paragraph({ text, heading: HeadingLevel.HEADING_2 });
const BL = (items) => items.map((t) => new Paragraph({ children: runs(t), numbering: { reference: "bullets", level: 0 },
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 } }));
const NL = (items) => items.map((t) => new Paragraph({ children: runs(t), numbering: { reference: "numbers", level: 0 },
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 } }));
const caption = (text) => new Paragraph({ children: [new TextRun({ text, size: 20, italics: true })],
  alignment: AlignmentType.CENTER, spacing: { before: 80, after: 240 } });

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function figure(file, text, widthIn = 5.2) {
  figN += 1;
  const { w, h } = pngSize(path.join(FIG, file));
  const wPx = widthIn * 96;
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120 }, keepNext: true, children: [
      new ImageRun({ type: "png", data: fs.readFileSync(path.join(FIG, file)),
        transformation: { width: wPx, height: wPx * h / w },
        altText: { title: `Figure ${figN}`, description: text, name: file } })] }),
    caption(`Figure ${figN}: ${text}`),
  ];
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
function table(title, rows, fractions) {
  tabN += 1;
  const widths = fractions.map((f) => Math.round(f * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const trs = rows.map((row, r) => new TableRow({ tableHeader: r === 0, children: row.map((c, i) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: border, bottom: border, left: border, right: border },
    shading: r === 0 ? { type: ShadingType.CLEAR, color: "auto", fill: "DCE3EC" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text: String(c), bold: r === 0, size: 21 })],
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })],
  })) }));
  return [
    new Paragraph({ children: [new TextRun({ text: `Table ${tabN}: ${title}`, bold: true, size: 21 })],
      alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, keepNext: true }),
    new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths, rows: trs }),
    new Paragraph({ text: "", spacing: { after: 160 } }),
  ];
}
const code = (lines) => lines.map((l) => new Paragraph({ children: [new TextRun({ text: l, font: "Courier New", size: 19 })],
  spacing: { after: 0 }, indent: { left: 360 } }));

// ------------------------------------------------------------------ title page
const center = (text, size, bold = false, after = 120) => new Paragraph({ alignment: AlignmentType.CENTER,
  spacing: { after }, children: [new TextRun({ text, size, bold })] });
const titlePage = [
  center("PES UNIVERSITY, BENGALURU", 28, true, 60),
  center("Department of Computer Science & Engineering (AI & ML)", 24, false, 600),
  center("A Mini Project Report on", 24, false, 200),
  center("CompressGrad", 52, true, 120),
  center("Recovering the Accuracy Lost to Prompt Compression with", 28, false, 40),
  center("Question-Aware Selection and TextGrad-Guided Repair", 28, false, 600),
  center("Submitted for the course", 22, false, 40),
  center("Prompt Engineering and Optimization for Generative AI (UE24AM343AB5)", 24, true, 40),
  center("B.Tech, Semester 5", 22, false, 600),
  center("Submitted by", 22, false, 160),
  ...[["Krrish Singla", "PES1UG24AM141"], ["Kishan K Shenoy", "PES1UG24AM138"],
    ["Leeladhar G Sairaju", "PES1UG24AM148"], ["Mohammad Bilal A", "PES1UG24AM162"]].map(([n, s]) =>
    center(`${n}  (${s})`, 24, false, 60)),
  center("", 22, false, 600),
  center("November 2026", 22, false, 0),
  new Paragraph({ children: [new PageBreak()] }),
];

// ------------------------------------------------------------------ body
const body = [
  new Paragraph({ text: "Contents", heading: HeadingLevel.HEADING_1 }),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  P("*If the contents list is empty, right-click it in Word and choose Update Field.*"),

  H1("Abstract"),
  P("Large language models (LLMs) are often given long inputs, and both their cost and their response time grow " +
    "with the number of input tokens. Prompt compression tools such as LLMLingua-2 shorten a prompt by deleting " +
    "words that a small model considers unimportant, but they do not know the question being asked, so they can " +
    "delete exactly the words the answer depends on. This project measures that trade-off and tests two ways to " +
    "win the lost accuracy back."),
  P(`On 100 questions from the HotpotQA dataset, compressing the context by 2${X}, 5${X}, 10${X} and 20${X} with ` +
    "LLMLingua-2 lowers the F1 score of the answers from 0.740 to 0.676, 0.483, 0.410 and 0.333. The first remedy is " +
    "a repair loop built with TextGrad, in which a larger judge model reads the same compressed text, critiques the " +
    `draft answer and rewrites it, without ever seeing the correct answer. After error analysis, it raises F1 by about ` +
    `0.11 at 5${X} and 10${X}, but replaying all of its model calls shows that it uses more tokens than simply sending ` +
    "the uncompressed prompt. The second remedy is question-aware compression: a reranker chooses the paragraphs that " +
    "matter for the question before LLMLingua-2 compresses them, using the same number of tokens per question. It keeps " +
    `the correct answer in the context far more often and raises F1 to 0.727, 0.691, 0.681 and 0.555. At 10${X} ` +
    "compression it keeps 92% of the full-context accuracy with 17% of the tokens, and the gains at 5×, 10× and 20× are " +
    "statistically significant."),

  // ---------------------------------------------------------------- 1
  H1("1. Introduction"),
  H2("1.1 Motivation"),
  P("Applications such as document question answering, retrieval-augmented generation and enterprise assistants send " +
    "long passages to an LLM with every request. Paid APIs charge per token and latency grows with prompt length, so " +
    "shorter prompts are cheaper and faster. Prompt compression promises large savings, but compression removes " +
    "information, and how much accuracy is lost at each compression level is not well measured."),
  H2("1.2 Problem Statement"),
  P("Given a long context and a question, reduce the number of context tokens sent to the answer model by a factor " +
    "of 2 to 20 while keeping the answer as accurate as possible, and do so without access to the correct answer."),
  H2("1.3 Objectives and Research Questions"),
  ...NL([
    `**RQ1.** How much accuracy does LLMLingua-2 compression cost at 2${X}, 5${X}, 10${X} and 20${X}?`,
    "**RQ2.** Can TextGrad-guided repair, with a judge that never sees the gold answer, recover part of the lost accuracy?",
    "**RQ3.** At which compression level does repair stop helping?",
    "**RQ4.** Does question-aware selection before compression recover more accuracy at the same token budget?",
    "**RQ5.** What does the repair step cost in tokens?",
  ]),
  H2("1.4 Scope"),
  P("The study uses one public dataset (HotpotQA, question answering), one answer model and one judge model, all on " +
    "the free tier of the Groq API. Summarization, latency measurement and paid models are outside the scope."),

  // ---------------------------------------------------------------- 2
  H1("2. Literature Survey"),
  H2("2.1 Prompt Compression"),
  P("LLMLingua (Jiang et al., 2023) uses a small language model to drop low-information tokens and reports up to " +
    `20${X} compression with small loss. LongLLMLingua (2024) makes compression question-aware by ranking documents ` +
    "by relevance before compressing tokens. LLMLingua-2 (Pan et al., 2024) treats compression as token " +
    "classification with a small encoder trained on GPT-4-compressed data and is several times faster. Selective " +
    "Context (Li et al., 2023) prunes tokens by self-information. LLMLingua-2 and Selective Context do not look at the question."),
  H2("2.2 Textual Gradients and Self-Refinement"),
  P("TextGrad (Yuksekgonul et al., 2024) treats an LLM's natural-language critique as a gradient that is passed " +
    "back to a text variable and used by an optimizer to rewrite it. Self-Refine and Reflexion improve outputs with " +
    "similar feedback loops. LLM-as-a-judge studies (Zheng et al., 2023) show that strong judges often agree with " +
    "humans but have biases, which is why our final scores use exact match and F1, not a judge."),
  H2("2.3 Research Gap"),
  P("Our Review 1 survey found no work that combines TextGrad with LLMLingua-style compression, and compression " +
    "papers report the effect of compression without trying to repair the answer afterwards. This project fills that " +
    "gap and adds a simple question-aware front end to LLMLingua-2."),

  // ---------------------------------------------------------------- 3
  H1("3. System Design"),
  H2("3.1 Architecture"),
  P("Figure 1 shows the pipeline. A HotpotQA question and its ten paragraphs go through one of two compressors that " +
    "produce the same number of tokens per question. The answer model answers from the compressed text. An optional " +
    "repair step lets a larger judge model critique and rewrite the answer. Finally the answer is scored against the " +
    "correct answer. Nothing before the scoring step ever sees the correct answer."),
  ...figure("fig_pipeline.png", "The CompressGrad pipeline", 3.6),
  H2("3.2 Modules"),
  ...table("Main modules", [
    ["Module", "Responsibility"],
    ["Data preparation", "Samples 100 HotpotQA questions with a fixed seed and formats the ten paragraphs"],
    ["Plain compressor", "LLMLingua-2 keeps 1/r of the context tokens"],
    ["Question-aware compressor", "Reranks paragraphs against the question, then LLMLingua-2 trims to the same budget"],
    ["Answer and cache layer", "Calls the models through LiteLLM; every response is cached and failed calls are retried"],
    ["Repair", "TextGrad loss and optimizer with the judge model (v1, v2, v3)"],
    ["Evaluation", "EM, F1, answer cleanup, sign/McNemar tests, bootstrap ranges, answer recall"],
    ["Cost analysis", "Replays every stored repair from the cache and counts prompt tokens"],
    ["Middleware and demo", "compress_and_answer() function and a side-by-side command-line demo"],
  ], [0.3, 0.7]),
  H2("3.3 Question-Aware Compression"),
  ...NL([
    "Split the context into its ten \"Title: text\" paragraphs.",
    "Score each paragraph against the question with the cross-encoder BAAI/bge-reranker-base.",
    "Bridge hop: HotpotQA needs two paragraphs, and the second often shares few words with the question, so a paragraph whose title appears in the best paragraph (or that mentions the best paragraph's title) is moved up behind it.",
    "Take paragraphs in this order until the token budget is reached.",
    "Let LLMLingua-2 trim them to exactly the token count plain compression used for the same question.",
  ]),
  P("Keeping paragraphs worth 1, 1.5, 2 and 3 times the budget before trimming was tried; 1 was best at every " +
    "level, meaning it is better to keep fewer paragraphs and cut them less."),
  H2("3.4 TextGrad Repair"),
  P("The draft answer is a TextGrad variable. A loss built from an evaluation instruction (the question plus the " +
    "compressed context) asks the judge whether the draft is supported, answers exactly what is asked and is short. " +
    "backward() turns the critique into feedback and the optimizer step rewrites the answer. **v1** used this " +
    "instruction alone. **v2** adds three rules: never answer \"unknown\", keep drafts the judge accepts (which stops " +
    "the loop early) and keep the short answer form. **v3** adds that the judge may only change the answer when the " +
    "context clearly supports it, and runs two rounds."),

  // ---------------------------------------------------------------- 4
  H1("4. Implementation"),
  H2("4.1 Tools and Technologies"),
  ...table("Tools used", [
    ["Tool", "Use"],
    ["Python 3.11", "All scripts"],
    ["llmlingua 0.2.2", "LLMLingua-2 compressor (XLM-RoBERTa-large, MeetingBank)"],
    ["sentence-transformers 6.1", "bge-reranker-base cross-encoder"],
    ["textgrad 0.1.8", "Textual-gradient repair loop"],
    ["litellm 1.106", "Calls to the Groq API"],
    ["Groq API (free tier)", "gpt-oss-20b (answers) and gpt-oss-120b (judge)"],
    ["datasets, matplotlib, pytest", "HotpotQA download, figures, unit tests"],
  ], [0.35, 0.65]),
  H2("4.2 Engineering Challenges"),
  ...BL([
    "**Model retirement:** the first model, llama-3.3-70b-versatile, was retired in August 2026, so the project moved to the gpt-oss models.",
    "**Daily token limit:** the free tier allows 200,000 tokens per model per day. The caller detects the daily limit, stops cleanly and resumes from the cache the next day.",
    "**Empty replies:** gpt-oss sometimes spends its whole output budget on hidden reasoning and returns nothing. Seven such replies had been cached and scored as wrong; the caller now retries them with a larger budget and never caches an empty reply.",
    "**No GPU:** the compressor and reranker run on the CPU.",
    "**Library integration:** a small engine class routes TextGrad's calls through the cached caller.",
  ]),
  H2("4.3 Code Quality"),
  P("Scoring and statistics are in a separate module with no API dependencies and are covered by unit tests. The " +
    "evaluation code is shared by all scripts, compressed contexts are matched to questions by id, and the repair " +
    "function can be imported by the middleware, the demo and the cost replay."),

  // ---------------------------------------------------------------- 5
  H1("5. Experimental Setup"),
  H2("5.1 Dataset"),
  P("HotpotQA (distractor setting) gives every question ten Wikipedia paragraphs, of which two contain the " +
    "supporting facts. 100 questions were sampled from the 7,405-question validation split with random seed 42. An " +
    "uncompressed prompt has 1,452 tokens on average. Example: \"In what year was the university where Sergei " +
    "Aleksandrovich Tokarev was a professor founded?\" needs two steps (the university, then its founding year); the " +
    "answer is 1755."),
  H2("5.2 Metrics"),
  ...BL([
    "**Exact match (EM):** 1 if the normalized answer equals the normalized correct answer, else 0 (lower case, no punctuation, no articles).",
    "**F1:** word-overlap score that gives partial credit; \"Salma Hayek\" against \"Salma Hayek Pinault\" scores EM 0 and F1 0.8.",
    "**Answer cleanup:** before scoring, prefixes, bracketed asides and trailing full stops are removed. It never uses the correct answer and is applied to every method.",
    "**Significance:** on the same questions, count the answers one method fixed and the other broke; McNemar's exact test gives the probability of such a split by chance.",
    "**Answer recall:** the share of questions whose correct answer still appears in the compressed text (no model calls needed).",
  ]),
  H2("5.3 Protocol"),
  P("Both compressors are evaluated on all 100 questions. Repair is evaluated on three disjoint sets of 30 questions: " +
    "questions 1–30 were used to design v2, questions 31–60 are held out, and questions 61–90 were kept unseen until " +
    "v3 was designed. Repair on question-aware contexts was run with v3 on questions 61–90. All decoding uses " +
    "temperature 0 and every response is cached, so results are repeatable."),

  // ---------------------------------------------------------------- 6
  H1("6. Results and Discussion"),
  H2("6.1 Plain Compression"),
  ...table("Plain LLMLingua-2 compression, 100 questions", [
    ["Level", "Prompt tokens", "EM", "F1", "F1 kept"],
    ["None", "1,452", "0.560", "0.740", "100%"],
    [`2${X}`, "765", "0.510", "0.676", "91%"],
    [`5${X}`, "383", "0.350", "0.483", "65%"],
    [`10${X}`, "251", "0.320", "0.410", "55%"],
    [`20${X}`, "182", "0.240", "0.333", "45%"],
  ], [0.2, 0.2, 0.2, 0.2, 0.2]),
  P(`2${X} costs little, but accuracy falls quickly after that. The reason is that the correct answer itself is ` +
    `deleted: it is still present in 82% of the compressed contexts at 2${X} but only 46%, 32% and 9% at 5${X}, 10${X} ` +
    "and 20×, and the model almost never answers correctly once it is gone."),
  H2("6.2 Question-Aware Compression"),
  ...figure("fig_recall.png", "Share of questions whose correct answer survives compression, at equal token budgets", 4.6),
  ...table("Plain vs question-aware compression (same questions, same tokens)", [
    ["Level", "EM plain", "EM QA", "F1 plain", "F1 QA", "EM fixed / broken", "McNemar p"],
    [`2${X}`, "0.51", "0.56", "0.676", "0.727", "8 / 3", "0.23"],
    [`5${X}`, "0.35", "0.51", "0.483", "0.691", "18 / 2", "0.0004"],
    [`10${X}`, "0.32", "0.53", "0.410", "0.681", "23 / 2", "< 0.0001"],
    [`20${X}`, "0.24", "0.41", "0.333", "0.555", "20 / 3", "0.0005"],
  ], [0.11, 0.13, 0.12, 0.14, 0.13, 0.19, 0.18]),
  P(`Question-aware compression raises exact match by 16 to 21 points at 5${X}, 10${X} and 20${X}, and these gains ` +
    `are statistically significant. At 10${X} its F1 of 0.681 is 92% of the uncompressed 0.740 while using 249 ` +
    "instead of 1,452 prompt tokens (Figure 3, Figure 4). A sentence-level variant keeps the answer even more often " +
    `(91%, 79% and 56% at 5${X}, 10${X} and 20${X}), but its accuracy run did not finish within the free tier's daily ` +
    "limit, so it is reported as answer recall only."),
  ...figure("fig_accuracy_qa.png", "EM and F1 against compression level, plain (grey) and question-aware (colour)", 4.6),
  ...figure("fig_tokens_qa.png", "Token cost against F1 for both compressors", 4.6),
  H2("6.3 TextGrad Repair"),
  P(`Repair v1 did not help: on questions 1–30 it hurt as many answers as it helped, turned answers into "not ` +
    `stated" and edited correct answers ("dogs" became "dog breeds"). The v2 rules fixed both problems. Pooled over ` +
    `the three question sets on plain contexts, v2 raises F1 by +0.105 at 5${X} and +0.114 at 10${X} (95% bootstrap ` +
    `ranges exclude zero; McNemar p = 0.013 and 0.035), recovering about 41% and 37% of the lost F1. At 20${X} the ` +
    "gain is +0.027 and not significant. The remaining errors are mostly entity swaps (\"Rudolf Höss\" became \"Kurt " +
    "Gerstein\") where compression had deleted the sentence linking two entities."),
  ...table("Repair v2 on plain contexts, pooled", [
    ["Level", "Questions", "F1 compressed", "F1 repaired", "Change [95% range]"],
    [`5${X}`, "90", "0.475", "0.580", "+0.105 [+0.026, +0.187]"],
    [`10${X}`, "90", "0.420", "0.534", "+0.114 [+0.032, +0.199]"],
    [`20${X}`, "60", "0.392", "0.419", "+0.027 [−0.047, +0.102]"],
  ], [0.14, 0.16, 0.2, 0.2, 0.3]),
  ...figure("fig_repair_v2.png", "Uncompressed, compressed-only and repaired (v2) F1 on plain contexts", 4.6),
  P(`On question-aware contexts (questions 61–90, v3) there is little left to repair: the draft alone already scores ` +
    `0.658, 0.727 and 0.541 at 5${X}, 10${X} and 20${X}, and repair changes this by +0.052, −0.005 and +0.076, none of ` +
    "which is significant."),
  H2("6.4 Cost of Repair"),
  P("Every stored repair was replayed from the cache, which reproduced every stored answer, and the prompt tokens of " +
    "all judge and optimizer calls were added up. Per question, the answer call plus repair uses 1,550 to 3,670 " +
    "prompt tokens, which is 107% to 252% of the 1,452 tokens of the uncompressed prompt, and most of them go to the " +
    "larger 120B model (Figure 6). Repair therefore does not save tokens in this setup."),
  ...figure("fig_repair_cost.png", "Prompt tokens per question for the answer call and the repair calls", 4.6),
  H2("6.5 Negative Results and Limitations"),
  ...BL([
    "A stricter \"copy the exact span\" answer prompt did not help (4 answers fixed, 5 broken on 93 questions), so the original prompt is used.",
    "One dataset, 100 questions and one model pair; repair sets have 30 questions each.",
    "The number of paragraphs kept before trimming was chosen on the same 100 questions; all four values tried beat plain compression by a wide margin.",
    "The judge is a larger model and may use its own knowledge; a control in which it answers directly was not run.",
    "HotpotQA is public and may have been seen in training. Output tokens and latency were not measured.",
  ]),

  // ---------------------------------------------------------------- 7
  H1("7. Conclusion and Future Work"),
  P("Compression with LLMLingua-2 costs little at 2× but much more beyond, mainly because the answer itself is " +
    "deleted. TextGrad repair, once its failure modes were fixed, recovers about 40% of the loss at 5× and 10×, but " +
    "costs more tokens than the full prompt. Choosing what to keep with the question in mind is both cheaper and more " +
    "effective: at the same budget it keeps 92% of the full accuracy at 10× compression."),
  ...table("Answers to the research questions", [
    ["Question", "Answer"],
    ["RQ1", "Compression costs 0.064 F1 at 2× and 0.407 at 20×"],
    ["RQ2", "Repair v2 recovers about 41% of the lost F1 at 5× and 37% at 10×"],
    ["RQ3", "Repair stops helping reliably between 10× and 20×"],
    ["RQ4", "Question-aware compression raises F1 to 0.691 / 0.681 / 0.555 at 5× / 10× / 20× (significant)"],
    ["RQ5", "Repair uses 107–252% of the uncompressed prompt's tokens"],
  ], [0.15, 0.85]),
  P("Future work: confirm the sentence-level variant on accuracy, extend to more datasets and to summarization, " +
    "run the control in which the judge answers directly, measure output tokens and latency, and let repair restore a " +
    "few tokens of the original context within a fixed budget."),

  // ---------------------------------------------------------------- 8
  H1("8. Team Contributions"),
  ...table("Team members", [
    ["Member", "SRN", "Review 1 section"],
    ["Krrish Singla", "PES1UG24AM141", "Problem, motivation and research gap"],
    ["Kishan K Shenoy", "PES1UG24AM138", "Literature survey: prompt compression"],
    ["Leeladhar G Sairaju", "PES1UG24AM148", "Literature survey: optimization, evaluation and the gap"],
    ["Mohammad Bilal A", "PES1UG24AM162", "Objective, technical approach and expected outcome"],
  ], [0.27, 0.27, 0.46]),
  P("Code, data sample and results: https://github.com/krrishsingla11/compressgrad"),

  // ---------------------------------------------------------------- references
  H1("References"),
  ...[
    "H. Jiang, Q. Wu, C.-Y. Lin, Y. Yang and L. Qiu, \"LLMLingua: Compressing prompts for accelerated inference of large language models,\" EMNLP, 2023.",
    "H. Jiang et al., \"LongLLMLingua: Accelerating and enhancing LLMs in long context scenarios via prompt compression,\" ACL, 2024.",
    "Z. Pan et al., \"LLMLingua-2: Data distillation for efficient and faithful task-agnostic prompt compression,\" Findings of ACL, 2024.",
    "M. Yuksekgonul et al., \"TextGrad: Automatic 'differentiation' via text,\" arXiv:2406.07496, 2024.",
    "Y. Li, B. Dong, F. Guerin and C. Lin, \"Compressing context to enhance inference efficiency of large language models,\" EMNLP, 2023.",
    "L. Zheng et al., \"Judging LLM-as-a-judge with MT-Bench and Chatbot Arena,\" NeurIPS Datasets and Benchmarks, 2023.",
    "Z. Yang et al., \"HotpotQA: A dataset for diverse, explainable multi-hop question answering,\" EMNLP, 2018.",
    "OpenAI, \"gpt-oss-120b and gpt-oss-20b model card,\" arXiv:2508.10925, 2025.",
    "A. Madaan et al., \"Self-Refine: Iterative refinement with self-feedback,\" NeurIPS, 2023.",
    "N. Shinn et al., \"Reflexion: Language agents with verbal reinforcement learning,\" NeurIPS, 2023.",
    "S. Xiao, Z. Liu, P. Zhang and N. Muennighoff, \"C-Pack: Packaged resources to advance general Chinese embedding,\" arXiv:2309.07597, 2023.",
    "Q. McNemar, \"Note on the sampling error of the difference between correlated proportions or percentages,\" Psychometrika, 12(2), 1947.",
  ].map((r, i) => new Paragraph({ children: [new TextRun(`[${i + 1}] ${r}`)], spacing: { after: 100 },
    indent: { left: 540, hanging: 540 } })),

  // ---------------------------------------------------------------- appendix
  H1("Appendix: How to Run"),
  P("Install the requirements, set the GROQ_API_KEY environment variable, and run from the repository folder. " +
    "Every model call is cached, so the demo and all analysis scripts also run without an API key once the " +
    "experiments have been run."),
  ...code([
    "pip install -r requirements.txt",
    "python prepare_data.py",
    "python compress.py",
    "python compress_qa.py",
    "python baseline.py",
    "python eval_compressed.py compressed_qa.json",
    "python compare_results.py results_compressed.json results_qa_promptv1.json",
    "python repair.py v2 ; python repair.py v2 heldout",
    "python repair.py v3 final qa ratios=5,10,20",
    "python cost_analysis.py",
    "python demo.py --id 38 --ratio 10",
    "python -m pytest test_metrics.py",
  ]),
];

// ------------------------------------------------------------------ document
const doc = new Document({
  creator: "CompressGrad team",
  title: "CompressGrad: Final Project Report",
  features: { updateFields: true },
  styles: {
    default: { document: { run: { font: FONT, size: 24 }, paragraph: { spacing: { line: 300 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 32, bold: true, color: "14213D" },
        paragraph: { spacing: { before: 240, after: 200 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 26, bold: true, color: "1F6F8B" },
        paragraph: { spacing: { before: 200, after: 100 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    { reference: "numbers", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }] },
  ] },
  sections: [
    { properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, children: titlePage },
    { properties: { page: { size: { width: 11906, height: 16838 },
      margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }, pageNumbers: { start: 1 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 20 })] })] }) },
      children: body },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote", OUT);
});

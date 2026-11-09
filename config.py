import os

# Models used everywhere in the project. Change them here only.
# Answer model: answers the questions (cheaper, faster)
ANSWER_MODEL = "groq/openai/gpt-oss-20b"
# Judge/optimizer model: gives feedback and repairs answers in TextGrad
JUDGE_MODEL = "groq/openai/gpt-oss-120b"

N_QUESTIONS = 100          # sample size
SEED = 42                  # keeps the same 100 questions every run
COMPRESSION_RATIOS = [2, 5, 10, 20]

# ---- answer format ----
# "v1": original prompt. "v2": asks for the exact span from the context (HotpotQA style).
# v2 was tested on 93 uncompressed questions: 4 fixed, 5 broken (p = 1.0), so v1 stays the default.
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1")   # env var lets one run switch without editing
CLEAN_ANSWERS = True       # strip "(RAF)"-style asides etc. before scoring (see metrics.clean_answer)

# ---- TextGrad repair stage ----
REPAIR_RATIOS = [5, 10, 20]   # compression levels to repair
N_REPAIR = 30                 # questions per level (keeps within the free daily limit)
REPAIR_ROUNDS = 1             # feedback + rewrite rounds per question

# Models used everywhere in the project. Change them here only.
# Answer model: answers the questions (cheaper, faster)
ANSWER_MODEL = "groq/openai/gpt-oss-20b"
# Judge/optimizer model: gives feedback and repairs answers in TextGrad
JUDGE_MODEL = "groq/openai/gpt-oss-120b"

N_QUESTIONS = 100          # sample size
SEED = 42                  # keeps the same 100 questions every run
COMPRESSION_RATIOS = [2, 5, 10, 20]

# ---- TextGrad repair stage ----
REPAIR_RATIOS = [5, 10, 20]   # compression levels to repair
N_REPAIR = 30                 # questions per level (keeps within the free daily limit)
REPAIR_ROUNDS = 1             # feedback + rewrite rounds per question

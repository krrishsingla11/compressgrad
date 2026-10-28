import json
import random
from datasets import load_dataset
from config import N_QUESTIONS, SEED

# HotpotQA "distractor" setting: each question comes with ~10 paragraphs (2 real + distractors)
ds = load_dataset("hotpotqa/hotpot_qa", "distractor", split="validation")

random.seed(SEED)
indices = random.sample(range(len(ds)), N_QUESTIONS)

items = []
for i in indices:
    row = ds[i]
    titles = row["context"]["title"]
    sentences = row["context"]["sentences"]
    context = "\n\n".join(
        f"{t}: {' '.join(s)}" for t, s in zip(titles, sentences)
    )
    items.append({
        "id": row["id"],
        "question": row["question"],
        "answer": row["answer"],
        "context": context,
    })

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Saved {len(items)} questions to data.json")
print("Example question:", items[0]["question"])
print("Example answer:  ", items[0]["answer"])
print("Context length (words):", len(items[0]["context"].split()))

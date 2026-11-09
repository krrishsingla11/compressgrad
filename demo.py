"""Side-by-side demo: full context vs plain LLMLingua-2 vs question-aware compression (+ repair).

Usage: python demo.py                      question 1 of the sample at 5x
       python demo.py --id 7 --ratio 10    another sample question / level
       python demo.py --repair             also run TextGrad repair on the compressed answer
       python demo.py --file notes.txt --question "Who founded the company?"   your own text

For sample questions the token budget matches compressed.json, so the answers come from the
cache and the demo runs offline after the experiments have been run once.
"""
import argparse
import json

from config import ANSWER_MODEL
from metrics import f1_score
from pipeline import compress_and_answer
from utils import ask, build_prompt, final_answer

ap = argparse.ArgumentParser()
ap.add_argument("--id", type=int, default=1, help="question number in data.json (1-100)")
ap.add_argument("--ratio", type=int, default=5, choices=[2, 5, 10, 20])
ap.add_argument("--repair", action="store_true")
ap.add_argument("--file")
ap.add_argument("--question")
args = ap.parse_args()

gold, plain_ctx, budget = None, None, None
if args.file:
    with open(args.file, encoding="utf-8") as f:
        context = f.read()
    question = args.question or input("Question: ")
else:
    with open("data.json", encoding="utf-8") as f:
        item = json.load(f)[args.id - 1]
    with open("compressed.json", encoding="utf-8") as f:
        plain = next(r for r in json.load(f)[str(args.ratio)] if r["id"] == item["id"])
    context, question, gold = item["context"], item["question"], item["answer"]
    plain_ctx, budget = plain["context"], plain["compressed_tokens"]


def show(label, answer, tokens):
    score = f"   F1 {f1_score(answer, gold):.2f}" if gold else ""
    print(f"{label:<34}{answer!r:<40} {tokens:>5} tokens{score}")


print(f"Question: {question}" + (f"\nGold:     {gold}" if gold else "") + "\n")
out = compress_and_answer(context, question, args.ratio, budget=budget, use_repair=args.repair)
show("Full context", final_answer(ask(build_prompt(context, question), ANSWER_MODEL)["text"]), out["tokens_full"])
if plain_ctx:
    show(f"Plain LLMLingua-2 ({args.ratio}x)",
         final_answer(ask(build_prompt(plain_ctx, question), ANSWER_MODEL)["text"]), budget)
show(f"Question-aware ({args.ratio}x)", out["draft"], out["tokens_compressed"])
if args.repair:
    show("Question-aware + TextGrad repair", out["final"], out["tokens_compressed"])
print("\nCompressed context the model saw:\n" + out["compressed"])

import json
import os

from llmlingua import PromptCompressor
from config import COMPRESSION_RATIOS

OUT = "compressed.json"

with open("data.json", encoding="utf-8") as f:
    data = json.load(f)

done = {}
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as f:
        done = json.load(f)

compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True,
    device_map="cpu",
)

for ratio in COMPRESSION_RATIOS:
    key = str(ratio)
    if key in done:
        print(f"{ratio}x already done, skipping")
        continue

    rows = []
    for i, item in enumerate(data, 1):
        r = compressor.compress_prompt(
            item["context"],
            rate=1 / ratio,            # fraction of tokens to KEEP
            force_tokens=["\n"],
            drop_consecutive=True,
        )
        rows.append({
            "id": item["id"],
            "context": r["compressed_prompt"],
            "origin_tokens": r["origin_tokens"],
            "compressed_tokens": r["compressed_tokens"],
        })
        if i % 10 == 0:
            print(f"  {ratio}x: {i}/{len(data)}")

    done[key] = rows
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(done, f, ensure_ascii=False, indent=2)

    orig = sum(r["origin_tokens"] for r in rows)
    comp = sum(r["compressed_tokens"] for r in rows)
    print(f"{ratio}x done. Actual ratio: {orig / comp:.1f}x")

print("All compression finished. Saved to", OUT)

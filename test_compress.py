from llmlingua import PromptCompressor

compressor = PromptCompressor(
    model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
    use_llmlingua2=True,
    device_map="cpu",
)

text = """The city council met on Tuesday to discuss the new transport budget.
After three hours of debate, the council voted to increase bus funding by
twelve percent, while delaying the planned metro extension until next year."""

# rate = fraction of tokens kept: 0.5 = 2x, 0.2 = 5x, 0.1 = 10x, 0.05 = 20x
result = compressor.compress_prompt(text, rate=0.5)

print("Compressed text:")
print(result["compressed_prompt"])
print()
print("Tokens:", result["origin_tokens"], "->", result["compressed_tokens"])

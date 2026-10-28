import os
import textgrad as tg
from textgrad.engine_experimental.litellm import LiteLLMEngine

if not os.environ.get("GROQ_API_KEY"):
    raise SystemExit("GROQ_API_KEY is not set. Run: set GROQ_API_KEY=your-key-here")

# If you get "model not found", swap in a current model name from the Groq console
MODEL = "groq/openai/gpt-oss-120b"

engine = LiteLLMEngine(model_string=MODEL, cache=False)
tg.set_backward_engine(engine, override=True)
model = tg.BlackboxLLM(engine)

question = tg.Variable(
    "What did the council vote to do with bus funding?",
    role_description="question",
    requires_grad=False,
)

answer = model(question)
answer.set_role_description("short factual answer")
print("Before:", answer.value)
print()

loss_fn = tg.TextLoss("Check if this answer is short, factual and complete. Give feedback.")
optimizer = tg.TGD(parameters=[answer], engine=engine)

loss = loss_fn(answer)
loss.backward()
optimizer.step()

print("After:", answer.value)

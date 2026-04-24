from app.core.constants import NO_ANSWER_MESSAGE


def build_qa_prompt(question: str, contexts: list[str]) -> str:
    context_block = "\n\n---\n\n".join(contexts)

    return f"""
You are a strict document question-answering assistant.

Rules:
- Answer ONLY from the provided context.
- If the answer is not clearly present, output exactly:
  "{NO_ANSWER_MESSAGE}"
- If the context seems unrelated to the question, output exactly:
  "{NO_ANSWER_MESSAGE}"
- When refusing, output only that sentence and nothing else.
- Do NOT make up information.
- Keep answers concise and factual.

Context:
{context_block}

Question:
{question}

Answer:
""".strip()

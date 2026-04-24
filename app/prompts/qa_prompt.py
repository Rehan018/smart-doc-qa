def build_qa_prompt(question: str, contexts: list[str]) -> str:
    context_block = "\n\n---\n\n".join(contexts)

    return f"""
You are a strict document question-answering assistant.

Rules:
- Answer ONLY from the provided context.
- If the answer is not clearly present, output exactly:
  "I couldn't find a reliable answer in the uploaded documents."
- If the context seems unrelated to the question, output exactly:
  "I couldn't find a reliable answer in the uploaded documents."
- When refusing, output only that sentence and nothing else.
- Do NOT make up information.
- Keep answers concise and factual.

Context:
{context_block}

Question:
{question}

Answer:
""".strip()

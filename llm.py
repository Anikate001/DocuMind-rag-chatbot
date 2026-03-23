import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def answer_with_citations(query: str, context: str, citations: list[str]) -> str:
    """
    Send query + retrieved context to Groq Llama3.
    Instructs it to cite sources and never hallucinate.
    """
    system_prompt = """You are a precise document assistant. Answer questions ONLY using the provided source excerpts.

Rules:
- Cite sources using [1], [2], [3] etc. after each claim
- If the answer is not in the sources, say "I couldn't find that in the uploaded documents"
- Never make up information not present in the sources
- Be concise but complete
- At the end, list which sources you used"""

    user_message = f"""Sources:
{context}

Question: {query}

Answer with citations:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # free on Groq, very capable
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        temperature=0.1,           # low temp = factual, less hallucination
        max_tokens=1024
    )

    answer = response.choices[0].message.content

    # Append citation legend
    citation_legend = "\n\n**Sources used:**\n" + "\n".join(citations)
    return answer + citation_legend
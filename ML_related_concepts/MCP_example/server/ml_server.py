import json
import math

from mcp.server import FastMCP

server = FastMCP("ML Tools")


@server.tool()
def sentiment_analysis(text: str) -> str:
    """Score text sentiment from -1 (negative) to 1 (positive)."""
    positive = {"good", "great", "excellent", "amazing", "love", "best"}
    negative = {"bad", "terrible", "awful", "horrible", "hate", "worst"}
    words = set(text.lower().split())
    pos = len(words & positive)
    neg = len(words & negative)
    total = pos + neg
    score = round((pos - neg) / total, 4) if total else 0.0
    label = "positive" if score > 0.3 else "negative" if score < -0.3 else "neutral"
    return json.dumps({"score": score, "label": label})


@server.tool()
def text_statistics(text: str) -> str:
    """Count characters, words, and average word length."""
    words = text.split()
    wc = len(words)
    return json.dumps({
        "char_count": len(text),
        "word_count": wc,
        "avg_word_length": round(len(text) / wc, 2) if wc else 0,
    })


@server.tool()
def cosine_similarity(vec1: list[float], vec2: list[float]) -> str:
    """Compute cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return json.dumps({"error": "Vectors must have the same length"})
    dot = sum(a * b for a, b in zip(vec1, vec2))
    n1 = math.sqrt(sum(a * a for a in vec1))
    n2 = math.sqrt(sum(b * b for b in vec2))
    if n1 == 0 or n2 == 0:
        return json.dumps({"error": "Zero vector"})
    return json.dumps({"similarity": round(dot / (n1 * n2), 4)})


if __name__ == "__main__":
    server.run(transport="stdio")

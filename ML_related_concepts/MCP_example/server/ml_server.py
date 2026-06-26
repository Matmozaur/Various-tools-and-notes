import math
import json
import csv
import io

from mcp.server import FastMCP

server = FastMCP("ML Tools Server")


def _sentiment_score(text: str) -> float:
    positive = {"good", "great", "excellent", "amazing", "fantastic", "positive",
                "wonderful", "love", "beautiful", "happy", "awesome", "best"}
    negative = {"bad", "terrible", "awful", "horrible", "negative",
                "hate", "ugly", "sad", "worst", "poor", "disgusting"}
    words = set(text.lower().split())
    pos_count = len(words & positive)
    neg_count = len(words & negative)
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return round((pos_count - neg_count) / total, 4)


@server.tool()
def sentiment_analysis(text: str) -> str:
    score = _sentiment_score(text)
    if score > 0.3:
        label = "positive"
    elif score < -0.3:
        label = "negative"
    else:
        label = "neutral"
    return json.dumps({"score": score, "label": label})


@server.tool()
def text_statistics(text: str) -> str:
    words = text.split()
    char_count = len(text)
    word_count = len(words)
    avg_word_length = round(char_count / word_count, 2) if word_count else 0
    return json.dumps({
        "char_count": char_count,
        "word_count": word_count,
        "avg_word_length": avg_word_length,
    })


@server.tool()
def cosine_similarity(vec1: list[float], vec2: list[float]) -> str:
    if len(vec1) != len(vec2):
        return json.dumps({"error": "Vectors must have the same length"})
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return json.dumps({"error": "Vectors must not be zero"})
    return json.dumps({"similarity": round(dot / (norm1 * norm2), 4)})


@server.tool()
def describe_dataset(csv_content: str) -> str:
    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    if not rows:
        return json.dumps({"error": "Empty CSV"})
    columns = list(rows[0].keys())
    numeric_cols = {}
    for col in columns:
        values = []
        for row in rows:
            val = row.get(col)
            if val is None:
                continue
            try:
                values.append(float(val))
            except (ValueError, TypeError):
                pass
        if values:
            numeric_cols[col] = {
                "min": min(values),
                "max": max(values),
                "mean": round(sum(values) / len(values), 4),
                "count": len(values),
            }
    return json.dumps({
        "rows": len(rows),
        "columns": columns,
        "numeric_statistics": numeric_cols,
    })


if __name__ == "__main__":
    server.run(transport="stdio")

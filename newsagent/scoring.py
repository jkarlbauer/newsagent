import numpy as np

DUPLICATE_THRESHOLD = 0.85


def _cosine_distance(a, b):
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return 1 - float(a @ b)


def _cosine_similarity(a, b):
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float(a @ b)


def _centroid(articles):
    return np.stack([a.embedding for a in articles]).mean(axis=0)


def _duplicate_count(article, all_articles):
    return sum(
        1 for other in all_articles
        if _cosine_similarity(article.embedding, other.embedding) >= DUPLICATE_THRESHOLD
    )


def score_articles(articles):
    if not articles:
        return articles
    centroid = _centroid(articles)
    for article in articles:
        distance = _cosine_distance(article.embedding, centroid)
        duplicates = _duplicate_count(article, articles)
        article.score = (1 - distance) * duplicates
    return articles


def select_top(articles, n):
    ranked = sorted(articles, key=lambda a: a.score, reverse=True)
    selected = []
    for candidate in ranked:
        if all(_cosine_similarity(candidate.embedding, s.embedding) < DUPLICATE_THRESHOLD for s in selected):
            selected.append(candidate)
        if len(selected) == n:
            break
    return selected

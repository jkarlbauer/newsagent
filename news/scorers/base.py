from abc import ABC, abstractmethod

import numpy as np

DUPLICATE_THRESHOLD = 0.91


class Scorer(ABC):
    @abstractmethod
    def score(self, articles: list) -> list:
        ...


def cosine_similarity(a, b):
    a = a / (np.linalg.norm(a) + 1e-9)
    b = b / (np.linalg.norm(b) + 1e-9)
    return float(a @ b)
    

def select_top(articles, n, threshold=DUPLICATE_THRESHOLD):
    ranked = sorted(articles, key=lambda a: a.score, reverse=True)
    selected = []
    for candidate in ranked:
        if all(cosine_similarity(candidate.embedding, s.embedding) < threshold for s in selected):
            selected.append(candidate)
        if len(selected) == n:
            break
    if len(selected) < n:
        for candidate in ranked:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) == n:
                break
    return selected

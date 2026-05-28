import numpy as np

from news.scorers.base import Scorer, cosine_similarity, DUPLICATE_THRESHOLD


class CombinedScorer(Scorer):
    """Scores by proximity to corpus centroid weighted by duplicate count.
    score = (1 - distance_from_centroid) * duplicates
    """

    def score(self, articles: list) -> list:
        if not articles:
            return articles

        embeddings = np.stack([a.embedding for a in articles])
        centroid = embeddings.mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
        total = len(articles)

        for article in articles:
            e = article.embedding / (np.linalg.norm(article.embedding) + 1e-9)
            proximity = float(e @ centroid)
            duplicates = sum(
                1 for other in articles
                if cosine_similarity(article.embedding, other.embedding) >= DUPLICATE_THRESHOLD
            )
            article.score = (1 - (1 - proximity) / 2) * duplicates
            article.coverage = duplicates / total

        return articles

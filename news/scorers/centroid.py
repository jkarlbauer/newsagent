import numpy as np

from news.scorers.base import Scorer


class CentroidProximityScorer(Scorer):
    """Scores by proximity to the corpus centroid — articles closest to the average topic rank higher."""

    def score(self, articles: list) -> list:
        if not articles:
            return articles
        centroid = np.stack([a.embedding for a in articles]).mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
        dists = []
        for article in articles:
            e = article.embedding / (np.linalg.norm(article.embedding) + 1e-9)
            dists.append(float(e @ centroid))
        min_d, max_d = min(dists), max(dists)
        span = max_d - min_d or 1.0
        for article, d in zip(articles, dists):
            article.score = d
            article.coverage = (d - min_d) / span
        return articles

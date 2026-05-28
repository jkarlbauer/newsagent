from news.scorers.base import Scorer, cosine_similarity, DUPLICATE_THRESHOLD


class DuplicateCountScorer(Scorer):
    """Scores by how many near-duplicate articles exist — denser topic clusters rank higher."""

    def score(self, articles: list) -> list:
        if not articles:
            return articles
        total = len(articles)
        for article in articles:
            duplicates = sum(
                1 for other in articles
                if cosine_similarity(article.embedding, other.embedding) >= DUPLICATE_THRESHOLD
            )
            article.score = duplicates
            article.coverage = duplicates / total
        return articles

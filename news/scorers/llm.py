import json
import time

import numpy as np
from sklearn.cluster import DBSCAN
from openai import OpenAI, APIStatusError

from news.scorers.base import Scorer, cosine_similarity, DUPLICATE_THRESHOLD

PROMPT_PATH = "prompts/rank.md"
CANDIDATES_PER_CLUSTER = 3
DBSCAN_EPS = 0.4
DBSCAN_MIN_SAMPLES = 2
MAX_RETRIES = 4
BACKOFF_BASE = 2


class LLMRankingScorer(Scorer):
    """Clusters articles with DBSCAN, picks the 3 articles closest to each cluster
    center (skipping near-duplicates), then asks an LLM to rank that pre-selection.

    coverage = fraction of the corpus that near-duplicates the article.
    score    = normalised rank from the LLM (1.0 = top); non-candidates get 0.
    """

    def __init__(self, config, user_topics: list[str]):
        self.client = OpenAI(
            api_key=config["deepseek_api_key"],
            base_url="https://api.deepseek.com",
        )
        self.model = config["deepseek_model"]
        self.user_topics = user_topics
        with open(PROMPT_PATH) as f:
            self.prompt = f.read()

    def score(self, articles: list) -> list:
        if not articles:
            return articles

        total = len(articles)
        embeddings = np.stack([a.embedding for a in articles])

        for i, article in enumerate(articles):
            duplicates = sum(
                1 for j in range(total)
                if cosine_similarity(embeddings[i], embeddings[j]) >= DUPLICATE_THRESHOLD
            )
            article.coverage = duplicates / total
            article.score = 0.0

        labels = DBSCAN(
            eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES, metric="cosine"
        ).fit_predict(embeddings)

        candidates = self._pick_candidates(embeddings, labels)
        n_clusters = len(set(labels) - {-1})
        n_noise = int(np.sum(labels == -1))
        print(f"  [llm_scorer] DBSCAN(eps={DBSCAN_EPS}): {n_clusters} clusters, "
              f"{n_noise} noise, {len(candidates)} candidates")

        if not candidates:
            candidates = list(range(total))

        ranked = self._llm_rank(candidates, articles)
        n = len(ranked)
        for rank, idx in enumerate(ranked):
            articles[idx].score = (n - rank) / n

        return articles

    def _pick_candidates(self, embeddings: np.ndarray, labels: np.ndarray) -> list[int]:
        selected: list[int] = []
        for cid in sorted(set(labels) - {-1}):
            members = np.where(labels == cid)[0]
            centroid = embeddings[members].mean(axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
            ranked_members = sorted(
                ((cosine_similarity(embeddings[idx], centroid), int(idx)) for idx in members),
                reverse=True,
            )
            picked = 0
            for _, idx in ranked_members:
                if picked >= CANDIDATES_PER_CLUSTER:
                    break
                if all(cosine_similarity(embeddings[idx], embeddings[s]) < DUPLICATE_THRESHOLD
                       for s in selected):
                    selected.append(idx)
                    picked += 1
        return selected

    def _llm_rank(self, candidate_indices: list[int], articles: list) -> list[int]:
        titles = [articles[i].title for i in candidate_indices]
        numbered = "\n".join(f"{j}. {t}" for j, t in enumerate(titles))
        user_msg = f"User interests: {', '.join(self.user_topics)}\n\nArticles:\n{numbered}"

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt},
                        {"role": "user", "content": user_msg},
                    ],
                )
                local_order = json.loads(response.choices[0].message.content.strip())
                seen: set[int] = set()
                result: list[int] = []
                for local_idx in local_order:
                    if 0 <= local_idx < len(candidate_indices):
                        idx = candidate_indices[local_idx]
                        if idx not in seen:
                            seen.add(idx)
                            result.append(idx)
                for idx in candidate_indices:
                    if idx not in seen:
                        result.append(idx)
                print(f"  [llm_scorer] ranked {len(result)} candidates:")
                for rank, idx in enumerate(result):
                    print(f"    {rank + 1}. {articles[idx].title}")
                return result
            except (APIStatusError, json.JSONDecodeError, ValueError) as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"  LLM ranking failed: {e}, falling back to candidate order")
                    return candidate_indices
                time.sleep(BACKOFF_BASE ** attempt)

        return candidate_indices

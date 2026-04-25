import numpy as np


class Embedder:
    def __init__(self, config):
        from sentence_transformers import SentenceTransformer
        model_name = config["embedding_model"]
        batch_size = config["embedding_batch_size"]
        overlap = config["embedding_overlap"]
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
        self.tokenizer = self.model.tokenizer
        self.batch_size = batch_size
        self.overlap = overlap
        self.chunk_size = self.tokenizer.model_max_length - 2

    def _chunk(self, text):
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) <= self.chunk_size:
            return [text]
        step = int(self.chunk_size * (1 - self.overlap))
        chunks = []
        start = 0
        while start < len(token_ids):
            end = min(start + self.chunk_size, len(token_ids))
            chunks.append(self.tokenizer.decode(token_ids[start:end], skip_special_tokens=True))
            if end == len(token_ids):
                break
            start += step
        return chunks

    def _embed_chunks(self, chunks):
        return self.model.encode(chunks, batch_size=self.batch_size, show_progress_bar=False, convert_to_numpy=True)

    def embed(self, text):
        chunks = self._chunk(text)
        embeddings = self._embed_chunks(chunks)
        return np.mean(embeddings, axis=0).astype(np.float32)

    def embed_articles(self, articles):
        for article in articles:
            article.embedding = self.embed(article.content)
        return articles

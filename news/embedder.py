import numpy as np


class Embedder:
    def __init__(self, config):
        from sentence_transformers import SentenceTransformer
        self.batch_size = config["embedding_batch_size"]
        self.overlap = config["embedding_overlap"]
        self.model = SentenceTransformer(config["embedding_model"], trust_remote_code=True)
        self.tokenizer = self.model.tokenizer
        self.chunk_size = self.model.max_seq_length - 2  # reserve 2 for CLS/SEP

    def _chunk_token_ids(self, text):
        token_ids = self.tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) <= self.chunk_size:
            return [token_ids]
        step = int(self.chunk_size * (1 - self.overlap))
        chunks, start = [], 0
        while start < len(token_ids):
            end = min(start + self.chunk_size, len(token_ids))
            chunks.append(token_ids[start:end])
            if end == len(token_ids):
                break
            start += step
        return chunks

    def _encode_batch(self, batch_token_ids):
        import torch
        cls_id = self.tokenizer.cls_token_id
        sep_id = self.tokenizer.sep_token_id
        pad_id = self.tokenizer.pad_token_id or 0

        sequences = [[cls_id] + ids + [sep_id] for ids in batch_token_ids]
        max_len = max(len(s) for s in sequences)

        input_ids = torch.full((len(sequences), max_len), pad_id, dtype=torch.long)
        attention_mask = torch.zeros(len(sequences), max_len, dtype=torch.long)
        for i, seq in enumerate(sequences):
            input_ids[i, :len(seq)] = torch.tensor(seq, dtype=torch.long)
            attention_mask[i, :len(seq)] = 1

        with torch.no_grad():
            out = self.model({"input_ids": input_ids, "attention_mask": attention_mask})
        return out["sentence_embedding"].cpu().numpy()

    def embed_articles(self, articles):
        all_chunk_ids = []
        chunk_counts = []
        for article in articles:
            chunks = self._chunk_token_ids(article.content)
            all_chunk_ids.extend(chunks)
            chunk_counts.append(len(chunks))

        all_embeddings = np.vstack([
            self._encode_batch(all_chunk_ids[i:i + self.batch_size])
            for i in range(0, len(all_chunk_ids), self.batch_size)
        ])

        offset = 0
        for article, count in zip(articles, chunk_counts):
            article.embedding = np.mean(all_embeddings[offset:offset + count], axis=0).astype(np.float32)
            offset += count

        return articles

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from typing import List

class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "keepitreal/vietnamese-sbert"):
        print(f"Đang tải embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Embedding model đã sẵn sàng.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()

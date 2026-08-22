from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embedding(text):
    embedding = model.encode(text)
    return np.array(embedding).astype("float32")
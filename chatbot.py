import sqlite3
import numpy as np
from .embeddings import create_embedding

DB_NAME = "noticeboard.db"


def get_notices():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    notices = conn.execute("""
        SELECT id, title, body, date
        FROM notices
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return notices


def search_notices(question, top_k=3):

    notices = get_notices()

    if not notices:
        return []

    question_embedding = create_embedding(question)

    results = []

    for notice in notices:

        text = notice["title"] + " " + notice["body"]

        notice_embedding = create_embedding(text)

        similarity = np.dot(
            question_embedding,
            notice_embedding
        ) / (
            np.linalg.norm(question_embedding) *
            np.linalg.norm(notice_embedding)
        )

        results.append(
            (similarity, notice)
        )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:top_k]
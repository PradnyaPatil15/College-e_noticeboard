import sqlite3
import numpy as np
from .embeddings import create_embedding
from .nlp import preprocess_text, detect_category, detect_intent

DB_NAME = "noticeboard.db"


def get_notices():

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    notices = conn.execute("""
        SELECT id, title, body, date,category
        FROM notices
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return notices


def search_notices(question, top_k=3):

    # ---------------- NLP ----------------
    words = preprocess_text(question)

    category = detect_category(words)
    intent = detect_intent(words)

    print("Question:", question)
    print("Category:", category)
    print("Intent:", intent)

    # ---------------- GET NOTICES ----------------
    notices = get_notices()

    if not notices:
        return []

    # ---------------- QUESTION EMBEDDING ----------------
    question_embedding = create_embedding(question)

    results = []

    for notice in notices:

        text = notice["title"] + " " + notice["body"]

        notice_embedding = create_embedding(text)

        # Avoid division by zero
        denominator = (
            np.linalg.norm(question_embedding) *
            np.linalg.norm(notice_embedding)
        )

        if denominator == 0:
            similarity = 0
        else:
            similarity = np.dot(
                question_embedding,
                notice_embedding
            ) / denominator

        # ---------------- CATEGORY BONUS ----------------
        category_bonus = 0

        if category and notice["category"]:
            if category.lower() == notice["category"].lower():
                category_bonus = 0.20

        # Final score
        final_score = similarity + category_bonus

        results.append(
            (final_score, notice)
        )

    # ---------------- SORT ----------------
    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:top_k]

import nltk

nltk.download("stopwords")
nltk.download("punkt")
nltk.download("punkt_tab")

from nltk.corpus import stopwords

stop_words = set(stopwords.words("english"))

# Lemmatizer
lemmatizer = WordNetLemmatizer()


# -----------------------------------------
# CATEGORY KEYWORDS
# -----------------------------------------

CATEGORY_KEYWORDS = {

    "Placement": [
        "placement",
        "job",
        "recruitment",
        "campus",
        "company",
        "career",
        "hiring",
        "interview",
        "drive",
        "package"
    ],

    "Exam": [
        "exam",
        "examination",
        "test",
        "internal",
        "semester",
        "paper",
        "assessment",
        "schedule"
    ],

    "Internship": [
        "internship",
        "intern",
        "training",
        "stipend"
    ],

    "Event": [
        "event",
        "fest",
        "competition",
        "techsprint",
        "hackathon"
    ],

    "Workshop": [
        "workshop",
        "seminar",
        "session",
        "webinar"
    ],

    "Scholarship": [
        "scholarship",
        "freeship",
        "financial",
        "grant"
    ]
}

# -----------------------------------------
# NLP PREPROCESSING
# -----------------------------------------

def preprocess_text(text):

    # Lowercase
    text = text.lower()

    # Remove special characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Tokenization
    words = nltk.word_tokenize(text)

    # Stopword removal
    words = [
        word
        for word in words
        if word not in stop_words
    ]

    # Lemmatization
    words = [
        lemmatizer.lemmatize(word)
        for word in words
    ]

    return words


# -----------------------------------------
# CATEGORY DETECTION
# -----------------------------------------

def detect_category(words):

    for category, keywords in CATEGORY_KEYWORDS.items():

        for word in words:

            if word in keywords:
                return category

    return None


# -----------------------------------------
# INTENT DETECTION
# -----------------------------------------

def detect_intent(words):

    # Date / Deadline Query
    if any(word in words for word in [
        "when",
        "date",
        "deadline",
        "last",
        "schedule",
        "timing"
    ]):
        return "DATE_QUERY"

    # Eligibility Query
    if any(word in words for word in [
        "who",
        "eligible",
        "eligibility",
        "apply",
        "requirement",
        "requirements"
    ]):
        return "ELIGIBILITY_QUERY"

    # Summary / Information Query
    if any(word in words for word in [
        "summary",
        "summarize",
        "about",
        "tell",
        "information",
        "details",
        "detail",
        "explain",
        "what"
    ]):
        return "SUMMARY_QUERY"

    # Latest Notices
    if any(word in words for word in [
        "latest",
        "recent",
        "new",
        "newest"
    ]):
        return "LATEST_NOTICES"

    # Normal Search
    return "SEARCH"

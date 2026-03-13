"""
Train a topic classifier on existing questions.csv using TF-IDF + Naive Bayes.
Can auto-classify new questions given a task description.

Usage:
    python classifier.py                          # prints accuracy report
    python classifier.py "construct a truth table" # predicts topic for input
"""
import pandas as pd
import sys
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.csv")


def load_and_train():
    df = pd.read_csv(CSV_PATH)
    df['text'] = df['task'].fillna('') + ' ' + df['keywords'].fillna('')

    topic_model = Pipeline([('tfidf', TfidfVectorizer()), ('clf', MultinomialNB())])
    sub_model = Pipeline([('tfidf', TfidfVectorizer()), ('clf', MultinomialNB())])

    topic_model.fit(df['text'], df['topic'])
    sub_model.fit(df['text'], df['sub_topic'])

    return topic_model, sub_model, df


def classify(text, topic_model, sub_model):
    return topic_model.predict([text])[0], sub_model.predict([text])[0]


if __name__ == "__main__":
    topic_model, sub_model, df = load_and_train()

    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        topic, sub = classify(text, topic_model, sub_model)
        print(f"topic: {topic}")
        print(f"sub_topic: {sub}")
    else:
        X = df['task'].fillna('') + ' ' + df['keywords'].fillna('')

        topic_scores = cross_val_score(
            Pipeline([('tfidf', TfidfVectorizer()), ('clf', MultinomialNB())]),
            X, df['topic'], cv=5)
        sub_scores = cross_val_score(
            Pipeline([('tfidf', TfidfVectorizer()), ('clf', MultinomialNB())]),
            X, df['sub_topic'], cv=3)

        print(f"topic accuracy:     {topic_scores.mean():.0%}")
        print(f"sub-topic accuracy: {sub_scores.mean():.0%}")
        print(f"trained on {len(df)} questions, {df['topic'].nunique()} topics")
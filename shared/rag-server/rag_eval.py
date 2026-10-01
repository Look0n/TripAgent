"""Manual Account retrieval smoke evaluation.

This does not invent or pre-populate metrics. Run it after the Account corpus
has been refreshed to inspect retrieval results.
"""
import json
from rag_pipeline import retrieve_context

TEST_QUERIES = [
    "What are travel preferences?",
    "Can a customer update their profile?",
    "Are AI preference suggestions saved automatically?",
]

if __name__ == "__main__":
    for query in TEST_QUERIES:
        print("\nQUERY:", query)
        print(json.dumps(retrieve_context(query, feature="account", k=3, caller="rag_eval"), indent=2))

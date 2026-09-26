# TripAgent Shared RAG Tool Contracts

The shared RAG service follows the Lab 8 pipeline while separating retrieval by TripAgent feature.

## Supported features
`account`, `accommodation`, `attractions`, `checklist`, `flight`

## Tools
- `refresh_corpus(feature, caller)` dynamically rebuilds only the selected feature corpus and Chroma collection.
- `retrieve_context(query, feature, k, caller)` performs vector retrieval for the selected feature and falls back to lexical retrieval if needed.
- `answer_question(query, feature, k, caller)` produces a retrieval-grounded Ollama answer with citations and confidence category.

The Account backend fixes `feature=account`; browsers do not choose the RAG feature.


## Corpus and Chroma layout

Each TripAgent feature has one generated JSONL corpus named explicitly for the feature:

- `corpus/account-corpus.jsonl`
- `corpus/accommodation-corpus.jsonl`
- `corpus/attractions-corpus.jsonl`
- `corpus/checklist-corpus.jsonl`
- `corpus/flight-corpus.jsonl`

Chroma remains directory-based because a persistent Chroma store contains multiple database/index files:

- `chroma/account/`
- `chroma/accommodation/`
- `chroma/attractions/`
- `chroma/checklist/`
- `chroma/flight/`

`refresh_corpus(feature)` regenerates the matching feature corpus and indexes it into the matching feature Chroma store.

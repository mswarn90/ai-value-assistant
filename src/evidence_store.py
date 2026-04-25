import chromadb
import os

COLLECTION_NAME = "evidence"
DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".chromadb"))


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def store_evidence(entries: list[dict]) -> int:
    collection = get_collection()
    ids, documents, metadatas = [], [], []

    for entry in entries:
        doc = f"{entry['claim']} — {entry['source']}. Industry: {entry['industry']}. Value type: {entry['value_type']}."
        raw_id = f"{entry['source'][:40]}_{entry['claim'][:40]}"
        entry_id = "".join(c if c.isalnum() else "_" for c in raw_id).lower()[:80]

        ids.append(entry_id)
        documents.append(doc)
        metadatas.append({
            "claim": entry["claim"],
            "source": entry["source"],
            "industry": entry.get("industry", ""),
            "value_type": entry.get("value_type", ""),
            "url": entry.get("url", ""),
            "date_collected": entry.get("date_collected", ""),
        })

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def retrieve_evidence(query: str, n_results: int = 5) -> list[dict]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        return []
    n_results = min(n_results, count)
    results = collection.query(query_texts=[query], n_results=n_results)
    entries = []
    for i, metadata in enumerate(results["metadatas"][0]):
        entry = dict(metadata)
        if results.get("distances"):
            entry["_distance"] = results["distances"][0][i]
        entries.append(entry)
    return entries


def count_evidence() -> int:
    return get_collection().count()

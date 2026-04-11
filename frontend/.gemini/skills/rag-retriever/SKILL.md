---
name: rag-retriever
description: A structured workflow for efficiently exploring, mapping, and extracting information from 'rag-test' collections using RAG (Retrieval-Augmented Generation) and Knowledge Graph tools.
---

# RAG Retriever Skill

This skill provides a high-signal strategy for navigating and extracting knowledge from collections in the `rag-test` environment. It prioritizes synthetic knowledge (Summaries/Wiki) before deep-diving into raw text chunks.

## Core Workflow: The "Outside-In" Approach

### 1. Discovery & Anchoring
Always start by identifying the exact collection name and its high-level structure.
- **Identify Collection:** Use `collection_list()` to find the exact name.
- **Get the "Big Picture":** Call `get_summaries(collection_name, summary_type=2)` (Type 2 is BOOK) to get genre, main characters, and themes immediately.
- **Map the Structure:** Call `get_table_of_contents(collection_name)` to understand chapter progression and chunk distribution.

### 2. Entity Exploration (Wiki-First)
Before using keyword searches on raw text, use the Wiki tools to get synthesized character and plot data.
- **Browse Entities:** Use `get_wiki_index(collection_id)` to see available characters, locations, and concepts.
- **Deep Dive:** Use `get_wiki_page(page_id)` for specific entities (e.g., "Captain Ahab"). Wiki pages often contain curated relations and significance that raw chunks lack.

### 3. Relational Mapping (Graph)
Use the Knowledge Graph to verify structural and character relationships.
- **Verify Schema:** Run a generic query like `MATCH (n) RETURN labels(n), keys(n) LIMIT 5` if you are unsure of the graph structure.
- **Common Patterns:**
    - `MATCH (c:COLLECTION {name: 'Name'})-[:CONTAINS]->(ch:CHAPTER) RETURN ch.name`
    - `MATCH (p1:PERSON {name: 'A'})-[r]-(p2:PERSON {name: 'B'}) RETURN type(r)`

### 4. Evidence Extraction (Raw Query)
Use `query_collection` only after you have a specific target or need direct quotes.
- **Keyword Strategy:** Combine entity names with specific action/theme words (e.g., "Ishmael Queequeg marriage bed").
- **Navigation:** Use `get_chunks_by_id` to read surrounding context if a query result is truncated or needs more "flavor."

## Success Tips & Pitfalls
- **Avoid Parallelism Issues:** Do NOT use the `wait_for_previous` parameter with `rag-test` MCP tools unless explicitly confirmed to work; standard parallel calls are safer.
- **Relationship Names:** Don't guess relationship types. Use `MATCH ()-[r]->() RETURN DISTINCT type(r)` to see what's available.
- **Chunk vs. Summary:** Use `get_chunks_by_id` for *what* happened; use `get_summaries` or `get_wiki_page` for *why* it matters.

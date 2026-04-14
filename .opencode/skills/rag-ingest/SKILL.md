---
name: rag-ingest
description: Complete book ingestion pipeline - hierarchical RAG summaries → wiki pages → graph nodes, with QA checks between each step
license: MIT
compatibility: opencode
metadata:
  audience: user
  workflow: rag, wiki, graph, ingestion-pipeline
  version: 1
---

# RAG Ingest Pipeline

Complete pipeline for ingesting books into knowledge base with 3 sequential steps:
1. **Hierarchical RAG** - Build chapter summaries from TOC
2. **RAG Wiki** - Create wiki pages for characters, themes, plot
3. **RAG Graph** - Create graph nodes and relationships

## IMPORTANT: Sequential Pipeline

**Each step depends on the previous step completing first.**

Do NOT skip steps. After each step, ask user before proceeding to next step.

## Step 1: Hierarchical RAG

### Purpose
Build hierarchical RAG summaries by finding Table of Contents, extracting chapter structure, and creating CHAPTER-level summaries.

### Workflow

1. **collection_list** → Find the book collection
2. **Ask user**: Which collection to process?
3. **Find TOC**: Search collection for "table of contents", "contents", "index"
4. **Parse chapters**: Extract chapter names from TOC
5. **Find chapter boundaries**: Get start chunk IDs for each chapter
6. **Create CHAPTER summaries**: For each chapter, create summary (summary_type=1)
7. **Optional CHUNKS**: If chapter >30 chunks, ask user before creating intermediate summaries
8. **Create BOOK summary**: From all chapter summaries (summary_type=2)
9. **Store TOC**: Store with add_table_of_contents

### QA Check (Step 1)

After completion, verify with graph query or manual check:

```python
# Verify CHAPTER summaries exist
get_summaries(collection_name="{book}", summary_type=1)

# Verify BOOK summary exists  
get_summaries(collection_name="{book}", summary_type=2)

# Get TOC
get_table_of_contents(collection_name="{book}")
```

**QA Checklist:**
- [ ] All chapters have summaries (summary_type=1)
- [ ] Book summary exists (summary_type=2)
- [ ] TOC stored with chapter_summary_ids
- [ ] No duplicate summaries
- [ ] All chapter_start_chunk_ids valid

### Ask User Before Step 2

```
Step 1 (Hierarchical RAG) complete.
- X CHAPTER summaries created
- BOOK summary created
- TOC stored

Proceed to Step 2 (RAG Wiki)? [Y/N]
```

---

## Step 2: RAG Wiki

### Purpose
Create wiki pages for characters, themes, plot summary, concepts from the book.

### Workflow

1. **Get BOOK summary**: Understand the book overview
2. **Get CHAPTER summaries**: List main events per chapter
3. **Query collection**: Search for key characters, themes
4. **Create wiki pages**:
   - **Source page**: Book overview (author, year, genre)
   - **Character pages**: Main characters (PERSON)
   - **Concept pages**: Major themes
   - **Analysis page**: Plot summary

### Wiki Page Types

| Type | Description |
|------|------------|
| source | Book overview, metadata |
| entity | Characters, people |
| concept | Themes, ideas |
| analysis | Plot summary, comparisons |

### QA Check (Step 2)

Verify wiki pages exist:

```python
get_wiki_index(collection_id="{book}")
```

**QA Checklist:**
- [ ] Source page created
- [ ] Main character pages created
- [ ] Theme/concept pages created
- [ ] Plot summary created
- [ ] All pages have valid cross-references
- [ ] No orphan pages (pages with no links)

**Launch QA Agent for wiki:**
```
Task prompt: "QA check on {book} wiki pages. Verify: all pages created, no orphans, cross-references valid."
```

### Ask User Before Step 3

```
Step 2 (RAG Wiki) complete.
- X wiki pages created
- Characters: list
- Themes: list

Proceed to Step 3 (RAG Graph)? [Y/N]
```

---

## Step 3: RAG Graph

### Purpose
Create Neo4j knowledge graph with chapters, entities, relationships.

### Workflow

1. **Get TOC**: Get chapter structure
2. **Create CHAPTER nodes**: For each chapter (linked to collection + chunks)
3. **Add PERSON entities**: Characters (from wiki pages)
4. **Add PLACE entities**: Locations
5. **Add EVENT entities**: Key plot events
6. **Link entities**: Create relationships between nodes
7. **QA check**: Verify graph integrity

### Node Types

| Type | Description |
|------|------------|
| CHAPTER | Book chapters |
| PERSON | Characters |
| PLACE | Locations |
| EVENT | Plot events |

### Relationships

Use allowed relations: INFLUENCES, LOVES, FRIEND_OF, KIN_OF, ENEMY_OF, RESIDES_IN, PARTICIPATED_IN, AFFECTS, etc.

### QA Check (Step 3)

Run graph QA:

```cypher
-- Verify chapters
MATCH (col:COLLECTION {name: '{book}'})-[r:CONTAINS]->(c:CHAPTER) RETURN count(c)

-- Verify entities
MATCH (e) WHERE e.collection_id = '{book}' RETURN labels(e), count(e)

-- Check relationships
MATCH (a)-[r]->(b) WHERE a.collection_id = '{book}' RETURN count(r)

-- Check for orphans
MATCH (e) WHERE e.collection_id = '{book}'
OPTIONAL MATCH (e)-[r]->(other)
WITH e, count(r) as rels WHERE rels = 0 RETURN e.name
```

**Launch QA Agent for graph:**
```
Task prompt: "QA check on {book} graph. Verify: chapters linked, entities added, relationships correct, no orphans."
```

**QA Checklist:**
- [ ] All chapters created and linked to collection
- [ ] All main characters added as PERSON
- [ ] All locations added as PLACE
- [ ] Key events added as EVENT
- [ ] No orphan nodes
- [ ] Relationship directions correct
- [ ] No duplicate relationships
- [ ] Graph health score 7+/10

### Ask User Completion

```
Step 3 (RAG Graph) complete.
- X CHAPTER nodes
- X PERSON nodes
- X PLACE nodes
- X EVENT nodes
- X relationships
- Health score: X/10

Pipeline complete! Book ingestion finished.
```

---

## Complete Pipeline Flow

```
Step 1: Hierarchical RAG
  ├── collection_list
  ├── Find TOC
  ├── Create CHAPTER summaries
  ├── Create BOOK summary
  ├── Store TOC
  └── QA check → ASK USER

Step 2: RAG Wiki  
  ├── Get summaries
  ├── Create wiki pages
  ├── QA check → ASK USER

Step 3: RAG Graph
  ├── Create chapters in graph
  ├── Add entities
  ├── Link relationships
  ├── QA check → DONE
```

## Health Score Definition

| Score | Criteria |
|-------|----------|
| 1-3 | Missing summaries or TOC |
| 4-6 | Summaries done, wiki incomplete |
| 7-8 | Wiki done, graph incomplete |
| 9-10 | All steps complete, QA passed |

## Usage

For any book in rag-test collection:

1. **Load rag-ingest skill**
2. **Confirm collection name**
3. **Run Step 1** → QA check → Ask user
4. **Run Step 2** → QA check → Ask user
5. **Run Step 3** → QA check → Complete

## Example: Dorian Gray

- Step 1: 20 CHAPTER summaries + BOOK summary + TOC
- Step 2: 11 wiki pages (source, 5 characters, 4 concepts, analysis)
- Step 3: 20 CHAPTER nodes + 6 PERSON + 3 PLACE + 4 EVENT + 15 relationships
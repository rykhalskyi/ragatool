---
name: hierarchical-rag-v1
description: Build hierarchical RAG summaries from existing vector chunks using rag-test MCP server
license: MIT
compatibility: opencode
metadata:
  audience: user
  workflow: rag, summarization, knowledge-management
  version: 3
---

# Hierarchical RAG - TOC-Based Chapter Summarization

## Overview

Builds hierarchical RAG summaries by **finding the Table of Contents**, extracting chapter structure, and creating CHAPTER-level summaries directly. CHUNKS level is only used when absolutely necessary (user approval required).

## Architecture

```
Level 0: Raw Chunks (existing source) - IDs like dracula.txt_1774557956_0
Level 1: CHAPTER (chapter summary) - direct from TOC, primary level
Level 2: CHUNKS (batched summaries) - ONLY when user approves for very large chapters
Level 3: BOOK (document overview) - single entry from all CHAPTER summaries
```

## MCP Tools (rag-test / ragatool servers)

| Tool | Purpose |
|------|---------|
| `collection_list` | List all available collections |
| `query_collection` | Search collection, returns chunks with IDs |
| `get_chunks_by_id` | Retrieve raw chunk texts by chunk IDs |
| `get_summaries` | Retrieve summaries by type (0=CHUNKS, 1=CHAPTER, 2=BOOK) |
| `add_summary` | Add new summary, returns GUID |
| `add_table_of_contents` | Store TOC |
| `get_table_of_contents` | Retrieve TOC |

**Server Addresses**: rag-test and ragatool are the same server on different addresses.

## Workflow

### Step 0: Ask User for Table of Contents

**IMPORTANT**: Before querying the collection, ask the user if they have a Table of Contents to provide.

1. **Ask user**: "Do you have a Table of Contents from the book? If so, copy and paste it below. The TOC should clearly list chapter names. You can optionally include chunk IDs at the start of each entry if you know them."

2. **If user provides TOC**:
   - **Extract chapter names**: Parse the list to get clear chapter names
   - **Extract chunk IDs** (optional): If TOC includes chunk IDs at start of entries, record them
   - **Build initial chapter scaffold**: Use provided info as primary chapter structure
   - If chunk IDs are provided, skip discovery; if not, proceed to Step 1-3 to find them

3. **If user declines or provides no TOC**: Proceed to Step 1 to discover TOC from collection

**User TOC Format Examples**:
```
Chapter 1: Jonathan Harker's Journal
Chapter 2: Journey to Castle
Chapter 3: The Hunt Begins
```

```
dracula.txt_1774557956_0 | Chapter 1: Jonathan Harker's Journal
dracula.txt_1774557956_25 | Chapter 2: Journey to Castle
```

```
Chapter I. Jonathan Harker's Journal ............... 1
Chapter II. Journey to Castle ..................... 25
```

### Step 1: Discover Collection & Find TOC

1. **List collections**: `collection_list`
2. **Ask user** which collection to process
3. **Query for TOC**: Try multiple queries to find Table of Contents:
   - `query_collection(collection_name, query_text="table of contents", n_results=3)`
   - `query_collection(collection_name, query_text="contents", n_results=3)`
   - `query_collection(collection_name, query_text="index", n_results=3)`
   - `query_collection(collection_name, query_text="chapter", n_results=3)`
4. **Identify TOC chunk**: Look for chunk containing:
   - "Table of Contents", "CONTENTS", "INDEX"
   - List of chapter titles/numbers
   - Page numbers alongside titles
5. **Get TOC chunk text**: `get_chunks_by_id(collection_name, ids=[toc_chunk_id])`

### Step 2: Extract Chapter List from TOC

Parse the TOC to extract:
- Chapter names/titles
- Page numbers (if available)
- Chapter order

### Step 3: Find Chapter Start Chunks

For each chapter from TOC:
1. **Query for chapter start**: `query_collection(collection_name, query_text="{chapter_name}", n_results=1)`
2. **Or iterate chunks**: Start from beginning, find chunk that matches chapter name
3. **Record**: `chapter_start_chunk_id` (raw chunk ID as returned by query)

### Step 4: Determine Chapter Boundaries

Between consecutive chapters:
1. Get chunk at chapter N start
2. Get chunk at chapter N+1 start (or end of book)
3. Calculate chunk count: `chapter_N+1_start_index - chapter_N_start_index`
4. If gaps exist (missing chunk IDs), query to fill in

### Step 5: Create CHAPTER Summaries (Primary)

**DEFAULT**: Create CHAPTER summary directly (summary_type=1):
- Get all raw chunk texts for the chapter
- Create comprehensive chapter summary
- Store `chunk_ids[]` - all raw chunk IDs covered

**EXCEPTION - CHUNKS level** (summary_type=0):
- ONLY if chapter has >30 chunks and summarization fails
- Ask user: "Chapter X has Y chunks. Create intermediate CHUNKS summaries?"
- If approved: batch ~10 chunks, create CHUNKS summaries, then CHAPTER

### Fallback: No TOC Found

If no TOC is found:
1. **Query for chapter markers**: Search for "Chapter", "CHAPTER", section numbers
2. **Iterate from start**: Walk chunks, detect chapter boundaries by text patterns
3. **Extract chapter names**: Parse chapter titles from chunk text
4. **Proceed with Step 3-5**: Use detected chapters for summarization

## Summary Schemas

### CHAPTER (Level 1) - PRIMARY
```json
{
  "summary_type": "CHAPTER",
  "chapter_name": "Chapter 1: Jonathan Harker's Journal",
  "chapter_index": 1,
  "chapter_start_chunk_id": "dracula.txt_1774557956_0",
  "summary": "Comprehensive chapter summary",
  "key_moments": ["event 1", "event 2"],
  "characters": ["Jonathan Harker", "Count Dracula"],
  "themes": ["imprisonment", "ancient evil"],
  "chunk_ids": ["dracula.txt_1774557956_0", "dracula.txt_1774557956_1", ...],
  "chunk_count": 25
}
```

### CHUNKS (Level 2) - OPTIONAL
Only created when user approves for very large chapters (>30 chunks).
```json
{
  "summary_type": "CHUNKS",
  "summary": "2-3 sentence summary of chunk batch",
  "chunk_ids": ["dracula.txt_1774557956_0", "dracula.txt_1774557956_1", ...],
  "chunk_count": 10,
  "chapter_name": "Chapter 1: Jonathan Harker's Journal",
  "parent_chapter_summary_id": "guid-of-chapter-summary"
}
```

### BOOK (Level 3)
```json
{
  "summary_type": "BOOK",
  "summary": "2-3 paragraph overview of entire book",
  "chapter_summary_ids": ["guid1", "guid2", ...],
  "num_chapters": 27,
  "total_chunks": 500,
  "main_characters": [{"name": "Jonathan Harker", "role": "protagonist"}],
  "major_themes": ["good vs evil", "immortality"]
}
```

## Table of Contents

**IMPORTANT**: TOC must store RAW CHUNK IDs as returned by query (e.g., `dracula.txt_1774557956_0`).

```json
{
  "book_title": "Dracula",
  "collection_name": "dracula",
  "chapters": [
    {
      "chapter_index": 1,
      "chapter_name": "Chapter I: Jonathan Harker's Journal",
      "chapter_start_chunk_id": "dracula.txt_1774557956_0",
      "chapter_summary_id": "8bf092ea-50f0-4478-8b82-3b14951ea0f4",
      "num_chunks": 25
    },
    {
      "chapter_index": 2,
      "chapter_name": "Chapter II: Journey to Castle",
      "chapter_start_chunk_id": "dracula.txt_1774557956_25",
      "chapter_summary_id": "111e6244-85d0-4047-8ec6-6758a613b140",
      "num_chunks": 30
    }
  ]
}
```

**Chunk ID Format**: `{filename}_{timestamp}_{number}` (e.g., `dracula.txt_1774557956_0`)
- These are the RAW IDs returned by `query_collection` and `get_chunks_by_id`
- Use these directly in TOC for navigation

## Decision Flow

```
Ask user for Table of Contents
     │
     ▼
User provides TOC?
     │
     ├─ Yes ─→ Parse chapter list from user TOC
     │         (if chunk IDs included, skip discovery)
     │
     └─ No ──→ Query collection for TOC
                 │
                 ▼
              Found TOC chunk?
                 │
                 ├─ Yes ─→ Parse chapter list from TOC
                 │
                 └─ No ──→ Fall back to iterative scanning
     │
     ▼
For each chapter from TOC:
     │
     ├─ Find chapter_start_chunk_id via query
     │
     ├─ Determine chapter_end (next chapter start or EOF)
     │
     ├─ Calculate chunk_count
     │
     ├─ Chunk count ≤ 30? → Create CHAPTER summary directly
     │
     └─ Chunk count > 30? → Ask user: "Create CHUNKS level?"
            │
            ├─ Yes → Batch into CHUNKS, then CHAPTER
            │
            └─ No → Try CHAPTER anyway, note limitation in summary
     │
     ▼
Create BOOK summary from all CHAPTER summaries
```

## ID Types

| Level | ID Format | Example |
|-------|-----------|---------|
| Level 0 (Raw Chunks) | `{filename}_{timestamp}_{number}` | `dracula.txt_1774557956_0` |
| Level 1-2 (Summaries) | GUID | `6af6f936-5447-4854-9cb8-9ac515e48f45` |

## Prompts

### CHAPTER Summary Prompt (PRIMARY)
```
You are summarizing a chapter of a book.

CHAPTER: {chapter_name}
CHAPTER INDEX: {chapter_index}
CHAPTER START CHUNK ID: {chapter_start_chunk_id}
TOTAL CHUNKS: {chunk_count}

SOURCE TEXT (all chunks in this chapter):
{combined_chunk_texts}

Generate a comprehensive chapter summary:
1. Main events and developments
2. Key characters and their actions
3. Themes explored
4. Significance to overall story

Return JSON:
{
  "chapter_name": "{chapter_name}",
  "chapter_index": {chapter_index},
  "chapter_start_chunk_id": "{chapter_start_chunk_id}",
  "summary": "3-5 sentence comprehensive summary",
  "key_moments": ["important events"],
  "characters": ["main characters"],
  "themes": ["themes explored"],
  "significance": "How this chapter advances the story",
  "chunk_count": {chunk_count}
}
```

### CHUNKS Summary Prompt (OPTIONAL - Only when approved by user)
```
You are summarizing a section of a large chapter.

CHAPTER: {chapter_name}
BATCH: {batch_number} of {total_batches}
CHUNK IDs: {chunk_ids}

SOURCE TEXT:
{combined_chunk_texts}

Create a concise summary of this chunk batch.

Return JSON:
{
  "summary": "2-3 sentence summary",
  "key_events": ["important events"],
  "characters": ["characters mentioned"],
  "chunk_ids": {chunk_ids}
}
```

### BOOK Summary Prompt
```
You are creating an overview of a book.

CHAPTER SUMMARIES:
{chapter_summaries}

Generate document overview:

Return JSON:
{
  "title": "Book title",
  "genre": "Genre",
  "overview": "2-3 paragraph summary",
  "main_characters": [{"name": "", "role": ""}],
  "major_themes": ["theme1", "theme2"],
  "narrative_structure": "How the story is structured",
  "num_chapters": {count}
}
```

## Practical Tips

1. **Find TOC first**: Query "table of contents", "contents", or "index" to find TOC chunk
2. **Use raw chunk IDs**: Store chunk IDs exactly as returned by query (e.g., `filename_timestamp_number`)
3. **Direct to CHAPTER**: Skip CHUNKS level - create CHAPTER summaries directly
4. **Ask for CHUNKS**: Only create CHUNKS when chapter has >30 chunks and summarization quality suffers
5. **Store chunk_ids**: Every summary must contain the raw chunk IDs it covers
6. **TOC for navigation**: TOC points to `chapter_start_chunk_id` for direct navigation
7. **Verify with query**: After saving summaries, query to verify storage

## Usage Example

```
0. Ask user: "Do you have a Table of Contents from the book? Copy and paste it below."
   - If user provides TOC, use it as chapter scaffold
   - If user declines, proceed to step 1

1. collection_list
   → Lists: ["dracula", "mobydick", "pride_prejudice"]

2. Ask user: "Which collection to process?"

3. Find TOC:
   query_collection(collection_name="dracula", query_text="table of contents", n_results=3)
   → Returns TOC chunk with ID like "dracula.txt_1774557956_toc"

4. Get TOC text:
   get_chunks_by_id(collection_name="dracula", ids=["dracula.txt_1774557956_toc"])
   → Returns: "I. Jonathan Harker's Journal... II. Journey to Castle..."

5. Parse chapters and find start IDs:
   For each chapter:
   - query_collection(collection_name="dracula", query_text="Chapter I: Jonathan Harker", n_results=1)
   - Get chapter_start_chunk_id: "dracula.txt_1774557956_0"

6. Create CHAPTER summaries (default):
   - Get all raw chunk texts for chapter
   - add_summary(summary_type=1, ...)
   - Store chunk_ids[] in summary

7. If chapter >30 chunks, ASK USER:
   "Chapter X has 45 chunks. Create intermediate CHUNKS summaries?"
   - If yes: batch ~10 chunks, add_summary(summary_type=0), then CHAPTER

8. add_table_of_contents(collection_name="dracula", toc={...})
   → TOC contains raw chunk IDs: "dracula.txt_1774557956_0", etc.

9. get_summaries(summary_type=1) to get all chapters, create BOOK, add_summary(summary_type=2)
```

## QA Check

Verify summaries created:

```python
# Get all CHAPTER summaries
get_summaries(collection_name="{book}", summary_type=1)

# Get BOOK summary
get_summaries(collection_name="{book}", summary_type=2)

# Verify TOC stored
get_table_of_contents(collection_name="{book}")
```

**Checklist:**
- [ ] All CHAPTER summaries exist (for each chapter)
- [ ] BOOK summary exists
- [ ] TOC stored with chapter_summary_ids
- [ ] No duplicate summaries
- [ ] Each chapter has valid start chunk ID
- [ ] Summary text is comprehensive (not empty)

**If issues found:**
- Missing CHAPTER: Recreate with add_summary
- Duplicate: Delete via get_summaries and recreate
- Empty text: Query more chunks and recreate

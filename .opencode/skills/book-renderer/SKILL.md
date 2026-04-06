---
name: book-renderer-v1
description: Read, summarize, and render books using rag-test/ragatool MCP server - chapters, TOC, chunks, and search
license: MIT
compatibility: opencode
metadata:
  audience: user
  workflow: book-reading, summarization, knowledge-management, storytelling
  version: 1
---

# Book Renderer - Read & Render Books via MCP

## Overview

Read, explore, and render books using rag-test/ragatool MCP server. Navigate by chapters, search text, get summaries at any level, and reconstruct complete story narratives.

**Servers**: rag-test (MUST use `rag-test_` prefix) or ragatool (use `ragatool_` prefix)

---

## MCP Tools Reference

### Collections
| Tool | Purpose |
|------|---------|
| `rag-test_collection_list` | List all available collections |
| `rag-test_get_table_of_contents` | Get stored TOC for a collection |
| `rag-test_add_table_of_contents` | Store TOC for a collection |
| `rag-test_update_table_of_contents` | Update existing TOC |

### Summaries (Hierarchical)
| Tool | Purpose |
|------|---------|
| `rag-test_get_summaries` | Get all summaries by type |
| `rag-test_get_single_summary` | Get single summary by type and index |
| `rag-test_add_summary` | Add new summary to collection |
| `rag-test_update_summary` | Update existing summary |
| `rag-test_delete_summary` | Delete a summary |

**Summary Types**: 0=CHUNKS, 1=CHAPTER, 2=BOOK

### Chunks & Search
| Tool | Purpose |
|------|---------|
| `rag-test_query_collection` | Search collection by text, returns matching chunks |
| `rag-test_get_chunks_by_id` | Get raw chunk text(s) by ID(s) |

---

## Workflow: Reading a Book

### Step 1: List Collections

```
rag-test_collection_list
```

Returns list like:
```json
[
  {"name": "Tale of 2 cities", "description": "...", "properties": "..."},
  {"name": "Dracula", "description": "...", "properties": "..."},
  {"name": "Moby Dick", "description": "...", "properties": "..."}
]
```

**Tip**: Collection names may have spaces or be lowercase versions of book titles.

---

### Step 2: Get Book Overview (BOOK Summary)

```
rag-test_get_summaries(collection_name="{name}", summary_type=2)
```

Returns single BOOK summary with:
- Title, author, genre
- Overview/synopsis
- Main characters with roles
- Major themes
- Narrative structure
- Famous quotes
- Chunk count

**Example** - A Tale of Two Cities:
```json
{
  "title": "A Tale of Two Cities",
  "author": "Charles Dickens",
  "overview": "Set during French Revolution, spanning London and Paris...",
  "main_characters": [
    {"name": "Charles Darnay", "role": "French aristocrat who renounces his family name"},
    {"name": "Sydney Carton", "role": "Brilliant but dissolute lawyer, Darnay's double"}
  ],
  "major_themes": ["Resurrection and Rebirth", "Sacrifice", "Duality"]
}
```

---

### Step 3: Navigate Chapters (CHAPTER Summaries)

Get ALL chapters:
```
rag-test_get_summaries(collection_name="{name}", summary_type=1)
```

**IMPORTANT**: This can return HUGE output (truncated). If list is too big, get chapters ONE AT A TIME using index:

```
rag-test_get_single_summary(collection_name="{name}", summary_type=1, summary_index=0)  // Chapter 1
rag-test_get_single_summary(collection_name="{name}", summary_type=1, summary_index=1)  // Chapter 2
...
```

**Summary Index** matches chapter order (0 = first chapter, 1 = second, etc.)

#### CHAPTER Summary Structure
```json
{
  "chapter_name": "Book the First: Chapter I - The Period",
  "chapter_index": 1,
  "chapter_start_chunk_id": "tale_2_cities.txt_1775156962_6",
  "summary": "The novel opens with Dickens's famous reflection...",
  "key_moments": ["Famous opening passage", "Depiction of social conditions"],
  "characters": ["Jarvis Lorry", "Jerry"],
  "themes": ["Duality", "Social injustice"],
  "significance": "Establishes the novel's themes...",
  "chunk_count": 20,
  "chunk_ids": ["tale_2_cities.txt_1775156962_6", "tale_2_cities.txt_1775156962_7", ...]
}
```

---

### Step 4: Search Within Book

```
rag-test_query_collection(collection_name="{name}", query_text="{search_term}", n_results=10)
```

**Tips**:
- `n_results` defaults to 10, adjust as needed
- For TOC, try: "table of contents", "contents", "index"
- For chapters, try exact chapter names or key phrases
- Returns matching chunks with IDs and distances

**Returns**:
```json
{
  "results": [
    {
      "id": "tale_2_cities.txt_1775156962_6",
      "text": "It was the best of times...",
      "distance": 0.15
    }
  ]
}
```

---

### Step 5: Get Raw Chunks

Get specific chunk(s) by ID:
```
rag-test_get_chunks_by_id(collection_name="{name}", ids=["chunk_id_1"])
```

Get multiple chunks at once:
```
rag-test_get_chunks_by_id(collection_name="{name}", ids=["chunk_id_1", "chunk_id_2", "chunk_id_3"])
```

**Chunk IDs format**: `{filename}_{timestamp}_{number}` (e.g., `tale_2_cities.txt_1775156962_6`)

---

### Step 6: Read TOC

```
rag-test_get_table_of_contents(collection_name="{name}")
```

Returns stored TOC with chapter structure. TOC should contain chapter names and chunk IDs.

---

## Practical Experience

### Lesson 1: Always Get BOOK Summary First

Before diving into chapters, get the BOOK summary. It gives:
- Complete story overview
- Main characters and their roles
- Major themes explained
- Narrative structure (e.g., "Book First: Recalled to Life", "Book Second: The Golden Thread")

This contextualizes individual chapters.

### Lesson 2: CHAPTER Summaries Can Be Huge

When calling `get_summaries(summary_type=1)`:
- Output can exceed 50,000 bytes
- Tool truncates and saves to file
- **Better approach**: Use `get_single_summary` with index

**Batch strategy**: Get 5-8 chapters at a time using sequential index calls.

### Lesson 3: Build Timelines from CHAPTER Summaries

To create a complete timeline:
1. Get BOOK summary for context
2. Get CHAPTER summaries sequentially (index 0, 1, 2...)
3. Extract key events from each `key_moments` array
4. Chronologically order events across chapters
5. Write narrative connecting events

**Example flow for Tale of Two Cities**:
- BOOK → Overview (French Revolution, London/Paris duality)
- Chapter 1 → "The Period" - 1775, social unrest, famous opening
- Chapter 2 → "The Mail" - Lorry receives "Recalled to Life" message
- Chapter 3 → "Night Shadows" - Lorry dreams of buried man
- ...continue building timeline...

### Lesson 4: Convert Summaries to Narrative

When user asks for "the story" or "timeline as a story":

1. **Gather data**:
   - BOOK summary for context
   - All CHAPTER summaries (sequentially)
   - Key events from each

2. **Structure narrative**:
   - Opening: Set scene (year, location, historical context)
   - Rising action: Build through chapters
   - Climax: Identify turning point
   - Resolution: Show ending

3. **Write prose, not lists**:
   - Use "then", "next", "meanwhile", "suddenly"
   - Connect chapters with transitions
   - Include character emotions and motivations
   - Add thematic insights

**Bad**: "Chapter 1: The Period - Famous opening. Chapter 2: The Mail - Lorry travels."

**Good**: "It was the best of times, it was the worst of times. In 1775, Mr. Jarvis Lorry rode the Dover mail coach through heavy mist, clutching a cryptic message that would change everything..."

### Lesson 5: Explain Themes & Symbolism

After summarizing plot, help user understand deeper meaning:

**Example - Carton's Sacrifice**:
```
Why does Carton sacrifice himself?
1. His life was empty and wasted
2. Love transformed into giving, not taking
3. Redemption through sacrifice
4. Duality fulfilled - shadow becomes real
5. Dickens's Christian symbolism - substitutionary death

Why not all escape together?
- One desperate window, one person
- Carton CHOSE to stay - the point
- Meaning through choice, not circumstance
```

---

## Summary Schemas

### BOOK (Type 2)
```json
{
  "title": "Book Title",
  "author": "Author Name",
  "genre": "Genre",
  "overview": "2-3 paragraph summary",
  "main_characters": [{"name": "", "role": ""}],
  "major_themes": ["theme1", "theme2"],
  "narrative_structure": "Book divisions and structure",
  "num_chapters": 27,
  "total_chunks": 1775,
  "famous_quotes": ["quote1", "quote2"]
}
```

### CHAPTER (Type 1)
```json
{
  "chapter_name": "Chapter Title",
  "chapter_index": 1,
  "chapter_start_chunk_id": "file_timestamp_number",
  "summary": "3-5 sentence summary",
  "key_moments": ["event1", "event2"],
  "characters": ["char1", "char2"],
  "themes": ["theme1"],
  "significance": "How chapter advances story",
  "chunk_count": 20,
  "chunk_ids": ["id1", "id2", ...]
}
```

### CHUNKS (Type 0)
```json
{
  "summary": "2-3 sentence summary of chunk batch",
  "chunk_ids": ["id1", "id2"],
  "chapter_name": "Parent chapter",
  "parent_chapter_summary_id": "guid"
}
```

---

## Decision Flow

```
User wants to read/render book
         │
         ▼
List collections → Ask user to pick
         │
         ▼
Get BOOK summary → Understand overview
         │
         ▼
User wants:
         │
    ┌────┴────┬──────────────┬────────────┐
    │         │              │            │
  Specific  Full story     Theme/       Search
  chapter   (timeline)    analysis     within
    │         │              │            │
    ▼         ▼              ▼            ▼
 get_single  Get all       Use BOOK     query_collection
 summary    CHAPTERs      +CHAPTER      with search term
 (by index) sequentially  summaries

```

---

## Common Tasks

### Task: "What is this book about?"
```
1. rag-test_get_summaries(type=2) → BOOK summary
2. Present: title, author, overview, themes, characters
```

### Task: "Tell me chapter 3"
```
1. rag-test_get_single_summary(type=1, index=2)
2. Present: chapter_name, summary, key_moments, characters
```

### Task: "Recreate the full story"
```
1. rag-test_get_summaries(type=2) → BOOK overview
2. rag-test_get_summaries(type=1) → ALL chapters
   (or sequential get_single_summary if large)
3. Build narrative connecting all chapters
4. Write prose, not bullet points
```

### Task: "Find a specific scene"
```
1. rag-test_query_collection(query_text="{scene keywords}", n_results=5)
2. rag-test_get_chunks_by_id(ids=["chunk_id"])
3. Present raw text or summarize
```

### Task: "What happened to character X?"
```
1. rag-test_query_collection(query_text="character name", n_results=10)
2. Analyze returned chunks for character arc
```

---

## Best Practices

1. **Start with BOOK summary** - Provides essential context
2. **Use sequential reads for chapters** - Avoid truncated output
3. **Search to find specific content** - Query is faster than reading all
4. **Convert to narrative when asked for "story"** - Not lists
5. **Explain themes and symbolism** - Help user understand deeper meaning
6. **Include quotes** - Famous lines bring books to life
7. **Connect chapters** - Show how events flow, don't just report

---

## Usage Examples

### Example 1: First-Time Book Exploration

```
> List collections
rag-test_collection_list
→ Found: "Tale of 2 cities"

> What's this book about?
rag-test_get_summaries(collection_name="Tale of 2 cities", summary_type=2)
→ Returns book overview with themes, characters, structure

> Tell me about the first chapter
rag-test_get_single_summary(collection_name="Tale of 2 cities", summary_type=1, summary_index=0)
→ Chapter 1 summary

> What about chapter 2?
rag-test_get_single_summary(collection_name="Tale of 2 cities", summary_type=1, summary_index=1)
→ Chapter 2 summary
```

### Example 2: Full Story Recreation

```
> Recreate the entire story of Moby Dick
1. rag-test_get_summaries(type=2) → Book overview
2. rag-test_get_summaries(type=1) → All chapters (or sequential)
3. Extract key_moments from each chapter
4. Write narrative prose connecting events
5. Include themes: obsession, fate, man vs nature
6. Add famous quotes: "Call me Ishmael"
```

### Example 3: Search and Deep Dive

```
> Find the famous opening line in Tale of Two Cities
rag-test_query_collection(collection_name="Tale of 2 cities", query_text="best of times worst of times", n_results=3)
→ Returns matching chunks

> Get the full text of that chunk
rag-test_get_chunks_by_id(collection_name="Tale of 2 cities", ids=["tale_2_cities.txt_1775156962_6"])
→ Returns full passage
```

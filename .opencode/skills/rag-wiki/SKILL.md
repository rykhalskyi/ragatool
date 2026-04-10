---
name: rag-wiki
description: RAG-based LLM Wiki Agent - maintain compounding knowledge base using rag-test MCP server
license: MIT
compatibility: opencode
metadata:
  audience: user
  workflow: rag, wiki, knowledge-management
  version: 2
---

# RAG LLM Wiki Agent Schema

Maintains a **persistent, compounding knowledge base** using the rag-test MCP server. Unlike simple RAG where the LLM rediscoveries knowledge from scratch on every query, this wiki accumulates synthesis over time. Cross-references are already built. Contradictions are flagged. The wiki keeps getting richer with every source and every question.

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: Raw Sources (Immutable)                  │
│  Collections → Chunks (source text segments)        │
│  The source of truth. Never modified.               │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  LAYER 2: Wiki (LLM-Generated)                     │
│  Summaries (CHUNKS, CHAPTER, BOOK)                 │
│  Wiki Pages (entities, concepts, sources, analyses)│
│  TOC linking chapters to summaries                  │
│  The compounding artifact. Updated on every ingest.│
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│  LAYER 3: Schema (This Skill)                       │
│  Defines conventions, workflows, page types        │
│  Co-evolved with user over time                     │
└─────────────────────────────────────────────────────┘
```

## Key Insight

**The wiki is a persistent, compounding artifact.** Knowledge is compiled once and kept current, not re-derived on every query. When you add a new source, the LLM integrates it into the existing wiki — updating entity pages, revising summaries, flagging contradictions. The cost of maintenance approaches zero because the LLM handles all the bookkeeping.

**Human's job**: Source curation, exploration direction, asking good questions, interpreting meaning.
**LLM's job**: Summarizing, cross-referencing, filing, bookkeeping — everything tedious.

Navigate with `get_wiki_index` to browse wiki pages, `get_table_of_contents` for chapter structure, and `query_collection` to search chunks.

## MCP Tools (rag-test server)

| Tool | Purpose |
|------|---------|
| `collection_list` | List all available collections |
| `query_collection` | Search collection, returns chunks with IDs |
| `get_chunks_by_id` | Retrieve raw chunk texts by IDs |
| `get_summaries` | Retrieve summaries by type (0=CHUNKS, 1=CHAPTER, 2=BOOK) |
| `add_summary` | Add new summary |
| `get_table_of_contents` | Retrieve TOC |
| `add_table_of_contents` | Store TOC |
| `get_wiki_index` | List all wiki pages in collection |
| `get_wiki_page` | Retrieve wiki page by ID |
| `add_wiki_page` | Create new wiki page |
| `edit_wiki_page` | Update existing wiki page |

## Page Types

### Entity Pages
Single topic focus: person, place, organization, event.
```yaml
title: [Name]
type: entity
tags: [relevant-tags]
created: [YYYY-MM-DD]
sources: [count]
```

### Concept Pages
Broader topics, theories, frameworks. Same frontmatter with `type: concept`.

### Source Pages
Summary of ingested sources. Frontmatter includes source reference.

### Analysis Pages
Synthesis, comparisons, answers to queries. Created on-demand.

## Workflows

### Ingest
1. User imports data to rag server and provides collection name
2. LLM reads source collection, discusses key takeaways
3. LLM creates source summaries and wiki pages in rag server
4. LLM updates TOC
5. LLM updates relevant entity/concept pages

### Query
1. User asks question
2. LLM searches rag server for relevant collection
3. LLM queries relevant chunks, TOC, summaries and wiki pages
4. LLM synthesizes answer
5. **If valuable**: file answer back as new wiki page

### Lint
Periodically health-check the wiki. The LLM is good at suggesting new questions and gaps to fill.

Check for:
- **Contradictions** between wiki pages (new sources vs old claims)
- **Stale claims** that newer sources have superseded
- **Orphan pages** with no inbound links
- **Missing cross-references** by chunk IDs or summary/wiki IDs
- **Concept gaps** — important topics mentioned but lacking dedicated pages
- **Data gaps** that could be filled with a web search

### Compound Your Explorations

Answers you ask for become wiki pages. A comparison, an analysis, a connection discovered — file it back into the wiki. Your explorations compound just like ingested sources do.

## Conventions

- Cross-references use markdown links: `[[chunk-id|Display Text]]` or `[[wiki-page-id|Display Text]]`
- Dates in ISO format: YYYY-MM-DD
- Never modify raw sources
- Add YAML frontmatter to all wiki pages
- Use chunk IDs for linking to source material
- Use summary/wiki IDs for linking to processed content

## Navigation

Use these tools to navigate the wiki:

| Tool | Use Case |
|------|----------|
| `get_wiki_index` | List all wiki pages in a collection |
| `get_table_of_contents` | View chapter structure and summary IDs |
| `query_collection` | Search for relevant chunks |
| `get_chunks_by_id` | Drill into specific source text |

## Wiki Page Schema

### Entity
```json
{
  "title": "Count Dracula",
  "type": "entity",
  "tags": ["character", "villain", "gothic-horror"],
  "text": "Comprehensive description with cross-references"
}
```

### Concept
```json
{
  "title": "Vampirism",
  "type": "concept",
  "tags": ["supernatural", "theme", "folklore"],
  "text": "Analysis of vampirism as a theme..."
}
```

### Source
```json
{
  "title": "Dracula - Bram Stoker",
  "type": "source",
  "tags": ["novel", "gothic-horror", "1897"],
  "text": "Source summary with key takeaways..."
}
```

### Analysis
```json
{
  "title": "Dracula Character Analysis",
  "type": "analysis",
  "tags": ["character-study", "themes", "dracula"],
  "text": "Comparative analysis..."
}
```

## ID Types Reference

| Level | ID Format | Example |
|-------|-----------|---------|
| Raw Chunks | `{filename}_{timestamp}_{number}` | `dracula.txt_1774557956_0` |
| Summaries | GUID | `8bf092ea-50f0-4478-8b82-3b14951ea0f4` |
| Wiki Pages | GUID | returned by `add_wiki_page` |
| TOC | GUID | returned by `add_table_of_contents` |

## Workflow Examples

### Ingest New Source

```
1. collection_list
   → Identify target collection or create new

2. User provides source material (collection already exists)

3. query_collection(collection_name, query_text, n_results)
   → Retrieve relevant chunks

4. get_chunks_by_id(collection_name, ids=[...])
   → Get full text of key chunks

5. add_summary(summary_type, ...)
   → Create source/chapter summaries

6. add_wiki_page(collection_name, page_title, type, tags, text)
   → Create wiki page for source. page_title is IMPORTANT

7. update TOC if needed
```

### Query Knowledge Base

```
1. User: "What are the main themes in Dracula?"

2. get_wiki_index(collection_name="dracula")
   → List wiki pages for relevant topics

3. query_collection(collection_name="dracula", query_text="themes", n_results=5)
   → Find relevant chunks

4. get_summaries(collection_name="dracula", summary_type=2)
   → Get book-level summary

5. get_wiki_page(page_id="...")
   → Retrieve relevant wiki pages

6. Synthesize answer from wiki + summaries + chunks
```

### Create Analysis Page

```
1. User: "Compare Jonathan Harker and Van Helsing"

2. query_collection for relevant content on both characters

3. get_chunks_by_id for detailed text

4. Synthesize comparison

5. add_wiki_page(collection_name, {
     "title": "Harker vs Van Helsing Comparison",
     "type": "analysis",
     "tags": ["comparison", "characters"],
     "text": "Detailed analysis..."
   })
```

## Output Formats

Answers can take different forms:
- **Markdown page** (default) - Wiki page format with frontmatter
- **Comparison table** - Side-by-side entity analysis
- **Summary** - Concise overview from summaries

Choose based on what best serves the query.

---
name: rag-retriever
description: RAG Retrieval Best Practices - search and retrieve information from rag-test MCP server
license: MIT
compatibility: opencode
metadata:
  audience: agent
  workflow: rag, retrieval, question-answering
  version: 1
---

# RAG Retriever Skill

Best practices for searching and retrieving information from the rag-test MCP server. This skill covers strategies for different question types and how to leverage the layered RAG architecture effectively.

## Retrieval Strategy Decision Tree

```
USER QUESTION
     │
     ▼
┌─────────────────────────┐
│ Is it a concrete/       │
│ specific fact question? │
│ (names, dates, events,  │
│  quotes, actions)       │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     │ YES         │ NO
     ▼             ▼
┌─────────┐  ┌──────────────────┐
│ QUERY   │  │ Is it about      │
│ chunks  │  │ themes/concepts/ │
│ directly│  │ analysis?        │
└────┬────┘  └────────┬─────────┘
     │                 │
     ▼                 ▼
┌─────────┐     ┌──────────────────┐
│ Specific│     │ Check WIKI pages │
│ chunks  │     │ + BOOK summaries │
└─────────┘     └────────┬─────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Need connections/ │
              │ relationships?   │
              └────────┬─────────┘
                      │
                      ▼
              ┌──────────────────┐
              │ Use GRAPH queries│
              └──────────────────┘
```

## Question Types & Best Strategies

### 1. Concrete/Specific Questions
**Examples**: "What happened to Ahab?", "What did Queequeg look like?", "How did Ishmael survive?"

**Best Strategy**: `query_collection` with specific terms
```javascript
query_collection({
  collection_name: "collection_name",
  query_text: "Ahab death final confrontation",  // Be specific
  n_results: 5
})
```

**Tips**:
- Use key terms from the question
- Lower n_results (5-10) for precision
- Check distances - lower = more relevant
- Specific terms work better than questions

### 2. Thematic/Conceptual Questions
**Examples**: "What is the theme of fate vs free will?", "How does Melville portray obsession?"

**Best Strategy**: Check WIKI pages + BOOK summaries first
```javascript
// Get book-level summary
get_summaries({ collection_name: "x", summary_type: 2 })

// Check relevant wiki pages
get_wiki_index({ collection_id: "x" })
// Then get specific pages about themes
```

**Tips**:
- WIKI pages contain LLM-generated synthesis
- BOOK summaries give the big picture
- CHAPTER summaries cover sections

### 3. Relationship/Connection Questions
**Examples**: "How is Ahab connected to Moby Dick?", "Who participated in the final confrontation?"

**Best Strategy**: GRAPH queries
```javascript
// Find all relationships for a character
graph_query({ 
  query: "MATCH (p:PERSON {name: 'Captain Ahab'})-[r]->(n) RETURN type(r), n.name"
})

// Find participants in an event
graph_query({
  query: "MATCH (e:EVENT {name: 'The Final Confrontation'})<-[r]-(p) RETURN p.name"
})
```

### 4. Navigation/Structure Questions
**Examples**: "What chapters are in the book?", "What is the collection about?"

**Best Strategy**: TOC + Collection listing
```javascript
// Get all collections
collection_list()

// Get table of contents
get_table_of_contents({ collection_name: "collection_name" })

// Get wiki index
get_wiki_index({ collection_id: "collection_id" })
```

## MCP Tools Reference

### Query & Retrieval
| Tool | Use Case | Best For |
|------|----------|----------|
| `query_collection` | Semantic search in chunks | Specific facts, quotes, events |
| `get_chunks_by_id` | Retrieve specific chunk text | Verifying facts, deep dives |
| `get_wiki_index` | Browse all wiki pages | Finding relevant entities/concepts |

### Summaries
| Tool | Type | Use Case |
|------|------|----------|
| `get_summaries` (type=0) | CHUNKS | Individual chunk summaries |
| `get_summaries` (type=1) | CHAPTER | Chapter summaries with key moments |
| `get_summaries` (type=2) | BOOK | Full book overview, themes, characters |

### Graph Navigation
| Tool | Use Case |
|------|----------|
| `graph_query` | Find relationships between entities |
| `graph_add_entities` | Add new entities (PERSON, EVENT, PLACE) |
| `graph_link_entities` | Create relationships |

### Allowed Labels & Relations
```
LABELS: COLLECTION, CHUNK, PERSON, EVENT, PLACE, Node, CHAPTER
RELATIONS: CONTAINS, MENTIONS, LOCATED_IN, PARTICIPATED_IN, KNOWS, MARRIED_TO, ENGAGED_TO, FRIEND_OF, ENEMY_OF, ALLIED_WITH, KIN_OF, WORKS_FOR, MEMBER_OF, LEADER_OF, TRANSFORMS, AFFECTS, INFLUENCES, OWNS, RESIDES_IN, ORIGINATES_FROM, HUNTS, MARKS, LOVES, HATES, CONFLICTS_WITH
```

## Retrieval Workflow

### Step 1: Identify Collection
```javascript
// List available collections
collection_list()
// Returns: [{name, description, properties}]
```

### Step 2: Determine Question Type
- **Concrete**: Use `query_collection`
- **Thematic**: Use wiki + summaries
- **Relational**: Use `graph_query`
- **Structural**: Use TOC

### Step 3: Execute Strategy
Execute the appropriate tool(s) based on question type.

### Step 4: Synthesize
Combine results from multiple sources:
1. Check wiki pages for synthesized understanding
2. Verify with specific chunks
3. Use graph for relationship context

### Step 5: Answer
Provide answer with citations referencing:
- Chunk IDs for specific quotes/facts
- Wiki page titles for concepts
- Graph relationships for connections

## Best Practices

### DO
- Use specific search terms over full questions
- Check distance scores (lower = better match)
- Start with wiki/summaries for overview questions
- Use graph for understanding relationships
- Limit n_results for precision (5-10 is often enough)

### DON'T
- Don't use `query_collection` with full natural language questions
- Don't request too many results (quality > quantity)
- Don't skip the TOC when exploring new collections
- Don't ignore distance scores when evaluating relevance

## Query Term Optimization

### Bad Queries
```
"What happened to the characters at the end of Moby Dick?"
"How does the book explore the theme of obsession?"
```

### Good Queries
```
"Ahab death Moby Dick final confrontation"
"obsession revenge Ahab whale hunt"
"friendship Ishmael Queequeg bond relationship"
```

## Experiment Results

From testing with Moby Dick:

| Question Type | Best Tool | n_results | Distance Threshold |
|---------------|----------|-----------|-------------------|
| Character actions | query_collection | 5-8 | < 0.8 |
| Thematic analysis | wiki + book summary | N/A | N/A |
| Relationships | graph_query | N/A | N/A |
| Specific quotes | query_collection | 3-5 | < 0.7 |
| Location events | TOC + query | 5-10 | < 0.9 |

## Example Workflows

### Factual Question
User: "How did Ishmael survive the sinking of the Pequod?"

```javascript
// 1. Query for specific information
query_collection({
  collection_name: "moby_dick",
  query_text: "Ishmael survival coffin Rachel",
  n_results: 5
})

// 2. Check wiki for context
get_wiki_page({ page_id: "128cda5e-4375-4a3b-90e9-9099606777b2" })  // Ishmael page

// 3. Verify with graph
graph_query({
  query: "MATCH (e:EVENT {name: 'Ishmael\\'s Survival'}) RETURN e"
})

// 4. Synthesize answer
```

### Thematic Question
User: "What is the symbolism of whiteness in Moby Dick?"

```javascript
// 1. Check wiki concept pages
get_wiki_index({ collection_id: "moby_dick" })
// Find relevant pages

// 2. Get book-level summary
get_summaries({ collection_name: "moby_dick", summary_type: 2 })

// 3. Query for specific instances
query_collection({
  collection_name: "moby_dick",
  query_text: "whiteness symbol evil death nature",
  n_results: 10
})

// 4. Synthesize answer
```

### Relationship Question
User: "Who are all the characters connected to Ahab?"

```javascript
// 1. Get all outgoing relationships
graph_query({
  query: "MATCH (a:PERSON {name: 'Captain Ahab'})-[r]->(n) RETURN type(r) as rel, n.name as target"
})

// 2. Get incoming relationships
graph_query({
  query: "MATCH (p)-[r]->(a:PERSON {name: 'Captain Ahab'}) RETURN type(r) as rel, p.name as source"
})

// 3. Synthesize connections
```

## Collection Properties

Each collection has chunking configuration:
```javascript
{
  name: "Collection Name",
  description: "Description",
  properties: {
    text_division: "500 symbols",
    overlap: "50 symbols"  // or 20, varies by collection
  }
}
```

This affects how content is chunked and retrieved. Smaller chunks = more precise, larger = more context.

## Performance Tips

1. **Parallel queries**: Execute independent queries simultaneously
2. **Cache wiki index**: Use `get_wiki_index` once, then filter
3. **Batch operations**: Use `graph_add_entities` for bulk entity creation
4. **Filter by distance**: Only use chunks with distance < 0.8 for facts

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No relevant chunks found | Broaden search terms, increase n_results |
| Wiki page not found | Use `get_wiki_index` to find correct page_id |
| Graph query empty | Check label spelling (case-sensitive) |
| Distance too high | Use more specific terms |

## Summary

The rag-test MCP server provides a powerful multi-layer retrieval system:

1. **Chunks** - Raw source material, semantic search via `query_collection`
2. **Summaries** - LLM-generated synthesis (CHUNKS/CHAPTER/BOOK)
3. **Wiki** - Entity/concept pages for quick reference
4. **Graph** - Relationship database for connections

Choose your tool based on question type, and combine layers for comprehensive answers.

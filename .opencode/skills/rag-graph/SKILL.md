---
name: rag-graph
description: Graph-based knowledge representation using rag-test MCP server - create chapters, entities, relationships in Neo4j
license: MIT
compatibility: opencode
metadata:
  audience: user
  workflow: graph, knowledge-graph, neo4j
  version: 1
---

# Graph-Based Knowledge Agent

Builds **knowledge graphs** using the rag-test MCP server's graph tools. Creates chapter nodes, entities (PERSON, PLACE, EVENT), and relationships to enable complex queries and traversal.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Knowledge Graph                                    │
├─────────────────────────────────────────────────────┤
│  CHAPTER nodes ← linked to COLLECTION               │
│  CHAPTER --CONTAINS--> CHUNK                      │
│  PERSON/PLACE/EVENT ← linked to chunks            │
│  Relations between entities                     │
└─────────────────────────────────────────────────────┘
```

## MCP Graph Tools

| Tool | Purpose |
|------|---------|
| `graph_create_chapter` | Create chapter nodes linked to collection + chunks |
| `graph_add_entities` | Add PERSON, PLACE, EVENT entities linked to chunks |
| `graph_link_entities` | Create relationships between entities |
| `graph_query` | Execute Cypher queries for QA/traversal |

## Node Types

### CHAPTER
Created automatically per chapter in source material:
- Linked to COLLECTION via `CONTAINS`
- Linked to chunks via `CONTAINS`
- Properties: `name`, `collection_id`, `id`

### PERSON
Characters, people, organizations:
- Properties: `name`, `description`, `collection_id`
- Linked to chunks via source reference

### PLACE  
Locations, settings:
- Properties: `name`, `description`, `collection_id`

### EVENT
Key events, plot points:
- Properties: `name`, `description`, `collection_id`

## Allowed Relations

```
INFLUENCES, LOCATED_IN, KIN_OF, LEADER_OF, CONTAINS, ORIGINATES_FROM,
ALLIED_WITH, OWNS, KNOWS, CONFLICTS_WITH, AFFECTS, MENTIONS, WORKS_FOR,
ENEMY_OF, HUNTS, MEMBER_OF, RESIDES_IN, LOVES, MARRIED_TO, PARTICIPATED_IN,
TRANSFORMS, HATES, MARKS, ENGAGED_TO, FRIEND_OF
```

## Workflow: Graph Creation

### Step 1: Verify Collection
```python
# Check collection exists
collection_list()
# Verify TOC for chapter structure  
get_table_of_contents(collection_name="book_name")
```

### Step 2: Create Chapters
```python
# Get TOC to find chunk ranges
toc = get_table_of_contents(collection_name="book_name")

# Create CHAPTER nodes for each chapter
for chapter in toc["chapters"]:
    graph_create_chapter(
        collection_id="book_name",
        chapter_name=f"Book - Chapter {chapter.index}",
        first_chunk_id=chapter.first_chunk_id,
        last_chunk_id=chapter.last_chunk_id
    )
```

### Step 3: Add Entities
```python
# Add main characters as PERSON entities
graph_add_entities(
    chunk_id="first_chunk_id",
    collection_id="book_name",
    entities=[
        {"type": "PERSON", "name": "Character Name", "description": "Role and description"},
        {"type": "PLACE", "name": "Location", "description": "Setting description"},
        {"type": "EVENT", "name": "Event Name", "description": "What happened"}
    ]
)
```

### Step 4: Link Entities
```python
# Create relationships
graph_link_entities(
    source_name="Character A",
    source_type="PERSON",
    target_name="Character B", 
    target_type="PERSON",
    relation="FRIEND_OF"  # Use allowed relation
)
```

## Common Patterns

### Character Relationships
```python
# Main influence
graph_link_entities("Mentor", "PERSON", "Protagonist", "PERSON", "INFLUENCES")
# Love interest
graph_link_entities("Protagonist", "PERSON", "LoveInterest", "PERSON", "LOVES")
# Family
graph_link_entities("Sibling", "PERSON", "Parent", "PERSON", "KIN_OF")
# Friendship
graph_link_entities("Character A", "PERSON", "Character B", "PERSON", "FRIEND_OF")
# Conflict
graph_link_entities("Hero", "PERSON", "Villain", "PERSON", "ENEMY_OF")
# Location
graph_link_entities("Character", "PERSON", "Location", "PLACE", "RESIDES_IN")
```

### Event Relationships  
```python
# Character participates in event
graph_link_entities("Character", "PERSON", "Event", "EVENT", "PARTICIPATED_IN")
# Character affects (causes) event
graph_link_entities("Character", "PERSON", "Event", "EVENT", "AFFECTS")
```

## QA Workflow

### Check Chapters
```cypher
MATCH (col:COLLECTION {name: 'book_name'})-[r:CONTAINS]->(c:CHAPTER) 
RETURN c.name ORDER BY c.name
```

### Check Entities
```cypher
MATCH (e:PERSON) WHERE e.collection_id = 'book_name' 
RETURN e.name, e.description
```

### Check Relationships
```cypher
MATCH (a:PERSON)-[r]->(b) 
WHERE a.collection_id = 'book_name' OR b.collection_id = 'book_name'
RETURN a.name, type(r), b.name
```

### Check for Orphans
```cypher
MATCH (e) WHERE e.collection_id = 'book_name'
OPTIONAL MATCH (e)-[r]->(other)
WITH e, count(r) as relationships
WHERE relationships = 0
RETURN e.name, labels(e)
```

### QA Checklist
1. ✅ All chapters created and linked to collection
2. ✅ All main characters added as PERSON
3. ✅ All locations added as PLACE
4. ✅ Key events added as EVENT
5. ✅ No orphan nodes
6. ✅ Relationship directions correct
7. ✅ No duplicate relationships

## Common Pitfalls

### Wrong Relationship Direction
**Problem:** `A -> B` when it should be `B -> A`
**Fix:** Delete manually in Neo4j browser:
```cypher
MATCH (a)-[r]->(b) WHERE a.name = 'A' AND b.name = 'B' DELETE r
```
Then add correct direction.

### Duplicate Relationships
**Problem:** Multiple relationships between same nodes
**Fix:** Delete one manually with Cypher

### Missing Nodes
**Problem:** Entity not found
**Fix:** Re-add with graph_add_entities using main chunk ID

### Forbidden Relation Error
**Problem:** Relation type not allowed
**Fix:** Use allowed relations list from above

## Cypher Reference

### Basic Queries
```cypher
-- Get all chapters in collection
MATCH (col:COLLECTION {name: 'book_name'})-[r:CONTAINS]->(c:CHAPTER) 
RETURN c.name

-- Get chapter's chunks
MATCH (c:CHAPTER {name: 'Book - Chapter 1'})-[r:CONTAINS]->(chunk:CHUNK) 
RETURN chunk.id ORDER BY chunk.id

-- Get entity relationships
MATCH (a:PERSON)-[r]->(b) 
WHERE a.name = 'Character Name'
RETURN a.name, type(r), b.name

-- Get all nodes in collection
MATCH (e) WHERE e.collection_id = 'book_name' 
RETURN labels(e), e.name
```

### Traversal Examples
```cypher
-- Find all characters connected to Character X
MATCH (c:PERSON {name: 'Character X'})-[r]-(connected)
RETURN connected.name, type(r)

-- Find path between two characters
MATCH path = (a:PERSON)-[*]-(b:PERSON)
WHERE a.name = 'A' AND b.name = 'B'
RETURN path

-- Find character's events
MATCH (c:PERSON {name: 'Character'})-[r:PARTICIPATED_IN|AFFECTS]->(e:EVENT)
RETURN e.name, type(r)
```

## Graph Health Score

Rate from 1-10 based on:
- All chapters linked (1-3)
- All main entities added (1-3)
- Correct relationships (1-2)
- No orphans/duplicates (1-2)

## Example Patterns

### Novels (Generic)
**PERSON entities to add:**
- Protagonist(s)
- Antagonist(s)
- Supporting characters
- Mentor figures

**PLACE entities:**
- Main setting(s)
- Important locations

**EVENT entities:**
- Inciting incident
- Climax
- Resolution
- Key plot points

### Character Arc Patterns
```python
# Mentor -> Protagonist (influence)
graph_link_entities("Mentor", "PERSON", "Hero", "PERSON", "INFLUENCES")

# Love interest
graph_link_entities("Hero", "PERSON", "LoveInterest", "PERSON", "LOVES")

# Family ties
graph_link_entities("Child", "PERSON", "Parent", "PERSON", "KIN_OF")

# Rivalry
graph_link_entities("Hero", "PERSON", "Rival", "PERSON", "ENEMY_OF")

# Mentor/Mentee
graph_link_entities("Teacher", "PERSON", "Student", "PERSON", "KNOWS")
```

### Example: Dorian Gray Graph
- 20 CHAPTER nodes (Chapter I-XX)
- 6 PERSON, 3 PLACE, 4 EVENT
- Health: 8/10

### Example: Dracula Graph (future)
- Use same patterns
- Chapters from TOC
- Characters: Dracula, Van Helsing, Jonathan Harker, Mina Harker, Renfield
- Locations: Transylvania, Carfax Abbey, London

### Example: Moby Dick Graph (future)
- 135 chapters (Loomings to Epilogue)
- Characters: Ishmael, Ahab, Queequeg, Starbuck
- Events: The chase, The white whale

## QA Agent Task

To run QA check on any book graph:

```python
# Launch general agent with this prompt:
"""
Run a thorough QA check on the {book_name} graph.

Check:
1. Verify all CHAPTER nodes exist and linked to collection
2. Verify PERSON entities with descriptions
3. Verify PLACE entities
4. Verify EVENT entities
5. Check for orphan nodes
6. Verify relationship directions
7. Check for duplicate relationships
8. Calculate health score (1-10)

Use:
- rag-test_graph_query for Cypher queries
- rag-test_collection_list to verify collection
- rag-test_get_table_of_contents for chapters

Report:
- Issues found
- Missing relationships
- Health score
"""
```

### Run QA Example
```
Task prompt: "QA check on dracula collection in rag-test graph"
```

## Usage

Load skill:
```
/skill rag-graph
```

Then for any book:
1. `collection_list` → find book
2. `get_table_of_contents` → get chapters
3. Create chapters in loop
4. Add entities (search for main characters)
5. Link relationships
6. Run QA with graph_query or task agent

## Health Score Criteria

| Score | Criteria |
|-------|----------|
| 1-3 | Missing chapters or collection link |
| 4-6 | Chapters done, missing entities |
| 7-8 | Entities done, relationship issues |
| 9-10 | Complete graph, QA passed |
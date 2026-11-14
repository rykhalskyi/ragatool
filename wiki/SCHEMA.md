# Project Wiki Schema

This wiki is a project-specific knowledge base stored in `<project-root>/wiki/`,
version-controlled alongside the code. It tracks project overview, build/deploy
instructions, work items, decisions, and research.

Design goal: **token-lean**. Git is the change history; the wiki stores current
knowledge and decisions.

## Token discipline

1. **Git is the history.** No `## Updates` sections, no dates in index entries,
   no restating superseded content. Use `git log -p wiki/pages/<file>`.
2. **One page per work item by default.** A ticket page carries `## Spec`,
   `## Plan`, and `## Outcome`. Separate `specs/` + `plans/` pages are created
   only for large/ambiguous epics shared by many tickets.
3. **Decisions get a one-liner** in `decisions.md`. Reference the id (`D-07`)
   from the ticket instead of restating rationale.
4. **Minimal frontmatter:** `created`, `type`, `status`, `summary`. No `tags`,
   no `related`.
5. **Never hand-edit `index.md`.** Regenerate with `node scripts/wiki.mjs index`.
   Append `log.md` / `decisions.md` with `wiki.mjs log` / `wiki.mjs decision`.
6. **Keep `AGENTS.md` short.** Detail lives in this `SCHEMA.md`.
7. **Batch writes** at the end of a work session.

## Architecture

```
wiki/
├── AGENTS.md      # short, always-loaded summary
├── SCHEMA.md      # full conventions (this file)
├── index.md       # generated catalog
├── log.md         # append-only activity log
├── decisions.md   # append-only decision record (ADR-lite)
└── pages/
    ├── project-overview.md
    ├── build-deploy.md
    ├── debugging.md          # optional
    ├── epics/
    ├── tickets/
    ├── specs/
    ├── plans/
    └── research/
```

## Page conventions

```yaml
---
created: YYYY-MM-DD
type: overview | build-deploy | epic | ticket | spec | plan | research
status: proposed | in-progress | implemented | superseded
summary: One-line description used to build index.md
---
```

- `created` never changes after creation.
- `summary` is required so the index can be built without reading page bodies.
- Do not add `tags` or `related`.

### Links

Use relative markdown links, never wikilinks. Paths are relative to the file
containing the link:

| From | To | Link |
|---|---|---|
| `wiki/index.md` | any page | `pages/<folder>/<slug>.md` |
| `pages/<sub>/x.md` | `pages/<other>/y.md` | `../<other>/y.md` |
| `pages/<sub>/x.md` | `pages/root-page.md` | `../root-page.md` |
| `pages/root-page.md` | `pages/<folder>/y.md` | `<folder>/y.md` |

### Slugs

- Tickets: `<ticket-id>-<brief>` (e.g. `ticket-15-localization-infra`,
  `issue-11-dual-price`). Brief = 2–4 lowercase hyphenated words.
- Specs and plans share one `<feature-slug>` so they cross-link.
- Research: `<topic>` in lowercase hyphenated words.

## Workflow

### Default: one page per work item

Create a single `pages/tickets/<slug>.md` and fill it in as work progresses:

```markdown
# T<n> — <Title>

Part of the [epic](../epics/<slug>.md).   # if applicable

## Spec
What and why: requirements, scope, design decisions, constraints.

## Plan
Ordered steps, files to create/modify, migrations, tests, risks.

## Outcome
What actually shipped, deviations from the plan, files changed.
```

Flip `status:` from `in-progress` to `implemented` when done.

### Large epic: optional spec + plan

Only for genuinely large/ambiguous work, or when one spec is shared by several
tickets: create `pages/specs/<slug>.md` and `pages/plans/<slug>.md`, and link
the ticket(s) to them.

## Operations

```bash
node scripts/wiki.mjs index
node scripts/wiki.mjs log <action> "<description>"
node scripts/wiki.mjs decision "<decision> — because <reason>"
node scripts/wiki.mjs lint
```

- **index**: scans `pages/**`, reads `summary` frontmatter, rewrites `index.md`.
- **log**: appends `## [YYYY-MM-DD] <action> | <description>` to `log.md`.
  Actions: `init`, `ticket`, `spec`, `plan`, `research`, `update`, `decision`.
- **decision**: appends `- [YYYY-MM-DD] D-nn — <decision> — because <reason>`.
- **lint**: checks missing `created`/`type`, dangling relative links, and pages
  missing from the index.

## Init

Idempotent; never overwrite existing pages:

1. Create the `wiki/` structure.
2. Populate `pages/project-overview.md` and `pages/build-deploy.md`.
3. Write a short `wiki/AGENTS.md` and this `wiki/SCHEMA.md`.
4. Copy the bundled `wiki.mjs` to `<project-root>/scripts/wiki.mjs`.
5. Create `log.md` and `decisions.md`.
6. Run `node scripts/wiki.mjs index`.

## Migration from `.design-specs`

If the project has `.design-specs/` or `.opencode/plans/`, offer to migrate:

1. `.design-specs/specs/*` → `pages/specs/<slug>.md` (file mtime as `created`).
2. `.opencode/plans/*` → `pages/plans/<slug>.md`.
3. Run `wiki.mjs index`; log each migration.
4. Do not delete originals unless the user explicitly asks.

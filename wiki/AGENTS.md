# Ragatool Project Wiki

Token-lean, version-controlled project knowledge base.

- Start at [wiki/index.md](index.md).
- Full conventions: [wiki/SCHEMA.md](SCHEMA.md).
- Stack and architecture: [pages/project-overview.md](pages/project-overview.md).
- Build, test, deploy: [pages/build-deploy.md](pages/build-deploy.md).

Work items live in `pages/tickets/` (one page per item with Spec, Plan, Outcome).
Large epics may add `pages/specs/` and `pages/plans/`. Research goes in `pages/research/`.

Maintain with `node scripts/wiki.mjs index|log|decision|lint` from the project root.
Never hand-edit `index.md`.

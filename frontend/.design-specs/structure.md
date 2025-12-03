# Project Structure

This document outlines the file structure of the `ragatouille` frontend application, following the standard conventions of an Angular CLI-generated project.

## Directory Organization

The project uses a feature-based structure within the `src/app` directory.

```
.
├── src/
│   ├── app/
│   │   ├── components/       # Shared, reusable "dumb" components
│   │   ├── services/         # Application-wide services
│   │   ├── models/           # TypeScript interfaces and classes for data
│   │   ├── pages/            # "Smart" components that represent routes
│   │   └── client/           # Generated API client
│   ├── assets/             # Static assets like images and fonts
│   ├── environments/       # Environment-specific configuration
│   └── styles/             # Global styles and variables
├── e2e/                    # End-to-end tests
├── angular.json            # Angular workspace configuration
├── package.json            # Project dependencies and scripts
└── tsconfig.json           # Base TypeScript configuration
```

## Naming Conventions

### Files
- **Components**: `[name].component.ts` (e.g., `collections-list.component.ts`)
- **Services**: `[name].service.ts` (e.g., `theme.service.ts`)
- **Models**: `[Name].ts` (e.g., `Collection.ts`)
- **Styling**: `[name].component.scss`
- **Tests**: `[name].spec.ts` (for unit/component tests), `[name].spec.ts` in `e2e/` (for E2E tests)

### Code
- **Classes/Types/Interfaces**: `PascalCase` (e.g., `export class CollectionsListComponent`)
- **Methods/Properties**: `camelCase` (e.g., `getCollections()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `const API_URL = ...`)
- **Decorators**: `@PascalCase` (e.g., `@Component`)

## Import Patterns

Imports should be ordered as follows to maintain consistency:

1.  **External Dependencies**: `@angular/*`, `rxjs`, etc.
2.  **Internal Absolute Imports**: from `src/app/*` (e.g., `import { MyService } from 'src/app/services/my.service';`)
3.  **Internal Relative Imports**: (`./my-child.component`)

## Code Organization Principles

1.  **Single Responsibility**: Each file should have a single, clear purpose. A component file should define the component, a service file the service, etc.
2.  **Modularity**: Code is organized into `NgModule`s or standalone components, directives, and pipes. Features are encapsulated within their own directories.
3.  **Smart vs. Dumb Components**:
    *   **Smart Components (Pages)**: Responsible for fetching data, managing state, and communicating with services.
    *   **Dumb Components (UI/Shared)**: Receive data via `@Input()` and emit events via `@Output()`. They have minimal logic and are highly reusable.

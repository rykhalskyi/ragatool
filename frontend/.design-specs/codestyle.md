# Frontend Code Style Guide

This document outlines the code style conventions and best practices for the `ragatouille` frontend application.

## 1. Naming Conventions

- **Files**: Use `kebab-case` for all files (e.g., `my-component.component.ts`).
- **Classes & Interfaces**: Use `PascalCase` (e.g., `class MyComponent {}`).
- **Methods & Properties**: Use `camelCase` (e.g., `myProperty: string;`).
- **Constants**: Use `UPPER_SNAKE_CASE` for global or static constants (e.g., `const BASE_URL = '/api';`).

## 2. Component Design

- **`OnPush` Change Detection**: For better performance, all new components should use `ChangeDetectionStrategy.OnPush`. This is especially important for presentational ("dumb") components.
  ```typescript
  @Component({
    selector: 'app-my-component',
    templateUrl: './my-component.html',
    styleUrls: ['./my-component.scss'],
    changeDetection: ChangeDetectionStrategy.OnPush
  })
  export class MyComponent { ... }
  ```
- **Lifecycle Hooks**: Use `@ngneat/until-destroy` to automatically unsubscribe from observables when a component is destroyed. Avoid manual `ngOnDestroy` logic for subscriptions where possible.
- **Inputs & Outputs**: Use `@Input()` to pass data into a component and `@Output()` to emit events out of it. Avoid direct parent-child dependencies.

## 3. State Management

- **Service-Based State**: For any state that needs to be shared across multiple components, create an Angular service. Use RxJS `BehaviorSubject` or `signal` within the service to manage and expose the state as an observable.
- **Avoid Component-Level State for Shared Data**: Do not store shared data directly in component properties if it can be managed by a service.

## 4. Styling (SCSS)

- **Centralize Variables (DRY)**: Do not use hardcoded pixel values, colors, or fonts directly in component styles. Instead, define and use SCSS variables from the central `src/styles/_variables.scss` file.
  ```scss
  // GOOD
  @import 'variables';
  .my-component {
    padding: $spacing-medium;
    height: $topbar-height;
  }

  // BAD
  .my-component {
    padding: 16px;
    height: 64px;
  }
  ```
- **Scoped Styles**: All styles should be encapsulated within the component's SCSS file. Avoid global styles unless absolutely necessary.

## 5. Templates (HTML)

- **Use `@if` and `@for`**: Prefer the new built-in control flow (`@if`, `@for`) over the older `*ngIf` and `*ngFor` directives for better performance and type checking.

## 6. General Principles

- **Immutability**: Treat data as immutable where possible. When updating state in a service or component, create a new object or array rather than mutating the existing one. This works well with `OnPush` change detection.
- **Remove Dead Code**: Regularly remove unused variables, properties, methods, and components to keep the codebase clean.
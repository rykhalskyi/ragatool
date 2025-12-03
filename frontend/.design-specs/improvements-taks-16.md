### Task: Implement Redesign of `SelectedCollectionImportComponent`

**Objective:** Redesign the `SelectedCollectionImportComponent` as described in `improvements-16.md`, ensuring adherence to project's technical guidelines and best practices.

**Key Features to Implement:**

1.  **Initialization:** On `OnInit`, the component should request `getImportsImportGet()` to retrieve the default import list.
2.  **Form Structure:**
    *   The component's HTML should contain a form with two conceptual fields: `import_name` and `settings`.
    *   The `import_name` will be represented by a select element.
    *   The `settings` will not be directly editable in this component.
3.  **Collection State Handling:**
    *   If the current collection is saved, its `import_name` and `settings` should be loaded into the form.
    *   The `import_name` select must be disabled when a saved collection's import type is loaded.
4.  **Import Button Logic:**
    *   The "Import" button should be disabled if no import is selected.
    *   Clicking the "Import" button should open the `FileImportDialog`, passing the current `settings` (either default or from a saved collection) as data.
5.  **State Management for Unsaved Imports:**
    *   If the user changes the `import_name` selection, its state should be stored using the `importFormState` service.
    *   This service should also be used to store unsaved import states when the user switches between collections and the `SelectedCollectionImportComponent`'s input collection changes.

**Technical Considerations & Best Practices (referencing `simplicity.md` and `tech.md`):**

*   **Angular Material:** Utilize Angular Material components for UI elements (e.g., `mat-select`, `mat-button`, dialogs).
*   **SCSS:** Apply SCSS for styling, using central style variables if applicable (DRY principle).
*   **Change Detection:** Consider using `ChangeDetectionStrategy.OnPush` for performance optimization if the component's inputs are primarily immutable.
*   **Clean Code:** Ensure tests are relevant and remove any dead code.
*   **Directives:** Prefer `@if` and `@for` over `*ngIf` and `*ngFor` in templates.
*   **OpenAPI Client:** Leverage the generated OpenAPI client (`DefaultService`) for API interactions.

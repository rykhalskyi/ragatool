### Once Before tests [ ]
    * if 'Dracula' exists in 'collections list':
        - click 'collection-item'
        - click 'delete icon'
        - click 'delete-confirm-button'

### 1. Add Dracula collecion [ ]
    (import recording "e2e/scenarios/2_step_import_recording.json")

### 2. Edit Lord of the ring description [ ]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'A story of Vlad Dracula'
    - click 'save-description-button'
    - text shown 'collection-description' 'A story of Vlad Dracula'

### 3. Import file again into Dracula collection [ ]
    - click 'collection-item'
    * if 'import-type-select' is enabled:
        - select in 'import-type-select' 'File'
    - click 'import-button'
    - popup shown 'Import File to Dracula'
    - click 'pick-file-button' emulate open file dialog 'text/lotr.txt'
    - click 'import-file-submit-button'
    - element shown 'import-progress'
    - wait until element 'import-progress' hidden
    - text shown 'chunk-count-text' 'Count: 6'

### 4. Rewrite Dracula description [ ]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'New updated description'
    - click 'save-description-button'
    - text shown 'collection-description' 'New updated description'

### 5. Cancel description editing [ ]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'This should be cancelled'
    - click 'cancel-description-button'
    - text shown 'collection-description' 'New updated description'

### 6. Delete Dracula collection [ ]
    - click 'collection-item'
    - click 'delete-collection-button'
    - click 'delete-confirm-button'
    - element hidden 'collection-item'

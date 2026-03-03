### Once Before tests [+]
    * if 'Lord of the Rings' exists in 'collections list':
        - click 'collection-item'
        - click 'delete icon'
        - click 'delete-confirm-button'

### 1. Add Lord of the ring collecion [+]
    - click 'settings-button'
    - disable 'two-step-import-switch'
    - click 'save-settings-button'
    - click 'add-collection-button'
    - popup shown 'add-collection-dialog-title'
    - input to 'add-collection-name-input' 'Lord of the Rings'
    - click 'add-collection-ok-button'
    - popup hidden
    - item shown 'collection-item'
    - click 'collection-item'
    - select in 'import-type-select' 'File'
    - click 'import-button'
    - popup shown 'Import File to Lord of the Rings'
    - click 'pick-file-button' emulate open file dialog 'text/lotr.txt'
    - click 'import-file-submit-button'
    - element shown 'import-progress'
    - wait until element 'import-progress' hidden 
    - text shown 'chunk-count-text' 'Count: 3'

### 2. Edit Lord of the ring description [+]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'A story of a ring.'
    - click 'save-description-button'
    - text shown 'collection-description' 'A story of a ring.'

### 3. Import file again into Lord of the Rings collection [+]
    - click 'collection-item'
    * if 'import-type-select' is enabled:
        - select in 'import-type-select' 'File'
    - click 'import-button'
    - popup shown 'Import File to Lord of the Rings'
    - click 'pick-file-button' emulate open file dialog 'text/lotr.txt'
    - click 'import-file-submit-button'
    - element shown 'import-progress'
    - wait until element 'import-progress' hidden
    - text shown 'chunk-count-text' 'Count: 6'

### 4. Rewrite Lord of the Rings description [+]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'New updated description'
    - click 'save-description-button'
    - text shown 'collection-description' 'New updated description'

### 5. Cancel description editing [+]
    - click 'collection-item'
    - click 'edit-description-button'
    - input to 'description-textarea' 'This should be cancelled'
    - click 'cancel-description-button'
    - text shown 'collection-description' 'New updated description'

### 6. Delete Lord of the Rings collection [+]
    - click 'collection-item'
    - click 'delete-collection-button'
    - click 'delete-confirm-button'
    - element hidden 'collection-item'

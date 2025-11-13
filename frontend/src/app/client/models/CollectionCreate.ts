/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ImportType } from './ImportType';
export type CollectionCreate = {
    name: string;
    description?: (string | null);
    model?: (string | null);
    chunk_size?: (number | null);
    chunk_overlap?: (number | null);
    enabled?: (boolean | null);
    import_type?: ImportType;
};


/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_import_file_import__collection_id__post } from '../models/Body_import_file_import__collection_id__post';
import type { Import } from '../models/Import';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ImportService {
    /**
     * Get Imports
     * @returns Import Successful Response
     * @throws ApiError
     */
    public static getImportsImportGet(): CancelablePromise<Array<Import>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/import/',
        });
    }
    /**
     * Import File
     * @param collectionId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importFileImportCollectionIdPost(
        collectionId: string,
        formData: Body_import_file_import__collection_id__post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/import/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

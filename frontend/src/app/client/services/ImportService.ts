/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_import_file_import__collection_id__post } from '../models/Body_import_file_import__collection_id__post';
import type { Body_import_file_step_1_import_step1__collection_id__post } from '../models/Body_import_file_step_1_import_step1__collection_id__post';
import type { Body_import_file_step_2_import_step2__collection_id__post } from '../models/Body_import_file_step_2_import_step2__collection_id__post';
import type { Body_import_url_import_url__colletion_id__post } from '../models/Body_import_url_import_url__colletion_id__post';
import type { Body_import_url_step_1_import_url_step1__collection_id__post } from '../models/Body_import_url_step_1_import_url_step1__collection_id__post';
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
    /**
     * Import Url
     * @param collectionId
     * @param url
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importUrlImportUrlColletionIdPost(
        collectionId: string,
        url: string,
        formData: Body_import_url_import_url__colletion_id__post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/import/url/{colletion_id}',
            query: {
                'collection_id': collectionId,
                'url': url,
            },
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Import File Step 1
     * @param collectionId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importFileStep1ImportStep1CollectionIdPost(
        collectionId: string,
        formData: Body_import_file_step_1_import_step1__collection_id__post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/import/step1/{collection_id}',
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
    /**
     * Import File Step 2
     * @param collectionId
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importFileStep2ImportStep2CollectionIdPost(
        collectionId: string,
        formData: Body_import_file_step_2_import_step2__collection_id__post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/import/step2/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Import Url Step 1
     * @param collectionId
     * @param url
     * @param formData
     * @returns any Successful Response
     * @throws ApiError
     */
    public static importUrlStep1ImportUrlStep1CollectionIdPost(
        collectionId: string,
        url: string,
        formData: Body_import_url_step_1_import_url_step1__collection_id__post,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/import/url/step1/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            query: {
                'url': url,
            },
            formData: formData,
            mediaType: 'application/x-www-form-urlencoded',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

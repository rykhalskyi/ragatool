/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Summary } from '../models/Summary';
import type { SummaryCreate } from '../models/SummaryCreate';
import type { SummaryUpdate } from '../models/SummaryUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SummariesService {
    /**
     * List Summaries By Collection
     * Get all summaries for a specific collection.
     * @param collectionId
     * @returns Summary Successful Response
     * @throws ApiError
     */
    public static listSummariesByCollectionSummariesCollectionCollectionIdGet(
        collectionId: string,
    ): CancelablePromise<Array<Summary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/summaries/collection/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Summaries By Type
     * Get summaries of a specific type for a collection.
     * @param collectionId
     * @param summaryType
     * @returns Summary Successful Response
     * @throws ApiError
     */
    public static listSummariesByTypeSummariesCollectionCollectionIdTypeSummaryTypeGet(
        collectionId: string,
        summaryType: number,
    ): CancelablePromise<Array<Summary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/summaries/collection/{collection_id}/type/{summary_type}',
            path: {
                'collection_id': collectionId,
                'summary_type': summaryType,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create New Summary
     * Create a new summary.
     * @param requestBody
     * @returns Summary Successful Response
     * @throws ApiError
     */
    public static createNewSummarySummariesPost(
        requestBody: SummaryCreate,
    ): CancelablePromise<Summary> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/summaries/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Existing Summary
     * Update an existing summary.
     * @param summaryId
     * @param requestBody
     * @returns Summary Successful Response
     * @throws ApiError
     */
    public static updateExistingSummarySummariesSummaryIdPut(
        summaryId: string,
        requestBody: SummaryUpdate,
    ): CancelablePromise<Summary> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/summaries/{summary_id}',
            path: {
                'summary_id': summaryId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Existing Summary
     * Delete a summary.
     * @param summaryId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteExistingSummarySummariesSummaryIdDelete(
        summaryId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/summaries/{summary_id}',
            path: {
                'summary_id': summaryId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

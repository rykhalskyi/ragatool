/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Collection } from '../models/Collection';
import type { CollectionContentRequest } from '../models/CollectionContentRequest';
import type { CollectionContentResponse } from '../models/CollectionContentResponse';
import type { CollectionCreate } from '../models/CollectionCreate';
import type { CollectionDetails } from '../models/CollectionDetails';
import type { CollectionQueryResponse } from '../models/CollectionQueryResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CollectionsService {
    /**
     * Read Collections
     * @returns Collection Successful Response
     * @throws ApiError
     */
    public static readCollectionsCollectionsGet(): CancelablePromise<Array<Collection>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/collections/',
        });
    }
    /**
     * Create New Collection
     * @param requestBody
     * @returns Collection Successful Response
     * @throws ApiError
     */
    public static createNewCollectionCollectionsPost(
        requestBody: CollectionCreate,
    ): CancelablePromise<Collection> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/collections/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Collection
     * @param collectionId
     * @returns Collection Successful Response
     * @throws ApiError
     */
    public static readCollectionCollectionsCollectionIdGet(
        collectionId: string,
    ): CancelablePromise<Collection> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/collections/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Existing Collection
     * @param collectionId
     * @param requestBody
     * @returns Collection Successful Response
     * @throws ApiError
     */
    public static updateExistingCollectionCollectionsCollectionIdPut(
        collectionId: string,
        requestBody: CollectionCreate,
    ): CancelablePromise<Collection> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/collections/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Existing Collection
     * @param collectionId
     * @returns any Successful Response
     * @throws ApiError
     */
    public static deleteExistingCollectionCollectionsCollectionIdDelete(
        collectionId: string,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/collections/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Collection Details
     * @param collectionId
     * @returns CollectionDetails Successful Response
     * @throws ApiError
     */
    public static readCollectionDetailsCollectionsCollectionIdDetailsGet(
        collectionId: string,
    ): CancelablePromise<CollectionDetails> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/collections/{collection_id}/details',
            path: {
                'collection_id': collectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Collection Content
     * @param collectionId
     * @param requestBody
     * @returns CollectionContentResponse Successful Response
     * @throws ApiError
     */
    public static readCollectionContentCollectionsCollectionIdContentPost(
        collectionId: string,
        requestBody: CollectionContentRequest,
    ): CancelablePromise<CollectionContentResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/collections/{collection_id}/content',
            path: {
                'collection_id': collectionId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Query Collection Endpoint
     * @param collectionId
     * @param queryText
     * @returns CollectionQueryResponse Successful Response
     * @throws ApiError
     */
    public static queryCollectionEndpointCollectionsCollectionIdQueryGet(
        collectionId: string,
        queryText: string,
    ): CancelablePromise<CollectionQueryResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/collections/{collection_id}/query',
            path: {
                'collection_id': collectionId,
            },
            query: {
                'query_text': queryText,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

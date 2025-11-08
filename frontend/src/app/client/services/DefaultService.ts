/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Run Proof Of Concept
     * @returns any Successful Response
     * @throws ApiError
     */
    public static runProofOfConceptPocGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/poc/',
        });
    }
    /**
     * Check Chromadb
     * @param query
     * @returns any Successful Response
     * @throws ApiError
     */
    public static checkChromadbCheckGet(
        query: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/check/',
            query: {
                'query': query,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Items
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readItemsItemsGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/items/',
        });
    }
    /**
     * Read Root
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readRootGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
}

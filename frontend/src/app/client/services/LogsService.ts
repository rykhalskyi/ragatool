/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Message } from '../models/Message';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LogsService {
    /**
     * Read Logs
     * Retrieve the latest n log entries.
     * @param n
     * @returns Message Successful Response
     * @throws ApiError
     */
    public static readLogsLogsGet(
        n: number = 10,
    ): CancelablePromise<Array<Message>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/logs/',
            query: {
                'n': n,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Stream
     * @returns any Successful Response
     * @throws ApiError
     */
    public static streamLogsStreamGet(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/logs/stream',
        });
    }
}

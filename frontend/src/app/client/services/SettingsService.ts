/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Setting } from '../models/Setting';
import type { SettingCreate } from '../models/SettingCreate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SettingsService {
    /**
     * Read Settings
     * @returns Setting Successful Response
     * @throws ApiError
     */
    public static readSettingsSettingsGet(): CancelablePromise<Array<Setting>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/settings/',
        });
    }
    /**
     * Update Settings
     * @param requestBody
     * @returns Setting Successful Response
     * @throws ApiError
     */
    public static updateSettingsSettingsPut(
        requestBody: Array<SettingCreate>,
    ): CancelablePromise<Array<Setting>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/settings/',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
